import { useEffect, useId, useRef, useState } from 'react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChevronDown, ExternalLink } from 'lucide-react'
import stockService from '@/services/stock.service'
import { EmptyState, SectionTitle } from './StockUI'
import { money } from './stock-format'

const RANGES = ['1D', '1W', '1M', '3M', '6M', '1Y', '5Y']
const MORE = ['10Y', '15Y', '20Y', '25Y', '30Y']

export default function StockChart({ symbol, title = 'Price Chart' }) {
  const [range, setRange] = useState('6M')
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState({ data: [], loading: true, error: '' })
  const gradient = useId()
  const more = useRef(null)
  useEffect(() => {
    const close = event => { if (more.current && (event.key === 'Escape' || !more.current.contains(event.target))) more.current.open = false }
    document.addEventListener('pointerdown', close)
    document.addEventListener('keydown', close)
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', close) }
  }, [])
  useEffect(() => {
    let live = true
    stockService.getChart(symbol, range).then(data => {
      if (live) setState({ data, loading: false, error: '' })
    }).catch(() => { if (live) setState({ data: [], loading: false, error: 'Price history is temporarily unavailable.' }) })
    return () => { live = false }
  }, [symbol, range, attempt])
  const select = (next) => { if (next === range) return; setRange(next); setState(value => ({ ...value, loading: true, error: '' })) }
  const date = (value) => {
    const parsed = new Date(value)
    if (!Number.isFinite(parsed.getTime())) return value
    return new Intl.DateTimeFormat('en-IN', range === '1D' ? { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: false } : { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short', ...(range.endsWith('Y') ? { year: '2-digit' } : {}) }).format(parsed)
  }
  return <section className="stock-section stock-band" id="price-chart"><div className="stock-container">
    <SectionTitle extra={<div className="stock-chart-ranges" aria-label="Chart timeframe">{RANGES.map(item => <button key={item} aria-pressed={range === item} onClick={() => select(item)}>{item}</button>)}
      <details ref={more} className="stock-range-more"><summary aria-label="More chart timeframes">{MORE.includes(range) && range}<ChevronDown size={12} /></summary><div>{MORE.map(item => <button key={item} aria-pressed={range === item} onClick={event => { select(item); event.currentTarget.closest('details').open = false }}>{item}</button>)}</div></details>
    </div>}><span>{title}</span><a className="stock-heading-link" target="_blank" rel="noreferrer" href={`https://finance.yahoo.com/quote/${encodeURIComponent(symbol)}/chart/`}><ExternalLink size={13} />Advanced chart</a></SectionTitle>
    <div className="stock-chart" aria-busy={state.loading}>
      {state.loading && <span className="stock-chart-loading" role="status">Loading price history…</span>}
      {state.error ? <EmptyState error onRetry={() => { setState(value => ({ ...value, loading: true })); setAttempt(value => value + 1) }}>{state.error}</EmptyState> : !state.loading && !state.data.length ? <EmptyState>No price data available</EmptyState> : state.data.length ? <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={state.data} margin={{ top: 12, right: 25, left: 0, bottom: 0 }} style={{ opacity: state.loading ? .45 : 1 }}>
          <defs><linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--stock-accent)" stopOpacity={.13} /><stop offset="100%" stopColor="var(--stock-accent)" stopOpacity={0} /></linearGradient></defs>
          <XAxis dataKey="date" ticks={Array.from({ length: Math.min(6, state.data.length) }, (_, i) => state.data[Math.round(i * (state.data.length - 1) / Math.max(1, Math.min(6, state.data.length) - 1))].date)} tickFormatter={date} tick={{ fill: 'var(--stock-muted)', fontSize: 10 }} axisLine={false} tickLine={false} minTickGap={20} />
          <YAxis tick={{ fill: 'var(--stock-muted)', fontSize: 10 }} tickFormatter={value => money(value).replace('.00', '')} axisLine={false} tickLine={false} domain={['auto', 'auto']} tickCount={5} width={60} />
          <Tooltip labelFormatter={date} formatter={value => [money(value), 'Price']} contentStyle={{ background: 'var(--stock-bg)', border: '1px solid var(--stock-border)', borderRadius: 9, color: 'var(--stock-text)', fontSize: 11 }} labelStyle={{ color: 'var(--stock-text)' }} cursor={{ stroke: 'var(--stock-muted)', strokeWidth: 1 }} />
          <Area type="monotone" dataKey="price" stroke="var(--stock-accent)" strokeWidth={1.8} fill={`url(#${gradient})`} dot={false} activeDot={{ r: 3.5, stroke: 'var(--stock-text)', strokeWidth: 1.5 }} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer> : <div className="sk sk-chart" />}
    </div>
  </div></section>
}
