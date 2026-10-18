import api from './api'

const aiService = {
  async analyzeStock(symbol, signal) {
    const { data } = await api.post('/ai/analyze', { symbol }, { timeout: 360000, signal })
    return data
  },
}

export default aiService
