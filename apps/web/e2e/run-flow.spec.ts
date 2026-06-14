import { expect, test } from "@playwright/test";

test("core run flow: open dashboard → pick incident → run → rail completes with a plan", async ({
  page,
}) => {
  // The app is open — no password. Go straight to the run page.
  await page.goto("/dashboard/run");

  // Choose a straight-through (no-approval) curated incident.
  await page.getByRole("combobox").click();
  await page.getByRole("option", { name: /Impossible-travel/i }).click();

  // Start the run.
  await page.getByRole("button", { name: "Run" }).click();

  // The five-agent rail and the synthesized plan appear once polling completes.
  await expect(page.getByText("Incident Response").first()).toBeVisible();
  await expect(page.getByText("Completed")).toBeVisible();
  // The plan renders in the Response-plan <pre> block.
  await expect(page.locator("pre").filter({ hasText: /Response plan for/ })).toBeVisible();
});
