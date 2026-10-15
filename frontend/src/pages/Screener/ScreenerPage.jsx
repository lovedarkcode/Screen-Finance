import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowUpDown, ArrowUpRight, RefreshCw, Search, Star } from 'lucide-react'
import stockService from '@/services/stock.service'
import watchlistService from '@/services/watchlist.service'
import { EmptyState, PriceChange, SectionTitle } from '@/components/stock/StockUI'
import { money, number } from '@/components/stock/stock-format'
import toast from 'react-hot-toast'

function SectorStocks({ sector }) {
  const [state, setState] = useState({ stocks: [], loading: true, error: false })
  const [attempt, setAttempt] = useState(0)
  const [watchlist, setWatchlist] = useState({ items: [], loading: true, error: false })
  const [pending, setPending] = useState([])
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState({ key: 'name', direction: 1 })
  useEffect(() => {
    let live = true
    stockService.getSectorStocks(sector.id).then(stocks => { if (live) setState({ stocks, loading: false, error: false }) })
      .catch(() => { if (live) setState({ stocks: [], loading: false, error: true }) })
    return () => { live = false }
  }, [sector.id, attempt])
  useEffect(() => {
    let live = true
    watchlistService.getWatchlist().then(data => { if (live) setWatchlist({ items: data.items || [], loading: false, error: false }) })
      .catch(() => { if (live) setWatchlist({ items: [], loading: false, error: true }) })
    return () => { live = false }
  }, [])
  const refresh = () => { setState({ stocks: [], loading: true, error: false }); setAttempt(value => value + 1) }
  const toggle = async symbol => {
    if (pending.includes(symbol)) return
    setPending(value => [...value, symbol])
    const saved = watchlist.items.includes(symbol)
    try {
      if (saved) await watchlistService.removeFromWatchlist(symbol)
      else await watchlistService.addToWatchlist(symbol)
      setWatchlist(value => ({ ...value, items: saved ? value.items.filter(item => item !== symbol) : [...value.items, symbol] }))
      toast.success(saved ? 'Removed from watchlist' : 'Added to watchlist')
    } catch { toast.error('Could not update your watchlist. Please try again.') }
    finally { setPending(value => value.filter(item => item !== symbol)) }
  }
  const changes = state.stocks.map(stock => stock.changePercent).filter(value => value != null && Number.isFinite(Number(value))).map(Number)
  const average = changes.length ? changes.reduce((sum, value) => sum + value, 0) / changes.length : null
  const filtered = state.stocks.filter(stock => `${stock.name} ${stock.symbol}`.toLowerCase().includes(query.trim().toLowerCase())).sort((a, b) => {
    const x = a[sort.key], y = b[sort.key]
    if (x == null) return y == null ? 0 : 1
    if (y == null) return -1
    return sort.direction * (sort.key === 'name' ? String(x).localeCompare(String(y)) : Number(x) - Number(y))
  })
  const sortBy = key => setSort(value => ({ key, direction: value.key === key ? -value.direction : key === 'name' ? 1 : -1 }))
  return <>
    <section className="stock-section stock-band"><div className="stock-container">
      <div className="market-screen-summary"><div><p className="market-eyebrow">Selected sector</p><SectionTitle>{sector.name}</SectionTitle><p className="market-description">{sector.description}</p></div>
        <div className="market-screen-stats"><div><small>Constituents</small><strong>{sector.tickerCount ?? '—'}</strong></div><div><small>Average 1D return</small><PriceChange value={average} /></div></div>
      </div><p className="stock-source-note">Equal-weight average of {changes.length} available constituent returns. Quotes may be delayed.</p>
    </div></section>
    <section className="stock-section"><div className="stock-container">
      <SectionTitle extra={<span className="stock-source-note">{state.loading ? 'Loading constituents…' : `${filtered.length} of ${state.stocks.length} companies`}</span>}>Sector Constituents</SectionTitle>
      <div className="market-table-toolbar"><label className="market-filter"><Search size={16} /><input aria-label="Filter sector stocks" placeholder="Search by name or symbol…" value={query} onChange={event => setQuery(event.target.value)} /></label><button className="stock-button" onClick={refresh} disabled={state.loading}><RefreshCw size={14} />Refresh quotes</button></div>
      {watchlist.error && <p className="stock-source-note" role="status">Watchlist unavailable. Reload the page to enable saved-stock actions.</p>}
      {state.loading ? <div className="market-loading" aria-label="Loading sector stocks" aria-busy="true">{[0, 1, 2, 3, 4].map(i => <div className="sk" key={i} />)}</div> : state.error ? <EmptyState error onRetry={refresh}>Sector quotes are temporarily unavailable.</EmptyState> : !filtered.length ? <EmptyState>{query.trim() ? `No companies match “${query}” in ${sector.name}.` : 'No constituents are available for this sector.'}{query && <button className="stock-button" onClick={() => setQuery('')}>Clear search</button>}</EmptyState> : <div className="market-table-scroll"><table className="market-table"><thead><tr>
        {[['name', 'Company'], ['price', 'Price'], ['change', '1D Change'], ['changePercent', '1D Return']].map(([key, label]) => <th key={key} aria-sort={sort.key === key ? sort.direction === 1 ? 'ascending' : 'descending' : 'none'}><button onClick={() => sortBy(key)}>{label}<ArrowUpDown size={11} /></button></th>)}<th>Watchlist / View</th>
      </tr></thead><tbody>{filtered.map(stock => <tr key={stock.symbol}><td><Link to={`/stock/${encodeURIComponent(stock.symbol)}`}><strong>{stock.name}</strong><small>{stock.symbol}</small></Link></td><td><strong>{money(stock.price)}</strong>{stock.price == null && <small>Quote unavailable</small>}</td><td className={stock.change == null ? '' : stock.change < 0 ? 'is-loss' : 'is-gain'}>{stock.change == null ? '—' : `${stock.change > 0 ? '+' : ''}${number(stock.change)}`}</td><td><PriceChange value={stock.changePercent} badge /></td><td><div className="market-table-actions"><button className="stock-icon-button" aria-label={`${watchlist.items.includes(stock.symbol) ? 'Remove' : 'Add'} ${stock.symbol} ${watchlist.items.includes(stock.symbol) ? 'from' : 'to'} watchlist`} aria-pressed={watchlist.items.includes(stock.symbol)} disabled={watchlist.loading || watchlist.error || pending.includes(stock.symbol)} onClick={() => toggle(stock.symbol)}><Star size={16} fill={watchlist.items.includes(stock.symbol) ? 'currentColor' : 'none'} /></button><Link className="stock-icon-button" aria-label={`View ${stock.symbol}`} to={`/stock/${encodeURIComponent(stock.symbol)}`}><ArrowUpRight size={16} /></Link></div></td></tr>)}</tbody></table></div>}
      <p className="stock-source-note">Select a company to view its price chart, fundamentals, financial results and peers.</p>
      <p className="stock-source-note market-mobile-hint">Swipe the table horizontally to see all values and watchlist actions.</p>
    </div></section>
  </>
}

