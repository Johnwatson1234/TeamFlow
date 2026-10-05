import { chromium } from 'playwright'

const BASE = 'http://localhost:5173'
const out = process.argv[2] || 'git-check.png'

const main = async () => {
  const browser = await chromium.launch()
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await ctx.newPage()
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await page.fill('input[type="password"]', '123456')
  const userInputs = await page.locator('input:not([type="password"])').all()
  for (const inp of userInputs) {
    if (await inp.isVisible().catch(() => false)) { await inp.fill('zhangsan'); break }
  }
  await page.click('button:has-text("登录")')
  await page.waitForURL(/\/projects/, { timeout: 15000 })
  await page.goto(`${BASE}/projects/1/git`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(800)
  const width = await page.evaluate(() => document.documentElement.scrollWidth)
  const vw = await page.evaluate(() => window.innerWidth)
  console.log('scrollWidth=', width, 'viewport=', vw, width <= vw + 1 ? 'OK no-hscroll' : 'OVERFLOW!')
  const tags = await page.$$eval('.score-tag', els => els.map(e => e.textContent))
  console.log('quality tags:', tags)
  await page.screenshot({ path: out })
  await browser.close()
}

main().catch((e) => { console.error(e); process.exit(1) })