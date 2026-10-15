import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import StockHeader from '@/components/stock/StockHeader'
import StockToolbar from '@/components/stock/StockToolbar'
import { StockSkeleton } from '@/components/stock/StockUI'
import { DEFAULT_SECTIONS, readPreference } from '@/components/stock/stock-format'
import StockChart from '@/components/stock/StockChart'
import StockMetrics from '@/components/stock/StockMetrics'
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
        overview: () => stockService.getOverview(symbol),
        quarters: () => stockService.getQuarters(symbol),
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
      <StockHeader stock={data.stock} profile={data.overview?.about} />
      {sections.priceChart && <StockChart symbol={symbol} />}
      {sections.keyMetrics && <StockMetrics metrics={data.overview?.metrics} loading={!data.overview && !errors.overview} error={errors.overview} />}
    </main>}
  </div>
}

export default function StockPage() {
  const { symbol } = useParams()
  return <StockDetail key={symbol} symbol={symbol} />
}