export default function ScreenerPage() {
  const [params, setParams] = useSearchParams()
  const [state, setState] = useState({ sectors: [], loading: true, error: false })
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let live = true
    stockService.getSectors().then(sectors => { if (live) setState({ sectors, loading: false, error: false }) })
      .catch(() => { if (live) setState({ sectors: [], loading: false, error: true }) })
    return () => { live = false }
  }, [attempt])
  const active = state.sectors.find(sector => sector.id === params.get('sector')) || state.sectors[0]
  return <>
    <section className="market-hero"><div className="stock-container"><p className="market-eyebrow">Discover / Screens</p><h1>Indian Market Screener</h1><p className="market-description">Explore sectors, compare constituent performance and find your next company to research.</p></div></section>
    <section className="stock-section stock-band-alt"><div className="stock-container"><SectionTitle>Explore Sectors</SectionTitle>
      {state.loading ? <div className="market-loading" aria-label="Loading sectors" aria-busy="true"><div className="sk" /></div> : state.error ? <EmptyState error onRetry={() => { setState({ sectors: [], loading: true, error: false }); setAttempt(value => value + 1) }}>Market sectors are temporarily unavailable.</EmptyState> : !state.sectors.length ? <EmptyState>No sectors are available yet.</EmptyState> : <div className="market-tabs" aria-label="Market sectors">{state.sectors.map(sector => <button key={sector.id} aria-pressed={active?.id === sector.id} onClick={() => setParams(previous => { const next = new URLSearchParams(previous); next.set('sector', sector.id); return next })}>{sector.name}<span> · {sector.tickerCount}</span></button>)}</div>}
    </div></section>
    {active && <SectorStocks key={active.id} sector={active} />}
    <footer className="stock-source-footer stock-container">Asset Hunter · Market data: Yahoo Finance / yfinance. Availability varies by company.</footer>
  </>
}
