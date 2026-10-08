# Real-Time Data API Research — Meme Desk Live Dashboard

**Researched:** 2026-10-05 · **Purpose:** feed architecture for the live version of the Meme Desk dashboard
**Rule of thumb used throughout:** every feed gets a primary + a fallback, because free/unofficial crypto APIs break.

---

## Quick decision matrix

| Feed | Primary (recommended) | Fallback | Realtime story |
|---|---|---|---|
| 1. Trending tokens | GeckoTerminal `trending_pools` (keyless) | pump.fun homepage trending via `frontend-api-v3` (unofficial) · Jupiter `toptrending` | Poll 60s |
| 2. Market data (price, mcap, vol, liq, txns) | DexScreener batch `/tokens/v1/solana/{30 mints}` (300 rpm, keyless) | GeckoTerminal token/pool endpoints · Jupiter Price v3 (cheap price-only ticks) | Poll 15–30s |
| 3. Holder distribution | RugCheck `/report` (top 20 + insider nets, cache 5–10 min) | Helius `getTokenLargestAccounts` / DAS (full lists, needs free key) | Poll 5–15 min |
| 4. Token safety | RugCheck (score, risks, mint/freeze, LP lock, insiders) | SolanaTracker `/tokens/{mint}` risk score (keyed) | On demand + cache |
| 5a. FOMO trader leaderboard | SolanaTracker `/pnl/{wallet}` + `/wallet/{owner}` per known wallet | cope.capital proxy API (free unlimited leaderboard reads) | Poll 15–60 min |
| 5b. pump.fun leaderboards | `frontend-api-v3.pump.fun` trending/top-runners (unofficial) | Manual/scheduled snapshot (no public API for leaderboard page) | Poll 5–15 min |
| Live tick feed (bonus) | PumpPortal WebSocket `subscribeTokenTrade` + `subscribeAccountTrade` | Helius webhooks on whale wallets | True push |

---

## 1. GeckoTerminal API

- **Base URL:** `https://api.geckoterminal.com/api/v2`
- **Docs:** `https://apiguide.geckoterminal.com` · OpenAPI at `https://api.geckoterminal.com/docs/index.html`
- **Auth:** none — keyless, no signup.
- **Free tier:** **~30 req/min per IP** (the tightest keyless source on this list). Paid CoinGecko plans raise it to ~500/min.
- **Realtime:** REST polling only. No WebSocket, no webhooks.
- **Versioning:** send `Accept: application/json` (optionally pin `application/json;version=20230302`).
- **Response style:** JSON:API envelope — data lives under `data[].attributes`.

### Key endpoints

```bash
# Trending pools on Solana (what the prototype used)
curl 'https://api.geckoterminal.com/api/v2/networks/solana/trending_pools?include=base_token' \
  -H 'accept: application/json'

# One token's data (price, fdv, top pools)
curl 'https://api.geckoterminal.com/api/v2/networks/solana/tokens/<MINT>' \
  -H 'accept: application/json'

# Batch up to ~30 tokens in one call (use this!)
curl 'https://api.geckoterminal.com/api/v2/networks/solana/tokens/multi/<M1>,<M2>,<M3>' \
  -H 'accept: application/json'

# OHLCV candles for a pool (timeframes: minute|hour|day, aggregate 1/5/15, limit ≤1000)
curl 'https://api.geckoterminal.com/api/v2/networks/solana/pools/<POOL>/ohlcv/hour?aggregate=1&limit=168' \
  -H 'accept: application/json'

# Recent trades on a pool
curl 'https://api.geckoterminal.com/api/v2/networks/solana/pools/<POOL>/trades' \
  -H 'accept: application/json'

# Lightweight price-only lookup
curl 'https://api.geckoterminal.com/api/v2/simple/networks/solana/token_price/<M1>,<M2>' \
  -H 'accept: application/json'
```

**Response fields we care about** (pool): `attributes.price_usd`, `fdv_usd`, `market_cap_usd`, `price_change_percentage.{m5,m15,m30,h1,h6,h24}`, `transactions.h24.{buys,sells,buyers,sellers}`, `volume_usd.h24`, `reserve_in_usd`. OHLCV returns nested arrays `[[ts, o, h, l, c, vol_usd], ...]`, newest first.

