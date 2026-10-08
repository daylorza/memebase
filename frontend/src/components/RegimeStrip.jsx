import { fmtUsd, fmtPct, timeAgo } from '../api.js'

const STATE_LABEL = { broken: 'WALL BROKEN ▲ $87K', pinned: 'PINNED BELOW $87K', bear: 'BELOW $84K — BEAR TRIGGER' }

export default function RegimeStrip({ payload }) {
  if (!payload) return <div className="panel"><p className="dim">Loading regime…</p></div>
  const d = payload.data
  if (!d) return (
    <div className="panel">
      <div className="panel-head"><h2>Regime</h2><span className="stale">● STALE</span></div>
      <p className="dim">No regime data yet — backend is warming up.</p>
    </div>
  )
  const btc = d.btc || {}, sol = d.sol || {}, pump = d.pump || {}
  const etf = d.etf_snapshot || {}
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Regime</h2>
        {payload.stale
          ? <span className="stale" title={'last update ' + timeAgo(payload.fetched_at)}>● STALE</span>
          : <span className="fresh" title={'updated ' + timeAgo(payload.fetched_at)}>● live</span>}
      </div>
      <div className="tiles">
        <div className="tile">
          <div className="label">BTC · vs $87k wall</div>
          <div className="price">{btc.price != null ? '$' + Math.round(btc.price).toLocaleString() : '—'} <span className={btc.change_24h >= 0 ? 'up' : 'down'}>{fmtPct(btc.change_24h)}</span></div>
          <div className={'state ' + (btc.state || '')}>{STATE_LABEL[btc.state] || '—'}</div>
          <div className="sub">{btc.dist_to_wall_pct != null ? Math.abs(btc.dist_to_wall_pct).toFixed(2) + '% ' + (btc.dist_to_wall_pct >= 0 ? 'below' : 'above') + ' the wall' : '—'}</div>
        </div>
        <div className="tile">
          <div className="label">SOL · 24h</div>
          <div className="price">{sol.price != null ? '$' + sol.price.toFixed(2) : '—'} <span className={sol.change_24h >= 0 ? 'up' : 'down'}>{fmtPct(sol.change_24h)}</span></div>
          <div className="sub">CoinGecko · keyless</div>
        </div>
        <div className="tile">
          <div className="label">PUMP · 24h</div>
          <div className="price">{pump.price != null ? '$' + pump.price.toFixed(6) : '—'} <span className={pump.change_24h >= 0 ? 'up' : 'down'}>{fmtPct(pump.change_24h)}</span></div>
          <div className="sub">liq {fmtUsd(pump.liquidity_usd, 0)} · vol {fmtUsd(pump.volume_h24, 0)}</div>
        </div>
        <div className="tile wide">
          <div className="label">Desk read</div>
          <div className="read">{d.read || '—'}</div>
          {!etf.live && <div className="sub">ETF flows are a weekly snapshot ({etf.as_of}), not live.</div>}
        </div>
      </div>
    </div>
  )
}
