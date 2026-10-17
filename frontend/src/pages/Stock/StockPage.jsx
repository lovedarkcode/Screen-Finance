import { Button } from '@/components/ui/button'
import { useEffect, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import StockHeader from '@/components/stock/StockHeader'
import StockToolbar from '@/components/stock/StockToolbar'
import { StockSkeleton } from '@/components/stock/StockUI'
import { DEFAULT_SECTIONS, readPreference } from '@/components/stock/stock-format'
import StockChart from '@/components/stock/StockChart'
import StockMetrics from '@/components/stock/StockMetrics'
import { PriceRange, ReturnsPerformance } from '@/components/stock/StockPerformance'
import StockShareholding from '@/components/stock/StockShareholding'
import StockFinancials from '@/components/stock/StockFinancials'
import StockCompany from '@/components/stock/StockCompany'
import StockPeers from '@/components/stock/StockPeers'
import StockStatements from '@/components/stock/StockStatements'
import { EmptyState, SectionTitle } from '@/components/stock/StockUI'
import stockService from '@/services/stock.service'
import '@/components/stock/stock-detail.css'

function StockDetail({ symbol }) {
  const [data, setData] = useState({})
  const [errors, setErrors] = useState({})
  const [attempt, setAttempt] = useState(0)
  const { theme, setTheme } = useOutletContext()
  const [sections] = useState(() => ({ ...DEFAULT_SECTIONS, ...readPreference('asset-hunter-stock-sections', {}) }))
  useEffect(() => {
    let live = true
    stockService.getStock(symbol).then(stock => {
      if (!live) return
      setData({ stock })
      setErrors({})
      const jobs = {
        overview: () => stockService.getOverview(symbol),
        quarters: () => stockService.getQuarters(symbol),
        peers: () => stockService.getPeers(symbol),
        shareholding: () => stockService.getShareholding(symbol),
      }
      for (const [key, fetch] of Object.entries(jobs)) {
        fetch().then(value => { if (live) setData(previous => ({ ...previous, [key]: value })) })
          .catch(error => { if (live) setErrors(previous => ({ ...previous, [key]: error })) })
      }
    }).catch(error => { if (live) setErrors({ stock: error }) })
    return () => { live = false }
  }, [symbol, attempt])
  const missing = errors.stock?.response?.status === 404
  return <div className="stock-detail" data-stock-theme={theme}>
    <StockToolbar stock={data.stock} theme={theme} setTheme={setTheme} />
    {errors.stock ? <main className="stock-error-page"><h1>{missing ? 'Stock not found' : 'Market data unavailable'}</h1>
      <p>{missing ? `The ticker “${symbol}” doesn't match an available listed stock.` : 'We couldn’t reach the market data provider. Please try again.'}</p>
      {!missing && <Button variant="outline" size="sm" className="stock-button" onClick={() => { setErrors({}); setData({}); setAttempt(value => value + 1) }}>Try again</Button>}
      <Button asChild variant="solid"><Link to="/screens">Go to Screener</Link></Button>
    </main> : !data.stock ? <StockSkeleton /> : <main>
      <StockHeader stock={data.stock} profile={data.overview?.about} />
      {sections.priceChart && <StockChart symbol={data.stock.symbol} currency={data.stock.currency} timeZone={data.stock.timeZone} />}
      {sections.keyMetrics && <StockMetrics metrics={data.overview?.metrics} loading={!data.overview && !errors.overview} error={errors.overview} />}
      {sections.priceRange && <PriceRange stock={data.stock} data={data.overview?.priceRange} loading={!data.overview && !errors.overview} error={errors.overview} />}
      {sections.returns && <ReturnsPerformance data={data.overview?.returns} loading={!data.overview && !errors.overview} error={errors.overview} />}
      {(sections.shareholding || sections.financials) && <section className="stock-section stock-band-alt"><div className="stock-container"><div className={`stock-panel-grid ${!sections.shareholding || !sections.financials ? 'stock-single-panel' : ''}`}>
        {sections.shareholding && <StockShareholding data={data.shareholding} loading={!data.shareholding && !errors.shareholding} error={errors.shareholding} />}
        {sections.financials && <StockFinancials quarters={data.quarters} currency={data.stock.currency} loading={!data.quarters && !errors.quarters} error={errors.quarters} />}
      </div>{sections.financials && <StockStatements symbol={symbol} quarters={errors.quarters ? { error: true } : data.quarters} />}</div></section>}
      {sections.about && <StockCompany stock={data.stock} about={data.overview?.about} loading={!data.overview && !errors.overview} error={errors.overview} />}
      {sections.peers && <StockPeers peers={data.peers} loading={!data.peers && !errors.peers} error={errors.peers} />}
      {sections.insights && <section className="stock-section" id="insights"><div className="stock-container"><SectionTitle>Asset Hunter Insights</SectionTitle>
        {data.overview?.insights?.length ? <><ul className="stock-insights">{data.overview.insights.map(item => <li key={item}>{item}</li>)}</ul><p className="stock-source-note">Computed from the latest available company fundamentals.</p></> : <EmptyState>No computed highlights available</EmptyState>}
      </div></section>}
      <footer className="stock-source-footer stock-container">Market data: Yahoo Finance / yfinance · Prices may be delayed. Availability varies by company.</footer>
    </main>}
  </div>
}

export default function StockPage() {
  const { symbol } = useParams()
  return <StockDetail key={symbol} symbol={symbol} />
}
