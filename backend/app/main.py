"""Meme Desk backend — M0 skeleton.

Single rule: the frontend talks only to this backend. All third-party
polling (GeckoTerminal, DexScreener, RugCheck, ...) lives here so rate
limits are managed in one place.
"""

from fastapi import FastAPI

app = FastAPI(title="Meme Desk", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "version": "0.1.0"}


@app.get("/api/trending")
def trending() -> dict:
    # M0: wire to GeckoTerminal trending_pools (see docs/api-sources.md §1)
    return {"data": [], "stale": True, "note": "not wired yet — M0"}


@app.get("/api/regime")
def regime() -> dict:
    # Serves the data behind the regime-strip widget.
    return {"data": None, "stale": True, "note": "not wired yet — M0"}
