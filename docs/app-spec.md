# Meme Desk — Live Dashboard App Spec v0.1

**Status:** draft · **Date:** 2026-10-08 · **Author:** Muse (for user review)
**Inputs:** `meme-desk-2026-10-05.html` (static prototype), `api-sources.md` (feed research), `regime-strip.html` (macro widget), initial watchlist universe (2026-10-08).

---

## 1. What this is

A personal, real-time investigation dashboard for Solana memecoins. It answers one question fast: **"what's hot, who's buying it, and is it safe to touch?"**

It is *not* a trading bot, *not* a public product (v1), and *not* financial advice. Single user. Read-only — no wallet connection, no trade execution in v1.

## 2. Views

### 2.1 Today (home)
The money view. One screen, four panels:
- **Regime strip** — macro context. Reuse the existing `regime-strip.html` widget: BTC vs the $87k level, BTC/SOL/PUMP 24h data, weekly ETF snapshot. (Already built and verified; integrate as-is.)
- **Triple-signal board** — tokens scoring on 2+ of: trending by volume, held by tracked whales, top-called on pump.fun. This is the highest-conviction surface in the product.
- **Trending now** — live trending tokens (cards/table): price, mcap/FDV, 24h change, 24h volume, 24h txns, liquidity.
- **Whale tape** — live trade feed from tracked wallets (frank, Theo, Swizzle, dreamloader, point farm capital, etc.), newest first.

### 2.2 Token detail (drill-down from any token)
- Price chart — embed DexScreener/GeckoTerminal chart iframe (v1; custom candles later via GeckoTerminal OHLCV).
- Market stats: price, mcap, FDV, 24h change/vol/txns, liquidity, pool, DEX.
- **Safety panel** (RugCheck): score, risk list, mint/freeze authorities, per-pool LP-lock %, insider-cluster count, transfer fee / transfer hook flags. Never labels a token "safe" — shows the raw signals.
- **Holder panel**: holder count, top-holder concentration bar, top 10 holders table, whale-holder callouts (flags when a tracked whale is in the holder list).
- Research links: DexScreener, GeckoTerminal, RugCheck, pump.fun, FOMO leaderboard.

### 2.3 Whales
- FOMO leaderboard table (rebuilt from SolanaTracker per-wallet PnL): trader, handle, realized PnL, win rate, trades. Wallet addresses click-to-copy.
- **Consensus matrix**: which tracked whales hold which tokens, position sizes, recent buy/sell flow. Overlap = the signal.
- Per-whale detail: holdings, recent trades, PnL.

### 2.4 Leaderboards (pump.fun)
- Traders, squads, best callouts, kill-cam highlights — via unofficial pump.fun endpoints + cope.capital proxy.
- Every panel from an unofficial source carries a **visible "stale / unofficial" state** when its feed is down or outdated.

### 2.5 Watchlist
- User-curated token list, persisted. Seed with the initial universe (whale-consensus + trending + callout names, Oct 2026).
- One-click add from any token card. Backend keeps market data warm for watchlist mints.

## 3. Data architecture

One backend owns all third-party polling. The frontend talks only to the backend. Rationale: rate limits are per-IP/key — a backend centralizes the budget and keeps secrets server-side; the PumpPortal WebSocket *must* live in the backend (one multiplexed connection or hourly IP ban).

### 3.1 Feed map (from `api-sources.md` — all free tier, v1)

| Feed | Source | Cadence | Notes |
|---|---|---|---|
| Trending tokens | GeckoTerminal `trending_pools` | 60s | Keyless; 30 req/min is the binding constraint — batch + cache |
| Market data (price, mcap, vol, liq, txns) | DexScreener `POST/GET /tokens/v1/solana/{≤30 mints}` | 20–30s | One call refreshes whole watchlist @300 rpm |
| Price ticks between refreshes | Jupiter Price v3 `?ids={≤50}` | 10–15s | Keyless 0.5 RPS; prices only |
| Token safety | RugCheck `/v1/tokens/{mint}/report` | On demand + 10-min cache | ~1 rps; score, risks, LP locks, mint/freeze, insiders, fees |
| Holder distribution | RugCheck top-20 + Helius `getTokenLargestAccounts` | 5–15 min | Helius free: 1M credits/mo |
| Whale consensus | SolanaTracker `/pnl/{wallet}` + `/wallet/{wallet}` | 60 min (free tier) | 10 wallets × 2 calls; €50 tier → 15-min |
| FOMO social layer | cope.capital `/v1/leaderboard` | 15 min | Free, unofficial proxy |
| pump.fun boards | `frontend-api-v3.pump.fun` trending/top-runners | 5–15 min | Unofficial; fallback + stale badge required |
| **Live tape (push)** | **PumpPortal WS** `subscribeTokenTrade` (watchlist) + `subscribeAccountTrade` (whale wallets) | real-time | Free, no auth; **single backend connection** |
| Whale alerts (push) | Helius webhooks on tracked wallets | event-driven | ~1 credit/event; nearly free |

