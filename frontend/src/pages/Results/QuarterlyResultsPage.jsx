import { useEffect, useState } from 'react'
import { Link, useOutletContext, useSearchParams } from 'react-router-dom'
import { ArrowRight, CalendarDays, ExternalLink, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { SearchInput } from '@/components/ui/search-input'
import { Segmented } from '@/components/ui/segmented'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, StockModal } from '@/components/stock/StockUI'
import api from '@/services/api'
import './quarterly-results.css'

const METRICS = [['sales', 'Sales'], ['ebitda', 'EBITDA'], ['net_profit', 'Net profit'], ['eps', 'EPS']]
const dateLabel = value => new Date(`${value}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
const amount = (value, currency, eps = false) => value == null ? '—' : (value / (eps ? 1 : currency === 'INR' ? 1e7 : 1e6)).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const growthLabel = value => value == null ? '—' : `${value > 0 ? '+' : ''}${value.toFixed(1)}%`

export default function QuarterlyResultsPage() {
  const [params, setParams] = useSearchParams()
  const { theme } = useOutletContext()
  const [attempt, setAttempt] = useState(0)
  const [comparison, setComparison] = useState('yoy')
  const [selected, setSelected] = useState(null)
  const [response, setResponse] = useState({ key: null, data: null, error: false })
  const request = new URLSearchParams()
  for (const key of ['market', 'quarter', 'industry', 'q', 'sort', 'page']) {
    if (params.get(key)) request.set(key, params.get(key))
  }
  const queryString = request.toString()
  const requestKey = `${queryString}:${attempt}`
  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(() => {
      api.get(`/results/imported?${queryString}`, { signal: controller.signal }).then(({ data }) => {
        setResponse({ key: requestKey, data, error: false })
      }).catch(() => {
        if (!controller.signal.aborted) setResponse({ key: requestKey, data: null, error: true })
      })
    }, 200)
    return () => { clearTimeout(timer); controller.abort() }
  }, [queryString, requestKey])
  const loading = response.key !== requestKey
  const data = loading ? null : response.data
  const filters = (name, value) => {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    if (name !== 'page') next.delete('page')
    if (name === 'market') { next.delete('industry'); next.delete('quarter') }
    setParams(next, { replace: name === 'q' })
  }
  const clear = () => setParams(params.get('market') ? { market: params.get('market') } : {})
  const refresh = () => setAttempt(value => value + 1)
  const options = data || response.data
  const market = params.get('market') || 'IN'
  const quarter = params.get('quarter') || ''
  const industry = params.get('industry') || ''
  const page = data?.page || 1
  const pages = Math.max(1, Math.ceil((data?.total || 0) / (data?.page_size || 12)))
  return <>
    <section className="market-hero"><div className="stock-container market-heading-row">
      <div><p className="market-eyebrow">Discover / Quarterly results</p><h1>Yahoo-imported quarterly comparisons</h1><p className="market-description">Follow the numbers behind the businesses. Compare sales, earnings and growth across the companies you track.</p></div>
      <Button variant="outline" size="sm" onClick={refresh} disabled={loading}><RefreshCw size={14} />Reload results</Button>
    </div></section>
    <section className="stock-section results-section" aria-label="Quarterly results"><div className="stock-container"><div className="filing-view-links"><Link className="market-link" to="/results">Automated latest filings &amp; AI summaries<ArrowRight size={14} /></Link></div>
      <div className="results-filters">
        <label>Market<select aria-label="Market" value={market} onChange={event => filters('market', event.target.value)}><option value="IN">India</option><option value="US">United States</option><option value="ALL">All markets</option></select></label>
        <label>Reporting quarter<select aria-label="Reporting quarter" value={quarter} onChange={event => filters('quarter', event.target.value)}><option value="">Latest per company</option>{[...new Set([...(options?.quarters || []), ...(quarter ? [quarter] : [])])].sort().reverse().map(value => <option key={value} value={value}>Ending {dateLabel(value)}</option>)}</select></label>
        <label>By industry<select aria-label="By industry" value={industry} onChange={event => filters('industry', event.target.value)}><option value="">All industries</option>{[...new Set([...(options?.industries || []), ...(industry ? [industry] : [])])].sort().map(value => <option key={value}>{value}</option>)}</select></label>
        <label className="results-search">Company<SearchInput aria-label="Search results by company or symbol" placeholder="Company or symbol…" value={params.get('q') || ''} maxLength={100} onChange={event => filters('q', event.target.value)} /></label>
      </div>
      <p className="stock-source-note results-disclosure"><CalendarDays size={14} />Dates refer to fiscal quarter ends. Announcement dates and standalone/consolidated basis are not supplied by this data source.</p>
      <div className="results-summary" aria-live="polite">{[['Matching companies', data?.total], ['Sales growing YoY', data?.growing_sales], ['Profit growing YoY', data?.growing_profit]].map(([label, value]) => <Card key={label}><span>{label}</span><strong>{value ?? '—'}</strong></Card>)}</div>
      <div className="results-toolbar"><div><h2>Quarterly performance</h2><p className="stock-source-note">{data ? `${data.universe_count} imported companies with quarterly records` : 'Imported company financials'} · Values in INR crore or reporting-currency millions; EPS per share.</p></div>
        <div className="results-controls"><Segmented label="Growth comparison" value={comparison} onChange={setComparison} options={[{ value: 'yoy', label: 'YoY' }, { value: 'qoq', label: 'QoQ' }]} />
          <label className="results-sort"><span className="sr-only">Sort results</span><select aria-label="Sort results" value={params.get('sort') || 'latest'} onChange={event => filters('sort', event.target.value)}><option value="latest">Latest quarter first</option><option value="name">Company name</option><option value="sales_growth">Sales growth (YoY)</option><option value="profit_growth">Profit growth (YoY)</option></select></label>
        </div>
      </div>
      {loading ? <div className="results-grid" aria-label="Loading quarterly results" aria-busy="true">{[0, 1, 2, 3].map(key => <Skeleton key={key} className="results-skeleton" />)}</div>
        : response.error ? <EmptyState error onRetry={refresh}>Quarterly results are temporarily unavailable. Please retry.</EmptyState>
          : !data?.items.length ? <EmptyState>No quarterly results match this selection. Try another reporting quarter or clear the filters.{data?.universe_count === 0 && <span> Quarterly records need to be imported before results can appear.</span>}<Button variant="outline" size="sm" onClick={clear}>Clear filters</Button></EmptyState>
            : <div className="results-grid">{data.items.map(item => <Card key={item.symbol} className="result-card">
              <div className="result-card-heading"><div><Link to={`/stock/${encodeURIComponent(item.symbol)}`}><h3>{item.name}</h3></Link><p>{item.symbol} · {item.exchange}</p></div><span className="result-quarter">{dateLabel(item.quarter_end)}</span></div>
              <p className="result-industry">{item.industry || item.sector || 'Industry unavailable'}</p>
              <div className="result-metrics-heading"><span>{item.currency} {item.currency === 'INR' ? 'Cr' : 'million'} · EPS per share</span><span>{comparison === 'yoy' ? 'vs year-ago quarter' : 'vs preceding quarter'}</span></div>
              <dl className="result-metrics">{METRICS.map(([key, label]) => {
                const metric = item.metrics[key]
                const change = metric[comparison]
                return <div key={key}><dt>{label}{key === 'eps' && metric.source_field && <small>{metric.source_field === 'Diluted EPS' ? 'Diluted' : 'Basic'}</small>}</dt><dd>{amount(metric.value, item.currency, key === 'eps')}</dd><dd className={change.value == null ? 'results-muted' : change.value < 0 ? 'is-loss' : 'is-gain'} title={change.reason || undefined}>{growthLabel(change.value)}</dd></div>
              })}</dl>
              <div className="result-card-footer"><Button variant="ghost" size="sm" aria-label={`View comparisons for ${item.name}`} onClick={() => setSelected(item)}>View comparisons<ArrowRight size={14} /></Button><a className="market-link" href={item.source_url} target="_blank" rel="noopener noreferrer">Statements<ExternalLink size={13} /></a></div>
            </Card>)}</div>}
      {data?.total > 0 && <nav className="results-pagination" aria-label="Results pages"><Button variant="outline" size="sm" disabled={page <= 1} onClick={() => filters('page', String(page - 1))}>Previous</Button><span>Page {page} of {pages} · {data.total} companies</span><Button variant="outline" size="sm" disabled={page >= pages} onClick={() => filters('page', String(page + 1))}>Next</Button></nav>}
      <p className="stock-source-note results-note">Missing figures are shown as —. Growth requires comparable quarters, matching currencies and a positive prior figure. This feed covers the imported universe; it is not an exchange-wide announcement feed.</p>
      {data?.updated_at && <p className="stock-source-note">Financial data last imported: {new Date(data.updated_at).toLocaleString('en-GB')} (your local time). Reload reads the latest stored records.</p>}
    </div></section>
    <StockModal open={Boolean(selected)} onOpenChange={open => { if (!open) setSelected(null) }} theme={theme} title={selected ? `${selected.name} · Quarterly comparisons` : 'Quarterly comparisons'} description="Reported figures from the imported provider statements. Amounts use the reporting currency; EPS is per share.">
      {selected && <><p className="stock-source-note">Quarter ending {dateLabel(selected.quarter_end)} · {selected.currency} {selected.currency === 'INR' ? 'crore' : 'million'}. Reporting basis is not identified by the provider.</p>
        <div className="results-history"><Table><TableHeader><TableRow><TableHead>Quarter ending</TableHead>{METRICS.map(([key, label]) => <TableHead key={key}>{label}</TableHead>)}</TableRow></TableHeader><TableBody>{selected.history.map(row => <TableRow key={row.quarter_end}><TableCell>{dateLabel(row.quarter_end)}<small>{row.currency}</small></TableCell>{METRICS.map(([key]) => <TableCell key={key}>{amount(row[key], row.currency, key === 'eps')}</TableCell>)}</TableRow>)}</TableBody></Table></div>
        <div className="results-comparison-notes">{METRICS.map(([key, label]) => <p key={key}><strong>{label}:</strong> YoY {growthLabel(selected.metrics[key].yoy.value)} · QoQ {growthLabel(selected.metrics[key].qoq.value)}{selected.metrics[key].yoy.reason && <small>YoY: {selected.metrics[key].yoy.reason}.</small>}{selected.metrics[key].qoq.reason && <small>QoQ: {selected.metrics[key].qoq.reason}.</small>}</p>)}</div>
        <p className="stock-source-note">YoY comparison: {selected.previous_year_end ? dateLabel(selected.previous_year_end) : 'unavailable'} · QoQ comparison: {selected.previous_quarter_end ? dateLabel(selected.previous_quarter_end) : 'unavailable'}. No announcement date is available.</p>
        <div className="results-dialog-links"><Link className="market-link" to={`/stock/${encodeURIComponent(selected.symbol)}`}>Open company<ArrowRight size={14} /></Link><a className="market-link" href={selected.source_url} target="_blank" rel="noopener noreferrer">Source financial statements<ExternalLink size={14} /></a></div>
      </>}
    </StockModal>
  </>
}
