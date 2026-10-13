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


def chart_url(mint: str | None, pool: str | None = None, gecko_indexed=()) -> str | None:
    if pool:
        return GECKO_POOL_URL.format(pool)
    if not mint:
        return None
    if mint in gecko_indexed:
        return GECKO_TOKEN_URL.format(mint)
    return DEX_TOKEN_URL.format(mint)
