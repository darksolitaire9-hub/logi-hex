import { test, expect } from './fixtures'

test.describe('Workspace Onboarding E2E Flow', () => {
  test.beforeEach(({ page }) => {
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
    page.on('pageerror', err => console.error('BROWSER ERROR:', err.message));
  });

  test('should allow creating a workspace and redirect to select it', async ({ page }) => {
    // Navigate directly to onboarding
    await page.goto('/onboarding')

    // Confirm we are on onboarding page (give Vite dev server time to compile)
    await expect(page.locator('form')).toBeVisible({ timeout: 15000 })

    // Fill in the form fields by input types
    await page.locator('input[type="text"]').fill('Acme HQ')
    
    // Fill user PIN and admin PIN (passwords)
    const passwordInputs = page.locator('input[type="password"]')
    await passwordInputs.nth(0).fill('1234')
    await passwordInputs.nth(1).fill('5678')

    // Submit the form
    await page.locator('button[type="submit"]').click()

    // The form submission calls create_workspace and redirects to /
    // On /, we display the workspace list or unlock screen
    await page.waitForURL('**/')

    // Verify workspace selection list shows the newly created workspace 'Acme HQ'
    // Since index.vue has: <div class="font-medium text-[var(--lh-ink-primary)]">{{ ws.name }}</div>
    // inside workspace selection buttons, we expect 'Acme HQ' to be visible.
    await expect(page.locator('text=Acme HQ')).toBeVisible()
  })
})
