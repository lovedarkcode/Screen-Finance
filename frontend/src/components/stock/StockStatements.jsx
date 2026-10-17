import { Segmented } from '@/components/ui/segmented'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table'
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
    {open && <><Segmented className="stock-report-tabs" label="Financial statement" value={active} onChange={setActive} options={TABLES.map(([value, label]) => ({ value, label }))} />
      {!table ? <Skeleton className="sk sk-card" /> : table.error ? <EmptyState error>Statement data is temporarily unavailable.</EmptyState> : !table.rows?.length ? <EmptyState>No statement data available</EmptyState> : <div className="stock-statement-scroll"><p className="stock-source-note">{table.unit}</p><Table className="stock-statement-table"><TableHeader><TableRow><TableHead>Metric</TableHead>{table.columns.map(column => <TableHead key={column}>{column}</TableHead>)}</TableRow></TableHeader><TableBody>{table.rows.map(row => <TableRow key={row.label}><TableHead scope="row">{row.label}</TableHead>{row.values.map((value, index) => <TableCell key={index}>{String(value).replace('INR ', '₹').replace('USD ', '$').replace('N/A', '—')}</TableCell>)}</TableRow>)}</TableBody></Table></div>}
    </>}
  </details>
}
