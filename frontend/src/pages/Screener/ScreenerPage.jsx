import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Shield,
  Train,
  Zap,
  Factory,
  Cpu,
  Code,
  Building,
  Car,
  Pill,
  Star,
  ArrowUpRight,
  Search,
  Activity,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Info
} from 'lucide-react'
import stockService from '@/services/stock.service'
import watchlistService from '@/services/watchlist.service'
import toast from 'react-hot-toast'

const SECTOR_ICONS = {
  defence: Shield,
  railway: Train,
  energy: Zap,
  production: Factory,
  electronics: Cpu,
  it: Code,
  banking: Building,
  auto: Car,
  pharma: Pill,
}

const ScreenerPage = () => {
  const navigate = useNavigate()
  const [sectors, setSectors] = useState([])
  const [activeSector, setActiveSector] = useState(null)
  const [stocks, setStocks] = useState([])
  const [loadingSectors, setLoadingSectors] = useState(true)
  const [loadingStocks, setLoadingStocks] = useState(false)
  const [watchlistSymbols, setWatchlistSymbols] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  const loadInitialData = async () => {
    try {
      setLoadingSectors(true)
      const [sectorsData, watchlistData] = await Promise.all([
        stockService.getSectors(),
        watchlistService.getWatchlist(),
      ])
      setSectors(sectorsData)
      setWatchlistSymbols(watchlistData?.items || [])
      
      if (sectorsData.length > 0) {
        setActiveSector(sectorsData[0])
      }
    } catch (err) {
      toast.error('Failed to load sectors metadata')
    } finally {
      setLoadingSectors(false)
    }
  }

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadSectorStocks = async () => {
    if (!activeSector) return
    try {
      setLoadingStocks(true)
      const stocksData = await stockService.getSectorStocks(activeSector.id)
      setStocks(stocksData)
    } catch (err) {
      toast.error(`Failed to load stocks for ${activeSector.name}`)
    } finally {
      setLoadingStocks(false)
    }
  }

  useEffect(() => {
    loadSectorStocks()
  }, [activeSector])

  const toggleWatchlist = async (e, symbol) => {
    e.stopPropagation()
    const isStarred = watchlistSymbols.includes(symbol)
    try {
      if (isStarred) {
        await watchlistService.removeFromWatchlist(symbol)
        setWatchlistSymbols(prev => prev.filter(sym => sym !== symbol))
        toast.success(`${symbol} removed from watchlist`)
      } else {
        await watchlistService.addToWatchlist(symbol)
        setWatchlistSymbols(prev => [...prev, symbol])
        toast.success(`${symbol} added to watchlist`)
      }
    } catch (err) {
      toast.error('Failed to update watchlist')
    }
  }

  // Filter stocks based on search input
  const filteredStocks = stocks.filter(stock => 
    stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    stock.symbol.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Calculate average performance of the active sector
  const validChangePercents = stocks
    .map(s => s.changePercent)
    .filter(v => v !== null && v !== undefined)
  const avgChange = validChangePercents.length > 0
    ? validChangePercents.reduce((a, b) => a + b, 0) / validChangePercents.length
    : 0

  if (loadingSectors) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
        <p className="text-sm">Loading market sectors...</p>
      </div>
    )
  }

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-[26px] font-semibold text-white flex items-center gap-2">
          <Activity className="w-7 h-7 text-indigo-400" />
          Indian Market Screener
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Browse sectors currently shaping the Indian stock market and track constituent equities in real time.
        </p>
      </div>

      {/* Grid of Sector Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-9 gap-3 mb-8">
        {sectors.map((sec) => {
          const IconComponent = SECTOR_ICONS[sec.id] || Info
          const isActive = activeSector?.id === sec.id

          return (
            <button
              key={sec.id}
              onClick={() => {
                setActiveSector(sec)
                setSearchQuery('')
              }}
              className={`group flex xl:flex-col items-center justify-start xl:justify-center text-left xl:text-center p-4 rounded-xl border transition-all duration-300 gap-3 cursor-pointer ${
                isActive
                  ? 'bg-indigo-500/10 border-indigo-500/50 shadow-md shadow-indigo-500/5'
                  : 'bg-[#14161c]/90 border-[#1f2129] hover:bg-[#1a1c23] hover:border-indigo-500/25'
              }`}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 transition-all ${
                isActive
                  ? 'bg-indigo-500/20 text-indigo-400'
                  : 'bg-[#1a1c23] text-gray-400 group-hover:text-indigo-300'
              }`}>
                <IconComponent className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <div className={`text-xs font-semibold truncate ${isActive ? 'text-indigo-300' : 'text-gray-300 group-hover:text-white'}`}>
                  {sec.name}
                </div>
                <div className="text-[10px] text-gray-500 mt-0.5">
                  {sec.tickerCount} Stocks
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Active Sector Detail Card */}
      {activeSector && (
        <div className="rounded-xl border border-[#1f2129] bg-[#14161c]/60 p-6 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-3xl">
            <span className="text-[10px] tracking-wider uppercase font-semibold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full">
              Active Sector
            </span>
            <h2 className="text-xl font-bold text-white mt-2 flex items-center gap-2">
              {activeSector.name}
            </h2>
            <p className="text-sm text-gray-400 mt-1.5 leading-relaxed">
              {activeSector.description}
            </p>
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <div className="bg-[#1a1c23] border border-[#262833] rounded-xl px-5 py-3 flex flex-col items-center">
              <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Constituents</span>
              <span className="text-lg font-bold text-white mt-1">{activeSector.tickerCount} Stocks</span>
            </div>
            
            <div className={`border rounded-xl px-5 py-3 flex flex-col items-center min-w-[130px] ${
              avgChange >= 0
                ? 'bg-emerald-500/5 border-emerald-500/20'
                : 'bg-red-500/5 border-red-500/20'
            }`}>
              <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Avg. 1D Return</span>
              <span className={`text-lg font-bold mt-1 flex items-center gap-1 ${
                avgChange >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {avgChange >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {avgChange >= 0 ? '+' : ''}{avgChange.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Stocks Table Section */}
      <div className="bg-[#14161c]/90 border border-[#1f2129] rounded-xl overflow-hidden">
        {/* Table Toolbar */}
        <div className="p-4 border-b border-[#1f2129] flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:max-w-xs">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search by name or symbol..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#1a1c23] border border-[#262833] rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
          </div>

          <button
            onClick={loadSectorStocks}
            disabled={loadingStocks}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#1a1c23] hover:bg-[#20232c] text-gray-300 hover:text-white rounded-lg border border-[#262833] text-xs font-semibold transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingStocks ? 'animate-spin' : ''}`} />
            Refresh Quotes
          </button>
        </div>

        {/* Loading / Empty / Data Table */}
        {loadingStocks ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mb-3"></div>
            <p className="text-xs">Fetching real-time quotes...</p>
          </div>
        ) : filteredStocks.length === 0 ? (
          <div className="text-center py-16 text-gray-500 text-xs">
            No stocks found matching "{searchQuery}" in this sector.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#1f2129] text-[11px] text-gray-500 font-semibold tracking-wider bg-[#0d0e13]/30">
                  <th className="py-3.5 px-6">Company</th>
                  <th className="py-3.5 px-4">Symbol</th>
                  <th className="py-3.5 px-4 text-right">Price</th>
                  <th className="py-3.5 px-4 text-right">1D Change</th>
                  <th className="py-3.5 px-4 text-right">1D Change %</th>
                  <th className="py-3.5 px-6 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f2129] text-xs">
                {filteredStocks.map((stock) => {
                  const price = stock.price !== null ? Number(stock.price) : null
                  const change = stock.change !== null ? Number(stock.change) : null
                  const changePercent = stock.changePercent !== null ? Number(stock.changePercent) : null
                  const isPositive = change >= 0
                  const isStarred = watchlistSymbols.includes(stock.symbol)

                  return (
                    <tr
                      key={stock.symbol}
                      onClick={() => navigate(`/stock/${stock.symbol}`)}
                      className="hover:bg-[#1a1c23]/60 cursor-pointer transition-colors group"
                    >
                      {/* Name */}
                      <td className="py-4 px-6 font-semibold text-white group-hover:text-indigo-400 transition-colors">
                        {stock.name}
                      </td>
                      {/* Symbol */}
                      <td className="py-4 px-4 font-mono text-[11px] text-gray-400">
                        {stock.symbol}
                      </td>
                      {/* Price */}
                      <td className="py-4 px-4 text-right font-bold text-white">
                        {price !== null ? (
                          `₹${price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                        ) : (
                          <span className="text-gray-500 font-normal">N/A</span>
                        )}
                      </td>
                      {/* Change */}
                      <td className={`py-4 px-4 text-right font-semibold ${
                        price === null ? 'text-gray-500' : isPositive ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {price !== null && change !== null ? (
                          `${isPositive ? '+' : ''}${change.toFixed(2)}`
                        ) : (
                          '--'
                        )}
                      </td>
                      {/* Change % */}
                      <td className="py-4 px-4 text-right">
                        {price !== null && changePercent !== null ? (
                          <span className={`inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded-full text-[11px] ${
                            isPositive
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-red-500/10 text-red-400 border border-red-500/20'
                          }`}>
                            {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-gray-500 font-normal">N/A</span>
                        )}
                      </td>
                      {/* Actions */}
                      <td className="py-4 px-6 text-center" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={(e) => toggleWatchlist(e, stock.symbol)}
                            className={`p-1.5 rounded-lg border transition-all ${
                              isStarred
                                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20'
                                : 'bg-[#1a1c23] border-[#262833] text-gray-500 hover:text-white hover:border-gray-500'
                            }`}
                            title={isStarred ? "Remove from Watchlist" : "Add to Watchlist"}
                          >
                            <Star className={`w-3.5 h-3.5 ${isStarred ? 'fill-amber-400' : ''}`} />
                          </button>
                          
                          <button
                            onClick={() => navigate(`/stock/${stock.symbol}`)}
                            className="p-1.5 bg-[#1a1c23] hover:bg-indigo-500 hover:text-white border border-[#262833] hover:border-indigo-400 rounded-lg text-gray-400 transition-all"
                            title="View Financials"
                          >
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScreenerPage
