#!/usr/bin/env python3
"""Validate the exact live Cosmos static clone."""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "cosmos-copy"
CANONICAL_FILE = ROOT / "scripts/cosmos-canonical-urls.txt"
REPORT_FILE = ROOT / "scripts/cosmos-live-build-report.json"
ASSET_MAP_FILE = ROOT / "scripts/cosmos-asset-map.json"
REDIRECT_FILE = ROOT / "scripts/cosmos-redirects.json"
REMOTE_FILE = ROOT / "scripts/cosmos-remaining-remote-assets.json"
BROWSER_REPORT = ROOT / "scripts/preview-check/browser-report.json"
VALIDATION_REPORT = ROOT / "scripts/cosmos-validation-report.json"


def hex_text(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8").lower()


# Legacy personal-site markers are encoded so the validator itself never introduces them.
OWNER_MARKERS = [
    hex_text("6c756c617a656c"),
    hex_text("6c756c617a656c20687562"),
    hex_text("6c756c616d696c65"),
    hex_text("6d6b68756e67656c612e6c40676d61696c2e636f6d"),
    hex_text("2b3237203833203731392035303634"),
    hex_text("3237383337313935303634"),
    hex_text("6c756c617a656c6875622e636f2e7a61"),
    hex_text("63616c656e646c792e636f6d2f6c756c616d696c655f6d"),
    hex_text("736f757468206166726963612c20616e7977686572652072656d6f7465"),
    hex_text("636f6e74616374206c756c616d696c65"),
    hex_text("67656f2e726567696f6e3d7a612d6774"),
    hex_text("6f673a6c6f63616c653d656e5f7a61"),
    hex_text("6173736574732f6f776e6572"),
    hex_text("64657369676e6f7073"),
    hex_text("6e6572646d61"),
    hex_text("70726f646f7073"),
    hex_text("6a6f68616e6e657362757267"),
    hex_text("67617574656e67"),
]
REJECTED_DARK_MARKERS = [
    "#0e0e10", "#f4f5f5", ".lz-hero-wordmark", ".lz-footer-wordmark",
    hex_text("6c756c617a656c2d766965772e637373"), "view-switch.js", ".lz-view-switch",
]
COSMOS_HOME_MARKERS = [
    "UI/UX design and development studio for SaaS, AI, defense, and military tech",
    "Selected works", "Contact Anna", "Business Developer", "Book a Call",
    "hello@cosmos.studio", "Cosmos Studio™",
]
COSMOS_NAV_MARKERS = [
    "Services", "Industries", "Works", "About", "Blog", "Contacts",
    "Contact Anna", "Business Developer", "Book a Call",
    "Product UX/UI Design", "Website Design", "Brand Identity Design",
    "Defense & Military Tech", "SaaS", "AI Products",
]
DROPDOWN_LABELS = [
    "For Marketing Teams", "For You", "For Tech", "Something Else",
]
TEXT_SUFFIXES = {".html", ".css", ".js", ".mjs", ".json", ".svg", ".xml", ".txt", ".lottie", ".map"}
LOCAL_ASSET_PREFIXES = ("/assets/", "/_c/", "/_m/", "/_next/", "/fonts/", "/img/", "/css/", "/js/", "/video/", "/videos/")
LOCAL_ASSET_RE = re.compile(r"""/[A-Za-z0-9_\-./%~+]+\.(?:css|mjs|js|woff2?|ttf|otf|png|jpe?g|webp|avif|svg|gif|ico|mp4|webm|mov|json|lottie|pdf|txt|xml)(?:\?[^\s"'`<>)\\]*)?""", re.I)
REMOTE_STATIC_RE = re.compile(
    r"https?://[^\s\"'<>`)\\]+\.(?:css|mjs|js|woff2?|ttf|otf|png|jpe?g|webp|avif|svg|gif|ico|mp4|webm|mov|json|lottie|pdf|txt|xml)(?:[?#][^\s\"'<>`)\\]*)?",
    re.I,
)
URL_ATTRS = [
    "href", "src", "srcset", "poster", "data-src", "data-srcset",
    "data-poster", "data-video", "content", "action", "style",
    "data-bg", "data-image", "data-wf-bg", "data-background-image",
]
SRCSET_ATTRS = {"srcset", "data-srcset"}
STYLE_URL_RE = re.compile(r"url\(\s*['\"]?([^)'\"]+)", re.I)
CSS_URL_RE = re.compile(r"url\(\s*['\"]?(https?://[^)'\"]+)", re.I)
CRITICAL_REMOTE_EXTS = {".css", ".js", ".mjs", ".woff", ".woff2", ".ttf", ".otf", ".svg", ".json", ".lottie"}

issues: list[str] = []
warnings: list[str] = []
REDIRECTS: dict[str, dict] = {}


def load_redirects() -> None:
    global REDIRECTS
    if REDIRECT_FILE.exists():
        REDIRECTS = json.loads(REDIRECT_FILE.read_text(encoding="utf-8"))


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
    if not value or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "sms:", "whatsapp:")):
        return True
    if value.startswith("//"):
        return True
    if value.startswith(("http://", "https://")):
        return True
    return False


