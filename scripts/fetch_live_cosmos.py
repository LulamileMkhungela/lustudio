#!/usr/bin/env python3
"""Fetch and build a strict static clone of https://www.cosmos.studio/.

The live Cosmos site and its CDN hosts are reachable from GitHub Actions but not
from the coding sandbox, so this script runs in .github/workflows/fetch-cosmos.yml.
It downloads exact HTML for every canonical sitemap route and every internal
route discovered from those pages, records HTTP redirects, recursively localizes
CSS, JavaScript, fonts, images, Lottie files, posters and videos, and preserves
the exact Webflow/GSAP interaction scripts. The only intentional DOM addition is
a Cosmos-styled audience selector beside the logo with For You selected.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
import re
import shutil
import sys
import threading
import time
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "cosmos-copy"
RAW_SITEMAP = ROOT / "scripts/cosmos-sitemap-raw.txt"
CANONICAL_FILE = ROOT / "scripts/cosmos-canonical-urls.txt"
REPORT_FILE = ROOT / "scripts/cosmos-live-build-report.json"
ASSET_MAP_FILE = ROOT / "scripts/cosmos-asset-map.json"
REDIRECT_FILE = ROOT / "scripts/cosmos-redirects.json"
REMOTE_FILE = ROOT / "scripts/cosmos-remaining-remote-assets.json"

LIVE = "https://www.cosmos.studio"
STAGING = "https://cosmoss-nordic-template.webflow.io"
JINA_HTML = "https://r.jina.ai/http://www.cosmos.studio"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
CACHE = "live-cosmos-2"

LIVE_HOSTS = {"www.cosmos.studio", "cosmos.studio"}
STAGING_HOSTS = {"cosmoss-nordic-template.webflow.io"}
INTERNAL_HOSTS = LIVE_HOSTS | STAGING_HOSTS
ASSET_PREFIXES = (
    "/assets/", "/_c/", "/_m/", "/fonts/", "/img/", "/css/", "/js/",
    "/video/", "/videos/", "/_next/",
)
STATIC_EXTS = {
    ".css", ".js", ".mjs", ".woff", ".woff2", ".ttf", ".otf",
    ".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg", ".gif", ".ico",
    ".mp4", ".webm", ".mov", ".json", ".lottie", ".pdf", ".txt", ".xml",
}
TEXT_EXTS = {".css", ".js", ".mjs", ".json", ".lottie", ".svg", ".xml", ".txt", ".html"}
STATIC_HOSTS = {
    "cdn.prod.website-files.com",
    "assets.website-files.com",
    "assets-global.website-files.com",
    "uploads-ssl.webflow.com",
    "d3e54v103j8qbb.cloudfront.net",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "res.cloudinary.com",
    "video.cosmos.studio",
    "fonts.gstatic.com",
    "fonts.googleapis.com",
    "widget.clutch.co",
    "raw.githubusercontent.com",
    "www.google.com",
    "www.gstatic.com",
    "clarity.ms",
    "www.clarity.ms",
}
EXTERNAL_LINK_HOSTS = {
    "calendar.google.com", "www.linkedin.com", "www.behance.net",
    "www.facebook.com", "www.instagram.com", "clutch.co", "www.upwork.com",
    "wa.me", "t.me", "chatgpt.com", "claude.ai", "www.perplexity.ai",
    "wow.cosmos.studio", "www.googletagmanager.com", "r.jina.ai",
    "localhost", "127.0.0.1",
}
MIME_EXT = {
    "text/css": ".css",
    "application/javascript": ".js",
    "text/javascript": ".js",
    "application/json": ".json",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "font/woff2": ".woff2",
    "font/woff": ".woff",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/xml": ".xml",
    "text/xml": ".xml",
}

MAX_PAGE_BYTES = 3 * 1024 * 1024
MAX_ASSET_BYTES = 8 * 1024 * 1024
MAX_TOTAL_ASSET_BYTES = 52 * 1024 * 1024
MAX_EXTRA_PATHS = 500
MAX_DISCOVERY_PASSES = 4
MAX_RECURSION_PASSES = 6
TEXT_SUFFIXES = {".html", ".css", ".js", ".mjs", ".json", ".lottie", ".svg", ".xml", ".txt", ".map"}
SPECIAL_ROOT_FILES = {"rss.xml", "robots.txt", "sitemap.xml"}

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
ASSET_HEADERS = {
    "User-Agent": UA,
    "Accept": "*/*",
    "Referer": "https://www.cosmos.studio/",
}

TOKEN_RE = re.compile(
    r"""(?:(?:https?:)?//[^\s"'`<>\\]+|/(?:assets|_c|_m|fonts|img|css|js|video|videos|_next)/[^\s"'`<>\\]+|(?:\.{1,2}/)?[A-Za-z0-9_~%+\-./]+\.(?:css|mjs|js|woff2?|ttf|otf|png|jpe?g|webp|avif|svg|gif|ico|mp4|webm|mov|json|lottie|pdf|txt|xml)(?:[?#][^\s"'`<>\\]*)?)""",
    re.I | re.X,
)
REMOTE_STATIC_RE = re.compile(
    r"https?://[^\s\"'<>`)\\]+\.(?:css|mjs|js|woff2?|ttf|otf|png|jpe?g|webp|avif|svg|gif|ico|mp4|webm|mov|json|lottie|pdf|txt|xml)(?:[?#][^\s\"'<>`)\\]*)?",
    re.I,
)
HTML_URL_ATTRS = [
    "href", "src", "srcset", "poster", "data-src", "data-srcset",
    "data-poster", "data-video", "content", "action", "style",
    "data-bg", "data-image", "data-wf-bg", "data-background-image",
]
CSS_URL_RE = re.compile(r"url\(\s*['\"]?(https?://[^)'\"]+)", re.I)
HREF_RE = re.compile(r"(<a\b[^>]*\bhref\s*=\s*)([\"'])(.*?)\2", re.I | re.S)
TAG_RE = re.compile(r"<(?:link|script|img|source|video|audio)\b[^>]*>", re.I)
CANONICAL_LINK_RE = re.compile(
    r"<link\b[^>]*\brel\s*=\s*[\"']?canonical[\"']?[^>]*>", re.I
)
NAV_RE = re.compile(r"<nav\b[^>]*>.*?</nav>", re.I | re.S)
NAVBAR_START_RE = re.compile(r"<nav\b[^>]*\bclass\s*=\s*[\"'][^\"']*\bnavbar\b[^\"']*[\"'][^>]*>", re.I)
NAV_TAG_RE = re.compile(r"<(/?)nav\b[^>]*>", re.I)
MOBILE_MENU_START_RE = re.compile(r"<div\b[^>]*\bid\s*=\s*[\"']mobile-menu[\"'][^>]*>", re.I)
DIV_TAG_RE = re.compile(r"<(/?)div\b[^>]*>", re.I)
HTML_TAG_RE = re.compile(r"<html\b[^>]*>", re.I)
BODY_TAG_RE = re.compile(r"<body\b[^>]*>", re.I)

