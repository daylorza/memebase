"""GeckoTerminal client — trending discovery + batched token data.

Binding constraint: ~30 req/min keyless. Every call goes through the gap
limiter (>=2.1s between calls). Batch-first: use tokens/multi, never loop
per-token.
"""

from .. import config
from . import _http

_limiter = _http.GapLimiter(config.GECKO_MIN_GAP)
_HEADERS = {"accept": "application/json"}


def _f(x):
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


async def fetch_trending(client) -> list[dict]:
    """Top trending Solana pools, normalized. One call."""
    await _limiter.wait()
    r = await client.get(
        f"{config.GECKO_BASE}/networks/solana/trending_pools",
        params={"include": "base_token"},
        headers=_HEADERS,
    )
    r.raise_for_status()
    body = r.json()

    included = {i.get("id"): (i.get("attributes") or {}) for i in body.get("included", [])}

    out: list[dict] = []
    for p in body.get("data", []):
        a = p.get("attributes") or {}
        rel = ((p.get("relationships") or {}).get("base_token") or {}).get("data") or {}
        tok = included.get(rel.get("id"), {}) or {}

        chg = (a.get("price_change_percentage") or {}).get("h24")
        tx = ((a.get("transactions") or {}).get("h24") or {})
        vol = (a.get("volume_usd") or {}).get("h24")

        out.append(
            {
                "pool": p.get("id"),
                "dex": a.get("dex_id"),
                "name": tok.get("name"),
                "symbol": tok.get("symbol"),
                "mint": tok.get("address"),
                "price_usd": _f(a.get("base_token_price_usd")),
                "fdv_usd": _f(a.get("fdv_usd")),
                "market_cap_usd": _f(a.get("market_cap_usd")),
                "change_h24": _f(chg),
                "volume_h24": _f(vol),
                "liquidity_usd": _f(a.get("reserve_in_usd")),
                "txns_h24": (tx.get("buys") or 0) + (tx.get("sells") or 0),
            }
        )
    return out


async def fetch_tokens_batch(client, mints: list[str]) -> dict[str, dict]:
    """Up to ~30 mints in ONE call. Returns {mint: normalized pool attrs}."""
    mints = [m for m in mints if m][:30]
    if not mints:
        return {}
    await _limiter.wait()
    r = await client.get(
        f"{config.GECKO_BASE}/networks/solana/tokens/multi/" + ",".join(mints),
        headers=_HEADERS,
    )
    r.raise_for_status()
    out: dict[str, dict] = {}
    for t in r.json().get("data", []):
        a = t.get("attributes") or {}
        mint = a.get("address")
        if not mint or mint in out:
            continue
        chg = (a.get("price_change_percentage") or {}).get("h24")
        out[mint] = {
            "mint": mint,
            "name": a.get("name"),
            "symbol": a.get("symbol"),
            "price_usd": _f(a.get("price_usd")),
            "fdv_usd": _f(a.get("fdv_usd")),
            "market_cap_usd": _f(a.get("market_cap_usd")),
            "change_h24": _f(chg),
            "source": "geckoterminal",
        }
    return out
