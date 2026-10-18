// Isolated browser fixtures: no account, database or paid provider is changed.
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
const fs = require('node:fs/promises')
const path = require('node:path')
const baseURL = process.env.APP_URL || 'http://127.0.0.1:5175'
const output = process.env.UI_VERIFY_OUTPUT_DIR || __dirname

const stock = symbol => ({ symbol, name: symbol === 'AAPL' ? 'Apple Inc.' : symbol, price: 200, change: 2, changePercent: 1, exchange: symbol.endsWith('.NS') ? 'NSE' : 'NASDAQ', currency: symbol.endsWith('.NS') ? 'INR' : 'USD', timeZone: 'America/New_York', date: '2026-10-16T20:00:00Z' })
const report = symbol => ({ symbol, companyId: `${stock(symbol).exchange}:${symbol}`, analysisRunId: `isolated-run-${symbol}`, companyName: stock(symbol).name, exchange: stock(symbol).exchange, currency: stock(symbol).currency, financialCurrency: stock(symbol).currency, generatedAt: '2026-10-17T12:00:00Z', quoteAsOf: stock(symbol).date, provider: 'NVIDIA', model: 'nvidia/nemotron-3-ultra-550b-a55b', cached: false,
  quality: { coverage: 'partial', checkedCalculations: 8, providerMetrics: 10, annualPeriods: 3, quarterlyPeriods: 1, issues: [{ code: 'annual_ttm_difference', severity: 'medium', text: 'Annual and trailing metrics cover different periods; check their fiscal dates before comparing them.', evidenceIds: ['E2', 'E5'] }] },
  trends: [2023, 2024, 2025].map(year => ({ period: `FY ending ${year}-12-31`, periodEnd: `${year}-12-31`, periodType: 'annual', revenueId: `R${year}`, netIncomeId: `N${year}`, netMarginId: `M${year}` })),
  research: { summary: [{ text: 'Reported profitability is supported by positive annual earnings.', evidenceIds: ['E3'], significance: 'high', findingId: 'F1' }], strengths: [{ text: 'The reported net profit margin indicates positive profitability.', evidenceIds: ['E3'], significance: 'high', findingId: 'F1' }], risks: [{ text: 'Annual and trailing results require comparison of their different reporting periods.', evidenceIds: ['E2', 'E5'], significance: 'medium', findingId: 'F2' }], watchItems: [{ text: 'Watch whether profitability is sustained in subsequent reporting periods.', evidenceIds: ['E3'], significance: 'medium', findingId: 'F3' }] },
  metricIds: ['E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10'], evidence: [
    { id: 'E1', label: 'Annual revenue', value: 200000000, unit: 'currency', currency: stock(symbol).currency, period: '2025-12-31', sourceId: 'income', inputs: [] },
    { id: 'E2', label: 'Annual net income', value: 40000000, unit: 'currency', currency: stock(symbol).currency, period: '2025-12-31', sourceId: 'income', inputs: [] },
    { id: 'E3', label: 'Net profit margin', value: 20, unit: 'percent', kind: 'calculated', periodType: 'annual', period: 'FY ending 2025-12-31', sourceId: 'income', formula: 'Annual net income ÷ annual revenue × 100', inputs: ['E2', 'E1'] },
    ...['Market capitalization', 'Trailing P/E', 'Annual revenue growth', 'Operating margin', 'Current ratio', 'Debt to equity', 'Free cash flow'].map((label, index) => ({ id: `E${index + 4}`, label, value: index === 0 ? 3e12 : 2, unit: index === 0 || index === 6 ? 'currency' : index === 2 || index === 3 ? 'percent' : 'times', currency: stock(symbol).currency, period: 'Latest provider snapshot', sourceId: 'income', inputs: [] })),
    { id: 'E11', label: 'Return on equity (provider)', value: 22.21, unit: 'percent', kind: 'normalized', periodType: 'ttm', period: 'TTM (provider); exact period end unavailable', sourceId: 'income', formula: 'Provider returnOnEquity × 100 (unit conversion only)', inputs: ['E12'] },
    { id: 'E12', label: 'Provider ROE ratio', value: .2221, unit: 'number', sourceId: 'income', period: 'TTM (provider); exact period end unavailable', inputs: [] },
    ...[2023, 2024, 2025].flatMap((year, index) => [{ id: `R${year}`, label: `Annual revenue (${year})`, value: 1e8 + index * 5e7, unit: 'currency', currency: stock(symbol).currency, period: `FY ending ${year}-12-31`, sourceId: 'income', inputs: [] }, { id: `N${year}`, label: `Annual net income (${year})`, value: 2e7 + index * 1e7, unit: 'currency', currency: stock(symbol).currency, period: `FY ending ${year}-12-31`, sourceId: 'income', inputs: [] }, { id: `M${year}`, label: `Net profit margin (${year})`, value: 20, unit: 'percent', period: `FY ending ${year}-12-31`, sourceId: 'income', inputs: [] }]),
  ], sources: [{ id: 'income', label: 'Yahoo Finance · Income statements', url: `https://finance.yahoo.com/quote/${symbol}/financials/`, retrievedAt: '2026-10-17T12:00:00Z' }], warnings: ['Primary filings and recent news were not reviewed.'] })

