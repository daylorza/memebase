"""Early-momentum detection: coins heating up BEFORE they hit the trending list.

GeckoTerminal trending_pools is a lagging list — by the time a coin trends
there, the first leg is usually done. This module keeps a short in-memory
time series from our own market polls and scores recent acceleration:
30-minute price return, gated on real liquidity and real volume.

In-memory only: a restart wipes history and the feed reports warming_up
until ~35 minutes of samples accumulate. Acceptable for v1.
"""

import time
from collections import deque

SERIES_MAXLEN = 240      # ~100 min at 25s polls
LOOKBACK_S = 30 * 60     # momentum window
WARMUP_S = 35 * 60       # minimum history before a mint can qualify
MIN_LIQ_USD = 20_000
MIN_VOL_H24_USD = 50_000
MIN_RET_30M = 0.03       # +3% in 30 min to make the board
TOP_N = 12

_series: dict[str, deque] = {}


def record(market: dict[str, dict]) -> None:
    """Append one snapshot per mint. Called from the market poll loop."""
    now = time.time()
    for mint, m in (market or {}).items():
        price = m.get("price_usd")
        if not mint or price is None:
            continue
        dq = _series.get(mint)
        if dq is None:
            dq = _series[mint] = deque(maxlen=SERIES_MAXLEN)
        dq.append((now, price, m.get("volume_h24"), m.get("liquidity_usd"), m.get("market_cap")))


def _sample_at_least(dq: deque, age_s: float):
    """Newest sample at least age_s old; None when history is too short."""
    now = time.time()
    best = None
    for s in dq:  # oldest -> newest
        if now - s[0] >= age_s:
            best = s
        else:
            break
    return best


def warming_up() -> bool:
    return not any(
        dq and dq[-1][0] - dq[0][0] >= WARMUP_S for dq in _series.values()
    )


def compute(market: dict[str, dict]) -> list[dict]:
    """Rank mints by 30-minute price return. Returns top TOP_N dicts."""
    out = []
    for mint, dq in _series.items():
        if len(dq) < 2 or dq[-1][0] - dq[0][0] < WARMUP_S:
            continue
        old = _sample_at_least(dq, LOOKBACK_S)
        if old is None:
            continue
        _, price_now, vol_now, liq_now, mcap_now = dq[-1]
        _, price_old, vol_old, _, _ = old
        if not price_old or price_old <= 0:
            continue
        if (liq_now or 0) < MIN_LIQ_USD or (vol_now or 0) < MIN_VOL_H24_USD:
            continue
        ret = price_now / price_old - 1
        if ret < MIN_RET_30M:
            continue
        m = (market or {}).get(mint) or {}
        vol_growth = (vol_now - (vol_old or 0)) / (vol_old or 1)
        out.append(
            {
                "mint": mint,
                "symbol": m.get("symbol"),
                "name": m.get("name"),
                "price_usd": price_now,
                "ret_30m": ret,
                "vol_growth_30m": vol_growth,
                "change_h24": m.get("change_h24"),
                "volume_h24": vol_now,
                "liquidity_usd": liq_now,
                "market_cap": mcap_now,
                "dex": m.get("dex"),
            }
        )
    out.sort(key=lambda d: d["ret_30m"], reverse=True)
    return out[:TOP_N]
