# Meme Desk

Live, real-time investigation dashboard for Solana memecoins. Answers one question fast:
**what's hot, who's buying it, and is it safe to touch?**

Personal project (v1). Read-only — no wallet connection, no trade execution.

## Spec & research

- [`docs/app-spec.md`](docs/app-spec.md) — product spec v0.1: views, feed map, architecture, milestones M0–M3
- [`docs/api-sources.md`](docs/api-sources.md) — real-time data API research (endpoints, rate limits, fallbacks)

## Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌──────────────┐
│  Frontend   │─────▶│  Backend (FastAPI)│─────▶│ Third-party  │
│  (React)    │◀─────│  poller + cache   │      │ APIs / WS    │
└─────────────┘      │  + PumpPortal WS  │      └──────────────┘
                     └──────────────────┘
```

The backend owns all third-party polling (rate limits are per-IP/key) and the
single multiplexed PumpPortal WebSocket connection. The frontend talks only to
the backend. Deployed on Atlas VPS behind Caddy.

## Quickstart (backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000/health
```

## Milestones

- **M0** — Skeleton + trending: scheduler, GeckoTerminal + DexScreener polling, Today view
- **M1** — Token detail: RugCheck safety + holder panels, chart embed
- **M2** — Whales: FOMO leaderboard rebuild, consensus matrix, live tape, whale alerts
- **M3** — Boards + watchlist: pump.fun panels, watchlist CRUD, snapshot history

## Decisions (locked)

- Backend: Python / FastAPI · Hosting: Atlas VPS + Caddy · v1 alerts: deferred
- Personal for now; may be sold later → auth pluggable, user-keyed data from day one
