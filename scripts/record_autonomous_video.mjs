import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const FRAMES_DIR = path.resolve("artifacts/screencast_frames");

if (fs.existsSync(FRAMES_DIR)) {
  fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
}
fs.mkdirSync(FRAMES_DIR, { recursive: true });

async function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

async function recordLiveWalkthrough() {
  console.log("Launching Chrome for Live Screencast Video Recording...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-gpu",
      "--window-size=1440,900",
      "--disable-features=TranslateUI",
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  let frameIndex = 0;
  const client = await page.target().createCDPSession();

  client.on("Page.screencastFrame", async ({ data, sessionId }) => {
    try {
      const idx = String(frameIndex++).padStart(5, "0");
      const filePath = path.join(FRAMES_DIR, `frame_${idx}.jpg`);
      fs.writeFileSync(filePath, Buffer.from(data, "base64"));
      await client.send("Page.screencastFrameAck", { sessionId });
    } catch {
      // ignore frame write glitches
    }
  });

  // Start screencast at ~15 fps (every 2nd frame)
  await client.send("Page.startScreencast", {
    format: "jpeg",
    quality: 85,
    maxWidth: 1440,
    maxHeight: 900,
    everyNthFrame: 2,
  });

  console.log("Screencast started. Beginning automated walkthrough...");

  // ==========================================
  // SCENE 1: Sign-In with Form Filling
  // ==========================================
  console.log("Scene 1: Sign In...");
  await page.goto("http://localhost:3000/sign-in", { waitUntil: "networkidle0" });
  await sleep(600);

  // Type work email
  const emailInput = await page.$('input[type="email"]');
  if (emailInput) {
    await emailInput.click();
    await page.type('input[type="email"]', "lead.engineer@atip-autonomous.internal", { delay: 40 });
  }
  await sleep(300);

  // Type password
  const passInput = await page.$('input[type="password"]');
  if (passInput) {
    await passInput.click();
    await page.type('input[type="password"]', "SuperSecretPass2026!", { delay: 40 });
  }
  await sleep(600);

  // Click Quick Reviewer Pass button to enter app
  const enterAppBtn = await page.$('button, a[href="/app"]');
  if (enterAppBtn) {
    await enterAppBtn.click();
  } else {
    await page.goto("http://localhost:3000/app", { waitUntil: "networkidle0" });
  }
  await sleep(800);

  // ==========================================
  // SCENE 2: Overview Dashboard & Popovers
  // ==========================================
  console.log("Scene 2: Dashboard Overview & Popovers...");
  await page.goto("http://localhost:3000/app", { waitUntil: "networkidle0" });
  await sleep(700);

  // Open notifications popover
  const bellBtn = await page.$('button[aria-label="Notifications"]');
  if (bellBtn) {
    await bellBtn.click();
    await sleep(900);
    // Click "Mark all read"
    const markRead = await page.evaluateHandle(() => {
      const btns = Array.from(document.querySelectorAll("button"));
      return btns.find((b) => b.textContent.includes("Mark all read"));
    });
    if (markRead && markRead.asElement()) {
      await markRead.asElement().click();
      await sleep(600);
    }
    // Close popover
    await bellBtn.click();
    await sleep(400);
  }

  // Open user profile popover
  const avatarBtn = await page.$('button[aria-label="User menu"]');
  if (avatarBtn) {
    await avatarBtn.click();
    await sleep(700);
    await avatarBtn.click();
    await sleep(400);
  }

  // ==========================================
  // SCENE 3: Settings & Execution Quotas
  // ==========================================
  console.log("Scene 3: Settings & Execution Policies...");
  await page.goto("http://localhost:3000/app/settings?tab=profile", { waitUntil: "networkidle0" });
  await sleep(600);

  // Type updated name
  const nameInput = await page.$('input[value="Jaweria Abdul Hameed"], input[placeholder="Your full name"], input[type="text"]');
  if (nameInput) {
    await nameInput.click({ clickCount: 3 });
    await nameInput.type("Jaweria Abdul Hameed (Lead Architect)", { delay: 30 });
    await sleep(500);
  }

  // Switch to Execution Policies tab
  await page.goto("http://localhost:3000/app/settings?tab=execution", { waitUntil: "networkidle0" });
  await sleep(800);

  // Switch to Members & Roles tab
  await page.goto("http://localhost:3000/app/settings?tab=members", { waitUntil: "networkidle0" });
  await sleep(800);

  // ==========================================
  // SCENE 4: Repositories & Connect Modal
  // ==========================================
  console.log("Scene 4: Repositories & Modal...");
  await page.goto("http://localhost:3000/app/repositories", { waitUntil: "networkidle0" });
  await sleep(600);

  // Filter search
  const repoSearch = await page.$('input[placeholder*="Search"], input[type="search"], input[type="text"]');
  if (repoSearch) {
    await repoSearch.type("dashboard", { delay: 40 });
    await sleep(500);
  }

  // Open Connect Repository modal
  const connectBtn = await page.evaluateHandle(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((b) => b.textContent.includes("Connect repository") || b.textContent.includes("Connect"));
  });
  if (connectBtn && connectBtn.asElement()) {
    await connectBtn.asElement().click();
    await sleep(800);
    // Close modal
    const closeBtn = await page.evaluateHandle(() => {
      const btns = Array.from(document.querySelectorAll("button"));
      return btns.find((b) => b.textContent.includes("Close") || b.getAttribute("aria-label") === "Close");
    });
    if (closeBtn && closeBtn.asElement()) {
      await closeBtn.asElement().click();
    } else {
      await page.keyboard.press("Escape");
    }
    await sleep(500);
  }

  // ==========================================
  // SCENE 5: Repository Workspace & M3 Mining
  // ==========================================
  console.log("Scene 5: Repository Workspace Tabs...");
  await page.goto("http://localhost:3000/app/repositories/nextjs-dashboard", { waitUntil: "networkidle0" });
  await sleep(700);

  // Click Commits tab
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button, a"));
    const t = tabs.find((x) => x.textContent.includes("Commits"));
    if (t) t.click();
  });
  await sleep(700);

  // Click Files tab
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button, a"));
    const t = tabs.find((x) => x.textContent.includes("Files"));
    if (t) t.click();
  });
  await sleep(700);

  // Click Dependencies tab
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button, a"));
    const t = tabs.find((x) => x.textContent.includes("Dependencies"));
    if (t) t.click();
  });
  await sleep(700);

  // Click Coverage Objectives tab
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("button, a"));
    const t = tabs.find((x) => x.textContent.includes("Coverage"));
    if (t) t.click();
  });
  await sleep(700);

  // Hover and Click "Analyze repository" CTA
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    const analyzeBtn = buttons.find((b) => b.textContent.includes("Analyze repository"));
    if (analyzeBtn) analyzeBtn.click();
  });
  await sleep(1000);

  // ==========================================
  // SCENE 6: Reports & Quality Trend Chart
  // ==========================================
  console.log("Scene 6: Reports & Trends...");
  await page.goto("http://localhost:3000/app/reports", { waitUntil: "networkidle0" });
  await sleep(700);

  // Toggle coverage metric
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    const covToggle = buttons.find((b) => b.textContent.includes("Coverage"));
    if (covToggle) covToggle.click();
  });
  await sleep(600);

  // Hover over the trend bar to show the rich tooltip
  const bar = await page.$("svg rect:nth-child(10), svg circle:nth-child(5)");
  if (bar) {
    await bar.hover();
    await sleep(800);
  }

  // ==========================================
  // SCENE 7: Dual Theme Switch (Spring 360°)
  // ==========================================
  console.log("Scene 7: Dual Theme Switch to Dark Mode...");
  const themeBtn = await page.$('button[aria-label="Toggle theme"], button:has(svg.lucide-sun), button:has(svg.lucide-moon)');
  if (themeBtn) {
    await themeBtn.click();
    await sleep(1000);
  } else {
    await page.evaluate(() => {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    });
    await sleep(800);
  }

  // Back to Repository Workspace in Dark Mode
  await page.goto("http://localhost:3000/app/repositories/nextjs-dashboard", { waitUntil: "networkidle0" });
  await sleep(1000);

  // Stop screencast
  console.log("Stopping screencast...");
  await client.send("Page.stopScreencast");
  await browser.close();

  console.log(`Live Screencast completed! Total frames captured: ${frameIndex}`);
}

recordLiveWalkthrough().catch((err) => {
  console.error("Walkthrough recording error:", err);
  process.exit(1);
});
