import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8000';
const OUT_DIR = path.resolve('scripts/preview-check');
fs.mkdirSync(OUT_DIR, { recursive: true });

// Strict-clone preview check: reject markers from earlier rejected personal-site builds.
const strictLegacyTokens = [
  '6c756c617a656c',
  '6c756c616d696c65',
  '6d6b68756e67656c612e6c40676d61696c2e636f6d',
  '6c756c617a656c6875622e636f2e7a61',
].map((value) => Buffer.from(value, 'hex').toString('utf8').toLowerCase());

// Customized-clone preview check: reject the requested-to-be-retired branding,
// contacts, award copy, dollar prices and digest references instead.
const customLegacyPatterns = [
  { name: 'old-brand', pattern: /\bCosmos\s+Studio\b|\|\s*Cosmos\b/i },
  { name: 'old-email', pattern: /hello@cosmos\.studio/i },
  { name: 'old-phone', pattern: /\+380\s*63\s*832\s*47\s*31|\+380638324731/ },
  { name: 'old-calendar', pattern: /calendar\.google\.com\/calendar\/u\/0\/appointments/i },
  { name: 'award', pattern: /(?:60\+|international\s+design\s+awards?|international\s+awards?|award-winning|\bawards?\b|awwwards|thefwa|\bfwa\b|css\s+design\s+awards?|css\s+da\b|cssda\s+awards?|red\s+dot|site\s+of\s+the\s+day|dev\s+award|\bsotd\b|\bsotm\b|\bowda\b|winner\s+brand\s+identity|css\s+winner|clutch\s+global(?:\s+awards?|\s+leaders?|\s+2026|\s+fall\s+2026)?|clutch\s*[-–—]?\s*top\s+user\s+research\s+company\s+2026|top\s+user\s+research\s+company\s+2026)/i },
  { name: 'dollar-price', pattern: /\$\s?\d/ },
  { name: 'digest', pattern: /AI\s*&\s*Design Weekly|AI\s+and\s+Design Weekly|Clutch Global Leader/i },
  { name: 'usd-schema', pattern: /priceCurrency"\s*:\s*"USD"|"currency"\s*:\s*"USD"/i },
  { name: 'legacy-api-form', pattern: /\/api\/form/i },
];

const removedBlogSlugs = [
  'canva-video-claude-chatgpt-gemini-mac-tesla-reality-view',
  'gpt-6-2-astra-sol-gemini-4-neon-microsoft-today',
  'claude-meetings-figma-3d-chatgpt-wallet',
  'adobe-creative-cloud-agents-claude-sheets-chatgpt-businesses',
  'clutch-global-award-fall-2026',
  'claude-fable-5-2-gemini-omni-shield-ai-echodyne',
  'chatgpt-chat-work-images-2-6-claude-finance',
  'claude-ultra-chatgpt-pro-limits-salesforce-rune',
  'copilot-fusion-figma-ai-model-suno-mcp',
  'ai-design-weekly-2',
  'ai-design-weekly-1',
];

const FORMSPREE_URL = 'https://formspree.io/f/xvkgqalq';
const CALENDLY_FRAGMENT = 'calendly.com/lulamile_m/meet-lulamile?month=2026-10&date=2026-10-29';
const WHATSAPP_URL = 'https://wa.me/380638324731';
const NEW_EMAIL = 'mkhungela.l@gmail.com';
const NEW_PHONE = '+27 83 719 5064';
const NEW_PRODUCT_STAT = '20+ products launched since 2017';
const NEW_DESIGN_STAT = '1 design awards normination';
const NEW_DESIGN_STAT_RE = /1\s+design\s+awards?\s+normination/i;
const NEW_DESIGN_STAT_GLOBAL_RE = /1\s+design\s+awards?\s+normination/gi;
const SERVICE_DROPDOWN_LABELS = [
  'Web Hosting', 'Website Design', 'Ecommerce', 'Business Systems',
  'Workflow Automation & AI', 'AI Assistants', 'Basic Graphic Design',
  'SEO & Search', 'Google Ads', 'Product Design & Strategy',
];
const WORKS_FILTER_EXPECTED_LABELS = ['All', ...SERVICE_DROPDOWN_LABELS];
const EDIT_PASS_BANNED_RE = /Related services|Services you may also need|Led by an Awwwards jury member|\bPovir\b|\bMad\s+Dogs?\b|Follow our work|WOW version|Facts for AI assistants|Cookie settings|&amp;\s*recognitions|\(Team\)|Latest articles|500\+|since\s+2018|60\+\s*international\s+design\s+awards?/i;
const OLD_OWNER_RE = /\bIllia\s+Kulbachnyi\b|\bKulbachnyi\b|\bIllia\b/;
const REMOVED_ROUTE_MARKERS = [
  ...removedBlogSlugs, 'povir-edtech-platform', 'maddogs-web3-website',
  'legal/ai-instructions', 'povir', 'maddogs', 'mad-dogs', 'mad dogs', 'ai-instructions',
];

const pages = [
  { name: 'home', path: '/', colorScheme: 'light' },
  { name: 'home-dark-scheme', path: '/', colorScheme: 'dark' },
  { name: 'services', path: '/services/website-design', colorScheme: 'light' },
  { name: 'projects', path: '/projects', colorScheme: 'light' },
  { name: 'pricing', path: '/pricing', colorScheme: 'light' },
  { name: 'blog', path: '/blog', colorScheme: 'light' },
  { name: 'contacts', path: '/contacts', colorScheme: 'light' },
];

const failedLocalResponses = [];
const pageErrors = [];
const legacyMarkerHits = [];
const customMarkerIssues = [];
const formActionIssues = [];
const bookCallIssues = [];
const screenshots = [];
const dropdownChecks = [];
const worksFilterChecks = [];
const domChecks = [];
const customChecks = [];
let previewMode = 'unknown';

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

  const pageData = await page.evaluate(() => {
    const navbar = document.querySelector('nav.navbar, .navbar_component');
    const navbarStyle = navbar ? getComputedStyle(navbar) : null;
    const visibleParts = [document.body.innerText];
    document.querySelectorAll('[alt],[title],[aria-label],[aria-valuetext],[content],[placeholder],[value],[label],[data-alt],[data-title]').forEach((element) => {
      ['alt', 'title', 'aria-label', 'aria-valuetext', 'content', 'placeholder', 'value', 'label', 'data-alt', 'data-title'].forEach((attribute) => {
        const value = element.getAttribute(attribute);
        if (value) visibleParts.push(value);
      });
    });
    const forms = [...document.querySelectorAll('form')].map((form) => ({
      method: (form.getAttribute('method') || '').toLowerCase(),
      action: form.getAttribute('action') || '',
    }));
    const bookLinks = [...document.querySelectorAll('a[href]')]
      .filter((anchor) => /book a (?:free discovery )?call/i.test(anchor.innerText || ''))
      .map((anchor) => anchor.getAttribute('href') || '');
    return {
      bodyTextLength: (document.body.innerText || '').trim().length,
      sectionCount: document.querySelectorAll('section').length,
      imageCount: document.querySelectorAll('img').length,
      navbarVisible: !!navbar && navbarStyle.display !== 'none' && navbarStyle.visibility !== 'hidden',
      title: document.title,
      visibleText: visibleParts.join('\n'),
      wordmarkCount: document.querySelectorAll('.lz-wordmark').length,
      forms,
      bookLinks,
    };
  });

  if (item.name === 'home' || previewMode === 'unknown') {
    previewMode = pageData.title.includes('LulaZel Hub') ? 'custom' : 'strict';
  }

  const html = await page.content();
  const bodyText = pageData.visibleText;

  if (previewMode === 'custom') {
    for (const check of customLegacyPatterns) {
      // The WhatsApp URL is intentionally preserved and only its visible number changed.
      if (check.name === 'old-phone') {
        if (check.pattern.test(bodyText.replaceAll(WHATSAPP_URL, ''))) {
          legacyMarkerHits.push({ page: item.name, token: check.name, source: 'visible-text' });
        }
        continue;
      }
      const haystack = ['old-email', 'old-calendar', 'usd-schema', 'legacy-api-form'].includes(check.name)
        ? `${bodyText}\n${html}`
        : bodyText;
      const cleanHaystack = check.name === 'award' ? haystack.replace(NEW_DESIGN_STAT_GLOBAL_RE, '') : haystack;
      if (check.pattern.test(cleanHaystack)) {
        legacyMarkerHits.push({ page: item.name, token: check.name, source: 'visible-text' });
      }
    }
    if (!pageData.title.includes('LulaZel Hub')) customMarkerIssues.push({ page: item.name, issue: 'title missing LulaZel Hub' });
    if (!bodyText.toLowerCase().includes('lulazel hub')) customMarkerIssues.push({ page: item.name, issue: 'body missing LulaZel Hub' });
    if (pageData.wordmarkCount < 1) customMarkerIssues.push({ page: item.name, issue: 'LulaZel Hub wordmark missing' });
    const removedSlug = REMOVED_ROUTE_MARKERS.find((marker) => html.toLowerCase().includes(marker));
    if (removedSlug) customMarkerIssues.push({ page: item.name, issue: `removed route/case marker remains: ${removedSlug}` });
    const cleanVisibleText = bodyText.replace(NEW_DESIGN_STAT_GLOBAL_RE, '');
    if (EDIT_PASS_BANNED_RE.test(cleanVisibleText) || OLD_OWNER_RE.test(cleanVisibleText)) {
      customMarkerIssues.push({ page: item.name, issue: 'removed edit-pass phrase remains visible' });
    }
    if (html.includes('footer_legal-wrap')) {
      customMarkerIssues.push({ page: item.name, issue: 'footer legal section remains' });
    }
    if (item.name === 'home') {
      if (!`${bodyText}\n${html}`.includes(NEW_PRODUCT_STAT)) {
        customMarkerIssues.push({ page: item.name, issue: 'new product stat missing' });
      }
      if (!NEW_DESIGN_STAT_RE.test(`${bodyText}\n${html}`)) {
        customMarkerIssues.push({ page: item.name, issue: 'new design stat missing' });
      }
      const decodedHtml = html.replaceAll('&amp;', '&');
      const missingService = SERVICE_DROPDOWN_LABELS.find((label) => !html.includes(label) && !decodedHtml.includes(label));
      if (missingService) {
        customMarkerIssues.push({ page: item.name, issue: `service dropdown label missing: ${missingService}` });
      }
    }
    for (const form of pageData.forms) {
      if (form.method !== 'post' || form.action !== FORMSPREE_URL) {
        formActionIssues.push({ page: item.name, ...form });
      }
    }
    let sawBookLink = false;
    for (const href of pageData.bookLinks) {
      sawBookLink = true;
      if (!href.includes(CALENDLY_FRAGMENT)) bookCallIssues.push({ page: item.name, href });
    }
    if (!sawBookLink && item.name !== 'home-dark-scheme') {
      customMarkerIssues.push({ page: item.name, issue: 'Book a Call CTA missing' });
    }
    if (item.name === 'contacts') {
      if (!bodyText.includes(NEW_EMAIL)) customMarkerIssues.push({ page: item.name, issue: 'new email missing' });
      if (!bodyText.includes(NEW_PHONE)) customMarkerIssues.push({ page: item.name, issue: 'new phone missing' });
      if (!html.includes(WHATSAPP_URL)) customMarkerIssues.push({ page: item.name, issue: 'WhatsApp URL changed' });
    }
    customChecks.push({
      page: item.name,
      mode: previewMode,
      wordmarkCount: pageData.wordmarkCount,
      formCount: pageData.forms.length,
      bookCallCount: pageData.bookLinks.length,
      title: pageData.title,
    });
  } else {
    const text = bodyText.toLowerCase();
    for (const token of strictLegacyTokens) {
      if (text.includes(token)) legacyMarkerHits.push({ page: item.name, token });
    }
  }

  domChecks.push({
    page: item.name,
    bodyTextLength: pageData.bodyTextLength,
    sectionCount: pageData.sectionCount,
    imageCount: pageData.imageCount,
    navbarVisible: pageData.navbarVisible,
    title: pageData.title,
  });

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
    const expectedOptions = ['For Marketing Teams', 'For You', 'For Tech', 'Something Else'];
    dropdownChecks.push({ defaultLabel, selected: selected.trim(), options: options.map((v) => v.trim()) });
    if (previewMode === 'custom') {
      if (defaultLabel !== 'For You' || selected.trim() !== 'For You') {
        customMarkerIssues.push({ page: item.name, issue: 'For You dropdown default missing' });
      }
      if (JSON.stringify(options.map((v) => v.trim())) !== JSON.stringify(expectedOptions)) {
        customMarkerIssues.push({ page: item.name, issue: 'audience dropdown options changed' });
      }
    }
    screenshots.push({ name: 'dropdown', path: '/', file: path.basename(dropdownScreenshot) });
  }
  await page.close();
}

