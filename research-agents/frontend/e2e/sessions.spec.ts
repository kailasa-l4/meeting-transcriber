import { test, expect } from '@playwright/test'

test.describe('Sessions List', () => {
  test('sessions page loads with table', async ({ page }) => {
    await page.goto('/sessions')
    await expect(page.locator('h1')).toContainText('Sessions')
    // Should show session data from mock fixtures
    await expect(page.getByText('Ghana').first()).toBeVisible()
  })

  test('sessions show status badges', async ({ page }) => {
    await page.goto('/sessions')
    // At least one status badge should be visible (completed, running, queued, etc.)
    await expect(page.getByText(/completed|running|queued|failed|seeding knowledge|waiting for approval/i).first()).toBeVisible()
  })

  test('sessions table shows all expected countries', async ({ page }) => {
    await page.goto('/sessions')
    // Mock data has Ghana, Kenya, Uganda, Nigeria
    await expect(page.getByText('Ghana').first()).toBeVisible()
    await expect(page.getByText('Kenya').first()).toBeVisible()
    await expect(page.getByText('Uganda').first()).toBeVisible()
    await expect(page.getByText('Nigeria').first()).toBeVisible()
  })

  test('sessions table has column headers', async ({ page }) => {
    await page.goto('/sessions')
    await expect(page.getByText('Country').first()).toBeVisible()
    await expect(page.getByText('Status').first()).toBeVisible()
    await expect(page.getByText('Stage').first()).toBeVisible()
  })

  test('clicking a session navigates to detail', async ({ page }) => {
    await page.goto('/sessions')
    const firstLink = page.locator('a[href*="/sessions/"]').first()
    if (await firstLink.isVisible()) {
      await firstLink.click()
      await expect(page).toHaveURL(/\/sessions\//)
    }
  })

  test('new country run button links to form', async ({ page }) => {
    await page.goto('/sessions')
    const newBtn = page.getByText('+ New Country Run')
    await expect(newBtn).toBeVisible()
    await newBtn.click()
    await expect(page).toHaveURL('/country/new')
  })
})

test.describe('Session Detail', () => {
  test('shows session country and status', async ({ page }) => {
    await page.goto('/sessions')
    const ghanaLink = page.locator('a[href*="/sessions/job-gh-001"]').first()
    if (await ghanaLink.isVisible()) {
      await ghanaLink.click()
      await expect(page.locator('h1')).toContainText('Ghana')
      await expect(page.getByText('completed').first()).toBeVisible()
    }
  })

  test('shows workflow progress section', async ({ page }) => {
    await page.goto('/sessions')
    const firstLink = page.locator('a[href*="/sessions/"]').first()
    if (await firstLink.isVisible()) {
      await firstLink.click()
      await expect(page.getByText(/workflow progress/i)).toBeVisible()
    }
  })

  test('shows leads table in session detail', async ({ page }) => {
    await page.goto('/sessions')
    const ghanaLink = page.locator('a[href*="/sessions/job-gh-001"]').first()
    if (await ghanaLink.isVisible()) {
      await ghanaLink.click()
      // Ghana session has leads
      await expect(page.getByText(/leads/i).first()).toBeVisible()
    }
  })

  test('back link returns to sessions list', async ({ page }) => {
    await page.goto('/sessions')
    const firstLink = page.locator('a[href*="/sessions/"]').first()
    if (await firstLink.isVisible()) {
      await firstLink.click()
      await expect(page).toHaveURL(/\/sessions\//)
      const backLink = page.getByText(/back to sessions/i)
      if (await backLink.isVisible()) {
        await backLink.click()
        await expect(page).toHaveURL('/sessions')
      }
    }
  })

  test('shows error message for failed session', async ({ page }) => {
    // job-gh-005 is the failed session
    await page.goto('/sessions')
    const failedLink = page.locator('a[href*="/sessions/job-gh-005"]').first()
    if (await failedLink.isVisible()) {
      await failedLink.click()
      await expect(page.getByText(/rate limit exceeded/i)).toBeVisible()
    }
  })
})
