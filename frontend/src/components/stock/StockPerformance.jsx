import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState, PriceChange, SectionTitle } from './StockUI'
import { compact, marketTime, money } from './stock-format'

export function PriceRange({ stock, data, loading, error }) {
  const price = value => money(value, stock.currency)
  const range = (label, low, high) => {
    const position = low != null && high != null && high > low && stock.price != null ? Math.max(0, Math.min(100, (stock.price - low) / (high - low) * 100)) : null
    return <Card className="stock-range-card"><p>{label}</p><div><strong className="is-loss">{price(low)}</strong><span className="stock-range-track">{position != null && <span style={{ left: `${position}%` }} />}</span><strong className="is-gain">{price(high)}</strong></div></Card>
  }
  return <section className="stock-section stock-band" id="price-range"><div className="stock-container"><SectionTitle>Price Range <small>As on {marketTime(stock.date, stock.timeZone)}</small></SectionTitle>
    {loading ? <Skeleton className="sk sk-card" /> : error ? <EmptyState error>Price range data is temporarily unavailable.</EmptyState> : <>
      <div className="stock-range-grid">{range('Today’s Range', data?.dayLow, data?.dayHigh)}{range('52 Week Range', data?.week52Low, data?.week52High)}</div>
      <div className="stock-session-grid">{[['Open', price(data?.open)], ['Prev Close', price(data?.previousClose)], ['Volume', compact(data?.volume, stock.currency)], ['VWAP', price(data?.vwap)]].map(([label, value]) => <Card key={label} className="stock-range-card" title={label === 'VWAP' && data?.vwap == null ? 'Trade-weighted intraday data is not available from the configured provider.' : undefined}><p>{label}</p><strong>{value}</strong></Card>)}</div>
    </>}
  </div></section>
}

export function ReturnsPerformance({ data = [], loading, error }) {
  return <section className="stock-section" id="returns"><div className="stock-container"><SectionTitle>Returns Performance</SectionTitle>
    {loading ? <Skeleton className="sk sk-card" /> : error ? <EmptyState error>Return history is temporarily unavailable.</EmptyState> : <div className="stock-returns-grid">{data.map(item => <Card className="stock-return-card" key={item.label}><span>{item.label}</span><PriceChange value={item.value} /></Card>)}</div>}
  </div></section>
}
