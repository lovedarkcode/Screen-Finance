import { useEffect, useState } from 'react'
import { Check, Pencil, Search, X } from 'lucide-react'
import { EmptyState, SectionTitle } from './StockUI'
import { money, number, readPreference } from './stock-format'

const DEFAULT = ['marketCap', 'peRatio', 'eps', 'faceValue', 'allTimeHigh', 'allTimeLow', 'debtToEquity']
const display = ({ value, unit }) => value == null ? '—' : unit === 'crore' ? `${money(value / 1e7)} Cr` : unit === 'inr' ? money(value) : `${number(value)}${unit === 'percent' ? '%' : ''}`

export default function StockMetrics({ metrics = [], loading, error }) {
  const [selected, setSelected] = useState(() => {
    const saved = readPreference('asset-hunter-stock-metrics', DEFAULT)
    return Array.isArray(saved) ? saved : DEFAULT
  })
  const [editing, setEditing] = useState(false)
  const [query, setQuery] = useState('')
  useEffect(() => { localStorage.setItem('asset-hunter-stock-metrics', JSON.stringify(selected)) }, [selected])
  const toggle = id => setSelected(value => value.includes(id) ? value.filter(item => item !== id) : [...value, id])
  const matches = metrics.filter(metric => metric.label.toLowerCase().includes(query.toLowerCase()))
  const visible = selected.map(id => metrics.find(metric => metric.id === id)).filter(Boolean)
  return <section className="stock-section stock-band-alt" id="key-metrics"><div className="stock-container">
    <SectionTitle extra={<div className="stock-metric-toolbar"><label className="stock-metric-search"><Search size={14} /><input aria-label="Search metrics" placeholder="Search metrics…" value={query} onChange={e => setQuery(e.target.value)} /></label>
      <button className={`stock-button stock-edit ${editing ? 'is-editing' : ''}`} onClick={() => { setEditing(!editing); setQuery('') }}>{editing ? <Check size={14} /> : <Pencil size={14} />}{editing ? 'Done' : 'Edit Metrics'}</button>
      {(query || editing) && <div className="stock-metric-options" aria-label="Available metrics">{matches.length ? matches.map(metric => <button key={metric.id} aria-pressed={selected.includes(metric.id)} onClick={() => toggle(metric.id)}><span>{metric.label}</span>{selected.includes(metric.id) && <Check size={14} />}</button>) : <p>No matching metrics found</p>}{editing && <button onClick={() => setSelected(DEFAULT)}>Reset to default metrics</button>}</div>}
    </div>}>Key Metrics</SectionTitle>
    {loading ? <div className="stock-metric-grid">{DEFAULT.map(id => <div key={id} className="sk sk-card" />)}</div> : error ? <EmptyState error>Company metrics are temporarily unavailable.</EmptyState> : visible.length ? <div className="stock-metric-grid">{visible.map(metric => <div className="stock-metric-card" key={metric.id}><div>{metric.label}</div><strong>{display(metric)}</strong>{editing && <button aria-label={`Remove ${metric.label}`} onClick={() => toggle(metric.id)}><X size={13} /></button>}</div>)}</div> : <EmptyState>Choose metrics using Edit Metrics.</EmptyState>}
  </div></section>
}