if (previewMode === 'custom') {
  const page = await context.newPage();
  page.on('pageerror', (error) => pageErrors.push({ page: 'works-filter', message: String(error) }));
  try {
    await page.goto(BASE_URL + '/projects', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);
    const filterData = await page.evaluate(() => {
      const wrappers = [...document.querySelectorAll('.dropdown_wr.w-dropdown')];
      const industries = wrappers.filter((dropdown) => /\bIndustries/i.test(dropdown.textContent || ''));
      const services = wrappers.find((dropdown) =>
        /\bServices/i.test(dropdown.textContent || '') && dropdown.querySelector('[fs-list-field="service"]')
      );
      const labels = services
        ? [...services.querySelectorAll('.w-form-label')].map((label) => (label.textContent || '').trim())
        : [];
      const footerIndustriesGroups = [...document.querySelectorAll('.footer_links-group')]
        .filter((group) => (group.textContent || '').trim().startsWith('Industries')).length;
      const hiddenServiceLabels = [...document.querySelectorAll('div[fs-list-field="service"]')]
        .map((field) => (field.getAttribute('fs-list-value') || field.textContent || '').trim());
      const filterBlock = document.querySelector('.section_works .filter-block.is-case');
      const sectionWorks = document.querySelector('.section_works');
      const ctaSection = document.querySelector('.section_cta');
      const zIndex = (element) => {
        const value = Number.parseInt(getComputedStyle(element).zIndex || '0', 10);
        return Number.isFinite(value) ? value : 0;
      };
      const siblingSections = sectionWorks && sectionWorks.parentElement
        ? [...sectionWorks.parentElement.children].filter((child) => child.tagName && child.tagName.toLowerCase() === 'section')
        : [];
      const worksIndex = sectionWorks ? siblingSections.indexOf(sectionWorks) : -1;
      const laterSections = worksIndex >= 0 ? siblingSections.slice(worksIndex + 1) : [];
      const laterSectionZIndex = Math.max(0, ...laterSections.map(zIndex));
      return {
        industriesFilterCount: industries.length,
        footerIndustriesGroups,
        labels,
        hiddenServiceLabels,
        filterZIndex: filterBlock ? zIndex(filterBlock) : 0,
        sectionZIndex: sectionWorks ? zIndex(sectionWorks) : 0,
        ctaZIndex: ctaSection ? zIndex(ctaSection) : 0,
        laterSectionZIndex,
        sectionOverflow: sectionWorks ? getComputedStyle(sectionWorks).overflow : '',
        hiddenIndustryFields: document.querySelectorAll('[fs-list-field="industry"]').length,
        staleIndustrySearchFields: document.querySelectorAll('[fs-list-field="title, service, industry"]').length,
      };
    });
    if (filterData.industriesFilterCount) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'Industries works filter remains' });
    }
    if (filterData.footerIndustriesGroups) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'Industries footer section remains' });
    }
    if (JSON.stringify(filterData.labels) !== JSON.stringify(WORKS_FILTER_EXPECTED_LABELS)) {
      customMarkerIssues.push({ page: 'works-filter', issue: `works Services labels are wrong: ${filterData.labels.join(' | ')}` });
    }
    if (!SERVICE_DROPDOWN_LABELS.every((label) => filterData.hiddenServiceLabels.includes(label))) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'works service fields do not cover all ten labels' });
    }
    if (filterData.hiddenServiceLabels.some((label) => !SERVICE_DROPDOWN_LABELS.includes(label))) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'old works service filter value remains' });
    }
    if (filterData.filterZIndex < 1000) {
      customMarkerIssues.push({ page: 'works-filter', issue: `works filter z-index too low: ${filterData.filterZIndex}` });
    }
    if (filterData.sectionOverflow !== 'visible') {
      customMarkerIssues.push({ page: 'works-filter', issue: `works section still clips dropdown: ${filterData.sectionOverflow}` });
    }
    if (filterData.sectionZIndex < 31 || filterData.sectionZIndex >= 99) {
      customMarkerIssues.push({ page: 'works-filter', issue: `works section stacking z-index is wrong: ${filterData.sectionZIndex}` });
    }
    if (filterData.sectionZIndex <= filterData.ctaZIndex) {
      customMarkerIssues.push({ page: 'works-filter', issue: `works section is not above the CTA section: ${filterData.sectionZIndex} <= ${filterData.ctaZIndex}` });
    }
    if (filterData.sectionZIndex <= filterData.laterSectionZIndex) {
      customMarkerIssues.push({ page: 'works-filter', issue: `works section is not above later sections: ${filterData.sectionZIndex} <= ${filterData.laterSectionZIndex}` });
    }
    if (filterData.hiddenIndustryFields) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'hidden industry filter fields remain' });
    }
    if (filterData.staleIndustrySearchFields) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'stale industry search field remains' });
    }
    const toggle = page.locator('.dropdown_wr.w-dropdown')
      .filter({ hasText: 'Services' })
      .locator('.w-dropdown-toggle')
      .first();
    if (await toggle.count()) {
      await toggle.click({ timeout: 5000 });
      await page.waitForTimeout(500);
    } else {
      customMarkerIssues.push({ page: 'works-filter', issue: 'Services works filter toggle missing' });
    }
    const geometry = await page.evaluate(() => {
      const list = document.querySelector('.dropdown_wr.w-dropdown .dropdown_open.w--open');
      if (!list) return { open: false };
      const rect = list.getBoundingClientRect();
      const x = rect.left + Math.min(rect.width / 2, 120);
      const sampleYs = [0.05, 0.25, 0.5, 0.75, 0.95]
        .map((ratio) => rect.top + rect.height * ratio)
        .filter((y) => y >= rect.top && y <= rect.bottom && y >= 0 && y < window.innerHeight);
      const hits = sampleYs.map((y) => {
        const hit = document.elementFromPoint(x, y);
        return {
          y: Math.round(y),
          onTop: !!hit && (list === hit || list.contains(hit)),
          hit: hit ? (hit.className || hit.tagName) : null,
        };
      });
      const cta = document.querySelector('.section_cta');
      const ctaRect = cta ? cta.getBoundingClientRect() : null;
      let overlapOnTop = null;
      let overlapY = null;
      if (ctaRect && ctaRect.top < window.innerHeight && ctaRect.top < rect.bottom && ctaRect.bottom > rect.top) {
        overlapY = Math.min(rect.bottom - 10, Math.max(rect.top + 10, ctaRect.top + 10));
        if (overlapY >= rect.top && overlapY <= rect.bottom && overlapY <= window.innerHeight) {
          const hit = document.elementFromPoint(x, overlapY);
          overlapOnTop = !!hit && (list === hit || list.contains(hit));
        }
      }
      return {
        open: true,
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        top: Math.round(rect.top),
        bottom: Math.round(rect.bottom),
        onTop: hits.length > 0 && hits.every((hit) => hit.onTop),
        hits,
        ctaTop: ctaRect ? Math.round(ctaRect.top) : null,
        overlapY: overlapY === null ? null : Math.round(overlapY),
        overlapOnTop,
        listZIndex: getComputedStyle(list).zIndex,
      };
    });
    if (!geometry.open) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'Services works filter did not open' });
    } else if (!geometry.onTop) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'Services works filter is behind another element' });
    } else if (geometry.overlapOnTop === false) {
      customMarkerIssues.push({ page: 'works-filter', issue: 'Services works filter is behind the following section' });
    }
    const screenshot = path.join(OUT_DIR, 'works-services.png');
    await page.screenshot({ path: screenshot, fullPage: false, animations: 'allow' });
    screenshots.push({ name: 'works-services', path: '/projects', file: path.basename(screenshot) });
    worksFilterChecks.push({ ...filterData, ...geometry });
  } catch (error) {
    customMarkerIssues.push({ page: 'works-filter', issue: `works filter check failed: ${String(error)}` });
  } finally {
    await page.close();
  }
}

await browser.close();

const report = {
  baseURL: BASE_URL,
  previewMode,
  viewport: { width: 1440, height: 1000 },
  screenshots,
  dropdownChecks,
  worksFilterChecks,
  domChecks,
  customChecks,
  failedLocalResponses,
  pageErrors,
  legacyMarkerHits,
  customMarkerIssues,
  formActionIssues,
  bookCallIssues,
};
fs.writeFileSync(path.join(OUT_DIR, 'browser-report.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
