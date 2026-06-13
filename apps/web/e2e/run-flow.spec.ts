import { expect, test } from "@playwright/test";

const PASSWORD = process.env.DEMO_PASSWORD ?? "changeme";

test("core run flow: unlock → pick incident → run → rail completes with a plan", async ({
  page,
}) => {
  await page.goto("/dashboard/run");

  // One-time password gate.
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Unlock" }).click();

  // The run page loads; choose a straight-through (no-approval) curated incident.
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
