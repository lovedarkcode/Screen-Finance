import api from './api'

const stockService = {
  searchStocks: async (query, limit = 8) => {
    const response = await api.get('/stocks', { params: { q: query, limit } })
    return response.data
  },
  getStock: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}`)
    return response.data
  },
  getMetrics: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/metrics`)
    return response.data
  },
  getChart: async (symbol, range = '1Yr') => {
    const response = await api.get(`/stocks/${symbol}/chart`, { params: { range } })
    return response.data
  },
  getQuarters: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/quarters`)
    return response.data
  },
  getProfitLoss: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/profit-loss`)
    return response.data
  },
  getBalanceSheet: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/balance-sheet`)
    return response.data
  },
  getCashFlow: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/cash-flow`)
    return response.data
  },
  getRatios: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/ratios`)
    return response.data
  },
  getPeers: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/peers`)
    return response.data
  },
  getSummary: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/summary`)
    return response.data
  },
  getAbout: async (symbol) => {
    const response = await api.get(`/stocks/${symbol}/about`)
    return response.data
  },
}

export default stockService
