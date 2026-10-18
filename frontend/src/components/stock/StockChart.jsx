import { Button } from '@/components/ui/button'
import { Segmented } from '@/components/ui/segmented'
import { DropdownMenu, DropdownMenuContent, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Skeleton } from '@/components/ui/skeleton'
import { useEffect, useState } from 'react'
import { Bar, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChevronDown, Check } from 'lucide-react'
import stockService from '@/services/stock.service'
import { EmptyState, SectionTitle } from './StockUI'
import { money } from './stock-format'
import ChartAlerts from './ChartAlerts'

const RANGES = ['1M', '6M', '1Y', '3Y', '5Y', '10Y', 'Max']
const MORE = ['1D', '1W', '3M', '15Y', '20Y', '25Y', '30Y']
const SERIES = [['price', 'Price', 'var(--stock-accent)'], ['dma50', '50 DMA', '#e6a52f'], ['dma100', '100 DMA', '#8596aa'], ['volume', 'Volume', '#a9bfe8']]

export default function StockChart(props) {
  return <ChartContent key={props.symbol} {...props} />
}

function ChartContent({ symbol, title = 'Price Chart', currency = 'INR', timeZone = 'Asia/Kolkata' }) {
  const [range, setRange] = useState('6M')
  const [metric, setMetric] = useState('price')
  const [scale, setScale] = useState('linear')
  const [visible, setVisible] = useState({ price: true, dma50: true, dma100: true, volume: true })
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState({ data: [], loading: true, error: '' })
  useEffect(() => {
    let live = true
    const request = metric === 'pe' ? stockService.getPeHistory(symbol) : stockService.getChart(symbol, range)
    request.then(data => {
      if (metric === 'pe' && range !== 'Max') {
        const units = { D: 1, W: 7, M: 30.4375, Y: 365.25 }
        const cutoff = Date.now() - parseInt(range) * units[range.slice(-1)] * 86400000
        data = data.filter(row => Date.parse(row.date) >= cutoff)
      }
      if (live) setState({ data, loading: false, error: '' })
    }).catch(() => { if (live) setState({ data: [], loading: false, error: 'Chart data is temporarily unavailable.' }) })
    return () => { live = false }
  }, [symbol, range, metric, attempt])
  const select = next => { if (next === range) return; setRange(next); setState({ data: [], loading: true, error: '' }) }
  const selectMetric = next => { if (next === metric) return; setMetric(next); setState({ data: [], loading: true, error: '' }) }
  const date = value => {
    const parsed = new Date(value)
    if (!Number.isFinite(parsed.getTime())) return value
    return new Intl.DateTimeFormat('en-IN', range === '1D' ? { timeZone, hour: '2-digit', minute: '2-digit', hour12: false } : { timeZone, day: 'numeric', month: 'short', ...(range.endsWith('Y') || range === 'Max' ? { year: '2-digit' } : {}) }).format(parsed)
  }
  const formatValue = value => metric === 'pe' ? Number(value).toFixed(2) + '×' : money(value, currency).replace('.00', '')
  const logSafe = state.data.every(row => (metric === 'pe' ? ['pe'] : ['price', 'dma50', 'dma100']).every(key => row[key] == null || row[key] > 0))
  return <section className="stock-section stock-band" id="price-chart"><div className="stock-container">
    <SectionTitle>{title}</SectionTitle>
    <div className="stock-chart-toolbar">
      <div className="stock-chart-ranges">
        <Segmented label="Chart timeframe" options={RANGES.map(value => ({ value, label: value.replace('Y', 'Yr') }))} value={range} onChange={select} />
        <DropdownMenu><DropdownMenuTrigger asChild><Button variant="ghost" size="sm" aria-label="More chart timeframes">{MORE.includes(range) ? range : 'More'}<ChevronDown size={12} /></Button></DropdownMenuTrigger>
          <DropdownMenuContent align="end"><DropdownMenuRadioGroup value={range} onValueChange={select}>{MORE.map(item => <DropdownMenuRadioItem key={item} value={item}>{item}</DropdownMenuRadioItem>)}</DropdownMenuRadioGroup></DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="stock-chart-options">
        <Segmented label="Chart metric" options={[{ value: 'price', label: 'Price' }, { value: 'pe', label: 'P/E Ratio' }]} value={metric} onChange={selectMetric} />
        <DropdownMenu><DropdownMenuTrigger asChild><Button variant="outline" size="sm">More<ChevronDown size={12} /></Button></DropdownMenuTrigger>
          <DropdownMenuContent align="end"><DropdownMenuRadioGroup value={scale} onValueChange={setScale}><DropdownMenuRadioItem value="linear">Linear scale</DropdownMenuRadioItem><DropdownMenuRadioItem value="log" disabled={!logSafe}>Logarithmic scale</DropdownMenuRadioItem></DropdownMenuRadioGroup></DropdownMenuContent>
        </DropdownMenu>
        <ChartAlerts symbol={symbol} currency={currency} />
      </div>
    </div>
    <div className="stock-chart" aria-busy={state.loading}>
      {state.loading && <span className="stock-chart-loading" role="status">Loading chart…</span>}
      {state.error ? <EmptyState error onRetry={() => { setState({ data: [], loading: true, error: '' }); setAttempt(value => value + 1) }}>{state.error}</EmptyState> : !state.loading && !state.data.length ? <EmptyState>{metric === 'pe' ? 'No recorded P/E snapshots in this timeframe.' : 'No price data available'}</EmptyState> : state.data.length ? <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={state.data} margin={{ top: 12, right: 4, left: 0, bottom: 0 }}>
          <XAxis dataKey="date" ticks={Array.from({ length: Math.min(6, state.data.length) }, (_, i) => state.data[Math.round(i * (state.data.length - 1) / Math.max(1, Math.min(6, state.data.length) - 1))].date)} tickFormatter={date} tick={{ fill: 'var(--stock-muted)', fontSize: 10 }} axisLine={false} tickLine={false} minTickGap={20} />
          <YAxis yAxisId="value" orientation="right" scale={scale === 'log' && logSafe ? 'log' : 'auto'} tick={{ fill: 'var(--stock-muted)', fontSize: 10 }} tickFormatter={formatValue} axisLine={false} tickLine={false} domain={['auto', 'auto']} tickCount={5} width={70} />
          {metric === 'price' && <YAxis yAxisId="volume" hide={!visible.volume} tickFormatter={value => Intl.NumberFormat('en', { notation: 'compact' }).format(value)} tick={{ fill: 'var(--stock-muted)', fontSize: 10 }} axisLine={false} tickLine={false} domain={[0, max => Math.max(1, max * 3)]} width={45} />}
          <Tooltip labelFormatter={date} formatter={(value, name) => [name === 'Volume' ? Number(value).toLocaleString() : formatValue(value), name]} contentStyle={{ background: 'var(--stock-bg)', border: '1px solid var(--stock-border)', borderRadius: 9, color: 'var(--stock-text)', fontSize: 11 }} labelStyle={{ color: 'var(--stock-text)' }} />
          {metric === 'price' && visible.volume && <Bar yAxisId="volume" dataKey="volume" name="Volume" fill="#a9bfe8" opacity={0.55} isAnimationActive={false} />}
          {metric === 'price' ? SERIES.filter(([key]) => key !== 'volume' && visible[key]).map(([key, label, color]) => <Line key={key} yAxisId="value" type="linear" dataKey={key} name={label} stroke={color} strokeWidth={key === 'price' ? 2 : 1.6} dot={state.data.length === 1} isAnimationActive={false} connectNulls={false} />) : <Line yAxisId="value" dataKey="pe" name="P/E Ratio" stroke="var(--stock-accent)" dot isAnimationActive={false} connectNulls={false} />}
        </ComposedChart>
      </ResponsiveContainer> : <Skeleton className="sk sk-chart" />}
    </div>
    {metric === 'price' ? <>
      <div className="stock-chart-toggles" role="group" aria-label="Chart overlays">{SERIES.map(([key, label, color]) => <Button key={key} variant="ghost" size="sm" aria-pressed={visible[key]} onClick={() => setVisible(value => ({ ...value, [key]: !value[key] }))}><span className="chart-toggle-check" style={{ background: visible[key] ? color : 'transparent', borderColor: color }}>{visible[key] && <Check size={13} />}</span>{label}</Button>)}</div>
      <p className="stock-source-note">DMA uses 50 or 100 trading-day closes. Intraday charts use completed prior sessions.{!state.loading && state.data.length > 0 && ['dma50', 'dma100'].some(key => visible[key] && !state.data.some(row => row[key] != null)) ? ' Some moving averages are unavailable or have insufficient daily history.' : ''}{!state.loading && visible.volume && state.data.length > 0 && !state.data.some(row => row.volume != null) ? ' Volume is unavailable for this instrument.' : ''}</p>
    </> : <p className="stock-source-note">Trailing P/E snapshots dated when recorded. Historical daily P/E is not supplied; gaps are not backfilled. P/E is unavailable for indices and non-positive earnings.</p>}
  </div></section>
}
