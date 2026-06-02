import { test, expect } from './fixtures'

test.describe('Localization (i18n) Elasticity & Integrity', () => {
  // Use the fixture to see if it causes the failure
  test.beforeEach(async ({ login }) => {
    await login()
  })

  test('Application does not leak raw keys in dashboard (Negative Pertinent)', async ({ page }) => {
    // Check if we are on dashboard
    await expect(page).toHaveURL(/.*dashboard/)
    
    // Negative Pertinent: Ensure the raw keys are NOT visible anywhere
    await expect(page.locator('body')).not.toContainText('catalog.title')
    await expect(page.locator('body')).not.toContainText('login.buttons.unlock')

    // Navigate to Items
    await page.locator('[data-testid="nav-items"]').click({ force: true })
    
    // Verify dashboard translation
    await expect(page.locator('h1')).toContainText('Catalog')
  })
})
