import { test, expect } from './fixtures'

test.describe('Client Management (Gold Standard)', () => {
  test.beforeEach(async ({ page, login }) => {
    // THEORY OF CONSTRAINTS: Mutate the persistent storage BEFORE login reloads the page
    await page.addInitScript(() => {
      const STORAGE_KEY = 'TAURI_MOCK_STATE';
      const existing = sessionStorage.getItem(STORAGE_KEY);
      const state = existing ? JSON.parse(existing) : { workspaces: [{ id: 'ws-1', name: 'Test Inventory', mode: 'INVENTORY' }] };
      state.mode = 'ACCOUNTS';
      if (state.workspaces && state.workspaces.length > 0) {
        state.workspaces[0].mode = 'ACCOUNTS';
      }
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    })
    await login()
  })

  test('should create a new client and show it in the list', async ({ page }) => {
    await page.locator('[data-testid="nav-clients"]').click({ force: true })
    await page.locator('button:has-text("Add Client")').click({ force: true })
    await page.locator('input[placeholder="e.g., Acme Corp"]').fill('Cyberdyne Systems')
    await page.locator('button:has-text("Create Client")').click({ force: true })
    await expect(page.locator('h3').filter({ hasText: 'Add New Client' })).toBeHidden()
    await expect(page.locator('text=Cyberdyne Systems')).toBeVisible()
  })

  test('should search for clients', async ({ page }) => {
    await page.locator('[data-testid="nav-clients"]').click({ force: true })
    await expect(page.locator('text=Acme Corp')).toBeVisible()
    await page.locator('input[placeholder="Search clients..."]').fill('NonExistent')
    await expect(page.locator('text=Acme Corp')).toBeHidden()
    await page.locator('input[placeholder="Search clients..."]').fill('Acme')
    await expect(page.locator('text=Acme Corp')).toBeVisible()
  })
})
