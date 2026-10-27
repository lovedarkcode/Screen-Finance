import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowDown, ArrowUp, Bot, ChevronLeft, ChevronRight, Search, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Chip } from '@/components/ui/chip'
import { Field } from '@/components/ui/field'
import { inputClass } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import { largeMoney, money, number } from '@/components/stock/stock-format'
import screenerService from '@/services/screener.service'
import './natural-language-screener.css'

const EXAMPLES = [
  'Find US technology companies with ROE above 20% and debt-to-equity below 0.5.',
  'Show Indian companies with revenue growth above 5% and P/E below 25.',
  'Find profitable US companies with market capitalization above $10 billion.',
]
const INITIAL = { market: 'IN', exchange: null, exchanges: [], sector: null, industry: null, filters: [], sort_by: 'market_cap', sort_period: 'snapshot', sort_desc: true, limit: 25 }
const BASE_COLUMNS = ['market_cap:snapshot', 'pe:ttm', 'roe:annual', 'revenue_growth:annual', 'debt_to_equity:snapshot', 'net_profit_margin:annual']
const PERIOD_LABELS = { annual: 'Latest fiscal year', ttm: 'Trailing twelve months', quarterly: 'Latest quarter', snapshot: 'Latest snapshot' }
const OPS = { gt: '>', gte: '≥', lt: '<', lte: '≤', eq: '=', between: 'Between' }
const keyFor = filter => `${filter.field}:${filter.period}${filter.period_end ? `:${filter.period_end}` : ''}`

function MetricValue({ metric }) {
  if (metric?.value == null) return <span className="nl-unavailable">Unavailable</span>
  const currency = typeof metric.currency === 'string' ? metric.currency.trim().toUpperCase() : ''
  const value = metric.unit === 'currency'
    ? /^[A-Z]{3}$/.test(currency) ? Math.abs(metric.value) >= 1e6 ? largeMoney(metric.value, currency) : money(metric.value, currency) : `${number(metric.value)} (currency unavailable)`
    : `${number(metric.value)}${metric.unit === 'percent' ? '%' : metric.unit === 'times' ? '×' : ''}`
  return <><strong>{value}</strong><small>{metric.period || 'Period unavailable'}</small></>
}

