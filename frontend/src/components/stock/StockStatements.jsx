import { useEffect, useState } from 'react'
import stockService from '@/services/stock.service'
import { EmptyState } from './StockUI'

const TABLES = [['quarters', 'Quarterly Results', 'getQuarters'], ['profitLoss', 'Profit & Loss', 'getProfitLoss'], ['balanceSheet', 'Balance Sheet', 'getBalanceSheet'], ['cashFlow', 'Cash Flow', 'getCashFlow'], ['ratios', 'Ratios', 'getRatios']]

export default function StockStatements({ symbol, quarters }) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState('quarters')
  const [tables, setTables] = useState({})
  useEffect(() => {
    if (!open) return
    let live = true
    for (const [id, , method] of TABLES.filter(([id]) => id !== 'quarters')) {
      stockService[method](symbol).then(value => { if (live) setTables(previous => ({ ...previous, [id]: value })) })
        .catch(() => { if (live) setTables(previous => ({ ...previous, [id]: { error: true } })) })
    }
    return () => { live = false }
  }, [open, symbol])
  const table = active === 'quarters' ? quarters : tables[active]
  return <details className="stock-statements" onToggle={event => setOpen(event.currentTarget.open)}><summary>Financial statements</summary>
    {open && <><div className="stock-report-tabs" role="group" aria-label="Financial statement">{TABLES.map(([id, label]) => <button key={id} aria-pressed={active === id} onClick={() => setActive(id)}>{label}</button>)}</div>
      {!table ? <div className="sk sk-card" /> : table.error ? <EmptyState error>Statement data is temporarily unavailable.</EmptyState> : !table.rows?.length ? <EmptyState>No statement data available</EmptyState> : <div className="stock-statement-scroll"><p className="stock-source-note">{table.unit}</p><table className="stock-statement-table"><thead><tr><th>Metric</th>{table.columns.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{table.rows.map(row => <tr key={row.label}><th>{row.label}</th>{row.values.map((value, index) => <td key={index}>{String(value).replace('INR ', '₹').replace('N/A', '—')}</td>)}</tr>)}</tbody></table></div>}
    </>}
  </details>
}
