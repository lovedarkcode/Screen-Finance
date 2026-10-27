// Isolated browser fixtures; no user account, database or NVIDIA calls are modified.
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
const fs = require('node:fs/promises')
const path = require('node:path')
const baseURL = process.env.APP_URL || 'http://127.0.0.1:5175'
const output = process.env.UI_VERIFY_OUTPUT_DIR || __dirname
const fields = [
  ['market_cap', 'Market capitalization', 'currency', ['snapshot']], ['pe', 'P/E', 'times', ['ttm']], ['roe', 'ROE', 'percent', ['annual', 'ttm']], ['revenue_growth', 'Revenue growth', 'percent', ['annual']], ['debt_to_equity', 'Debt/equity', 'times', ['snapshot']], ['net_profit_margin', 'Net profit margin', 'percent', ['annual', 'ttm']], ['net_income', 'Net income', 'currency', ['annual', 'ttm']],
].map(([field, label, unit, periods]) => ({ field, label, unit, periods, default_period: periods[0], definition: 'Explicit browser fixture; no real financial claim.' }))
const definition = () => ({ market: 'US', exchange: null, sector: 'Technology', industry: null, filters: [{ field: 'roe', operator: 'gt', value: 20, period: 'annual', period_end: null, currency: null }, { field: 'debt_to_equity', operator: 'lt', value: .5, period: 'snapshot', period_end: null, currency: null }], sort_by: 'market_cap', sort_period: 'snapshot', sort_desc: true, limit: 25 })
const values = { roe: 30, debt_to_equity: .2, market_cap: 20e9, pe: 15, revenue_growth: 25, net_profit_margin: 20, net_income: 1e9 }
function response(screen, page = 1) {
  const matches = screen.filters.every(filter => ({ gt: () => values[filter.field] > filter.value, gte: () => values[filter.field] >= filter.value, lt: () => values[filter.field] < filter.value, lte: () => values[filter.field] <= filter.value, eq: () => values[filter.field] === filter.value, between: () => values[filter.field] >= filter.value[0] && values[filter.field] <= filter.value[1] })[filter.operator]())
  const total = matches ? screen.market === 'IN' ? 2 : 30 : 0
  const symbols = Array.from({ length: total }, (_, index) => screen.market === 'IN' ? index ? 'MTARTECH.NS' : 'RELIANCE.NS' : `TEST${index + 1}`)
  return { status: 'success', original_query: '', parsed_filters: screen, total_count: total, page, page_size: screen.limit, universe_count: screen.market === 'IN' ? 10 : 40, data_as_of: '2026-10-17T12:00:00Z', warnings: ['Explicit isolated browser dataset; not exchange-wide results.'], execution_ms: 12, stocks: symbols.slice((page - 1) * screen.limit, page * screen.limit).map(symbol => ({ symbol, name: `Fixture Company ${symbol}`, exchange: screen.market === 'IN' ? 'NSE' : 'NASDAQ', sector: 'Technology', currency: screen.market === 'IN' ? 'INR' : 'USD', metrics: Object.fromEntries(fields.flatMap(field => field.periods.map(basis => [`${field.field}:${basis}`, { value: values[field.field], unit: field.unit, currency: screen.market === 'IN' ? 'INR' : 'USD', period: basis === 'annual' ? 'FY ending 2025-12-31' : 'Latest provider snapshot', updated_at: '2026-10-17T12:00:00Z', validation_status: 'fixture', source: 'Browser fixture' }])))})) }
}

