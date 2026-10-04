import { expect, test } from "@playwright/test";

test("demo login, sample review, save, reopen, and logout", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Every complaint deserves a clear next step." })).toBeVisible();
  await page.screenshot({ path: "test-results/demo-desktop.png", fullPage: true });
  await page.getByRole("button", { name: "Enter demo", exact: true }).click();
  await expect(page.getByText("Live AI is unavailable", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Load synthetic sample (no AI call)", exact: true }).click();
  await page.getByRole("button", { name: "Save Complaint" }).click();
  const saved = page.getByText(/Complaint #\d+ saved successfully\./);
  await expect(saved).toBeVisible();
  const id = (await saved.innerText()).match(/#(\d+)/)![1];
  await page.getByRole("button", { name: "Saved complaints", exact: true }).click();
  await page.getByRole("button", { name: new RegExp(`Complaint #${id} ·`) }).click();
  const detail = page.getByRole("region", { name: "Complaint details" });
  await expect(detail.getByRole("heading", { name: `Complaint #${id}`, exact: true })).toBeVisible();
  // Seeded batch already has a complaint, so Low escalates to Medium.
  await expect(detail.getByText("Medium", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/demo-inbox.png", fullPage: true });
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("button", { name: "Enter demo", exact: true })).toBeVisible();
  await expect.poll(async () => (await page.request.get("/api/v1/complaints")).status()).toBe(401);
});

test("mobile landing fits the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Enter demo", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/demo-mobile.png", fullPage: true });
});
