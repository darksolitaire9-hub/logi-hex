import { test, expect } from './fixtures'

test.describe('Localization (i18n) Elasticity & Integrity', () => {

  test('Application does not leak raw keys in default locale (Negative Pertinent)', async ({ page }) => {
    await page.goto('/')
    
    // Wait for the mock to load workspaces
    await page.waitForSelector('text=Test Inventory')
    
    // Negative Pertinent: Ensure the raw key is NOT visible anywhere on the body
    await expect(page.locator('body')).not.toContainText('login.buttons.unlock')

    // Click the workspace
    await page.locator('text=Test Inventory').click()

    // Verify default translation is active on the login screen
    await expect(page.locator('button:has-text("Unlock")')).toBeVisible()

    // Log in
    await page.locator('input[type="password"]').fill('1234')
    await page.locator('button[type="submit"]').click()
    await page.waitForURL(/.*dashboard/)

    // Verify dashboard translation
    await page.locator('nav >> text=Stock Items').click() 
    await expect(page.locator('h1')).toContainText('Catalog')

    // Negative Pertinent: Verify raw key is STILL not leaked after dynamic switch
    await expect(page.locator('body')).not.toContainText('catalog.title')
  })
})
