import { Outlet, useLocation } from 'react-router-dom'
import Navbar from '@/components/common/Navbar'
import { useEffect, useState } from 'react'
import StockToolbar from '@/components/stock/StockToolbar'
import { readPreference } from '@/components/stock/stock-format'
import '@/components/stock/stock-detail.css'
import '@/components/common/market-pages.css'

const Mainlayouts = () => {
  const { pathname } = useLocation()
  const [theme, setTheme] = useState(() => readPreference('asset-hunter-stock-theme', 'dark'))
  useEffect(() => { localStorage.setItem('asset-hunter-stock-theme', JSON.stringify(theme)) }, [theme])
  if (pathname.startsWith('/stock/')) return <Outlet context={{ theme, setTheme }} />
  if (pathname === '/feed' || pathname === '/screens') return <div className="stock-detail" data-stock-theme={theme}>
    <StockToolbar theme={theme} setTheme={setTheme} />
    <main><Outlet /></main>
  </div>
  return (
    <div className="min-h-screen bg-[#0d0e13] text-gray-200">
      <Navbar />
      <main className="px-6 py-4 mx-auto max-w-[1440px]">
        <Outlet />
      </main>
    </div>
  )
}

export default Mainlayouts
