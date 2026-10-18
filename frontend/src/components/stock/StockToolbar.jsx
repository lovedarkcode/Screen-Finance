import { Button } from '@/components/ui/button'
import { IconButton } from '@/components/ui/icon-button'
import { SearchInput } from '@/components/ui/search-input'
import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Briefcase, LogOut, Moon, Search, Sparkles, Star, Sun, UserRound } from 'lucide-react'
import { useDispatch, useSelector } from 'react-redux'
import { logout, selectUser } from '@/store/authSlice'
import stockService from '@/services/stock.service'
import { StockModal, PriceChange } from './StockUI'
import { money } from './stock-format'

export default function StockToolbar({ stock, theme, setTheme }) {
  const navigate = useNavigate()
  const { pathname, search: locationSearch } = useLocation()
  const screenerOpen = pathname === '/feed' && new URLSearchParams(locationSearch).get('screener') === 'ai'
  const dispatch = useDispatch()
  const user = useSelector(selectUser)
  const [accountOpen, setAccountOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const searchInput = useRef(null)
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
    if (!searchOpen || query.trim().length < 1) return
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
      <nav className="market-navigation" aria-label="Main navigation"><NavLink to="/feed">Feed</NavLink><NavLink to="/screens">Screens</NavLink><Button variant={screenerOpen ? 'muted' : 'ghost'} size="sm" aria-pressed={screenerOpen} onClick={() => navigate(screenerOpen ? '/feed' : '/feed?screener=ai')}><Sparkles size={14} />AI Screener</Button></nav>
      {stock && scrolled && <div className="stock-compact-quote"><strong>{stock.baseSymbol || stock.symbol}</strong><strong>{money(stock.price, stock.currency)}</strong><PriceChange value={stock.changePercent} /></div>}
      <Button variant="outline" size="sm" className="stock-search-trigger" onClick={() => setSearchOpen(true)} aria-label="Search stocks and sectors"><Search size={15} /><span>Search Indian &amp; US stocks …</span></Button>
      <div className="stock-header-actions">
        <IconButton variant="ghost" className="stock-icon-button stock-theme-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</IconButton>
        <IconButton variant="ghost" className="stock-icon-button stock-theme-button" aria-label="Account and saved lists" onClick={() => setAccountOpen(true)}><UserRound size={17} /></IconButton>
      </div>
    </div></header>
    <StockModal open={accountOpen} onOpenChange={setAccountOpen} theme={theme} title={user?.name || 'Your Asset Hunter'} description={user?.email || 'Manage your saved stocks and investments.'}>
      <div className="market-account-links"><Link to="/watchlist" onClick={() => setAccountOpen(false)}><Star size={17} />Watchlist<ArrowRight size={15} /></Link><Link to="/portfolio" onClick={() => setAccountOpen(false)}><Briefcase size={17} />Portfolio<ArrowRight size={15} /></Link>
        {user ? <Button variant="ghost" size="sm" onClick={async () => { await dispatch(logout()); setAccountOpen(false); navigate('/login', { replace: true }) }}><LogOut size={17} />Sign out</Button> : <Link to="/login">Sign in<ArrowRight size={15} /></Link>}
      </div>
    </StockModal>
    <StockModal open={searchOpen} onOpenChange={setSearchOpen} theme={theme} title="Search stocks or sectors" description="Find NSE/BSE and US companies by name or symbol, or browse Indian sectors." initialFocus={searchInput}>
      <form className="stock-search-form" onSubmit={e => { e.preventDefault(); if (search.items[0] && query.trim().length >= 1) select(search.items[0].symbol) }}>
        <SearchInput ref={searchInput} wrapperClassName="flex-1 sm:w-auto" aria-label="Search company or symbol" autoComplete="off" placeholder="Try Apple, AAPL, or TCS.NS…" value={query} onChange={e => { setQuery(e.target.value); setSearch({ items: [], loading: e.target.value.trim().length >= 1, error: '' }) }} /><IconButton type="submit" variant="ghost" className="stock-icon-button" aria-label="Search"><ArrowRight size={19} /></IconButton>
      </form>
      {query.trim().length >= 1 ? <div className="stock-search-results" aria-live="polite">
        {search.loading ? <p>Searching companies…</p> : search.error ? <p role="alert">{search.error}</p> : search.items.length ? search.items.map(item => <Button variant="ghost" size="sm" key={item.symbol} onClick={() => select(item.symbol)}><span><strong>{item.name}</strong><small>{item.symbol} · {item.exchange} · {item.currency}</small></span><ArrowRight size={16} /></Button>) : <p>No results found for “{query}”. Try a stock name or symbol.</p>}
      </div> : <div className="stock-sector-list"><p>{sectors === null ? 'Loading sectors…' : sectors.length ? 'Browse sectors' : 'Sector data is unavailable. Use stock search or the Screener.'}</p>{(sectors || []).map(sector => <Button variant="ghost" size="sm" key={sector.id} onClick={() => { setSearchOpen(false); navigate(`/screens?sector=${encodeURIComponent(sector.id)}`) }}>{sector.name}</Button>)}</div>}
      <Link className="stock-search-footer" to="/screens" onClick={() => setSearchOpen(false)}><ArrowLeft size={14} /> Back to Screener</Link>
    </StockModal>
  </>
}
