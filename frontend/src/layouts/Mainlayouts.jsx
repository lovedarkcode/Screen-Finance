import { Outlet, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import StockToolbar from '@/components/stock/StockToolbar'
import { readPreference } from '@/components/stock/stock-format'
import '@/components/stock/stock-detail.css'
import '@/components/common/market-pages.css'

const Mainlayouts = () => {
  const { pathname } = useLocation()
  const [theme, setTheme] = useState(() => readPreference('asset-hunter-stock-theme', 'dark'))
  useEffect(() => {
    localStorage.setItem('asset-hunter-stock-theme', JSON.stringify(theme))
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.classList.toggle('light', theme === 'light')
  }, [theme])
  if (pathname.startsWith('/stock/')) return <Outlet context={{ theme, setTheme }} />
  return (
    <div className="stock-detail" data-stock-theme={theme}>
      <StockToolbar theme={theme} setTheme={setTheme} />
      <main>
        <Outlet context={{ theme, setTheme }} />
      </main>
    </div>
  )
}

export default Mainlayouts
