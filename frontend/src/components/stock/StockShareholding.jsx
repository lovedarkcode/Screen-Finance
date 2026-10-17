import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Segmented } from '@/components/ui/segmented'
import { useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { EmptyState, SectionTitle } from './StockUI'
import { number } from './stock-format'

const COLORS = ['#00b69b', '#e65c1b', '#3b82f6', '#f5a623']

export default function StockShareholding({ data = [], loading, error }) {
  const [selected, setSelected] = useState(0)
  const report = data[selected] || data[0]
  return <Card asChild><article className="stock-panel" id="shareholding"><SectionTitle>Shareholding Pattern (in %)</SectionTitle>
    {loading ? <Skeleton className="sk sk-panel" /> : error ? <EmptyState error>Ownership data is temporarily unavailable.</EmptyState> : !report?.holdings?.length ? <EmptyState>No shareholding data available</EmptyState> : <>
      <Segmented className="stock-report-tabs" label="Ownership reporting date" options={data.map((item, index) => ({ value: String(index), label: item.label }))} value={String(selected)} onChange={value => setSelected(Number(value))} />
      <div className="stock-chart-legend">{report.holdings.map((item, index) => <span key={item.name}><i style={{ background: COLORS[index % COLORS.length] }} />{item.name}</span>)}</div>
      <div className="stock-donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={report.holdings} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} startAngle={0} endAngle={360} stroke="var(--stock-card)" strokeWidth={2} isAnimationActive={false}>{report.holdings.map((item, index) => <Cell key={item.name} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip formatter={value => `${number(value)}%`} contentStyle={{ background: 'var(--stock-bg)', color: 'var(--stock-text)', border: '1px solid var(--stock-border)', borderRadius: 8, fontSize: 11 }} itemStyle={{ color: 'var(--stock-text)' }} /></PieChart></ResponsiveContainer></div>
      <div className="stock-holding-values">{report.holdings.map(item => <div key={item.name}><span>{item.name}</span><strong>{number(item.value)}%</strong></div>)}</div>
      {!report.periodEnd && <p className="stock-source-note">Current provider snapshot · reporting date unavailable</p>}
    </>}
  </article></Card>
}
