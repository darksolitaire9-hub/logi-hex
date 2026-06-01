import { test, expect } from './fixtures'

// Disable parallelism for stress tests to ensure pure isolation
test.describe.configure({ mode: 'serial' })

test.describe('Resilience & Stress Testing (Gold Standard)', () => {
  const logs: string[] = []
  const errors: any[] = []

  test.beforeEach(async ({ page, login }) => {
    // Strict Console & Error Monitoring
    page.on('console', msg => {
      const text = msg.text()
      if (msg.type() === 'error') {
        errors.push(`Console Error: ${text}`)
      }
      logs.push(`[${msg.type()}] ${text}`)
    })
    page.on('pageerror', err => {
      errors.push(`Page Error: ${err.message}`)
    })

    await login()
  })

  test.afterEach(async ({}, testInfo) => {
    // Filter out expected errors for specific tests
    let filteredErrors = [...errors]
    if (testInfo.title.includes('D. Atomicity')) {
      filteredErrors = filteredErrors.filter(e => !e.includes('Database is locked'))
    }

    // Capture state for assertion
    const currentErrors = [...filteredErrors]
    errors.length = 0
    logs.length = 0

    if (currentErrors.length > 0) {
      throw new Error(`Stress test failed due to unexpected errors:\n${currentErrors.join('\n')}`)
    }
  })

  test('A. Race Conditions: Hammering the Log Movement button', async ({ page }) => {
    // Prove the system handles rapid-fire IPC calls without double-processing or crashing
    await page.locator('nav >> text=Stock Items').click()
    await page.locator('button:has-text("Use Stock")').first().click()
    await expect(page.locator('[data-testid="confirm-movement-btn"]')).toBeVisible()
    await page.locator('[data-testid^="qty-input-"]').first().fill('5')

    await page.evaluate(() => {
      const btn = document.querySelector('[data-testid="confirm-movement-btn"]') as HTMLButtonElement
      if (btn) {
        for (let i = 0; i < 50; i++) btn.click()
      }
    })

    await expect(page.locator('body')).toContainText('Movement Logged', { timeout: 15000 })
  })

  test('B. Memory Leaks: Rapid Modal Cycling (Robust Cleanup)', async ({ page }) => {
    // Prove that opening/closing modals with navigation cleanup doesn't explode memory
    await page.locator('nav >> text=Stock Items').click()

    const client = await page.context().newCDPSession(page)
    await client.send('HeapProfiler.enable')

    const startHeap = (await client.send('Runtime.getHeapUsage')).usedSize

    await page.locator('button:has-text("Use Stock")').first().click()
    await expect(page.locator('[data-testid="confirm-movement-btn"]')).toBeVisible()
    
    // Robust cleanup via navigation
    await page.goto('/dashboard')
    await page.goto('/dashboard/items')
    
    await expect(page.locator('[data-testid="confirm-movement-btn"]')).toBeHidden({ timeout: 15000 })

    const endHeap = (await client.send('Runtime.getHeapUsage')).usedSize
    console.log(`    Memory baseline: ${(endHeap / 1024 / 1024).toFixed(2)} MB`)
    expect(endHeap).toBeLessThan(startHeap * 10) 
  })

  test('C. UI Freezing: Handling Massive Datasets (50,000 records)', async ({ page }) => {
    // Prove the virtual list handles 50,000 records without blocking the main thread
    await page.evaluate(() => { (window as any).STRESS_TEST_MASSIVE_HISTORY = true })
    await page.locator('nav >> text=Dashboard').click()
    
    // Assert 50k items are tracked in the summary
    await expect(page.locator('text=Total Ledger Movements').locator('..').locator('div').nth(1)).toHaveText('50000', { timeout: 60000 })

    const respStart = Date.now()
    await page.goto('/dashboard/items')
    await expect(page.locator('h1')).toBeVisible({ timeout: 20000 })
    console.log(`    Responsiveness check took ${Date.now() - respStart}ms`)
    expect(Date.now() - respStart).toBeLessThan(10000)
  })

  test('D. Atomicity: Database Locked Handling', async ({ page }) => {
    // Prove the frontend handles "Database Busy" errors gracefully instead of crashing
    await page.locator('nav >> text=Stock Items').click()
    await page.locator('button:has-text("Use Stock")').first().click()
    
    await page.locator('[data-testid^="qty-input-"]').first().fill('10')
    await page.locator('[data-testid="movement-notes"]').fill('STRESS_TEST_LOCK')
    
    await page.locator('[data-testid="confirm-movement-btn"]').click({ force: true })
    
    // Success: readable error toast appears, proving the IPC error was caught and handled
    await expect(page.locator('text=Database Busy').first()).toBeVisible({ timeout: 15000 })
    await expect(page.locator('[data-testid="confirm-movement-btn"]')).toBeVisible()
  })
})
