"""Meme Desk backend — M0.

Single rule: the frontend talks only to this backend. All third-party
polling (GeckoTerminal, DexScreener, Jupiter, CoinGecko) lives here so rate
limits are managed in one place.

Every /api/* response carries a `stale` flag — the frontend shows STALE
badges from it. Stale flags over fake data, always.
"""

import logging
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config, scheduler, watchlist
from .cache import TTLCache
from .clients import dexscreener

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("meme-desk")

cache = TTLCache()
START = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient(
        timeout=config.HTTP_TIMEOUT,
        headers={"User-Agent": config.USER_AGENT},
    )
    app.state.client = client
    app.state.tasks = scheduler.start(client, cache)
    # Warm the cache once so the first page load has data.
    for warm in (scheduler.poll_trending, scheduler.poll_market, scheduler.poll_regime):
        try:
            await warm(client, cache)
        except Exception:
            log.exception("startup warm of %s failed; loops will retry", warm.__name__)
    yield
    for t in app.state.tasks:
        t.cancel()
    await client.aclose()


app = FastAPI(title="Meme Desk", version="0.1.0", lifespan=lifespan)

# NOTE: allow-all CORS is for v1 personal use only (single user, private box).
# Tighten this the moment the dashboard is shared or sold.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "version": "0.1.0", "uptime_s": int(time.time() - START)}


@app.get("/api/trending")
async def trending() -> dict:
    entry = await cache.read("trending", config.TRENDING_TTL)
    market = (await cache.peek("market")) or {}
    data = entry["data"] or []
    # Enrich with fresher DexScreener market data where we have it.
    enriched = []
    for d in data:
        md = market.get(d.get("mint") or "")
        enriched.append({**d, "market": md} if md else d)
    return {
        "data": enriched,
        "count": len(enriched),
        "stale": entry["stale"],
        "fetched_at": entry["fetched_at"],
    }


@app.get("/api/token/{mint}")
async def token(mint: str) -> dict:
    market = (await cache.peek("market")) or {}
    cached = market.get(mint)
    entry = await cache.read(f"token:{mint}", config.TOKEN_TTL)
    if cached and not entry["stale"] and entry["data"]:
        return {"data": entry["data"], "stale": False, "fetched_at": entry["fetched_at"]}
    # On-demand fetch (single mint through the batch endpoint — still one call).
    try:
        fresh = await dexscreener.fetch_tokens(app.state.client, [mint])
        if mint in fresh:
            await cache.set(f"token:{mint}", fresh[mint])
            entry = await cache.read(f"token:{mint}", config.TOKEN_TTL)
    except Exception:
        log.exception("on-demand fetch for %s failed", mint)
    data = entry["data"] or cached
    return {
        "data": data,
        "stale": entry["stale"] if entry["data"] else True,
        "fetched_at": entry["fetched_at"],
    }


@app.get("/api/regime")
async def regime() -> dict:
    entry = await cache.read("regime", config.REGIME_TTL)
    return {
        "data": entry["data"],
        "stale": entry["stale"],
        "fetched_at": entry["fetched_at"],
    }


@app.get("/api/watchlist")
async def get_watchlist() -> dict:
    market = (await cache.peek("market")) or {}
    ticks = ((await cache.peek("ticks")) or {}).get("prices", {})
    items = []
    for w in watchlist.WATCHLIST:
        item = dict(w)
        md = market.get(w["mint"])
        if md:
            item["market"] = md
        if w["mint"] in ticks:
            item["tick_price"] = ticks[w["mint"]]
        items.append(item)
    return {"data": items, "count": len(items)}
