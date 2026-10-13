"""Background polling loops — one per feed, batch-first, never crash.

Rule: on ANY exception, log it and keep serving the stale cache. A dead
feed must never take down the dashboard or the other feeds.
"""

import asyncio
import logging
import time

from . import config
from . import links
from . import momentum
from . import watchlist
from .clients import coingecko, dexscreener, geckoterminal, jupiter

log = logging.getLogger("meme-desk.scheduler")


async def _loop(name: str, interval: float, fn, *args) -> None:
    while True:
        try:
            await fn(*args)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("poll loop %r failed; serving stale cache", name)
        await asyncio.sleep(interval)


async def poll_trending(client, cache) -> None:
    data = await geckoterminal.fetch_trending(client)
    for d in data:
        # Trending pools come from GeckoTerminal, so the pool page always resolves.
        d["chart_url"] = links.chart_url(d.get("mint"), pool=d.get("pool"))
    await cache.set("trending", data)
    await cache.set("trending_mints", [d["mint"] for d in data if d.get("mint")])
    log.info("trending refreshed: %d pools", len(data))


async def poll_gecko_index(client, cache) -> None:
    """Which watchlist mints does GeckoTerminal actually index? (cheap: 1 call / 10 min)

    Drives the GeckoTerminal-first / DexScreener-fallback chart links.
    """
    mints = watchlist.mints()
    if not mints:
        return
    batch = await geckoterminal.fetch_tokens_batch(client, mints)
    await cache.set("gecko_indexed", sorted(batch.keys()))
    log.info("gecko index refreshed: %d/%d watchlist mints indexed", len(batch), len(mints))


async def poll_market(client, cache) -> None:
    trending_mints = (await cache.peek("trending_mints")) or []
    mints: list[str] = []
    for m in trending_mints + watchlist.mints():
        if m and m not in mints:
            mints.append(m)
    mints = mints[:30]  # DexScreener batch cap — batch-first, never per-token loops
    if not mints:
        return
    fresh = await dexscreener.fetch_tokens(client, mints)
    merged = (await cache.peek("market")) or {}
    merged.update(fresh)
    await cache.set("market", merged)
    momentum.record(merged)  # feed the early-momentum time series
    log.info("market refreshed: %d/%d mints", len(fresh), len(mints))


async def poll_ticks(client, cache) -> None:
    market = (await cache.peek("market")) or {}
    mints = list(market.keys())[:50]
    if not mints:
        return
    prices = await jupiter.fetch_prices(client, mints)
    if prices:
        await cache.set("ticks", {"prices": prices, "ts": time.time()})
        log.debug("ticks refreshed: %d prices", len(prices))


def _btc_state(price: float) -> tuple[str, float]:
    dist_pct = (config.BTC_WALL - price) / price * 100
    if price >= config.BTC_WALL:
        return "broken", dist_pct
    if price < config.BTC_BEAR:
        return "bear", dist_pct
    return "pinned", dist_pct


def _desk_read(btc_price: float, state: str) -> str:
    if state == "broken":
        return (
            "BTC cleared the third-tap wall at $87k — volatility expands. Watch the retest: "
            "hold above $87k opens $90k; a wick-and-fail back under is the bull trap. For memecoin "
            "beta, the green light is a daily close above the wall, not a wick."
        )
    if state == "bear":
        return (
            "BTC lost $84k — the bear trigger. $80k comes into play fast. Memecoin beta gets no bid "
            "here: stand down on new entries, protect capital, let the tape re-stabilize above $84k first."
        )
    return (
        "Third rejection at $87k but the $85k shelf held — a market coiling, not rolling over. "
        "Memecoin beta stays contested tape: keep size small until $87k breaks or $84k fails."
    )


async def poll_regime(client, cache) -> None:
    # Partial-failure tolerant: each source is independent; a single-source
    # blip must not nuke the whole panel. Merge with previous cache.
    prev = (await cache.peek("regime")) or {}

    macro = None
    try:
        macro = await coingecko.fetch_btc_sol(client)
    except Exception:
        log.warning("regime: coingecko failed, keeping previous BTC/SOL")

    pump: dict = {}
    try:
        pump_pairs = await dexscreener.fetch_tokens(client, [config.PUMP_MINT])
        pump = pump_pairs.get(config.PUMP_MINT, {})
    except Exception:
        log.warning("regime: dexscreener PUMP fetch failed, keeping previous")

    if macro is None and not pump and not prev:
        raise RuntimeError("regime: all sources failed and cache is empty")

    btc = macro["btc"] if macro else (prev.get("btc") or {})
    sol = macro["sol"] if macro else (prev.get("sol") or {})
    if not pump:
        pump = prev.get("pump") or {}

    btc_price = btc.get("price")
    state, dist_pct = _btc_state(btc_price) if btc_price else (prev.get("btc", {}).get("state", "pinned"), 0.0)

    regime = {
        "btc": {
            "price": btc_price,
            "change_24h": btc.get("change_24h"),
            "state": state,  # broken | pinned | bear
            "dist_to_wall_pct": round(dist_pct, 2) if btc_price else None,
            "wall": config.BTC_WALL,
        },
        "sol": sol,
        "pump": {
            "price": pump.get("price_usd"),
            "change_24h": pump.get("change_h24"),
            "liquidity_usd": pump.get("liquidity_usd"),
            "volume_h24": pump.get("volume_h24"),
            "dex": pump.get("dex"),
        },
        "read": _desk_read(btc_price, state) if btc_price else prev.get("read", ""),
        # Weekly snapshot — NOT live. Refresh from the morning tape.
        "etf_snapshot": {
            "as_of": "2026-10-05",
            "live": False,
            "flows": {"BTC": "+$241M", "SOL": "+", "XRP": "+", "ETH": "-$138M"},
            "next_catalyst": "FOMC minutes Wed",
        },
    }
    await cache.set("regime", regime)
    log.info("regime refreshed: btc=%s state=%s", btc_price, state)


def start(client, cache) -> list[asyncio.Task]:
    """Create all background poll tasks. Call once at startup."""
    return [
        asyncio.create_task(_loop("trending", config.TRENDING_INTERVAL, poll_trending, client, cache)),
        asyncio.create_task(_loop("market", config.MARKET_INTERVAL, poll_market, client, cache)),
        asyncio.create_task(_loop("ticks", config.TICK_INTERVAL, poll_ticks, client, cache)),
        asyncio.create_task(_loop("regime", config.REGIME_INTERVAL, poll_regime, client, cache)),
        asyncio.create_task(_loop("gecko_index", config.GECKO_INDEX_INTERVAL, poll_gecko_index, client, cache)),
    ]
