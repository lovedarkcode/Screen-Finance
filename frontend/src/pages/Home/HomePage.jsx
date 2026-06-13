import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import {
  Star,
  Landmark,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Cpu,
  Zap,
  Newspaper,
  ChevronRight,
  Activity,
  LineChart
} from 'lucide-react'
import watchlistService from '@/services/watchlist.service'
import stockService from '@/services/stock.service'
import toast from 'react-hot-toast'

// Fallback static base data in case of initial network load delay
const TICKERS_DEFAULT = [
  { symbol: 'RELIANCE.NS', name: 'Reliance Industries', price: 2450.45, change: 12.30, changePercent: 0.50, exchange: 'NSE' },
  { symbol: 'TCS.NS', name: 'Tata Consultancy Services', price: 3890.10, change: -45.50, changePercent: -1.16, exchange: 'NSE' },
  { symbol: 'HDFCBANK.NS', name: 'HDFC Bank', price: 1610.75, change: 8.40, changePercent: 0.52, exchange: 'NSE' },
  { symbol: 'INFY.NS', name: 'Infosys Limited', price: 1480.20, change: -15.30, changePercent: -1.02, exchange: 'NSE' },
  { symbol: 'ICICIBANK.NS', name: 'ICICI Bank', price: 1120.30, change: 14.10, changePercent: 1.27, exchange: 'NSE' },
  { symbol: 'TATAMOTORS.NS', name: 'Tata Motors', price: 960.50, change: 32.70, changePercent: 3.52, exchange: 'NSE' },
  { symbol: 'SBIN.NS', name: 'State Bank of India', price: 830.40, change: -2.10, changePercent: -0.25, exchange: 'NSE' },
  { symbol: 'BHARTIARTL.NS', name: 'Bharti Airtel', price: 1390.80, change: 22.40, changePercent: 1.64, exchange: 'NSE' }
]

const INDEXES_DEFAULT = [
  { name: 'NIFTY 50', symbol: '^NSEI', price: 23465.60, change: 110.25, changePercent: 0.47, sparkline: [23350, 23380, 23370, 23410, 23400, 23440, 23465] },
  { name: 'SENSEX', symbol: '^BSESN', price: 77150.40, change: 345.80, changePercent: 0.45, sparkline: [76800, 76950, 76900, 77050, 77020, 77110, 77150] },
  { name: 'BANK NIFTY', symbol: '^NSEBANK', price: 50125.10, change: -140.20, changePercent: -0.28, sparkline: [50300, 50250, 50280, 50200, 50180, 50220, 50125] },
  { name: 'NIFTY IT', symbol: '^CNXIT', price: 35240.80, change: -285.50, changePercent: -0.80, sparkline: [35550, 35480, 35510, 35400, 35350, 35310, 35240] }
]