DROPDOWN_HTML = """
<div class="cosmos-audience" data-cosmos-audience>
  <button aria-expanded="false" aria-haspopup="listbox" class="cosmos-audience_trigger" type="button">
    <span class="cosmos-audience_label" data-cosmos-audience-current>For You</span>
    <svg aria-hidden="true" class="cosmos-audience_arrow" viewBox="0 0 12 8"><path d="M1 1.5 6 6.5 11 1.5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
  </button>
  <div class="cosmos-audience_menu" role="listbox">
    <button aria-selected="false" class="cosmos-audience_option" data-view-option="marketing" role="option" type="button">For Marketing Teams</button>
    <button aria-selected="true" class="cosmos-audience_option is-selected" data-view-option="you" role="option" type="button">For You</button>
    <button aria-selected="false" class="cosmos-audience_option" data-view-option="tech" role="option" type="button">For Tech</button>
    <button aria-selected="false" class="cosmos-audience_option" data-view-option="else" role="option" type="button">Something Else</button>
  </div>
</div>
""".strip()

AUDIENCE_CSS = """
/* Intentional Cosmos UI addition: audience selector beside the logo. */
.cosmos-brand-cluster{display:flex;align-items:center;gap:.6rem;justify-self:start;min-width:max-content}
.cosmos-brand-cluster>.navbar-logo_wr,.cosmos-brand-cluster>.menu_logo-wrap{display:inline-flex;align-items:center;width:auto}
.cosmos-audience{position:relative;display:inline-flex;align-items:center;flex:0 0 auto;z-index:40;font-family:Switzer,Inter,Arial,sans-serif}
.cosmos-audience_trigger{appearance:none;display:inline-flex;align-items:center;gap:.45rem;min-height:2.25rem;padding:.45rem .72rem;border:1px solid rgba(15,16,17,.14);border-radius:999px;background:#fff;color:#0f1011;font:500 .8rem/1 Switzer,Inter,Arial,sans-serif;cursor:pointer;white-space:nowrap;box-shadow:0 2px 12px rgba(15,16,17,.04)}
.cosmos-audience_arrow{width:.62rem;height:.44rem;transition:transform .2s ease}
.cosmos-audience.is-open .cosmos-audience_arrow{transform:rotate(180deg)}
.cosmos-audience_menu{display:none;position:absolute;top:calc(100% + .5rem);left:0;min-width:14rem;padding:.35rem;border:1px solid rgba(15,16,17,.12);border-radius:.8rem;background:#fff;box-shadow:0 18px 48px rgba(15,16,17,.13);z-index:60}
.cosmos-audience.is-open .cosmos-audience_menu{display:grid}
.cosmos-audience_option{appearance:none;width:100%;padding:.68rem .72rem;border:0;border-radius:.55rem;background:transparent;color:#0f1011;text-align:left;font:500 .85rem/1.2 Switzer,Inter,Arial,sans-serif;cursor:pointer;white-space:nowrap}
.cosmos-audience_option:hover,.cosmos-audience_option.is-selected{background:whitesmoke}
@media(max-width:991px){.navbar_component>.cosmos-brand-cluster>.cosmos-audience{display:none}#mobile-menu>.cosmos-brand-cluster>.cosmos-audience,.menu_content>.cosmos-brand-cluster>.cosmos-audience{display:inline-flex}}
/* Preserve the light Cosmos presentation even when the visitor prefers dark mode. */
@media(prefers-color-scheme:dark){
  :root,.process-section{color-scheme:light!important;--_colors---primary--paper:whitesmoke!important;--_colors---grey--50:whitesmoke!important;--_colors---primary--white:#fff!important;--_colors---grey--75:#e8e8e8!important;--_colors---grey--100:#ddd!important;--_colors---primary--black:#0f1011!important;--_colors---grey--250:grey!important;--_colors---grey--300:#707070!important;--_colors---grey--400:#666!important;--_colors---bg:whitesmoke!important;--_colors---txt:#0f1011!important;--_colors---tag:#fff!important;--_colors---btn-inactive-bg:#fff!important;--_colors---btn-active-bg:#1c1d1f!important;--_colors---brn-active-text:#fff!important;--_colors---btn-inactive-text:#666!important;--ink:#0f1011!important;--bg:whitesmoke!important;--grey:#707070!important}
  html,body{background-color:whitesmoke!important;color:#0f1011!important}
  html .section_home-header,html .ct-sec,html .dx-fitstill{background-color:whitesmoke!important}
  html .navbar_component{background-color:#fff!important}
  html .skip-link,html a.blog_block,html .dx-p a,html .work-other_brand-name,html .link-w-icon,html .works_name-v2,html .navbar_logo-anim,html .navbar_logo-anim_text,html .navbar-logo_wr,html .dropdown-link,html .faq_accordion a,html .contact-form_success-wrap .heading-style-h5,html .menu_link,html .menu_link .menu_link-text,html .menu_legal-link{color:#0f1011!important}
  html .dx{--ink:#0f1011!important;--bg:whitesmoke!important;--grey:#707070!important}
  html .dx-card,html .dx-btn,html .dx-btn-in,html .dx-cta2,html .dx-fitcard.is-no,html .dx-rv-badge,html .dx-rv-card,html .ct-card:not(.is-dark),html .ct-info,html .calc_steps,html .calc_card,html .contact-form_form-block,html .contact-form_success-wrap,html .about_content,html .faq_accordion,html .page-button-2,html .resources_item-label,html .takeaways{background-color:#fff!important;color:#0f1011!important}
  html .dx-cta2-photo,html .is-no .dx-fitpill,html .calc_help,html .cc-opt,html .cc-ico,html .cc-dot{background-color:#e8e8e8!important}
  html .dx-rv-badge,html .dx-rv-q,html .dx-rv-who b,html .dx-rv-link,html .contact-form_field,html .ct-card:not(.is-dark),html .ct-info{color:#0f1011!important}
}
""".strip() + "\n"

FALLBACK_CSS = """
/* Exact Cosmos shell fallback content for routes without a downloaded body. */
.cosmos-fallback{padding-top:10rem;padding-bottom:6rem;background:var(--_colors---primary--paper,whitesmoke);color:var(--_colors---primary--black,#0f1011)}
.cosmos-fallback_inner{max-width:62rem;margin:0 auto;font-family:Switzer,Inter,Arial,sans-serif}
.cosmos-fallback_label{font-family:Inter,Switzer,Arial,sans-serif;font-size:.72rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#707070}
.cosmos-fallback h1{margin:1rem 0 1.25rem;font:600 clamp(3rem,7vw,7rem)/.98 Switzer,Inter,Arial,sans-serif;letter-spacing:-.055em;color:#0f1011}
.cosmos-fallback p{margin:0 0 1.1rem;font:400 clamp(1rem,1.5vw,1.25rem)/1.6 Inter,Switzer,Arial,sans-serif;color:#666}
.cosmos-fallback_actions{display:flex;flex-wrap:wrap;gap:.7rem;margin-top:2rem}
.cosmos-fallback_actions a{display:inline-flex;align-items:center;min-height:2.9rem;padding:0 1.1rem;border:1px solid rgba(15,16,17,.16);border-radius:999px;background:#fff;color:#0f1011;font:500 .88rem Inter,Switzer,Arial,sans-serif;text-decoration:none}
.cosmos-fallback_actions a.is-solid{background:#0f1011;color:#fff;border-color:#0f1011}
.cosmos-fallback_canonical{margin-top:2.5rem;font-size:.8rem!important;word-break:break-word}
""".strip() + "\n"