**Caveats:** 30 rpm means ~1 call every 2s max — design around batching + a 60s cache; one dashboard refresh should cost ≤3 calls (trending + one batch). Only FDV, no verified circulating-supply mcap. Data lags raw chain by ~1–2 min. Beta flag still on docs, but production-stable in practice; operator is CoinGecko (funded, 10+ yrs).

---

## 2. DexScreener API

- **Base URL:** `https://api.dexscreener.com`
- **Docs:** `https://docs.dexscreener.com/api/reference`
- **Auth:** none — fully public, **no paid tier exists**.
- **Free tier:** **300 req/min** for pair/token/search endpoints · **60 req/min** for token-profiles/boosts/orders/ads endpoints. 429 on exceed, **no `Retry-After` header** — back off manually.
- **Realtime:** REST polling only for market data. A WebSocket exists **only** for token-profiles/boosts/ads metadata — prices and trades are REST-only.
- **Best trait:** batching + highest free rate limit = the dashboard's workhorse for market-data polling.

### Key endpoints

```bash
# Search pairs/tokens (max 30 results, no pagination)
curl 'https://api.dexscreener.com/latest/dex/search?q=Agency'

# ⭐ Batch: top pair data for up to ~30 mints in ONE call (refresh whole watchlist)
curl 'https://api.dexscreener.com/tokens/v1/solana/<M1>,<M2>,<M3>'

# All pairs containing one token (every DEX)
curl 'https://api.dexscreener.com/latest/dex/tokens/<MINT>'

# One specific pair (comma-separate multiple)
curl 'https://api.dexscreener.com/latest/dex/pairs/solana/<PAIR_ADDRESS>'

# Newest token profiles (discovery feed)
curl 'https://api.dexscreener.com/token-profiles/latest/v1'
```

**Response fields we care about:** `priceUsd`, `priceNative`, `fdv`, `marketCap`, `liquidity.{usd,base,quote}`, `volume.{m5,h1,h6,h24}`, `priceChange.{m5,h1,h6,h24}`, `txns.{m5,h1,h6,h24}.{buys,sells}`, `pairCreatedAt`, `baseToken.{name,symbol,address}`, `info.{imageUrl,websites,socials}`.

**Caveats:** no OHLCV/history endpoint (current state only). Search capped at 30 results. Treat `info` metadata (names, socials, images) as untrusted user content. Very reliable uptime, but still cache 15–30s to be polite.

---

## 3. RugCheck API

- **Base URL:** `https://api.rugcheck.xyz`
- **Docs:** no formal public docs; a Swagger UI exists at `https://api.rugcheck.xyz/swagger/index.html`. Community skill docs + our own live usage (Oct 2026 session) confirm the schema below.
- **Auth:** none for read endpoints. Bulk `POST /v1/bulk/tokens/...` endpoints require a Solana-wallet JWT login — skip those.
- **Free tier:** ~**1 req/sec anonymous** (FluxRPC documents 1 rps; community reports ~60/min). Respect 429s; add 2–3s delays in bulk jobs.
- **Realtime:** REST polling only. **Cache 5–10 min per mint** — safety data barely changes.

### Key endpoints

```bash
# Full report (what the prototype used)
curl 'https://api.rugcheck.xyz/v1/tokens/<MINT>/report'

# Lightweight verdict only (cheaper for watchlist sweeps)
curl 'https://api.rugcheck.xyz/v1/tokens/<MINT>/report/summary'
```

**Response fields we care about** (verified live):
- `score`, `score_normalised` — 1 = clean, ~7 = minor warnings, ~60 = dangerous
- `risks[]` — `{ name, level: info|warn|danger, score, description }` (e.g. *"High market cap per holder"*, *"Mutable metadata"*)
- `topHolders[]` — `{ address, pct }`, top ~20 (this is the holder-spread data)
- `totalHolders`
- `markets[]` — per-pool `{ marketType, pubkey, liquidityA/B, lpLockedPct }` ← LP-lock status lives here
- `tokenAuthorities` → `mintAuthority`, `freezeAuthority` (null = safe)
- `insiderNetworks[]` — `{ id, size, tokenAmount, ... }` ← cluster/insider detection (statistical heuristic, false positives happen)
- `fileMeta` → `{ name, symbol, mutable }`
- `transferFee.transferFeeBasisPoints` (Token-2022 tax, e.g. 100 = 1% — the SI case)
- `transferHook.authority` (present on PUMP — flag it)
- `creator`, `creatorBalance`

