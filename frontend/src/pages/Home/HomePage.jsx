import { Segmented } from '@/components/ui/segmented'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table'
import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowRight, Layers, Newspaper, RefreshCw } from 'lucide-react'
import stockService from '@/services/stock.service'
import api from '@/services/api'
import StockChart from '@/components/stock/StockChart'
import NaturalLanguageScreener from '@/components/screener/NaturalLanguageScreener'
import { EmptyState, PriceChange, SectionTitle } from '@/components/stock/StockUI'
import { money, marketTime, number } from '@/components/stock/stock-format'

const INDICES = [
  { symbol: '^NSEI', name: 'NIFTY 50' }, { symbol: '^BSESN', name: 'SENSEX' },
  { symbol: '^NSEBANK', name: 'BANK NIFTY' }, { symbol: '^CNXIT', name: 'NIFTY IT' },
]
const STOCKS = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'TATAMOTORS.NS', 'SBIN.NS', 'BHARTIARTL.NS']

export default function HomePage() {
  const [searchParams] = useSearchParams()
  const screenerOpen = searchParams.get('screener') === 'ai'
  const screenerRef = useRef(null)
  useEffect(() => {
    if (!screenerOpen) return
    screenerRef.current?.scrollIntoView({ block: 'start' })
    screenerRef.current?.querySelector('textarea')?.focus({ preventScroll: true })
  }, [screenerOpen])
  const [quotes, setQuotes] = useState({})
  const [loading, setLoading] = useState(true)
  const [attempt, setAttempt] = useState(0)
  const [benchmark, setBenchmark] = useState(INDICES[0])
  const [tab, setTab] = useState('all')
  const [sectors, setSectors] = useState({ items: [], loading: true, error: false })
  const [news, setNews] = useState({ items: [], loading: true, error: false })
  useEffect(() => {
    let live = true
    Promise.allSettled([...INDICES.map(index => index.symbol), ...STOCKS].map(async symbol => {
      try {
        const quote = await stockService.getStock(symbol)
        if (live) setQuotes(value => ({ ...value, [symbol]: quote }))
      } catch { if (live) setQuotes(value => ({ ...value, [symbol]: { error: true } })) }
    })).then(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [attempt])
  useEffect(() => {
    let live = true
    stockService.getSectors().then(items => { if (live) setSectors({ items, loading: false, error: false }) })
      .catch(() => { if (live) setSectors({ items: [], loading: false, error: true }) })
    api.get('/news').then(({ data }) => { if (live) setNews({ items: data.items || [], loading: false, error: false }) })
      .catch(() => { if (live) setNews({ items: [], loading: false, error: true }) })
    return () => { live = false }
  }, [attempt])
  const refresh = () => { setQuotes({}); setLoading(true); setSectors({ items: [], loading: true, error: false }); setNews({ items: [], loading: true, error: false }); setAttempt(value => value + 1) }
  const stocks = STOCKS.map(symbol => quotes[symbol]).filter(quote => quote?.price != null && !quote.error)
  const measured = stocks.filter(stock => stock.changePercent != null)
  const advances = measured.filter(stock => stock.changePercent > 0).length
  const declines = measured.filter(stock => stock.changePercent < 0).length
  const unchanged = measured.length - advances - declines
  const movers = stocks.filter(stock => tab === 'gainers' ? stock.changePercent > 0 : tab === 'losers' ? stock.changePercent < 0 : true)
    .sort((a, b) => tab === 'losers' ? a.changePercent - b.changePercent : tab === 'gainers' ? b.changePercent - a.changePercent : a.name.localeCompare(b.name))
  return <>
    <section className="market-hero"><div className="stock-container"><div className="market-heading-row"><div><p className="market-eyebrow">Discover / Feed</p><h1>Your market, at a glance</h1><p className="market-description">Follow Indian benchmarks, explore company performance and move from the market view to the details that matter.</p></div><Button variant="outline" size="sm" className="stock-button" onClick={refresh} disabled={loading}><RefreshCw size={14} />Refresh market</Button></div></div></section>
    {screenerOpen && <div ref={screenerRef} style={{ scrollMarginTop: 110 }}><NaturalLanguageScreener /></div>}
    <section className="stock-section stock-band-alt"><div className="stock-container"><SectionTitle extra={<span className="stock-source-note">Select an index to explore its history</span>}>Market Overview</SectionTitle>
      <div className="market-index-grid">{INDICES.map(index => {
        const quote = quotes[index.symbol]
        return <Card asChild><button className="market-card market-index-card" key={index.symbol} aria-pressed={benchmark.symbol === index.symbol} onClick={() => setBenchmark(index)}><span>{index.name}</span>
          {!quote ? <Skeleton className="sk" style={{ height: 63, marginTop: 10 }} aria-label={`Loading ${index.name}`} /> : <><strong>{number(quote.price)}</strong><PriceChange value={quote.changePercent} /><small>{quote.error || quote.price == null ? 'Quote unavailable · try refresh' : quote.date ? marketTime(quote.date) : 'Latest provider quote · may be delayed'}</small></>}
        </button></Card>
      })}</div>
    </div></section>
    <StockChart key={`${benchmark.symbol}-${attempt}`} symbol={benchmark.symbol} title={`${benchmark.name} Performance`} />
    <section className="stock-section stock-band-alt"><div className="stock-container market-grid">
      <Card className="market-card"><SectionTitle>Market Movers</SectionTitle><Segmented className="market-tabs" label="Market mover filters" value={tab} onChange={setTab} options={[['all', 'All tracked'], ['gainers', 'Gainers'], ['losers', 'Losers']].map(([value, label]) => ({ value, label }))} />
        <p className="stock-source-note" style={{ marginBottom: 16 }}>A curated sample of eight companies. All tracked is ordered by company name.</p>
        {loading && !stocks.length ? <div className="market-loading" aria-busy="true" aria-label="Loading market movers"><Skeleton className="sk" /><Skeleton className="sk" /><Skeleton className="sk" /></div> : !movers.length ? <EmptyState error={!stocks.length} onRetry={!stocks.length ? refresh : undefined}>{stocks.length ? `No ${tab} in the available tracked companies.` : 'Tracked company quotes are temporarily unavailable.'}</EmptyState> : <div className="market-table-scroll"><Table className="market-table market-movers-table"><TableHeader><TableRow><TableHead>Company</TableHead><TableHead>Price</TableHead><TableHead>1D Return</TableHead></TableRow></TableHeader><TableBody>{movers.map(stock => <TableRow key={stock.symbol}><TableCell><Link to={`/stock/${encodeURIComponent(stock.symbol)}`}><strong>{stock.name}</strong><small>{stock.symbol}</small></Link></TableCell><TableCell>{money(stock.price)}</TableCell><TableCell><PriceChange value={stock.changePercent} badge /></TableCell></TableRow>)}</TableBody></Table></div>}
        <p className="stock-source-note">{stocks.length} of {STOCKS.length} tracked quotes available{loading ? ' · Still loading…' : ''}</p><Link className="market-link" style={{ marginTop: 18 }} to="/screens">Explore all sectors<ArrowRight size={14} /></Link>
      </Card>
      <Card className="market-card"><SectionTitle>Tracked Market Breadth</SectionTitle><p className="market-description">Today’s direction across the tracked companies with available returns.</p>
        <div className="market-stat-list"><div><span>Advancing</span><strong className="is-gain">{measured.length ? advances : '—'}</strong></div><div><span>Declining</span><strong className="is-loss">{measured.length ? declines : '—'}</strong></div><div><span>Unchanged</span><strong>{measured.length ? unchanged : '—'}</strong></div></div>
        {!!(advances + declines) && <div className="market-breadth" aria-label={`${advances} advancing and ${declines} declining`}><span style={{ flex: advances }} /><span style={{ flex: declines }} /></div>}
        <p className="stock-source-note">Sample: {measured.length} companies. This is a tracked-company snapshot, not exchange-wide market breadth.</p><Link className="market-link" style={{ marginTop: 22 }} to="/watchlist">Open your watchlist<ArrowRight size={14} /></Link>
      </Card>
    </div></section>
    <section className="stock-section"><div className="stock-container"><SectionTitle extra={<Link className="market-link" to="/screens">Open Screener<ArrowRight size={14} /></Link>}>Explore Sectors</SectionTitle>
      {sectors.loading ? <div className="market-loading" aria-label="Loading sectors" aria-busy="true"><Skeleton className="sk" /></div> : sectors.error ? <EmptyState error onRetry={refresh}>Sector discovery is temporarily unavailable.</EmptyState> : !sectors.items.length ? <EmptyState>No market sectors available.</EmptyState> : <div className="market-sector-grid">{sectors.items.map(sector => <Card asChild><Link key={sector.id} className="market-card market-sector-card" to={`/screens?sector=${encodeURIComponent(sector.id)}`}><Layers size={18} /><span><strong>{sector.name}</strong><small>{sector.tickerCount} companies</small></span><ArrowRight size={14} /></Link></Card>)}</div>}
    </div></section>
    <section className="stock-section stock-band"><div className="stock-container"><SectionTitle>Market News</SectionTitle>{news.loading ? <div className="market-loading" aria-label="Loading market news" aria-busy="true"><Skeleton className="sk" /></div> : news.error ? <EmptyState error onRetry={refresh}>Market news is temporarily unavailable.</EmptyState> : news.items.length ? <div className="market-sector-grid">{news.items.map((item, index) => <Card asChild><article className="market-card" key={item.id || index}><h3>{item.title}</h3><p className="stock-source-note">{item.source}</p></article></Card>)}</div> : <div className="market-news-empty"><Newspaper size={24} /><strong>No market stories available yet</strong><p>Latest stories will appear here when available from your news feed.</p></div>}</div></section>
    <footer className="stock-source-footer stock-container">Asset Hunter · Market data: Yahoo Finance / yfinance. Quotes may be delayed. Refresh to request the latest available data.</footer>
  </>
}
