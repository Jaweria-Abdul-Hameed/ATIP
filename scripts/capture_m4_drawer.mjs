import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("artifacts/ui");

async function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

async function run() {
  console.log("Capturing Risk Intelligence Drawer screenshots...");
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--window-size=1440,900"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Light mode
  await page.goto("http://localhost:3000/app/risk", { waitUntil: "networkidle0" });
  await page.evaluate(() => {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("theme", "light");
  });
  await sleep(600);

  // Click first row in table
  await page.evaluate(() => {
    const row = document.querySelector("tbody tr");
    if (row) row.click();
  });
  await sleep(600);

  const outLight = path.join(ARTIFACTS_DIR, "04_Risk_Intelligence_drawer_light.png");
  await page.screenshot({ path: outLight, fullPage: false });
  console.log(`Saved: ${outLight}`);

  // 2. Dark mode
  await page.evaluate(() => {
    document.documentElement.classList.add("dark");
    localStorage.setItem("theme", "dark");
  });
  await sleep(600);

  const outDark = path.join(ARTIFACTS_DIR, "04_Risk_Intelligence_drawer_dark.png");
  await page.screenshot({ path: outDark, fullPage: false });
  console.log(`Saved: ${outDark}`);

  await browser.close();
  console.log("Drawer screenshots captured successfully!");
}

run().catch((err) => {
  console.error("Capture drawer error:", err);
  process.exit(1);
});
