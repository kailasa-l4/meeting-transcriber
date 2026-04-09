import { test, expect } from '@playwright/test'

test.describe('Approvals Inbox', () => {
  test('approvals page loads', async ({ page }) => {
    await page.goto('/approvals')
    await expect(page.locator('h1')).toContainText('Approval')
  })

  test('shows pending drafts count', async ({ page }) => {
    await page.goto('/approvals')
    // Should show "X drafts pending review" badge
    await expect(page.getByText(/draft.*pending review/i).first()).toBeVisible()
  })

  test('shows pending drafts in table', async ({ page }) => {
    await page.goto('/approvals')
    const content = page.locator('main')
    await expect(content).toBeVisible()
    // Should show the approval inbox table with lead names
    await expect(page.getByText(/lead name/i).or(page.getByText(/company/i)).first()).toBeVisible()
  })

  test('shows review links for pending drafts', async ({ page }) => {
    await page.goto('/approvals')
    // Each pending draft should have a "Review" link
    const reviewLink = page.getByText('Review').first()
    await expect(reviewLink).toBeVisible()
  })

  test('navigating to draft review', async ({ page }) => {
    await page.goto('/approvals')
    const reviewLink = page.locator('a[href*="/approvals/"]').first()
    if (await reviewLink.isVisible()) {
      await reviewLink.click()
      await expect(page).toHaveURL(/\/approvals\//)
    }
  })
})

test.describe('Draft Review', () => {
  test('shows lead context bar', async ({ page }) => {
    await page.goto('/approvals')
    const reviewLink = page.locator('a[href*="/approvals/"]').first()
    if (await reviewLink.isVisible()) {
      await reviewLink.click()
      // Should show lead name, company, country info
      await expect(page.getByText(/lead/i).first()).toBeVisible()
      await expect(page.getByText(/country/i).first()).toBeVisible()
    }
  })

  test('shows email preview section', async ({ page }) => {
    await page.goto('/approvals')
    const reviewLink = page.locator('a[href*="/approvals/"]').first()
    if (await reviewLink.isVisible()) {
      await reviewLink.click()
      await expect(page.getByText(/email preview/i)).toBeVisible()
    }
  })

  test('shows action buttons', async ({ page }) => {
    await page.goto('/approvals')
    const reviewLink = page.locator('a[href*="/approvals/"]').first()
    if (await reviewLink.isVisible()) {
      await reviewLink.click()
      // Should show Approve & Send, Request Changes, and Reject buttons
      await expect(page.getByText(/approve/i).first()).toBeVisible()
      await expect(page.getByText(/request changes/i).first()).toBeVisible()
      await expect(page.getByText(/reject/i).first()).toBeVisible()
    }
  })

  test('back link returns to approvals list', async ({ page }) => {
    await page.goto('/approvals')
    const reviewLink = page.locator('a[href*="/approvals/"]').first()
    if (await reviewLink.isVisible()) {
      await reviewLink.click()
      await expect(page).toHaveURL(/\/approvals\//)
      const backLink = page.getByText(/back to approvals/i)
      if (await backLink.isVisible()) {
        await backLink.click()
        await expect(page).toHaveURL('/approvals')
      }
    }
  })

  test('shows version history sidebar', async ({ page }) => {
    await page.goto('/approvals')
    const reviewLink = page.locator('a[href*="/approvals/"]').first()
    if (await reviewLink.isVisible()) {
      await reviewLink.click()
      // Should show version history
      await expect(page.getByText(/version/i).first()).toBeVisible()
    }
  })
})
