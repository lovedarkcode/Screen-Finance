import { Card } from '@/components/ui/card'
import { Segmented } from '@/components/ui/segmented'
import { Skeleton } from '@/components/ui/skeleton'
import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EmptyState, SectionTitle } from './StockUI'
import { compact, money, number } from './stock-format'

const SERIES = [['totalIncome', 'Total Income', '#00b69b'], ['profitBeforeTax', 'Profit Before Tax', '#f5a623'], ['netProfitLoss', 'Net Profit/Loss', '#3b82f6']]

export default function StockFinancials({ quarters, currency = 'INR', loading, error }) {
  const [tab, setTab] = useState('Results')
  const data = quarters?.chart || []
  const eps = tab === 'Earnings Per Share'
  const reportCurrency = quarters?.currency || currency
  const chartUnit = quarters?.chartUnit || (reportCurrency === 'INR' ? 'Lakhs' : 'Millions')
  const series = eps ? [['eps', 'Earnings Per Share', 'var(--stock-accent)']] : SERIES.map(([key, label, color]) => [key, key === 'totalIncome' ? quarters?.incomeLabel || label : label, color])
  const available = data.some(row => series.some(([key]) => row[key] != null))
  return <Card asChild><article className="stock-panel" id="financials"><SectionTitle>Financial Result ({eps ? 'EPS in' : 'Amount in'} {reportCurrency === 'INR' ? '₹' : reportCurrency}{!eps && ` ${chartUnit}`})</SectionTitle>
    <Segmented className="stock-financial-tabs" label="Financial chart" options={['Results', 'Earnings Per Share'].map(value => ({ value, label: value }))} value={tab} onChange={setTab} />
    <div className="stock-chart-legend">{series.map(([, label, color]) => <span key={label}><i style={{ background: color }} />{label}</span>)}</div>
    <div className="stock-financial-chart">{loading ? <Skeleton className="sk sk-panel" /> : error ? <EmptyState error>Financial results are temporarily unavailable.</EmptyState> : !available ? <EmptyState>No financial data available</EmptyState> : <ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ top: 5, right: 4, left: -18, bottom: 5 }}>
      <CartesianGrid vertical={false} stroke="var(--stock-subtle)" />
      <XAxis dataKey="date" tick={{ fill: 'var(--stock-muted)', fontSize: 9 }} tickLine={false} axisLine={false} interval={0} tickFormatter={value => value.replace(/^(\d+) (\w+) (\d+)/, '$2 $3')} />
      <YAxis tick={{ fill: 'var(--stock-muted)', fontSize: 10 }} axisLine={false} tickLine={false} tickCount={5} tickFormatter={value => eps ? number(value, 1) : compact(value, reportCurrency)} />
      <Tooltip contentStyle={{ background: 'var(--stock-bg)', border: '1px solid var(--stock-border)', borderRadius: 8, fontSize: 11 }} labelStyle={{ color: 'var(--stock-text)' }} cursor={{ fill: 'var(--stock-surface)' }} formatter={(value, name) => [eps ? money(value, reportCurrency) : `${money(value, reportCurrency)} ${chartUnit}`, name]} />
      {series.map(([key, name, color]) => <Bar key={key} dataKey={key} name={name} fill={color} radius={[3, 3, 0, 0]} maxBarSize={24} isAnimationActive={false} />)}
    </BarChart></ResponsiveContainer>}</div>
  </article></Card>
}
