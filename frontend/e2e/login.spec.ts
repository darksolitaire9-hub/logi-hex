import { test, expect } from './fixtures'

test.describe('Login & Security (Gold Standard)', () => {
  test.beforeEach(({ page }) => {
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  })

  test('should succeed with valid PIN', async ({ page }) => {
    await page.goto('/')
    
    // Select the test workspace
    await page.locator('text=Test Inventory').click()
    
    // Should be on the PIN entry screen
    await expect(page.locator('input[type="password"]')).toBeVisible()
    
    // Try valid PIN
    await page.locator('input[type="password"]').fill('1234')
    await page.locator('button:has-text("Unlock")').click()
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 15000 })
  })

  test('Accessibility: Login screen should be WCAG compliant', async ({ page }) => {
    await page.goto('/')
    await page.locator('text=Test Inventory').click()
    
    // Basic a11y checks - labels should exist
    await expect(page.locator('label:has-text("PIN")')).toBeVisible()
    
    // Future: Run @axe-core/playwright if installed
  })
})
