#!/usr/bin/env python3
"""Static server for the customized source-site clone, with captured live redirects."""
from __future__ import annotations

import json
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "cosmos-copy"
REDIRECTS_FILE = SITE / "redirects.json"


def load_redirects() -> dict[str, dict]:
    if not REDIRECTS_FILE.exists():
        return {}
    try:
        return json.loads(REDIRECTS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


REDIRECTS = load_redirects()


class CosmosHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".json": "application/json",
        ".lottie": "application/json",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".txt": "text/plain; charset=utf-8",
        ".xml": "application/xml",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def resolve_redirect(self, path: str) -> dict | None:
        candidates = [path]
        if path != "/":
            candidates.append(path.rstrip("/") or "/")
            candidates.append(path.rstrip("/") + "/")
        for candidate in candidates:
            if candidate in REDIRECTS:
                return REDIRECTS[candidate]
        return None

    def rewrite_path(self) -> bool:
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        record = self.resolve_redirect(path)
        if record:
            target = record.get("target_path") or record.get("target") or "/"
            if parsed.query:
                target += ("&" if "?" in target else "?") + parsed.query
            try:
                status = int(record.get("status", 301))
            except (TypeError, ValueError):
                status = 301
            if status not in {301, 302, 303, 307, 308}:
                status = 301
            self.send_response(status)
            self.send_header("Location", target)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return True

        new_path = re.sub(r"/assets/js/(?:/+)?assets/js/", "/assets/js/", parsed.path)
        rel_path = unquote(new_path).lstrip("/")
        if rel_path.endswith("rss.xml") and rel_path not in {"rss.xml", "blog/rss.xml"} and not (SITE / rel_path).exists() and (SITE / "rss.xml").exists():
            new_path = "/rss.xml"
        elif new_path == "/":
            new_path = "/index.html"
        elif not Path(urlsplit(new_path).path).suffix:
            rel = unquote(new_path).lstrip("/")
            index_candidate = SITE / rel / "index.html"
            html_candidate = SITE / f"{rel}.html"
            if index_candidate.exists():
                new_path = "/" + index_candidate.relative_to(SITE).as_posix()
            elif html_candidate.exists():
                new_path = "/" + html_candidate.relative_to(SITE).as_posix()
        self.path = new_path + (("?" + parsed.query) if parsed.query else "")
        return False

    def do_GET(self) -> None:
        if self.rewrite_path():
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        if self.rewrite_path():
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    server = ThreadingHTTPServer(("0.0.0.0", port), CosmosHandler)
    print(f"Serving LulaZel Hub static site on 0.0.0.0:{port} with {len(REDIRECTS)} redirects", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
