"""Chart deep-links for tokens: GeckoTerminal first, DexScreener fallback.

GeckoTerminal pool pages are used when we know the exact pool (trending
items come from GeckoTerminal, so they always resolve). Otherwise we check
the periodic gecko_index (which watchlist mints GeckoTerminal actually
indexes) and fall back to DexScreener's token page, which we know resolves
because our market data comes from there.
"""

GECKO_POOL_URL = "https://www.geckoterminal.com/solana/pools/{}"
GECKO_TOKEN_URL = "https://www.geckoterminal.com/solana/tokens/{}"
DEX_TOKEN_URL = "https://dexscreener.com/solana/{}"


def _pool_addr(pool: str | None) -> str | None:
    # GeckoTerminal API ids look like "solana_<address>"; the website wants
    # just the address.
    if not pool:
        return None
    return pool.split("_", 1)[-1] if "_" in pool else pool


def chart_url(mint: str | None, pool: str | None = None, gecko_indexed=()) -> str | None:
    addr = _pool_addr(pool)
    if addr:
        return GECKO_POOL_URL.format(addr)
    if not mint:
        return None
    if mint in gecko_indexed:
        return GECKO_TOKEN_URL.format(mint)
    return DEX_TOKEN_URL.format(mint)
