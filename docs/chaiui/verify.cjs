// Run against Vite on port 5173. All API responses are isolated browser fixtures.
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
const fs = require('node:fs/promises')
const path = require('node:path')

async function main() {
  const browser = await chromium.launch({ headless: true })
  const passed = [], errors = [], ranges = [], authRequests = []
  const check = (name, value) => { assert.ok(value, name); passed.push(name) }
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
    await context.addInitScript(() => localStorage.setItem('access_token', 'isolated-chaiui-check'))
    let saved = ['ALPHA.NS'], chartError = false, searchError = false, watchlistError = false, removeError = false
    const stock = { symbol: 'ALPHA.NS', baseSymbol: 'ALPHA', name: 'Alpha Limited', price: 123.45, change: 2.45, changePercent: 2.02, date: '2026-10-17T10:30:00Z', exchange: 'NSE' }
    const table = { unit: 'Amount in INR Lakhs', columns: ['Jun 2026', 'Sep 2026'], rows: [{ label: 'Revenue', values: [1000, 1200] }] }
    await context.route('**/api/v1/**', async route => {
      const request = route.request(), url = new URL(request.url()), endpoint = decodeURIComponent(url.pathname.replace('/api/v1', ''))
      const ok = json => route.fulfill({ json }), fail = () => route.fulfill({ status: 503, json: { detail: 'Test outage' } })
      if (endpoint === '/auth/me') return ok({ id: 'review', name: 'UI Review', email: 'ui@example.test' })
      if (endpoint === '/auth/login' || endpoint === '/auth/register') { authRequests.push(request.postDataJSON()); return ok({ access_token: 'fixture-token', user: { name: 'UI Review' } }) }
      if (endpoint === '/watchlist') return watchlistError ? fail() : ok({ items: saved })
      if (endpoint.startsWith('/watchlist/')) { if (removeError) return fail(); await new Promise(resolve => setTimeout(resolve, 100)); saved = saved.filter(symbol => symbol !== endpoint.split('/').pop()); return ok({ items: saved }) }
      if (endpoint === '/stocks/sectors') return ok([{ id: 'it', name: 'IT & Software', tickerCount: 1 }])
      if (endpoint.startsWith('/stocks/sectors/')) return ok([stock])
      if (endpoint === '/stocks') return searchError ? fail() : ok({ items: [stock] })
      if (endpoint.endsWith('/chart')) {
        ranges.push(url.searchParams.get('range'))
        return chartError ? fail() : ok(Array.from({ length: 12 }, (_, i) => ({ date: `2026-10-${String(i + 1).padStart(2, '0')}`, price: 100 + i * 2 })))
      }
      if (endpoint.endsWith('/overview')) return ok({
        metrics: [{ id: 'marketCap', label: 'Market Cap', value: 1e10, unit: 'crore' }, { id: 'peRatio', label: 'P/E Ratio', value: 20 }, { id: 'eps', label: 'EPS', value: 6.17, unit: 'inr' }],
        priceRange: { dayLow: 120, dayHigh: 125, week52Low: 90, week52High: 140, open: 121, previousClose: 121, volume: 10000 },
        returns: [{ label: '1D', value: 2 }, { label: '1M', value: -3 }],
        about: { description: 'A company profile for isolated UI checks. '.repeat(25), headquarters: 'Mumbai', ceo: 'Sample CEO', website: 'https://example.test', industry: 'Software' },
      })
      if (endpoint.endsWith('/quarters')) return ok({ ...table, chart: ['30 Jun 2026', '30 Sep 2026'].map((date, i) => ({ date, totalIncome: 1000 + i * 200, profitBeforeTax: 200 + i * 50, netProfitLoss: 150 + i * 50, eps: 5 + i })) })
      if (endpoint.endsWith('/shareholding')) return ok(['Sep 2026', 'Jun 2026'].map((label, i) => ({ label, periodEnd: label, holdings: [{ name: 'Promoters', value: 50 + i }, { name: 'Institutions', value: 30 - i }, { name: 'Public', value: 20 }] })))
      if (endpoint.endsWith('/peers')) return ok([{ ...stock, symbol: 'BETA.NS', baseSymbol: 'BETA', name: 'Beta Limited', marketCap: 2e10, peRatio: 22 }])
      if (/\/(profit-loss|balance-sheet|cash-flow|ratios)$/.test(endpoint)) return ok(table)
      if (/^\/stocks\/[^/]+$/.test(endpoint)) return ok({ ...stock, symbol: endpoint.split('/').pop() })
      return ok({ items: [] })
    })
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', msg => { if (msg.type() === 'error' && /validateDOMNesting|cannot be a descendant|cannot contain|Encountered two children/.test(msg.text())) errors.push(msg.text()) })
    const go = route => page.goto(`http://127.0.0.1:5173${route}`, { waitUntil: 'networkidle' })
    await go('/stock/ALPHA.NS')
    check('Price, financial and ownership charts render', await page.locator('.recharts-surface').count() >= 3)
    await Promise.all([page.waitForResponse(response => response.url().includes('range=1W')), page.getByRole('button', { name: '1W', exact: true }).click()])
    check('Short chart range uses existing API', ranges.includes('1W'))
    await page.getByRole('button', { name: 'More chart timeframes' }).click()
    await Promise.all([page.waitForResponse(response => response.url().includes('range=10Y')), page.getByRole('menuitemradio', { name: '10Y' }).click()])
    check('Long range menu uses existing API', ranges.includes('10Y'))
    check('Range menu closes after selection', await page.getByRole('menu').count() === 0)
    await page.getByRole('button', { name: 'Earnings Per Share', exact: true }).click()
    check('Financial chart switches to EPS', await page.getByRole('heading', { name: /Financial Result \(EPS/ }).count() === 1)
    await page.getByRole('group', { name: 'Ownership reporting date' }).getByRole('button', { name: 'Jun 2026' }).click()
    check('Ownership report changes values', (await page.locator('.stock-holding-values').innerText()).includes('51.00%'))
    await page.getByText('Financial statements', { exact: true }).click()
    await page.getByRole('button', { name: 'Balance Sheet', exact: true }).click()
    await page.locator('.stock-statement-table tbody tr').waitFor()
    check('Statements retain financial values and row headers', await page.locator('.stock-statement-table tbody th[scope=row]').textContent() === 'Revenue')
    await page.getByRole('button', { name: 'Edit Metrics', exact: true }).click()
    await page.getByLabel('Remove EPS', { exact: true }).click()
    await page.getByRole('button', { name: 'Done', exact: true }).click()
    check('Metric controls persist removal', !(await page.locator('.stock-metric-grid').innerText()).includes('EPS'))
    await page.getByRole('button', { name: 'Read more', exact: true }).click()
    check('Company description expands', await page.getByRole('button', { name: 'Show less' }).getAttribute('aria-expanded') === 'true')
    await page.getByRole('button', { name: 'Search stocks and sectors' }).click()
    const search = page.getByLabel('Search company or symbol')
    await page.waitForFunction(() => document.activeElement?.getAttribute('aria-label') === 'Search company or symbol')
    check('Search dialog focuses the input on opening', true)
    check('Search is a labelled ChaiUI search field', await search.getAttribute('type') === 'search')
    await search.fill('alpha')
    await page.getByRole('button', { name: /Alpha Limited.*ALPHA.NS/ }).waitFor()
    check('Typing keeps focus in search', await search.evaluate(el => document.activeElement === el))
    await page.getByRole('link', { name: 'Back to Screener' }).focus()
    await page.keyboard.press('Tab')
    check('Dialog traps forward Tab', await page.getByRole('button', { name: 'Close', exact: true }).evaluate(el => document.activeElement === el))
    await page.keyboard.press('Shift+Tab')
    check('Dialog traps reverse Tab', await page.getByRole('link', { name: 'Back to Screener' }).evaluate(el => document.activeElement === el))
    await page.keyboard.press('Escape')
    check('Escape restores trigger focus', await page.getByRole('button', { name: 'Search stocks and sectors' }).evaluate(el => document.activeElement === el))
    searchError = true
    await page.getByRole('button', { name: 'Search stocks and sectors' }).click()
    await search.fill('failure')
    await page.getByRole('alert').filter({ hasText: 'Search is temporarily unavailable' }).waitFor()
    check('Search failure is visible', true)
    await page.keyboard.press('Escape')
    searchError = false
    chartError = true
    await page.getByRole('button', { name: '1M', exact: true }).click()
    await page.getByText('Price history is temporarily unavailable.').waitFor()
    chartError = false
    await page.locator('#price-chart').getByRole('button', { name: 'Try again' }).click()
    await page.locator('#price-chart .recharts-surface').waitFor()
    check('Chart outage retry recovers', true)
    for (const theme of ['dark', 'light']) {
      if (await page.locator('.stock-detail').first().getAttribute('data-stock-theme') !== theme) await page.getByRole('button', { name: `Switch to ${theme} mode` }).click()
      for (const width of [1440, 390]) {
        await page.setViewportSize({ width, height: 1000 })
        for (const route of ['/feed', '/screens?sector=it', '/stock/ALPHA.NS', '/watchlist']) {
          await go(route)
          check(`No overflow ${route} ${theme} ${width}`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
          await page.screenshot({ path: path.join(__dirname, `${route.split('/')[1].split('?')[0]}-${theme}-${width}.png`), fullPage: true })
          if (route === '/stock/ALPHA.NS') {
            await page.getByRole('button', { name: 'Search stocks and sectors' }).click()
            await page.getByRole('dialog').waitFor()
            await page.screenshot({ path: path.join(__dirname, `search-${theme}-${width}.png`), fullPage: true })
            await page.keyboard.press('Escape')
          }
        }
      }
    }
    await go('/watchlist')
    removeError = true
    await page.getByRole('button', { name: 'Remove ALPHA.NS from watchlist' }).click()
    await page.locator('[data-slot=toast]').filter({ hasText: 'Failed to remove stock from watchlist' }).waitFor()
    check('Failed removal keeps the saved stock and shows a ChaiUI error toast', await page.getByRole('link', { name: 'Alpha Limited', exact: true }).count() === 1)
    await page.getByRole('button', { name: 'Dismiss', exact: true }).click()
    check('ChaiUI toast dismisses', await page.locator('[data-slot=toast]').count() === 0)
    removeError = false
    await page.getByRole('button', { name: 'Remove ALPHA.NS from watchlist' }).click()
    await page.getByRole('heading', { name: 'Your watchlist is empty' }).waitFor()
    check('Watchlist removal retains route and reaches empty state', page.url().endsWith('/watchlist'))
    check('Empty watchlist action remains readable', await page.getByRole('link', { name: 'Explore Screens' }).evaluate(el => getComputedStyle(el).color !== getComputedStyle(el).backgroundColor))
    check('Successful removal shows a ChaiUI success toast', await page.locator('[data-slot=toast]').filter({ hasText: 'removed from watchlist successfully' }).count() === 1)
    watchlistError = true
    await go('/watchlist')
    await page.getByText('Could not load watchlist. Please try again.').waitFor()
    watchlistError = false
    await page.getByRole('button', { name: 'Try again' }).click()
    await page.getByRole('heading', { name: 'Your watchlist is empty' }).waitFor()
    check('Watchlist retry recovers', true)
    await context.clearCookies()
    await page.evaluate(() => localStorage.removeItem('access_token'))
    await go('/login')
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.getByText('Password is required', { exact: true }).waitFor()
    check('ChaiUI field links validation errors', await page.getByLabel('Password', { exact: true }).getAttribute('aria-invalid') === 'true' && !!await page.getByLabel('Password', { exact: true }).getAttribute('aria-describedby'))
    await page.screenshot({ path: path.join(__dirname, 'login-390.png'), fullPage: true })
    await page.getByLabel('Email', { exact: true }).fill('ui@example.test')
    await page.getByLabel('Password', { exact: true }).fill('example-password')
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.waitForURL('**/feed')
    check('Login submits original fields and navigates', authRequests[0].email === 'ui@example.test' && authRequests[0].password === 'example-password')
    await page.evaluate(() => localStorage.removeItem('access_token'))
    await go('/register')
    await page.getByLabel('Name', { exact: true }).fill('UI Review')
    await page.getByLabel('Email', { exact: true }).fill('new@example.test')
    await page.getByLabel('Password', { exact: true }).fill('example-password')
    await page.getByRole('button', { name: 'Create account', exact: true }).click()
    await page.waitForURL('**/feed')
    check('Registration submits original fields', authRequests[1].name === 'UI Review' && authRequests[1].email === 'new@example.test')
    check('No runtime or DOM nesting errors', errors.length === 0)
    await fs.writeFile(path.join(__dirname, 'chaiui-verification.json'), JSON.stringify({ passed, errors, fixtureData: true }, null, 2))
    console.log(`${passed.length} ChaiUI browser checks passed`)
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