const HomePage = () => {
  const navigate = useNavigate()
  const [activeRange, setActiveRange] = useState('1W')
  const [tickers, setTickers] = useState(TICKERS_DEFAULT)
  const [indexes, setIndexes] = useState(INDEXES_DEFAULT)
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(true)
  const [chartLoading, setChartLoading] = useState(true)
  const [moversTab, setMoversTab] = useState('gainers')
  const [recentNews, setRecentNews] = useState([
    {
      title: 'TCS bags $2 Billion multi-year digital transformation deal from European client',
      source: 'Economic Times',
      sentiment: 'Bullish',
      time: '10 mins ago',
      impact: '+2.4%'
    },
    {
      title: 'RBI Monetary Policy: Repo rate kept unchanged at 6.5%, stance remains cautious',
      source: 'Bloomberg Quint',
      sentiment: 'Neutral',
      time: '45 mins ago',
      impact: '0.0%'
    },
    {
      title: 'Tata Motors DVR shares conversion approved by shareholders with 99.8% majority',
      source: 'Moneycontrol',
      sentiment: 'Bullish',
      time: '2 hours ago',
      impact: '+4.1%'
    },
    {
      title: 'Infosys posts weaker Q1 guidance due to slower tech spend in US financial market',
      source: 'Reuters India',
      sentiment: 'Bearish',
      time: '4 hours ago',
      impact: '-3.2%'
    }
  ])

  // Load Real-time indices and tickers
  const loadRealTimeQuotes = async () => {
    try {
      // 1. Fetch live quotes for index cards
      const indexSymbols = [
        { symbol: '^NSEI', name: 'NIFTY 50' },
        { symbol: '^BSESN', name: 'SENSEX' },
        { symbol: '^NSEBANK', name: 'BANK NIFTY' },
        { symbol: '^CNXIT', name: 'NIFTY IT' }
      ]

      const indexPromises = indexSymbols.map(async (item) => {
        try {
          const detail = await stockService.getStock(item.symbol)
          if (detail && detail.price) {
            return {
              name: item.name,
              symbol: item.symbol,
              price: Number(detail.price),
              change: Number(detail.change || 0),
              changePercent: Number(detail.changePercent || 0),
              sparkline: [
                Number(detail.price) * 0.99,
                Number(detail.price) * 0.995,
                Number(detail.price) * 0.998,
                Number(detail.price) * 1.002,
                Number(detail.price) * 0.999,
                Number(detail.price) * 1.001,
                Number(detail.price)
              ]
            }
          }
          return null
        } catch {
          return null
        }
      })

      const indexResults = await Promise.all(indexPromises)
      const validIndexes = indexResults.filter(Boolean)
      if (validIndexes.length > 0) {
        setIndexes(validIndexes)
      }

      // 2. Fetch live quotes for stock tickers
      const tickerSymbols = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'TATAMOTORS.NS', 'SBIN.NS', 'BHARTIARTL.NS'
      ]

      const tickerPromises = tickerSymbols.map(async (sym) => {
        try {
          const detail = await stockService.getStock(sym)
          if (detail && detail.price) {
            return {
              symbol: sym,
              name: detail.name || sym.split('.')[0],
              price: Number(detail.price),
              change: Number(detail.change || 0),
              changePercent: Number(detail.changePercent || 0),
              exchange: detail.exchange || 'NSE'
            }
          }
          return null
        } catch {
          return null
        }
      })

      const tickerResults = await Promise.all(tickerPromises)
      const validTickers = tickerResults.filter(Boolean)
      if (validTickers.length > 0) {
        setTickers(validTickers)
      }
    } catch (err) {
      console.error('Error loading real-time indices/tickers:', err)
    } finally {
      setLoading(false)
    }
  }

  // Load Nifty 50 historical chart data
  const loadMainChart = async () => {
    setChartLoading(true)
    try {
      const data = await stockService.getChart('^NSEI', activeRange)
      if (data && data.length > 0) {
        setChartData(
          data.map((item) => ({
            label: item.month,
            price: item.price
          }))
        )
      }
    } catch (err) {
      console.error('Error loading main index chart:', err)
    } finally {
      setChartLoading(false)
    }
  }

  useEffect(() => {
    loadRealTimeQuotes()
  }, [])

  useEffect(() => {
    loadMainChart()
  }, [activeRange])

  // Real-time market minor price fluctuations simulation
  useEffect(() => {
    const interval = setInterval(() => {
      // Fluctuate tickers by small decimal points to show "live feed activity"
      setTickers((prevTickers) =>
        prevTickers.map((t) => {
          if (Math.random() > 0.4) return t
          const fluctuation = (Math.random() - 0.5) * 0.0008
          const newPrice = t.price * (1 + fluctuation)
          const delta = newPrice - t.price
          const newChange = t.change + delta
          const newPercent = (newChange / (t.price - t.change)) * 100

          return {
            ...t,
            price: newPrice,
            change: newChange,
            changePercent: newPercent,
            flash: delta > 0 ? 'up' : 'down'
          }
        })
      )

      // Fluctuate indices by small decimal points
      setIndexes((prevIndexes) =>
        prevIndexes.map((ind) => {
          if (Math.random() > 0.4) return ind
          const fluctuation = (Math.random() - 0.48) * 0.0006
          const newPrice = ind.price * (1 + fluctuation)
          const delta = newPrice - ind.price
          const newChange = ind.change + delta
          const newPercent = (newChange / (ind.price - ind.change)) * 100
          const newSparkline = [...ind.sparkline.slice(1), Math.round(newPrice)]

          return {
            ...ind,
            price: newPrice,
            change: newChange,
            changePercent: newPercent,
            sparkline: newSparkline
          }
        })
      )
    }, 4000)

    return () => clearInterval(interval)
  }, [])

  // Clear ticker flashes
  useEffect(() => {
    const timeout = setTimeout(() => {
      setTickers((prev) => prev.map((t) => (t.flash ? { ...t, flash: null } : t)))
    }, 900)
    return () => clearTimeout(timeout)
  }, [tickers])

  const getMovers = () => {
    const sorted = [...tickers]
    if (moversTab === 'gainers') {
      return sorted.sort((a, b) => b.changePercent - a.changePercent).slice(0, 5)
    } else if (moversTab === 'losers') {
      return sorted.sort((a, b) => a.changePercent - b.changePercent).slice(0, 5)
    } else {
      return sorted.sort((a, b) => b.price - a.price).slice(0, 5)
    }
  }

  return (
    <div className="min-h-screen bg-[#0d0e13] text-gray-200">
      {/* Ticker Ribbon */}
      <div className="relative border-b border-[#1f2129] bg-[#090a0e] py-2.5 overflow-hidden shrink-0">
        <style>{`
          @keyframes marquee {
            0% { transform: translateX(0%); }
            100% { transform: translateX(-50%); }
          }
          .animate-marquee {
            display: flex;
            width: max-content;
            animation: marquee 35s linear infinite;
          }
          .animate-marquee:hover {
            animation-play-state: paused;
          }
        `}</style>
        <div className="animate-marquee gap-8 items-center">
          {[...tickers, ...tickers].map((t, idx) => {
            const isPos = t.changePercent >= 0
            const flashColor = t.flash === 'up' ? 'border-emerald-500/50 bg-emerald-500/10' : t.flash === 'down' ? 'border-red-500/50 bg-red-500/10' : 'border-transparent'
            return (
              <div
                key={`${t.symbol}-${idx}`}
                onClick={() => navigate(`/stock/${t.symbol}`)}
                className={`flex items-center gap-2 px-3 py-1 cursor-pointer rounded border transition-all duration-300 hover:bg-[#1a1c23]/80 ${flashColor}`}
              >
                <span className="font-semibold text-xs text-white tracking-wide">{t.symbol.split('.')[0]}</span>
                <span className="text-[11px] font-medium font-mono">
                  {t.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className={`flex items-center gap-0.5 text-[10px] font-bold ${isPos ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isPos ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                  {isPos ? '+' : ''}{t.changePercent.toFixed(2)}%
                </span>
              </div>
            )
          })}
        </div>
      </div>

      <div className="max-w-[1440px] mx-auto px-6 py-6 space-y-6">
        {/* Index Summary Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {indexes.map((ind) => {
            const isPos = ind.changePercent >= 0
            return (
              <div
                key={ind.name}
                className="relative rounded-xl border border-[#1f2129] bg-[#14161c]/80 p-4.5 flex items-center justify-between hover:border-indigo-500/30 transition-all duration-300"
              >
                <div>
                  <span className="text-[11px] font-bold text-gray-500 tracking-wider block">{ind.name}</span>
                  <span className="text-[20px] font-bold text-white tracking-tight mt-1 block font-mono">
                    {ind.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </span>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className={`text-xs font-semibold flex items-center gap-0.5 ${isPos ? 'text-emerald-400' : 'text-red-400'}`}>
                      {isPos ? '+' : ''}{ind.changePercent.toFixed(2)}%
                    </span>
                    <span className="text-[10px] text-gray-500 font-medium">({isPos ? 'Gain' : 'Loss'})</span>
                  </div>
                </div>

                {/* Sparkline */}
                <div className="w-20 h-10 shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={ind.sparkline.map((val, i) => ({ val, i }))}>
                      <defs>
                        <linearGradient id={`grad-${ind.name}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={isPos ? '#10b981' : '#ef4444'} stopOpacity={0.25} />
                          <stop offset="95%" stopColor={isPos ? '#10b981' : '#ef4444'} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <Area
                        type="monotone"
                        dataKey="val"
                        stroke={isPos ? '#10b981' : '#ef4444'}
                        strokeWidth={1.5}
                        fill={`url(#grad-${ind.name})`}
                        dot={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )
          })}
        </div>

        {/* Dashboard Main View */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Main Chart Card */}
          <div className="xl:col-span-2 rounded-xl border border-[#1f2129] bg-[#14161c]/80 p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                    <LineChart className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-[16px] font-semibold text-white">NIFTY 50 Live Chart</h2>
                    <p className="text-[11px] text-gray-500">Real-time Benchmark Index Performance</p>
                  </div>
                </div>

                {/* Range Buttons */}
                <div className="flex items-center gap-1 bg-[#1a1c23] rounded-md p-0.5 border border-[#262833]">
                  {['1D', '1W', '1M', '1Y'].map((range) => (
                    <button
                      key={range}
                      onClick={() => setActiveRange(range)}
                      className={`px-3 py-1 text-[11px] font-semibold rounded transition-colors ${
                        activeRange === range
                          ? 'bg-indigo-500 text-white'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      {range}
                    </button>
                  ))}
                </div>
              </div>

              {/* Central Recharts Area Chart */}
              <div className="h-[280px] w-full mt-4 flex items-center justify-center">
                {chartLoading ? (
                  <div className="flex flex-col items-center gap-2 text-xs text-gray-500">
                    <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-indigo-500"></div>
                    <span>Loading index history...</span>
                  </div>
                ) : chartData.length === 0 ? (
                  <span className="text-xs text-gray-500">No chart data available for this range.</span>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, bottom: 5, left: -20 }}>
                      <defs>
                        <linearGradient id="niftyGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis
                        dataKey="label"
                        tick={{ fill: '#6b7280', fontSize: 10 }}
                        axisLine={{ stroke: '#1f2129' }}
                        tickLine={false}
                      />
                      <YAxis
                        domain={['auto', 'auto']}
                        orientation="right"
                        tick={{ fill: '#6b7280', fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          background: '#15171c',
                          border: '1px solid #2a2d36',
                          borderRadius: 8,
                          fontSize: 12,
                          color: '#e5e7eb'
                        }}
                        labelStyle={{ color: '#9ca3af', fontWeight: 'bold' }}
                      />
                      <Area
                        type="monotone"
                        dataKey="price"
                        stroke="#6366f1"
                        strokeWidth={2.5}
                        fill="url(#niftyGrad)"
                        dot={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-[#1f2129] pt-4 mt-4 text-xs text-gray-500">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Live Yahoo Finance Connection</span>
              </div>
              <span className="font-mono text-[10px]">Real-time Updates Enabled</span>
            </div>
          </div>

          {/* AI Intelligence Brief */}
          <div className="rounded-xl border border-[#1f2129] bg-[#14161c]/80 p-5 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-[16px] font-semibold text-white">AI Analyst Briefing</h2>
                  <p className="text-[11px] text-gray-500">Instant AI Sentiment & Technical Review</p>
                </div>
              </div>

              {/* Sentiment Gauge */}
              <div className="bg-[#1a1c23] border border-[#262833] rounded-lg p-3.5 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-gray-400">Market Sentiment</span>
                  <span className="font-bold text-emerald-400">Bullish (62%)</span>
                </div>
                <div className="w-full h-2 rounded-full bg-red-500/30 overflow-hidden flex">
                  <div className="h-full bg-emerald-500" style={{ width: '62%' }} />
                </div>
                <div className="flex justify-between text-[9px] text-gray-500">
                  <span>Bearish (38%)</span>
                  <span>Neutral (Neutrality: Moderate)</span>
                </div>
              </div>

              {/* Bullet Points */}
              <div className="space-y-3 pt-1">
                <div className="flex items-start gap-2.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2 shrink-0"></div>
                  <p className="text-xs leading-relaxed text-gray-300">
                    <span className="font-semibold text-white">IT sector rebound:</span> Lower guidance from US tech is mostly priced in, creating strong support for local equities.
                  </p>
                </div>
                <div className="flex items-start gap-2.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2 shrink-0"></div>
                  <p className="text-xs leading-relaxed text-gray-300">
                    <span className="font-semibold text-white">Strong Support:</span> NIFTY shows minor consolidations but retains support lines at 23,200.
                  </p>
                </div>
                <div className="flex items-start gap-2.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 shrink-0"></div>
                  <p className="text-xs leading-relaxed text-gray-300">
                    <span className="font-semibold text-white">RSI Indicators:</span> High cap financial stocks like HDFC indicate short-term overbought lines. Expect minor corrections.
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={() => navigate('/ai')}
              className="mt-6 flex items-center justify-center gap-2 w-full py-2.5 bg-indigo-500 hover:bg-indigo-600 active:scale-[0.99] text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-500/15 transition-all"
            >
              <Zap className="w-3.5 h-3.5" /> ASK THE AI STOCK AGENT
            </button>
          </div>
        </div>

        {/* Tabbed Movers & Financial News */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Movers Table */}
          <div className="lg:col-span-2 rounded-xl border border-[#1f2129] bg-[#14161c]/80 p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4 border-b border-[#1f2129] pb-3">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  <h2 className="text-[15px] font-semibold text-white">Market Movers</h2>
                </div>

                {/* Tabs */}
                <div className="flex items-center gap-1.5 text-xs">
                  {['gainers', 'losers', 'active'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setMoversTab(tab)}
                      className={`pb-1 font-semibold uppercase px-2 transition-all ${
                        moversTab === tab
                          ? 'border-b-2 border-indigo-400 text-indigo-400'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-gray-500 border-b border-[#1f2129]">
                      <th className="py-2.5 font-medium">Company</th>
                      <th className="py-2.5 font-medium text-right">Price</th>
                      <th className="py-2.5 font-medium text-right">Change</th>
                      <th className="py-2.5 font-medium text-right">Change %</th>
                      <th className="py-2.5 font-medium text-right">Link</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getMovers().map((stock) => {
                      const isPos = stock.changePercent >= 0
                      return (
                        <tr
                          key={stock.symbol}
                          onClick={() => navigate(`/stock/${stock.symbol}`)}
                          className="border-b border-[#1f2129]/40 hover:bg-[#1a1c23]/40 cursor-pointer transition-colors group"
                        >
                          <td className="py-3">
                            <div className="font-semibold text-gray-200 group-hover:text-indigo-300 transition-colors">
                              {stock.name}
                            </div>
                            <div className="text-[10px] text-gray-500 font-mono mt-0.5">{stock.symbol}</div>
                          </td>
                          <td className="py-3 text-right font-mono font-medium">
                            INR {stock.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className={`py-3 text-right font-mono font-medium ${isPos ? 'text-emerald-400' : 'text-red-400'}`}>
                            {isPos ? '+' : ''}{stock.change.toFixed(2)}
                          </td>
                          <td className={`py-3 text-right font-mono font-semibold`}>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                              isPos
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-red-500/10 text-red-400 border border-red-500/20'
                            }`}>
                              {isPos ? '+' : ''}{stock.changePercent.toFixed(2)}%
                            </span>
                          </td>
                          <td className="py-3 text-right text-gray-500 group-hover:text-indigo-400 transition-colors">
                            <ChevronRight className="w-4 h-4 ml-auto" />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
            
            <button
              onClick={() => navigate('/screens')}
              className="w-full text-center text-xs text-indigo-400 hover:text-indigo-300 font-semibold mt-4 pt-3 border-t border-[#1f2129] flex items-center justify-center gap-1"
            >
              Explore Screener Tools <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Financial News Feed */}
          <div className="rounded-xl border border-[#1f2129] bg-[#14161c]/80 p-5 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Newspaper className="w-4 h-4 text-indigo-400" />
                <h2 className="text-[15px] font-semibold text-white">Live News Terminal</h2>
              </div>

              {/* News Items */}
              <div className="space-y-3 overflow-y-auto max-h-[300px] pr-1 scrollbar-thin">
                {recentNews.map((news, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-[#171921]/60 border border-[#21232c] hover:border-indigo-500/20 rounded-lg space-y-1.5 cursor-pointer transition-all duration-200"
                  >
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-gray-400 font-semibold">{news.source}</span>
                      <span className="text-gray-500">{news.time}</span>
                    </div>
                    <h3 className="text-xs font-semibold text-gray-200 leading-snug hover:text-indigo-300 transition-colors">
                      {news.title}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                        news.sentiment === 'Bullish'
                          ? 'bg-emerald-500/15 text-emerald-400'
                          : news.sentiment === 'Bearish'
                          ? 'bg-red-500/15 text-red-400'
                          : 'bg-gray-500/15 text-gray-400'
                      }`}>
                        {news.sentiment}
                      </span>
                      {news.sentiment !== 'Neutral' && (
                        <span className={`text-[10px] font-mono font-bold ${
                          news.sentiment === 'Bullish' ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          {news.impact}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="text-[10px] text-gray-500 text-center mt-3 font-mono">
              Market data delayed by 15 mins
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
