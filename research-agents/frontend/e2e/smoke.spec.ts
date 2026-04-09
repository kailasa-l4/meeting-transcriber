import { test, expect } from '@playwright/test'

test('homepage loads with dashboard title', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('h1')).toContainText('Dashboard')
})

test('navigation sidebar is visible', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Sessions')).toBeVisible()
  await expect(page.getByText('Leads')).toBeVisible()
  await expect(page.getByText('Approvals')).toBeVisible()
})
