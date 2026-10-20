// Browser-only synthetic fixtures; never inserted into the database.
const { chromium } = require('C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const metrics = Object.fromEntries(['revenue', 'net_income', 'eps', 'operating_margin'].map(field => [field, { yoy: { value: '10', reason: null }, qoq: { value: null } }]))
const result = { id: 1, company_id: 1, ticker: 'FIX', company_name: 'Fixture US Company', exchange: 'NYSE', provider: 'Yahoo Finance/yfinance', period_basis: 'inferred_from_annual_period_end', fiscal_year: 2026, quarter_period: 'Q2', period_end: '2026-06-30', filing_date: null, filing_date_kind: 'unavailable', currency: 'USD', revenue: '2000000000', net_income: '200000000', eps: '2.5', eps_basis: 'diluted', operating_margin: '20', revision: 1, comparisons: { metrics }, summary_status: 'completed', summary_model: 'nvidia/nemotron-3-super-120b-a12b', ai_summary_json: { positive_triggers: ['Revenue increased by 10%.'], red_flags: [], executive_summary: ['Reported revenue was USD 2,000,000,000.00.', 'Operating margin was 20.00%.'] } }
const listings = [
  { company_id: 1, ticker: 'FIX', company_name: 'Fixture US Company', exchange: 'NYSE', data_status: 'ready', latest_result: result },
  { company_id: 2, ticker: 'FIX.NS', company_name: 'Fixture India Company', exchange: 'NSE', data_status: 'ready', latest_result: { ...result, id: 2, ticker: 'FIX.NS', company_name: 'Fixture India Company', currency: 'INR' } },
  { company_id: 3, ticker: 'PENDING.BO', company_name: 'Fixture Pending', exchange: 'BSE', data_status: 'pending', latest_result: null },
  { company_id: 4, ticker: 'EMPTY.NS', company_name: 'Fixture Unavailable', exchange: 'NSE', data_status: 'unavailable', latest_result: null },
  { company_id: 5, ticker: 'RETRY', company_name: 'Fixture Retry', exchange: 'NASDAQ', data_status: 'error', latest_result: null },
  ...Array.from({ length: 11 }, (_, i) => ({ company_id: i + 6, ticker: `MORE${i}.NS`, company_name: `Additional Company ${i}`, exchange: 'NSE', data_status: 'pending', latest_result: null })),
]
async function main() {
  const browser = await chromium.launch({ headless: true })
  const checks = [], errors = []
  const check = (label, value = true) => { assert(value, label); checks.push(label) }
  let mode = 'loading', release
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } })
    await context.addInitScript(() => localStorage.setItem('access_token', 'isolated-yahoo-browser-check'))
    await context.route('**/api/v1/**', async route => {
      const url = new URL(route.request().url())
      if (url.pathname.endsWith('/auth/me')) return route.fulfill({ json: { id: 1, name: 'Fixture', email: 'fixture@example.com' } })
      if (url.pathname.endsWith('/results')) {
        if (mode === 'loading') await new Promise(resolve => { release = resolve })
        if (mode === 'error') return route.fulfill({ status: 503, json: {} })
        const p = url.searchParams, market = p.get('market')
        let rows = listings.filter(row => (!market || market === 'ALL' || (['NSE', 'BSE'].includes(row.exchange) ? 'IN' : 'US') === market) && (!p.get('exchange') || row.exchange === p.get('exchange')) && (!p.get('q') || row.ticker.includes(p.get('q').toUpperCase())))
        const coverage = { listed: rows.length, with_results: rows.filter(row => row.latest_result).length, ...Object.fromEntries(['pending', 'ready', 'unavailable', 'error'].map(status => [status, rows.filter(row => row.data_status === status).length])) }
        if (p.get('status') && p.get('status') !== 'all') rows = rows.filter(row => row.data_status === p.get('status'))
        const total = rows.length, page = Number(p.get('page') || 1)
        rows = rows.slice((page - 1) * 12, page * 12)
        if (['pending', 'failed'].includes(mode)) rows = rows.map(row => ({ ...row, latest_result: row.latest_result ? { ...row.latest_result, summary_status: mode, ai_summary_json: null } : null }))
        return route.fulfill({ json: { items: rows, total, page, page_size: 12, source: 'Yahoo Finance/yfinance', coverage, catalog_status: {}, poll_status: null } })
      }
      if (url.pathname.includes('/results/')) return route.fulfill({ json: { items: [result, { ...result, id: 3, quarter_period: 'Q1', period_end: '2026-03-31' }] } })
      return route.fulfill({ json: [] })
    })
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    const reload = async () => { await page.getByRole('button', { name: 'Reload filings' }).click() }
    await page.goto('http://127.0.0.1:5186/results')
    await page.getByLabel('Loading company filings').waitFor()
    check('Loading state')
    while (!release) await page.waitForTimeout(20)
    mode = 'ready'; release()
    await page.locator('.filing-card').first().waitFor()
    check('All-catalog server pagination renders 12 listings', await page.locator('.filing-card').count() === 12)
    check('Yahoo source label', await page.getByText(/Yahoo Finance\/yfinance/).isVisible())
    check('Announcement date is unavailable, not invented', (await page.locator('.filing-card').first().innerText()).includes('Announcement date unavailable'))
    check('Coverage includes pending and unavailable listings', (await page.locator('.filing-access-note').innerText()).includes('16 exchange listings'))
    await page.screenshot({ path: 'docs/quarterly-results/filings-desktop.png' })
    await page.getByRole('button', { name: 'Next', exact: true }).click()
    await page.getByText('Page 2 of 2').waitFor()
    check('Second catalog page', await page.locator('.filing-card').count() === 4)
    await page.getByRole('button', { name: 'Previous', exact: true }).click()
    await page.getByRole('button', { name: 'View FIX history', exact: true }).click()
    const dialog = page.getByRole('dialog')
    await dialog.locator('tbody tr').first().waitFor()
    check('Company history and comparative columns', await dialog.locator('tbody tr').count() === 2 && (await dialog.innerText()).toLowerCase().includes('revenue yoy'))
    await page.keyboard.press('Escape')
    await page.getByLabel('Results exchange').selectOption('BSE')
    await page.waitForFunction(() => document.querySelectorAll('.filing-card').length === 1 && document.querySelector('.filing-card').textContent.includes('Fixture Pending'))
    check('BSE exchange filter and pending discovery state', await page.locator('.filing-card').count() === 1)
    await page.getByLabel('Results exchange').selectOption('')
    await page.getByLabel('Results data status').selectOption('unavailable')
    await page.getByText('Fixture Unavailable', { exact: true }).waitFor()
    check('Unavailable statements shown without fake numbers', await page.getByText(/Yahoo did not return usable quarterly statements/).isVisible())
    await page.getByLabel('Results data status').selectOption('error')
    await page.getByText('Fixture Retry', { exact: true }).waitFor()
    check('Retry state')
    await page.getByLabel('Results data status').selectOption('ready')
    await page.getByLabel('Filing market').selectOption('US')
    await page.waitForFunction(() => document.querySelectorAll('.filing-card').length === 1 && document.querySelector('.filing-card').textContent.includes('Fixture US Company'))
    check('Ready and market filters', await page.locator('.filing-card').count() === 1)
    await page.getByLabel('Search filings by company or ticker').fill('MISSING')
    await page.getByText('No exchange listings match this selection.').waitFor()
    await page.getByRole('button', { name: 'Clear filters' }).click()
    await page.locator('.filing-card').first().waitFor()
    check('Search and clear filters')
    mode = 'pending'; await reload()
    await page.getByText(/AI summary is queued or processing/).first().waitFor()
    check('AI pending retains numeric data', (await page.locator('.filing-card').first().innerText()).includes('2,000.00'))
    mode = 'failed'; await reload()
    await page.getByText(/AI summary unavailable/).first().waitFor()
    check('AI failure retains saved statements')
    mode = 'error'; await reload()
    await page.getByText('Company filings are temporarily unavailable.').waitFor()
    mode = 'ready'; await page.getByRole('button', { name: 'Try again' }).click()
    await page.locator('.filing-card').first().waitFor()
    check('API error recovery')
    await page.setViewportSize({ width: 390, height: 844 })
    await page.screenshot({ path: 'docs/quarterly-results/filings-mobile.png' })
    check('Mobile has no document overflow', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
    check('No browser runtime errors', errors.length === 0)
    fs.writeFileSync('docs/quarterly-results/filings-browser-verification.json', JSON.stringify({ synthetic: true, checks }, null, 2))
    console.log(`Passed ${checks.length} Yahoo catalog browser checks.`)
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })



