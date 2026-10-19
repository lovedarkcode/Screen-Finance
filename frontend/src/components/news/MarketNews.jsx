import { useEffect, useState } from 'react'
import { ExternalLink, Newspaper, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState, SectionTitle } from '@/components/stock/StockUI'
import api from '@/services/api'

function publishedDate(value) {
  const date = new Date(value)
  if (!value || !Number.isFinite(date.getTime())) return null
  return date.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function MarketNews() {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState({ items: [], loading: true, error: false })
  useEffect(() => {
    const controller = new AbortController()
    api.get('/news', { params: { limit: 6 }, signal: controller.signal }).then(({ data }) => {
      if (!controller.signal.aborted) setState({ ...data, loading: false, error: false })
    }).catch(() => {
      if (!controller.signal.aborted) setState(value => ({ ...value, loading: false, error: true }))
    })
    const timer = setInterval(() => {
      if (document.visibilityState === 'visible') setAttempt(value => value + 1)
    }, 300000)
    return () => { controller.abort(); clearInterval(timer) }
  }, [attempt])
  const refresh = () => { setState(value => ({ ...value, loading: true, error: false })); setAttempt(value => value + 1) }
  return <section className="stock-section stock-band" aria-label="Market news"><div className="stock-container">
    <SectionTitle extra={<Button variant="ghost" size="sm" onClick={refresh} disabled={state.loading}><RefreshCw size={14} />Refresh news</Button>}>Market News</SectionTitle>
    {state.loading && !state.items.length ? <div className="market-loading" aria-label="Loading market news" aria-busy="true"><Skeleton className="sk" /></div> : state.error && !state.items.length ? <EmptyState error onRetry={refresh}>Market news is temporarily unavailable.</EmptyState> : state.items.length ? <>
      {(state.stale || state.error) && <p className="stock-source-note" role="status">Showing previously fetched headlines. Live news is temporarily unavailable.</p>}
      {state.partial && <p className="stock-source-note">Some market feeds are temporarily unavailable.</p>}
      <div className="market-sector-grid" aria-busy={state.loading}>{state.items.map(item => <Card key={item.id || item.url} asChild><a className="market-card market-news-card" href={item.url} target="_blank" rel="noopener noreferrer"><div className="market-news-meta">{publishedDate(item.published_at) && <time dateTime={item.published_at}>{publishedDate(item.published_at)}</time>}</div><h3>{item.title}</h3><span className="market-link">Read article<ExternalLink size={13} /><span className="sr-only"> (opens in a new tab)</span></span></a></Card>)}</div>
      <p className="stock-source-note" style={{ marginTop: 14 }}>Updates every five minutes.{state.updated_at && <> Last updated: {publishedDate(state.updated_at)}.</>}</p>
    </> : <div className="market-news-empty"><Newspaper size={24} /><strong>No market headlines available right now</strong><p>Try refreshing the news feed shortly.</p></div>}
  </div></section>
}
