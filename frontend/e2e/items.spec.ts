import { test, expect } from './fixtures'

test.describe('Catalog Management (Gold Standard)', () => {
  test.beforeEach(async ({ login }) => {
    await login()
  })

  test('should create and then edit an item', async ({ page }) => {
    await page.locator('[data-testid="nav-items"]').click({ force: true })
    await expect(page).toHaveURL(/.*dashboard\/items/)

    // 1. Create
    await page.locator('[data-testid="add-item-btn"]').click({ force: true })
    await page.locator('[data-testid="item-label-input"]').fill('Steel Crate')
    await page.locator('[data-testid="item-unit-select"]').selectOption('Pieces')
    await page.locator('[data-testid="submit-item-btn"]').click({ force: true })
    
    // Success
    await expect(page.locator('h3').filter({ hasText: 'Steel Crate' }).first()).toBeVisible({ timeout: 10000 })

    // 2. Edit
    await page.locator('h3:has-text("Steel Crate") >> button').first().click({ force: true })
    await expect(page.locator('text=Edit Item')).toBeVisible()
    
    await page.locator('[data-testid="edit-item-label-input"]').fill('Titanium Crate')
    await page.locator('[data-testid="save-item-btn"]').click({ force: true })
    
    // Verify update
    await expect(page.locator('h3').filter({ hasText: 'Titanium Crate' }).first()).toBeVisible()
  })

  test('Cascade: stock display updates after movement', async ({ page }) => {
    await page.locator('[data-testid="nav-items"]').click({ force: true })
    
    // Initial stock
    await expect(page.locator('div.lh-card:has(h3:has-text("Coffee Beans"))').locator('[data-testid="stock-display"]').first()).toHaveText(/50/)

    // Log a "Receive" movement
    await page.locator('div.lh-card:has(h3:has-text("Coffee Beans"))').locator('[data-testid="receive-stock-btn"]').first().click({ force: true })
    await page.locator('[data-testid="qty-input-item-1"]').fill('25')
    await page.locator('[data-testid="confirm-movement-btn"]').click({ force: true })

    // Check for success message
    await expect(page.locator('text=Movement Logged').first()).toBeVisible()

    // Stock should now be 75
    await expect(page.locator('div.lh-card:has(h3:has-text("Coffee Beans"))').locator('[data-testid="stock-display"]').first()).toHaveText(/75/)
  })
})
