const { chromium } = require('C:/Program Files/Python314/Lib/site-packages/playwright/driver/package')
const assert = require('node:assert/strict')
async function main() {
  const browser = await chromium.launch({ headless:true })
  let mode = 'loading', release
  const items = Array.from({length:6}, (_, i) => ({ id:String(i), title:'Market headline ' + (i+1), source:'Yahoo Finance', url:'https://example.com/article-' + i, published_at:'2026-10-19T08:00:00Z' }))
  try {
    const context = await browser.newContext({ viewport:{width:1440,height:1000}, reducedMotion:'reduce' })
    await context.addInitScript(() => localStorage.setItem('access_token','isolated-news-check'))
    await context.route('**/api/v1/**', async route => {
      const endpoint = decodeURIComponent(new URL(route.request().url()).pathname)
      if (endpoint.endsWith('/news')) {
        if (mode === 'loading') await new Promise(resolve => { release=resolve })
        if (mode === 'error') return route.fulfill({status:503,json:{detail:'Unavailable'}})
        return route.fulfill({json:{items:mode === 'empty' ? [] : items, stale:mode === 'stale', updated_at:'2026-10-19T08:05:00Z'}})
      }
      if (endpoint.endsWith('/auth/me')) return route.fulfill({json:{id:1,name:'Fixture',email:'fixture@example.com'}})
      if (endpoint.endsWith('/chart') || endpoint.endsWith('/sectors')) return route.fulfill({json:[]})
      return route.fulfill({json:{symbol:'TEST',name:'Fixture company',price:100,changePercent:1}})
    })
    const page = await context.newPage()
    const errors=[]
    page.on('pageerror',error => errors.push(error.message))
    await page.goto('http://127.0.0.1:5178/feed')
    const news = page.getByRole('region',{name:'Market news',exact:true})
    await news.getByLabel('Loading market news').waitFor()
    mode='ready'; release()
    await news.locator('.market-news-card').first().waitFor()
    assert.equal(await news.locator('.market-news-card').count(),6)
    assert(!(await news.innerText()).includes('Yahoo Finance'))
    assert.equal(await news.locator('time').count(),6)
    const first = news.locator('.market-news-card').first()
    assert.equal(await first.getAttribute('href'),'https://example.com/article-0')
    assert.equal(await first.getAttribute('target'),'_blank')
    assert((await first.getAttribute('rel')).includes('noopener'))
    await news.screenshot({path:'docs/market-news/desktop.png'})
    await page.setViewportSize({width:390,height:844})
    await news.screenshot({path:'docs/market-news/mobile.png'})
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
    mode='error'
    await news.getByRole('button',{name:'Refresh news'}).click()
    await news.getByText(/Showing previously fetched headlines/).waitFor()
    assert.equal(await news.locator('.market-news-card').count(),6)
    await page.reload()
    await news.getByText('Market news is temporarily unavailable.').waitFor()
    mode='ready'
    await news.getByRole('button',{name:'Try again'}).click()
    await news.locator('.market-news-card').first().waitFor()
    mode='stale'
    await news.getByRole('button',{name:'Refresh news'}).click()
    await news.getByText(/Showing previously fetched headlines/).waitFor()
    mode='empty'
    await page.reload()
    await news.getByText('No market headlines available right now').waitFor()
    assert.deepEqual(errors,[])
    console.log('Market news browser checks passed: loading, headlines, dates, article links, no provider label, mobile layout, retry, retained headlines, stale and empty states.')
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode=1 })
