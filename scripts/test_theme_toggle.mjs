import puppeteer from "puppeteer-core";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("artifacts/ui");

async function main() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  await page.goto("http://localhost:3000/app", { waitUntil: "networkidle0" });
  await new Promise((res) => setTimeout(res, 500));

  // Find theme toggle button
  const toggleBtn = await page.$('button[aria-label="Toggle light or dark theme"]');
  if (!toggleBtn) {
    throw new Error("Theme toggle button not found");
  }

  // Click once to switch to dark
  await toggleBtn.click();
  await new Promise((res) => setTimeout(res, 400));
  await page.screenshot({
    path: path.join(ARTIFACTS_DIR, "18_Theme_Toggled_Dark.png"),
    fullPage: false,
  });

  // Click again to switch back to light
  await toggleBtn.click();
  await new Promise((res) => setTimeout(res, 400));
  await page.screenshot({
    path: path.join(ARTIFACTS_DIR, "19_Theme_Toggled_Light.png"),
    fullPage: false,
  });

  await browser.close();
  console.log("Theme toggle test and screenshots completed!");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