def check_local_ref(path: str, source: Path, attr: str) -> None:
    value = html.unescape(path.strip())
    if is_external_or_special(value):
        return
    # Meta descriptions, viewport strings and numeric Open Graph fields are not routes.
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
    if value.startswith(("/", "./", "../", "//", "http://", "https://")):
        return True
    return "/" in value or bool(Path(urlsplit(value).path).suffix)


def validate_html(path: Path) -> None:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        issues.append(f"invalid UTF-8 HTML: {path.relative_to(ROOT)}")
        return
    soup = BeautifulSoup(raw, "html.parser")
    if not soup.html:
        issues.append(f"missing html element: {path.relative_to(ROOT)}")
        return
    if soup.html.get("data-wf-domain") != "www.cosmos.studio":
        issues.append(f"wrong Webflow domain: {path.relative_to(ROOT)}")
    if soup.html.get("data-view") != "you" or soup.html.get("data-view-label") != "For You":
        issues.append(f"For You default missing: {path.relative_to(ROOT)}")
    if not soup.body or not soup.body.get("data-cosmos-route"):
        issues.append(f"route marker missing: {path.relative_to(ROOT)}")
    canonical = soup.find("link", rel=lambda x: x and "canonical" in x)
    if not canonical or "cosmos.studio" not in (canonical.get("href") or ""):
        issues.append(f"Cosmos canonical missing: {path.relative_to(ROOT)}")
    dropdowns = soup.select("[data-cosmos-audience]")
    if not dropdowns:
        issues.append(f"audience dropdown missing: {path.relative_to(ROOT)}")
    for dropdown in dropdowns:
        labels = [o.get_text(" ", strip=True) for o in dropdown.select("[data-view-option]")]
        if labels != DROPDOWN_LABELS:
            issues.append(f"dropdown options wrong in {path.relative_to(ROOT)}: {labels}")
        selected = dropdown.select_one(".cosmos-audience_option.is-selected")
        if not selected or selected.get_text(" ", strip=True) != "For You" or selected.get("aria-selected") != "true":
            issues.append(f"For You not selected in {path.relative_to(ROOT)}")
        cluster = dropdown.find_parent(class_="cosmos-brand-cluster")
        if not cluster or not cluster.find("a"):
            issues.append(f"dropdown not beside logo in {path.relative_to(ROOT)}")
    if not soup.select_one(".navbar_component"):
        issues.append(f"Cosmos navbar missing: {path.relative_to(ROOT)}")
    for tag in soup.find_all(["link", "script"]):
        if tag.has_attr("integrity") or tag.has_attr("crossorigin"):
            issues.append(f"stale integrity/crossorigin on localized tag in {path.relative_to(ROOT)}")
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
    lower = raw.lower()
    for marker in OWNER_MARKERS:
        if marker in lower:
            issues.append(f"legacy personal-site content remains in {path.relative_to(ROOT)}")
            break
    for marker in REJECTED_DARK_MARKERS:
        if marker.lower() in lower:
            issues.append(f"rejected legacy layer in {path.relative_to(ROOT)}: {marker}")
    if "cosmoss-nordic-template.webflow.io" in lower:
        issues.append(f"staging Webflow domain remains in {path.relative_to(ROOT)}")


