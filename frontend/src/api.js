// All data comes from our own backend — never third-party APIs directly.
// Every response carries { data, stale, fetched_at }; callers surface stale.

async function get(path) {
  const r = await fetch(path, { headers: { accept: 'application/json' } })
  if (!r.ok) throw new Error(`GET ${path} → ${r.status}`)
  return r.json()
}

export const api = {
  trending: () => get('/api/trending'),
  regime: () => get('/api/regime'),
  watchlist: () => get('/api/watchlist'),
  token: (mint) => get(`/api/token/${mint}`),
}

export function fmtUsd(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  const abs = Math.abs(n)
  if (abs >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B'
  if (abs >= 1e6) return '$' + (n / 1e6).toFixed(2) + 'M'
  if (abs >= 1e3) return '$' + (n / 1e3).toFixed(2) + 'K'
  return '$' + Number(n).toFixed(digits)
}

export function fmtPct(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  const s = n >= 0 ? '+' : ''
  return s + Number(n).toFixed(2) + '%'
}

export function timeAgo(ts) {
  if (!ts) return 'never'
  const s = Math.max(0, Math.floor(Date.now() / 1000 - ts))
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  return `${Math.floor(m / 60)}h ago`
}
