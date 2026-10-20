// Render saved real API evidence; authentication is mocked only in this browser context.
const { chromium } = require('C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const fs = require('node:fs')
const assert = require('node:assert/strict')
async function main() {
 const evidence = JSON.parse(fs.readFileSync('docs/quarterly-results/pipeline-live-verification.json', 'utf8'))
 const payload = evidence.api['/api/results'].body
 const browser = await chromium.launch({ headless: true })
 try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } })
  await context.addInitScript(() => localStorage.setItem('access_token','isolated-real-payload-render'))
  await context.route('**/api/v1/**', route => {
   const path = new URL(route.request().url()).pathname
   return route.fulfill({ json: path.endsWith('/auth/me') ? { id: 1, name: 'Evidence', email: 'evidence@example.com' } : path.endsWith('/results') ? { ...payload, page_size: 12, items: payload.items.slice(0,12) } : [] })
  })
  const page = await context.newPage()
  const errors=[]
  page.on('pageerror', error=>errors.push(error.message))
  await page.goto('http://127.0.0.1:5186/results')
  await page.locator('.filing-card').first().waitFor()
  assert.equal(await page.locator('.filing-card').count(),12)
  assert((await page.locator('.filing-access-note').innerText()).includes(payload.coverage.listed.toLocaleString('en-US')))
  await page.screenshot({ path:'docs/quarterly-results/yahoo-live-desktop.png' })
  await page.setViewportSize({ width:390,height:844 })
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))
  await page.screenshot({ path:'docs/quarterly-results/yahoo-live-mobile.png' })
  assert.deepEqual(errors,[])
  console.log('Saved real Yahoo API payload renders correctly at desktop and mobile widths.')
 } finally { await browser.close() }
}
main().catch(error=>{console.error(error);process.exitCode=1})
