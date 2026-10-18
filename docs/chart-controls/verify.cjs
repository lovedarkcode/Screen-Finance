const { chromium } = require('C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
async function main() {
  const browser = await chromium.launch({ headless: true })
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
    await context.addInitScript(() => localStorage.setItem('access_token', 'chart-test'))
    let peEmpty = false
    const requests = []
    await context.route('**/api/v1/**', route => {
      const url = new URL(route.request().url())
      const endpoint = decodeURIComponent(url.pathname)
      const ok = json => route.fulfill({ json })
      if (endpoint.endsWith('/auth/me')) return ok({ id: 1, name: 'Test', email: 'test@example.test' })
      if (endpoint.endsWith('/chart')) {
        requests.push(url.searchParams.get('range'))
        assert.equal(url.searchParams.get('indicators'), 'true')
        return ok(Array.from({ length: 120 }, (_, i) => ({ date: new Date(Date.now() - (120-i)*86400000).toISOString(), price: 100+i, dma50: 80+i, dma100: 60+i, volume: 10000+i*10 })))
      }
      if (endpoint.endsWith('/pe-history')) return ok(peEmpty ? [] : [{ date: new Date().toISOString(), pe: 20 }])
      if (endpoint.endsWith('/news')) return ok({ items: [] })
      if (endpoint.endsWith('/sectors')) return ok([])
      if (endpoint.includes('/stocks/')) return ok({ price: 200, symbol: endpoint.split('/').pop(), name: 'Fixture', changePercent: 1, date: new Date().toISOString() })
      return ok([])
    })
    const page = await context.newPage()
    const errors = []
    page.on('pageerror', e => errors.push(e.message))
    await page.goto('http://127.0.0.1:5178/feed')
    const chart = page.locator('#price-chart')
    await chart.locator('.recharts-line').first().waitFor()
    assert.equal(await chart.locator('.recharts-line').count(), 3)
    for (const name of ['50 DMA', '100 DMA', 'Price', 'Volume']) {
      const button = chart.getByRole('group', { name: 'Chart overlays' }).getByRole('button', { name, exact: true })
      assert.equal(await button.getAttribute('aria-pressed'), 'true')
      await button.click()
      assert.equal(await button.getAttribute('aria-pressed'), 'false')
      await button.click()
    }
    for (const name of ['1M', '6M', '1Yr', '3Yr', '5Yr', '10Yr', 'Max']) {
      await chart.getByRole('button', { name, exact: true }).click()
      await chart.locator('.recharts-line').first().waitFor()
    }
    assert(requests.includes('3Y') && requests.includes('Max'))
    await chart.getByRole('button', { name: 'P/E Ratio', exact: true }).click()
    await chart.locator('.recharts-line-dot').waitFor(); await chart.screenshot({ path: 'docs/chart-controls/pe-debug.png' })
    assert.equal(await chart.locator('.recharts-line').count(), 1)
    await chart.getByRole('button', { name: 'Price', exact: true }).click()
    await chart.locator('.recharts-line').first().waitFor()
    await chart.getByRole('button', { name: 'Alerts', exact: true }).click()
    await page.getByLabel('Target price (INR)').fill('150')
    await page.getByRole('button', { name: 'Save alert', exact: true }).click()
    await chart.getByText(/Alert reached/).waitFor()
    assert.equal(await page.evaluate(() => JSON.parse(localStorage.getItem('chart-alert:^NSEI')).triggered), true)
    await chart.getByRole('button', { name: 'Alerts (1)', exact: true }).click()
    await page.getByRole('button', { name: 'Remove alert', exact: true }).click()
    assert.equal(await page.evaluate(() => localStorage.getItem('chart-alert:^NSEI')), null)
    await page.getByRole('button', { name: 'Close', exact: true }).click()
    await chart.screenshot({ path: 'docs/chart-controls/desktop.png' })
    await page.setViewportSize({ width: 390, height: 844 })
    await chart.scrollIntoViewIfNeeded()
    await chart.screenshot({ path: 'docs/chart-controls/mobile.png' })
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
    peEmpty = true
    await chart.getByRole('button', { name: 'P/E Ratio', exact: true }).click()
    await chart.getByText('No recorded P/E snapshots in this timeframe.').waitFor()
    assert.deepEqual(errors, [])
    console.log('Chart browser checks passed: overlays, ranges, P/E, empty state, alert save/trigger/remove, mobile overflow, no runtime errors.')
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })


