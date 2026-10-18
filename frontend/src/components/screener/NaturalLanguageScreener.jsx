import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowDown, ArrowUp, Bot, ChevronLeft, ChevronRight, Plus, Search, SlidersHorizontal, Sparkles, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Chip } from '@/components/ui/chip'
import { Field } from '@/components/ui/field'
import { IconButton } from '@/components/ui/icon-button'
import { Input, inputClass } from '@/components/ui/input'
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
const INITIAL = { market: 'US', exchange: null, exchanges: [], sector: null, industry: null, filters: [], sort_by: 'market_cap', sort_period: 'snapshot', sort_desc: true, limit: 25 }
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
  const [sectors, setSectors] = useState([])
  const [industries, setIndustries] = useState([])
  const [editor, setEditor] = useState(false)
  const [screen, setScreen] = useState(INITIAL)
  const [result, setResult] = useState(null)
  const [originalQuery, setOriginalQuery] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dirty, setDirty] = useState(false)
  const request = useRef(null)
  useEffect(() => {
    const controller = new AbortController()
    screenerService.metrics(controller.signal).then(data => setMetrics(Array.isArray(data.metrics) ? data.metrics : [])).catch(() => {})
    screenerService.sectors(controller.signal).then(data => { setSectors(Array.isArray(data.sectors) ? data.sectors : []); setIndustries(Array.isArray(data.industries) ? data.industries : []) }).catch(() => {})
    return () => { controller.abort(); request.current?.abort() }
  }, [])
  const registry = Object.fromEntries(metrics.map(item => [item.field, item]))
  const change = patch => { setScreen(previous => ({ ...previous, ...patch })); setDirty(true) }
  const setPrompt = value => {
    setQuery(value)
    setScreen(INITIAL)
    setOriginalQuery(null)
    setResult(null)
    setEditor(false)
    setDirty(false)
    setError('')
  }
  const updateFilter = (index, patch) => change({ filters: screen.filters.map((item, at) => at === index ? { ...item, ...patch } : item) })
  const run = async (kind, definition = screen, page = 1) => {
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    setError('')
    setResult(null)
    if (kind === 'search') { setScreen(INITIAL); setOriginalQuery(null); setEditor(false); setDirty(false) }
    try {
      const data = kind === 'search' ? await screenerService.search(query.trim(), controller.signal) : await screenerService.execute(definition, page, controller.signal, originalQuery)
      if (controller.signal.aborted) return
      setResult(data)
      if (data.parsed_filters) { setScreen(data.parsed_filters); setOriginalQuery(data.original_query || (kind === 'search' ? query.trim() : originalQuery)); setEditor(true); setDirty(false) }
    } catch (failure) {
      if (controller.signal.aborted) return
      const detail = failure.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'The screener could not complete this request. Please check the filters and try again.')
    } finally { if (!controller.signal.aborted) setLoading(false) }
  }
  const changeMarket = value => { const market = value || null; change({ market, exchange: null, exchanges: [], sector: null, industry: null, filters: screen.filters.map(item => ({ ...item, currency: registry[item.field]?.unit === 'currency' && (Array.isArray(item.value) ? item.value.some(value => value !== 0) : item.value !== 0) ? market === 'IN' ? 'INR' : market === 'US' ? 'USD' : null : null })) }) }
  const columns = [...new Set([...BASE_COLUMNS, ...(result?.parsed_filters?.filters || []).map(keyFor)])].filter(key => registry[key.split(':')[0]])
  const sort = key => {
    const [field, period] = key.split(':')
    const next = { ...screen, sort_by: field, sort_period: period, sort_desc: screen.sort_by === field ? !screen.sort_desc : true }
    setScreen(next)
    run('execute', next)
  }
  const addFilter = () => {
    const field = metrics[0]?.field
    if (field) change({ filters: [...screen.filters, { field, operator: 'gt', value: 0, period: registry[field].default_period, period_end: null, currency: null }] })
  }
  const setThreshold = (index, text, bound = null) => {
    const value = text === '' ? '' : Number(text)
    updateFilter(index, { value: bound === null ? value : screen.filters[index].value.map((item, at) => at === bound ? value : item) })
  }
  const invalidNumbers = screen.filters.some(item => (Array.isArray(item.value) ? item.value : [item.value]).some(value => typeof value !== 'number' || !Number.isFinite(value)))
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
      <div className="nl-heading"><span className="nl-bot-icon"><Bot size={23} /></span><div><p className="market-eyebrow">Your stock discovery assistant</p><h2>Find companies in your own words</h2><p>Describe the fundamentals you want. Review the filters, compare matching stocks, and continue your research.</p></div><Chip><Sparkles size={12} />AI Screener</Chip></div>
      <form onSubmit={event => { event.preventDefault(); if (query.trim().length >= 3) run('search') }}>
        <label className="nl-query-label" htmlFor="nl-screen-query">What would you like to screen?</label>
        <Textarea id="nl-screen-query" value={query} onChange={event => setPrompt(event.target.value)} maxLength={1500} placeholder="Find US technology companies with ROE above 20% and debt-to-equity below 0.5…" disabled={loading} />
        <div className="nl-query-actions"><Button type="button" variant="ghost" size="sm" onClick={() => setEditor(value => !value)} aria-expanded={editor}><SlidersHorizontal size={15} />Edit financial filters</Button><span>{query.length}/1500</span><Button type="submit" variant="solid" iconRight={null} disabled={loading || query.trim().length < 3}>{loading ? <Spinner label="Screening stocks" /> : <Search size={16} />}Find stocks</Button></div>
      </form>
      <div className="nl-examples" aria-label="Example screening requests">{EXAMPLES.map((example, index) => <Button key={example} type="button" variant="outline" size="sm" disabled={loading} onClick={() => setPrompt(example)}>{['US quality & debt', 'Indian growth & value', 'Profitable US companies'][index]}</Button>)}</div>
      {loading && <div className="nl-status" role="status"><Spinner label="Working" /><p>Checking your screen and matching it against imported financial data…</p></div>}
      {error && <div className="nl-feedback" role="alert"><strong>Screening is unavailable</strong><p>{error}</p><Button variant="ghost" size="sm" onClick={() => setEditor(true)}>Use financial filters</Button></div>}
      {result && result.status !== 'success' && <div className="nl-feedback" role="status"><strong>{result.status === 'invalid' ? 'Check the conditions' : result.status === 'unsupported' ? 'This condition needs another approach' : 'A little more detail'}</strong><p>{result.clarification}</p><Button variant="ghost" size="sm" onClick={() => setEditor(true)}>Set explicit filters</Button></div>}
      {editor && <div className="nl-editor" inert={loading || undefined}><div className="nl-editor-heading"><h3>Screening filters</h3><small>Changes rerun the database screen without another AI request.</small></div>
        <div className="nl-controls"><Field label="Market"><select className={inputClass} value={screen.market || ''} onChange={event => changeMarket(event.target.value)}><option value="">All markets</option><option value="US">United States · USD</option><option value="IN">India · INR</option></select></Field>
          <Field label="Exchange"><select className={inputClass} value={screen.exchanges?.length ? '__selected' : screen.exchange || ''} onChange={event => change(event.target.value === '__selected' ? {} : { exchange: event.target.value || null, exchanges: [] })}><option value="">All supported exchanges</option>{!!screen.exchanges?.length && <option value="__selected">{screen.exchanges.join(' or ')}</option>}{(screen.market === 'IN' ? ['NSE', 'BSE'] : screen.market === 'US' ? ['NASDAQ', 'NYSE', 'NYSE American', 'NYSE Arca', 'Cboe', 'OTC', 'OTCQB', 'OTCQX'] : ['NSE', 'BSE', 'NASDAQ', 'NYSE', 'NYSE American', 'NYSE Arca', 'Cboe', 'OTC', 'OTCQB', 'OTCQX']).map(value => <option key={value}>{value}</option>)}</select></Field>
          <Field label="Sector"><Input value={screen.sector || ''} list="nl-sectors" placeholder="Any sector" onChange={event => change({ sector: event.target.value || null })} /></Field><datalist id="nl-sectors">{[...new Set(sectors.filter(item => !screen.market || item.market === screen.market).map(item => item.name))].map(value => <option key={value} value={value} />)}</datalist>
          <Field label="Industry"><Input value={screen.industry || ''} list="nl-industries" placeholder="Any industry" onChange={event => change({ industry: event.target.value || null })} /></Field><datalist id="nl-industries">{[...new Set(industries.filter(item => !screen.market || item.market === screen.market).map(item => item.name))].map(value => <option key={value} value={value} />)}</datalist>
        </div>
        <p className="nl-filter-definition">Changing market keeps threshold numbers and changes their currency; no exchange-rate conversion is applied. For monetary filters across all markets, choose a market first.</p>
        <Field label="Screening date (optional)"><Input type="date" value={screen.as_of || ''} onChange={event => change({ as_of: event.target.value || null })} /></Field>
        <div className="nl-filter-list">{screen.filters.map((filter, index) => <div className="nl-filter" key={index}>
          <Field label={`Metric ${index + 1}`}><select className={inputClass} value={filter.field} onChange={event => updateFilter(index, { field: event.target.value, period: registry[event.target.value].default_period, currency: null, period_end: null })}>{metrics.map(item => <option key={item.field} value={item.field}>{item.label}{item.unit === 'percent' ? ' (%)' : item.unit === 'times' ? ' (ratio)' : ''}</option>)}</select></Field>
          <Field label={`Comparison ${index + 1}`}><select className={inputClass} value={filter.operator} onChange={event => updateFilter(index, { operator: event.target.value, value: event.target.value === 'between' ? [Array.isArray(filter.value) ? filter.value[0] : filter.value, Array.isArray(filter.value) ? filter.value[1] : filter.value] : Array.isArray(filter.value) ? filter.value[0] : filter.value })}>{Object.entries(OPS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
          <Field label={`Threshold ${index + 1}`}><Input type="number" step="any" value={Array.isArray(filter.value) ? filter.value[0] : filter.value} onChange={event => setThreshold(index, event.target.value, Array.isArray(filter.value) ? 0 : null)} /></Field>
          {filter.operator === 'between' && <Field label={`Upper threshold ${index + 1}`}><Input type="number" step="any" value={filter.value[1]} onChange={event => setThreshold(index, event.target.value, 1)} /></Field>}
          <Field label={`Period ${index + 1}`}><select className={inputClass} value={filter.period || registry[filter.field]?.default_period || ''} onChange={event => updateFilter(index, { period: event.target.value, period_end: null })}>{(registry[filter.field]?.periods || []).map(value => <option key={value} value={value}>{PERIOD_LABELS[value]}</option>)}</select></Field>
          <Field label={`Fiscal end ${index + 1}`} hint="Leave blank for latest report"><Input type="date" value={filter.period_end || ''} onChange={event => updateFilter(index, { period_end: event.target.value || null })} /></Field>
          <IconButton variant="ghost" aria-label={`Remove filter ${index + 1}`} onClick={() => change({ filters: screen.filters.filter((_, at) => at !== index) })}><X size={15} /></IconButton>
          <p className="nl-filter-definition">{registry[filter.field]?.definition}{registry[filter.field]?.unit === 'currency' && ` Threshold currency: ${filter.currency || (screen.market === 'IN' ? 'INR' : screen.market === 'US' ? 'USD' : 'choose a market for nonzero thresholds')}; zero thresholds also apply across reporting currencies.`}</p>
        </div>)}</div>
        <div className="nl-editor-actions"><Button variant="ghost" size="sm" disabled={screen.filters.length >= 12 || !metrics.length} onClick={addFilter}><Plus size={14} />Add condition</Button><Field label="Rows per page"><select className={inputClass} value={screen.limit} onChange={event => change({ limit: Number(event.target.value) })}>{[...new Set([10, 25, 50, 100, screen.limit])].sort((a, b) => a - b).map(value => <option key={value}>{value}</option>)}</select></Field><Button variant="soft" disabled={loading || !metrics.length || invalidNumbers} onClick={() => run('execute')}>Apply filters</Button></div>
        {!metrics.length && <p className="nl-feedback">Supported metrics are unavailable. Please refresh the page when the API is reachable.</p>}
      </div>}
    </Card>
    {result?.status === 'success' && <div className="nl-results" aria-label="Stock screening results"><div className="nl-results-heading"><div><h3>{result.total_count} matching {result.total_count === 1 ? 'company' : 'companies'}</h3><p>{result.universe_count} imported {marketLabel} listings screened · {result.cached ? 'Cached screen' : `${result.execution_ms} ms`}{dirty && ' · Filters changed; apply to update results'}</p></div><Chip>{applied.market ? `${applied.market} market` : 'All markets'}</Chip></div>
      {!!result.warnings?.length && <ul className="nl-notes">{result.warnings.map(note => <li key={note}>{note}</li>)}</ul>}
      {!result.stocks.length ? <Card className="nl-empty"><Search size={22} /><h3>{result.empty_reason === 'page_out_of_range' ? 'No stocks on this page' : 'No matching stocks found'}</h3><p>{result.explanation || (result.universe_count ? `Only ${result.universe_count} imported ${marketLabel} listings were screened; this does not cover the entire market. No imported company satisfies every applied condition with eligible data. Missing values or incompatible reporting periods cannot match. Try adjusting the filters.` : 'No companies have been imported for this market yet.')}</p>{result.original_query && <p>Source request: {result.original_query}</p>}<div className="nl-applied-filters" aria-label="Applied screening filters"><Chip>{applied.market ? `${applied.market} market` : 'All markets'}</Chip>{[applied.exchanges?.length ? applied.exchanges.join(' or ') : applied.exchange, applied.sector, applied.industry].filter(Boolean).map(value => <Chip key={value}>{value}</Chip>)}{applied.filters.map((filter, index) => <Chip key={index}>{filterLabel(filter)}</Chip>)}</div></Card> : <Table className="nl-results-table" aria-label="Matching stocks"><TableHeader><TableRow><TableHead>Company</TableHead>{columns.map(key => { const [field, basis] = key.split(':'); return <TableHead key={key}><Button variant="ghost" size="sm" disabled={loading || dirty} onClick={() => sort(key)}>{registry[field].label}{screen.sort_by === field ? screen.sort_desc ? <ArrowDown size={12} /> : <ArrowUp size={12} /> : null}</Button><small>{basis}{key.split(':')[2] && ` · ${key.split(':')[2]}`}</small></TableHead> })}<TableHead>Research</TableHead></TableRow></TableHeader><TableBody>{result.stocks.map(stock => <TableRow key={stock.symbol}><TableCell><Link to={`/stock/${encodeURIComponent(stock.symbol)}`}><strong>{stock.name}</strong><small>{stock.symbol} · {stock.exchange}</small></Link><small>{stock.sector || 'Sector unavailable'}</small></TableCell>{columns.map(key => <TableCell key={key} title={stock.metrics[key]?.definition}><MetricValue metric={stock.metrics[key]} /><small>{stock.metrics[key]?.validation_status}{stock.metrics[key]?.source && ` · ${stock.metrics[key].source}`}</small></TableCell>)}<TableCell><Button asChild variant="outline" size="sm"><Link to={`/stock/${encodeURIComponent(stock.symbol)}`}>View analysis</Link></Button></TableCell></TableRow>)}</TableBody></Table>}
      <div className="nl-pagination"><span>Page {result.page} of {Math.max(1, Math.ceil(result.total_count / result.page_size))}{result.data_as_of && ` · Last dataset refresh: ${new Date(result.data_as_of).toLocaleString()}`}</span><Button variant="outline" size="sm" disabled={loading || dirty || result.page <= 1} onClick={() => run('execute', result.parsed_filters, result.page - 1)}><ChevronLeft size={14} />Previous</Button><Button variant="outline" size="sm" disabled={loading || dirty || result.page >= 1000 || result.page * result.page_size >= result.total_count} onClick={() => run('execute', result.parsed_filters, result.page + 1)}>Next<ChevronRight size={14} /></Button></div>
    </div>}
  </div></section>
}
