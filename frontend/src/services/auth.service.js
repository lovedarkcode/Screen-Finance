import api from './api'

const TOKEN_KEY = 'access_token'

const authService = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY)
  },
  setToken(token) {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  },
  clearToken() {
    localStorage.removeItem(TOKEN_KEY)
  },

  async register({ name, email, password }) {
    const { data } = await api.post('/auth/register', { name, email, password })
    return data
  },

  async login({ email, password }) {
    const { data } = await api.post('/auth/login', { email, password })
    return data
  },

  async loginWithGoogle(credential) {
    const { data } = await api.post('/auth/google', { credential })
    return data
  },

  async me() {
    const { data } = await api.get('/auth/me')
    return data
  },

  async logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // ignore — server is stateless
    }
    this.clearToken()
  },
}

export default authService
