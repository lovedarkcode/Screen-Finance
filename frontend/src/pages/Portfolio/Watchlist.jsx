import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Star, Landmark, TrendingUp, TrendingDown, Trash2, ArrowUpRight } from 'lucide-react'
import watchlistService from '@/services/watchlist.service'
import stockService from '@/services/stock.service'
import toast from 'react-hot-toast'

const Watchlist = () => {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadWatchlist = async () => {
    setLoading(true)
    setError('')
    try {
      const watchlistData = await watchlistService.getWatchlist()
      const symbols = watchlistData?.items || []
      
      if (symbols.length === 0) {
        setItems([])
        return
      }

      // Fetch details for each symbol in parallel
      const detailsPromises = symbols.map(async (symbol) => {
        try {
          const detail = await stockService.getStock(symbol)
          return { ...detail, symbol }
        } catch (err) {
          // If a stock fails to load, still show the symbol card with minimal info
          return {
            symbol,
            name: symbol,
            price: null,
            change: null,
            changePercent: null,
            exchange: 'Live Provider',
            error: true
          }
        }
      })

      const results = await Promise.all(detailsPromises)
      setItems(results)
    } catch (err) {
      setError('Could not load watchlist. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWatchlist()
  }, [])

  const handleRemove = async (e, symbol) => {
    e.stopPropagation() // Prevent navigating to stock page
    try {
      await watchlistService.removeFromWatchlist(symbol)
      setItems((prev) => prev.filter((item) => item.symbol !== symbol))
      toast.success(`${symbol} removed from watchlist successfully`)
    } catch (err) {
      toast.error('Failed to remove stock from watchlist')
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
        <p className="text-sm">Loading your custom watchlist...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 max-w-2xl mx-auto mt-8">
        <h2 className="text-base font-semibold text-red-200">Error Loading Watchlist</h2>
        <p className="mt-1 text-sm text-red-100/80">{error}</p>
        <button
          onClick={loadWatchlist}
          className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-200 border border-red-500/30 rounded-md text-xs font-semibold transition-all"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-[26px] font-semibold text-white flex items-center gap-2">
            <Star className="w-7 h-7 text-amber-400 fill-amber-400" />
            Watchlist
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Track and view your starred stocks here. Click on any card to view detailed financial analytics.
          </p>
        </div>
        <div className="px-3 py-1.5 bg-[#1a1c23] border border-[#262833] rounded-md text-xs text-gray-400">
          Total Stocks: <span className="font-semibold text-white">{items.length}</span>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[300px] border border-dashed border-[#262833] rounded-xl bg-[#14161c]/50 p-8 text-center max-w-2xl mx-auto mt-4">
          <div className="w-16 h-16 rounded-full bg-indigo-500/10 flex items-center justify-center mb-4">
            <Star className="w-8 h-8 text-indigo-400" />
          </div>
          <h3 className="text-lg font-medium text-white">Your watchlist is empty</h3>
          <p className="text-sm text-gray-400 mt-2 max-w-sm">
            Start adding stocks to your watchlist by clicking the star icon in the stock header.
          </p>
          <button
            onClick={() => navigate('/screens')}
            className="mt-6 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-md text-sm font-medium transition-all shadow-md shadow-indigo-500/10"
          >
            Explore Screens
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {items.map((stock) => {
            const price = Number(stock.price || 0)
            const change = Number(stock.change || 0)
            const changePercent = Number(stock.changePercent || 0)
            const isPositive = change >= 0
            const currency = stock.currencySymbol || 'INR'

            return (
              <div
                key={stock.symbol}
                onClick={() => navigate(`/stock/${stock.symbol}`)}
                className="group relative cursor-pointer rounded-xl border border-[#1f2129] bg-[#14161c]/90 p-5 hover:bg-[#1a1c23] hover:border-indigo-500/40 hover:shadow-lg hover:shadow-indigo-500/5 transition-all duration-300 flex flex-col justify-between min-h-[160px]"
              >
                <div>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-2.5">
                      <div className="w-10 h-10 rounded-lg bg-[#1a1c23] border border-[#262833] flex items-center justify-center shrink-0">
                        <Landmark className="w-5 h-5 text-gray-300 group-hover:text-indigo-400 transition-colors" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-[15px] font-semibold text-white truncate leading-snug group-hover:text-indigo-300 transition-colors">
                          {stock.name}
                        </h3>
                        <span className="text-[11px] text-gray-500 font-mono">
                          {stock.symbol} | {stock.exchange}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={(e) => handleRemove(e, stock.symbol)}
                      className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-md transition-colors shrink-0"
                      title="Remove from watchlist"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="mt-5 flex items-baseline justify-between">
                    <div>
                      {price ? (
                        <div className="text-[17px] font-bold text-white tracking-tight">
                          {currency} {price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </div>
                      ) : (
                        <div className="text-[14px] text-gray-500">Live data unavailable</div>
                      )}
                    </div>

                    {price && (
                      <span
                        className={`flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${
                          isPositive
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-400 border border-red-500/20'
                        }`}
                      >
                        {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                        {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
                      </span>
                    )}
                  </div>
                </div>

                <div className="absolute right-4 bottom-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <ArrowUpRight className="w-4 h-4 text-indigo-400" />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default Watchlist