**Caveats:** community-run project, no SLA; endpoints/fields can shift without notice. Insider-network counts are heuristic — present as "detected clusters", not proof. Does **not** give the full paginated holder list (top 20 only) — use Helius/Moralis for that. Note: `tokenAmount` inside `insiderNetworks` can exceed JS safe-integer range; treat as string/bigint.

---

## 4. pump.fun — official & unofficial APIs

**There is no official public pump.fun API with docs.** Everything below is reverse-engineered from the frontend. It works today and is widely used, but it's the least contractually stable source on this list.

### 4a. `frontend-api.pump.fun` (v1, what the site historically used) — keyless

```bash
# Newest coins
curl 'https://frontend-api.pump.fun/coins?limit=50&offset=0&sort=created_timestamp&order=DESC'

# Trending-ish (by last trade)
curl 'https://frontend-api.pump.fun/coins?sort=last_trade_timestamp&order=DESC&limit=50'

# One coin's metadata (mcap, bonding-curve progress, KOTH status…)
curl 'https://frontend-api.pump.fun/coins/<MINT>'

# Recent trades for a coin
curl 'https://frontend-api.pump.fun/trades/all/<MINT>?limit=200'
```

### 4b. `frontend-api-v3.pump.fun` (current frontend version) — keyless

```bash
curl 'https://frontend-api-v3.pump.fun/coins/top-runners'   # trending
curl 'https://frontend-api-v3.pump.fun/coins/recommended'   # recommended/new
```

### 4c. Realtime trade feed (WebSocket) — via PumpPortal (third party, see §5)

**Caveats:** endpoints migrate between versions (v1 → v3 happened without announcement); rate limiting is enforced but unpublished; no SLA. Use pump.fun APIs for *discovery/trending flavor*, always cross-check prices against DexScreener/GeckoTerminal.

---

## 5. PumpPortal (pump.fun data + trading infra, third party)

- **Docs:** `https://pumpportal.fun/data-api/real-time/`
- **WebSocket:** `wss://pumpportal.fun/api/data` — **free, no auth** (docs also show optional `?api-key=`).
- **Subscriptions** (send JSON over the socket):
  - `{"method":"subscribeNewToken"}` — every new coin creation (mint, creator, bonding-curve reserves, metadata URI)
  - `{"method":"subscribeTokenTrade","keys":["<MINT>",...]}` — all buys/sells on watched tokens (txType, solAmount, tokenAmount, traderPublicKey, marketCapSol, reserves → derive live price)
  - `{"method":"subscribeAccountTrade","keys":["<WALLET>",...]}` — **every trade by a watched wallet = live whale feed**
  - `{"method":"subscribeMigration"}` — bonding-curve graduation events
- **⚠️ Critical rule:** **one WebSocket connection for ALL subscriptions.** Multiple connections → hourly IP ban.
- Trading endpoints exist (`POST /api/trade?api-key=`, 0.5% fee) — not needed for the dashboard.
- **Caveats:** third-party dependency (not pump.fun itself); review ToS before production; needs reconnect/outage handling. Alternative WS: `wss://pumpdev.io/ws` (PumpDev, also free, same three subscription methods).

---

## 6. SolanaTracker Data API (powers the FOMO leaderboard page)

- **Base URL:** `https://data.solanatracker.io` · **Docs:** `https://docs.solanatracker.io` · header `x-api-key: <KEY>`
- **Pricing (EUR):** Free **€0** = 10,000 req/month, 3 req/sec · Advanced €50 = 200K · Pro €200 = 1M · Premium €397 = 10M **+ WebSocket Datastream** (20+ rooms: live prices, trades, launches, wallet activity, holder updates). No WS below Premium.
- **The FOMO leaderboard page itself (`solanatracker.io/leaderboard/fomo`) has NO documented public API.** Rebuild it from these:

