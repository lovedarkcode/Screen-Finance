import { useEffect, useState } from 'react'
import { Link, useOutletContext, useSearchParams } from 'react-router-dom'
import { ArrowRight, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { SearchInput } from '@/components/ui/search-input'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, StockModal } from '@/components/stock/StockUI'
import api from '@/services/api'
import './quarterly-results.css'

const dateLabel = value => value ? new Date(`${value}T00:00:00Z`).toLocaleDateString('en-GB', { timeZone: 'UTC' }) : 'Unavailable'
const numeric = value => value == null ? null : Number(value)
const amount = (value, currency, scale = true) => value == null ? '—' : (Number(value) / (scale ? currency === 'INR' ? 1e7 : 1e6 : 1)).toLocaleString('en-GB', { maximumFractionDigits: 2, minimumFractionDigits: 2 })
const percent = value => value == null ? '—' : `${Number(value).toFixed(2)}%`

function Summary({ filing }) {
  const sections = filing.ai_summary_json
  if (filing.summary_status !== 'completed' || !sections) return <p className="stock-source-note filing-summary-status">{filing.summary_status === 'failed' ? 'AI summary unavailable. The financial figures are saved; the worker can retry after the provider issue is resolved.' : 'AI summary is queued or processing. Reload to check its status.'}</p>
  return <div className="filing-summary">{[['positive_triggers', 'Positive triggers'], ['red_flags', 'Warning red flags'], ['executive_summary', 'Executive summary']].map(([key, label]) => <section key={key}><h4>{label}</h4>{key === 'executive_summary' ? <p>{sections[key].join(' ')}</p> : sections[key].length ? <ul>{sections[key].map(text => <li key={text}>{text}</li>)}</ul> : <p>No {key === 'red_flags' ? 'red flag' : 'positive trigger'} selected from the available evidence.</p>}</section>)}</div>
}

