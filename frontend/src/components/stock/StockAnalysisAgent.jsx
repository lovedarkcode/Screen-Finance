import { useEffect, useRef, useState } from 'react'
import { BookOpen, Check, RefreshCw, Sparkles, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Chip } from '@/components/ui/chip'
import { Dialog } from '@/components/ui/dialog'
import { IconButton } from '@/components/ui/icon-button'
import { Spinner } from '@/components/ui/spinner'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import aiService from '@/services/ai.service'
import { largeMoney, money, number } from './stock-format'
import './stock-analysis.css'

function evidenceValue(item) {
  if (item.unit === 'text') return item.value
  if (item.unit === 'currency') return Math.abs(item.value) >= 1e6 ? largeMoney(item.value, item.currency) : money(item.value, item.currency)
  return `${number(item.value)}${item.unit === 'percent' ? '%' : item.unit === 'times' ? '×' : ''}`
}

const metricOrigin = item => item.kind === 'normalized' ? 'Provider · unit conversion' : item.kind === 'calculated' ? 'Recalculated' : 'Provider metric'

function TrendTable({ title, rows, evidence, onEvidence }) {
  return <section className="analysis-trends"><h3>{title} ({rows.length} periods)</h3>{rows.length ? <Table aria-label={title}>
    <TableHeader><TableRow><TableHead>Period ending</TableHead><TableHead>Revenue</TableHead><TableHead>Net income</TableHead><TableHead>Net margin</TableHead></TableRow></TableHeader>
    <TableBody>{[...rows].sort((a, b) => a.periodEnd.localeCompare(b.periodEnd)).map(row => <TableRow key={row.periodEnd}><TableCell>{row.periodEnd}</TableCell>{['revenueId', 'netIncomeId', 'netMarginId'].map(key => <TableCell key={key}>{evidence[row[key]] ? <Button variant="ghost" size="sm" onClick={() => onEvidence(row[key])} aria-label={`${evidence[row[key]].label}, ${row.periodEnd}, view evidence`}>{evidenceValue(evidence[row[key]])}</Button> : '—'}</TableCell>)}</TableRow>)}</TableBody>
  </Table> : <p className="analysis-muted">Comparable financial history was not available.</p>}</section>
}

function Findings({ title, items, onEvidence, tone }) {
  return <section className="analysis-findings"><h3>{title}</h3>{items.length ? <ul>{items.map((item, index) => <li key={index}>
    <span className={`analysis-finding-dot ${tone || ''}`} aria-hidden="true" /><div>{tone && item.significance && <span className="analysis-significance">{item.significance} significance</span>}<p>{item.text}</p>
      <div className="analysis-citations" aria-label="Supporting evidence">{item.evidenceIds.map(id => <Button key={id} variant="ghost" size="sm" onClick={() => onEvidence(id)} aria-label={`View evidence ${id}`}>[{id}]</Button>)}</div>
    </div>
  </li>)}</ul> : <p className="analysis-muted">No evidence-backed findings in this category.</p>}</section>
}

