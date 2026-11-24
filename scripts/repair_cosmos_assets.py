#!/usr/bin/env python3
"""Second-pass repair of Cosmos assets discovered by the browser runtime.

The exact live Webflow HTML contains dynamic chunk URLs and headkit-injected
scripts that are not visible as literal URLs in the source HTML. This script
uses the first browser pass's failed local responses plus a static scan of the
generated clone to fetch those exact resources from Cosmos/Webflow/CDN mirrors,
then rewrites and refreshes the build manifests.
"""
from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import fetch_live_cosmos as f

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "cosmos-copy"
ASSET_MAP_FILE = ROOT / "scripts/cosmos-asset-map.json"
REPORT_FILE = ROOT / "scripts/cosmos-live-build-report.json"
REMOTE_FILE = ROOT / "scripts/cosmos-remaining-remote-assets.json"
BROWSER_REPORT = ROOT / "scripts/preview-check/browser-report.json"
REPAIR_REPORT = ROOT / "scripts/cosmos-repair-report.json"

LOCAL_STATIC_RE = re.compile(
    r"""(?<!:)/[A-Za-z0-9_\-./%~+]+\.(?:css|mjs|js|woff2?|ttf|otf|png|jpe?g|webp|avif|svg|gif|ico|mp4|webm|mov|json|lottie|pdf|txt|xml)(?:\?[^\s"'`<>)\\]*)?""",
    re.I,
)
CRITICAL_EXTS = {".css", ".js", ".mjs", ".woff", ".woff2", ".ttf", ".otf", ".svg", ".json", ".lottie"}

initial_map: dict[str, str] = {}
if ASSET_MAP_FILE.exists():
    initial_map = json.loads(ASSET_MAP_FILE.read_text(encoding="utf-8"))
f.ASSET_MAP.update(initial_map)


def write_result(result: dict, url: str, local: str) -> None:
    target = f.file_for_public_path(local)
    target.parent.mkdir(parents=True, exist_ok=True)
    if result.get("text") is not None:
        rewritten = f.rewrite_text(result["text"], result.get("fetched_from") or url)
        target.write_bytes(rewritten.encode("utf-8"))
    else:
        target.write_bytes(result["data"])


def local_exists(local: str) -> bool:
    path = urlsplit(html.unescape(local)).path
    return (SITE / f.safe_rel_path(path.lstrip("/"))).exists()


def build_equivalents() -> None:
    texts: list[str] = []
    try:
        response = f.http_get(f.STAGING + "/", headers=f.HEADERS, timeout=45)
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


def missing_local_paths() -> set[str]:
    paths = browser_failed_paths()
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in f.TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in LOCAL_STATIC_RE.finditer(text):
            local = html.unescape(match.group(0)).rstrip(".,;:!?)]}")
            if local.startswith("//") or Path(urlsplit(local).path).suffix.lower() not in f.STATIC_EXTS:
                continue
            if not local_exists(local):
                paths.add(local)
    return {p for p in paths if p.startswith("/") and not p.startswith("//")}


def critical_remote_urls() -> set[str]:
    urls = set(f.find_remaining_remote_assets())
    if REMOTE_FILE.exists():
        try:
            urls.update(json.loads(REMOTE_FILE.read_text(encoding="utf-8")))
        except ValueError:
            pass
    return {
        url for url in urls
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


def main() -> None:
    build_equivalents()
    local_repaired: set[str] = set()
    remote_repaired: set[str] = set()
    failures: list[dict] = []
    attempted_local: set[str] = set()
    attempted_remote: set[str] = set()
    summaries: list[dict] = []

    for pass_index in range(3):
        missing = {p for p in missing_local_paths() if p not in attempted_local}
        remote = {u for u in critical_remote_urls() if u not in attempted_remote}
        print(f"repair pass {pass_index + 1}: {len(missing)} local paths, {len(remote)} critical remote URLs")
        new_mappings = False
        for local in sorted(missing):
            attempted_local.add(local)
            url = f.LIVE + local
            result = f.download_asset(url)
            if result.get("status") == "ok":
                write_result(result, url, local)
                f.ASSET_MAP[url] = local
                local_repaired.add(local)
                new_mappings = True
            else:
                failures.append({"url": url, "local": local, **{k: v for k, v in result.items() if k not in {"data", "text"}}})
        for remote_url in sorted(remote):
            attempted_remote.add(remote_url)
            result = f.download_asset(remote_url)
            if result.get("status") == "ok":
                local = f.public_path_for_asset(remote_url, result.get("content_type", ""))
                write_result(result, remote_url, local)
                f.ASSET_MAP[remote_url] = local
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