async function main() {
  await fs.mkdir(output, { recursive: true })
  const browser = await chromium.launch({ headless: true })
  const searches = [], executions = [], errors = []
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
    await context.addInitScript(() => localStorage.setItem('access_token', 'isolated-screener-check'))
    let mode = 'success'
    await context.route('**/api/v1/**', async route => {
      const endpoint = new URL(route.request().url()).pathname.replace('/api/v1', '')
      const ok = json => route.fulfill({ json })
      if (endpoint === '/auth/me') return ok({ id: 1, name: 'Browser fixture', email: 'fixture@example.test' })
      if (endpoint === '/screener/metrics') return ok({ metrics: fields })
      if (endpoint === '/screener/search') {
        const body = route.request().postDataJSON(); searches.push(body)
        if (mode === 'clarification') return ok({ status: 'clarification', clarification: 'Please specify a numeric threshold.' })
        if (mode === 'error') return route.fulfill({ status: 503, json: { detail: 'Please retry in a moment.' } })
        return ok({ ...response({ ...definition(), market: body.market }), original_query: body.query, eligible_count: body.market === 'IN' ? 8 : 35 })
      }
      if (endpoint === '/screener/execute') {
        const body = route.request().postDataJSON(); executions.push(body)
        return ok({ ...response(body.screen, body.page), eligible_count: 35, original_query: body.original_query })
      }
      if (endpoint === '/stocks/sectors') return ok([])
      if (endpoint.endsWith('/chart')) return ok([{ date: '2026-10-15T20:00:00Z', price: 100 }, { date: '2026-10-16T20:00:00Z', price: 101 }])
      if (endpoint.endsWith('/overview')) return ok({ metrics: [], priceRange: {}, about: {}, returns: [] })
      if (/\/(peers|shareholding|pe-history)$/.test(endpoint)) return ok([])
      if (endpoint.endsWith('/quarters')) return ok({ chart: [], rows: [], columns: [] })
      if (/^\/stocks\/[^/]+$/.test(endpoint)) return ok({ symbol: 'TEST', name: 'Fixture company', price: 100, change: 1, changePercent: 1, currency: 'USD', exchange: 'NASDAQ' })
      return ok({ items: [] })
    })
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    await page.goto(`${baseURL}/feed?screener=ai`)
    const bot = page.getByRole('region', { name: 'AI stock screener', exact: true })
    const input = bot.getByLabel('What would you like to screen?')
    const market = bot.getByLabel('Market', { exact: true })
    await input.waitFor()
    assert.equal(await market.inputValue(), 'IN')
    assert.equal(await bot.getByRole('combobox').count(), 1)
    assert.equal(await bot.getByRole('button', { name: 'Edit financial filters' }).count(), 0)
    assert.equal(searches.length, 0)
    await market.selectOption('US')
    await input.fill('Show companies with ROE above 20% and debt-to-equity below 0.5.')
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByRole('heading', { name: '30 matching listings' }).waitFor()
    assert.equal(searches.at(-1).market, 'US')
    assert.match(await bot.getByLabel('Interpreted request').innerText(), /ROE/)
    await bot.getByRole('button', { name: 'Next', exact: true }).click()
    await bot.getByText('Page 2 of 2', { exact: false }).waitFor()
    assert.equal(executions.at(-1).page, 2)
    assert.equal(executions.at(-1).screen.market, 'US')
    assert.equal(searches.length, 1)
    await bot.getByRole('button', { name: 'Market capitalization', exact: true }).click()
    await bot.getByText('Page 1 of 2', { exact: false }).waitFor()
    assert.equal(executions.at(-1).screen.sort_desc, false)
    await market.selectOption('IN')
    assert.equal(await bot.getByLabel('Stock screening results').count(), 0)
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByRole('heading', { name: '2 matching listings' }).waitFor()
    assert.equal(searches.at(-1).market, 'IN')
    await bot.screenshot({ path: path.join(output, 'discovery-desktop.png') })
    await page.setViewportSize({ width: 390, height: 844 })
    await bot.screenshot({ path: path.join(output, 'discovery-mobile.png') })
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
    mode = 'clarification'
    await input.fill('Show low debt companies')
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByText('Please specify a numeric threshold.').waitFor()
    mode = 'error'
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByText('Please retry in a moment.').waitFor()
    assert.deepEqual(errors, [])
    console.log('Passed: market selection, prompt requests, read-only conditions, pagination, sorting, result reset, desktop/mobile, clarification and errors.')
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
