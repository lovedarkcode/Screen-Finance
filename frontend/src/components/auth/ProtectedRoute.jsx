import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { selectAuthBootstrapped, selectIsAuthenticated } from '@/store/authSlice'

const ProtectedRoute = () => {
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const bootstrapped = useSelector(selectAuthBootstrapped)
  const location = useLocation()

  if (!bootstrapped) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0d0e13] text-gray-400 text-sm">
        Loading…
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}

export default ProtectedRoute
