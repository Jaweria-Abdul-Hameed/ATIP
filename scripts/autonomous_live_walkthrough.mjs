import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUTPUT_DIR = path.resolve("C:/Users/Jaweria/.gemini/antigravity/brain/5297cf64-eab5-4fe9-af63-8878e967fa15/demo_screenshots");

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

async function runLiveWalkthrough() {
  console.log("Starting Autonomous Live Walkthrough...");
  console.log("Output Directory:", OUTPUT_DIR);

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--window-size=1440,900"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Sign In Page - Form Filling
  console.log("Step 1: Sign In - Filling authentication fields...");
  await page.goto("http://localhost:3000/sign-in", { waitUntil: "networkidle0" });
  await page.type('input[type="email"]', "lead.engineer@atip-autonomous.internal", { delay: 30 });
  await page.type('input[type="password"]', "SuperSecretPass2026!", { delay: 30 });
  await sleep(400);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "01_sign_in_filled.png"), fullPage: false });

  // 2. Settings Page - Profile & Execution Quotas form filling
  console.log("Step 2: Settings - Profile & Sandbox Quotas...");
  await page.goto("http://localhost:3000/app/settings?tab=profile", { waitUntil: "networkidle0" });
  await sleep(500);
  // Clear and type profile name
  const nameInput = await page.$('input[value="Jaweria Abdul Hameed"], input[placeholder="Your full name"], input[type="text"]');
  if (nameInput) {
    await nameInput.click({ clickCount: 3 });
    await nameInput.type("Jaweria Abdul Hameed (Lead Architect)", { delay: 20 });
  }
  await page.screenshot({ path: path.join(OUTPUT_DIR, "02_settings_profile_filled.png"), fullPage: false });

  // Settings: Execution & Sandbox Quotas tab
  await page.goto("http://localhost:3000/app/settings?tab=execution", { waitUntil: "networkidle0" });
  await sleep(500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "03_settings_execution_sandbox.png"), fullPage: false });

  // Settings: Team Members & RBAC
  await page.goto("http://localhost:3000/app/settings?tab=members", { waitUntil: "networkidle0" });
  await sleep(500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "04_settings_members_rbac.png"), fullPage: false });

  // 3. Repositories Screen - Search & Connect Repository Modal
  console.log("Step 3: Repositories List & Connect Modal...");
  await page.goto("http://localhost:3000/app/repositories", { waitUntil: "networkidle0" });
  await sleep(500);
  const repoSearch = await page.$('input[placeholder*="Search"], input[type="search"], input[type="text"]');
  if (repoSearch) {
    await repoSearch.type("dashboard", { delay: 30 });
  }
  await sleep(300);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "05_repositories_filtered.png"), fullPage: false });

  // Click Connect repository button to open modal dialog
  const connectBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent.includes("Connect repository") || b.textContent.includes("Connect"));
  });
  if (connectBtn && connectBtn.asElement()) {
    await connectBtn.asElement().click();
    await sleep(600);
    // Fill in modal inputs if any
    const modalInput = await page.$('div[role="dialog"] input, div.fixed input');
    if (modalInput) {
      await modalInput.type("Jaweria-Abdul-Hameed/ATIP", { delay: 25 });
    }
    await sleep(300);
    await page.screenshot({ path: path.join(OUTPUT_DIR, "06_connect_repo_modal_filled.png"), fullPage: false });
  }

  // 4. Repository Workspace Screen - All M3 Mining Tabs
  console.log("Step 4: Repository Workspace - Mined Data & Analysis CTA...");
  const workspaceUrl = "http://localhost:3000/app/repositories/nextjs-dashboard";
  await page.goto(workspaceUrl, { waitUntil: "networkidle0" });
  await sleep(500);

  // Tab: Overview
  await page.screenshot({ path: path.join(OUTPUT_DIR, "07_repo_tab_overview.png"), fullPage: false });

  // Tab: Commits
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button, a"));
    const commitTab = tabs.find((t) => t.textContent.includes("Commits"));
    if (commitTab) commitTab.click();
  });
  await sleep(500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "08_repo_tab_commits.png"), fullPage: false });

  // Tab: Files & Complexity
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button, a"));
    const filesTab = tabs.find((t) => t.textContent.includes("Files"));
    if (filesTab) filesTab.click();
  });
  await sleep(500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "09_repo_tab_files_complexity.png"), fullPage: false });

  // Tab: Dependencies
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button, a"));
    const depTab = tabs.find((t) => t.textContent.includes("Dependencies"));
    if (depTab) depTab.click();
  });
  await sleep(500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "10_repo_tab_dependencies.png"), fullPage: false });

  // Tab: Coverage Objectives
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button, a"));
    const covTab = tabs.find((t) => t.textContent.includes("Coverage"));
    if (covTab) covTab.click();
  });
  await sleep(500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "11_repo_tab_coverage.png"), fullPage: false });

  // Trigger "Analyze repository" CTA button
  console.log("Step 5: Triggering 'Analyze repository' CTA...");
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    const analyzeBtn = buttons.find((b) => b.textContent.includes("Analyze repository"));
    if (analyzeBtn) analyzeBtn.click();
  });
  await sleep(800);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "12_repo_analysis_triggered.png"), fullPage: false });

  // 5. Reports Screen - Interactive Trend Graph & CSV/JSON Export
  console.log("Step 6: Reports & Metrics Visualization...");
  await page.goto("http://localhost:3000/app/reports", { waitUntil: "networkidle0" });
  await sleep(500);
  // Toggle coverage metric on the graph
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    const covToggle = buttons.find((b) => b.textContent.includes("Coverage"));
    if (covToggle) covToggle.click();
  });
  await sleep(400);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "13_reports_interactive_graph.png"), fullPage: false });

  // 6. Popovers: Notifications and Profile Menu
  console.log("Step 7: Popovers (Notifications & Profile)...");
  await page.goto("http://localhost:3000/app", { waitUntil: "networkidle0" });
  await sleep(500);
  // Open Notifications
  const bellBtn = await page.$('button[aria-label="Notifications"]');
  if (bellBtn) {
    await bellBtn.click();
    await sleep(400);
    await page.screenshot({ path: path.join(OUTPUT_DIR, "14_notifications_popover_open.png"), fullPage: false });
  }

  // Open Profile Popover
  const avatarBtn = await page.$('button[aria-label="User menu"]');
  if (avatarBtn) {
    await avatarBtn.click();
    await sleep(400);
    await page.screenshot({ path: path.join(OUTPUT_DIR, "15_profile_popover_open.png"), fullPage: false });
  }

  // 7. Dark Mode View of Repository Workspace
  console.log("Step 8: Dark Mode Theme Switch...");
  await page.goto(workspaceUrl, { waitUntil: "networkidle0" });
  await page.evaluate(() => {
    document.documentElement.classList.add("dark");
    localStorage.setItem("theme", "dark");
  });
  await sleep(500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, "16_repo_workspace_dark_mode.png"), fullPage: false });

  await browser.close();
  console.log("Live Autonomous Walkthrough Completed Successfully!");
}

runLiveWalkthrough().catch((err) => {
  console.error("Live walkthrough error:", err);
  process.exit(1);
});