AUDIENCE_JS = """
(function(){
  function init(){
    document.querySelectorAll('[data-cosmos-audience]').forEach(function(root){
      var trigger=root.querySelector('.cosmos-audience_trigger');
      var current=root.querySelector('[data-cosmos-audience-current]');
      var options=Array.prototype.slice.call(root.querySelectorAll('[data-view-option]'));
      var selected=root.querySelector('.is-selected')||options.filter(function(o){return o.getAttribute('data-view-option')==='you';})[0]||options[0];
      function apply(option){
        options.forEach(function(o){o.classList.toggle('is-selected',o===option);o.setAttribute('aria-selected',o===option?'true':'false');});
        if(current)current.textContent=option.textContent.trim();
        document.documentElement.setAttribute('data-view',option.getAttribute('data-view-option')||'you');
        document.documentElement.setAttribute('data-view-label',option.textContent.trim());
      }
      if(selected)apply(selected);
      if(trigger)trigger.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();var open=root.classList.toggle('is-open');trigger.setAttribute('aria-expanded',open?'true':'false');});
      options.forEach(function(option){option.addEventListener('click',function(){apply(option);root.classList.remove('is-open');if(trigger)trigger.setAttribute('aria-expanded','false');});});
    });
    document.addEventListener('click',function(e){document.querySelectorAll('[data-cosmos-audience].is-open').forEach(function(root){if(!root.contains(e.target)){root.classList.remove('is-open');var t=root.querySelector('.cosmos-audience_trigger');if(t)t.setAttribute('aria-expanded','false');}});});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
""".strip() + "\n"

ASSET_MAP: dict[str, str] = {}
ASSET_RECORDS: list[dict] = []
CONTENT_TO_PATH: dict[str, str] = {}
STAGING_EQUIVALENTS: dict[str, list[str]] = {}
REDIRECTS: dict[str, dict] = {}
TOTAL_ASSET_BYTES = 0
ACTIVE_ASSET_BYTES = 0
BUDGET_LOCK = threading.Lock()


def http_get(url: str, *, headers: dict | None = None, stream: bool = False,
             timeout: int = 45, allow_redirects: bool = True):
    last = None
    for attempt in range(3):
        try:
            return requests.get(
                url,
                headers=headers or HEADERS,
                timeout=timeout,
                allow_redirects=allow_redirects,
                stream=stream,
            )
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))
    raise last


def encode_existing_path(path: str) -> str:
    return quote(path, safe="/~()*!.'_%-@+,")


def canonical_live_url(url_or_path: str) -> str:
    value = html.unescape(url_or_path.strip())
    if value.startswith("//"):
        value = "https:" + value
    if value.startswith("http://"):
        value = "https://" + value[7:]
    if not value.startswith("http"):
        value = LIVE + (value if value.startswith("/") else "/" + value)
    p = urlsplit(value)
    host = (p.hostname or "").lower()
    if host in LIVE_HOSTS:
        host = "www.cosmos.studio"
    if host in STAGING_HOSTS:
        host = "cosmoss-nordic-template.webflow.io"
    path = unquote(p.path) or "/"
    if len(path) > 1:
        path = path.rstrip("/") or "/"
    return urlunsplit(("https", host, quote(path, safe="/~()*!.'_-"), p.query, ""))


def canonical_path(url_or_path: str) -> str:
    p = urlsplit(canonical_live_url(url_or_path)).path
    p = unquote(p) or "/"
    if len(p) > 1:
        p = p.rstrip("/") or "/"
    return p


def parse_sitemap_urls() -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    def add(url: str):
        clean = canonical_live_url(url)
        if clean not in seen:
            seen.add(clean)
            urls.append(clean)

    try:
        response = http_get(LIVE + "/sitemap.xml", headers={**HEADERS, "Accept": "application/xml"})
        if response.ok:
            for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", response.text, re.I | re.S):
                add(html.unescape(loc))
    except Exception as exc:  # noqa: BLE001
        print(f"sitemap fetch warning: {exc}", file=sys.stderr)

    raw = RAW_SITEMAP.read_text(encoding="utf-8")
    for part in re.split(r"(?=https://www\.cosmos\.studio)", raw):
        part = part.strip()
        if not part.startswith("https://www.cosmos.studio"):
            continue
        part = re.sub(r"\d{4}-\d{2}-\d{2}T.*$", "", part).strip()
        add(part)

    def sort_key(url: str):
        path = canonical_path(url)
        if path == "/":
            return (0, "")
        top = path.strip("/").split("/")[0]
        order = {
            "about": 1, "projects": 2, "blog": 3, "pricing": 4,
            "contacts": 5, "reviews": 6, "services": 7,
            "industries": 8, "legal": 9,
        }
        return (order.get(top, 20), path)

    urls.sort(key=sort_key)
    return urls


def page_file(path: str) -> Path:
    if path == "/":
        return SITE / "index.html"
    rel = unquote(path).lstrip("/")
    if rel.endswith(".html"):
        return SITE / safe_rel_path(rel)
    return SITE / safe_rel_path(rel) / "index.html"


def safe_rel_path(path: str) -> str:
    path = unquote(path).replace("\\", "/")
    parts = []
    for part in path.split("/"):
        if part in {"", ".", ".."}:
            continue
        part = re.sub(r'[<>:"|?*]', "_", part)
        parts.append(part)
    return "/".join(parts)


def quote_path(path: str) -> str:
    return quote(unquote(path), safe="/~()*!.'_-")


def is_asset_url(url: str) -> bool:
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    path = unquote(p.path)
    ext = Path(path).suffix.lower()
    if host in INTERNAL_HOSTS:
        return path.startswith(ASSET_PREFIXES) or Path(path).name in SPECIAL_ROOT_FILES
    if host in EXTERNAL_LINK_HOSTS and host not in STATIC_HOSTS:
        return False
    if host in STATIC_HOSTS:
        return True
    return False


def strip_token(token: str) -> tuple[str, str]:
    suffix_chars = ".,;:!?)]}"
    index = len(token)
    while index and token[index - 1] in suffix_chars:
        index -= 1
    return token[:index], token[index:]


def normalize_asset_url(token: str, base_url: str | None) -> tuple[str, str] | None:
    raw = html.unescape(token).strip()
    if not raw or raw.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
        return None
    if raw.startswith("//"):
        raw = "https:" + raw
    if raw.startswith("http://"):
        raw = "https://" + raw[7:]
    base = base_url or LIVE + "/"
    bp = urlsplit(base)
    if raw.startswith("https://"):
        absolute = raw
    elif raw.startswith("/"):
        host = (bp.hostname or "").lower()
        if host in INTERNAL_HOSTS:
            root = LIVE
        else:
            root = f"{bp.scheme or 'https'}://{bp.netloc}"
        absolute = root + raw
    elif Path(unquote(urlsplit(raw).path)).name in SPECIAL_ROOT_FILES:
        absolute = LIVE + "/" + raw
    else:
        absolute = urljoin(base, raw)
    p = urlsplit(absolute)
    host = (p.hostname or "").lower()
    if host in EXTERNAL_LINK_HOSTS and host not in STATIC_HOSTS:
        return None
    if host in LIVE_HOSTS:
        host = "www.cosmos.studio"
    elif host in STAGING_HOSTS:
        host = "cosmoss-nordic-template.webflow.io"
    clean = urlunsplit(("https", host, encode_existing_path(p.path), p.query, ""))
    if not is_asset_url(clean):
        return None
    return clean, p.fragment


