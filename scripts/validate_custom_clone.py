#!/usr/bin/env python3
"""Validate the customized LulaZel Hub static clone.

Checks the requested rebrand/contact/currency/blog/form/CTA changes and all
local references. Writes a machine-readable report for the preview workflow.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, Comment

ROOT = Path(os.environ.get("LZ_ROOT", Path(__file__).resolve().parents[1]))
SITE = ROOT / "cosmos-copy"
SCRIPTS = ROOT / "scripts"
REPORT_FILE = SCRIPTS / "custom-validation-report.json"
LEGACY_REPORT_FILE = SCRIPTS / "cosmos-validation-report.json"
RUN_LOG = SCRIPTS / "validate-custom-last-run.txt"
LEGACY_RUN_LOG = SCRIPTS / "validate-last-run.txt"

NEW_BRAND = "LulaZel Hub"
OLD_BRAND_RE = re.compile(r"\bCosmos\s+Studio\b|\|\s*Cosmos\b", re.I)
OLD_EMAIL = "hello@cosmos.studio"
NEW_EMAIL = "mkhungela.l@gmail.com"
OLD_PHONE = "+380 63 832 47 31"
NEW_PHONE = "+27 83 719 5064"
WHATSAPP_URL = "https://wa.me/380638324731"
OLD_CALENDAR_FRAGMENT = "calendar.google.com/calendar/u/0/appointments/schedules/"
CALENDLY_FRAGMENT = "calendly.com/lulamile_m/meet-lulamile?month=2026-10&date=2026-10-29"
FORMSPREE_URL = "https://formspree.io/f/xvkgqalq"
AWARD_RE = re.compile(
    r"(?:60\+|international\s+design\s+awards?|international\s+awards?"
    r"|award-winning|\bawards?\b|awwwards|thefwa|\bfwa\b"
    r"|css\s+design\s+awards?|css\s+da\b|cssda\s+awards?|red\s+dot"
    r"|site\s+of\s+the\s+day|dev\s+award|\bsotd\b|\bsotm\b|\bowda\b"
    r"|winner\s+brand\s+identity|css\s+winner"
    r"|clutch\s+global(?:\s+awards?|\s+leaders?|\s+2026|\s+fall\s+2026)?"
    r"|clutch\s*[-–—]?\s*top\s+user\s+research\s+company\s+2026"
    r"|top\s+user\s+research\s+company\s+2026)",
    re.I,
)
MONEY_RE = re.compile(r"\$\s?\d")


def award_mention(value: str) -> bool:
    """Ignore the exact new nomination claim while detecting legacy awards."""
    return bool(AWARD_RE.search(NEW_DESIGN_STAT_RE.sub("", value)))
DIGEST_RE = re.compile(r"AI\s*&\s*(?:amp;)?\s*Design Weekly|AI\s+and\s+Design Weekly|Clutch Global Leader", re.I)
REMOVED_BLOG_SLUGS = {
    "canva-video-claude-chatgpt-gemini-mac-tesla-reality-view",
    "gpt-6-2-astra-sol-gemini-4-neon-microsoft-today",
    "claude-meetings-figma-3d-chatgpt-wallet",
    "adobe-creative-cloud-agents-claude-sheets-chatgpt-businesses",
    "clutch-global-award-fall-2026",
    "claude-fable-5-2-gemini-omni-shield-ai-echodyne",
    "chatgpt-chat-work-images-2-6-claude-finance",
    "claude-ultra-chatgpt-pro-limits-salesforce-rune",
    "copilot-fusion-figma-ai-model-suno-mcp",
    "ai-design-weekly-2",
    "ai-design-weekly-1",
}
REMOVED_CASE_SLUGS = {
    "povir-edtech-platform",
    "maddogs-web3-website",
}
REMOVED_ROUTE_SLUGS = REMOVED_BLOG_SLUGS | REMOVED_CASE_SLUGS | {"legal/ai-instructions"}
REMOVED_ROUTE_MARKERS = {
    *(slug.lower() for slug in REMOVED_ROUTE_SLUGS),
    "povir",
    "maddogs",
    "mad-dogs",
    "mad dogs",
    "ai-instructions",
}
NEW_PRODUCT_STAT = "20+ products launched since 2017"
NEW_DESIGN_STAT = "1 design awards normination"
NEW_DESIGN_STAT_RE = re.compile(r"1\s+design\s+awards?\s+normination", re.I)
OWNER_NAME = "Lulamile Mkhungela"
OWNER_IMAGE = "/assets/img/lulamile.webp"
SERVICE_DROPDOWN_LABELS = [
    "Web Hosting", "Website Design", "Ecommerce", "Business Systems",
    "Workflow Automation & AI", "AI Assistants", "Basic Graphic Design",
    "SEO & Search", "Google Ads", "Product Design & Strategy",
]
EDIT_PASS_BANNED_RE = re.compile(
    r"Related services|Services you may also need|Led by an Awwwards jury member"
    r"|\bPovir\b|\bMad\s+Dogs?\b|Follow our work|WOW version"
    r"|Facts for AI assistants|Cookie settings|&amp;\s*recognitions|\(Team\)"
    r"|Latest articles|500\+|since\s+2018"
    r"|60\+\s*international\s+design\s+awards?",
    re.I,
)
OLD_OWNER_RE = re.compile(r"\bIllia\s+Kulbachnyi\b|\bKulbachnyi\b|\bIllia\b")
KEEP_BLOG_SLUGS = {
    "pitch-deck-design-services",
    "military-symbology-ui-design",
    "ai-product-design-agencies",
    "how-to-choose-ui-ux-design-agency",
    "ui-ux-design-cost-startup",
    "c2-interface-design",
    "defense-tech-design-agencies",
    "defense-tech-pitch-deck",
    "b2b-saas-dashboard-design-patterns",
    "fix-vibe-coded-mvp-lovable-bolt-cursor",
    "ux-audit-cost",
    "how-to-choose-ui-ux-agency-defense-tech",
}
DROPDOWN_LABELS = ["For Marketing Teams", "For You", "For Tech", "Something Else"]
TEXT_SUFFIXES = {".html", ".css", ".js", ".mjs", ".json", ".svg", ".xml", ".txt", ".md"}
VISIBLE_ATTRS = [
    "alt", "title", "aria-label", "aria-valuetext", "placeholder", "content",
    "value", "data-name", "label", "data-alt", "data-title", "data-cat",
]
URL_ATTRS = [
    "href", "src", "srcset", "poster", "data-src", "data-srcset",
    "data-poster", "data-video", "content", "action", "style",
    "data-bg", "data-image", "data-wf-bg", "data-background-image",
]
SRCSET_ATTRS = {"srcset", "data-srcset"}
LOCAL_ASSET_PREFIXES = ("/assets/", "/_c/", "/_m/", "/_next/", "/fonts/", "/img/", "/css/", "/js/", "/video/", "/videos/")
LOCAL_ASSET_RE = re.compile(r"/[A-Za-z0-9_\-./%~+]+\.(?:css|mjs|js|woff2?|ttf|otf|png|jpe?g|webp|avif|svg|gif|ico|mp4|webm|mov|json|lottie|pdf|txt|xml)(?:\?[^\s\"'`<>)\\]*)?", re.I)
STYLE_URL_RE = re.compile(r"url\(\s*['\"]?([^)'\"]+)", re.I)
CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^)'\"]+)", re.I)

issues: list[str] = []
warnings: list[str] = []
REDIRECTS: dict[str, dict] = {}


def load_redirects() -> None:
    global REDIRECTS
    for path in [SCRIPTS / "cosmos-redirects.json", SITE / "redirects.json"]:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    REDIRECTS.update(data)
            except (ValueError, TypeError):
                pass


def safe_rel(path: str) -> str:
    path = unquote(path).replace("\\", "/")
    parts = []
    for part in path.split("/"):
        if part in {"", ".", ".."}:
            continue
        parts.append(part)
    return "/".join(parts)


def normalized_route(path: str) -> str:
    p = urlsplit(html.unescape(path)).path
    p = unquote(p) or "/"
    if p != "/":
        p = p.rstrip("/") or "/"
    return p


def local_target(path: str) -> list[Path]:
    p = urlsplit(html.unescape(path))
    rel = p.path
    if rel in {"", "/"}:
        return [SITE / "index.html"]
    rel = safe_rel(rel)
    candidates = [SITE / rel]
    if not rel.endswith(".html"):
        candidates.append(SITE / rel / "index.html")
    if not Path(rel).suffix:
        candidates.append(SITE / f"{rel}.html")
    return candidates


def local_path_exists(path: str) -> bool:
    if any(candidate.exists() for candidate in local_target(path)):
        return True
    route = normalized_route(path)
    return route in REDIRECTS or (route + "/") in REDIRECTS


def is_external_or_special(value: str) -> bool:
    value = html.unescape(value.strip())
    return (
        not value
        or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "sms:", "whatsapp:"))
        or value.startswith("//")
        or value.startswith(("http://", "https://"))
    )


def check_local_ref(path: str, source: Path, attr: str) -> None:
    value = html.unescape(path.strip())
    if is_external_or_special(value):
        return
    if attr == "content" and not value.startswith(("/", "./", "../")):
        return
    if value.startswith(LOCAL_ASSET_PREFIXES) or Path(urlsplit(value).path).suffix:
        if not local_path_exists(value):
            issues.append(f"missing local reference in {source.relative_to(ROOT)} [{attr}]: {value}")
    elif not local_path_exists(value):
        issues.append(f"missing local route in {source.relative_to(ROOT)} [{attr}]: {value}")


def split_attr_values(value: str, attr: str = "") -> list[str]:
    value = html.unescape(value)
    if attr in SRCSET_ATTRS and "," in value:
        return [chunk.strip().split()[0] for chunk in value.split(",") if chunk.strip()]
    if "," in value and re.search(r"\s+\d+(\.\d+)?[wx]\b", value):
        return [chunk.strip().split()[0] for chunk in value.split(",") if chunk.strip()]
    return [value]


def looks_like_ref(value: str) -> bool:
    value = html.unescape(value.strip())
    if not value:
        return False
    return value.startswith(("/", "./", "../", "//", "http://", "https://")) or "/" in value or bool(Path(urlsplit(value).path).suffix)


def visible_strings(soup: BeautifulSoup) -> list[str]:
    strings = [
        str(node) for node in soup.find_all(string=True)
        if not isinstance(node, Comment) and not (node.parent and node.parent.name in {"script", "style"})
    ]
    for tag in soup.find_all(True):
        for attr in VISIBLE_ATTRS:
            value = tag.get(attr)
            if isinstance(value, str):
                strings.append(value)
    return strings


def validate_html(path: Path, counters: Counter) -> None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    counters["html_pages"] += 1
    if not soup.html:
        issues.append(f"missing html element: {path.relative_to(ROOT)}")
        return
    if soup.html.get("data-view") != "you" or soup.html.get("data-view-label") != "For You":
        issues.append(f"For You default missing: {path.relative_to(ROOT)}")
    canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
    if not canonical or "cosmos.studio" not in (canonical.get("href") or ""):
        issues.append(f"Cosmos canonical link missing/changed: {path.relative_to(ROOT)}")
    dropdown = soup.select_one("[data-cosmos-audience]")
    if not dropdown:
        issues.append(f"audience dropdown missing: {path.relative_to(ROOT)}")
    else:
        labels = [option.get_text(" ", strip=True) for option in dropdown.select("[data-view-option]")]
        if labels != DROPDOWN_LABELS:
            issues.append(f"dropdown options wrong in {path.relative_to(ROOT)}: {labels}")
        selected = dropdown.select_one(".cosmos-audience_option.is-selected")
        if not selected or selected.get_text(" ", strip=True) != "For You":
            issues.append(f"For You not selected in {path.relative_to(ROOT)}")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if NEW_BRAND not in title:
        issues.append(f"LulaZel Hub missing from title: {path.relative_to(ROOT)}")
    visible = "\n".join(visible_strings(soup))
    if OLD_BRAND_RE.search(visible):
        issues.append(f"old Cosmos brand remains visible in {path.relative_to(ROOT)}")
    if award_mention(visible):
        issues.append(f"award mention remains visible in {path.relative_to(ROOT)}")
    if EDIT_PASS_BANNED_RE.search(visible) or OLD_OWNER_RE.search(visible):
        issues.append(f"removed edit-pass phrase remains visible in {path.relative_to(ROOT)}")
    if MONEY_RE.search(visible):
        issues.append(f"dollar currency remains visible in {path.relative_to(ROOT)}")
    if DIGEST_RE.search(visible):
        issues.append(f"removed digest/award post mention remains visible in {path.relative_to(ROOT)}")
    if OLD_EMAIL.lower() in raw.lower():
        issues.append(f"old email remains in {path.relative_to(ROOT)}")
    if OLD_PHONE in raw or "+380638324731" in raw:
        issues.append(f"old phone remains in {path.relative_to(ROOT)}")
    if OLD_CALENDAR_FRAGMENT in raw:
        issues.append(f"old calendar URL remains in {path.relative_to(ROOT)}")
    if "'/api/form'" in raw or '"/api/form"' in raw:
        issues.append(f"legacy /api/form remains in {path.relative_to(ROOT)}")
    if any(marker in raw.lower() for marker in REMOVED_ROUTE_MARKERS):
        issues.append(f"removed route/case slug remains in {path.relative_to(ROOT)}")
    if EDIT_PASS_BANNED_RE.search(raw) or OLD_OWNER_RE.search(raw):
        issues.append(f"removed edit-pass phrase remains in {path.relative_to(ROOT)}")
    if path.as_posix().endswith("contacts/index.html"):
        if WHATSAPP_URL not in raw:
            issues.append("WhatsApp URL was changed")
        if f"{NEW_PHONE} · WhatsApp" not in raw:
            issues.append("new visible WhatsApp number missing")
        if NEW_EMAIL not in raw:
            issues.append("new email missing from contacts page")
    if 'class="lz-wordmark' not in raw:
        issues.append(f"LulaZel wordmark missing in {path.relative_to(ROOT)}")
    counters["wordmark_pages"] += 1 if 'class="lz-wordmark' in raw else 0
    for form in soup.find_all("form"):
        counters["forms"] += 1
        if form.get("method", "").lower() != "post" or form.get("action") != FORMSPREE_URL:
            issues.append(f"form does not POST to Formspree in {path.relative_to(ROOT)}")
        else:
            counters["forms_formspree"] += 1
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True).lower()
        if "book a call" in label or "book a discovery call" in label or "book a free discovery call" in label:
            counters["book_call_links"] += 1
            if CALENDLY_FRAGMENT not in html.unescape(anchor["href"]):
                issues.append(f"Book a Call link not Calendly in {path.relative_to(ROOT)}: {anchor['href']}")
            else:
                counters["book_call_calendly"] += 1
    for script in soup.find_all("script", type=lambda value: value and "ld+json" in value):
        text = script.string or ""
        if OLD_BRAND_RE.search(text):
            issues.append(f"old brand remains in structured data in {path.relative_to(ROOT)}")
        if OLD_EMAIL in text or "+380638324731" in text:
            issues.append(f"old contact remains in structured data in {path.relative_to(ROOT)}")
        if OLD_CALENDAR_FRAGMENT in text:
            issues.append(f"old calendar URL remains in structured data in {path.relative_to(ROOT)}")
        if 'priceCurrency":"USD' in text or '"currency":"USD' in text:
            issues.append(f"USD remains in structured data in {path.relative_to(ROOT)}")
        if MONEY_RE.search(text):
            issues.append(f"dollar currency remains in structured data in {path.relative_to(ROOT)}")
    for tag in soup.find_all(True):
        for attr in URL_ATTRS:
            value = tag.get(attr)
            if not isinstance(value, str):
                continue
            if attr == "style":
                for item in STYLE_URL_RE.findall(value):
                    check_local_ref(item, path, attr)
                continue
            for item in split_attr_values(value, attr):
                if attr in {"content", "data-video", "data-bg", "data-image", "data-wf-bg", "data-background-image"} and not looks_like_ref(item):
                    continue
                check_local_ref(item, path, attr)


def validate_css_refs(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except UnicodeDecodeError:
        return
    for ref in CSS_URL_RE.findall(text):
        if ref.startswith(("http://", "https://", "//", "data:", "#")):
            continue
        check_local_ref(ref, path, "css url()")


def validate_text_assets() -> None:
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or path.name.endswith(".html"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except UnicodeDecodeError:
            continue
        if any(marker in text.lower() for marker in REMOVED_ROUTE_MARKERS):
            issues.append(f"removed route/case slug remains in {path.relative_to(ROOT)}")
        if path.suffix.lower() == ".js" and re.search(r"Cookie settings|Clutch 2026 award|textContent='Awards'|data-clutch-badge", text, re.I):
            issues.append(f"removed JS injection remains in {path.relative_to(ROOT)}")
        if path.suffix.lower() in {".txt", ".md", ".xml", ".svg"} and (EDIT_PASS_BANNED_RE.search(text) or OLD_OWNER_RE.search(text)):
            issues.append(f"removed edit-pass phrase remains in {path.relative_to(ROOT)}")
        if re.search(re.escape(OLD_EMAIL), text, re.I):
            issues.append(f"old email remains in {path.relative_to(ROOT)}")
        if OLD_CALENDAR_FRAGMENT in text:
            issues.append(f"old calendar URL remains in {path.relative_to(ROOT)}")
        if re.search(r"['\"]/api/form['\"]", text):
            issues.append(f"legacy /api/form remains in {path.relative_to(ROOT)}")
        # Minified vendor JS contains harmless regex replacements like "$1".
        # Base64 data blobs and bundled game JS also contain accidental "60+"
        # strings that are not visible award copy. Only a clean word-boundary
        # phrase in plain text/embedded SVG <text> nodes counts as an award.
        if path.suffix.lower() in {".svg", ".xml", ".txt", ".md"}:
            if path.suffix.lower() in {".svg", ".xml"}:
                visible_text = " ".join(
                    match.group(1)
                    for match in re.finditer(r"<(?:text|title|desc)[^>]*>(.*?)</(?:text|title|desc)>", text, re.I | re.S)
                )
                visible_text += " " + " ".join(
                    match.group(1)
                    for match in re.finditer(
                        r"(?:alt|title|aria-label|content|value|label|data-alt|data-title)=\"([^\"]*)\"",
                        text,
                        re.I,
                    )
                )
            else:
                visible_text = " ".join(
                    line.strip()
                    for line in text.splitlines()
                    if line.strip() and not re.search(r"[=;{}]", line)
                )
            if MONEY_RE.search(visible_text):
                issues.append(f"dollar currency remains in {path.relative_to(ROOT)}")
            if award_mention(visible_text):
                issues.append(f"award mention remains in {path.relative_to(ROOT)}")
        if path.suffix.lower() == ".css":
            validate_css_refs(path)


def validate_rss() -> None:
    for path in [SITE / "blog" / "rss.xml", SITE / "rss.xml"]:
        if not path.exists():
            issues.append(f"RSS missing: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        items = re.findall(r"<item>.*?</item>", text, re.S | re.I)
        if len(items) != 12:
            issues.append(f"RSS has {len(items)} items, expected 12: {path.relative_to(ROOT)}")
        if any(slug in text for slug in REMOVED_BLOG_SLUGS):
            issues.append(f"removed blog slug remains in {path.relative_to(ROOT)}")
        if OLD_BRAND_RE.search(text):
            issues.append(f"old brand remains in {path.relative_to(ROOT)}")
        if MONEY_RE.search(text):
            issues.append(f"dollar currency remains in {path.relative_to(ROOT)}")


def validate_blog_index() -> None:
    path = SITE / "blog" / "index.html"
    if not path.exists():
        issues.append("blog index missing")
        return
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    cards = soup.select(".blog_item-v3")
    if len(cards) != 12:
        issues.append(f"blog index has {len(cards)} cards, expected 12")
    hrefs = [a.get("href", "") for card in cards for a in card.find_all("a", href=True)]
    for slug in KEEP_BLOG_SLUGS:
        if not any(slug in href for href in hrefs):
            issues.append(f"kept blog slug missing from index: {slug}")
    if soup.select_one(".w-pagination-wrapper"):
        issues.append("blog pagination for removed posts remains")


def validate_manifests() -> None:
    canonical_file = SCRIPTS / "cosmos-canonical-urls.txt"
    urls = [line.strip() for line in canonical_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(urls) != 98:
        issues.append(f"canonical URL count is {len(urls)}, expected 98")
    if any(marker in url.lower() for marker in REMOVED_ROUTE_MARKERS for url in urls):
        issues.append("removed route/case slug remains in canonical URL list")
    for path in [ROOT / "sitemap.xml", SITE / "sitemap.xml"]:
        if not path.exists():
            issues.append(f"sitemap missing: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        locs = re.findall(r"<loc>(.*?)</loc>", text, re.S)
        if len(locs) != 98:
            issues.append(f"sitemap has {len(locs)} URLs, expected 98: {path.relative_to(ROOT)}")
        if any(marker in loc.lower() for marker in REMOVED_ROUTE_MARKERS for loc in locs):
            issues.append(f"removed route/case slug remains in {path.relative_to(ROOT)}")
    for name in [
        "cosmos-canonical-urls.txt", "cosmos-sitemap-raw.txt", "cosmos-site-file-list.txt",
        "cosmos-site-file-sizes.txt", "fetch-build-last-run.txt", "validate-last-run.txt",
        "cosmos-live-build-report.json", "cosmos-asset-map.json",
        "cosmos-remaining-remote-assets.json", "cosmos-repair-report.json",
        "cosmos-redirects.json",
    ]:
        path = SCRIPTS / name
        if path.exists() and any(marker in path.read_text(encoding="utf-8", errors="replace").lower() for marker in REMOVED_ROUTE_MARKERS):
            issues.append(f"removed route/case slug remains in {path.relative_to(ROOT)}")
    for name in ["build-manifest.json", "asset-map.json", "remaining-remote-assets.json", "redirects.json", "_redirects"]:
        path = SITE / name
        if path.exists() and any(marker in path.read_text(encoding="utf-8", errors="replace").lower() for marker in REMOVED_ROUTE_MARKERS):
            issues.append(f"removed route/case slug remains in {path.relative_to(ROOT)}")


def validate_repository_text() -> None:
    """Check non-code diagnostics/manifests for requested rebrand cleanup."""
    paths = [
        ROOT / "README.md",
        ROOT / "robots.txt",
        ROOT / "sitemap.xml",
    ]
    paths += [
        path
        for path in SCRIPTS.rglob("*")
        if path.is_file() and path.suffix.lower() in {".txt", ".json", ".md", ".xml"}
    ]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        without_wa = text.replace(WHATSAPP_URL, "")
        clean_lines = " ".join(
            line.strip()
            for line in text.splitlines()
            if line.strip() and len(line) < 500 and not re.search(r"[=;{}]", line)
        )
        if OLD_BRAND_RE.search(text):
            issues.append(f"old brand remains in {path.relative_to(ROOT)}")
        if re.search(re.escape(OLD_EMAIL), text, re.I):
            issues.append(f"old email remains in {path.relative_to(ROOT)}")
        if OLD_PHONE in without_wa or "+380638324731" in without_wa:
            issues.append(f"old phone remains in {path.relative_to(ROOT)}")
        if OLD_CALENDAR_FRAGMENT in text:
            issues.append(f"old calendar URL remains in {path.relative_to(ROOT)}")
        if re.search(r"['\"]/api/form['\"]", text):
            issues.append(f"legacy /api/form remains in {path.relative_to(ROOT)}")
        if MONEY_RE.search(clean_lines):
            issues.append(f"dollar currency remains in {path.relative_to(ROOT)}")
        if award_mention(clean_lines):
            issues.append(f"award mention remains in {path.relative_to(ROOT)}")
        if any(marker in text.lower() for marker in REMOVED_ROUTE_MARKERS):
            issues.append(f"removed route/case slug remains in {path.relative_to(ROOT)}")
        if EDIT_PASS_BANNED_RE.search(clean_lines) or OLD_OWNER_RE.search(clean_lines):
            issues.append(f"removed edit-pass phrase remains in {path.relative_to(ROOT)}")


def validate_logo_and_bridge() -> None:
    logo = SITE / "assets" / "img" / "cosmos-logo.svg"
    if not logo.exists() or NEW_BRAND not in logo.read_text(encoding="utf-8", errors="replace"):
        issues.append("small logo SVG was not renamed")
    bridge = SITE / "_c" / "wf-form-bridge.v2.js"
    if not bridge.exists():
        issues.append("form bridge missing")
        return
    text = bridge.read_text(encoding="utf-8", errors="replace")
    if FORMSPREE_URL not in text:
        issues.append("form bridge does not point to Formspree")
    if re.search(r"['\"]/api/form['\"]", text):
        issues.append("form bridge still references /api/form")
    if OLD_EMAIL in text:
        issues.append("form bridge still references old email")


def validate_edit_pass(html_files: list[Path]) -> None:
    index = SITE / "index.html"
    if not index.exists():
        issues.append("index.html missing for edit-pass checks")
        return
    soup = BeautifulSoup(index.read_text(encoding="utf-8", errors="replace"), "html.parser")
    nav_dropdowns = soup.select(".navbar_links-wrap .w-dropdown, .menu_links-wrap .w-dropdown")
    services = [
        dropdown for dropdown in nav_dropdowns
        if "Services" in dropdown.get_text(" ", strip=True)
    ]
    if not services:
        issues.append("Services dropdown missing from navigation")
    else:
        for dropdown in services:
            labels = [anchor.get_text(" ", strip=True) for anchor in dropdown.select("a.dropdown-link")]
            if labels != SERVICE_DROPDOWN_LABELS:
                issues.append(f"Services dropdown labels are wrong: {labels}")
    if any("Industries" in dropdown.get_text(" ", strip=True) for dropdown in nav_dropdowns):
        issues.append("Industries dropdown remains in top navigation or mobile menu")
    if not (SITE / "assets" / "img" / "lulamile.webp").exists():
        issues.append("owner image missing")
    for rel in ("projects/povir-edtech-platform", "projects/maddogs-web3-website", "legal/ai-instructions"):
        if (SITE / rel).exists():
            issues.append(f"removed page remains: {rel}")
    product_seen = any(NEW_PRODUCT_STAT in path.read_text(encoding="utf-8", errors="replace") for path in html_files)
    design_seen = any(NEW_DESIGN_STAT_RE.search(path.read_text(encoding="utf-8", errors="replace")) for path in html_files)
    if not product_seen:
        issues.append("new product stat missing from HTML")
    if not design_seen:
        issues.append("new design nomination stat missing from HTML")


def main() -> int:
    load_redirects()
    counters: Counter = Counter()
    html_files = sorted(SITE.rglob("*.html"))
    for path in html_files:
        validate_html(path, counters)
    validate_text_assets()
    validate_rss()
    validate_blog_index()
    validate_manifests()
    validate_repository_text()
    validate_logo_and_bridge()
    validate_edit_pass(html_files)
    site_files = [p for p in SITE.rglob("*") if p.is_file()]
    site_bytes = sum(p.stat().st_size for p in site_files)
    rss_items = len(re.findall(r"<item>", (SITE / "blog" / "rss.xml").read_text(encoding="utf-8", errors="replace")))
    canonical_count = len([line for line in (SCRIPTS / "cosmos-canonical-urls.txt").read_text(encoding="utf-8").splitlines() if line.strip()])
    report = {
        "issues": len(issues),
        "issue_samples": issues[:30],
        "warnings": warnings,
        "canonical_urls": canonical_count,
        "html_pages": len(html_files),
        "site_files": len(site_files),
        "site_bytes": site_bytes,
        "kept_blog_posts": 12,
        "rss_items": rss_items,
        "blog_cards": len(BeautifulSoup((SITE / "blog" / "index.html").read_text(encoding="utf-8", errors="replace"), "html.parser").select(".blog_item-v3")),
        "removed_blog_posts": len(REMOVED_BLOG_SLUGS),
        "forms": counters["forms"],
        "forms_posting_to_formspree": counters["forms_formspree"],
        "book_call_links": counters["book_call_links"],
        "book_call_links_to_calendly": counters["book_call_calendly"],
        "wordmark_pages": counters["wordmark_pages"],
        "usd_zar_rate": "R18 per 1 USD",
        "formspree": FORMSPREE_URL,
        "calendly": "https://calendly.com/lulamile_m/meet-lulamile?month=2026-10&date=2026-10-29",
        "whatsapp_url_preserved": WHATSAPP_URL,
    }
    legacy_report = {
        "all_issues": issues,
        "asset_status_counts": {},
        "canonical_counts": {},
        "canonical_urls": canonical_count,
        "exact_pages": len(html_files) - 6,
        "html_pages": len(html_files),
        "issue_samples": issues[:30],
        "issues": len(issues),
        "localized_assets": 0,
        "redirects": len(REDIRECTS),
        "remaining_remote_assets": 0,
        "site_bytes": site_bytes,
        "site_files": len(site_files),
        "warnings": warnings,
        "customization": report,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    LEGACY_REPORT_FILE.write_text(json.dumps(legacy_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = json.dumps(report, indent=2, sort_keys=True)
    RUN_LOG.write_text(summary + "\n", encoding="utf-8")
    LEGACY_RUN_LOG.write_text(summary + "\n", encoding="utf-8")
    print(summary)
    if issues:
        print(f"custom clone validation failed with {len(issues)} issues", file=sys.stderr)
        return 1
    print("custom clone validation clean: 0 issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
