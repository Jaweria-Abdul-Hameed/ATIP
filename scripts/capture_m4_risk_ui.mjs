import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("artifacts/ui");

async function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

async function run() {
  console.log("Capturing M4 Risk Intelligence and Test Plans UI Screenshots...");
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--window-size=1440,1000"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1000 });

  // 1. Navigate to Risk Intelligence
  const riskUrl = "http://localhost:3000/app/risk";
  console.log(`Navigating to ${riskUrl}...`);
  await page.goto(riskUrl, { waitUntil: "networkidle0" });
  await sleep(1500);

  const pOverview = path.join(ARTIFACTS_DIR, "36_risk_intelligence_overview.png");
  await page.screenshot({ path: pOverview, fullPage: false });
  console.log(`Captured: ${pOverview}`);

  // 2. Click first row to open detail drawer
  await page.evaluate(() => {
    const row = document.querySelector("tbody tr");
    if (row) row.click();
  });
  await sleep(800);

  const pDrawer = path.join(ARTIFACTS_DIR, "37_risk_intelligence_drawer.png");
  await page.screenshot({ path: pDrawer, fullPage: false });
  console.log(`Captured: ${pDrawer}`);

  // Close drawer
  await page.evaluate(() => {
    const closeBtn = Array.from(document.querySelectorAll("button")).find(b => b.textContent.includes("Close"));
    if (closeBtn) closeBtn.click();
  });
  await sleep(400);

  // 3. Switch to Change Impact Graph if available
  await page.evaluate(() => {
    const impactTab = Array.from(document.querySelectorAll("button")).find(b => b.textContent.includes("Change Impact Graph"));
    if (impactTab) impactTab.click();
  });
  await sleep(600);

  const pImpact = path.join(ARTIFACTS_DIR, "38_risk_intelligence_impact_tab.png");
  await page.screenshot({ path: pImpact, fullPage: false });
  console.log(`Captured: ${pImpact}`);

  // 4. Navigate to Test Plans
  const plansUrl = "http://localhost:3000/app/test-plans";
  console.log(`Navigating to ${plansUrl}...`);
  await page.goto(plansUrl, { waitUntil: "networkidle0" });
  await sleep(1500);

  const pPlans = path.join(ARTIFACTS_DIR, "39_test_plans_selection.png");
  await page.screenshot({ path: pPlans, fullPage: false });
  console.log(`Captured: ${pPlans}`);

  // Click Test Gaps Tab
  await page.evaluate(() => {
    const gapsTab = Array.from(document.querySelectorAll("button")).find(b => b.textContent.includes("Test Gaps"));
    if (gapsTab) gapsTab.click();
  });
  await sleep(600);

  const pGaps = path.join(ARTIFACTS_DIR, "40_test_plans_gaps.png");
  await page.screenshot({ path: pGaps, fullPage: false });
  console.log(`Captured: ${pGaps}`);

  await browser.close();
  console.log("All M4 UI screenshots captured successfully!");
}

run().catch((err) => {
  console.error("Screenshot capture error:", err);
  process.exit(1);
});
