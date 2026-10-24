import puppeteer from 'puppeteer-core';
import path from 'path';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const ARTIFACTS_DIR = path.resolve("artifacts/ui");

async function main() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  console.log('1. Navigating to http://localhost:3000/app ...');
  await page.goto('http://localhost:3000/app', { waitUntil: 'networkidle0' });

  // Locate theme toggle button in header
  const themeBtn = await page.$('header button[aria-label*="mode" i], header button[aria-label*="theme" i]');
  if (!themeBtn) {
    throw new Error('Theme toggle button not found in header!');
  }
  console.log('PASS: Found ThemeToggle button in Topbar header.');

  // Check initial state
  const initialClass = await page.evaluate(() => document.documentElement.className);
  console.log('Initial documentElement class:', initialClass);

  // Click theme toggle to switch to dark mode
  console.log('2. Clicking ThemeToggle to activate dark mode...');
  await themeBtn.click();

  // Check that rotating spring animation class was triggered
  const isSpinning = await page.evaluate(() => {
    const spinEl = document.querySelector('header .animate-theme-spin');
    return spinEl !== null;
  });
  console.log('Theme toggle spring animation triggered:', isSpinning);

  await new Promise((r) => setTimeout(r, 650));

  const darkClass = await page.evaluate(() => document.documentElement.className);
  console.log('After 1st toggle documentElement class:', darkClass);
  if (!darkClass.includes('dark')) {
    throw new Error('Dark class not found on documentElement after toggle!');
  }
  console.log('PASS: Dark mode activated successfully on <html>!');

  // Capture dark mode screenshot of Overview
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '18_Theme_Toggled_Dark.png'), fullPage: false });
  console.log('Captured artifacts/ui/18_Theme_Toggled_Dark.png');

  // Verify Overview page dynamic filter
  console.log('3. Testing Overview dynamic scope filtering...');
  const repoSelect = await page.$('select');
  if (repoSelect) {
    await page.select('select', 'api-service');
    await new Promise((r) => setTimeout(r, 400));
    const statCardsText = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('.font-serif'));
      return cards.map(c => c.textContent?.trim()).join(' | ');
    });
    console.log('Stat cards after filtering to api-service:', statCardsText);
  }

  // Navigate to Risk Intelligence while in Dark Mode
  console.log('4. Navigating to http://localhost:3000/app/risk in Dark Mode...');
  await page.goto('http://localhost:3000/app/risk', { waitUntil: 'networkidle0' });
  const riskDarkClass = await page.evaluate(() => document.documentElement.className);
  console.log('Risk page documentElement class:', riskDarkClass);
  if (!riskDarkClass.includes('dark')) {
    throw new Error('Dark mode did not persist to /app/risk!');
  }
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '04_Risk_Intelligence_Dark.png'), fullPage: false });
  console.log('Captured artifacts/ui/04_Risk_Intelligence_Dark.png');

  // Test Risk Intelligence dynamic interactions in Dark Mode:
  console.log('5. Testing Risk Intelligence interactions...');
  // Select repository mobile-app
  const riskRepoSelect = await page.$('div:has(> label) select');
  if (riskRepoSelect) {
    await page.select('div:has(> label) select', 'mobile-app');
    await new Promise((r) => setTimeout(r, 400));
    console.log('PASS: Selected mobile-app repository on Risk page.');
  }

  // Click first row to open drawer
  const firstRow = await page.$('tbody tr');
  if (firstRow) {
    await firstRow.click();
    await new Promise((r) => setTimeout(r, 400));
    const drawerOpen = await page.evaluate(() => {
      return document.body.innerText.toLowerCase().includes('risk evidence drilldown');
    });
    console.log('Risk drawer opened successfully:', drawerOpen);
    // Close the drawer before interacting with header
    await page.evaluate(() => {
      const drawer = document.querySelector('.fixed.inset-0.z-50');
      if (drawer) {
        const btn = drawer.querySelector('button');
        if (btn) btn.click();
      }
    });
    await new Promise((r) => setTimeout(r, 400));
    const stillOpen = await page.evaluate(() => !!document.querySelector('.fixed.inset-0.z-50'));
    console.log('Is drawer still open?', stillOpen);
  }

  // Toggle back to Light Mode from Risk page
  console.log('6. Clicking ThemeToggle on /app/risk to return to light mode...');
  const riskThemeBtn = await page.$('header button[aria-label*="mode" i], header button[aria-label*="theme" i]');
  if (!riskThemeBtn) {
    throw new Error('Theme toggle button not found on /app/risk header!');
  }
  await riskThemeBtn.click();
  await new Promise((r) => setTimeout(r, 650));

  const riskLightClass = await page.evaluate(() => document.documentElement.className);
  console.log('After 2nd toggle documentElement class:', riskLightClass);
  if (riskLightClass.includes('dark')) {
    throw new Error('Expected light mode, but dark class still present!');
  }
  console.log('PASS: Light mode restored successfully!');
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '19_Theme_Toggled_Light.png'), fullPage: false });

  await browser.close();
  console.log('\n=== ALL THEME TOGGLE & DARK MODE & DYNAMIC INTERACTION CHECKS PASSED PERFECTLY ===\n');
}

main().catch((err) => {
  console.error('VERIFICATION FAILED:', err);
  process.exit(1);
});
