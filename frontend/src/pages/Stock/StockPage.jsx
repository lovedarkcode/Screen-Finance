import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import StockHeader from '@/components/stock/StockHeader'
import QuarterlyTable from '@/components/stock/QuarterlyTable'
import FinancialTable from '@/components/stock/FinancialTable'
import AIInsightCard from '@/components/stock/AIInsightCard'
import NewsCard from '@/components/stock/NewsCard'
import Overview from './Overview'
import stockService from '@/services/stock.service'

const TABS = [
  'Overview', 'Chart', 'Analysis', 'Peers', 'Quarters',
  'Profit & Loss', 'Balance Sheet', 'Cash Flow', 'Ratios',
  'Investors', 'Documents', 'AI Summary',
]

const emptyTable = (title) => ({ title, unit: 'Live provider data', columns: [], rows: [] })
const optional = (result, fallback) => result.status === 'fulfilled' ? result.value : fallback

const StockPage = () => {
  const { symbol } = useParams()
  const [active, setActive] = useState('Overview')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    const loadStock = async () => {
      setLoading(true)
      setError('')
      try {
        const [
          stock,
          metrics,
          chart,
          quarters,
          profitLoss,
          balanceSheet,
          cashFlow,
          ratios,
          summary,
          about,
          peers,
        ] = await Promise.allSettled([
          stockService.getStock(symbol),
          stockService.getMetrics(symbol),
          stockService.getChart(symbol),
          stockService.getQuarters(symbol),
          stockService.getProfitLoss(symbol),
          stockService.getBalanceSheet(symbol),
          stockService.getCashFlow(symbol),
          stockService.getRatios(symbol),
          stockService.getSummary(symbol),
          stockService.getAbout(symbol),
          stockService.getPeers(symbol),
        ])

        if (!cancelled) {
          if (stock.status === 'rejected') {
            throw stock.reason
          }

          const liveStock = stock.value
          setData({
            stock: liveStock,
            metrics: optional(metrics, [
              { label: 'Current Price', value: `${liveStock.currencySymbol || 'INR'} ${Number(liveStock.price || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}` },
              { label: 'Exchange', value: liveStock.exchange },
              { label: 'Currency', value: liveStock.currency || 'INR' },
            ]),
            chart: optional(chart, []),
            quarters: optional(quarters, emptyTable('Quarterly Results')),
            tables: {
              profitLoss: optional(profitLoss, emptyTable('Profit & Loss')),
              balanceSheet: optional(balanceSheet, emptyTable('Balance Sheet')),
              cashFlow: optional(cashFlow, emptyTable('Cash Flow')),
              ratios: optional(ratios, emptyTable('Ratios')),
            },
            summary: optional(summary, {
              summary: `${liveStock.name} is listed on ${liveStock.exchange}. Live price data is loaded from the market data provider.`,
              keyPoints: [`Symbol: ${liveStock.symbol}`, `Currency: ${liveStock.currency || 'INR'}`],
            }),
            about: optional(about, {
              description: 'Company profile is not available from the live data provider.',
              founded: 'N/A',
              headquarters: 'N/A',
              website: 'N/A',
            }),
            peers: optional(peers, []),
          })
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || 'Could not load live stock data.')
          setData(null)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadStock()
    return () => {
      cancelled = true
    }
  }, [symbol])

  if (loading) {
    return (
      <div className="rounded-lg border border-[#1f2129] bg-[#14161c] p-6 text-sm text-gray-400">
        Loading live NSE/BSE market data...
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6">
        <h2 className="text-base font-semibold text-red-200">Live data unavailable</h2>
        <p className="mt-1 text-sm text-red-100/80">{error}</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-4">
      <div>
        <StockHeader stock={data.stock} />

        <div className="border-b border-[#1f2129] mb-4">
          <nav className="flex items-center gap-5 text-[12px] overflow-x-auto">
            {TABS.map((t) => {
              const isActive = active === t
              return (
                <button
                  key={t}
                  onClick={() => setActive(t)}
                  className={`relative pb-2 whitespace-nowrap transition-colors ${
                    isActive
                      ? 'text-indigo-400 font-medium'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    {t}
                    {t === 'AI Summary' && (
                      <span className="text-[8px] font-semibold px-1 py-0.5 bg-indigo-500/20 text-indigo-300 rounded">
                        NEW
                      </span>
                    )}
                  </span>
                  {isActive && (
                    <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-indigo-400" />
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        <Overview metrics={data.metrics} chartData={data.chart} stock={data.stock} />

        <div className="mt-4">
          <QuarterlyTable quarters={data.quarters} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mt-4">
          <FinancialTable {...data.tables.profitLoss} />
          <FinancialTable {...data.tables.balanceSheet} />
          <FinancialTable {...data.tables.cashFlow} />
          <FinancialTable {...data.tables.ratios} />
        </div>
      </div>

      <aside className="flex flex-col gap-3">
        <AIInsightCard summary={data.summary.summary} keyPoints={data.summary.keyPoints} />
        <NewsCard about={data.about} related={data.peers} />
      </aside>
    </div>
  )
}

export default StockPage
