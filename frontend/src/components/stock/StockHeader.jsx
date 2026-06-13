import { useEffect, useState } from 'react'
import { toast } from 'react-hot-toast'
import watchlistService from '@/services/watchlist.service'
import {
  ChevronDown,
  Star,
  MessageSquare,
  FileDown,
  Plus,
  Landmark,
} from 'lucide-react'

const StockHeader = ({ stock }) => {
  const [isStarred, setIsStarred] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let active = true
    const checkWatchlist = async () => {
      if (!stock || !stock.symbol) return
      try {
        const data = await watchlistService.getWatchlist()
        if (active && data && Array.isArray(data.items)) {
          const symbolUpper = stock.symbol.toUpperCase()
          setIsStarred(data.items.includes(symbolUpper))
        }
      } catch (err) {
        console.error('Error fetching watchlist:', err)
      }
    }
    checkWatchlist()
    return () => {
      active = false
    }
  }, [stock?.symbol])

  const toggleWatchlist = async () => {
    if (!stock || !stock.symbol || loading) return
    setLoading(true)
    const symbolUpper = stock.symbol.toUpperCase()
    try {
      if (isStarred) {
        await watchlistService.removeFromWatchlist(symbolUpper)
        setIsStarred(false)
        toast.success(`${stock.name || symbolUpper} removed from watchlist successfully`)
      } else {
        await watchlistService.addToWatchlist(symbolUpper)
        setIsStarred(true)
        toast.success(`${stock.name || symbolUpper} has been added to watchlist successfully`)
      }
    } catch (err) {
      console.error('Error toggling watchlist:', err)
      toast.error('Failed to update watchlist')
    } finally {
      setLoading(false)
    }
  }

  const change = Number(stock.change || 0)
  const changePercent = Number(stock.changePercent || 0)
  const price = Number(stock.price || 0)
  const isPositive = change >= 0
  const currency = stock.currencySymbol || stock.currency || 'INR'


  return (
    <section className="flex items-start justify-between gap-6 mb-5">
      <div className="flex items-start gap-4">
        <div className="w-14 h-14 rounded-xl bg-[#1a1c23] border border-[#262833] flex items-center justify-center">
          <Landmark className="w-7 h-7 text-gray-200" />
        </div>
        <div>
          <h1 className="text-[26px] font-semibold text-white leading-tight">{stock.name}</h1>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-xl font-semibold text-white">
              {currency} {price ? price.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : 'N/A'}
            </span>
            <span
              className={`flex items-center gap-1 text-sm font-medium ${
                isPositive ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              <span className="text-[10px]">{isPositive ? 'UP' : 'DOWN'}</span>
              {Math.abs(change).toFixed(2)} ({changePercent.toFixed(2)}%)
            </span>
          </div>
          <p className="text-[11px] text-gray-500 mt-1">
            {stock.date} <span className="mx-1">|</span> {stock.marketStatus}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap justify-end pt-2">
        <button className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-gray-300 bg-[#1a1c23] border border-[#262833] rounded-md hover:bg-[#22252e]">
          <Landmark className="w-3 h-3" /> {stock.symbol} <ChevronDown className="w-3 h-3" />
        </button>
        <button className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-gray-300 bg-[#1a1c23] border border-[#262833] rounded-md hover:bg-[#22252e]">
          {stock.exchange}
        </button>
        <button className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-gray-300 bg-[#1a1c23] border border-[#262833] rounded-md hover:bg-[#22252e]">
          {stock.country} <ChevronDown className="w-3 h-3" />
        </button>

        <div className="w-px h-5 bg-[#262833] mx-1" />

        <button className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-[#1a1c23] rounded-md">
          <MessageSquare className="w-4 h-4" />
        </button>
        <button
          onClick={toggleWatchlist}
          disabled={loading}
          className={`p-1.5 rounded-md hover:bg-[#1a1c23] transition-colors ${
            isStarred ? 'text-amber-400' : 'text-gray-400 hover:text-gray-200'
          }`}
          title={isStarred ? "Remove from watchlist" : "Add to watchlist"}
        >
          <Star className={`w-4 h-4 ${isStarred ? 'fill-current' : ''}`} />
        </button>


        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-200 bg-[#1a1c23] border border-[#262833] rounded-md hover:bg-[#22252e]">
          <FileDown className="w-3.5 h-3.5" /> EXPORT TO EXCEL
        </button>
        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 rounded-md shadow-sm">
          <Plus className="w-3.5 h-3.5" /> FOLLOW
        </button>
      </div>
    </section>
  )
}

export default StockHeader
