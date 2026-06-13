import { defineConfig, devices } from "@playwright/test";

/**
 * Local e2e gate for the core run flow. Requires the Phase 3 API running separately
 * (MOCK_MODE=true, DEMO_PASSWORD set). The dev server is started/reused automatically.
 *
 *   cd backend && DEMO_PASSWORD=changeme uv run python -m secops.app serve
 *   cd apps/web && DEMO_PASSWORD=changeme npx playwright test
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 60_000 },
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
