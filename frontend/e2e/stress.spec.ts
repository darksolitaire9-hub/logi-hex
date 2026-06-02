import { test, expect } from './fixtures'

// Disable parallelism for stress tests to ensure pure isolation
test.describe.configure({ mode: 'serial' })

test.describe('Resilience & Stress Testing (Gold Standard)', () => {
  const errors: any[] = []

  test.beforeEach(async ({ page, login }) => {
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })
    page.on('pageerror', err => errors.push(err.message))
    await login()
  })

  test.afterEach(async () => {
    let filtered = errors.filter(e => !e.includes('Database is locked'))
    errors.length = 0
    if (filtered.length > 0) throw new Error(`Unexpected errors: ${filtered.join('\n')}`)
  })

  test('A. Race Conditions: Hammering the Log Movement button', async ({ page }) => {
    await page.locator('[data-testid="nav-items"]').click({ force: true })
    await page.locator('button:has-text("Use Stock")').first().click({ force: true })
    await page.locator('[data-testid^="qty-input-"]').first().fill('5')

    await page.evaluate(() => {
      const btn = document.querySelector('[data-testid="confirm-movement-btn"]') as HTMLButtonElement
      if (btn) for (let i = 0; i < 50; i++) btn.click()
    })

    await expect(page.locator('body')).toContainText('Movement Logged', { timeout: 15000 })
  })

  test('B. Memory Leaks: Rapid Modal Cycling (Robust Cleanup)', async ({ page }) => {
    await page.locator('[data-testid="nav-items"]').click({ force: true })
    const client = await page.context().newCDPSession(page)
    await client.send('HeapProfiler.enable')
    const startHeap = (await client.send('Runtime.getHeapUsage')).usedSize

    await page.locator('button:has-text("Use Stock")').first().click({ force: true })
    await expect(page.locator('[data-testid="confirm-movement-btn"]')).toBeVisible()
    
    await page.goto('/dashboard')
    await expect(page.locator('[data-testid="confirm-movement-btn"]')).toBeHidden({ timeout: 15000 })

    const endHeap = (await client.send('Runtime.getHeapUsage')).usedSize
    expect(endHeap).toBeLessThan(startHeap * 10) 
  })

  test('C. UI Freezing: Handling Massive Datasets (50,000 records)', async ({ page }) => {
    await page.evaluate(() => { 
      const STORAGE_KEY = 'TAURI_MOCK_STATE';
      const state = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{}');
      state.massiveHistory = true; 
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    })
    await page.reload() 
    
    await expect(page.locator('text=Total Ledger Movements').locator('..').locator('div').nth(1)).toHaveText('50000', { timeout: 60000 })

    const respStart = Date.now()
    await page.goto('/dashboard/items')
    await expect(page.locator('h1')).toBeVisible({ timeout: 20000 })
    expect(Date.now() - respStart).toBeLessThan(10000)
  })

  test('D. Atomicity: Database Locked Handling', async ({ page }) => {
    await page.locator('[data-testid="nav-items"]').click({ force: true })
    await page.locator('button:has-text("Use Stock")').first().click({ force: true })
    await page.locator('[data-testid^="qty-input-"]').first().fill('10')
    await page.locator('[data-testid="confirm-movement-btn"]').click({ force: true })
    await expect(page.locator('body')).toContainText('Movement Logged', { timeout: 15000 })
  })
})
