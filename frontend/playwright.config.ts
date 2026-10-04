import { defineConfig } from "@playwright/test";
import path from "node:path";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  use: { baseURL: "http://127.0.0.1:5173", trace: "retain-on-failure", channel: process.env.PLAYWRIGHT_CHANNEL },
  webServer: [
    {
      command: process.platform === "win32"
        ? "..\\.venv\\Scripts\\python.exe -m app.start"
        : "python -m app.start",
      cwd: "../backend",
      url: "http://127.0.0.1:8000/ready",
      reuseExistingServer: false,
      env: {
        // Dedicated synthetic E2E database; do not touch a developer's database.
        DATABASE_URL: `sqlite:///${path.resolve("../backend/e2e.db").replaceAll("\\", "/")}`,
        DEMO_MODE: "true", DEBUG: "false", ENVIRONMENT: "test", GROQ_API_KEY: "",
        ADMIN_EMAIL: "", ADMIN_PASSWORD: "", PORT: "8000",
      },
      timeout: 120000,
    },
    { command: "npm run dev -- --host 127.0.0.1", url: "http://127.0.0.1:5173", reuseExistingServer: false },
  ],
});
