import { Dialog } from '@base-ui/react/dialog'
import { TrendingDown, TrendingUp, X } from 'lucide-react'
import { percent } from './stock-format'

export function SectionTitle({ children, extra }) {
  return <div className="stock-section-heading"><h2>{children}</h2>{extra}</div>
}

export function EmptyState({ children, error, onRetry }) {
  return <div className="stock-empty" role={error ? 'alert' : 'status'}><p>{children}</p>{onRetry && <button className="stock-button" onClick={onRetry}>Try again</button>}</div>
}

export function PriceChange({ value, absolute, badge = false }) {
  const Icon = value < 0 ? TrendingDown : TrendingUp
  return <span className={`stock-change ${value == null ? '' : value < 0 ? 'is-loss' : 'is-gain'} ${badge ? 'stock-badge' : ''}`}>
    {value != null && <Icon size={14} />}{absolute != null && `${absolute > 0 ? '+' : ''}${absolute.toFixed(2)} `}{absolute != null ? `(${percent(value)})` : percent(value)}
  </span>
}

export function StockModal({ open, onOpenChange, theme, title, description, drawer, children }) {
  return <Dialog.Root open={open} onOpenChange={onOpenChange}>
    <Dialog.Portal><Dialog.Backdrop className="stock-backdrop" />
      <Dialog.Popup className={`stock-detail stock-modal ${drawer ? 'stock-drawer' : ''}`} data-stock-theme={theme}>
        <div className="stock-modal-heading"><div><Dialog.Title>{title}</Dialog.Title>{description && <Dialog.Description>{description}</Dialog.Description>}</div>
          <Dialog.Close className="stock-icon-button" aria-label="Close"><X size={18} /></Dialog.Close>
        </div>{children}
      </Dialog.Popup>
    </Dialog.Portal>
  </Dialog.Root>
}

export function StockSkeleton() {
  return <div aria-busy="true" aria-label="Loading stock details" className="stock-skeleton">
    <div className="stock-container"><div className="sk sk-title" /><div className="sk sk-label" /><div className="sk sk-price" /><div className="sk sk-label" /></div>
    <div className="stock-band"><div className="stock-container"><div className="sk sk-title" /><div className="sk sk-chart" /></div></div>
    <div className="stock-container stock-metric-grid">{Array.from({ length: 10 }, (_, i) => <div className="sk sk-card" key={i} />)}</div>
  </div>
}
