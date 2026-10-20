// Isolated browser fixtures: no account, database or provider modifications.
const { chromium } = require('C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
const fs = require('node:fs')

function fixture(index, market = 'IN') {
  const currency = market === 'IN' ? 'INR' : 'USD'
  const metrics = Object.fromEntries(['sales', 'ebitda', 'net_profit', 'eps'].map((key, i) => [key, {
    value: key === 'eps' ? 2.5 : (200 - i * 50) * 1e7, currency,
    source_field: key === 'eps' ? 'Diluted EPS' : key,
    yoy: { value: 25, reason: null }, qoq: { value: 10, reason: null },
  }]))
  const symbol = `FIX${index}${market === 'IN' ? '.NS' : ''}`
  return { symbol, market, name: `Fixture Company ${String(index + 1).padStart(2, '0')}`, industry: index % 2 ? 'Software' : 'Hardware', exchange: market === 'IN' ? 'NSE' : 'NASDAQ',
    currency, quarter_end: '2026-06-30', previous_quarter_end: '2026-03-31', previous_year_end: '2025-06-30', metrics,
    source_url: `https://finance.yahoo.com/quote/${symbol}/financials/`,
    history: ['2026-06-30', '2026-03-31', '2025-06-30'].map(quarter_end => ({ quarter_end, currency, sales: 200e7, net_profit: 50e7, ebitda: null, eps: 2.5 })),
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true })
  const checks = []
  const check = (name, condition) => { assert(condition, name); checks.push(name) }
  let mode = 'loading', release
  const source = [...Array.from({ length: 14 }, (_, i) => fixture(i)), fixture(20, 'US')]
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, reducedMotion: 'reduce' })
    await context.addInitScript(() => { localStorage.setItem('access_token', 'isolated-quarterly-test'); localStorage.setItem('asset-hunter-stock-theme', '"dark"') })
    await context.route('**/api/v1/**', async route => {
      const url = new URL(route.request().url())
      if (url.pathname.endsWith('/auth/me')) return route.fulfill({ json: { id: 1, name: 'Fixture', email: 'fixture@example.com' } })
      if (!url.pathname.endsWith('/results/imported')) return route.fulfill({ json: [] })
      if (mode === 'live') return route.fulfill({ json: JSON.parse(fs.readFileSync('docs/quarterly-results/live-verification.json', 'utf8')).database.IN })
      if (mode === 'loading') await new Promise(resolve => { release = resolve })
      if (mode === 'error') return route.fulfill({ status: 503, json: { detail: 'Unavailable' } })
      const params = url.searchParams
      const market = params.get('market') || 'IN'
      const universe = source.filter(item => market === 'ALL' || item.market === market)
      let items = universe.filter(item => (!params.get('industry') || item.industry === params.get('industry')) && (!params.get('q') || item.name.toLowerCase().includes(params.get('q').toLowerCase())))
      if (mode === 'empty') items = []
      const page = Number(params.get('page') || 1)
      return route.fulfill({ json: { items: items.slice((page - 1) * 12, page * 12), total: items.length, page, page_size: 12,
        universe_count: universe.length, quarters: ['2026-06-30', '2026-03-31'], industries: ['Hardware', 'Software'],
        growing_sales: items.length, growing_profit: items.length, updated_at: '2026-10-20T08:00:00Z' } })
    })
    const page = await context.newPage()
    const errors = []
    page.on('pageerror', error => errors.push(error.message))
    await page.goto('http://127.0.0.1:5186/results/imported')
    await page.getByLabel('Loading quarterly results').waitFor()
    check('Loading state appears', true)
    await page.waitForFunction(() => performance.getEntriesByType('resource').some(item => item.name.includes('/auth/me')))
    while (!release) await page.waitForTimeout(50)
    mode = 'ready'; release()
    await page.locator('.result-card').first().waitFor()
    check('First page shows twelve results', await page.locator('.result-card').count() === 12)
    check('Reporting dates are distinguished from announcements', (await page.locator('.results-disclosure').innerText()).includes('fiscal quarter ends'))
    await page.screenshot({ path: 'docs/quarterly-results/desktop-dark.png' })
    await page.getByRole('button', { name: 'Next', exact: true }).click()
    await page.getByText('Page 2 of 2').waitFor()
    check('Pagination uses server page', await page.locator('.result-card').count() === 2 && page.url().includes('page=2'))
    await page.getByLabel('Reporting quarter', { exact: true }).selectOption('2026-06-30')
    await page.getByLabel('By industry', { exact: true }).selectOption('Software')
    await page.getByText('Page 1 of 1').waitFor()
    check('Industry filtering preserves selected quarter and resets page', page.url().includes('quarter=2026-06-30') && !page.url().includes('page=2') && await page.locator('.result-card').count() === 7)
    await page.getByRole('button', { name: 'QoQ', exact: true }).click()
    check('Growth comparison changes displayed values', (await page.locator('.result-card').first().innerText()).includes('+10.0%'))
    await page.getByRole('button', { name: /View comparisons for/ }).first().click()
    const dialog = page.getByRole('dialog')
    await dialog.waitFor()
    check('Comparison dialog shows history and source', await dialog.locator('tbody tr').count() === 3 && (await dialog.getByRole('link', { name: 'Source financial statements' }).getAttribute('href')).startsWith('https://finance.yahoo.com/'))
    await dialog.screenshot({ path: 'docs/quarterly-results/comparisons.png' })
    await page.keyboard.press('Escape')
    await page.getByLabel('Search results by company or symbol').fill('Company 02')
    await page.getByText('Page 1 of 1 · 1 companies').waitFor()
    check('Company search filters results', await page.locator('.result-card').count() === 1)
    await page.getByLabel('Search results by company or symbol').fill('')
    await page.waitForURL(url => !url.searchParams.get('q'))
    await page.waitForFunction(() => document.querySelectorAll('.result-card').length === 7)
    await page.getByLabel('By industry', { exact: true }).selectOption('')
    await page.getByText('Page 1 of 2').waitFor()
    await page.getByRole('button', { name: 'Switch to light mode' }).click()
    await page.screenshot({ path: 'docs/quarterly-results/desktop-light.png' })
    await page.setViewportSize({ width: 390, height: 844 })
    await page.locator('.result-card').last().scrollIntoViewIfNeeded()
    check('All mobile result cards remain reachable', await page.locator('.result-card').last().isVisible())
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.screenshot({ path: 'docs/quarterly-results/mobile.png' })
    check('Mobile page has no horizontal overflow', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
    await page.getByLabel('Market', { exact: true }).selectOption('US')
    await page.getByText('Page 1 of 1').waitFor()
    check('Market selection changes currency and clears incompatible filters', (await page.locator('.result-card').first().innerText()).includes('USD million') && !page.url().includes('quarter='))
    mode = 'error'
    await page.getByRole('button', { name: 'Reload results' }).click()
    await page.getByText('Quarterly results are temporarily unavailable. Please retry.').waitFor()
    mode = 'ready'
    await page.getByRole('button', { name: 'Try again', exact: true }).click()
    await page.locator('.result-card').first().waitFor()
    check('Provider/database error can be retried', true)
    mode = 'empty'
    await page.getByRole('button', { name: 'Reload results' }).click()
    await page.getByText(/No quarterly results match this selection/).waitFor()
    check('Empty state provides clear filters', await page.getByRole('button', { name: 'Clear filters' }).isVisible())
    check('No browser runtime errors', errors.length === 0)
    fs.writeFileSync('docs/quarterly-results/browser-verification.json', JSON.stringify({ fixture: true, checks }, null, 2))
    console.log(`Passed ${checks.length} quarterly-results browser checks.`)
    if (fs.existsSync('docs/quarterly-results/live-verification.json')) {
      mode = 'live'
      await page.setViewportSize({ width: 1440, height: 1100 })
      await page.goto('http://127.0.0.1:5186/results/imported')
      await page.locator('.result-card').first().waitFor()
      const real = JSON.parse(fs.readFileSync('docs/quarterly-results/live-verification.json', 'utf8')).database.IN
      assert.equal(await page.locator('.result-card').count(), real.items.length)
      assert((await page.locator('.result-card').first().innerText()).includes(real.items[0].name))
      await page.screenshot({ path: 'docs/quarterly-results/imported-data-desktop.png' })
      await page.setViewportSize({ width: 390, height: 844 })
      await page.screenshot({ path: 'docs/quarterly-results/imported-data-mobile.png' })
      console.log(`Rendered ${real.items.length} real imported Indian companies using a saved read-only database response and isolated authentication.`)
    }
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
