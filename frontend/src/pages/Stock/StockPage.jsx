import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import StockHeader from '@/components/stock/StockHeader'
import StockToolbar from '@/components/stock/StockToolbar'
import { StockSkeleton } from '@/components/stock/StockUI'
import { DEFAULT_SECTIONS, readPreference } from '@/components/stock/stock-format'
import Overview from './Overview'
import stockService from '@/services/stock.service'
import '@/components/stock/stock-detail.css'

function StockDetail({ symbol }) {
  const [data, setData] = useState({})
  const [errors, setErrors] = useState({})
  const [attempt, setAttempt] = useState(0)
  const [theme, setTheme] = useState(() => readPreference('asset-hunter-stock-theme', 'dark'))
  const [sections, setSections] = useState(() => ({ ...DEFAULT_SECTIONS, ...readPreference('asset-hunter-stock-sections', {}) }))
  useEffect(() => { localStorage.setItem('asset-hunter-stock-theme', JSON.stringify(theme)) }, [theme])
  useEffect(() => { localStorage.setItem('asset-hunter-stock-sections', JSON.stringify(sections)) }, [sections])
  useEffect(() => {
    let live = true
    stockService.getStock(symbol).then(stock => {
      if (!live) return
      setData({ stock })
      setErrors({})
      const jobs = {
        metrics: () => stockService.getMetrics(symbol),
        chart: () => stockService.getChart(symbol, '6M'),
        quarters: () => stockService.getQuarters(symbol),
        about: () => stockService.getAbout(symbol),
        peers: () => stockService.getPeers(symbol),
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
    <StockToolbar stock={data.stock} theme={theme} setTheme={setTheme} sections={sections} setSections={setSections} />
    {errors.stock ? <main className="stock-error-page"><h1>{missing ? 'Stock not found' : 'Market data unavailable'}</h1>
      <p>{missing ? `The ticker “${symbol}” doesn't match an available listed stock.` : 'We couldn’t reach the market data provider. Please try again.'}</p>
      {!missing && <button className="stock-button" onClick={() => { setErrors({}); setData({}); setAttempt(value => value + 1) }}>Try again</button>}
      <Link className="stock-button stock-primary" to="/screens">Go to Screener</Link>
    </main> : !data.stock ? <StockSkeleton /> : <main>
      <StockHeader stock={data.stock} profile={data.about} />
      <div className="stock-container stock-section"><Overview metrics={data.metrics || []} chartData={data.chart || []} stock={data.stock} /></div>
    </main>}
  </div>
}

export default function StockPage() {
  const { symbol } = useParams()
  return <StockDetail key={symbol} symbol={symbol} />
}
