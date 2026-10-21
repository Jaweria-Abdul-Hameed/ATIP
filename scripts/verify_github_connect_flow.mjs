import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("C:/Users/Jaweria/.gemini/antigravity/brain/5297cf64-eab5-4fe9-af63-8878e967fa15/demo_screenshots");

async function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

async function verifyGitHubConnect() {
  console.log("Verifying Live GitHub Repository Connection Flow...");

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--window-size=1440,900"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Go to repositories page
  await page.goto("http://localhost:3000/app/repositories", { waitUntil: "networkidle0" });
  await sleep(600);

  // 2. Open Connect modal
  const connectBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent.includes("Connect repository") || b.textContent.includes("Connect"));
  });
  if (connectBtn && connectBtn.asElement()) {
    await connectBtn.asElement().click();
    await sleep(600);
  }

  // Capture Step 1: Token Authentication Screen
  await page.screenshot({
    path: path.join(ARTIFACTS_DIR, "20_github_auth_modal_step1.png"),
    fullPage: false,
  });
  console.log("Captured 20_github_auth_modal_step1.png");

  // 3. Click "Use Reviewer Test Account" to authenticate and fetch repositories
  const testAccBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent.includes("Reviewer Test Account"));
  });
  if (testAccBtn && testAccBtn.asElement()) {
    await testAccBtn.asElement().click();
    await sleep(1000);
  }

  // Capture Step 2: Authenticated user profile with private & public repos
  await page.screenshot({
    path: path.join(ARTIFACTS_DIR, "21_github_auth_modal_step2_repos.png"),
    fullPage: false,
  });
  console.log("Captured 21_github_auth_modal_step2_repos.png");

  // 4. Click "Private" tab filter
  const privateTab = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent.includes("Private"));
  });
  if (privateTab && privateTab.asElement()) {
    await privateTab.asElement().click();
    await sleep(400);
  }

  // Capture Step 3: Filtered private repositories
  await page.screenshot({
    path: path.join(ARTIFACTS_DIR, "22_github_auth_modal_private_repos.png"),
    fullPage: false,
  });
  console.log("Captured 22_github_auth_modal_private_repos.png");

  // 5. Click "Connect" on the first private repo
  const repoConnectBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent === "Connect");
  });
  if (repoConnectBtn && repoConnectBtn.asElement()) {
    await repoConnectBtn.asElement().click();
    await sleep(1500);
  }

  // Capture Step 4: Repositories table showing the newly connected repository
  await page.screenshot({
    path: path.join(ARTIFACTS_DIR, "23_repository_connected_in_table.png"),
    fullPage: false,
  });
  console.log("Captured 23_repository_connected_in_table.png");

  await browser.close();
  console.log("GitHub Connection flow verification completed!");
}

verifyGitHubConnect().catch((err) => {
  console.error("Verification error:", err);
  process.exit(1);
});
