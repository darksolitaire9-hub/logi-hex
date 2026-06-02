import { test, expect } from './fixtures'

test.describe('Settings & Configuration (Gold Standard)', () => {
  test.beforeEach(async ({ login }) => {
    await login()
  })

  test('should protect settings with Admin PIN', async ({ page }) => {
    await page.locator('[data-testid="nav-settings"]').click({ force: true })
    await expect(page.locator('text=Restricted Area')).toBeVisible()

    // Try wrong PIN
    await page.locator('input[type="password"]').fill('0000')
    await page.locator('button:has-text("Unlock Settings")').click({ force: true })
    await expect(page.locator('text=Invalid PIN')).toBeVisible()

    // Correct PIN (5678 from mock)
    await page.locator('input[type="password"]').fill('5678')
    await page.locator('button:has-text("Unlock Settings")').click({ force: true })

    await expect(page.locator('text=Enterprise Settings')).toBeVisible()
  })

  test('should switch workspace mode and affect UI', async ({ page }) => {
    // 1. Unlock settings
    await page.locator('[data-testid="nav-settings"]').click({ force: true })
    await page.locator('input[type="password"]').fill('5678')
    await page.locator('button:has-text("Unlock Settings")').click({ force: true })

    // 2. Switch to Accounts mode
    await page.locator('button:has-text("Accounts")').click({ force: true })

    // 3. Verify Dashboard/Items UI change
    // Should see 'Clients' link in sidebar now
    await expect(page.locator('[data-testid="nav-clients"]')).toBeVisible()
    
    // Should NOT see 'Forecasting' anymore
    await expect(page.locator('[data-testid="nav-forecast"]')).toBeHidden()
  })
})
