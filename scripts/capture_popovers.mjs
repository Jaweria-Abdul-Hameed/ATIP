import puppeteer from "puppeteer-core";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("artifacts/ui");

async function main() {
  console.log("Launching Chrome...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Notifications Popover
  await page.goto("http://localhost:3000/app", { waitUntil: "networkidle0" });
  await page.evaluate(() => {
    document.documentElement.classList.remove("dark");
  });
  await new Promise((res) => setTimeout(res, 500));
  // Click notification bell
  const bellButton = await page.$('button[aria-label="Notifications"]');
  if (bellButton) {
    await bellButton.click();
    await new Promise((res) => setTimeout(res, 300));
    await page.screenshot({
      path: path.join(ARTIFACTS_DIR, "15_Notifications_Popover.png"),
      fullPage: false,
    });
    console.log("Captured 15_Notifications_Popover.png");
  }

  // 2. Topbar Profile Popover
  await page.goto("http://localhost:3000/app", { waitUntil: "networkidle0" });
  await new Promise((res) => setTimeout(res, 500));
  const topbarProfileBtn = await page.$('button[aria-label="User account menu"]');
  if (topbarProfileBtn) {
    await topbarProfileBtn.click();
    await new Promise((res) => setTimeout(res, 300));
    await page.screenshot({
      path: path.join(ARTIFACTS_DIR, "16_Topbar_Profile_Popover.png"),
      fullPage: false,
    });
    console.log("Captured 16_Topbar_Profile_Popover.png");
  }

  // 3. Sidebar Profile Popover
  await page.goto("http://localhost:3000/app", { waitUntil: "networkidle0" });
  await new Promise((res) => setTimeout(res, 500));
  const sidebarProfileBtn = await page.$('button[aria-label="User profile menu"]');
  if (sidebarProfileBtn) {
    await sidebarProfileBtn.click();
    await new Promise((res) => setTimeout(res, 300));
    await page.screenshot({
      path: path.join(ARTIFACTS_DIR, "17_Sidebar_Profile_Popover.png"),
      fullPage: false,
    });
    console.log("Captured 17_Sidebar_Profile_Popover.png");
  }

  await browser.close();
  console.log("Finished capturing popover screenshots!");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
