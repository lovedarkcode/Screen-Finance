// Isolated browser fixtures; no backend or user data is changed.
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
const fs = require('node:fs/promises')
const path = require('node:path')
const baseURL = process.env.APP_URL || 'http://127.0.0.1:5174'

async function main() {
  const browser = await chromium.launch({ headless: true })
  const passed = [], errors = [], queries = [], ranges = []
  const check = (label, value) => { assert.ok(value, label); passed.push(label) }
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
    await context.addInitScript(() => localStorage.setItem('access_token', 'isolated-us-market-check'))
    const stock = symbol => ({ symbol, baseSymbol: symbol.replace('.NS', ''), name: ({ AAPL: 'Apple Inc.', F: 'Ford Motor Company', 'BRK-B': 'Berkshire Hathaway', 'TCS.NS': 'TCS Limited', TSM: 'Taiwan Semiconductor' })[symbol] || symbol, price: symbol.endsWith('.NS') ? 123.45 : 200.25, change: 2, changePercent: 1, exchange: symbol.endsWith('.NS') ? 'NSE' : 'NASDAQ', currency: symbol.endsWith('.NS') ? 'INR' : 'USD', timeZone: symbol.endsWith('.NS') ? 'Asia/Kolkata' : 'America/New_York', date: '2026-10-16T20:00:00Z' })
    await context.route('**/api/v1/**', route => {
      const url = new URL(route.request().url()), endpoint = decodeURIComponent(url.pathname.replace('/api/v1', ''))
      const symbol = endpoint.split('/')[2], currency = symbol === 'TSM' ? 'TWD' : symbol?.endsWith('.NS') ? 'INR' : 'USD'
      const ok = json => route.fulfill({ json })
      if (endpoint === '/auth/me') return ok({ id: 'review', name: 'UI Review', email: 'ui@example.test' })
      if (endpoint === '/watchlist') return ok({ items: ['AAPL', 'TCS.NS'] })
      if (endpoint === '/stocks/sectors') return ok([])
      if (endpoint === '/stocks') {
        const q = url.searchParams.get('q'); queries.push(q)
        return ok({ items: [stock(q === 'F' ? 'F' : q.toUpperCase().startsWith('BRK') ? 'BRK-B' : q.toUpperCase().startsWith('TCS') ? 'TCS.NS' : 'AAPL')] })
      }
      if (endpoint.endsWith('/chart')) {
        ranges.push(url.searchParams.get('range'))
        return ok(Array.from({ length: 5 }, (_, i) => ({ date: new Date(Date.UTC(2026, 9, 16, 13, 30 + i)).toISOString(), price: 200 + i })))
      }
      if (endpoint.endsWith('/overview')) return ok({
        currency: stock(symbol).currency, financialCurrency: currency,
        metrics: [{ id: 'marketCap', label: 'Market Cap', value: 3e12, currency: stock(symbol).currency, unit: currency === 'INR' ? 'crore' : 'compact' }, { id: 'eps', label: 'EPS', value: 5.5, currency: stock(symbol).currency, unit: currency === 'INR' ? 'inr' : 'currency' }, { id: 'revenue', label: 'Revenue', value: 1e8, currency, unit: currency === 'INR' ? 'crore' : 'compact' }],
        priceRange: { dayLow: 190, dayHigh: 205, open: 195, previousClose: 198, week52Low: 150, week52High: 220, volume: 1e6 },
        about: { sector: 'Technology', description: 'Isolated market UI fixture.' }, returns: [{ label: '1 Month', value: 2 }],
      })
      if (endpoint.endsWith('/shareholding')) return ok([{ label: 'Latest available', holdings: [{ name: 'Insiders', value: 10 }, { name: 'Institutions', value: 60 }, { name: 'Other holders', value: 30 }] }])
      if (endpoint.endsWith('/peers')) return ok([{ ...stock('MSFT'), marketCap: 2e12, peRatio: 25 }])
      if (/\/(quarters|profit-loss|balance-sheet|cash-flow|ratios)$/.test(endpoint)) return ok({ currency, chartUnit: currency === 'INR' ? 'Lakhs' : 'Millions', unit: `Figures in ${currency} ${currency === 'INR' ? 'Crore' : 'Millions'}`, columns: ['Jun 2026'], rows: [{ label: 'Revenue', values: [`${currency} 100 Million`] }], chart: [{ date: '30 Jun 2026', totalIncome: 100, profitBeforeTax: 25, netProfitLoss: 20, eps: 5.5 }] })
      if (/^\/stocks\/[^/]+$/.test(endpoint)) return ok(stock(symbol))
      return ok({ items: [] })
    })
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    const go = route => page.goto(`${baseURL}${route}`, { waitUntil: 'networkidle' })
    const searchFor = async query => {
      await page.getByRole('button', { name: 'Search stocks and sectors' }).click()
      await page.getByLabel('Search company or symbol').fill(query)
      await page.locator('.stock-search-results button').first().click()
      await page.waitForLoadState('networkidle')
    }
    await go('/stock/TCS.NS')
    check('Indian quotes retain rupees', await page.locator('.stock-price').innerText() === '₹123.45')
    await searchFor('Apple')
    await page.getByRole('heading', { name: 'Apple Inc.', exact: true }).waitFor()
    check('US company search opens its analysis route', page.url().endsWith('/stock/AAPL') && await page.getByRole('heading', { name: 'Apple Inc.', exact: true }).count() === 1)
    check('US quote uses dollars and exchange label', await page.locator('.stock-price').innerText() === '$200.25' && (await page.locator('.stock-classification').innerText()).includes('NASDAQ · USD'))
    check('US timestamp uses the exchange timezone', (await page.locator('.stock-timestamp').innerText()).includes('16:00') && (await page.locator('.stock-timestamp').innerText()).includes('EDT'))
    check('US market cap uses billions/trillions and EPS uses dollars', (await page.locator('.stock-metric-grid').innerText()).includes('$3T') && (await page.locator('.stock-metric-grid').innerText()).includes('$5.50'))
    check('Price chart axes show dollars', (await page.locator('#price-chart').innerText()).includes('$') && !(await page.locator('#price-chart').innerText()).includes('₹'))
    await page.getByRole('button', { name: '1D', exact: true }).click()
    await page.locator('#price-chart').getByText('09:30', { exact: true }).waitFor()
    check('US intraday labels use New York time', ranges.includes('1D'))
    check('US financial chart labels millions in USD', (await page.locator('#financials h2').innerText()).includes('USD Millions'))
    await page.getByRole('button', { name: 'Earnings Per Share', exact: true }).click()
    check('US EPS chart keeps the currency', (await page.locator('#financials h2').innerText()).includes('EPS in USD'))
    await page.getByText('Financial statements', { exact: true }).click()
    await page.locator('.stock-statement-table tbody tr').waitFor()
    check('Statements retain USD units and values', (await page.locator('.stock-statement-scroll').innerText()).includes('Figures in USD Millions') && (await page.locator('.stock-statement-table').innerText()).includes('$100 Million'))
    check('US peer monetary values use dollars', (await page.locator('.stock-peer-table').innerText()).includes('$200.25') && !(await page.locator('.stock-peer-table').innerText()).includes('Cr'))
    await searchFor('F')
    check('Single-letter US symbol is searchable', queries.includes('F') && page.url().endsWith('/stock/F'))
    await searchFor('BRK')
    check('Share-class symbols survive search and routing', page.url().endsWith('/stock/BRK-B'))
    await go('/watchlist')
    check('Mixed-market watchlist uses each stock currency', (await page.locator('main').innerText()).includes('$200.25') && (await page.locator('main').innerText()).includes('₹123.45'))
    await go('/stock/TSM')
    check('ADR quote stays USD while financial chart uses reporting currency', await page.locator('.stock-price').innerText() === '$200.25' && (await page.locator('#financials h2').innerText()).includes('TWD Millions'))
    await page.getByRole('button', { name: 'Edit Metrics', exact: true }).click()
    await page.locator('.stock-metric-options').getByRole('button', { name: 'Revenue', exact: true }).click()
    await page.getByRole('button', { name: 'Done', exact: true }).click()
    check('ADR revenue retains its reporting currency', (await page.locator('.stock-metric-grid').innerText()).includes('NT$100M'))
    for (const theme of ['dark', 'light']) {
      if (await page.locator('.stock-detail').first().getAttribute('data-stock-theme') !== theme) await page.getByRole('button', { name: `Switch to ${theme} mode` }).click()
      for (const width of [1440, 390]) {
        await page.setViewportSize({ width, height: 1000 })
        await go('/stock/AAPL')
        check(`US analysis fits ${width}px in ${theme} mode`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
        await page.screenshot({ path: path.join(__dirname, `apple-${theme}-${width}.png`), fullPage: true })
      }
    }
    check('No browser runtime errors', errors.length === 0)
    await fs.writeFile(path.join(__dirname, 'verification.json'), JSON.stringify({ passed, errors, fixtureData: true }, null, 2))
    console.log(`${passed.length} US-market browser checks passed`)
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
