export const number = (value, digits = 2) => value == null || !Number.isFinite(Number(value))
  ? '—' : Number(value).toLocaleString('en-IN', { minimumFractionDigits: digits, maximumFractionDigits: digits })
export const money = (value, currency = 'INR') => value == null || !Number.isFinite(Number(value)) ? '—' : new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-US', { style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
export const largeMoney = (value, currency = 'INR') => value == null || !Number.isFinite(Number(value)) ? '—' : currency === 'INR' ? `${money(value / 1e7, currency)} Cr` : new Intl.NumberFormat('en-US', { style: 'currency', currency, notation: 'compact', maximumFractionDigits: 2 }).format(value)
export const compact = (value, currency = 'INR') => value == null ? '—' : currency !== 'INR' ? new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(value) : value >= 1e7
  ? `${number(value / 1e7)} Cr` : value >= 1e5 ? `${number(value / 1e5)} L` : number(value, 0)
export const percent = (value) => value == null ? '—' : `${value > 0 ? '+' : ''}${number(value)}%`
export const marketTime = (value, timeZone = 'Asia/Kolkata') => {
  if (!value || !Number.isFinite(new Date(value).getTime())) return 'Market timestamp unavailable'
  const label = new Intl.DateTimeFormat('en-US', { timeZone, timeZoneName: 'short' }).formatToParts(new Date(value)).find(part => part.type === 'timeZoneName')?.value
  return `${new Intl.DateTimeFormat('en-IN', { timeZone, day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value))} ${timeZone === 'Asia/Kolkata' ? 'IST' : label}`
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
