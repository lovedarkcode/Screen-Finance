import { Routes, Route, Navigate } from 'react-router-dom'
import Mainlayouts from './layouts/Mainlayouts'
import StockPage from './pages/Stock/StockPage'
import HomePage from './pages/Home/HomePage'
import ScreenerPage from './pages/Screener/ScreenerPage'
import PortfolioPage from './pages/Portfolio/PortfolioPage'
import Watchlist from './pages/Portfolio/Watchlist'
import AIChat from './pages/AI/AIChat'

const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<Mainlayouts />}>
        <Route path="/" element={<Navigate to="/stock/AAPL" replace />} />
        <Route path="/feed" element={<HomePage />} />
        <Route path="/stock/:symbol" element={<StockPage />} />
        <Route path="/screens" element={<ScreenerPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/ai" element={<AIChat />} />
      </Route>
    </Routes>
  )
}

export default AppRoutes
