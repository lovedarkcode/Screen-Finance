import { useEffect, useState } from 'react'
import { Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogActions } from '@/components/ui/dialog'
import stockService from '@/services/stock.service'
import { money } from './stock-format'

export default function ChartAlerts({ symbol, currency }) {
  const key = `chart-alert:${symbol}`
  const [rule, setRule] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(key))
      return saved && Number.isFinite(saved.target) && saved.target > 0 && ['above', 'below'].includes(saved.direction) ? saved : null
    } catch { return null }
  })
  const [open, setOpen] = useState(false)
  const [target, setTarget] = useState('')
  const [direction, setDirection] = useState('above')
  const [status, setStatus] = useState('')
  useEffect(() => {
    if (!rule || rule.triggered) return
    let live = true
    let timer
    const check = async () => {
      try {
        const quote = await stockService.getStock(symbol)
        if (!live) return
        if (!Number.isFinite(quote.price)) throw new Error('Missing price')
        if (rule.direction === 'above' ? quote.price >= rule.target : quote.price <= rule.target) {
          const triggered = { ...rule, triggered: true }
          setRule(triggered)
          setStatus(`Alert reached: ${symbol} is ${money(quote.price, currency)}. Quote time: ${quote.date || 'unavailable'}.`)
          try { localStorage.setItem(key, JSON.stringify(triggered)) } catch { /* Current tab still shows the alert. */ }
          return
        }
        setStatus(`Monitoring ${symbol}; last checked ${new Date().toLocaleTimeString()}. Quotes may be delayed.`)
      } catch { if (live) setStatus('Could not check the alert. Retrying in one minute.') }
      if (live) timer = setTimeout(check, 60000)
    }
    check()
    return () => { live = false; clearTimeout(timer) }
  }, [rule, symbol, currency, key])
  const save = event => {
    event.preventDefault()
    const value = Number(target)
    if (!Number.isFinite(value) || value <= 0) return
    const next = { target: value, direction, triggered: false }
    try { localStorage.setItem(key, JSON.stringify(next)) }
    catch { setStatus('Browser storage is unavailable. The alert could not be saved.'); return }
    setRule(next)
    setStatus('Alert saved. Checking the latest quote…')
    setOpen(false)
  }
  const remove = () => {
    try { localStorage.removeItem(key) }
    catch { setStatus('Browser storage is unavailable. The alert could not be removed.'); return }
    setRule(null); setStatus('Alert removed.')
  }
  return <>
    <Button variant="outline" size="sm" onClick={() => { setTarget(rule?.target?.toString() || ''); setDirection(rule?.direction || 'above'); setOpen(true) }}><Bell size={14} />Alerts{rule ? ' (1)' : ''}</Button>
    {status && <span className="stock-source-note chart-alert-status" role="status">{status}</span>}
    <Dialog open={open} onClose={() => setOpen(false)} title={`Price alert · ${symbol}`} description="Saved in this browser. Checks once a minute while this chart is open. Quotes may be delayed; no email or background notifications.">
      {rule && <p className="mt-3 text-sm">{rule.triggered ? 'Triggered' : 'Active'}: {rule.direction} {money(rule.target, currency)}</p>}
      <form onSubmit={save} className="chart-alert-form">
        <label>Notify when price is<select value={direction} onChange={e => setDirection(e.target.value)}><option value="above">At or above</option><option value="below">At or below</option></select></label>
        <label>Target price ({currency})<input type="number" min="0.000001" step="any" required value={target} onChange={e => setTarget(e.target.value)} /></label>
        <DialogActions><Button type="button" variant="ghost" onClick={() => setOpen(false)}>Close</Button>{rule && <Button type="button" variant="outline" onClick={remove}>Remove alert</Button>}<Button type="submit">Save alert</Button></DialogActions>
      </form>
    </Dialog>
  </>
}
