#!/usr/bin/env python3
"""Second-pass repair of Cosmos assets discovered by the browser runtime.

The exact live Webflow HTML contains dynamic chunk URLs and headkit-injected
scripts that are not visible as literal URLs in the source HTML. This script
uses the first browser pass's failed local responses plus a recursive static
scan of the generated clone to fetch those exact resources from Cosmos/Webflow
and their original CDN mirrors, then rewrites and refreshes the manifests.
"""
from __future__ import annotations

import concurrent.futures
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

import fetch_live_cosmos as f

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "cosmos-copy"
ASSET_MAP_FILE = ROOT / "scripts/cosmos-asset-map.json"
REPORT_FILE = ROOT / "scripts/cosmos-live-build-report.json"
REMOTE_FILE = ROOT / "scripts/cosmos-remaining-remote-assets.json"
BROWSER_REPORT = ROOT / "scripts/preview-check/browser-report.json"
REPAIR_REPORT = ROOT / "scripts/cosmos-repair-report.json"

LOCAL_STATIC_RE = re.compile(
    r"""(?<![:/])/[A-Za-z0-9_\-./%~+]+\.(?:css|mjs|js|woff2?|ttf|otf|png|jpe?g|webp|avif|svg|gif|ico|mp4|webm|mov|json|lottie|pdf|txt|xml)(?:\?[^\s"'`<>)\\]*)?""",
    re.I,
)
CSS_LOCAL_URL_RE = re.compile(r"url\(\s*['\"]?([^)'\"]+)", re.I)
JS_RELATIVE_RE = re.compile(
    r"""["']?(\.{1,2}/[A-Za-z0-9_\-./%~+]+\.(?:css|mjs|js|json))["']?""",
    re.I,
)
CRITICAL_EXTS = {".css", ".js", ".mjs", ".woff", ".woff2", ".ttf", ".otf", ".svg", ".json", ".lottie"}
REMOTE_HOST_MARKERS = {
    "cdn.prod.website-files.com", "assets.website-files.com",
    "assets-global.website-files.com", "uploads-ssl.webflow.com",
    "cloudinary.com", "cloudfront.net", "jsdelivr.net", "unpkg.com",
    "raw.githubusercontent.com", "fonts.gstatic.com", "fonts.googleapis.com",
    "clarity.ms", "www.clarity.ms", "video.cosmos.studio",
}

initial_map: dict[str, str] = {}
if ASSET_MAP_FILE.exists():
    initial_map = json.loads(ASSET_MAP_FILE.read_text(encoding="utf-8"))
f.ASSET_MAP.update(initial_map)


def is_static_host(host: str) -> bool:
    host = host.lower()
    return host in f.INTERNAL_HOSTS or host in f.STATIC_HOSTS or any(marker in host for marker in REMOTE_HOST_MARKERS)


def local_mirror_for_remote(url: str) -> str | None:
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    if not is_static_host(host):
        return None
    query = ("?" + p.query) if p.query else ""
    if host in f.INTERNAL_HOSTS:
        return f.quote_path(p.path) + query
    return "/_m/" + p.netloc + f.quote_path(p.path) + query


def register_mapping(url: str, local: str, extra_urls: list[str] | None = None) -> None:
    urls = [url] + (extra_urls or [])
    for candidate in urls:
        if not candidate:
            continue
        p = urlsplit(candidate)
        if not is_static_host((p.hostname or "").lower()):
            continue
        f.ASSET_MAP[candidate] = local
        encoded = urlunsplit((p.scheme, p.netloc, f.quote_path(p.path), p.query, ""))
        if encoded != candidate:
            f.ASSET_MAP[encoded] = local
        mirror = local_mirror_for_remote(candidate)
        if mirror and mirror != local:
            f.ASSET_MAP[candidate] = mirror
            f.ASSET_MAP[encoded] = mirror
    if local.startswith("/"):
        f.ASSET_MAP[f.LIVE + local] = local


