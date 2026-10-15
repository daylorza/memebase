import { fmtPrice, fmtPct, fmtUsd, timeAgo } from '../api.js'

export default function MoversPanel({ payload }) {
  if (!payload) return <div className="panel"><p className="dim">Loading movers…</p></div>
  const rows = payload.data || []
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Heating up <span className="dim" style={{ fontWeight: 'normal' }}>· early momentum, 30m</span></h2>
        <span className="fresh">● live</span>
      </div>
      {payload.warming_up ? (
        <p className="dim">Collecting price history — the early-momentum board goes live after ~35 minutes of data. Check back soon.</p>
      ) : rows.length === 0 ? (
        <p className="dim">Nothing moving +3% in the last 30 minutes with real liquidity. Quiet tape.</p>
      ) : (
        <table>
          <thead>
            <tr><th>#</th><th>Token</th><th>Price</th><th>30m</th><th>24h</th><th>24h Vol</th><th>Liquidity</th><th>Mcap</th></tr>
          </thead>
          <tbody>
            {rows.map((t, i) => {
              const tokenCell = (
                <><b>{t.symbol || '?'}</b> <span className="dim">{t.name || ''}</span></>
              )
              return (
                <tr key={t.mint || i}>
                  <td className="dim">{i + 1}</td>
                  <td>{t.chart_url ? (
                    <a className="token-link" href={t.chart_url} target="_blank" rel="noopener noreferrer" title="Open chart">{tokenCell}</a>
                  ) : tokenCell}</td>
                  <td className="num">{fmtPrice(t.price_usd)}</td>
                  <td className="num"><span className={'badge ' + (t.ret_30m >= 0 ? 'badge-up' : 'badge-down')}>{fmtPct(t.ret_30m * 100)}</span></td>
                  <td className="num"><span className={'badge ' + ((t.change_h24 ?? 0) >= 0 ? 'badge-up' : 'badge-down')}>{fmtPct(t.change_h24)}</span></td>
                  <td className="num">{fmtUsd(t.volume_h24, 0)}</td>
                  <td className="num">{fmtUsd(t.liquidity_usd, 0)}</td>
                  <td className="num">{fmtUsd(t.market_cap, 0)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
      <p className="foot">Our own 30-minute momentum read · liquidity ≥ $20K · volume ≥ $50K · updated {timeAgo(payload.fetched_at)}</p>
    </div>
  )
}
