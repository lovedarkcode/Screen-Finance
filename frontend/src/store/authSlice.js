import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import authService from '../services/auth.service'

const extractMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return error?.message || fallback
}

export const registerUser = createAsyncThunk(
  'auth/register',
  async (payload, { rejectWithValue }) => {
    try {
      const data = await authService.register(payload)
      authService.setToken(data.access_token)
      return data
    } catch (err) {
      return rejectWithValue(extractMessage(err, 'Registration failed'))
    }
  },
)

export const loginUser = createAsyncThunk(
  'auth/login',
  async (payload, { rejectWithValue }) => {
    try {
      const data = await authService.login(payload)
      authService.setToken(data.access_token)
      return data
    } catch (err) {
      return rejectWithValue(extractMessage(err, 'Login failed'))
    }
  },
)

export const googleLogin = createAsyncThunk(
  'auth/google',
  async (credential, { rejectWithValue }) => {
    try {
      const data = await authService.loginWithGoogle(credential)
      authService.setToken(data.access_token)
      return data
    } catch (err) {
      return rejectWithValue(extractMessage(err, 'Google sign-in failed'))
    }
  },
)

export const fetchCurrentUser = createAsyncThunk(
  'auth/me',
  async (_, { rejectWithValue }) => {
    try {
      return await authService.me()
    } catch (err) {
      authService.clearToken()
      return rejectWithValue(extractMessage(err, 'Session expired'))
    }
  },
)

export const logout = createAsyncThunk('auth/logout', async () => {
  await authService.logout()
})

const initialState = {
  user: null,
  token: authService.getToken(),
  status: 'idle',
  error: null,
  bootstrapped: false,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearAuthError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    const handleSuccess = (state, { payload }) => {
      state.user = payload.user
      state.token = payload.access_token
      state.status = 'succeeded'
      state.error = null
      state.bootstrapped = true
    }
    const handleFailure = (state, { payload, error }) => {
      state.status = 'failed'
      state.error = payload || error?.message || 'Something went wrong'
    }
    const handlePending = (state) => {
      state.status = 'loading'
      state.error = null
    }

    builder
      .addCase(registerUser.pending, handlePending)
      .addCase(registerUser.fulfilled, handleSuccess)
      .addCase(registerUser.rejected, handleFailure)

      .addCase(loginUser.pending, handlePending)
      .addCase(loginUser.fulfilled, handleSuccess)
      .addCase(loginUser.rejected, handleFailure)

      .addCase(googleLogin.pending, handlePending)
      .addCase(googleLogin.fulfilled, handleSuccess)
      .addCase(googleLogin.rejected, handleFailure)

      .addCase(fetchCurrentUser.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(fetchCurrentUser.fulfilled, (state, { payload }) => {
        state.user = payload
        state.status = 'succeeded'
        state.bootstrapped = true
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        state.user = null
        state.token = null
        state.status = 'idle'
        state.bootstrapped = true
      })

      .addCase(logout.fulfilled, (state) => {
        state.user = null
        state.token = null
        state.status = 'idle'
        state.error = null
      })
  },
})

export const { clearAuthError } = authSlice.actions
export default authSlice.reducer

export const selectAuth = (state) => state.auth
export const selectUser = (state) => state.auth.user
export const selectIsAuthenticated = (state) => Boolean(state.auth.user)
export const selectAuthBootstrapped = (state) => state.auth.bootstrapped
