#!/usr/bin/env python3
"""Fail when the last browser preview still has broken local responses or errors.

Works for both the strict-clone pre-customization preview and the customized
LulaZel Hub preview; the capture script records which mode it used.
"""
from __future__ import annotations

import json
import os
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
    custom = count(report.get("customMarkerIssues", report.get("custom_marker_issues")))
    forms = count(report.get("formActionIssues", report.get("form_action_issues")))
    book_calls = count(report.get("bookCallIssues", report.get("book_call_issues")))
    blank = [check.get("page") for check in report.get("domChecks", []) if check.get("bodyTextLength", 0) < 800]
    expected_mode = os.environ.get("EXPECTED_PREVIEW_MODE")
    mode_issue = bool(expected_mode and report.get("previewMode") != expected_mode)
    if failed or errors or legacy or custom or forms or book_calls or blank or mode_issue:
        print(json.dumps({
            "previewMode": report.get("previewMode", "unknown"),
            "expectedPreviewMode": expected_mode or None,
            "failedLocalResponses": failed,
            "pageErrors": errors,
            "legacyMarkerHits": legacy,
            "customMarkerIssues": custom,
            "formActionIssues": forms,
            "bookCallIssues": book_calls,
            "blankPages": blank,
        }, indent=2, sort_keys=True))
        sys.exit(1)
    print(
        "browser preview clean: 0 failed local responses, 0 page errors, "
        "0 legacy markers, 0 custom marker issues, 0 form issues, "
        "0 Book a Call issues, no blank pages"
    )


if __name__ == "__main__":
    main()
