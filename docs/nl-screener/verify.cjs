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
  const passed = [], errors = [], searches = [], executions = []
  const check = (label, condition) => { assert.ok(condition, label); passed.push(label) }
  let mode = 'pending', resolvePending
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
    await context.addInitScript(() => localStorage.setItem('access_token', 'isolated-screener-check'))
    await context.route('**/api/v1/**', async route => {
      const endpoint = decodeURIComponent(new URL(route.request().url()).pathname.replace('/api/v1', ''))
      const ok = json => route.fulfill({ json })
      if (endpoint === '/auth/me') return ok({ id: 1, name: 'Browser fixture', email: 'fixture@example.test' })
      if (endpoint === '/screener/metrics') return ok({ metrics: fields, version: 'fixture' })
      if (endpoint === '/screener/sectors') return ok({ sectors: [{ market: 'US', name: 'Technology', count: 40 }, { market: 'IN', name: 'Technology', count: 10 }] })
      if (endpoint === '/screener/search') {
        const request = route.request().postDataJSON(); searches.push(request)
        if (mode === 'pending') return new Promise(resolve => { resolvePending = async () => { await ok({ ...response(definition()), original_query: request.query }); resolve() } })
        if (mode === 'clarify') return ok({ status: 'clarification', clarification: 'Please specify the numeric threshold for low debt.', stocks: [], warnings: [] })
        if (mode === 'error') return route.fulfill({ status: 503, json: { detail: 'NVIDIA could not interpret the screen right now.' } })
        if (request.query.includes('NSE or BSE')) return ok({ ...response({ ...definition(), market: 'IN', sector: null, exchanges: ['NSE', 'BSE'], limit: 20 }), original_query: request.query })
        if (request.query.startsWith('Show Indian')) return ok({ ...response({ ...definition(), market: 'IN', sector: null, filters: [{ field: 'revenue_growth', operator: 'gt', value: 5, period: 'annual', period_end: null, currency: null }, { field: 'pe', operator: 'lt', value: 25, period: 'ttm', period_end: null, currency: null }] }), original_query: request.query })
        return ok({ ...response(definition()), original_query: request.query })
      }
      if (endpoint === '/screener/execute') {
        const body = route.request().postDataJSON(); executions.push(body)
        const data = response(body.screen, body.page)
        if (body.screen.market === null && data.stocks.length) data.stocks[0].metrics['market_cap:snapshot'].currency = null
        if (mode === 'diagnostic_empty') Object.assign(data, { stocks: [], total_count: 0, empty_reason: 'missing_metrics', explanation: 'No companies match every condition: required metric values are missing or unverified.' })
        return ok({ ...data, original_query: body.original_query || null })
      }
      if (endpoint === '/watchlist') return ok({ items: [] })
      if (endpoint === '/stocks/sectors') return ok([])
      if (endpoint === '/news') return ok({ items: [] })
      if (endpoint.endsWith('/chart')) return ok([{ date: '2026-10-15T20:00:00Z', price: 100 }, { date: '2026-10-16T20:00:00Z', price: 101 }])
      if (endpoint.endsWith('/overview')) return ok({ metrics: [], priceRange: {}, about: {}, returns: [] })
      if (/\/(peers|shareholding)$/.test(endpoint)) return ok([])
      if (endpoint.endsWith('/quarters')) return ok({ chart: [], rows: [], columns: [] })
      if (/^\/stocks\/[^/]+$/.test(endpoint)) {
        const symbol = endpoint.split('/')[2]
        return ok({ symbol, name: `Fixture Company ${symbol}`, price: 100, change: 1, changePercent: 1, currency: symbol.endsWith('.NS') ? 'INR' : 'USD', exchange: symbol.endsWith('.NS') ? 'NSE' : 'NASDAQ', date: '2026-10-16T20:00:00Z' })
      }
      return ok({ items: [] })
    })
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    const go = route => page.goto(`${baseURL}${route}`, { waitUntil: 'networkidle' })
    await go('/feed')
    const bot = page.getByRole('region', { name: 'AI stock screener', exact: true })
    const input = bot.getByLabel('What would you like to screen?')
    const launcher = page.getByRole('button', { name: 'AI Screener', exact: true })
    check('Landing feed hides the screener until enabled', await bot.count() === 0 && await launcher.getAttribute('aria-pressed') === 'false')
    await launcher.click()
    await input.waitFor()
    check('Header button opens and focuses the feed screener', page.url().endsWith('/feed?screener=ai') && await input.evaluate(element => element === document.activeElement) && await launcher.getAttribute('aria-pressed') === 'true')
    await launcher.click()
    await bot.waitFor({ state: 'hidden' })
    check('Header button can close the screener', await bot.count() === 0)
    await page.goBack({ waitUntil: 'networkidle' })
    await input.waitFor()
    check('Browser Back restores the open screener', await launcher.getAttribute('aria-pressed') === 'true')
    check('Bot is integrated into the landing feed', await bot.count() === 1 && await page.getByRole('heading', { name: 'Your market, at a glance' }).count() === 1)
    check('Feed does not show the stock-only analysis launcher', await page.getByRole('button', { name: 'Analyze with AI', exact: true }).count() === 0)
    check('No LLM call happens on page load', searches.length === 0)
    await bot.getByRole('button', { name: 'US quality & debt', exact: true }).click()
    check('Example prompts populate the natural language input', (await input.inputValue()).includes('ROE above 20%'))
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.locator('.nl-status').waitFor()
    check('Loading state is visible and duplicate submission is disabled', await bot.getByRole('button', { name: 'Find stocks', exact: true }).isDisabled())
    await resolvePending()
    await bot.getByRole('table', { name: 'Matching stocks' }).waitFor()
    check('Only query text is sent to the AI search endpoint', Object.keys(searches[0]).join() === 'query')
    check('Extracted conditions are editable', await bot.getByLabel('Metric 1', { exact: true }).inputValue() === 'roe' && await bot.getByLabel('Threshold 1', { exact: true }).inputValue() === '20')
    check('Results include financial values and reporting periods', (await bot.getByRole('table').innerText()).includes('30.00%') && (await bot.getByRole('table').innerText()).includes('FY ending 2025-12-31'))
    await bot.getByRole('button', { name: 'Next', exact: true }).click()
    await bot.getByText(/Page 2 of 2/).waitFor()
    check('Pagination executes structured filters without another LLM call', searches.length === 1 && executions.at(-1).page === 2)
    check('Edited execution retains the submitted source prompt', executions.at(-1).original_query === searches[0].query)
    await bot.getByRole('button', { name: 'ROE', exact: true }).click()
    await bot.getByText(/Page 1 of 2/).waitFor()
    check('Sorting is server-side and skips AI interpretation', executions.at(-1).screen.sort_by === 'roe' && searches.length === 1)
    await bot.getByLabel('Threshold 1', { exact: true }).fill('99')
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByRole('heading', { name: 'No matching stocks found' }).waitFor()
    check('Edited threshold produces a true empty state', executions.at(-1).screen.filters[0].value === 99 && searches.length === 1)
    check('Empty state explains coverage and shows applied filters', (await bot.locator('.nl-empty').innerText()).includes('40 imported US listings') && (await bot.getByLabel('Applied screening filters').innerText()).includes('ROE > 99%') && await bot.getByRole('table').count() === 0)
    check('Empty state preserves the source prompt', (await bot.locator('.nl-empty').innerText()).includes(searches[0].query))
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 })
      await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth)
      check(`Applied filters fit an empty state at ${width}px`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      await bot.locator('.nl-empty').screenshot({ path: path.join(output, `empty-${width}.png`) })
    }
    await bot.getByRole('button', { name: 'Remove filter 1', exact: true }).click()
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByRole('table').waitFor()
    check('Removing a filter reruns without an LLM call', executions.at(-1).screen.filters.length === 1 && searches.length === 1)
    await bot.getByLabel('Market', { exact: true }).selectOption('IN')
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByRole('link', { name: 'Fixture Company RELIANCE.NS RELIANCE.NS · NSE' }).waitFor()
    check('Indian results retain INR formatting and canonical ticker', (await bot.getByRole('table').innerText()).includes('Cr') && await bot.getByRole('link', { name: 'Fixture Company RELIANCE.NS RELIANCE.NS · NSE' }).getAttribute('href') === '/stock/RELIANCE.NS')
    await bot.getByLabel('Sector', { exact: true }).fill('Energy')
    const executeCount = executions.length
    await bot.getByRole('button', { name: 'Indian growth & value', exact: true }).click()
    check('A new example clears the previous sector editor and results', await bot.getByLabel('Sector', { exact: true }).count() === 0 && await bot.getByRole('table').count() === 0)
    mode = 'ready'
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByRole('table').waitFor()
    check('Indian example runs a fresh AI search without stale Energy restriction', (await input.inputValue()).includes('above 5%') && await bot.getByLabel('Market', { exact: true }).inputValue() === 'IN' && await bot.getByLabel('Sector', { exact: true }).inputValue() === '' && executions.length === executeCount && Object.keys(searches.at(-1)).join() === 'query')
    check('New Indian screen shows its own revenue growth and PE filters', await bot.getByLabel('Metric 1', { exact: true }).inputValue() === 'revenue_growth' && await bot.getByLabel('Threshold 1', { exact: true }).inputValue() === '5' && await bot.getByLabel('Metric 2', { exact: true }).inputValue() === 'pe')
    await bot.getByLabel('Sector', { exact: true }).fill('Energy')
    await bot.getByRole('button', { name: 'Indian growth & value', exact: true }).click()
    check('Selecting the same example again also clears sector edits', await bot.getByLabel('Sector', { exact: true }).count() === 0 && await bot.getByRole('table').count() === 0)
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByRole('table').waitFor()
    await input.fill('Find Indian companies on NSE or BSE with ROE above 20% and debt-to-equity below 0.5. Show the top 20.')
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByRole('table').waitFor()
    check('Exchange alternatives and custom result limit are visible', await bot.getByLabel('Exchange', { exact: true }).inputValue() === '__selected' && await bot.getByLabel('Rows per page', { exact: true }).inputValue() === '20')
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByRole('table').waitFor()
    check('Structured execution preserves both exchanges and top 20', executions.at(-1).screen.exchanges.join(',') === 'NSE,BSE' && executions.at(-1).screen.limit === 20)
    await bot.getByLabel('Exchange', { exact: true }).selectOption('NSE')
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByRole('table').waitFor()
    check('Selecting one exchange clears previous alternatives', executions.at(-1).screen.exchange === 'NSE' && executions.at(-1).screen.exchanges.length === 0)
    for (const theme of ['dark', 'light']) {
      if (await page.locator('.stock-detail').first().getAttribute('data-stock-theme') !== theme) await page.getByRole('button', { name: `Switch to ${theme} mode` }).click()
      for (const width of [1440, 390]) {
        await page.setViewportSize({ width, height: 1000 })
        await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth)
        check(`Feed screener fits ${width}px in ${theme} mode`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
        await bot.screenshot({ path: path.join(output, `feed-${theme}-${width}.png`) })
      }
    }
    await bot.getByRole('link', { name: 'Fixture Company RELIANCE.NS RELIANCE.NS · NSE' }).click()
    await page.getByRole('heading', { name: 'Fixture Company RELIANCE.NS', exact: true }).waitFor()
    check('Company selection opens the existing stock analysis route', page.url().endsWith('/stock/RELIANCE.NS') && await page.getByRole('button', { name: 'Analyze with AI', exact: true }).count() === 1)
    check('Feed bot is not duplicated on stock routes', await page.getByRole('region', { name: 'AI stock screener', exact: true }).count() === 0)
    await launcher.click()
    await input.waitFor()
    check('Stock-page header opens the screener on the landing feed', page.url().endsWith('/feed?screener=ai') && await bot.count() === 1)
    mode = 'clarify'
    await input.fill('Find US companies with low debt')
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByText('Please specify the numeric threshold for low debt.').waitFor()
    check('Ambiguity asks for clarification instead of inventing a threshold', await bot.getByRole('table').count() === 0)
    mode = 'error'
    await input.fill('Find US companies with ROE above 20%')
    await bot.getByRole('button', { name: 'Find stocks', exact: true }).click()
    await bot.getByRole('alert').waitFor()
    check('Provider errors expose a usable filter-editor action', (await bot.getByRole('alert').innerText()).includes('NVIDIA could not interpret'))
    await bot.getByRole('button', { name: 'Use financial filters', exact: true }).click()
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByRole('table').waitFor()
    check('Manual screening remains usable after a provider failure', executions.at(-1).screen.market === 'US')
    await bot.getByLabel('Market', { exact: true }).selectOption('')
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByText(/currency unavailable/).waitFor()
    check('All-market execution sends null market and retains companies with unknown currency', executions.at(-1).screen.market === null && (await bot.locator('.nl-results-heading').innerText()).includes('All markets'))
    check('Unknown currency displays a number without inventing a currency or crashing', (await bot.getByRole('table').innerText()).includes('(currency unavailable)'))
    await bot.getByLabel('Screening date (optional)', { exact: true }).fill('2025-03-01')
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByRole('table').waitFor()
    check('Historical screening date is sent independently of fiscal dates', executions.at(-1).screen.as_of === '2025-03-01' && executions.at(-1).screen.filters.length === 0)
    mode = 'diagnostic_empty'
    await bot.getByRole('button', { name: 'Apply filters', exact: true }).click()
    await bot.getByRole('heading', { name: 'No matching stocks found' }).waitFor()
    check('Empty state shows the backend explanation for missing metrics', (await bot.locator('.nl-empty').innerText()).includes('required metric values are missing or unverified'))
    check('No browser runtime errors', errors.length === 0)
    await fs.writeFile(path.join(output, 'verification.json'), JSON.stringify({ passed, errors, fixtureData: true }, null, 2))
    console.log(`${passed.length} natural-language screener browser checks passed`)
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
