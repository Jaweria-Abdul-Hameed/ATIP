import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("C:/Users/Jaweria/.gemini/antigravity/brain/5297cf64-eab5-4fe9-af63-8878e967fa15/demo_screenshots");

async function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

async function run() {
  console.log("Capturing Metrics Guidance Screenshots...");

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--window-size=1440,1000"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1000 });

  // 1. Navigate to Flask repo
  const flaskUrl = "http://localhost:3000/app/repositories/repo_d7cf577153de4edd";
  console.log(`Navigating to ${flaskUrl}...`);
  await page.goto(flaskUrl, { waitUntil: "networkidle0" });
  await sleep(1000);

  // Click Files Tab
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Files"));
    if (tab) tab.click();
  });
  await sleep(800);

  // Capture Files Tab with Quick Ranges Bar
  const pLegend = path.join(ARTIFACTS_DIR, "33_files_tab_metrics_legend.png");
  await page.screenshot({ path: pLegend, fullPage: false });
  console.log(`Captured: ${pLegend}`);

  // Expand "What do these mean?" toggle
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    const toggleBtn = buttons.find((b) => b.textContent.includes("What do these mean?"));
    if (toggleBtn) toggleBtn.click();
  });
  await sleep(600);

  const pExpanded = path.join(ARTIFACTS_DIR, "34_files_tab_expanded_guide.png");
  await page.screenshot({ path: pExpanded, fullPage: false });
  console.log(`Captured: ${pExpanded}`);

  // 2. Navigate to Settings -> Profile
  const settingsUrl = "http://localhost:3000/app/settings?tab=profile";
  console.log(`Navigating to ${settingsUrl}...`);
  await page.goto(settingsUrl, { waitUntil: "networkidle0" });
  await sleep(1000);

  // Scroll to Code Quality Guide
  await page.evaluate(() => {
    const guide = document.getElementById("code-quality-guide");
    if (guide) {
      guide.scrollIntoView({ behavior: "instant", block: "start" });
    }
  });
  await sleep(600);

  const pSettings = path.join(ARTIFACTS_DIR, "35_settings_profile_code_quality_guide.png");
  await page.screenshot({ path: pSettings, fullPage: false });
  console.log(`Captured: ${pSettings}`);

  await browser.close();
  console.log("All screenshots captured successfully!");
}

run().catch((err) => {
  console.error("Capture failed:", err);
  process.exit(1);
});
