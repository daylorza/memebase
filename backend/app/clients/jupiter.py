"""Jupiter Price API v3 — cheap price-tick layer between DexScreener refreshes.

Keyless: 0.5 RPS. Prices only (no volume/liquidity). Low-confidence tokens
return null — we fail closed and keep the last known price.
"""

from .. import config
from . import _http

_limiter = _http.GapLimiter(config.JUPITER_MIN_GAP)


async def fetch_prices(client, mints: list[str]) -> dict[str, float]:
    """Up to 50 mints per call. Returns {mint: price_usd}."""
    mints = [m for m in mints if m][:50]
    if not mints:
        return {}
    await _limiter.wait()
    r = await client.get(
        f"{config.JUP_BASE}/price/v3",
        params={"ids": ",".join(mints)},
        headers={"accept": "application/json"},
    )
    r.raise_for_status()
    data = (r.json().get("data") or {})
    out: dict[str, float] = {}
    for mint, v in data.items():
        if v and v.get("price") is not None:
            try:
                out[mint] = float(v["price"])
            except (TypeError, ValueError):
                continue
    return out