```bash
H="x-api-key: $SOLANATRACKER_API_KEY"

# Wallet PnL — realized/unrealized, win %, volume (the leaderboard's columns)
curl -H "$H" 'https://data.solanatracker.io/pnl/<WALLET>'
# → summary: realized, unrealized, total, totalInvested, winPercentage, totalWins/Losses…

# Wallet holdings (whale-consensus feed: what is frank holding right now?)
curl -H "$H" 'https://data.solanatracker.io/wallet/<WALLET>'

# Wallet trade history
curl -H "$H" 'https://data.solanatracker.io/wallet/<WALLET>/trades'

# Token page: metadata + pools + risk score /10 + holders summary
curl -H "$H" 'https://data.solanatracker.io/tokens/<MINT>'

# Trending by volume (5m|15m|30m|1h|4h|12h|24h)
curl -H "$H" 'https://data.solanatracker.io/tokens/trending/1h'

# Prices (batch)
curl -H "$H" 'https://data.solanatracker.io/price/multi?tokens=<M1>,<M2>'
curl -H "$H" 'https://data.solanatracker.io/price?token=<MINT>&priceChanges=true'

# OHLCV incl. 1-second resolution (unique feature)
curl -H "$H" 'https://data.solanatracker.io/chart/<MINT>?type=1m&time_from=<UNIX>&time_to=<UNIX>'
```

**Free-tier math for the whale-consensus feed:** 10 tracked wallets × `/pnl` + `/wallet` = 20 calls/refresh. Free 10K/mo ≈ 333/day ≈ **hourly refreshes fit** (240/day); 15-min refreshes don't. Advanced (€50) removes the worry.

**Caveats:** needs a free API key (signup). No leaderboard endpoint — you own the ranking logic. Datastream WS (the true realtime path) starts at €397/mo.

---

## 7. fomo.family

**The official fomo.family API is NOT usable server-side.** Community researchers confirm: Cloudflare rejects every non-browser client at the edge with `HTTP 430 {"error":"unauthorized"}` — including exact browser-header replays. Privy session tokens rotate hourly. Scraping = fragile + against their ToS posture.

### Workarounds (third-party proxies — evaluate carefully)

**Option A — cope.capital API** (cleanest documented proxy)
- `POST https://api.cope.capital/v1/register` `{"agent_name":"..."}` → free `cope_...` key, no signup
- `GET /v1/leaderboard?timeframe=24h|7d|30d|all&limit=N` — **free, unlimited**
- `GET /v1/traders/search?min_win_rate=75&min_trades=10&sort_by=pnl` — free
- `GET /v1/activity/poll?since=<ts>` — free (efficient heartbeat); `GET /v1/activity` — 250 calls/day free, then x402 pay-per-call ($0.005 USDC)
- Docs: `https://api.cope.capital/docs`

**Option B — fomoapi.io** — HTTP proxy of fomo data; free key, ~1,000 credits/month.

**Caveats:** both are third parties re-selling/scraping fomo data — no SLA, could vanish; verify a few rows against the live leaderboard before trusting. For the dashboard, prefer SolanaTracker `/pnl` (first-party data, §6) and treat fomo proxies as the social-identity layer (handles, followers).

---

## 8. Birdeye API

