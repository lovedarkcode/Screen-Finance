import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EmptyState, SectionTitle } from './StockUI'
import { money, number } from './stock-format'

const SERIES = [['totalIncome', 'Total Income', '#00b69b'], ['profitBeforeTax', 'Profit Before Tax', '#f5a623'], ['netProfitLoss', 'Net Profit/Loss', '#3b82f6']]

export default function StockFinancials({ quarters, loading, error }) {
  const [tab, setTab] = useState('Results')
  const data = quarters?.chart || []
  const eps = tab === 'Earnings Per Share'
  const series = eps ? [['eps', 'Earnings Per Share', '#b7b4e7']] : SERIES
  const available = data.some(row => series.some(([key]) => row[key] != null))
  return <article className="stock-panel" id="financials"><SectionTitle>Financial Result (Amount in ₹ Lakhs)</SectionTitle>
    <div className="stock-financial-tabs" role="group" aria-label="Financial chart"><button aria-pressed={!eps} onClick={() => setTab('Results')}>Results</button><button aria-pressed={eps} onClick={() => setTab('Earnings Per Share')}>Earnings Per Share</button></div>
    <div className="stock-chart-legend">{series.map(([, label, color]) => <span key={label}><i style={{ background: color }} />{label}</span>)}</div>
    <div className="stock-financial-chart">{loading ? <div className="sk sk-panel" /> : error ? <EmptyState error>Financial results are temporarily unavailable.</EmptyState> : !available ? <EmptyState>No financial data available</EmptyState> : <ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ top: 5, right: 4, left: -18, bottom: 5 }}>
      <CartesianGrid vertical={false} stroke="var(--stock-subtle)" />
      <XAxis dataKey="date" tick={{ fill: 'var(--stock-muted)', fontSize: 9 }} tickLine={false} axisLine={false} interval={0} tickFormatter={value => value.replace(/^(\d+) (\w+) (\d+)/, '$2 $3')} />
      <YAxis tick={{ fill: 'var(--stock-muted)', fontSize: 10 }} axisLine={false} tickLine={false} tickCount={5} tickFormatter={value => eps ? number(value, 1) : Math.abs(value) >= 1e5 ? `${number(value / 1e5, 0)}L` : Math.abs(value) >= 1000 ? `${number(value / 1000, 0)}K` : number(value, 0)} />
      <Tooltip contentStyle={{ background: 'var(--stock-bg)', border: '1px solid var(--stock-border)', borderRadius: 8, fontSize: 11 }} labelStyle={{ color: 'var(--stock-text)' }} cursor={{ fill: 'var(--stock-surface)' }} formatter={(value, name) => [eps ? money(value) : `₹${number(value)} L`, name]} />
      {series.map(([key, name, color]) => <Bar key={key} dataKey={key} name={name} fill={color} radius={[3, 3, 0, 0]} maxBarSize={24} isAnimationActive={false} />)}
    </BarChart></ResponsiveContainer>}</div>
  </article>
}
