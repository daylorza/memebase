"""CoinGecko keyless — BTC/SOL 24h read for the regime strip.

Endpoint: /simple/price?ids=bitcoin,solana&vs_currencies=usd&include_24hr_change=true
Conservative 6s gap; we only call it once per 60s regime poll.
"""

from .. import config
from . import _http

_limiter = _http.GapLimiter(config.COINGECKO_MIN_GAP)


async def fetch_btc_sol(client) -> dict:
    await _limiter.wait()
    r = await client.get(
        f"{config.COINGECKO_BASE}/simple/price",
        params={
            "ids": "bitcoin,solana",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        headers={"accept": "application/json"},
    )
    r.raise_for_status()
    j = r.json()
    return {
        "btc": {
            "price": float(j["bitcoin"]["usd"]),
            "change_24h": float(j["bitcoin"].get("usd_24h_change") or 0),
        },
        "sol": {
            "price": float(j["solana"]["usd"]),
            "change_24h": float(j["solana"].get("usd_24h_change") or 0),
        },
    }
