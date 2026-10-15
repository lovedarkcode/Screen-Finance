import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Briefcase, LogOut, Moon, Search, Star, Sun, UserRound } from 'lucide-react'
import { useDispatch, useSelector } from 'react-redux'
import { logout, selectUser } from '@/store/authSlice'
import stockService from '@/services/stock.service'
import { StockModal, PriceChange } from './StockUI'
import { money } from './stock-format'

export default function StockToolbar({ stock, theme, setTheme }) {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const user = useSelector(selectUser)
  const [accountOpen, setAccountOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState({ items: [], loading: false, error: '' })
  const [sectors, setSectors] = useState(null)
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const scroll = () => setScrolled(window.scrollY > 160)
    scroll()
    window.addEventListener('scroll', scroll, { passive: true })
    return () => window.removeEventListener('scroll', scroll)
  }, [])
  useEffect(() => {
    if (!searchOpen) return
    let live = true
    stockService.getSectors().then(value => { if (live) setSectors(value) }).catch(() => { if (live) setSectors([]) })
    return () => { live = false }
  }, [searchOpen])
  useEffect(() => {
    if (!searchOpen || query.trim().length < 2) return
    let live = true
    const timer = setTimeout(async () => {
      setSearch({ items: [], loading: true, error: '' })
      try {
        const result = await stockService.searchStocks(query.trim())
        if (live) setSearch({ items: result.items || [], loading: false, error: '' })
      } catch { if (live) setSearch({ items: [], loading: false, error: 'Search is temporarily unavailable. Please try again.' }) }
    }, 250)
    return () => { live = false; clearTimeout(timer) }
  }, [query, searchOpen])
  const select = (symbol) => {
    setSearchOpen(false)
    setQuery('')
    navigate(`/stock/${encodeURIComponent(symbol)}`)
    window.scrollTo(0, 0)
  }
  return <>
    <header className="stock-toolbar"><div className="stock-container stock-toolbar-inner">
      <Link className="stock-brand" to="/screens"><span className="stock-brand-mark"><img src="/assest-hunter.png" alt="" /></span><span>Asset Hunter</span></Link>
      <nav className="market-navigation" aria-label="Main navigation"><NavLink to="/feed">Feed</NavLink><NavLink to="/screens">Screens</NavLink></nav>
      {stock && scrolled && <div className="stock-compact-quote"><strong>{stock.baseSymbol || stock.symbol}</strong><strong>{money(stock.price)}</strong><PriceChange value={stock.changePercent} /></div>}
      <button className="stock-search-trigger" onClick={() => setSearchOpen(true)} aria-label="Search stocks and sectors"><Search size={15} /><span>Search equity stocks, sectors …</span></button>
      <div className="stock-header-actions">
        <button className="stock-icon-button stock-theme-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button>
        <button className="stock-icon-button stock-theme-button" aria-label="Account and saved lists" onClick={() => setAccountOpen(true)}><UserRound size={17} /></button>
      </div>
    </div></header>
    <StockModal open={accountOpen} onOpenChange={setAccountOpen} theme={theme} title={user?.name || 'Your Asset Hunter'} description={user?.email || 'Manage your saved stocks and investments.'}>
      <div className="market-account-links"><Link to="/watchlist" onClick={() => setAccountOpen(false)}><Star size={17} />Watchlist<ArrowRight size={15} /></Link><Link to="/portfolio" onClick={() => setAccountOpen(false)}><Briefcase size={17} />Portfolio<ArrowRight size={15} /></Link>
        {user ? <button onClick={async () => { await dispatch(logout()); setAccountOpen(false); navigate('/login', { replace: true }) }}><LogOut size={17} />Sign out</button> : <Link to="/login">Sign in<ArrowRight size={15} /></Link>}
      </div>
    </StockModal>
    <StockModal open={searchOpen} onOpenChange={setSearchOpen} theme={theme} title="Search stocks or sectors" description="Find a company by its name, symbol or sector.">
      <form className="stock-search-form" onSubmit={e => { e.preventDefault(); if (search.items[0] && query.trim().length >= 2) select(search.items[0].symbol) }}>
        <Search size={19} /><input aria-label="Search company or symbol" autoComplete="off" placeholder="Search company or symbol…" value={query} onChange={e => { setQuery(e.target.value); setSearch({ items: [], loading: e.target.value.trim().length >= 2, error: '' }) }} /><button className="stock-icon-button" aria-label="Search"><ArrowRight size={19} /></button>
      </form>
      {query.trim().length >= 2 ? <div className="stock-search-results" aria-live="polite">
        {search.loading ? <p>Searching companies…</p> : search.error ? <p role="alert">{search.error}</p> : search.items.length ? search.items.map(item => <button key={item.symbol} onClick={() => select(item.symbol)}><span><strong>{item.name}</strong><small>{item.symbol} · {item.exchange}</small></span><ArrowRight size={16} /></button>) : <p>No results found for “{query}”. Try a stock name or symbol.</p>}
      </div> : <div className="stock-sector-list"><p>{sectors === null ? 'Loading sectors…' : sectors.length ? 'Browse sectors' : 'Sector data is unavailable. Use stock search or the Screener.'}</p>{(sectors || []).map(sector => <button key={sector.id} onClick={() => { setSearchOpen(false); navigate(`/screens?sector=${encodeURIComponent(sector.id)}`) }}>{sector.name}</button>)}</div>}
      <Link className="stock-search-footer" to="/screens" onClick={() => setSearchOpen(false)}><ArrowLeft size={14} /> Back to Screener</Link>
    </StockModal>
  </>
}
