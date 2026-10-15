// Run with Node while Vite is serving localhost:5173. Uses the installed Playwright driver.
// Override PLAYWRIGHT_PATH to use another existing Playwright installation; installs nothing.
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
const fs = require('node:fs/promises')
const path = require('node:path')

async function main() {
  const browser = await chromium.launch({ headless: true })
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
    await context.addInitScript(() => localStorage.setItem('access_token', 'isolated-browser-test'))
    let sectorFails = false, quotesFail = false, newsFails = false, watchlistFails = false, sectorDelay = false, quoteRequests = 0, mutations = 0
    let saved = []
    const sectors = [{ id: 'it', name: 'IT & Software', tickerCount: 3, description: 'Software companies.' }, { id: 'banking', name: 'Banking', tickerCount: 1, description: 'Banks.' }]
    const stocks = [{ symbol: 'ALPHA.NS', name: 'Alpha Limited', price: 100, change: 2, changePercent: 2 }, { symbol: 'BETA.NS', name: 'Beta Limited', price: 200, change: -2, changePercent: -1 }, { symbol: 'UNKNOWN.NS', name: 'Unavailable Limited', price: null, change: null, changePercent: null }]
    await context.route('**/api/v1/**', async route => {
      const request = route.request(), url = new URL(request.url()), endpoint = decodeURIComponent(url.pathname.replace('/api/v1', ''))
      const ok = json => route.fulfill({ json })
      const fail = () => route.fulfill({ status: 503, json: { detail: 'Test outage' } })
      if (endpoint === '/auth/me') return ok({ id: 'test', name: 'Visual review', email: 'visual@example.test' })
      if (endpoint === '/watchlist') return watchlistFails ? fail() : ok({ items: saved })
      if (endpoint.startsWith('/watchlist/')) {
        mutations++
        await new Promise(resolve => setTimeout(resolve, 150))
        const symbol = endpoint.split('/').pop()
        saved = request.method() === 'DELETE' ? saved.filter(value => value !== symbol) : [...saved, symbol]
        return ok({ items: saved })
      }
      if (endpoint === '/stocks/sectors') return sectorFails ? fail() : ok(sectors)
      if (endpoint.startsWith('/stocks/sectors/')) {
        quoteRequests++
        if (sectorDelay && endpoint.endsWith('/it')) await new Promise(resolve => setTimeout(resolve, 500))
        return quotesFail ? fail() : ok(endpoint.endsWith('/it') ? stocks : [{ ...stocks[0], name: 'Bank Limited' }])
      }
      if (endpoint === '/stocks') return ok({ items: [stocks[0]], total: 1 })
      if (endpoint.endsWith('/chart')) return ok(Array.from({ length: 12 }, (_, i) => ({ date: `2026-10-${String(i + 1).padStart(2, '0')}`, price: 100 + i })))
      if (endpoint === '/news') return newsFails ? fail() : ok({ items: [] })
      if (/^\/stocks\/[^/]+$/.test(endpoint)) {
        const symbol = endpoint.split('/').pop()
        return ok({ ...stocks[symbol === 'RELIANCE.NS' ? 1 : 0], symbol, name: symbol === 'ALPHA.NS' ? 'Alpha Limited' : symbol, date: '2026-10-15T10:30:00Z', exchange: 'NSE', currency: 'INR' })
      }
      return ok({})
    })
    const page = await context.newPage(), errors = [], passed = []
    page.on('pageerror', error => errors.push(error.message))
    const go = route => page.goto(`http://localhost:5173${route}`, { waitUntil: 'networkidle' })
    const check = (name, value) => { assert.ok(value, name); passed.push(name) }
    await go('/screens?sector=it')
    await page.locator('tbody tr').first().waitFor()
    check('Deep-link sector and three constituents', await page.locator('tbody tr').count() === 3)
    check('Unknown quote is displayed honestly', await page.getByText('Quote unavailable', { exact: true }).count() === 1)
    check('Average excludes unavailable quotes', (await page.locator('.market-screen-stats').innerText()).includes('+0.50%'))
    await page.getByLabel('Filter sector stocks').fill('beta')
    check('Name filter', await page.locator('tbody tr').count() === 1)
    await page.getByLabel('Filter sector stocks').fill('missing')
    await page.getByText(/No companies match/).waitFor()
    await page.getByRole('button', { name: 'Clear search' }).click()
    await page.getByRole('button', { name: 'Price', exact: true }).click()
    check('Numeric sort descending and null last', (await page.locator('tbody tr').allTextContents())[0].includes('Beta') && (await page.locator('tbody tr').last().innerText()).includes('Unavailable'))
    await page.getByRole('button', { name: 'Add ALPHA.NS to watchlist' }).click()
    check('Pending watchlist action disabled', await page.getByRole('button', { name: 'Add ALPHA.NS to watchlist' }).isDisabled())
    await page.getByRole('button', { name: 'Remove ALPHA.NS from watchlist' }).waitFor()
    check('Watchlist mutation persisted', saved.includes('ALPHA.NS') && mutations === 1)
    await page.getByRole('button', { name: 'Remove ALPHA.NS from watchlist' }).click()
    await page.getByRole('button', { name: 'Add ALPHA.NS to watchlist' }).waitFor()
    check('Watchlist removal persisted', !saved.includes('ALPHA.NS') && mutations === 2)
    const before = quoteRequests
    await page.getByRole('button', { name: 'Refresh quotes' }).click()
    await page.locator('tbody tr').first().waitFor()
    check('Refresh requests current sector', quoteRequests > before)
    await page.getByRole('button', { name: 'Switch to light mode' }).click()
    await page.getByRole('navigation').getByRole('link', { name: 'Feed', exact: true }).click()
    await page.getByRole('heading', { name: 'Your market, at a glance' }).waitFor()
    check('Theme carries from Screens into Feed', await page.locator('.stock-detail').first().getAttribute('data-stock-theme') === 'light')
    await page.getByRole('button', { name: /SENSEX/ }).click()
    await page.getByRole('heading', { name: /SENSEX Performance/ }).waitFor()
    await page.getByRole('button', { name: '1W', exact: true }).click()
    check('Shared chart timeframe selector works', await page.getByRole('button', { name: '1W', exact: true }).getAttribute('aria-pressed') === 'true')
    await page.getByRole('button', { name: 'Losers', exact: true }).click()
    check('Movers filter removes positive returns', await page.locator('.market-movers-table tbody tr').count() === 1)
    check('News endpoint empty state', await page.getByText('No market stories available yet').count() === 1)
    await page.getByRole('link', { name: 'IT & Software 3 companies' }).click()
    await page.locator('tbody tr').first().waitFor()
    check('Feed sector card routes to selected Screener sector', new URL(page.url()).searchParams.get('sector') === 'it')
    await page.getByRole('button', { name: 'Search stocks and sectors' }).click()
    await page.getByLabel('Search company or symbol').fill('alpha')
    await page.getByRole('button', { name: /Alpha Limited.*ALPHA.NS/ }).click()
    await page.getByRole('heading', { name: 'Alpha Limited', exact: true }).waitFor()
    check('Shared search routes into stock detail', page.url().endsWith('/stock/ALPHA.NS'))
    check('Theme carries into stock detail', await page.locator('.stock-detail').first().getAttribute('data-stock-theme') === 'light')
    await page.getByRole('button', { name: 'Account and saved lists' }).click()
    check('Account retains saved-list routes', await page.getByRole('dialog').getByRole('link', { name: 'Watchlist' }).getAttribute('href') === '/watchlist')
    await page.keyboard.press('Escape')
    for (const width of [1440, 1024, 768, 390]) {
      await page.setViewportSize({ width, height: 900 })
      for (const route of ['/feed', '/screens?sector=it', '/stock/ALPHA.NS']) {
        await go(route)
        check(`No page overflow: ${route} at ${width}px`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      }
    }
    quotesFail = true
    await go('/screens?sector=it')
    await page.getByText('Sector quotes are temporarily unavailable.').waitFor()
    await page.screenshot({ path: path.join(__dirname, 'screens-error-390.png'), fullPage: true })
    quotesFail = false
    await page.getByRole('button', { name: 'Try again' }).click()
    await page.locator('tbody tr').first().waitFor()
    check('Quote error retry recovers', await page.locator('tbody tr').count() === 3)
    watchlistFails = true
    await go('/screens?sector=it')
    await page.getByText(/Watchlist unavailable/).waitFor()
    check('Watchlist outage does not block sectors or quotes', await page.locator('tbody tr').count() === 3)
    sectorFails = true
    await go('/screens')
    await page.getByText('Market sectors are temporarily unavailable.').waitFor()
    sectorFails = false
    await page.getByRole('button', { name: 'Try again' }).click()
    await page.locator('tbody tr').first().waitFor()
    check('Sector error retry recovers', await page.locator('tbody tr').count() === 3)
    sectorDelay = true
    await go('/screens?sector=banking')
    await page.getByRole('button', { name: 'IT & Software · 3' }).click()
    await page.getByRole('button', { name: 'Banking · 1' }).click()
    await page.locator('tbody tr').first().waitFor()
    await page.waitForTimeout(700)
    check('Late old sector response cannot overwrite current sector', await page.locator('tbody tr').count() === 1 && (await page.locator('tbody').innerText()).includes('Bank Limited'))
    newsFails = true
    await go('/feed')
    await page.getByText('Market news is temporarily unavailable.').waitFor()
    check('News error isolated from market quotes', await page.locator('.market-movers-table tbody tr').count() > 0)
    check('No browser runtime errors', errors.length === 0)
    await fs.writeFile(path.join(__dirname, 'verification.json'), JSON.stringify({ passed, runtimeErrors: errors, fixtureData: true }, null, 2))
    console.log(`${passed.length} browser checks passed`)
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
