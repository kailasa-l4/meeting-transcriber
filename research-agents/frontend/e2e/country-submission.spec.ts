import { test, expect } from '@playwright/test'

test.describe('Country Submission', () => {
  test('navigates to country form via sidebar', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Country Run')
    await expect(page).toHaveURL('/country/new')
    await expect(page.locator('h1')).toContainText('New Country')
  })

  test('country field is required', async ({ page }) => {
    await page.goto('/country/new')
    const submitBtn = page.getByRole('button', { name: /submit country run/i })
    await expect(submitBtn).toBeVisible()
  })

  test('shows validation error when submitting empty form', async ({ page }) => {
    await page.goto('/country/new')
    const submitBtn = page.getByRole('button', { name: /submit country run/i })
    await submitBtn.click()
    // Should show "Country is required" error
    await expect(page.getByText(/country is required/i)).toBeVisible()
  })

  test('shows advanced options when expanded', async ({ page }) => {
    await page.goto('/country/new')
    const advancedToggle = page.getByText(/advanced options/i)
    await expect(advancedToggle).toBeVisible()
    await advancedToggle.click()
    // Should show additional fields like target types, regions, etc.
    await expect(page.getByLabel(/target types/i)).toBeVisible()
    await expect(page.getByLabel(/regions/i)).toBeVisible()
    await expect(page.getByLabel(/language preference/i)).toBeVisible()
    await expect(page.getByLabel(/outreach tone/i)).toBeVisible()
  })

  test('hides advanced options when toggled off', async ({ page }) => {
    await page.goto('/country/new')
    const advancedToggle = page.getByText(/show advanced options/i)
    await advancedToggle.click()
    await expect(page.getByLabel(/target types/i)).toBeVisible()
    // Toggle off
    const hideToggle = page.getByText(/hide advanced options/i)
    await hideToggle.click()
    await expect(page.getByLabel(/target types/i)).not.toBeVisible()
  })

  test('submits form successfully with valid country', async ({ page }) => {
    await page.goto('/country/new')
    await page.getByLabel(/country/i).fill('Ghana')
    await page.getByRole('button', { name: /submit country run/i }).click()
    // Should show success message
    await expect(page.getByText(/submitted successfully/i)).toBeVisible()
    await expect(page.getByText('Ghana')).toBeVisible()
  })

  test('can submit another run after success', async ({ page }) => {
    await page.goto('/country/new')
    await page.getByLabel(/country/i).fill('Kenya')
    await page.getByRole('button', { name: /submit country run/i }).click()
    await expect(page.getByText(/submitted successfully/i)).toBeVisible()
    // Click "Submit another"
    await page.getByRole('button', { name: /submit another/i }).click()
    // Should show the form again with empty fields
    await expect(page.getByLabel(/country/i)).toBeVisible()
    await expect(page.getByLabel(/country/i)).toHaveValue('')
  })
})
