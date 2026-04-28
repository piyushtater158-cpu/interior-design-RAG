import { test, expect } from '@playwright/test';

const LIVE = process.env.BACKEND_LIVE === '1';

test.beforeEach(async ({ page }) => {
  if (LIVE) return;
  await page.route('**/auth/magic-link', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ token: 'tkn-mock', user_id: 'u-mock' }),
    });
  });
  await page.route('**/admin/ab-config', (r) => r.fulfill({ status: 403, body: '' }));
});

test('landing → signin → workspace → room picker', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

  await page.getByRole('button', { name: /sign in to start/i }).click();
  await expect(page).toHaveURL(/\/signin$/);

  await page.getByLabel('Email').fill('test@demo.com');
  await page.getByRole('button', { name: /^sign in$/i }).click();

  await expect(page).toHaveURL(/\/app$/);

  await page.getByText('Bedroom', { exact: true }).first().click();
  await expect(page).toHaveURL(/\/app\/new\?type=bedroom/);
});
