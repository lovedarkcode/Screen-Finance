import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Layers, Moon, Search, Sun } from 'lucide-react'
import stockService from '@/services/stock.service'
import { StockModal, PriceChange } from './StockUI'
import { DEFAULT_SECTIONS, SECTIONS, money } from './stock-format'

export default function StockToolbar({ stock, theme, setTheme, sections, setSections }) {
  const navigate = useNavigate()
  const [searchOpen, setSearchOpen] = useState(false)
  const [manageOpen, setManageOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState({ items: [], loading: false, error: '' })
  const [sectors, setSectors] = useState([])
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
    stockService.getSectors().then(value => { if (live) setSectors(value) }).catch(() => {})
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
      <Link className="stock-brand" to="/screens"><img src="/assest-hunter.png" alt="" /><span>Asset Hunter</span></Link>
      <span className="stock-header-divider" />
      {stock && scrolled && <div className="stock-compact-quote"><strong>{stock.baseSymbol || stock.symbol}</strong><strong>{money(stock.price)}</strong><PriceChange value={stock.changePercent} /></div>}
      <button className="stock-search-trigger" onClick={() => setSearchOpen(true)} aria-label="Search stocks and sectors"><Search size={15} /><span>Search equity stocks, sectors …</span></button>
      <div className="stock-header-actions"><button className="stock-button stock-manage" aria-label="Manage sections" onClick={() => setManageOpen(true)}><Layers size={15} /><span>Manage sections</span></button>
        <button className="stock-icon-button stock-theme-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button>
      </div>
    </div></header>
    <StockModal open={searchOpen} onOpenChange={setSearchOpen} theme={theme} title="Search stocks or sectors" description="Find a company by its name, symbol or sector.">
      <form className="stock-search-form" onSubmit={e => { e.preventDefault(); if (search.items[0] && query.trim().length >= 2) select(search.items[0].symbol) }}>
        <Search size={19} /><input aria-label="Search company or symbol" autoComplete="off" placeholder="Search company or symbol…" value={query} onChange={e => { setQuery(e.target.value); setSearch({ items: [], loading: e.target.value.trim().length >= 2, error: '' }) }} /><button className="stock-icon-button" aria-label="Search"><ArrowRight size={19} /></button>
      </form>
      {query.trim().length >= 2 ? <div className="stock-search-results" aria-live="polite">
        {search.loading ? <p>Searching companies…</p> : search.error ? <p role="alert">{search.error}</p> : search.items.length ? search.items.map(item => <button key={item.symbol} onClick={() => select(item.symbol)}><span><strong>{item.name}</strong><small>{item.symbol} · {item.exchange}</small></span><ArrowRight size={16} /></button>) : <p>No results found for “{query}”. Try a stock name or symbol.</p>}
      </div> : <div className="stock-sector-list"><p>Browse sectors</p>{sectors.map(sector => <button key={sector.id} onClick={() => { setSearchOpen(false); navigate(`/screens?sector=${encodeURIComponent(sector.id)}`) }}>{sector.name}</button>)}</div>}
      <Link className="stock-search-footer" to="/screens" onClick={() => setSearchOpen(false)}><ArrowLeft size={14} /> Back to Screener</Link>
    </StockModal>
    <StockModal open={manageOpen} onOpenChange={setManageOpen} theme={theme} title="Manage Sections" description="Toggle which sections appear on this page" drawer>
      <div className="stock-section-list">{SECTIONS.map(([id, title, description]) => <button key={id} role="switch" aria-checked={sections[id]} onClick={() => setSections(value => ({ ...value, [id]: !value[id] }))}>
        <span className="stock-section-icon"><Layers size={15} /></span><span><strong>{title}</strong><small>{description}</small></span><span className={`stock-switch ${sections[id] ? 'is-checked' : ''}`} />
      </button>)}</div><div className="stock-drawer-footer"><button className="stock-button" onClick={() => setSections({ ...DEFAULT_SECTIONS })}>Reset to Default</button><button className="stock-button stock-primary" onClick={() => setManageOpen(false)}>Done</button></div>
    </StockModal>
  </>
}