export default function StockAnalysisAgent({ stock, theme }) {
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState('idle')
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('research')
  const [highlight, setHighlight] = useState('')
  const request = useRef(null)
  useEffect(() => () => request.current?.abort(), [])
  useEffect(() => {
    if (tab !== 'evidence' || !highlight || !open) return
    const frame = requestAnimationFrame(() => {
      const target = document.getElementById(`analysis-evidence-${highlight}`)
      target?.scrollIntoView({ block: 'nearest', behavior: 'instant' })
      target?.focus({ preventScroll: true })
    })
    return () => cancelAnimationFrame(frame)
  }, [tab, highlight, open])
  const analyze = async () => {
    setOpen(true)
    if (!stock || status === 'loading' || report) return
    const controller = new AbortController()
    request.current = controller
    setStatus('loading')
    setError('')
    try {
      const data = await aiService.analyzeStock(stock.symbol, controller.signal)
      if (controller.signal.aborted) return
      if (data.symbol !== stock.symbol || data.exchange !== stock.exchange || data.companyId !== `${stock.exchange}:${stock.symbol}` || !data.analysisRunId) {
        setError('Received research for a different or unverified listing. Please try again.')
        setStatus('error')
        return
      }
      setReport(data)
      setStatus('ready')
    } catch (failure) {
      if (controller.signal.aborted) return
      const detail = failure.response?.data?.detail
      setError(typeof detail === 'string' ? detail : failure.code === 'ECONNABORTED' ? 'Analysis took too long. Please try again.' : 'AI analysis is temporarily unavailable. Please try again.')
      setStatus('error')
    }
  }
  const showEvidence = id => { setHighlight(id); setTab('evidence') }
  const evidence = Object.fromEntries((report?.evidence || []).map(item => [item.id, item]))
  return <>
    <Button className="stock-ai-launcher" variant="solid" size="lg" iconRight={null} disabled={!stock} aria-busy={status === 'loading'} onClick={analyze}>
      {status === 'loading' ? <Spinner label="Preparing research" /> : <Sparkles size={18} />}Analyze with AI
    </Button>
    <Dialog open={open} onClose={() => setOpen(false)} title="AI Stock Analysis" description={stock ? `${stock.name} · ${stock.symbol} · ${stock.exchange}` : 'Company research'} className="stock-detail stock-analysis-dialog" data-stock-theme={theme}>
      <IconButton className="analysis-close" variant="ghost" aria-label="Close AI analysis" onClick={() => setOpen(false)}><X /></IconButton>
      {status === 'loading' && <div className="analysis-loading" role="status"><Spinner label="Analyzing stock" /><h3>Preparing your research</h3><p>Retrieving financial statements, calculating metrics, and generating an evidence-backed summary.</p><span className="analysis-muted">You can close this panel while the analysis runs.</span></div>}
      {status === 'error' && <div className="analysis-error" role="alert"><h3>Research is unavailable</h3><p>{error}</p><Button variant="outline" onClick={analyze}><RefreshCw size={15} />Try again</Button></div>}
      {report && <div className="analysis-report">
        <div className="analysis-report-meta"><Chip><Sparkles size={12} />AI provider: {report.provider}</Chip><span>{report.cached ? 'Saved research' : 'Generated'} · {new Date(report.generatedAt).toLocaleString()}</span></div>
        <p className="analysis-intro">AI interpretation of retrieved financial evidence. Select a citation to inspect its figures, period, and calculation.</p>
        {report.quality && <div className="analysis-quality" aria-label="Evidence quality"><Chip>Evidence: {report.quality.coverage}</Chip><span>{report.quality.checkedCalculations} calculation checks · {report.quality.annualPeriods} annual periods · {report.quality.quarterlyPeriods} quarterly periods</span><small>Single-provider evidence · data coverage, not investment confidence</small></div>}
        <div className="analysis-metrics">{report.metricIds.slice(0, 8).map(id => evidence[id]).filter(Boolean).map(item => <Card key={item.id} className="analysis-metric"><Button variant="ghost" type="button" onClick={() => showEvidence(item.id)}><span>{item.label}</span><strong>{evidenceValue(item)}</strong><small>{metricOrigin(item)} · [{item.id}]</small><small>{item.period}</small></Button></Card>)}</div>
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList><TabsTrigger value="research"><Sparkles size={14} />Research</TabsTrigger><TabsTrigger value="trends">Financial trends</TabsTrigger><TabsTrigger value="evidence"><BookOpen size={14} />Evidence ({report.evidence.length})</TabsTrigger></TabsList>
          <TabsContent value="research">
            <Findings title="Research summary" items={report.research.summary} onEvidence={showEvidence} />
            <div className="analysis-findings-grid"><Findings title="Strengths" items={report.research.strengths} onEvidence={showEvidence} tone="positive" /><Findings title="Risks" items={report.research.risks} onEvidence={showEvidence} tone="negative" /></div>
            <Findings title="What to watch" items={report.research.watchItems} onEvidence={showEvidence} />
          </TabsContent>
          <TabsContent value="trends"><p className="analysis-muted">Available periods only. Amounts retain their reporting currency; missing figures are shown as unavailable.</p>
            <TrendTable title="Annual financial history" rows={(report.trends || []).filter(row => row.periodType === 'annual')} evidence={evidence} onEvidence={showEvidence} />
            <TrendTable title="Quarterly financial history" rows={(report.trends || []).filter(row => row.periodType === 'quarterly')} evidence={evidence} onEvidence={showEvidence} />
          </TabsContent>
          <TabsContent value="evidence"><p className="analysis-muted analysis-evidence-intro">Financial amounts retain their reporting currency. Periods may differ between statements and the current quote.</p>
            {!!report.quality?.issues.length && <section className="analysis-data-checks" aria-label="Financial data checks"><h3>Financial data checks</h3>{report.quality.issues.map((issue, index) => <div key={`${issue.code}-${index}`}><span className="analysis-significance">{issue.severity} significance</span><p>{issue.text}</p><div className="analysis-citations">{issue.evidenceIds.map(id => <Button key={id} variant="ghost" size="sm" onClick={() => showEvidence(id)} aria-label={`View flagged evidence ${id}`}>[{id}]</Button>)}</div></div>)}</section>}
            <ol className="analysis-evidence-list">{report.evidence.map(item => <li key={item.id} id={`analysis-evidence-${item.id}`} tabIndex={-1} className={highlight === item.id ? 'is-highlighted' : ''}>
              <div className="analysis-evidence-heading"><span>[{item.id}] {item.label}</span><Chip>{item.kind === 'calculated' && <Check size={11} />}{metricOrigin(item)}</Chip></div>
              <strong className={item.unit === 'text' ? 'analysis-profile' : ''}>{evidenceValue(item)}</strong>
              <small>Period: {item.period}{item.currency && ` · ${item.currency}`}</small>
              {item.sourceField && <small>Source record: {item.sourceField}</small>}
              {item.formula && <div className="analysis-formula"><span>{item.formula}</span><div>{item.inputs.map(id => <Button key={id} variant="ghost" size="sm" onClick={() => showEvidence(id)} aria-label={`View input evidence ${id}`}>[{id}] {evidence[id]?.label}: {evidence[id] && evidenceValue(evidence[id])}</Button>)}</div></div>}
            </li>)}</ol>
          </TabsContent>
        </Tabs>
        <p className="analysis-muted analysis-model">Model: {report.model} · Quote as of {report.quoteAsOf ? new Date(report.quoteAsOf).toLocaleString() : 'unavailable'}<br />Listing: {report.companyId} · Analysis run: {report.analysisRunId}</p>
      </div>}
    </Dialog>
  </>
}
