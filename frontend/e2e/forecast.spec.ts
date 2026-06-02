import { test, expect } from './fixtures'

test.describe('Forecasting (Gold Standard)', () => {
  test.beforeEach(async ({ login }) => {
    await login()
  })

  test('should generate a forecast', async ({ page }) => {
    await page.locator('[data-testid="nav-forecast"]').click({ force: true })
    
    // Select an item by value
    await page.locator('select').selectOption('item-1')

    // Generate Forecast
    await page.locator('button:has-text("Generate Forecast")').click({ force: true })

    // Verify results appear
    await expect(page.locator('text=Forecast Trajectory')).toBeVisible()
  })

  test('Resilience: Rapid navigation during forecasting', async ({ page }) => {
    await page.locator('[data-testid="nav-forecast"]').click({ force: true })
    await page.locator('select').selectOption('item-1')

    // Start forecast
    await page.locator('button:has-text("Generate Forecast")').click({ force: true })

    // Immediately navigate away
    await page.locator('[data-testid="nav-settings"]').click({ force: true })
    
    // UI should not crash
    await expect(page.locator('text=Restricted Area')).toBeVisible()
  })
})
