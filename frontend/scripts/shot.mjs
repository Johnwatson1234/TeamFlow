import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = resolve(__dirname, '../../docs/screenshots')
mkdirSync(OUT_DIR, { recursive: true })

const BASE = 'http://localhost:5173'
const USERNAME = 'zhangsan'
const PASSWORD = '123456'

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await page.fill('input[type="text"], input[placeholder*="用户名"], input[placeholder*="账号"]', USERNAME)
  await page.fill('input[type="password"]', PASSWORD)
  await page.click('button[type="submit"], .login-btn, button:has-text("登录")')
  await page.waitForURL(/\/projects(\/|$|\?)/, { timeout: 15000 })
}

async function shoot(page, route, out) {
  await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1200)
  await page.screenshot({ path: resolve(OUT_DIR, out) })
  console.log('saved', out)
}

const main = async () => {
  const browser = await chromium.launch()
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 })
  const page = await ctx.newPage()
  try {
    await login(page)
    // 截图 1：项目仪表盘（统计卡片 + 图表 + 风险，信息密度最高）
    await shoot(page, '/projects/1', 'dashboard.png')
    // 截图 2：知识图谱（AntV G6 可视化，最直观的差异化能力）
    await shoot(page, '/projects/1/graph', 'graph.png')
  } catch (e) {
    console.error('shot failed:', e.message)
    process.exitCode = 1
  } finally {
    await browser.close()
  }
}

main()