async function main() {
  await fs.mkdir(output, { recursive: true })
  const browser = await chromium.launch({ headless: true })
  const passed = [], errors = [], requests = []
  let mode = 'pending', pending = null
  const check = (label, condition) => { assert.ok(condition, label); passed.push(label) }
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
    await context.addInitScript(() => localStorage.setItem('access_token', 'isolated-ai-analysis-review'))
    await context.route('**/api/v1/**', async route => {
      const endpoint = decodeURIComponent(new URL(route.request().url()).pathname.replace('/api/v1', ''))
      const symbol = endpoint.split('/')[2]
      const ok = json => route.fulfill({ json })
      if (endpoint === '/auth/me') return ok({ id: 'review', name: 'UI Review', email: 'ui@example.test' })
      if (endpoint === '/ai/analyze') {
        const body = route.request().postDataJSON(); requests.push(body)
        if (mode === 'pending') return new Promise(resolve => { pending = async () => { await ok(report(body.symbol)).catch(() => {}); resolve() } })
        if (mode === 'error') return route.fulfill({ status: 503, json: { detail: 'NVIDIA analysis is temporarily unavailable. Please retry.' } })
        if (mode === 'wrong-company') return ok(report('AAPL'))
        return ok(report(body.symbol))
      }
      if (endpoint === '/watchlist') return ok({ items: [] })
      if (endpoint === '/stocks/sectors') return ok([])
      if (endpoint === '/stocks') return ok({ items: [] })
      if (endpoint.endsWith('/chart')) return ok([{ date: '2026-10-16T20:00:00Z', price: 200 }, { date: '2026-10-15T20:00:00Z', price: 198 }].reverse())
      if (endpoint.endsWith('/overview')) return ok({ metrics: [], priceRange: {}, about: {}, returns: [] })
      if (endpoint.endsWith('/shareholding') || endpoint.endsWith('/peers')) return ok([])
      if (/\/(quarters|profit-loss|balance-sheet|cash-flow|ratios)$/.test(endpoint)) return ok({ currency: stock(symbol).currency, chartUnit: 'Millions', unit: 'Figures in Millions', columns: [], rows: [], chart: [] })
      if (/^\/stocks\/[^/]+$/.test(endpoint)) return ok(stock(symbol))
      return ok({ items: [] })
    })
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    const go = route => page.goto(`${baseURL}${route}`, { waitUntil: 'networkidle' })
    const launcher = page.getByRole('button', { name: 'Analyze with AI', exact: true })
    const dialog = page.getByRole('dialog', { name: 'AI Stock Analysis', exact: true })
    await go('/stock/AAPL')
    check('Stock header and chart have no Yahoo Finance links', await page.locator('a[href*="finance.yahoo.com"]').count() === 0 && await page.getByRole('link', { name: /Advanced chart|View market quote/ }).count() === 0)
    check('Analysis is opt-in; opening a stock does not call the LLM', requests.length === 0)
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 })
      await page.evaluate(() => scrollTo(0, document.body.scrollHeight))
      const box = await launcher.boundingBox()
      check(`Launcher remains bottom-right after scrolling at ${width}px`, box.x + box.width > width - 30 && box.x + box.width <= width - 12 && box.y + box.height >= 970 && box.y + box.height <= 988)
    }
    await launcher.click()
    await dialog.getByRole('heading', { name: 'Preparing your research' }).waitFor()
    check('Click sends only the selected symbol', requests.length === 1 && JSON.stringify(requests[0]) === '{"symbol":"AAPL"}')
    await page.keyboard.press('Escape')
    await launcher.click()
    check('Closing and reopening pending work does not duplicate it', requests.length === 1)
    await pending()
    await dialog.getByRole('heading', { name: 'Research summary' }).waitFor()
    check('Verified report exposes research, strengths, risks and watch items', (await dialog.innerText()).includes('What to watch') && (await dialog.innerText()).includes('nvidia/nemotron-3-ultra-550b-a55b'))
    check('Company and AI provider labels are distinct', (await dialog.innerText()).includes('AI provider: NVIDIA') && (await dialog.innerText()).includes('Apple Inc. · AAPL · NASDAQ'))
    check('Evidence coverage and reporting periods are visible beside metrics', (await dialog.getByLabel('Evidence quality').innerText()).includes('3 annual periods') && (await dialog.locator('.analysis-metrics').innerText()).includes('FY ending 2025-12-31'))
    check('Strengths and risks show significance', await dialog.getByText('high significance', { exact: true }).count() > 0)
    await dialog.getByRole('tab', { name: 'Financial trends', exact: true }).click()
    check('Annual history shows available periods and source values', await dialog.getByRole('table', { name: 'Annual financial history' }).getByRole('row').count() === 4 && (await dialog.getByRole('table', { name: 'Annual financial history' }).innerText()).includes('$100M'))
    await dialog.getByRole('button', { name: 'Annual revenue (2023), 2023-12-31, view evidence' }).click()
    await page.waitForFunction(() => document.activeElement.id === 'analysis-evidence-R2023')
    check('Trend values open their exact fiscal-period evidence', (await page.locator('#analysis-evidence-R2023').innerText()).includes('2023-12-31'))
    check('Period conflict flags are visible in evidence', (await dialog.getByLabel('Financial data checks').innerText()).includes('Annual and trailing metrics cover different periods'))
    check('Provider ROE conversion is distinct from recalculated metrics', (await page.locator('#analysis-evidence-E11').innerText()).includes('Provider · unit conversion') && !(await page.locator('#analysis-evidence-E11').innerText()).includes('Recalculated'))
    await dialog.getByRole('tab', { name: 'Research', exact: true }).click()
    await dialog.getByRole('button', { name: 'View evidence E3', exact: true }).first().click()
    await page.locator('#analysis-evidence-E3').waitFor()
    check('Citation opens evidence and focuses the cited calculation', await page.locator('#analysis-evidence-E3').evaluate(el => el === document.activeElement))
    check('Evidence retains exact figure, period and formula', (await page.locator('#analysis-evidence-E3').innerText()).includes('20.00%') && (await page.locator('#analysis-evidence-E3').innerText()).includes('2025-12-31') && (await page.locator('#analysis-evidence-E3').innerText()).includes('Annual net income ÷ annual revenue × 100'))
    check('AI research and evidence have no Yahoo Finance links or source list', await page.locator('a[href*="finance.yahoo.com"]').count() === 0 && await dialog.locator('.analysis-source-list').count() === 0)
    await dialog.getByRole('button', { name: 'View input evidence E2', exact: true }).click()
    await page.waitForFunction(() => document.activeElement.id === 'analysis-evidence-E2')
    check('Formula input links navigate to original values', (await page.locator('#analysis-evidence-E2').innerText()).includes('$40M'))
    for (const theme of ['dark', 'light']) {
      await page.keyboard.press('Escape')
      if (await page.locator('.stock-detail').first().getAttribute('data-stock-theme') !== theme) await page.getByRole('button', { name: `Switch to ${theme} mode` }).click()
      await launcher.click()
      for (const width of [1440, 390]) {
        await page.setViewportSize({ width, height: 1000 })
        await dialog.getByRole('tab', { name: 'Research', exact: true }).click()
        await dialog.evaluate(el => { el.scrollTop = 0 })
        check(`Research fits viewport in ${theme} at ${width}px`, await dialog.evaluate(el => el.scrollWidth <= el.clientWidth && el.getBoundingClientRect().top >= 0 && el.getBoundingClientRect().bottom <= innerHeight))
        await page.screenshot({ path: path.join(output, `research-${theme}-${width}.png`) })
        await dialog.getByRole('tab', { name: 'Financial trends', exact: true }).click()
        check(`Financial trends fit viewport in ${theme} at ${width}px`, await dialog.evaluate(el => el.scrollWidth <= el.clientWidth))
        await dialog.getByRole('table', { name: 'Annual financial history' }).scrollIntoViewIfNeeded()
        await page.screenshot({ path: path.join(output, `trends-${theme}-${width}.png`) })
      }
    }
    await page.keyboard.press('Escape')
    check('Reopening completed research does not call the provider again', requests.length === 1 && await launcher.evaluate(el => el === document.activeElement))
    for (const route of ['/feed', '/screens', '/watchlist', '/ai']) {
      await go(route)
      check(`Launcher is absent on ${route}`, await launcher.count() === 0)
    }
    mode = 'error'
    await go('/stock/NVDA')
    await launcher.click()
    await dialog.getByRole('alert').waitFor()
    check('Provider failure displays a retry action', (await dialog.getByRole('alert').innerText()).includes('temporarily unavailable'))
    mode = 'success'
    await dialog.getByRole('button', { name: 'Try again' }).click()
    await dialog.getByRole('heading', { name: 'Research summary' }).waitFor()
    check('Retry retrieves research for the current stock', requests.at(-1).symbol === 'NVDA')
    await page.keyboard.press('Escape')
    mode = 'pending'
    await go('/stock/RELIANCE.NS')
    await launcher.click()
    await dialog.getByRole('heading', { name: 'Preparing your research' }).waitFor()
    await page.keyboard.press('Escape')
    // Client-side route navigation unmounts the previous stock and aborts its HTTP request.
    await page.evaluate(() => { history.pushState({}, '', '/stock/MTARTECH.NS'); dispatchEvent(new PopStateEvent('popstate')) })
    await page.getByRole('heading', { name: 'MTARTECH.NS', exact: true }).waitFor()
    await pending()
    mode = 'success'
    await launcher.click()
    await dialog.getByRole('heading', { name: 'Research summary' }).waitFor()
    check('Navigating while pending prevents stale research from appearing', requests.at(-1).symbol === 'MTARTECH.NS' && (await dialog.innerText()).includes('MTARTECH.NS') && !(await dialog.innerText()).includes('RELIANCE'))
    await page.keyboard.press('Escape')
    mode = 'wrong-company'
    await go('/stock/BE')
    await launcher.click()
    await dialog.getByRole('alert').waitFor()
    check('A response for another listing is rejected before rendering', (await dialog.getByRole('alert').innerText()).includes('different or unverified listing') && await dialog.getByRole('heading', { name: 'Research summary' }).count() === 0)
    check('Removed links and generic disclaimer stay removed', await page.locator('a[href*="finance.yahoo.com"]').count() === 0 && await dialog.getByText('Coverage and limitations', { exact: true }).count() === 0)
    check('No browser runtime errors', errors.length === 0)
    await fs.writeFile(path.join(output, 'verification.json'), JSON.stringify({ passed, errors, fixtureData: true }, null, 2))
    console.log(`${passed.length} AI stock analysis browser checks passed`)
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
