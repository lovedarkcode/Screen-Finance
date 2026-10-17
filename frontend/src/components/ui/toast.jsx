// Adapted from https://ui.chaicode.com/r/toast.json (ChaiUI).
import { X } from 'lucide-react'
import * as React from 'react'
import { cn } from '@/lib/utils'

const ToastContext = React.createContext(null)
const toneClass = {
  default: '',
  success: '[&_[data-toast-dot]]:bg-green-500',
  danger: '[&_[data-toast-dot]]:bg-red-500',
}

function ToastProvider({ children }) {
  const [items, setItems] = React.useState([])
  const next = React.useRef(0)
  const timers = React.useRef(new Set())
  const dismiss = React.useCallback(id => setItems(all => all.filter(item => item.id !== id)), [])
  React.useEffect(() => {
    const activeTimers = timers.current
    return () => { activeTimers.forEach(window.clearTimeout); activeTimers.clear() }
  }, [])
  const toast = React.useCallback((message, opts) => {
    const id = ++next.current
    setItems(all => [...all.slice(-2), { id, message, tone: opts?.tone ?? 'default' }])
    const timer = window.setTimeout(() => { timers.current.delete(timer); dismiss(id) }, opts?.duration ?? 4000)
    timers.current.add(timer)
  }, [dismiss])
  return <ToastContext value={toast}>
    {children}
    <div aria-live="polite" role="status" className="pointer-events-none fixed inset-x-0 bottom-4 z-[110] flex flex-col items-center gap-2 px-4">
      {items.map(item => <div key={item.id} data-slot="toast" className={cn('pointer-events-auto flex w-fit max-w-md items-center gap-3 rounded-xl border border-card-edge-hover bg-card/90 py-2.5 pr-2 pl-4 text-sm text-card-foreground backdrop-blur-md motion-safe:animate-chai-pop', toneClass[item.tone])}>
        {item.tone !== 'default' && <span data-toast-dot="" className="size-1.5 shrink-0 rounded-full" aria-hidden="true" />}
        <span className="min-w-0">{item.message}</span>
        <button type="button" onClick={() => dismiss(item.id)} aria-label="Dismiss" className="grid size-7 shrink-0 cursor-pointer place-items-center rounded-md text-muted-foreground transition-colors outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/50"><X className="size-3.5" aria-hidden="true" /></button>
      </div>)}
    </div>
  </ToastContext>
}

function useToast() {
  const toast = React.use(ToastContext)
  if (!toast) throw new Error('useToast must be used inside <ToastProvider>')
  return toast
}

export { ToastProvider, useToast }
