import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('sidebar links work', async ({ page }) => {
    await page.goto('/')

    await page.click('text=Sessions')
    await expect(page).toHaveURL('/sessions')

    await page.click('text=Leads')
    await expect(page).toHaveURL('/leads')

    await page.click('text=Approvals')
    await expect(page).toHaveURL('/approvals')

    await page.click('text=Dashboard')
    await expect(page).toHaveURL('/')
  })

  test('dashboard shows stat cards', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText(/total sessions/i).first()).toBeVisible()
    await expect(page.getByText(/total leads/i).first()).toBeVisible()
    await expect(page.getByText(/pending approvals/i).first()).toBeVisible()
  })

  test('dashboard shows recent sessions section', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText(/recent sessions/i)).toBeVisible()
    await expect(page.getByText(/view all/i)).toBeVisible()
  })

  test('dashboard recent sessions link to detail', async ({ page }) => {
    await page.goto('/')
    const sessionLink = page.locator('a[href*="/sessions/"]').first()
    if (await sessionLink.isVisible()) {
      await sessionLink.click()
      await expect(page).toHaveURL(/\/sessions\//)
    }
  })

  test('dashboard view all link goes to sessions', async ({ page }) => {
    await page.goto('/')
    const viewAll = page.getByText(/view all/i)
    await expect(viewAll).toBeVisible()
    await viewAll.click()
    await expect(page).toHaveURL('/sessions')
  })

  test('sidebar is visible on all pages', async ({ page }) => {
    const pages = ['/', '/sessions', '/leads', '/approvals', '/country/new']
    for (const url of pages) {
      await page.goto(url)
      await expect(page.getByText('Gold Leads')).toBeVisible()
      await expect(page.getByText('Dashboard')).toBeVisible()
      await expect(page.getByText('Sessions')).toBeVisible()
      await expect(page.getByText('Leads')).toBeVisible()
      await expect(page.getByText('Approvals')).toBeVisible()
    }
  })

  test('new country run link in sidebar works', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Country Run')
    await expect(page).toHaveURL('/country/new')
    await expect(page.locator('h1')).toContainText('New Country')
  })
})