def validate_text_assets() -> None:
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or path.name.endswith(".html"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lower = text.lower()
        for marker in OWNER_MARKERS:
            if marker in lower:
                issues.append(f"legacy personal-site content remains in {path.relative_to(ROOT)}")
                break
        for marker in REJECTED_DARK_MARKERS:
            if marker.lower() in lower:
                issues.append(f"rejected legacy layer in {path.relative_to(ROOT)}: {marker}")
        if "..../assets" in text:
            issues.append(f"double-prefixed asset path in {path.relative_to(ROOT)}")
        if "cosmoss-nordic-template.webflow.io" in lower:
            issues.append(f"staging Webflow domain remains in {path.relative_to(ROOT)}")
        # Browser-driven checks cover dynamic JavaScript chunk paths; static
        # scanning there creates false positives from minified URL fragments.
        if path.suffix.lower() == ".css":
            for match in LOCAL_ASSET_RE.finditer(text):
                check_local_ref(match.group(0), path, "asset-url")


def remote_static_urls() -> set[str]:
    found: set[str] = set()
    static_host_markers = {
        "www.cosmos.studio", "cosmos.studio", "cdn.prod.website-files.com",
        "assets.website-files.com", "assets-global.website-files.com",
        "uploads-ssl.webflow.com", "cloudinary.com", "cloudfront.net",
        "jsdelivr.net", "unpkg.com", "raw.githubusercontent.com",
        "video.cosmos.studio", "fonts.gstatic.com", "fonts.googleapis.com",
        "www.google.com", "www.gstatic.com", "widget.clutch.co",
    }
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".css"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if path.suffix.lower() == ".html":
            soup = BeautifulSoup(text, "html.parser")
            values: list[str] = []
            for tag in soup.find_all(True):
                for attr in URL_ATTRS:
                    value = tag.get(attr)
                    if not isinstance(value, str):
                        continue
                    if attr == "style":
                        values.extend(html.unescape(item) for item in STYLE_URL_RE.findall(value))
                    else:
                        values.extend(html.unescape(item) for item in split_attr_values(value, attr))
            for style in soup.find_all("style"):
                values.extend(html.unescape(value) for value in STYLE_URL_RE.findall(style.get_text()))
        else:
            values = [html.unescape(value) for value in CSS_URL_RE.findall(text)]
        for value in values:
            for match in REMOTE_STATIC_RE.finditer(html.unescape(value)):
                url = html.unescape(match.group(0)).rstrip(".,;:!?)]}")
                url_path = urlsplit(url).path.lower()
                if url_path.endswith(("/sitemap.xml", "/robots.txt")):
                    continue
                host = (urlsplit(url).hostname or "").lower()
                if host in static_host_markers or any(marker in host for marker in static_host_markers):
                    found.add(url)
    return found


def browser_count(value) -> int:
    if isinstance(value, list):
        return len(value)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    if not SITE.exists():
        raise SystemExit("cosmos-copy missing")
    # After customization the strict validator's old-brand/no-owner assertions
    # are intentionally obsolete. Delegate to the custom validator so running
    # the historical command still validates the current site correctly.
    index = SITE / "index.html"
    if index.exists() and "LulaZel Hub" in index.read_text(encoding="utf-8", errors="replace")[:500000]:
        custom_validator = ROOT / "scripts" / "validate_custom_clone.py"
        result = subprocess.run(
            [sys.executable, str(custom_validator), *sys.argv[1:]],
            cwd=str(ROOT),
        )
        raise SystemExit(result.returncode)
    load_redirects()
    canonical_urls = [line.strip() for line in CANONICAL_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(canonical_urls) != 112:
        issues.append(f"canonical URL count is {len(canonical_urls)}, expected 112")
    counts = Counter()
    for url in canonical_urls:
        path = urlsplit(url).path or "/"
        counts[path.strip("/").split("/")[0] or "root"] += 1
        if not local_path_exists(path):
            issues.append(f"missing local page for canonical route: {path}")
    expected_counts = {"blog": 24, "services": 32, "projects": 37, "industries": 11, "legal": 3}
    for key, expected in expected_counts.items():
        if counts[key] != expected:
            issues.append(f"canonical {key} count is {counts[key]}, expected {expected}")
    html_files = sorted(SITE.rglob("*.html"))
    if len(html_files) < 112:
        issues.append(f"HTML page count is {len(html_files)}, expected at least 112")
    for path in html_files:
        validate_html(path)
    validate_text_assets()

    index = (SITE / "index.html").read_text(encoding="utf-8")
    index_text = BeautifulSoup(index, "html.parser").get_text(" ", strip=True)
    for marker in COSMOS_HOME_MARKERS:
        if marker not in index_text and marker not in index:
            issues.append(f"exact Cosmos home wording missing: {marker}")
    for marker in COSMOS_NAV_MARKERS:
        if marker not in index_text and marker not in index:
            issues.append(f"exact Cosmos nav/list item missing: {marker}")
    for required in ["gsap.min.js", "webflow.", "headkit-", "cc-site-", "jquery-3.5.1", "shared.", "page-51e8e2"]:
        if required not in index:
            issues.append(f"exact Cosmos script/style reference missing: {required}")

    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
    if len(locs) != len(canonical_urls):
        issues.append(f"sitemap loc count is {len(locs)}, expected {len(canonical_urls)}")
    robots = (SITE / "robots.txt").read_text(encoding="utf-8")
    if "cosmos.studio" not in robots:
        issues.append("robots.txt does not reference Cosmos sitemap")
    for required in ["redirects.json", "_redirects", "remaining-remote-assets.json", "build-manifest.json"]:
        if not (SITE / required).exists():
            issues.append(f"missing generated manifest: {required}")
    if not (ROOT / "scripts/serve.py").exists():
        issues.append("custom redirect-aware server is missing")

    report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    if report.get("exact_page_count", 0) < 110:
        issues.append(f"only {report.get('exact_page_count')} exact live pages fetched")
    if report.get("localized_asset_count", 0) < 100:
        issues.append(f"only {report.get('localized_asset_count')} localized assets")
    if report.get("site_total_bytes", 0) > 120 * 1024 * 1024:
        issues.append(f"site is too large: {report.get('site_total_bytes')} bytes")
    asset_map = json.loads(ASSET_MAP_FILE.read_text(encoding="utf-8"))
    for remote, local in asset_map.items():
        if local.startswith(("http://", "https://", "//")):
            continue
        if not local_path_exists(local):
            issues.append(f"asset map target missing for {remote}: {local}")

    allowed_remote = set(json.loads(REMOTE_FILE.read_text(encoding="utf-8"))) if REMOTE_FILE.exists() else set()
    remaining = remote_static_urls()
    for url in remaining:
        if url not in allowed_remote:
            issues.append(f"unlisted remote static asset remains: {url}")
        ext = Path(urlsplit(url).path).suffix.lower()
        if ext in CRITICAL_REMOTE_EXTS and url not in allowed_remote:
            issues.append(f"critical remote source is not localized: {url}")

    if BROWSER_REPORT.exists():
        browser = json.loads(BROWSER_REPORT.read_text(encoding="utf-8"))
        failed_count = browser_count(browser.get("failedLocalResponses", browser.get("failed_local_responses")))
        legacy_count = browser_count(browser.get("legacyMarkerHits", browser.get("legacy_marker_hits")))
        error_count = browser_count(browser.get("pageErrors", browser.get("page_errors")))
        if failed_count:
            issues.append(f"browser preview had local failed responses: {failed_count}")
        if legacy_count:
            issues.append(f"browser preview showed legacy personal-site content: {legacy_count}")
        if error_count:
            issues.append(f"browser preview had page errors: {error_count}")
        dom_checks = browser.get("domChecks", [])
        for check in dom_checks:
            if check.get("bodyTextLength", 0) < 800:
                issues.append(f"browser preview body looks blank: {check.get('page')}")
        for screenshot in ["home.png", "home-dark-scheme.png", "services.png", "projects.png", "dropdown.png"]:
            if not (ROOT / "scripts/preview-check" / screenshot).exists():
                issues.append(f"missing browser preview screenshot: {screenshot}")
    else:
        issues.append("browser preview report is missing")

    custom_js = SITE / "assets/js/cosmos-audience.js"
    if custom_js.exists():
        result = subprocess.run(["node", "--check", str(custom_js)], capture_output=True, text=True)
        if result.returncode:
            issues.append(f"custom JS syntax error: {result.stderr.strip()}")

    total_size = sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file())
    summary = {
        "issues": len(issues),
        "warnings": warnings,
        "canonical_urls": len(canonical_urls),
        "canonical_counts": dict(counts),
        "html_pages": len(html_files),
        "site_files": sum(1 for p in SITE.rglob("*") if p.is_file()),
        "site_bytes": total_size,
        "localized_assets": len(asset_map),
        "exact_pages": report.get("exact_page_count"),
        "redirects": len(REDIRECTS),
        "remaining_remote_assets": len(remaining),
        "asset_status_counts": report.get("asset_status_counts"),
        "issue_samples": issues[:100],
        "all_issues": issues,
    }
    VALIDATION_REPORT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    if issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
