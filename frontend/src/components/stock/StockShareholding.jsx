import { useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { EmptyState, SectionTitle } from './StockUI'
import { number } from './stock-format'

const COLORS = ['#00b69b', '#e65c1b', '#3b82f6', '#f5a623']

export default function StockShareholding({ data = [], loading, error }) {
  const [selected, setSelected] = useState(0)
  const report = data[selected] || data[0]
  return <article className="stock-panel" id="shareholding"><SectionTitle>Shareholding Pattern (in %)</SectionTitle>
    {loading ? <div className="sk sk-panel" /> : error ? <EmptyState error>Ownership data is temporarily unavailable.</EmptyState> : !report?.holdings?.length ? <EmptyState>No shareholding data available</EmptyState> : <>
      <div className="stock-report-tabs" aria-label="Ownership reporting date">{data.map((item, index) => <button key={item.periodEnd || item.label} aria-pressed={index === selected} onClick={() => setSelected(index)}>{item.label}</button>)}</div>
      <div className="stock-chart-legend">{report.holdings.map((item, index) => <span key={item.name}><i style={{ background: COLORS[index % COLORS.length] }} />{item.name}</span>)}</div>
      <div className="stock-donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={report.holdings} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} startAngle={0} endAngle={360} stroke="var(--stock-card)" strokeWidth={2} isAnimationActive={false}>{report.holdings.map((item, index) => <Cell key={item.name} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip formatter={value => `${number(value)}%`} contentStyle={{ background: 'var(--stock-bg)', color: 'var(--stock-text)', border: '1px solid var(--stock-border)', borderRadius: 8, fontSize: 11 }} itemStyle={{ color: 'var(--stock-text)' }} /></PieChart></ResponsiveContainer></div>
      <div className="stock-holding-values">{report.holdings.map(item => <div key={item.name}><span>{item.name}</span><strong>{number(item.value)}%</strong></div>)}</div>
      {!report.periodEnd && <p className="stock-source-note">Current provider snapshot · reporting date unavailable</p>}
    </>}
  </article>
}
