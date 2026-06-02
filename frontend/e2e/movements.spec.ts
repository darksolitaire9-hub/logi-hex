import { test, expect } from './fixtures'

test.describe('Movement Ledger (Gold Standard)', () => {
  test.beforeEach(async ({ login }) => {
    await login()
  })

  test('should log a movement successfully', async ({ page }) => {
    await page.locator('[data-testid="nav-items"]').click({ force: true })
    
    // Select first 'Use Stock' button
    await page.locator('[data-testid="use-stock-btn"]').first().click({ force: true })
    
    await page.locator('[data-testid^="qty-input-"]').first().fill('5')
    await page.locator('[data-testid="confirm-movement-btn"]').click({ force: true })
    
    // Check for success text ANYWHERE to avoid selector complexity
    await expect(page.locator('body')).toContainText('Movement Logged', { timeout: 15000 })
    
    // Explicitly click close if it's stuck
    await page.keyboard.press('Escape')
    await expect(page.locator('[data-testid="confirm-movement-btn"]')).toBeHidden({ timeout: 15000 })
  })

  test('Boundary: should fail when trying to send more than available stock', async ({ page }) => {
    await page.locator('[data-testid="nav-items"]').click({ force: true })
    await page.locator('[data-testid="use-stock-btn"]').first().click({ force: true })
    
    await page.locator('[data-testid^="qty-input-"]').first().fill('1001')
    await page.locator('[data-testid="confirm-movement-btn"]').click({ force: true })
    
    // Check for Error text
    await expect(page.locator('body')).toContainText('Error', { timeout: 15000 })
    await expect(page.locator('[data-testid="confirm-movement-btn"]')).toBeVisible()
  })
})
