import { Routes, Route, Navigate } from 'react-router-dom'
import Mainlayouts from './layouts/Mainlayouts'
import Authlayout from './layouts/Authlayout'
import ProtectedRoute from './components/auth/ProtectedRoute'

import StockPage from './pages/Stock/StockPage'
import HomePage from './pages/Home/HomePage'
import ScreenerPage from './pages/Screener/ScreenerPage'
import QuarterlyResultsPage from './pages/Results/QuarterlyResultsPage'
import LatestFilingsPage from './pages/Results/LatestFilingsPage'
import PortfolioPage from './pages/Portfolio/PortfolioPage'
import Watchlist from './pages/Portfolio/Watchlist'
import AIChat from './pages/AI/AIChat'

import Login from './pages/Auth/Login'
import Register from './pages/Auth/Register'
import ForgotPassword from './pages/Auth/ForgotPassword'

const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<Authlayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<Mainlayouts />}>
          <Route path="/" element={<Navigate to="/feed" replace />} />
          <Route path="/feed" element={<HomePage />} />
          <Route path="/stock/:symbol" element={<StockPage />} />
          <Route path="/screens" element={<ScreenerPage />} />
          <Route path="/results" element={<LatestFilingsPage />} />
          <Route path="/results/imported" element={<QuarterlyResultsPage />} />
          <Route path="/results/latest" element={<LatestFilingsPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/ai" element={<AIChat />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes
