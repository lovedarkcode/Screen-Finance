import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Landmark, Star, Trash2 } from 'lucide-react'
import { useToast } from '@/components/ui/toast'
import { Button } from '@/components/ui/button'
import { Card, CardBody } from '@/components/ui/card'
import { Chip } from '@/components/ui/chip'
import { IconButton } from '@/components/ui/icon-button'
import { Spinner } from '@/components/ui/spinner'
import { EmptyState, PriceChange } from '@/components/stock/StockUI'
import { money } from '@/components/stock/stock-format'
import watchlistService from '@/services/watchlist.service'
import stockService from '@/services/stock.service'

export default function Watchlist() {
  const toast = useToast()
  const [state, setState] = useState({ items: [], loading: true, error: false })
  const [attempt, setAttempt] = useState(0)
  const [pending, setPending] = useState([])
  useEffect(() => {
    let live = true
    watchlistService.getWatchlist().then(async data => {
      const items = await Promise.all((data.items || []).map(async symbol => {
        try { return { ...await stockService.getStock(symbol), symbol } }
        catch { return { symbol, name: symbol, price: null, changePercent: null } }
      }))
      if (live) setState({ items, loading: false, error: false })
    }).catch(() => { if (live) setState({ items: [], loading: false, error: true }) })
    return () => { live = false }
  }, [attempt])
  const refresh = () => { setState(value => ({ ...value, loading: true, error: false })); setAttempt(value => value + 1) }
  const remove = async symbol => {
    if (pending.includes(symbol)) return
    setPending(value => [...value, symbol])
    try {
      await watchlistService.removeFromWatchlist(symbol)
      setState(value => ({ ...value, items: value.items.filter(item => item.symbol !== symbol) }))
      toast(`${symbol} removed from watchlist successfully`, { tone: 'success' })
    } catch { toast('Failed to remove stock from watchlist', { tone: 'danger' }) }
    finally { setPending(value => value.filter(item => item !== symbol)) }
  }
  return <div className="stock-container py-8">
    <div className="market-heading-row mb-8"><div>
      <h1 className="flex items-center gap-2 text-2xl font-semibold"><Star className="size-6 text-brand" />Watchlist</h1>
      <p className="market-description">Track your saved stocks and open a company to view its financial analytics.</p>
    </div><Chip>Total Stocks: {state.items.length}</Chip></div>
    {state.loading ? <div className="flex min-h-[300px] items-center justify-center"><Spinner label="Loading your watchlist" /></div>
      : state.error ? <EmptyState error onRetry={refresh}>Could not load watchlist. Please try again.</EmptyState>
      : !state.items.length ? <Card className="mx-auto max-w-xl"><CardBody className="items-center py-12 text-center">
        <Star className="mb-3 size-8 text-brand" /><h2 className="text-lg font-semibold">Your watchlist is empty</h2>
        <p className="mb-5 text-sm text-muted-foreground">Save companies with the star button in Screens.</p>
        <Button asChild variant="solid"><Link to="/screens">Explore Screens</Link></Button>
      </CardBody></Card> : <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {state.items.map(stock => <Card key={stock.symbol} className="min-w-0 p-5">
          <div className="flex items-start gap-3"><Landmark className="mt-1 size-5 shrink-0 text-brand" /><div className="min-w-0 flex-1">
            <h2 className="truncate text-sm font-semibold"><Link to={`/stock/${encodeURIComponent(stock.symbol)}`} className="after:absolute after:inset-0 focus-visible:after:outline-2 focus-visible:after:outline-ring">{stock.name}</Link></h2>
            <p className="mt-1 text-xs text-muted-foreground">{stock.symbol}{stock.exchange && ` · ${stock.exchange}`}</p>
          </div><IconButton variant="ghost" className="relative z-10 size-8 text-muted-foreground hover:text-destructive" aria-label={`Remove ${stock.symbol} from watchlist`} disabled={pending.includes(stock.symbol)} onClick={() => remove(stock.symbol)}><Trash2 /></IconButton></div>
          <div className="mt-6 flex flex-wrap items-baseline justify-between gap-2"><strong className="text-lg">{stock.price == null ? 'Live data unavailable' : money(stock.price)}</strong><PriceChange value={stock.changePercent} badge /></div>
          <ArrowUpRight className="mt-4 size-4 self-end text-muted-foreground" aria-hidden="true" />
        </Card>)}
      </div>}
  </div>
}