def discover_asset_urls(text: str, base_url: str | None = None) -> set[str]:
    found: set[str] = set()
    for match in TOKEN_RE.finditer(text):
        core, _ = strip_token(match.group(0))
        resolved = normalize_asset_url(core, base_url)
        if resolved:
            found.add(resolved[0])
    return found


def guess_ext(url: str, content_type: str = "") -> str:
    path = unquote(urlsplit(url).path)
    ext = Path(path).suffix.lower()
    if ext in STATIC_EXTS and len(ext) <= 8:
        return ext
    ctype = content_type.split(";", 1)[0].strip().lower()
    return MIME_EXT.get(ctype, ".bin")


def public_path_for_asset(url: str, content_type: str = "") -> str:
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    path = unquote(p.path)
    if host in INTERNAL_HOSTS and (
        path.startswith(ASSET_PREFIXES) or Path(path).name in SPECIAL_ROOT_FILES
    ):
        local = quote_path(path)
        if p.query:
            local += "?" + p.query
        return local
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:20]
    return f"/assets/external/{digest}{guess_ext(url, content_type)}"


def file_for_public_path(public: str) -> Path:
    path = urlsplit(public).path
    rel = safe_rel_path(path.lstrip("/"))
    return SITE / rel


def is_text_asset(url: str, content_type: str, data: bytes) -> str | None:
    ext = Path(unquote(urlsplit(url).path)).suffix.lower()
    ctype = content_type.split(";", 1)[0].strip().lower()
    if ext not in TEXT_EXTS and not (
        ctype.startswith("text/") or ctype in {"application/javascript", "application/json", "image/svg+xml"}
    ):
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def asset_keys(url: str) -> set[str]:
    basename = unquote(urlsplit(url).path).split("/")[-1].lower()
    cleaned = re.sub(r"^[0-9a-f]{24}_", "", basename)
    cleaned = cleaned.replace("cosmoss-nordic-template.webflow.", "")
    canonical = re.sub(r"[^a-z0-9.]+", "", cleaned)
    keys = {canonical} if canonical else set()
    keys.update(token for token in re.findall(r"[0-9a-f]{8,}", basename) if token)
    if "cosmos-logo" in basename:
        keys.add("logosvg")
    return keys


def build_staging_equivalents(texts: list[str]) -> None:
    urls: set[str] = set()
    for text in texts:
        urls.update(discover_asset_urls(text, STAGING + "/"))
    for url in urls:
        host = (urlsplit(url).hostname or "").lower()
        if host not in STATIC_HOSTS and host not in STAGING_HOSTS:
            continue
        for key in asset_keys(url):
            STAGING_EQUIVALENTS.setdefault(key, [])
            if url not in STAGING_EQUIVALENTS[key]:
                STAGING_EQUIVALENTS[key].append(url)
    print(f"staging equivalent keys: {len(STAGING_EQUIVALENTS)}")


def asset_candidates(url: str) -> list[str]:
    candidates = [url]
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    path = unquote(p.path)
    ext = Path(path).suffix.lower()
    if host in LIVE_HOSTS and p.path.startswith(ASSET_PREFIXES):
        candidates.append(STAGING + p.path)
    if host in LIVE_HOSTS and p.path.startswith("/_m/"):
        mirrored = p.path[4:].split("/", 1)
        if len(mirrored) == 2 and "." in mirrored[0]:
            mirror_host, mirror_path = mirrored[0], mirrored[1].lstrip("/")
            for decoded in (mirror_path, unquote(mirror_path)):
                candidate = f"https://{mirror_host}/{decoded}"
                if p.query:
                    candidate += "?" + p.query
                if candidate not in candidates:
                    candidates.append(candidate)
    if host == "cdn.jsdelivr.net":
        decoded_path = unquote(path)
        if decoded_path != path:
            decoded = urlunsplit((p.scheme or "https", p.netloc, quote(decoded_path, safe="/~()*!.'_%-@+,"), p.query, ""))
            if decoded not in candidates:
                candidates.append(decoded)
        parts = path.strip("/").split("/")
        if len(parts) >= 5 and parts[0] == "gh":
            user, repo_ref = parts[1], parts[2]
            repo, _, ref = repo_ref.partition("@")
            ref = ref or "main"
            raw = f"https://raw.githubusercontent.com/{user}/{repo}/{ref}/" + "/".join(parts[3:])
            if p.query:
                raw += "?" + p.query
            candidates.append(raw)
        elif len(parts) >= 2 and parts[0] == "npm":
            unpkg = "https://unpkg.com/" + "/".join(parts[1:])
            if p.query:
                unpkg += "?" + p.query
            candidates.append(unpkg)
    basename = path.split("/")[-1].lower()
    canonical = re.sub(r"[^a-z0-9.]+", "", re.sub(r"^[0-9a-f]{24}_", "", basename))
    ordered_keys = [canonical] + sorted(t for t in re.findall(r"[0-9a-f]{8,}", basename) if t)
    seen_keys: set[str] = set()
    for key in ordered_keys:
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        for candidate in STAGING_EQUIVALENTS.get(key, []):
            if candidate in candidates:
                continue
            if Path(unquote(urlsplit(candidate).path)).suffix.lower() != ext:
                continue
            candidates.append(candidate)
            if len(candidates) >= 8:
                return candidates
    return candidates


def download_asset(url: str) -> dict:
    global TOTAL_ASSET_BYTES, ACTIVE_ASSET_BYTES
    reserved = 0
    last_status = "no-candidate"
    for candidate in asset_candidates(url):
        try:
            headers = ASSET_HEADERS.copy()
            if "jsdelivr.net" in (urlsplit(candidate).hostname or ""):
                headers.pop("Referer", None)
            response = http_get(candidate, headers=headers, stream=True, timeout=45)
            ctype = response.headers.get("content-type", "")
            try:
                declared = int(response.headers.get("content-length") or "0")
            except ValueError:
                declared = 0
            if not response.ok:
                last_status = f"http-{response.status_code}"
                continue
            if declared > MAX_ASSET_BYTES:
                last_status = "too-large"
                continue
            reserve = declared or 1024 * 1024
            with BUDGET_LOCK:
                if TOTAL_ASSET_BYTES + ACTIVE_ASSET_BYTES + reserve > MAX_TOTAL_ASSET_BYTES:
                    return {"url": url, "status": "budget", "declared": declared}
                ACTIVE_ASSET_BYTES += reserve
                reserved = reserve
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_content(64 * 1024):
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_ASSET_BYTES:
                    last_status = "too-large-stream"
                    break
                chunks.append(chunk)
            if size > MAX_ASSET_BYTES:
                continue
            data = b"".join(chunks)
            if not data:
                last_status = "empty"
                continue
            if ctype.startswith("text/html") and not data.lstrip().lower().startswith(b"<svg"):
                last_status = "html-response"
                continue
            local = public_path_for_asset(url, ctype)
            text = is_text_asset(url, ctype, data)
            digest = hashlib.sha1(data).hexdigest()
            write = True
            duplicate = False
            if text is None:
                with BUDGET_LOCK:
                    if digest in CONTENT_TO_PATH:
                        local = CONTENT_TO_PATH[digest]
                        write = False
                        duplicate = True
                    else:
                        CONTENT_TO_PATH[digest] = local
            # Account for the downloaded bytes immediately. Otherwise a whole
            # pass of parallel workers is budgeted against the previous pass's
            # total and the generated clone can grow far past the repository cap.
            with BUDGET_LOCK:
                TOTAL_ASSET_BYTES += size
                ACTIVE_ASSET_BYTES -= reserved
                reserved = 0
            return {
                "url": url,
                "status": "ok",
                "local": local,
                "data": data,
                "text": text,
                "write": write,
                "duplicate": duplicate,
                "size": size,
                "declared": declared,
                "content_type": ctype,
                "fetched_from": response.url,
            }
        except Exception as exc:  # noqa: BLE001
            last_status = f"error:{type(exc).__name__}"
            continue
        finally:
            if reserved:
                with BUDGET_LOCK:
                    ACTIVE_ASSET_BYTES -= reserved
                reserved = 0
    return {"url": url, "status": last_status, "declared": 0}