def fast_fetch(url: str) -> dict:
    """Fetch one exact asset quickly from a small set of equivalent mirrors."""
    last_status = "no-candidate"
    for candidate in f.asset_candidates(url)[:4]:
        try:
            headers = f.ASSET_HEADERS.copy()
            if "jsdelivr.net" in (urlsplit(candidate).hostname or ""):
                headers.pop("Referer", None)
            response = requests.get(candidate, headers=headers, timeout=12, allow_redirects=True)
            if not response.ok:
                last_status = f"http-{response.status_code}"
                continue
            ctype = response.headers.get("content-type", "")
            data = response.content
            if not data or len(data) > f.MAX_ASSET_BYTES:
                last_status = "empty-or-too-large"
                continue
            if ctype.startswith("text/html") and not data.lstrip().lower().startswith(b"<svg"):
                last_status = "html-response"
                continue
            text = f.is_text_asset(url, ctype, data)
            return {
                "url": url,
                "status": "ok",
                "data": data,
                "text": text,
                "size": len(data),
                "content_type": ctype,
                "base_url": candidate,
                "fetched_from": response.url,
            }
        except Exception as exc:  # noqa: BLE001
            last_status = f"error:{type(exc).__name__}"
    return {"url": url, "status": last_status}


def write_result(result: dict, url: str, local: str) -> None:
    target = f.file_for_public_path(local)
    target.parent.mkdir(parents=True, exist_ok=True)
    base = result.get("base_url") or result.get("fetched_from") or url
    if result.get("text") is not None:
        rewritten = f.rewrite_text(result["text"], base)
        target.write_bytes(rewritten.encode("utf-8"))
    else:
        target.write_bytes(result["data"])


def local_exists(local: str) -> bool:
    path = urlsplit(html.unescape(local)).path
    return (SITE / f.safe_rel_path(path.lstrip("/"))).exists()


def build_equivalents() -> None:
    texts: list[str] = []
    try:
        response = requests.get(f.STAGING + "/", headers=f.HEADERS, timeout=10)
        if response.ok:
            texts.append(response.text)
    except Exception as exc:  # noqa: BLE001
        print(f"staging root warning: {exc}", file=sys.stderr)
    f.build_staging_equivalents(texts)
    remote_urls = set(initial_map.keys())
    if REMOTE_FILE.exists():
        try:
            remote_urls.update(json.loads(REMOTE_FILE.read_text(encoding="utf-8")))
        except ValueError:
            pass
    for url in remote_urls:
        for key in f.asset_keys(url):
            bucket = f.STAGING_EQUIVALENTS.setdefault(key, [])
            if url not in bucket:
                bucket.append(url)


def browser_failed_paths() -> set[str]:
    paths: set[str] = set()
    if not BROWSER_REPORT.exists():
        return paths
    try:
        report = json.loads(BROWSER_REPORT.read_text(encoding="utf-8"))
    except ValueError:
        return paths
    for item in report.get("failedLocalResponses", []):
        url = item.get("url", "")
        p = urlsplit(url)
        local = p.path + (("?" + p.query) if p.query else "")
        if local and Path(p.path).suffix.lower() in f.STATIC_EXTS:
            paths.add(local)
    return paths


def html_local_values(text: str) -> list[str]:
    soup = BeautifulSoup(text, "html.parser")
    values: list[str] = []
    for tag in soup.find_all(True):
        for attr in f.HTML_URL_ATTRS:
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
        values.extend(html.unescape(v) for v in CSS_LOCAL_URL_RE.findall(style.get_text()))
    return values


def base_url_for_generated_js(public: str) -> str:
    for remote, local in f.ASSET_MAP.items():
        if urlsplit(local).path == public:
            return remote
    return f.LIVE + public


def js_values(text: str, public: str) -> tuple[list[str], list[str]]:
    base = base_url_for_generated_js(public)
    local_values: list[str] = []
    remote_values: list[str] = []
    for match in LOCAL_STATIC_RE.finditer(text):
        value = html.unescape(match.group(0)).rstrip(".,;:!?)]}")
        if urlsplit(value).path.startswith(f.ASSET_PREFIXES):
            local_values.append(value)
    for match in JS_RELATIVE_RE.finditer(text):
        absolute = urljoin(base, html.unescape(match.group(1)))
        remote_values.append(absolute)
    for match in f.REMOTE_STATIC_RE.finditer(text):
        remote_values.append(html.unescape(match.group(0)).rstrip(".,;:!?)]}"))
    return local_values, remote_values


