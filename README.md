
# Meme Desk

Live, real-time investigation dashboard for Solana memecoins. Answers *"what's actually moving right now"* — before the lagging trending lists catch it.

![Meme Desk dashboard](<img width="1440" height="900" alt="memedesk-dashboard" src="https://github.com/user-attachments/assets/c8349e67-e97e-4c2f-91fb-9bb64f129bf5" />)


## What it shows

- **Heating up** — early-momentum board built from our own market-poll time series. A coin only qualifies with **+3% in 30 minutes**, **≥ $20K liquidity**, **≥ $50K 24h volume**. (~35 min warmup after a backend restart.)
- **Trending now** — GeckoTerminal trending pools, enriched with DexScreener market data: price, 24h change, volume, liquidity, mcap.
- **Regime strip** — BTC vs the $87K wall, SOL, and PUMP, with a desk read.
- **Watchlist** — seed universe with live prices.
- Every token name links out to its chart — **GeckoTerminal first, DexScreener fallback**.

## Design

UI normalized to the [shadcn/ui](https://ui.shadcn.com) design system (dark theme tokens, card / table / badge / alert patterns).

## Stack

- **Backend:** Python / FastAPI — asyncio poll loops, TTL cache with stale flags, resilient scheduler
- **Frontend:** React + Vite
- **Data (all keyless, read-only):** GeckoTerminal · DexScreener · Jupiter · CoinGecko

## Poll cadence

| Feed | Interval |
|---|---|
| GeckoTerminal trending | 60s |
| DexScreener market batch | 25s |
| Jupiter price ticks | 12s |
| Regime (CoinGecko + PUMP) | 60s |
| GeckoTerminal index check | 10 min |

## Quickstart

```bash
# backend
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8000

# frontend
cd frontend && npm install && npm run build   # serves from backend at /
# or: npm run dev                              # local dev
```

API: `GET /health`, `/api/trending`, `/api/movers`, `/api/token/{mint}`, `/api/regime`, `/api/watchlist`

## Deploy

Runs as a systemd service behind Tailscale Serve on a `/memedesk` subpath (additive — the existing root dashboard is untouched). The backend strips the `/memedesk` prefix itself and serves the built frontend from `frontend/dist`.

## Status

Personal build v0.1 — **read-only**: no wallet connection, no trade execution. Alerts deferred past v1. Auth is pluggable and data is user-keyed in case it's ever shared or sold.