export default function NaturalLanguageScreener() {
  const [query, setQuery] = useState('')
  const [metrics, setMetrics] = useState([])
  const [market, setMarket] = useState('IN')
  const [screen, setScreen] = useState(INITIAL)
  const [result, setResult] = useState(null)
  const [originalQuery, setOriginalQuery] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const request = useRef(null)
  useEffect(() => {
    const controller = new AbortController()
    screenerService.metrics(controller.signal).then(data => setMetrics(Array.isArray(data.metrics) ? data.metrics : [])).catch(() => {})
    return () => { controller.abort(); request.current?.abort() }
  }, [])
  const registry = Object.fromEntries(metrics.map(item => [item.field, item]))
  const setPrompt = value => {
    setQuery(value)
    setScreen(INITIAL)
    setOriginalQuery(null)
    setResult(null)
    setError('')
  }
  const run = async (kind, definition = screen, page = 1) => {
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    setError('')
    setResult(null)
    if (kind === 'search') { setScreen(INITIAL); setOriginalQuery(null) }
    try {
      const data = kind === 'search' ? await screenerService.search(query.trim(), market, controller.signal) : await screenerService.execute(definition, page, controller.signal, originalQuery)
      if (controller.signal.aborted) return
      setResult(data)
      if (data.parsed_filters) { setScreen(data.parsed_filters); setOriginalQuery(data.original_query || (kind === 'search' ? query.trim() : originalQuery)) }
    } catch (failure) {
      if (controller.signal.aborted) return
      const detail = failure.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'The screener could not complete this request. Please try again in a moment.')
    } finally { if (!controller.signal.aborted) setLoading(false) }
  }
  const columns = [...new Set([...BASE_COLUMNS, ...(result?.parsed_filters?.filters || []).map(keyFor)])].filter(key => registry[key.split(':')[0]])
  const sort = key => {
    const [field, period] = key.split(':')
    const next = { ...screen, sort_by: field, sort_period: period, sort_desc: screen.sort_by === field ? !screen.sort_desc : true }
    setScreen(next)
    run('execute', next)
  }
  const applied = result?.parsed_filters
  const marketLabel = applied?.market === 'IN' ? 'Indian' : applied?.market === 'US' ? 'US' : 'all-market'
  const filterLabel = filter => {
    const metric = registry[filter.field]
    const format = value => `${value}${metric?.unit === 'percent' ? '%' : metric?.unit === 'times' ? '×' : filter.currency ? ` ${filter.currency}` : ''}`
    const threshold = Array.isArray(filter.value) ? filter.value.map(format).join(' and ') : format(filter.value)
    return `${metric?.label || filter.field} ${OPS[filter.operator]} ${threshold} · ${PERIOD_LABELS[filter.period] || filter.period}${filter.period_end ? ` ending ${filter.period_end}` : ' (latest available)'}`
  }
  return <section className="stock-section nl-screener" aria-label="AI stock screener"><div className="stock-container">
    <Card className="nl-bot-card">
      <div className="nl-heading"><span className="nl-bot-icon"><Bot size={23} /></span><div><p className="market-eyebrow">Your stock discovery assistant</p><h2>Find companies in your own words</h2><p>Choose a market and describe the companies you want. We match your conditions against available financial data across exchange listings.</p></div><Chip><Sparkles size={12} />AI Screener</Chip></div>
      <div className="nl-market-picker"><Field label="Market"><select className={inputClass} value={market} disabled={loading} onChange={event => { setMarket(event.target.value); setPrompt(query) }}><option value="IN">Indian market</option><option value="US">US market</option></select></Field><p>{market === 'IN' ? 'NSE and BSE listings' : 'NYSE and NASDAQ listings. Ask for S&P 500 in your prompt'}</p></div>
      <form onSubmit={event => { event.preventDefault(); if (query.trim().length >= 3) run('search') }}>
        <label className="nl-query-label" htmlFor="nl-screen-query">What would you like to screen?</label>
        <Textarea id="nl-screen-query" value={query} onChange={event => setPrompt(event.target.value)} maxLength={1500} placeholder={market === 'IN' ? 'Show Indian companies with revenue growth above 5% and P/E below 25.' : 'Find US technology companies with ROE above 20% and debt-to-equity below 0.5.'} disabled={loading} />
        <div className="nl-query-actions"><span>{query.length}/1500</span><Button type="submit" variant="solid" iconRight={null} disabled={loading || query.trim().length < 3}>{loading ? <Spinner label="Screening stocks" /> : <Search size={16} />}Find stocks</Button></div>
      </form>
      <div className="nl-examples" aria-label="Example screening requests">{EXAMPLES.map((example, index) => <Button key={example} type="button" variant="outline" size="sm" disabled={loading} onClick={() => { setMarket(index === 1 ? 'IN' : 'US'); setPrompt(example) }}>{['US quality & debt', 'Indian growth & value', 'Profitable US companies'][index]}</Button>)}</div>
      {loading && <div className="nl-status" role="status"><Spinner label="Working" /><p>Finding companies that match your request in the selected market...</p></div>}
      {error && <div className="nl-feedback" role="alert"><strong>Screening is unavailable</strong><p>{error}</p></div>}
      {result && result.status !== 'success' && <div className="nl-feedback" role="status"><strong>{result.status === 'invalid' ? 'Check the conditions' : result.status === 'unsupported' ? 'This condition needs another approach' : 'A little more detail'}</strong><p>{result.clarification}</p></div>}
    </Card>
    {result?.status === 'success' && <div className="nl-results" aria-label="Stock screening results"><div className="nl-results-heading"><div><h3>{result.total_count} matching {result.total_count === 1 ? 'listing' : 'listings'}</h3><p>{result.universe_count.toLocaleString()} {marketLabel} listings / {result.eligible_count?.toLocaleString() ?? '-'} with eligible data for your conditions</p></div><Chip>{applied.market ? `${applied.market} market` : 'All markets'}</Chip></div>
      <div className="nl-applied-filters" aria-label="Interpreted request">{[applied.index === 'SP500' ? 'S&P 500' : null, applied.exchanges?.length ? applied.exchanges.join(' or ') : applied.exchange, applied.sector, applied.industry].filter(Boolean).map(value => <Chip key={value}>{value}</Chip>)}{applied.filters.map((filter, index) => <Chip key={index}>{filterLabel(filter)}</Chip>)}</div>
      {!!result.warnings?.length && <ul className="nl-notes">{result.warnings.map(note => <li key={note}>{note}</li>)}</ul>}
      {!result.stocks.length ? <Card className="nl-empty"><Search size={22} /><h3>{result.empty_reason === 'page_out_of_range' ? 'No stocks on this page' : 'No matching stocks found'}</h3><p>{result.explanation || (result.universe_count ? `Only ${result.universe_count} imported ${marketLabel} listings were screened; this does not cover the entire market. No imported company satisfies every applied condition with eligible data. Missing values or incompatible reporting periods cannot match. Try adjusting the filters.` : 'No companies have been imported for this market yet.')}</p>{result.original_query && <p>Source request: {result.original_query}</p>}<div className="nl-applied-filters" aria-label="Applied screening filters"><Chip>{applied.market ? `${applied.market} market` : 'All markets'}</Chip>{[applied.index === 'SP500' ? 'S&P 500' : null, applied.exchanges?.length ? applied.exchanges.join(' or ') : applied.exchange, applied.sector, applied.industry].filter(Boolean).map(value => <Chip key={value}>{value}</Chip>)}{applied.filters.map((filter, index) => <Chip key={index}>{filterLabel(filter)}</Chip>)}</div></Card> : <Table className="nl-results-table" aria-label="Matching stocks"><TableHeader><TableRow><TableHead>Company</TableHead>{columns.map(key => { const [field, basis] = key.split(':'); return <TableHead key={key}><Button variant="ghost" size="sm" disabled={loading} onClick={() => sort(key)}>{registry[field].label}{screen.sort_by === field ? screen.sort_desc ? <ArrowDown size={12} /> : <ArrowUp size={12} /> : null}</Button><small>{basis}{key.split(':')[2] && ` · ${key.split(':')[2]}`}</small></TableHead> })}<TableHead>Research</TableHead></TableRow></TableHeader><TableBody>{result.stocks.map(stock => <TableRow key={stock.symbol}><TableCell><Link to={`/stock/${encodeURIComponent(stock.symbol)}`}><strong>{stock.name}</strong><small>{stock.symbol} · {stock.exchange}</small></Link><small>{stock.sector || 'Sector unavailable'}</small></TableCell>{columns.map(key => <TableCell key={key} title={stock.metrics[key]?.definition}><MetricValue metric={stock.metrics[key]} /><small>{stock.metrics[key]?.validation_status}{stock.metrics[key]?.source && ` · ${stock.metrics[key].source}`}</small></TableCell>)}<TableCell><Button asChild variant="outline" size="sm"><Link to={`/stock/${encodeURIComponent(stock.symbol)}`}>View analysis</Link></Button></TableCell></TableRow>)}</TableBody></Table>}
      <div className="nl-pagination"><span>Page {result.page} of {Math.max(1, Math.ceil(result.total_count / result.page_size))}{result.data_as_of && ` · Last dataset refresh: ${new Date(result.data_as_of).toLocaleString()}`}</span><Button variant="outline" size="sm" disabled={loading || result.page <= 1} onClick={() => run('execute', result.parsed_filters, result.page - 1)}><ChevronLeft size={14} />Previous</Button><Button variant="outline" size="sm" disabled={loading || result.page >= 1000 || result.page * result.page_size >= result.total_count} onClick={() => run('execute', result.parsed_filters, result.page + 1)}>Next<ChevronRight size={14} /></Button></div>
    </div>}
  </div></section>
}
