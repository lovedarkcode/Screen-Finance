import api from './api'

const screenerService = {
  async metrics(signal) { return (await api.get('/screener/metrics', { signal })).data },
  async sectors(signal) { return (await api.get('/screener/sectors', { signal })).data },
  async search(query, market, signal) { return (await api.post('/screener/search', { query, market }, { signal, timeout: 75000 })).data },
  async execute(screen, page = 1, signal, originalQuery = null) { return (await api.post('/screener/execute', { screen, page, ...(originalQuery ? { original_query: originalQuery } : {}) }, { signal })).data },
}

export default screenerService
