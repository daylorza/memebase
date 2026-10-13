"""M0 tunables — from docs/app-spec.md §3.1 and docs/api-sources.md.

All third-party feeds here are keyless and read-only. The binding
constraint is GeckoTerminal's ~30 req/min: batch-first, never per-token
loops, and always serve from cache with visible stale flags.
"""

# --- poll intervals (seconds) ---
TRENDING_INTERVAL = 60
MARKET_INTERVAL = 25
TICK_INTERVAL = 12
REGIME_INTERVAL = 60

# --- cache TTLs (seconds) ---
TRENDING_TTL = 90
MARKET_TTL = 40
TICK_TTL = 20
REGIME_TTL = 90
TOKEN_TTL = 120  # on-demand /api/token/{mint} cache
GECKO_INDEX_INTERVAL = 600  # how often to re-check GeckoTerminal index coverage

# --- per-source minimum spacing between calls (rate-limit safety) ---
GECKO_MIN_GAP = 2.1      # 30 req/min keyless
JUPITER_MIN_GAP = 2.0    # 0.5 RPS keyless
COINGECKO_MIN_GAP = 6.0  # conservative for free simple/price
# DexScreener: 300 req/min — no explicit gap needed at our cadence

# --- regime levels (ported from regime-strip.html) ---
BTC_WALL = 87_000.0
BTC_BEAR = 84_000.0
PUMP_MINT = "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"  # verified 2026-10-06

# --- endpoints ---
GECKO_BASE = "https://api.geckoterminal.com/api/v2"
DEX_BASE = "https://api.dexscreener.com"
JUP_BASE = "https://api.jup.ag"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

HTTP_TIMEOUT = 20.0
USER_AGENT = "meme-desk/0.1.0 (personal dashboard)"