- **Base:** `https://public-api.birdeye.so` · **Docs:** `https://docs.birdeye.so` · headers `X-API-KEY` + `x-chain: solana`
- **Pricing:** Free **$0** = 30K CU/month, 1 rps · Lite $39 = 1.5M CU/15 rps · Starter $99 = 5M · Premium $199 = 15M/50 rps · **Premium Plus $250** = 20M + **WebSocket** · Business $499+
- **WebSocket** (Premium Plus+): `wss://public-api.birdeye.so/socket/solana?x-api-key=KEY` — channels: `SUBSCRIBE_PRICE`, `SUBSCRIBE_TXS`, `SUBSCRIBE_TOKEN_NEW_LISTING`, `SUBSCRIBE_NEW_PAIR`, `SUBSCRIBE_LARGE_TRADE_TXS`, `SUBSCRIBE_WALLET_TXS`, `SUBSCRIBE_TOKEN_STATS`. Max 100 tokens/connection.
- **Key endpoints:** `GET /defi/token_overview` (price, vol, holders, mcap in one shot), `/defi/price`, `/defi/ohlcv`, `/defi/token_security`, `/defi/v3/token/holder` (holder list), `/v1/wallet/token_list`, `/wallet/v2/pnl`.
- **Verdict for this project:** the free tier (30K CU ≈ ~750 price calls/**month**) is unusable for a live dashboard. Excellent data depth, but only makes sense at Lite ($39) or higher. **Not recommended as primary; optional paid upgrade later.**

---

## 9. Helius (Solana-native infra — best free on-chain data)

- **Base:** `https://mainnet.helius-rpc.com/?api-key=<KEY>` (RPC + DAS + Enhanced multiplexed on one URL) · **Docs:** `https://docs.helius.dev`
- **Pricing:** Free **$0** = **1M credits/month**, 10 RPS · Developer $49 = 10M/50 RPS · Business $499 = 100M/200 RPS. Credit costs: standard RPC = 1, **DAS = 10**, Enhanced tx = 100, **webhook event delivered = 1**.
- **Why it matters for the dashboard:**
  - `getTokenLargestAccounts` (1 credit) → **full top-holder list** (RugCheck only gives top 20)
  - `getProgramAccountsV2` (1 credit, cursor-paginated) → full holder enumeration
  - DAS `getAssetsByOwner({ownerAddress, displayOptions:{showFungible:true}})` (10 credits) → **whale wallet portfolios** (rebuild "what is frank holding" trustlessly)
  - **Webhooks** (create via API, 1 credit/event) → subscribe to the 10 whale wallets → **push-based whale-trade alerts**, no polling
- **Free-tier math:** 10 whales × `getAssetsByOwner` (10 cr) = 100 credits/hourly refresh → ~72K/month. Comfortable. Webhooks at 1 credit/event are nearly free until whales trade a lot.
- **Verdict:** **the most generous free tier for on-chain holder + whale data.** Free key requires signup (email). Recommended as the holder-distribution primary alongside RugCheck, and as the whale-alert push mechanism.

---

## 10. Jupiter Price API v3 (+ Tokens API)

- **Base:** `https://api.jup.ag/price/v3` · **Docs:** `https://developers.jup.ag`
- **Auth:** keyless at **0.5 RPS** (30/min); free API key → 1 RPS; Developer $25/mo → 10 RPS.
- **Price (the cheap tick feed):**

```bash
# Up to 50 mints per call — one call refreshes the whole watchlist's prices
curl 'https://api.jup.ag/price/v3?ids=<M1>,<M2>,<M3>'
# → { data: { "<MINT>": { price, confidenceLevel } } }
```

- **Trending discovery:** `GET https://api.jup.ag/tokens/v2/toptrending/24h` (also `toporganicscore`, `toptraded`; intervals `5m|1h|6h|24h`), `GET /tokens/v2/search?query=...`, `GET /tokens/v2/recent`.
- **Caveats:** prices only (no volume/liquidity/txns); low-confidence tokens return `null` (fail closed). Perfect as a **cheap price-tick layer** between heavier DexScreener refreshes.

---

## 11. Moralis Solana API

- **Base:** `https://solana-gateway.moralis.io` · header `X-API-Key` · **Docs:** `https://docs.moralis.com`
- **Free tier:** ~40K CU/day (community-reported; verify at signup). Paid from ~$49–149/mo.
- **Standout endpoints for this dashboard:**
  - Token holder stats → `totalHolders`, `holderChange` (5m→30d), `holderDistribution` (whales/sharks/dolphins/… buckets) — a nicer holder summary than raw lists
  - Token price, swaps/pairs, liquidity, volume stats
  - pump.fun-specific: `/token/mainnet/exchange/pumpfun/bonding` (pre-graduation) and `/graduated` — native pump.fun discovery
  - Wallet balances + portfolio
- **Caveats:** CU costs per endpoint add up fast; free tier is dev-grade. Overlaps Helius (which is cheaper/free-er for pure on-chain reads). Consider only if the holder-distribution buckets or pump.fun endpoints prove uniquely useful in testing.

---

## Suggested feed architecture (v1, all-free)

```
┌─ Poll 60s ──────────────────────────────────────────────┐
│ Trending: GeckoTerminal trending_pools (keyless, ~1 call) │
│         + pump.fun top-runners (unofficial, ~1 call)      │
└──────────────────────────────────────────────────────────┘
┌─ Poll 20s ──────────────────────────────────────────────┐
│ Market data: DexScreener /tokens/v1/solana/{30 mints}     │
│              (1 call refreshes whole watchlist @300 rpm)  │
│ Ticks: Jupiter price/v3?ids={50 mints} (0.5 RPS keyless)  │
└──────────────────────────────────────────────────────────┘
┌─ Poll 5–10 min (cached) ────────────────────────────────┐
│ Safety+holders: RugCheck /report per mint (1 rps, cache) │
│ Holders deep: Helius getTokenLargestAccounts (free key)  │
└──────────────────────────────────────────────────────────┘
┌─ Poll 15–60 min ────────────────────────────────────────┐
│ Whale consensus: SolanaTracker /pnl + /wallet per wallet │
│                  (free tier → hourly; €50 → 15-min)       │
│ FOMO social: cope.capital /v1/leaderboard (free)         │
└──────────────────────────────────────────────────────────┘
┌─ Push (no polling) ─────────────────────────────────────┐
│ Live tape: PumpPortal WS subscribeTokenTrade (watchlist) │
│            + subscribeAccountTrade (whale wallets)        │
│ Whale alerts: Helius webhooks on 10 wallets (1 cr/event) │
└──────────────────────────────────────────────────────────┘
```

**Estimated free-tier headroom:** this design stays inside every free limit (GeckoTerminal 30/min, DexScreener 300/min, RugCheck 1/sec, Jupiter 0.5/sec keyless, Helius 1M credits/mo, SolanaTracker 10K req/mo at hourly whale refreshes).

**First paid upgrade when it hurts:** Helius Developer ($49/mo, 10M credits) or SolanaTracker Advanced (€50/mo, 200K req) — whichever feed the user refreshes most. Birdeye only if its token_security/holder depth proves irreplaceable in testing.

---

## Risks & gotchas (read before building)

1. **GeckoTerminal's 30 req/min is the binding constraint** on the keyless stack. One unbatched loop (e.g. per-token OHLCV per refresh) will 429 the whole dashboard. Always batch (`tokens/multi`, DexScreener `/tokens/v1`), always cache.
2. **Unofficial endpoints have no contract.** `frontend-api.pump.fun` already migrated v1→v3 silently; RugCheck has no versioned public docs; fomo.family Cloudflare-blocks all non-browser clients (HTTP 430). Every unofficial source needs a fallback provider and a visible "stale data" state in the UI.
3. **The FOMO leaderboard has no public API** — neither solanatracker.io's page nor fomo.family's. Rebuild rankings from SolanaTracker `/pnl` (first-party, keyed) or the cope.capital proxy (third-party, free). Budget for this in the data model from day one.
4. **Free tiers that look generous but aren't:** Birdeye free = ~750 price calls/**month** (useless for live); SolanaTracker free = hourly whale refreshes max. Helius free (1M credits) is the only genuinely dashboard-grade free tier.
5. **RugCheck insider data is heuristic**, not ground truth — label it "detected clusters". And never call a token "safe" off a clean report; the prototype's own notes already say this.
6. **PumpPortal's one-connection rule** — multiplex all WS subscriptions on a single socket or face hourly IP bans. Put the WS client in the backend, not in each browser tab.
7. **ToS fine print:** DexScreener/GeckoTerminal tolerate dashboard use; fomo.family actively blocks programmatic access; pump.fun's frontend API is "tolerated". If this becomes a public product (not a personal dashboard), re-check each ToS and expect to pay for SolanaTracker/Birdeye tiers.