def discovered_remote_urls() -> set[str]:
    urls = set(f.find_remaining_remote_assets())
    if REMOTE_FILE.exists():
        try:
            urls.update(json.loads(REMOTE_FILE.read_text(encoding="utf-8")))
        except ValueError:
            pass
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".js", ".mjs"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        public = "/" + path.relative_to(SITE).as_posix()
        _, remote_values = js_values(text, public)
        for value in remote_values:
            host = (urlsplit(value).hostname or "").lower()
            if is_static_host(host) and Path(urlsplit(value).path).suffix.lower() in CRITICAL_EXTS:
                urls.add(value)
    return urls


def missing_local_paths() -> set[str]:
    paths = browser_failed_paths()
    for remote in discovered_remote_urls():
        mirror = local_mirror_for_remote(remote)
        if mirror and not local_exists(mirror):
            paths.add(mirror)
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in f.TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        suffix = path.suffix.lower()
        if suffix == ".html":
            values = html_local_values(text)
        elif suffix == ".css":
            values = CSS_LOCAL_URL_RE.findall(text)
        elif suffix in {".js", ".mjs"}:
            public = "/" + path.relative_to(SITE).as_posix()
            local_values, _ = js_values(text, public)
            values = local_values
        else:
            values = [html.unescape(m.group(0)) for m in LOCAL_STATIC_RE.finditer(text)]
        for value in values:
            for match in LOCAL_STATIC_RE.finditer(html.unescape(value)):
                local = html.unescape(match.group(0)).rstrip(".,;:!?)]}")
                p = urlsplit(local).path
                if local.startswith("//") or not p.startswith(f.ASSET_PREFIXES):
                    continue
                if Path(p).suffix.lower() not in f.STATIC_EXTS:
                    continue
                if not local_exists(local):
                    paths.add(local)
                mirror = local_mirror_for_remote(f.LIVE + local)
                if mirror and mirror != local and not local_exists(mirror):
                    paths.add(mirror)
    return {p for p in paths if p.startswith("/") and not p.startswith("//")}


def critical_remote_urls() -> set[str]:
    return {
        url for url in discovered_remote_urls()
        if Path(urlsplit(url).path).suffix.lower() in CRITICAL_EXTS
    }


def rewrite_all_text_files() -> None:
    reverse_map: dict[str, str] = {}
    for remote, local in f.ASSET_MAP.items():
        reverse_map.setdefault(urlsplit(local).path, remote)
    changed = 0
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in f.TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(SITE).as_posix()
        base = reverse_map.get("/" + rel, f.LIVE + "/" + rel)
        rewritten = f.rewrite_text(text, base)
        if rewritten != text:
            path.write_text(rewritten, encoding="utf-8")
            changed += 1
    print(f"rewrote {changed} text files")