def rewrite_text(text: str, base_url: str | None = None) -> str:
    def replace(match: re.Match) -> str:
        token = match.group(0)
        core, suffix = strip_token(token)
        resolved = normalize_asset_url(core, base_url)
        if not resolved:
            return token
        url, _fragment = resolved
        local = ASSET_MAP.get(url)
        if not local:
            return token
        raw = html.unescape(core)
        fragment = urlsplit(raw).fragment
        output = local + (("#" + fragment) if fragment else "")
        if "&amp;" in core:
            output = html.escape(output, quote=False)
        return output + suffix

    return TOKEN_RE.sub(replace, text)


def internal_page_path(href: str) -> str | None:
    raw = html.unescape(href.strip())
    if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "sms:", "whatsapp:")):
        return None
    if raw.startswith("//"):
        raw = "https:" + raw
    if raw.startswith("http://"):
        raw = "https://" + raw[7:]
    if raw.startswith("https://"):
        p = urlsplit(raw)
        host = (p.hostname or "").lower()
        if host not in INTERNAL_HOSTS:
            return None
        path = unquote(p.path) or "/"
    elif raw.startswith("/"):
        path = unquote(urlsplit(raw).path) or "/"
    else:
        path = unquote(urlsplit(urljoin(LIVE + "/", raw)).path) or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    if path.startswith(ASSET_PREFIXES) or path in {"/robots.txt", "/sitemap.xml"}:
        return None
    ext = Path(path).suffix.lower()
    if ext and ext != ".html":
        return None
    return path


def rewrite_internal_hrefs(text: str) -> str:
    def replace(match: re.Match) -> str:
        prefix, quote_char, href = match.group(1), match.group(2), match.group(3)
        path = internal_page_path(href)
        if path is None:
            return match.group(0)
        raw = html.unescape(href)
        if raw.startswith(("http://", "https://")):
            p = urlsplit(raw)
        else:
            p = urlsplit(urljoin(LIVE + "/", raw))
        out = path
        if p.query:
            out += "?" + p.query
        if p.fragment:
            out += "#" + p.fragment
        if "&amp;" in href:
            out = html.escape(out, quote=False)
        return f"{prefix}{quote_char}{out}{quote_char}"

    return HREF_RE.sub(replace, text)


