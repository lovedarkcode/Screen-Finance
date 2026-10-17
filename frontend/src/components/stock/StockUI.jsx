import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog } from '@/components/ui/dialog'
import { IconButton } from '@/components/ui/icon-button'
import { Chip } from '@/components/ui/chip'
import { TrendingDown, TrendingUp, X } from 'lucide-react'
import { percent } from './stock-format'

export function SectionTitle({ children, extra }) {
  return <div className="stock-section-heading"><h2>{children}</h2>{extra}</div>
}

export function EmptyState({ children, error, onRetry }) {
  return <div className="stock-empty" role={error ? 'alert' : 'status'}><p>{children}</p>{onRetry && <Button variant="outline" size="sm" className="stock-button" onClick={onRetry}>Try again</Button>}</div>
}

export function PriceChange({ value, absolute, badge = false }) {
  const Icon = value < 0 ? TrendingDown : TrendingUp
  const Tag = badge ? Chip : 'span'
  return <Tag {...(badge ? { tone: value == null ? 'default' : value < 0 ? 'danger' : 'success' } : {})} className={`stock-change ${value == null ? '' : value < 0 ? 'is-loss' : 'is-gain'} ${badge ? 'stock-badge' : ''}`}>
    {value != null && <Icon size={14} />}{absolute != null && `${absolute > 0 ? '+' : ''}${absolute.toFixed(2)} `}{absolute != null ? `(${percent(value)})` : percent(value)}
  </Tag>
}

export function StockModal({ open, onOpenChange, theme, title, description, initialFocus, children }) {
  return <Dialog open={open} onClose={() => onOpenChange(false)} title={title} description={description} initialFocus={initialFocus} className="stock-detail stock-chai-dialog" data-stock-theme={theme}>
    <IconButton variant="ghost" className="absolute right-4 top-4" aria-label="Close" onClick={() => onOpenChange(false)}><X size={18} /></IconButton>
    <div className="mt-5">{children}</div>
  </Dialog>
}

export function StockSkeleton() {
  return <div aria-busy="true" aria-label="Loading stock details" className="stock-skeleton">
    <div className="stock-container"><Skeleton className="sk sk-title" /><Skeleton className="sk sk-label" /><Skeleton className="sk sk-price" /><Skeleton className="sk sk-label" /></div>
    <div className="stock-band"><div className="stock-container"><Skeleton className="sk sk-title" /><Skeleton className="sk sk-chart" /></div></div>
    <div className="stock-container stock-metric-grid">{Array.from({ length: 10 }, (_, i) => <Skeleton className="sk sk-card" key={i} />)}</div>
  </div>
}
