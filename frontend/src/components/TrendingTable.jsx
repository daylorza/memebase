import { fmtPrice, fmtPct, fmtUsd, timeAgo } from '../api.js'

function Stale({ stale, fetchedAt }) {
  if (!stale) return <span className="fresh" title={'updated ' + timeAgo(fetchedAt)}>● live</span>
  return <span className="stale" title={'last update ' + timeAgo(fetchedAt)}>● STALE</span>
}

export default function TrendingTable({ payload }) {
  if (!payload) return <div className="panel"><p className="dim">Loading trending…</p></div>
  const rows = payload.data || []
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Trending now</h2>
        <Stale stale={payload.stale} fetchedAt={payload.fetched_at} />
      </div>
      {rows.length === 0 ? (
        <p className="dim">No data yet — backend is warming up. Check back in a minute.</p>
      ) : (
        <table>
          <thead>
            <tr><th>#</th><th>Token</th><th>Price</th><th>24h</th><th>24h Vol</th><th>Liquidity</th><th>Mcap</th></tr>
          </thead>
          <tbody>
            {rows.map((t, i) => {
              const m = t.market || {}
              const chg = m.change_h24 ?? t.change_h24
              const tokenCell = (
                <><b>{t.symbol || '?'}</b> <span className="dim">{t.name || ''}</span></>
              )
              return (
                <tr key={t.pool || i}>
                  <td className="dim">{i + 1}</td>
                  <td>{t.chart_url ? (
                    <a className="token-link" href={t.chart_url} target="_blank" rel="noopener noreferrer" title="Open chart">{tokenCell}</a>
                  ) : tokenCell}</td>
                  <td className="num">{fmtPrice(m.price_usd ?? t.price_usd)}</td>
                  <td className="num"><span className={'badge ' + (chg >= 0 ? 'badge-up' : 'badge-down')}>{fmtPct(chg)}</span></td>
                  <td className="num">{fmtUsd(m.volume_h24 ?? t.volume_h24, 0)}</td>
                  <td className="num">{fmtUsd(m.liquidity_usd ?? t.liquidity_usd, 0)}</td>
                  <td className="num">{fmtUsd(m.market_cap ?? t.market_cap_usd ?? t.fdv_usd, 0)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
      <p className="foot">GeckoTerminal trending pools · enriched by DexScreener · updated {timeAgo(payload.fetched_at)}</p>
    </div>
  )
}