### 3.2 Backend responsibilities
- Central scheduler with per-source rate-limit buckets; batch-first fetching.
- Cache layer (in-memory + SQLite/Postgres): TTLs per feed per the table above.
- PumpPortal WS client: single connection, multiplexed subscriptions, auto-reconnect with backoff, outage → tape shows "reconnecting".
- Snapshot store: periodic snapshots of trending/leaderboard state (powers "what changed since yesterday" later).
- REST API for the frontend: `/api/trending`, `/api/token/{mint}`, `/api/whales`, `/api/whale/{wallet}`, `/api/leaderboards`, `/api/watchlist` (CRUD), `/api/regime`.

### 3.3 Frontend responsibilities
- Polls backend only (5–15s for tape/prices, 60s+ for the rest).
- Renders all views above; handles stale/loading/error states per panel.
- No API keys in the browser. Ever.

## 4. Tech stack (recommended)

- **Backend:** Node.js (Fastify or Express) — best fit for the multiplexed WebSocket client and JSON-heavy polling. Alternative: Python/FastAPI if preferred; the user decides.
- **Frontend:** React (Vite) + a charting lib (lightweight-charts) — or start with DexScreener/GeckoTerminal embeds and upgrade later.
- **Store:** SQLite for v1 (watchlist, snapshots, cache overflow); Postgres if it outgrows that.
- **Hosting:** the user's **Atlas VPS** (already owned, persistent) is the natural home for the always-on backend (WS + scheduler need a persistent process). Frontend can be served from the same box or a static host.
- **No wallet integration, no trade execution in v1.** (PumpPortal trading endpoints exist but are explicitly out of scope.)

## 5. Rate-limit budget (sanity check)

The v1 design stays inside every free tier: GeckoTerminal ≤30/min (we use ~3/min), DexScreener ≤300/min (we use ~3/min), RugCheck ~1/sec with caching, Jupiter 0.5/sec keyless, Helius 1M credits/mo (whale refreshes ≈ 72K/mo), SolanaTracker 10K req/mo at hourly whale refreshes. First paid upgrade when it hurts: Helius Developer $49/mo or SolanaTracker Advanced €50/mo.

## 6. Milestones

- **M0 — Skeleton + trending:** backend scheduler, GeckoTerminal + DexScreener polling, Today view with trending + regime strip.
- **M1 — Token detail:** RugCheck safety + holder panels, chart embed, research links.
- **M2 — Whales:** FOMO leaderboard rebuild, consensus matrix, PumpPortal live tape, Helius whale alerts.
- **M3 — Boards + watchlist:** pump.fun leaderboard panels, watchlist CRUD + persistence, snapshot history ("new since yesterday").

## 7. Decisions (locked 2026-10-08)

1. Backend language: **Python (FastAPI)** — user's pick. Async throughout; WebSocket client via `websockets`, scheduler via `asyncio`/`apscheduler`.
2. Hosting: **everything on the Atlas VPS, served via Caddy** (already installed). Backend + frontend on one box; Caddy as reverse proxy / TLS.
3. Alerts: **deferred** past v1.
4. Audience: **personal for now, but may be sold as a digital asset later.** Build implications:
   - Keep auth pluggable: single-user mode now (simple token gate), structured so per-user accounts can be added without re-architecting.
   - No hard-coded single-user assumptions in the data layer (watchlists, snapshots keyed by user id from day one, even if there's only one user).
   - Mind provider ToS: the free-tier posture in §5 is fine for personal use; a sold product will need paid SolanaTracker/Birdeye tiers and a ToS re-check per `api-sources.md` risk #7. Note the upgrade path in code comments where unofficial sources are used.

---

## Appendix: source files

- Prototype: `~/workspace/your_files/meme-desk-2026-10-05.html`
- Feed research: `~/workspace/crypto-dash-research/api-sources.md`
- Regime widget: `~/workspace/crypto-dash-research/regime-strip.html` (+ `macro-regime-tile.md`)
- Watchlist universe: defined in chat 2026-10-08 (whale-consensus + trending + callout names; contracts for pill/fone/ZCAT/OCTO/COCKROACH/ALLINU/e/acc still unverified)
