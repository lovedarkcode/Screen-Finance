export const number = (value, digits = 2) => value == null || !Number.isFinite(Number(value))
  ? '—' : Number(value).toLocaleString('en-IN', { minimumFractionDigits: digits, maximumFractionDigits: digits })
export const money = (value) => value == null ? '—' : `₹${number(value)}`
export const compact = (value) => value == null ? '—' : value >= 1e7
  ? `${number(value / 1e7)} Cr` : value >= 1e5 ? `${number(value / 1e5)} L` : number(value, 0)
export const percent = (value) => value == null ? '—' : `${value > 0 ? '+' : ''}${number(value)}%`
export const marketTime = (value) => {
  if (!value || !Number.isFinite(new Date(value).getTime())) return 'Market timestamp unavailable'
  return `${new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value))} IST`
}
export const readPreference = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback } catch { return fallback }
}
export const SECTIONS = [
  ['priceChart', 'Price Chart', 'Area chart with selectable timeframes'],
  ['keyMetrics', 'Key Metrics', 'Valuation, earnings and financial ratios'],
  ['priceRange', 'Price Range', 'Day range and 52-week high/low'],
  ['returns', 'Returns Performance', 'Performance across seven timeframes'],
  ['shareholding', 'Shareholding Pattern', 'Ownership breakdown from your provider'],
  ['financials', 'Financial Result', 'Quarterly income, profit and earnings'],
  ['about', 'About Company', 'Business description and company info'],
  ['peers', 'Peer Comparison', 'Side-by-side comparison with peers'],
  ['insights', 'Asset Hunter Insights', 'Highlights computed from company metrics'],
]
export const DEFAULT_SECTIONS = Object.fromEntries(SECTIONS.map(([id]) => [id, id !== 'insights']))
