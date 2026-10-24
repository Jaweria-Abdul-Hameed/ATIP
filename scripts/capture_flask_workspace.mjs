import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("C:/Users/Jaweria/.gemini/antigravity/brain/5297cf64-eab5-4fe9-af63-8878e967fa15/demo_screenshots");

async function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

async function run() {
  console.log("Capturing Flask Repository Workspace tabs...");

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--window-size=1440,900"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // Navigate directly to the pallets/flask workspace
  const flaskUrl = "http://localhost:3000/app/repositories/repo_d7cf577153de4edd";
  console.log(`Navigating to ${flaskUrl}...`);
  await page.goto(flaskUrl, { waitUntil: "networkidle0" });
  await sleep(1200);

  // 1. Overview Tab
  const pOverview = path.join(ARTIFACTS_DIR, "28_mined_repo_overview_hotspots.png");
  await page.screenshot({ path: pOverview, fullPage: false });
  console.log(`Captured Overview: ${pOverview}`);

  // 2. Commits Tab
  console.log("Switching to Commits Tab...");
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Commits"));
    if (tab) tab.click();
  });
  await sleep(800);
  const pCommits = path.join(ARTIFACTS_DIR, "29_mined_repo_commits_churn.png");
  await page.screenshot({ path: pCommits, fullPage: false });
  console.log(`Captured Commits: ${pCommits}`);

  // 3. Files Tab
  console.log("Switching to Files Tab...");
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Files"));
    if (tab) tab.click();
  });
  await sleep(800);
  const pFiles = path.join(ARTIFACTS_DIR, "30_mined_repo_files_complexity.png");
  await page.screenshot({ path: pFiles, fullPage: false });
  console.log(`Captured Files: ${pFiles}`);

  // 4. Dependencies Tab
  console.log("Switching to Dependencies Tab...");
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Dependencies"));
    if (tab) tab.click();
  });
  await sleep(1000);
  const pDeps = path.join(ARTIFACTS_DIR, "31_mined_repo_dependencies_blast_radius.png");
  await page.screenshot({ path: pDeps, fullPage: false });
  console.log(`Captured Dependencies: ${pDeps}`);

  // 5. Coverage Objectives Tab
  console.log("Switching to Coverage Objectives Tab...");
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Coverage"));
    if (tab) tab.click();
  });
  await sleep(800);
  const pCov = path.join(ARTIFACTS_DIR, "32_mined_repo_coverage_objectives.png");
  await page.screenshot({ path: pCov, fullPage: false });
  console.log(`Captured Coverage: ${pCov}`);

  await browser.close();
  console.log("Flask workspace tab screenshots captured successfully!");
}

run().catch((err) => {
  console.error("Capture failed:", err);
  process.exit(1);
});
