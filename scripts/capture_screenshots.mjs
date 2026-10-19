import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("artifacts/ui");

if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

const routes = [
  { name: "01_Overview", path: "/app" },
  { name: "02_Repositories", path: "/app/repositories" },
  { name: "03_Repository_Workspace", path: "/app/repositories/nextjs-dashboard" },
  { name: "04_Risk_Intelligence", path: "/app/risk" },
  { name: "05_Test_Plans", path: "/app/test-plans" },
  { name: "06_Test_Runs", path: "/app/runs" },
  { name: "07_Run_Details", path: "/app/runs/run-1042" },
  { name: "08_WhiteBox_Coverage", path: "/app/coverage" },
  { name: "09_AI_Analysis", path: "/app/analysis" },
  { name: "10_Reports", path: "/app/reports" },
  { name: "11_Settings", path: "/app/settings" },
  { name: "12_Sign_In", path: "/sign-in" },
];

async function main() {
  console.log("Launching Chrome at:", CHROME_PATH);
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Capture Light Mode Screenshots
  for (const r of routes) {
    const url = `http://localhost:3000${r.path}`;
    console.log(`Navigating to ${url} (light mode)...`);
    await page.goto(url, { waitUntil: "networkidle0" });
    await page.evaluate(() => {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    });
    await new Promise((res) => setTimeout(res, 400));
    const outPath = path.join(ARTIFACTS_DIR, `${r.name}_light.png`);
    await page.screenshot({ path: outPath, fullPage: false });
    console.log(`Saved: ${outPath}`);
  }

  // 2. Capture Dark Mode Screenshots
  for (const r of routes) {
    const url = `http://localhost:3000${r.path}`;
    console.log(`Navigating to ${url} (dark mode)...`);
    await page.goto(url, { waitUntil: "networkidle0" });
    await page.evaluate(() => {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    });
    await new Promise((res) => setTimeout(res, 400));
    const outPath = path.join(ARTIFACTS_DIR, `${r.name}_dark.png`);
    await page.screenshot({ path: outPath, fullPage: false });
    console.log(`Saved: ${outPath}`);
  }

  // 3. Capture Mobile Responsive Screenshots
  await page.setViewport({ width: 390, height: 844, isMobile: true });
  await page.goto("http://localhost:3000/app", { waitUntil: "networkidle0" });
  await page.screenshot({
    path: path.join(ARTIFACTS_DIR, "01_Overview_mobile.png"),
    fullPage: false,
  });

  await page.goto("http://localhost:3000/app/coverage", { waitUntil: "networkidle0" });
  await page.screenshot({
    path: path.join(ARTIFACTS_DIR, "08_WhiteBox_Coverage_mobile.png"),
    fullPage: false,
  });

  await browser.close();
  console.log("All screenshots successfully captured in artifacts/ui/!");
}

main().catch((err) => {
  console.error("Screenshot error:", err);
  process.exit(1);
});
