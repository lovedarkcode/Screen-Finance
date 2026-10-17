import { money } from '@/components/stock/stock-format'
import { SearchInput } from '@/components/ui/search-input'
import { Button } from '@/components/ui/button'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import stockService from '@/services/stock.service'

const SearchBar = () => {
  const navigate = useNavigate()
  const wrapperRef = useRef(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const onClick = (event) => {
      if (!wrapperRef.current?.contains(event.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  useEffect(() => {
    const trimmed = query.trim()
    if (trimmed.length < 1) return
    let live = true
    const timeout = window.setTimeout(async () => {
      setLoading(true)
      setError('')
      try {
        const data = await stockService.searchStocks(trimmed)
        if (!live) return
        setResults(data.items || [])
        setOpen(true)
      } catch {
        if (!live) return
        setResults([])
        setError('Indian and US stock search is unavailable.')
        setOpen(true)
      } finally {
        if (live) setLoading(false)
      }
    }, 250)

    return () => { live = false; window.clearTimeout(timeout) }
  }, [query])

  const selectStock = (stock) => {
    setQuery('')
    setOpen(false)
    navigate(`/stock/${stock.symbol}`)
  }

  return (
    <div ref={wrapperRef} className="relative flex-1 max-w-xl">
      <SearchInput
        aria-label="Search Indian and US company or symbol"
        wrapperClassName="w-full sm:w-full"
        value={query}
        onChange={(event) => { setQuery(event.target.value); setResults([]); setError(''); setOpen(false); setLoading(false) }}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder="Search Indian and US company or symbol..."
        className="pr-10"
      />
      <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-gray-500 border border-[#33363f] rounded px-1.5 py-0.5">
        /
      </kbd>

      {open && (
        <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-md border border-[#262833] bg-[#14161c] shadow-xl">
          {loading && (
            <div className="px-3 py-2 text-[12px] text-gray-500">Searching Indian and US exchanges...</div>
          )}
          {!loading && error && (
            <div className="px-3 py-2 text-[12px] text-red-300">{error}</div>
          )}
          {!loading && !error && results.length === 0 && (
            <div className="px-3 py-2 text-[12px] text-gray-500">No listed company found</div>
          )}
          {!loading && !error && results.map((stock) => (
            <Button variant="ghost" size="sm"
              key={stock.symbol}
              type="button"
              onClick={() => selectStock(stock)}
              className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-[#1a1c23]"
            >
              <span className="min-w-0">
                <span className="block truncate text-[13px] font-medium text-gray-100">
                  {stock.name}
                </span>
                <span className="block text-[11px] text-gray-500">
                  {stock.symbol} | {stock.exchange} | {stock.sector}
                </span>
              </span>
              {stock.price && (
                <span className="shrink-0 text-[12px] font-semibold text-gray-200">
                  {money(stock.price, stock.currency)}
                </span>
              )}
            </Button>
          ))}
        </div>
      )}
    </div>
  )
}

export default SearchBar
