import { useEffect } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { Toaster } from 'react-hot-toast'

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
      <AuthBootstrap>
        <AppRoutes />
      </AuthBootstrap>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#15171c', color: '#e6e7eb', border: '1px solid #2a2d36' },
        }}
      />
    </BrowserRouter>
  )
}

export default App
