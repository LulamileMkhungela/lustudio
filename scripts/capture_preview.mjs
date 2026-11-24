import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';
const OUT_DIR = path.resolve('scripts/preview-check');
fs.mkdirSync(OUT_DIR, { recursive: true });

const legacyTokens = [
  '6c756c617a656c',
  '6c756c616d696c65',
  '6d6b68756e67656c612e6c40676d61696c2e636f6d',
  '6c756c617a656c6875622e636f2e7a61',
].map((value) => Buffer.from(value, 'hex').toString('utf8').toLowerCase());

const pages = [
  { name: 'home', path: '/', colorScheme: 'light' },
  { name: 'home-dark-scheme', path: '/', colorScheme: 'dark' },
  { name: 'services', path: '/services/website-design', colorScheme: 'light' },
  { name: 'projects', path: '/projects', colorScheme: 'light' },
];

const failedLocalResponses = [];
const pageErrors = [];
const legacyMarkerHits = [];
const screenshots = [];
const dropdownChecks = [];

const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
  reducedMotion: 'no-preference',
  colorScheme: 'light',
});

for (const item of pages) {
  const page = await context.newPage();
  await page.emulateMedia({ colorScheme: item.colorScheme });
  page.on('response', (response) => {
    if (response.url().startsWith(BASE_URL) && response.status() >= 400) {
      failedLocalResponses.push({ page: item.name, url: response.url(), status: response.status() });
    }
  });
  page.on('pageerror', (error) => pageErrors.push({ page: item.name, message: String(error) }));
  await page.goto(BASE_URL + item.path, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.evaluate(async () => {
    if (document.fonts && document.fonts.ready) {
      await Promise.race([document.fonts.ready, new Promise((resolve) => setTimeout(resolve, 2500))]);
    }
  });
  await page.waitForTimeout(5000);
  const text = (await page.locator('body').innerText()).toLowerCase();
  for (const token of legacyTokens) {
    if (text.includes(token)) legacyMarkerHits.push({ page: item.name, token });
  }
  const screenshot = path.join(OUT_DIR, `${item.name}.png`);
  await page.screenshot({ path: screenshot, fullPage: false, animations: 'allow' });
  screenshots.push({ name: item.name, path: `/${item.path.replace(/^\//, '')}`, file: path.basename(screenshot) });
  if (item.name === 'home') {
    const trigger = page.locator('.navbar_component .cosmos-audience_trigger').first();
    const defaultLabel = (await page.locator('.navbar_component [data-cosmos-audience-current]').first().innerText()).trim();
    const selected = await page.locator('.navbar_component .cosmos-audience_option.is-selected').first().innerText();
    await trigger.click();
    await page.waitForTimeout(350);
    const options = await page.locator('.navbar_component [data-view-option]').allInnerTexts();
    const dropdownScreenshot = path.join(OUT_DIR, 'dropdown.png');
    await page.screenshot({ path: dropdownScreenshot, fullPage: false, animations: 'allow' });
    dropdownChecks.push({ defaultLabel, selected: selected.trim(), options: options.map((v) => v.trim()) });
    screenshots.push({ name: 'dropdown', path: '/', file: path.basename(dropdownScreenshot) });
  }
  await page.close();
}

await browser.close();

const report = {
  baseURL: BASE_URL,
  viewport: { width: 1440, height: 1000 },
  screenshots,
  dropdownChecks,
  failedLocalResponses,
  pageErrors,
  legacyMarkerHits,
};
fs.writeFileSync(path.join(OUT_DIR, 'browser-report.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
