#!/usr/bin/env python3
"""Fail when the last browser preview still has broken local responses or errors."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPORT = Path(__file__).resolve().parents[1] / "scripts/preview-check/browser-report.json"


def count(value) -> int:
    if isinstance(value, list):
        return len(value)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    if not REPORT.exists():
        raise SystemExit("browser report missing")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    failed = count(report.get("failedLocalResponses", report.get("failed_local_responses")))
    errors = count(report.get("pageErrors", report.get("page_errors")))
    legacy = count(report.get("legacyMarkerHits", report.get("legacy_marker_hits")))
    blank = [check.get("page") for check in report.get("domChecks", []) if check.get("bodyTextLength", 0) < 800]
    if failed or errors or legacy or blank:
        print(json.dumps({
            "failedLocalResponses": failed,
            "pageErrors": errors,
            "legacyMarkerHits": legacy,
            "blankPages": blank,
        }, indent=2, sort_keys=True))
        sys.exit(1)
    print("browser preview clean: 0 failed local responses, 0 page errors, 0 legacy markers, no blank pages")


if __name__ == "__main__":
    main()
