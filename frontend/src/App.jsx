import { useEffect } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { ToastProvider } from '@/components/ui/toast'

import AppRoutes from './Routes'
import { fetchCurrentUser } from './store/authSlice'
import authService from './services/auth.service'
import './App.css'

const AuthBootstrap = ({ children }) => {
  const dispatch = useDispatch()

  useEffect(() => {
    if (authService.getToken()) {
      dispatch(fetchCurrentUser())
    } else {
      dispatch({ type: 'auth/me/rejected' })
    }
  }, [dispatch])

  return children
}

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthBootstrap>
          <AppRoutes />
        </AuthBootstrap>
      </ToastProvider>
    </BrowserRouter>
  )
}

export default App
