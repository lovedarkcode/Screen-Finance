// Verifies real local-backend data. Only authentication is mocked in this isolated browser.
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const fs = require('node:fs/promises')
const path = require('node:path')
const assert = require('node:assert/strict')

async function main() {
  const browser = await chromium.launch({ headless: true })
  const errors = [], passed = []
  const check = (label, value) => { assert.ok(value, label); passed.push(label) }
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
    await context.addInitScript(() => localStorage.setItem('access_token', 'isolated-public-data-review'))
    await context.route('**/api/v1/auth/me', route => route.fulfill({ json: { id: 'review', name: 'UI Review', email: 'ui@example.test' } }))
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    await page.goto(`${process.env.APP_URL || 'http://127.0.0.1:5174'}/stock/AAPL`)
    await page.getByRole('heading', { name: 'Apple Inc.', exact: true }).waitFor({ timeout: 45000 })
    await page.locator('#price-chart .recharts-surface').waitFor({ timeout: 45000 })
    await page.locator('.stock-metric-card').first().waitFor({ timeout: 60000 })
    await page.locator('#financials .recharts-surface').waitFor({ timeout: 60000 })
    check('Live Apple quote uses USD', (await page.locator('.stock-price').innerText()).startsWith('$'))
    check('Live fundamentals use dollar market values', (await page.locator('.stock-metric-grid').innerText()).includes('$'))
    check('Live quarterly financials use USD millions', (await page.locator('#financials h2').innerText()).includes('USD Millions'))
    await page.getByText('Financial statements', { exact: true }).click()
    await page.locator('.stock-statement-table tbody tr').first().waitFor()
    check('Live financial statements contain USD values', (await page.locator('.stock-statement-table').innerText()).includes('$'))
    await page.getByRole('button', { name: 'Search stocks and sectors' }).click()
    await page.getByLabel('Search company or symbol').fill('Microsoft')
    await page.getByRole('button', { name: /Microsoft.*MSFT/ }).click({ timeout: 30000 })
    await page.getByRole('heading', { name: 'Microsoft Corporation', exact: true }).waitFor({ timeout: 45000 })
    check('Live US company search opens Microsoft analysis', page.url().endsWith('/stock/MSFT'))
    check('No browser runtime errors with real data', errors.length === 0)
    await fs.writeFile(path.join(__dirname, 'live-browser-verification.json'), JSON.stringify({ passed, errors, marketDataFixtures: false, authenticationFixture: true }, null, 2))
    console.log(`${passed.length} live-market browser checks passed`)
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
