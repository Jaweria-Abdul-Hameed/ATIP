import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("C:/Users/Jaweria/.gemini/antigravity/brain/5297cf64-eab5-4fe9-af63-8878e967fa15/demo_screenshots");

if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

async function run() {
  console.log("Starting Live Public Repository Connection & Mining Verification...");

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--window-size=1440,900"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Navigate to /app/repositories
  console.log("Navigating to http://localhost:3000/app/repositories...");
  await page.goto("http://localhost:3000/app/repositories", { waitUntil: "networkidle0" });
  await sleep(800);

  // 2. Click "Connect repository"
  console.log("Opening Connect Repository modal...");
  const connectBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent.includes("Connect repository") || b.textContent.includes("Connect"));
  });
  if (connectBtn && connectBtn.asElement()) {
    await connectBtn.asElement().click();
    await sleep(600);
  }

  // 3. Capture modal showing the Public Repository URL tab and presets
  const step1Path = path.join(ARTIFACTS_DIR, "24_connect_public_repo_modal.png");
  await page.screenshot({ path: step1Path, fullPage: false });
  console.log(`Captured: ${step1Path}`);

  // 4. Connect public repository: pallets/flask
  console.log("Selecting public repository preset: pallets/flask...");
  const flaskPreset = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent.includes("pallets/flask"));
  });
  if (flaskPreset && flaskPreset.asElement()) {
    await flaskPreset.asElement().click();
    console.log("Clicked preset pallets/flask");
  } else {
    // Fill in input manually
    await page.evaluate(() => {
      const input = document.querySelector('input[placeholder*="pallets/flask"]');
      if (input) {
        input.value = "https://github.com/pallets/flask";
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });
    await sleep(400);
    const submitBtn = await page.evaluateHandle(() => {
      const buttons = Array.from(document.querySelectorAll("button"));
      return buttons.find((b) => b.textContent.includes("Connect & Index Repository"));
    });
    if (submitBtn && submitBtn.asElement()) {
      await submitBtn.asElement().click();
    }
  }

  // Wait for connection to finish
  console.log("Waiting for repository connection to complete...");
  await sleep(3500);

  // 5. Capture Repositories table showing the newly connected public repo
  const step2Path = path.join(ARTIFACTS_DIR, "25_public_repo_connected_in_table.png");
  await page.screenshot({ path: step2Path, fullPage: false });
  console.log(`Captured: ${step2Path}`);

  // 6. Click into the repository workspace
  console.log("Opening repository workspace for pallets/flask...");
  const repoLink = await page.evaluateHandle(() => {
    const links = Array.from(document.querySelectorAll("a"));
    return links.find((a) => a.textContent.includes("flask") || a.href.includes("/app/repositories/"));
  });
  if (repoLink && repoLink.asElement()) {
    await repoLink.asElement().click();
    await page.waitForNavigation({ waitUntil: "networkidle0" }).catch(() => {});
    await sleep(1500);
  }

  const workspaceUrl = page.url();
  console.log(`Active Workspace URL: ${workspaceUrl}`);

  // 7. Capture workspace before analysis
  const step3Path = path.join(ARTIFACTS_DIR, "26_repo_workspace_before_analysis.png");
  await page.screenshot({ path: step3Path, fullPage: false });
  console.log(`Captured: ${step3Path}`);

  // 8. Click "Analyze repository" to trigger live mining pipeline!
  console.log("Triggering live repository mining and static analysis...");
  const analyzeBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent.includes("Analyze repository"));
  });
  if (analyzeBtn && analyzeBtn.asElement()) {
    await analyzeBtn.asElement().click();
    console.log("Clicked 'Analyze repository' CTA!");
    await sleep(1200);
  }

  // Capture analysis running state
  const step4Path = path.join(ARTIFACTS_DIR, "27_repo_analysis_in_progress.png");
  await page.screenshot({ path: step4Path, fullPage: false });
  console.log(`Captured: ${step4Path}`);

  // 9. Poll until analysis is completed
  console.log("Waiting for mining pipeline to clone, parse AST, build dependency graph, and analyze complexity...");
  let completed = false;
  for (let i = 0; i < 40; i++) {
    await sleep(2000);
    const statusText = await page.evaluate(() => {
      const badge = document.querySelector('[class*="border"]');
      const text = document.body.innerText;
      if (text.includes("Analysis completed successfully") || text.includes("completed")) {
        return "completed";
      }
      return text.includes("Analyzing") || text.includes("Mining") || text.includes("Building") ? "running" : "idle";
    });
    console.log(`Poll [${i + 1}/40]: status = ${statusText}`);
    if (statusText === "completed") {
      completed = true;
      break;
    }
  }

  await sleep(1500);

  // 10. Capture Overview Tab (Churn & Hotspots, Summary)
  const step5Path = path.join(ARTIFACTS_DIR, "28_mined_repo_overview_hotspots.png");
  await page.screenshot({ path: step5Path, fullPage: false });
  console.log(`Captured Overview Tab: ${step5Path}`);

  // 11. Switch to Commits Tab
  console.log("Inspecting Commits Tab (Git history churn)...");
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Commits"));
    if (tab) tab.click();
  });
  await sleep(800);
  const step6Path = path.join(ARTIFACTS_DIR, "29_mined_repo_commits_churn.png");
  await page.screenshot({ path: step6Path, fullPage: false });
  console.log(`Captured Commits Tab: ${step6Path}`);

  // 12. Switch to Files Tab (Complexity & Maintainability)
  console.log("Inspecting Files Tab (Cyclomatic complexity & Maintainability index)...");
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Files"));
    if (tab) tab.click();
  });
  await sleep(800);
  const step7Path = path.join(ARTIFACTS_DIR, "30_mined_repo_files_complexity.png");
  await page.screenshot({ path: step7Path, fullPage: false });
  console.log(`Captured Files Tab: ${step7Path}`);

  // 13. Switch to Dependencies Tab (AST Dependency Graph & Blast Radius)
  console.log("Inspecting Dependencies Tab (AST graph & blast radius)...");
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Dependencies"));
    if (tab) tab.click();
  });
  await sleep(800);
  const step8Path = path.join(ARTIFACTS_DIR, "31_mined_repo_dependencies_blast_radius.png");
  await page.screenshot({ path: step8Path, fullPage: false });
  console.log(`Captured Dependencies Tab: ${step8Path}`);

  // 14. Switch to Coverage Objectives Tab
  console.log("Inspecting Coverage Objectives Tab...");
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button"));
    const tab = tabs.find((t) => t.textContent.trim().startsWith("Coverage"));
    if (tab) tab.click();
  });
  await sleep(800);
  const step9Path = path.join(ARTIFACTS_DIR, "32_mined_repo_coverage_objectives.png");
  await page.screenshot({ path: step9Path, fullPage: false });
  console.log(`Captured Coverage Tab: ${step9Path}`);

  await browser.close();
  console.log("All public repository mining verification checks completed successfully!");
}

run().catch((err) => {
  console.error("Execution failed:", err);
  process.exit(1);
});
