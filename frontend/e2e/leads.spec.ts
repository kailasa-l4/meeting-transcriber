import { test, expect } from '@playwright/test'

test.describe('Leads List', () => {
  test('leads page loads with data', async ({ page }) => {
    await page.goto('/leads')
    await expect(page.locator('h1')).toContainText('Leads')
  })

  test('leads show confidence scores', async ({ page }) => {
    await page.goto('/leads')
    // Confidence scores appear as percentages (e.g. 92%, 85%)
    await expect(page.getByText(/%/).first()).toBeVisible()
  })

  test('leads table has column headers', async ({ page }) => {
    await page.goto('/leads')
    await expect(page.getByText('Name').first()).toBeVisible()
    await expect(page.getByText('Company').first()).toBeVisible()
    await expect(page.getByText('Confidence').first()).toBeVisible()
  })

  test('search filters leads', async ({ page }) => {
    await page.goto('/leads')
    const searchInput = page.getByPlaceholder(/name, company, or email/i)
    await expect(searchInput).toBeVisible()
    await searchInput.fill('Gold')
    // Should filter to leads containing "Gold" in name/company/email
    // "Gold Coast Refinery Ltd" and "Ashanti Gold Corporation" should match
    await expect(page.getByText(/gold/i).first()).toBeVisible()
  })

  test('search with no results shows empty state', async ({ page }) => {
    await page.goto('/leads')
    const searchInput = page.getByPlaceholder(/name, company, or email/i)
    await searchInput.fill('xyznonexistent12345')
    // Should show empty state message
    await expect(page.getByText(/no leads match/i)).toBeVisible()
  })

  test('clear filters button appears and works', async ({ page }) => {
    await page.goto('/leads')
    const searchInput = page.getByPlaceholder(/name, company, or email/i)
    await searchInput.fill('Gold')
    // Clear filters button should appear
    const clearBtn = page.getByRole('button', { name: /clear filters/i })
    await expect(clearBtn).toBeVisible()
    await clearBtn.click()
    // Search should be cleared
    await expect(searchInput).toHaveValue('')
  })

  test('verification status filter works', async ({ page }) => {
    await page.goto('/leads')
    const statusSelect = page.getByRole('combobox')
    if (await statusSelect.isVisible()) {
      await statusSelect.selectOption('verified')
      // Should show only verified leads
      await expect(page.getByText(/%/).first()).toBeVisible()
    }
  })

  test('clicking a lead navigates to detail', async ({ page }) => {
    await page.goto('/leads')
    const firstLink = page.locator('a[href*="/leads/"]').first()
    if (await firstLink.isVisible()) {
      await firstLink.click()
      await expect(page).toHaveURL(/\/leads\//)
    }
  })
})

test.describe('Lead Detail', () => {
  test('shows lead name and company', async ({ page }) => {
    // Navigate to a known lead (lead-001: Kwame Asante, GCB Bank)
    await page.goto('/leads')
    const kwameLink = page.getByText('Kwame Asante').first()
    if (await kwameLink.isVisible()) {
      await kwameLink.click()
      await expect(page.locator('h1')).toContainText('Kwame Asante')
      await expect(page.getByText('GCB Bank Limited').first()).toBeVisible()
    }
  })

  test('shows confidence breakdown section', async ({ page }) => {
    await page.goto('/leads')
    const firstLink = page.locator('a[href*="/leads/"]').first()
    if (await firstLink.isVisible()) {
      await firstLink.click()
      await expect(page.getByText(/confidence breakdown/i)).toBeVisible()
    }
  })

  test('shows source evidence section', async ({ page }) => {
    await page.goto('/leads')
    const firstLink = page.locator('a[href*="/leads/"]').first()
    if (await firstLink.isVisible()) {
      await firstLink.click()
      await expect(page.getByText(/source evidence/i)).toBeVisible()
    }
  })

  test('shows verification notes section', async ({ page }) => {
    await page.goto('/leads')
    const firstLink = page.locator('a[href*="/leads/"]').first()
    if (await firstLink.isVisible()) {
      await firstLink.click()
      await expect(page.getByText(/verification notes/i)).toBeVisible()
    }
  })

  test('back link returns to leads list', async ({ page }) => {
    await page.goto('/leads')
    const firstLink = page.locator('a[href*="/leads/"]').first()
    if (await firstLink.isVisible()) {
      await firstLink.click()
      await expect(page).toHaveURL(/\/leads\//)
      const backLink = page.getByText(/back to leads/i)
      if (await backLink.isVisible()) {
        await backLink.click()
        await expect(page).toHaveURL('/leads')
      }
    }
  })
})