export default function LatestFilingsPage() {
  const [params, setParams] = useSearchParams()
  const { theme } = useOutletContext()
  const [attempt, setAttempt] = useState(0)
  const [response, setResponse] = useState({ key: null, data: null, error: false })
  const [history, setHistory] = useState({ ticker: null, data: null, error: false })
  const [historyAttempt, setHistoryAttempt] = useState(0)
  const query = new URLSearchParams()
  for (const key of ['market', 'exchange', 'status', 'q', 'page']) if (params.get(key)) query.set(key, params.get(key))
  query.set('page_size', '12')
  const queryString = query.toString()
  const requestKey = `${queryString}:${attempt}`
  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(() => {
      api.get(`/results?${queryString}`, { signal: controller.signal }).then(({ data }) => setResponse({ key: requestKey, data, error: false }))
        .catch(() => { if (!controller.signal.aborted) setResponse({ key: requestKey, data: null, error: true }) })
    }, 200)
    return () => { clearTimeout(timer); controller.abort() }
  }, [queryString, requestKey])
  const ticker = history.ticker
  useEffect(() => {
    if (!ticker) return
    const controller = new AbortController()
    api.get(`/results/${encodeURIComponent(ticker)}?page_size=100`, { signal: controller.signal })
      .then(({ data }) => setHistory({ ticker, data, error: false }))
      .catch(() => { if (!controller.signal.aborted) setHistory({ ticker, data: null, error: true }) })
    return () => controller.abort()
  }, [ticker, historyAttempt])
  const loading = response.key !== requestKey
  const data = loading ? null : response.data
  const setFilter = (name, value) => {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    if (name !== 'page') next.delete('page')
    setParams(next, { replace: name === 'q' })
  }
  const pages = Math.max(1, Math.ceil((data?.total || 0) / (data?.page_size || 12)))
  return <>
    <section className="market-hero"><div className="stock-container market-heading-row"><div><p className="market-eyebrow">Quarterly results / Automated filings</p><h1>Latest quarterly results</h1><p className="market-description"></p></div><Button variant="outline" size="sm" onClick={() => setAttempt(value => value + 1)} disabled={loading}><RefreshCw size={14} />Reload filings</Button></div></section>
    <section className="stock-section results-section" aria-label="Automated quarterly filings"><div className="stock-container">
      <div className="filing-view-links"><Link className="market-link" to="/results/imported"></Link><span className="stock-source-note">Yahoo Finance/yfinance{data ? ` · ${data.total.toLocaleString()} listings` : ''}</span></div>
      <div className="results-filters filing-filters"><label>Market<select aria-label="Filing market" value={params.get('market') || 'ALL'} onChange={event => setFilter('market', event.target.value)}><option value="ALL">All markets</option><option value="IN">India</option><option value="US">United States</option></select></label><label>Exchange<select aria-label="Results exchange" value={params.get('exchange') || ''} onChange={event => setFilter('exchange', event.target.value)}><option value="">All exchanges</option>{['NSE', 'BSE', 'NYSE', 'NASDAQ'].map(value => <option key={value} value={value}>{value}</option>)}</select></label><label>Data status<select aria-label="Results data status" value={params.get('status') || 'all'} onChange={event => setFilter('status', event.target.value)}>{[['all', 'All listings'], ['ready', 'Results available'], ['pending', 'Awaiting first check'], ['unavailable', 'Yahoo data unavailable'], ['error', 'Retry scheduled']].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Company<SearchInput aria-label="Search filings by company or ticker" placeholder="Company or ticker…" value={params.get('q') || ''} maxLength={100} onChange={event => setFilter('q', event.target.value)} /></label></div>
      {data?.coverage && <p className="filing-access-note" role="status">{data.coverage.listed.toLocaleString()} exchange listings · {data.coverage.with_results.toLocaleString()} with saved quarterly results · {data.coverage.pending.toLocaleString()} awaiting first check · {data.coverage.unavailable.toLocaleString()} unavailable on Yahoo · {data.coverage.error.toLocaleString()} scheduled for retry.</p>}
      {data?.catalog_status && Object.entries(data.catalog_status).some(([, value]) => value.status !== 'ok') && <p className="filing-access-note" role="status">Some exchange directories could not refresh. The last successful catalog is retained; check the worker status before assuming complete coverage.</p>}
      <p className="stock-source-note results-note">Sorted by fiscal quarter end, not announcement date. Fiscal year and quarter labels are inferred from the provider's annual period end. NSE and BSE listings are separate even when they share an ISIN. Missing reports are never replaced with estimated figures.</p>
      {loading ? <div className="results-grid" aria-label="Loading company filings" aria-busy="true">{[0, 1].map(key => <Skeleton key={key} className="results-skeleton" />)}</div>
        : response.error ? <EmptyState error onRetry={() => setAttempt(value => value + 1)}>Company filings are temporarily unavailable.</EmptyState>
          : !data?.items.length ? <EmptyState>No exchange listings match this selection.<Button variant="outline" size="sm" onClick={() => setParams({})}>Clear filters</Button></EmptyState>
            : <div className="results-grid">{data.items.map(entry => {
              const filing = entry.latest_result
              if (!filing) return <Card className="result-card filing-card" key={entry.company_id}>
                <div className="result-card-heading"><div><h3>{entry.company_name}</h3><p>{entry.ticker} · {entry.exchange}</p></div><span className="result-quarter">{entry.data_status === 'pending' ? 'Awaiting first check' : entry.data_status === 'unavailable' ? 'Data unavailable' : 'Retry scheduled'}</span></div>
                <p className="stock-source-note">{entry.data_status === 'pending' ? 'This listing is queued for Yahoo quarterly-statement discovery.' : entry.data_status === 'unavailable' ? 'Yahoo did not return usable quarterly statements for this listing. The worker will check again.' : 'The last request failed. The worker will retry automatically.'}</p>
                <p className="stock-source-note">{entry.isin ? `ISIN ${entry.isin} · ` : ''}{entry.checked_at ? `Last checked ${new Date(entry.checked_at).toLocaleString('en-GB')}` : 'No provider check yet'}{entry.data_error ? ` · ${entry.data_error}` : ''}</p>
              </Card>
              return <Card className="result-card filing-card" key={entry.company_id}>
              <div className="result-card-heading"><div><Link to={`/stock/${encodeURIComponent(filing.ticker)}`}><h3>{filing.company_name}</h3></Link><p>{filing.ticker} · {filing.exchange}</p></div><span className="result-quarter">FY{filing.fiscal_year} {filing.quarter_period}</span></div>
              <p className="result-industry">Period ended {dateLabel(filing.period_end)} · Announcement date unavailable · Revision {filing.revision}</p>
              <div className="result-metrics-heading"><span>{filing.currency} {filing.currency === 'INR' ? 'crore' : 'million'} · EPS per share</span><span>YoY growth</span></div>
              <dl className="result-metrics">{[['revenue', 'Revenue'], ['net_income', 'Net income'], ['eps', `${filing.eps_basis || 'Reported'} EPS`], ['operating_margin', 'Operating margin']].map(([field, label]) => {
                const change = filing.comparisons.metrics[field].yoy
                const delta = numeric(change.value)
                return <div key={field}><dt>{label}</dt><dd>{field === 'operating_margin' ? percent(filing[field]) : amount(filing[field], filing.currency, field !== 'eps')}</dd><dd className={delta == null ? 'results-muted' : delta < 0 ? 'is-loss' : 'is-gain'} title={change.reason || undefined}>{delta == null ? '—' : `${delta > 0 ? '+' : ''}${delta.toFixed(1)}${field === 'operating_margin' ? ' pp' : '%'}`}</dd></div>
              })}</dl>
              {entry.data_status === 'error' && <p className="stock-source-note">Last refresh failed; showing previously saved results. Retry scheduled.</p>}<Summary filing={filing} />
              <div className="result-card-footer"><Button variant="ghost" size="sm" onClick={() => setHistory({ ticker: filing.ticker, data: null, error: false })}>View {filing.ticker} history<ArrowRight size={14} /></Button><span className="stock-source-note">{filing.summary_model || `Summary ${filing.summary_status}`}</span></div>
            </Card>})}</div>}
      {data?.total > 0 && <nav className="results-pagination" aria-label="Filing pages"><Button variant="outline" size="sm" disabled={data.page <= 1} onClick={() => setFilter('page', String(data.page - 1))}>Previous</Button><span>Page {data.page} of {pages}</span><Button variant="outline" size="sm" disabled={data.page >= pages} onClick={() => setFilter('page', String(data.page + 1))}>Next</Button></nav>}
      {data?.poll_status && <p className="stock-source-note results-note">Last worker run: {new Date(data.poll_status.started_at).toLocaleString('en-GB')} (your local time) · {data.poll_status.status.replaceAll('_', ' ')}. Reload reads saved data; it does not call Yahoo.</p>}
    </div></section>
    <StockModal open={Boolean(ticker)} onOpenChange={open => { if (!open) setHistory({ ticker: null, data: null, error: false }) }} theme={theme} title={`${ticker || ''} · Quarterly history`} description="Reported quarterly financials and verified year-on-year comparisons. Values retain each period's reporting currency.">
      {history.error ? <EmptyState error onRetry={() => setHistoryAttempt(value => value + 1)}>Quarterly history is temporarily unavailable.</EmptyState> : !history.data ? <Skeleton className="results-skeleton" aria-label="Loading filing history" /> : !history.data.items.length ? <EmptyState>No provider filings are stored for this company.</EmptyState> : <div className="results-history"><Table><TableHeader><TableRow>{['Fiscal period', 'Period end', 'Announcement date', 'Revenue', 'Net income', 'EPS', 'Operating margin', 'Revenue YoY', 'Profit YoY'].map(label => <TableHead key={label}>{label}</TableHead>)}</TableRow></TableHeader><TableBody>{history.data.items.map(row => <TableRow key={row.id}><TableCell>FY{row.fiscal_year} {row.quarter_period}<small>{row.currency} {row.currency === 'INR' ? 'crore' : 'million'}</small></TableCell><TableCell>{dateLabel(row.period_end)}</TableCell><TableCell>{dateLabel(row.filing_date)}<small>{row.filing_date_kind === 'filing' ? 'Filing date' : 'Unavailable from Yahoo'}</small></TableCell><TableCell>{amount(row.revenue, row.currency)}</TableCell><TableCell>{amount(row.net_income, row.currency)}</TableCell><TableCell>{amount(row.eps, row.currency, false)}<small>{row.eps_basis}</small></TableCell><TableCell>{percent(row.operating_margin)}</TableCell><TableCell>{percent(row.comparisons.metrics.revenue.yoy.value)}</TableCell><TableCell>{percent(row.comparisons.metrics.net_income.yoy.value)}</TableCell></TableRow>)}</TableBody></Table></div>}
    </StockModal>
  </>
}
