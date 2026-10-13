import { useEffect, useState } from 'react'
import { api, fmtUsd, timeAgo } from './api.js'
import TrendingTable from './components/TrendingTable.jsx'
import RegimeStrip from './components/RegimeStrip.jsx'

function usePoll(fn, intervalMs) {
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    let alive = true
    const tick = async () => {
      try {
        const data = await fn()
        if (alive) { setPayload(data); setError(null) }
      } catch (e) {
        if (alive) setError(String(e.message || e))
      }
    }
    tick()
    const id = setInterval(tick, intervalMs)
    return () => { alive = false; clearInterval(id) }
  }, [])
  return [payload, error]
}

export default function App() {
  const [trending, trendingErr] = usePoll(api.trending, 60000)
  const [regime] = usePoll(api.regime, 60000)
  const [watchlist] = usePoll(api.watchlist, 60000)

  return (
    <div className="app">
      <header>
        <h1>MEME <span>DESK</span></h1>
        <span className="dim">Today · live · personal build v0.1</span>
      </header>

      {trendingErr && <div className="banner">Backend unreachable: {trendingErr}. Is it running on :8000?</div>}

      <RegimeStrip payload={regime} />
      <TrendingTable payload={trending} />

      <div className="panel">
        <div className="panel-head"><h2>Watchlist</h2><span className="dim">{watchlist ? watchlist.count + ' seeds' : ''}</span></div>
        <div className="chips">
          {(watchlist?.data || []).map((w) => (
            <a className="chip token-link" key={w.mint} title={w.mint + ' — open chart'} href={w.chart_url} target="_blank" rel="noopener noreferrer">
              <b>{w.symbol}</b>
              <span className="dim">{w.market?.price_usd != null ? ' $' + w.market.price_usd : ''}</span>
            </a>
          ))}
        </div>
        <p className="foot">Seed universe · prices enriched by DexScreener market cache.</p>
      </div>

      <footer>Data: GeckoTerminal · DexScreener · Jupiter · CoinGecko — all keyless, read-only. Not financial advice.</footer>
    </div>
  )
}