def update_manifests(local_repaired: set[str], remote_repaired: set[str], failures: list[dict]) -> dict:
    ASSET_MAP_FILE.write_text(json.dumps(f.ASSET_MAP, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (SITE / "asset-map.json").write_text(json.dumps(f.ASSET_MAP, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    remaining = f.find_remaining_remote_assets()
    REMOTE_FILE.write_text(json.dumps(remaining, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (SITE / "remaining-remote-assets.json").write_text(
        json.dumps(remaining, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = json.loads(REPORT_FILE.read_text(encoding="utf-8")) if REPORT_FILE.exists() else {}
    site_files = [p for p in SITE.rglob("*") if p.is_file()]
    total_bytes = sum(p.stat().st_size for p in site_files)
    report["localized_asset_count"] = len(f.ASSET_MAP)
    report["remaining_remote_asset_count"] = len(remaining)
    report["site_file_count"] = len(site_files)
    report["site_total_bytes"] = total_bytes
    report["repaired_local_assets"] = sorted(local_repaired)
    report["repaired_remote_assets"] = sorted(remote_repaired)
    report["repair_failures"] = failures[:300]
    statuses = Counter(report.get("asset_status_counts", {}))
    statuses["repaired"] = len(local_repaired) + len(remote_repaired)
    report["asset_status_counts"] = dict(statuses)
    REPORT_FILE.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (SITE / "build-manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "local_repaired": len(local_repaired),
        "remote_repaired": len(remote_repaired),
        "failures": len(failures),
        "remaining_remote_assets": len(remaining),
        "site_file_count": len(site_files),
        "site_total_bytes": total_bytes,
        "remaining_missing_local_paths": len(missing_local_paths()),
    }


def previous_attempts() -> tuple[set[str], set[str]]:
    attempted_local: set[str] = set()
    attempted_remote: set[str] = set()
    if not REPAIR_REPORT.exists():
        return attempted_local, attempted_remote
    try:
        previous = json.loads(REPAIR_REPORT.read_text(encoding="utf-8"))
    except ValueError:
        return attempted_local, attempted_remote
    attempted_local.update(previous.get("attempted_local", []))
    attempted_remote.update(previous.get("attempted_remote", []))
    for item in previous.get("failures", []):
        if item.get("local"):
            attempted_local.add(item["local"])
        elif item.get("url"):
            attempted_remote.add(item["url"])
    return attempted_local, attempted_remote


def main() -> None:
    build_equivalents()
    local_repaired: set[str] = set()
    remote_repaired: set[str] = set()
    failures: list[dict] = []
    attempted_local, attempted_remote = previous_attempts()
    summaries: list[dict] = []

    for pass_index in range(5):
        missing = {p for p in missing_local_paths() if p not in attempted_local}
        remote = {u for u in critical_remote_urls() if u not in attempted_remote}
        print(f"repair pass {pass_index + 1}: {len(missing)} local paths, {len(remote)} critical remote URLs")
        new_mappings = False

        local_batch = sorted(missing)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            local_results = list(executor.map(fast_fetch, [f.LIVE + p for p in local_batch]))
        for local, result in zip(local_batch, local_results):
            attempted_local.add(local)
            if result.get("status") == "ok":
                write_result(result, f.LIVE + local, local)
                extra = [result.get("base_url"), result.get("fetched_from")]
                register_mapping(f.LIVE + local, local, [x for x in extra if x])
                local_repaired.add(local)
                new_mappings = True
            else:
                failures.append({"url": f.LIVE + local, "local": local, **{k: v for k, v in result.items() if k not in {"data", "text"}}})

        remote_batch = sorted(remote)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            remote_results = list(executor.map(fast_fetch, remote_batch))
        for remote_url, result in zip(remote_batch, remote_results):
            attempted_remote.add(remote_url)
            if result.get("status") == "ok":
                local = local_mirror_for_remote(remote_url) or f.public_path_for_asset(remote_url, result.get("content_type", ""))
                write_result(result, remote_url, local)
                register_mapping(remote_url, local, [result.get("base_url"), result.get("fetched_from")])
                remote_repaired.add(remote_url)
                new_mappings = True
            else:
                failures.append({"url": remote_url, **{k: v for k, v in result.items() if k not in {"data", "text"}}})

        if new_mappings:
            rewrite_all_text_files()
        summary = update_manifests(local_repaired, remote_repaired, failures)
        summaries.append(summary)
        print(f"repair pass {pass_index + 1}: {json.dumps(summary, sort_keys=True)}")
        if not new_mappings:
            break

    REPAIR_REPORT.write_text(json.dumps({
        "passes": summaries,
        "local_repaired": sorted(local_repaired),
        "remote_repaired": sorted(remote_repaired),
        "attempted_local": sorted(attempted_local),
        "attempted_remote": sorted(attempted_remote),
        "failures": failures[:500],
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "passes": summaries,
        "local_repaired": len(local_repaired),
        "remote_repaired": len(remote_repaired),
        "failures": len(failures),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
