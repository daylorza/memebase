"""DexScreener client — the market-data workhorse.

Free, keyless, 300 req/min. /tokens/v1/solana/{mints} refreshes up to 30
mints in ONE call — this is how the whole watchlist stays fresh.
No OHLCV here (current state only); candles come later via GeckoTerminal.
"""

from .. import config

_HEADERS = {"accept": "application/json"}


def _f(x):
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def _normalize_pair(p: dict) -> dict | None:
    bt = p.get("baseToken") or {}
    mint = bt.get("address")
    if not mint:
        return None
    liq = p.get("liquidity") or {}
    vol = p.get("volume") or {}
    chg = p.get("priceChange") or {}
    tx = (p.get("txns") or {}).get("h24") or {}
    return {
        "mint": mint,
        "name": bt.get("name"),
        "symbol": bt.get("symbol"),
        "price_usd": _f(p.get("priceUsd")),
        "price_native": p.get("priceNative"),
        "fdv": _f(p.get("fdv")),
        "market_cap": _f(p.get("marketCap")),
        "liquidity_usd": _f(liq.get("usd")),
        "volume_h24": _f(vol.get("h24")),
        "change_h24": _f(chg.get("h24")),
        "txns_h24": (tx.get("buys") or 0) + (tx.get("sells") or 0),
        "dex": p.get("dexId"),
        "pair": p.get("pairAddress"),
        "source": "dexscreener",
    }


async def fetch_tokens(client, mints: list[str]) -> dict[str, dict]:
    """Top-pair market data for up to 30 mints. Returns {mint: entry}."""
    mints = [m for m in mints if m][:30]
    if not mints:
        return {}
    r = await client.get(
        f"{config.DEX_BASE}/tokens/v1/solana/" + ",".join(mints),
        headers=_HEADERS,
    )
    r.raise_for_status()
    out: dict[str, dict] = {}
    for p in r.json() or []:
        n = _normalize_pair(p)
        if n and n["mint"] not in out:
            out[n["mint"]] = n
    return out