def set_attribute(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(r"\s" + re.escape(name) + r"\s*=\s*[\"'][^\"']*[\"']", re.I)
    replacement = f' {name}="{escaped}"'
    if pattern.search(tag):
        return pattern.sub(replacement, tag, count=1)
    if tag.endswith(">"):
        return tag[:-1] + replacement + ">"
    return tag


def clean_sri_tags(text: str) -> str:
    attr_re = re.compile(
        r"\s+(?:integrity|crossorigin)(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+))?",
        re.I,
    )

    def clean(match: re.Match) -> str:
        return attr_re.sub("", match.group(0))

    return TAG_RE.sub(clean, text)


def normalize_source_domain(text: str) -> str:
    return (
        text.replace("https://cosmoss-nordic-template.webflow.io", LIVE)
        .replace("http://cosmoss-nordic-template.webflow.io", LIVE)
        .replace("cosmoss-nordic-template.webflow.io", "www.cosmos.studio")
    )


def set_page_attributes(text: str, path: str, canonical: str) -> str:
    match = HTML_TAG_RE.search(text)
    if match:
        tag = match.group(0)
        tag = set_attribute(tag, "lang", "en")
        tag = set_attribute(tag, "data-wf-domain", "www.cosmos.studio")
        tag = set_attribute(tag, "data-view", "you")
        tag = set_attribute(tag, "data-view-label", "For You")
        text = text[: match.start()] + tag + text[match.end() :]
    match = BODY_TAG_RE.search(text)
    if match:
        tag = set_attribute(match.group(0), "data-cosmos-route", path)
        text = text[: match.start()] + tag + text[match.end() :]
    canonical_tag = f'<link rel="canonical" href="{html.escape(canonical, quote=True)}"/>'
    count = [0]

    def canonical_replace(m: re.Match) -> str:
        count[0] += 1
        return canonical_tag if count[0] == 1 else ""

    text, replacements = CANONICAL_LINK_RE.subn(canonical_replace, text)
    if replacements == 0:
        text = re.sub(r"</head>", canonical_tag + "</head>", text, count=1, flags=re.I)
    return text


def inject_custom_assets(text: str) -> str:
    css = (
        f'<link rel="stylesheet" href="/assets/css/cosmos-audience.css?v={CACHE}"/>'
        f'<link rel="stylesheet" href="/assets/css/cosmos-fallback.css?v={CACHE}"/>'
    )
    script = f'<script src="/assets/js/cosmos-audience.js?v={CACHE}" defer=""></script>'
    if re.search(r"</head>", text, re.I):
        text = re.sub(r"</head>", css + "</head>", text, count=1, flags=re.I)
    else:
        text = css + text
    if re.search(r"</body>", text, re.I):
        text = re.sub(r"</body>", script + "</body>", text, count=1, flags=re.I)
    else:
        text += script
    return text


def dropdown_fragment(soup: BeautifulSoup):
    return BeautifulSoup(DROPDOWN_HTML, "html.parser").contents[0]


def wrap_logo_with_dropdown(nav_soup: BeautifulSoup, selector: str, cluster_class: str) -> bool:
    anchor = nav_soup.select_one(selector)
    if not anchor:
        return False
    cluster = nav_soup.new_tag("div")
    cluster["class"] = f"cosmos-brand-cluster {cluster_class}"
    anchor.wrap(cluster)
    cluster.append(deepcopy(dropdown_fragment(nav_soup)))
    return True


def balanced_tag_span(text: str, start: int, tag_re) -> tuple[int, int] | None:
    depth = 0
    for match in tag_re.finditer(text, start):
        if match.group(1):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            return start, match.end()
    return None


def inject_mobile_dropdown_outside_nav(text: str) -> str:
    start_match = MOBILE_MENU_START_RE.search(text)
    if not start_match:
        return text
    span = balanced_tag_span(text, start_match.start(), DIV_TAG_RE)
    if not span:
        return text
    start, end = span
    fragment_soup = BeautifulSoup(text[start:end], "html.parser")
    menu = fragment_soup.find("div", id="mobile-menu") or fragment_soup.find("div")
    if not menu:
        return text
    anchor = menu.select_one("a.menu_logo-wrap") or menu.find("a", recursive=False)
    if anchor:
        cluster = fragment_soup.new_tag("div")
        cluster["class"] = "cosmos-brand-cluster is-mobile"
        anchor.wrap(cluster)
        cluster.append(deepcopy(dropdown_fragment(fragment_soup)))
    else:
        menu.insert(0, deepcopy(dropdown_fragment(fragment_soup)))
    return text[:start] + str(menu) + text[end:]


def inject_dropdown(text: str) -> str:
    start_match = NAVBAR_START_RE.search(text)
    if not start_match:
        return inject_mobile_dropdown_outside_nav(text)
    span = balanced_tag_span(text, start_match.start(), NAV_TAG_RE)
    if not span:
        return inject_mobile_dropdown_outside_nav(text)
    start, end = span
    nav_soup = BeautifulSoup(text[start:end], "html.parser")
    nav = nav_soup.find("nav")
    if not nav:
        return inject_mobile_dropdown_outside_nav(text)
    desktop = wrap_logo_with_dropdown(
        nav_soup, ".navbar_component a.navbar-logo_wr, .navbar_component > a", "is-desktop"
    )
    if not desktop:
        component = nav_soup.select_one(".navbar_component")
        anchor = component.find("a", recursive=False) if component else None
        if anchor:
            cluster = nav_soup.new_tag("div")
            cluster["class"] = "cosmos-brand-cluster is-desktop"
            anchor.wrap(cluster)
            cluster.append(deepcopy(dropdown_fragment(nav_soup)))
        elif component:
            component.insert(0, deepcopy(dropdown_fragment(nav_soup)))
    mobile = wrap_logo_with_dropdown(
        nav_soup, "#mobile-menu a.menu_logo-wrap, .menu > a.menu_logo-wrap", "is-mobile"
    )
    if not mobile:
        menu = nav_soup.select_one("#mobile-menu, .menu")
        anchor = menu.find("a", recursive=False) if menu else None
        if anchor:
            cluster = nav_soup.new_tag("div")
            cluster["class"] = "cosmos-brand-cluster is-mobile"
            anchor.wrap(cluster)
            cluster.append(deepcopy(dropdown_fragment(nav_soup)))
        elif menu:
            menu.insert(0, deepcopy(dropdown_fragment(nav_soup)))
    result = text[:start] + str(nav) + text[end:]
    if not mobile:
        result = inject_mobile_dropdown_outside_nav(result)
    return result


def make_fallback_template(root_html: str) -> str:
    soup = BeautifulSoup(root_html, "html.parser")
    for selector in ["header.section_home-header", "main.main-wrapper", "main"]:
        node = soup.select_one(selector)
        if node:
            node.decompose()
    main = soup.new_tag("main")
    main["id"] = "main"
    main["class"] = "main-wrapper cosmos-fallback-main"
    main.append(
        BeautifulSoup(
            """
<section class="section cosmos-fallback"><div class="padding-global"><div class="container-large"><div class="cosmos-fallback_inner">
  <div class="cosmos-fallback_label">Cosmos Studio</div>
  <h1>__COSMOS_HEADING__</h1>
  <p>Cosmos Studio is a UI/UX design and development studio for SaaS, AI, defense, and military tech. One senior team handles research, UX, UI, design systems, and front-end development in React and Next.js.</p>
  <p>Since 2018, our designers and engineers have contributed to 500+ digital product launches. A typical project takes 2–6 weeks.</p>
  <div class="cosmos-fallback_actions"><a class="is-solid" href="/projects">See selected works</a><a href="/contacts">Contact Anna</a><a href="/pricing">Get an estimate</a><a href="__COSMOS_CANONICAL__">View the original Cosmos Studio page</a></div>
  <p class="cosmos-fallback_canonical">Canonical Cosmos route: <a href="__COSMOS_CANONICAL__">__COSMOS_CANONICAL__</a></p>
</div></div></div></section>
""".strip(),
            "html.parser",
        )
    )
    nav = soup.find("nav")
    if nav:
        nav.insert_after(main)
    else:
        soup.body.insert(0, main)
    if soup.title:
        soup.title.string = "__COSMOS_TITLE__"
    description = soup.find("meta", attrs={"name": "description"})
    if description:
        description["content"] = "__COSMOS_DESCRIPTION__"
    return "<!DOCTYPE html>\n" + str(soup)


def human_title(path: str) -> str:
    if path == "/":
        return "Cosmos Studio"
    slug = path.strip("/").split("/")[-1]
    words = re.sub(r"[-_]+", " ", slug).strip()
    if not words:
        return "Cosmos Studio"
    small = {"ux", "ui", "saas", "ai", "b2b", "web3", "geo", "seo", "c2", "uas", "wcag", "mvp"}
    pieces = []
    for word in words.split():
        pieces.append(word.upper() if word.lower() in small else word.capitalize())
    return " ".join(pieces)


def collect_internal_paths_and_labels(pages: dict[str, str]) -> tuple[set[str], dict[str, str]]:
    paths: set[str] = {"/"}
    labels: dict[str, str] = {}
    for page_html in pages.values():
        soup = BeautifulSoup(page_html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            path = internal_page_path(anchor.get("href", ""))
            if not path:
                continue
            paths.add(path)
            label = anchor.get_text(" ", strip=True)
            if label and path not in labels and len(label) < 120:
                labels[path] = label
    return paths, labels


def make_redirect_record(source_path: str, status: int, location: str,
                         final_url: str | None = None) -> dict:
    target = urljoin(LIVE + source_path, location)
    target_path = internal_page_path(target)
    return {
        "source": source_path,
        "status": int(status),
        "target": target,
        "target_path": target_path or target,
        "final_url": final_url or target,
        "external": target_path is None,
    }


def add_redirect_record(source_path: str, record: dict | None) -> None:
    """Record a live redirect unless it would only add/remove a trailing slash."""
    if not record:
        return
    target = record.get("target_path") or ""
    if target.startswith(("http://", "https://")):
        target_norm = None
    else:
        target_norm = unquote(urlsplit(target).path) or "/"
        if target_norm != "/":
            target_norm = target_norm.rstrip("/") or "/"
    source_norm = source_path if source_path == "/" else source_path.rstrip("/") or "/"
    if target_norm is not None and target_norm == source_norm:
        return
    REDIRECTS[source_path] = record
    if source_path.endswith("/") and source_path != "/":
        REDIRECTS[source_path.rstrip("/")] = record


def fetch_page_source(path: str) -> tuple[str | None, str, dict | None]:
    variants = [
        ("live", LIVE + quote_path(path), HEADERS),
        ("staging", STAGING + quote_path(path), HEADERS),
        ("jina", JINA_HTML + quote_path(path), {**HEADERS, "x-respond-with": "html", "x-return-format": "html"}),
    ]
    for name, url, headers in variants:
        try:
            response = http_get(url, headers=headers, timeout=50)
            redirect_record = None
            if response.history:
                first = response.history[0]
                location = first.headers.get("Location") or response.url
                redirect_record = make_redirect_record(path, first.status_code, location, response.url)
            if not response.ok and name != "jina":
                continue
            data = response.content
            if len(data) < 8000 or len(data) > MAX_PAGE_BYTES:
                continue
            page_text = data.decode("utf-8", "replace")
            if "<html" not in page_text.lower() or "</html>" not in page_text.lower():
                continue
            if "Jina Reader" in page_text and "<html" not in page_text[:1000].lower():
                continue
            return normalize_source_domain(page_text), name, redirect_record
        except Exception as exc:  # noqa: BLE001
            print(f"page fetch {name} {path}: {exc}", file=sys.stderr)
    return None, "fallback", None


def probe_redirect(path: str) -> dict | None:
    try:
        response = http_get(
            LIVE + quote_path(path),
            headers={**HEADERS, "Accept": "text/html"},
            timeout=25,
            allow_redirects=False,
        )
        if 300 <= response.status_code < 400 and response.headers.get("Location"):
            return make_redirect_record(path, response.status_code, response.headers["Location"])
    except Exception:  # noqa: BLE001
        return None
    return None


def write_custom_files() -> None:
    (SITE / "assets/css").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/js").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/external").mkdir(parents=True, exist_ok=True)
    (SITE / "assets/css/cosmos-audience.css").write_text(AUDIENCE_CSS, encoding="utf-8")
    (SITE / "assets/css/cosmos-fallback.css").write_text(FALLBACK_CSS, encoding="utf-8")
    (SITE / "assets/js/cosmos-audience.js").write_text(AUDIENCE_JS, encoding="utf-8")


def fetch_all_assets(initial_texts: list[tuple[str, str]]) -> tuple[list[dict], Counter]:
    global TOTAL_ASSET_BYTES
    pending = set()
    for text, base in initial_texts:
        pending.update(discover_asset_urls(text, base))
    seen: set[str] = set()
    failures: list[dict] = []
    statuses: Counter = Counter()
    for depth in range(MAX_RECURSION_PASSES):
        batch = sorted(
            pending - seen,
            key=lambda u: (
                0 if Path(urlsplit(u).path).suffix.lower() in {".css", ".js", ".woff", ".woff2"} else 1,
                u,
            ),
        )
        if not batch:
            break
        print(f"asset pass {depth + 1}: {len(batch)} URLs")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(download_asset, batch))
        for url, result in zip(batch, results):
            seen.add(url)
            statuses[result["status"]] += 1
            if result["status"] != "ok":
                failures.append({k: v for k, v in result.items() if k not in {"data", "text"}})
                continue
            local = result["local"]
            ASSET_MAP[url] = local
            ASSET_RECORDS.append(result)
            if result.get("write"):
                target = file_for_public_path(local)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(result["data"])
            if result.get("text") is not None:
                pending.update(discover_asset_urls(result["text"], result.get("fetched_from") or url))
    # Rewrite text assets after the complete URL map is known.
    for record in ASSET_RECORDS:
        if not record.get("write") or record.get("text") is None:
            continue
        rewritten = rewrite_text(record["text"], record.get("fetched_from") or record["url"])
        target = file_for_public_path(record["local"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(rewritten.encode("utf-8"))
    return failures, statuses


def write_sitemap(urls: list[str]) -> None:
    locs = "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + locs + "\n</urlset>\n"
    (SITE / "sitemap.xml").write_text(xml, encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_robots() -> None:
    try:
        response = http_get(LIVE + "/robots.txt", headers={**HEADERS, "Accept": "text/plain"})
        text = response.text if response.ok and response.text.strip() else "User-agent: *\nAllow: /\n"
    except Exception:  # noqa: BLE001
        text = "User-agent: *\nAllow: /\n"
    if "Sitemap:" not in text:
        text = text.rstrip() + "\n\nSitemap: https://www.cosmos.studio/sitemap.xml\n"
    (SITE / "robots.txt").write_text(text, encoding="utf-8")
    (ROOT / "robots.txt").write_text(text, encoding="utf-8")


def write_redirects() -> None:
    payload = json.dumps(REDIRECTS, indent=2, sort_keys=True) + "\n"
    REDIRECT_FILE.write_text(payload, encoding="utf-8")
    (SITE / "redirects.json").write_text(payload, encoding="utf-8")
    lines = ["# Cosmos Studio redirects captured from the live site."]
    for source, record in sorted(REDIRECTS.items()):
        if source == "/":
            continue
        target = record.get("target_path") or record.get("target")
        if not target.startswith(("http://", "https://")):
            source_norm = source.rstrip("/") or "/"
            target_norm = unquote(urlsplit(target).path) or "/"
            target_norm = target_norm.rstrip("/") or "/"
            if source_norm == target_norm:
                continue
        status = record.get("status", 301)
        if status not in {301, 302, 303, 307, 308}:
            status = 301
        lines.append(f"{source}\t{target}\t{status}")
    (SITE / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")


def html_asset_values(text: str) -> list[str]:
    soup = BeautifulSoup(text, "html.parser")
    values: list[str] = []
    for tag in soup.find_all(True):
        for attr in HTML_URL_ATTRS:
            value = tag.get(attr)
            if not isinstance(value, str):
                continue
            for item in value.split(","):
                item = item.strip()
                if re.search(r"\s+\d+(?:\.\d+)?[wx]\s*$", item):
                    item = item.split()[0]
                if item:
                    values.append(html.unescape(item))
    for style in soup.find_all("style"):
        values.extend(html.unescape(value) for value in CSS_URL_RE.findall(style.get_text()))
    return values


def find_remaining_remote_assets() -> list[str]:
    remaining: set[str] = set()
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".css"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if path.suffix.lower() == ".html":
            values = html_asset_values(text)
        else:
            values = [html.unescape(value) for value in CSS_URL_RE.findall(text)]
        for value in values:
            for match in REMOTE_STATIC_RE.finditer(value):
                url = html.unescape(match.group(0)).rstrip(".,;:!?)]}")
                url_path = urlsplit(url).path.lower()
                if url_path.endswith(("/sitemap.xml", "/robots.txt")):
                    continue
                host = (urlsplit(url).hostname or "").lower()
                if host in INTERNAL_HOSTS or host in STATIC_HOSTS:
                    remaining.add(url)
    return sorted(remaining)


def write_readme(canonical_count: int) -> None:
    (ROOT / "README.md").write_text(
        f"""# Cosmos Studio static clone

This workspace is a strict static clone of `https://www.cosmos.studio/`, built from exact live HTML, styles, scripts, wording, projects, and media references.

- All {canonical_count} canonical sitemap routes and every internal route discovered from those pages have local pages with the exact Cosmos shell.
- Original Webflow CSS, runtime JavaScript, GSAP interactions, fonts, images, Lottie files, posters and media are preserved.
- Referenced static assets are localized under `cosmos-copy/assets/`; any oversized remote media that exceeds the repository size budget is listed in `scripts/cosmos-remaining-remote-assets.json` and keeps its exact Cosmos URL.
- HTTP redirects observed on the live site are recorded in `scripts/cosmos-redirects.json` and implemented by `scripts/serve.py`.
- The only intentional UI change is a light Cosmos-styled audience dropdown beside the logo: `For Marketing Teams`, `For You` (default), `For Tech`, and `Something Else`.
- Custom views for non-default dropdown options are intentionally not implemented.

## Refresh the source

`scripts/fetch_live_cosmos.py` is run by `.github/workflows/fetch-cosmos.yml` on a machine with access to Cosmos and its CDNs. It fetches the live sitemap and route HTML, localizes assets, applies the dropdown, validates the result, captures browser screenshots, and commits the generated site to the current branch.

## Preview

```bash
./scripts/serve.sh 3000
```
""".strip()
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "assets").mkdir(parents=True)
    write_custom_files()

    urls = parse_sitemap_urls()
    canonical_paths = [canonical_path(url) for url in urls]
    CANONICAL_FILE.write_text("\n".join(urls) + "\n", encoding="utf-8")
    print(f"canonical URLs: {len(urls)}")

    known_aliases = {
        "/", "/works", "/services", "/industries", "/legal", "/careers",
        "/generic", "/404", "/index.html", "/404.html",
    }
    all_paths = set(canonical_paths) | known_aliases
    exact_pages: dict[str, str] = {}
    page_sources: dict[str, str] = {}
    attempted: set[str] = set()

    for discovery_pass in range(MAX_DISCOVERY_PASSES):
        todo = sorted(all_paths - attempted)
        if not todo or len(all_paths) > MAX_EXTRA_PATHS + len(canonical_paths):
            break
        print(f"page discovery pass {discovery_pass + 1}: fetching {len(todo)} routes")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(fetch_page_source, todo))
        for path, (page_html, source, redirect_record) in zip(todo, results):
            attempted.add(path)
            add_redirect_record(path, redirect_record)
            if page_html:
                exact_pages[path] = page_html
                page_sources[path] = source
        discovered, _ = collect_internal_paths_and_labels(exact_pages)
        new_paths = discovered - all_paths
        if not new_paths:
            break
        print(f"page discovery pass {discovery_pass + 1}: found {len(new_paths)} new internal routes")
        all_paths.update(new_paths)

    # Probe all live routes for exact redirect headers, including routes that render 200 via a follow.
    probe_paths = sorted(p for p in all_paths if p not in REDIRECTS and not p.endswith(".html"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        probe_results = list(executor.map(probe_redirect, probe_paths))
    for path, record in zip(probe_paths, probe_results):
        add_redirect_record(path, record)

    # Some alias URLs return a bare Webflow 404 page with no Cosmos shell. Use the
    # exact Cosmos fallback shell for those routes instead of carrying the 404 body.
    shell_drops: list[str] = []
    for path, page_html in list(exact_pages.items()):
        soup = BeautifulSoup(page_html, "html.parser")
        if not soup.select_one("nav.navbar, .navbar_component"):
            shell_drops.append(path)
            exact_pages.pop(path, None)
            page_sources.pop(path, None)
    if shell_drops:
        print(f"using Cosmos shell fallback for {len(shell_drops)} non-shell source pages")

    source_counts = Counter(page_sources.values())
    print("page sources:", dict(source_counts))
    if "/" not in exact_pages:
        raise SystemExit("Could not fetch the exact Cosmos home page")

    # Build a staging CDN equivalence map from the exact staging home and all fetched pages.
    try:
        staging_root_response = http_get(STAGING + "/", headers=HEADERS, timeout=45)
        staging_texts = [staging_root_response.text] if staging_root_response.ok else []
    except Exception:  # noqa: BLE001
        staging_texts = []
    staging_texts.extend(exact_pages.values())
    build_staging_equivalents(staging_texts)

    _, link_labels = collect_internal_paths_and_labels(exact_pages)
    fallback_template = make_fallback_template(exact_pages["/"])
    canonical_by_path = {canonical_path(url): url for url in urls}

    seed_assets = """
<a href="/rss.xml">RSS</a>
<link href="/assets/fonts/switzer-variable.woff2" rel="preload"/>
<link href="/assets/fonts/intervariable-latin.woff2" rel="preload"/>
<link href="/assets/fonts/digital-7-mono.woff2" rel="preload"/>
<script src="/assets/js/navhide-1.0.2.js"></script>
<script src="/assets/js/faqpolish-1.0.1.js"></script>
<script src="/assets/js/footerhoverlite-1.0.1.js"></script>
<script src="/assets/js/ddpolish-1.0.0.js"></script>
<img src="/assets/img/red-dot-logo.webp"/>
""".strip()
    pending_texts = [(exact_pages.get(path, fallback_template), LIVE + path) for path in sorted(all_paths)]
    pending_texts.extend((page_html, LIVE + path) for path, page_html in exact_pages.items())
    pending_texts.extend((text, STAGING + "/") for text in staging_texts)
    pending_texts.append((seed_assets, LIVE + "/"))
    failures, asset_statuses = fetch_all_assets(pending_texts)

    pages_written = 0
    fallback_count = 0
    for path in sorted(all_paths):
        exact = exact_pages.get(path)
        if exact:
            page_text = exact
        else:
            fallback_count += 1
            title = link_labels.get(path) or human_title(path)
            canonical = canonical_by_path.get(path, LIVE + path)
            description = f"{title} — Cosmos Studio, a UI/UX design and development studio for SaaS, AI, defense, and military tech."
            page_text = (
                fallback_template
                .replace("__COSMOS_TITLE__", html.escape(f"{title} | Cosmos Studio"))
                .replace("__COSMOS_DESCRIPTION__", html.escape(description, quote=True))
                .replace("__COSMOS_HEADING__", html.escape(title))
                .replace("__COSMOS_CANONICAL__", html.escape(canonical, quote=True))
            )
        canonical = canonical_by_path.get(path, LIVE + path)
        page_text = normalize_source_domain(page_text)
        page_text = rewrite_internal_hrefs(page_text)
        page_text = rewrite_text(page_text, LIVE + path)
        page_text = clean_sri_tags(page_text)
        page_text = inject_dropdown(page_text)
        page_text = inject_custom_assets(page_text)
        page_text = set_page_attributes(page_text, path, canonical)
        target = page_file(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_text, encoding="utf-8")
        pages_written += 1

    if (SITE / "404/index.html").exists():
        (SITE / "404.html").write_text((SITE / "404/index.html").read_text(encoding="utf-8"), encoding="utf-8")
    elif (SITE / "index.html").exists() and not (SITE / "404.html").exists():
        (SITE / "404.html").write_text((SITE / "index.html").read_text(encoding="utf-8"), encoding="utf-8")

    # Exact blog pages use a relative `rss.xml` link. Keep the literal link
    # unchanged, but also expose the captured feed at the site root so the
    # static server and validator can resolve that special file.
    blog_rss = SITE / "blog" / "rss.xml"
    root_rss = SITE / "rss.xml"
    if blog_rss.exists() and not root_rss.exists():
        root_rss.write_bytes(blog_rss.read_bytes())
        ASSET_MAP[f"{LIVE}/rss.xml"] = "/rss.xml"

    write_sitemap(urls)
    write_robots()
    write_redirects()
    ASSET_MAP_FILE.write_text(json.dumps(ASSET_MAP, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    remaining_remote = find_remaining_remote_assets()
    REMOTE_FILE.write_text(json.dumps(remaining_remote, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (SITE / "remaining-remote-assets.json").write_text(
        json.dumps(remaining_remote, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    site_files = [p for p in SITE.rglob("*") if p.is_file()]
    total_bytes = sum(p.stat().st_size for p in site_files)
    report = {
        "canonical_url_count": len(urls),
        "canonical_paths": canonical_paths,
        "exact_page_count": len(exact_pages),
        "page_source_counts": dict(source_counts),
        "internal_route_count": len(all_paths),
        "pages_written": pages_written,
        "fallback_pages": fallback_count,
        "redirect_count": len(REDIRECTS),
        "asset_urls_seen": sum(asset_statuses.values()),
        "asset_status_counts": dict(asset_statuses),
        "localized_asset_count": len(ASSET_MAP),
        "remaining_remote_asset_count": len(remaining_remote),
        "asset_failures": failures[:300],
        "site_file_count": len(site_files),
        "site_total_bytes": total_bytes,
        "dropdown": ["For Marketing Teams", "For You", "For Tech", "Something Else"],
        "default_dropdown": "For You",
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (SITE / "build-manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(len(urls))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
