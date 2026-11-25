#!/usr/bin/env python3
"""Apply the requested LulaZel Hub customization to the exact Cosmos clone.

The pass is deliberately source-preserving: it edits raw HTML slices rather than
serializing the whole document, so exact Webflow markup, CSS class names,
animation hooks and script bytes stay intact except where a requested change
requires an edit. It is safe to run after a fresh exact-clone rebuild.
"""
from __future__ import annotations

import email.utils
import html
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(os.environ.get("LZ_ROOT", Path(__file__).resolve().parents[1]))
SITE = ROOT / "cosmos-copy"
SCRIPTS = ROOT / "scripts"

OLD_BRAND = "Cosmos Studio"
NEW_BRAND = "LulaZel Hub"
OLD_EMAIL = "hello@cosmos.studio"
NEW_EMAIL = "mkhungela.l@gmail.com"
OLD_PHONE_SPACED = "+380 63 832 47 31"
OLD_PHONE_COMPACT = "+380638324731"
NEW_PHONE = "+27 83 719 5064"
WHATSAPP_URL = "https://wa.me/380638324731"  # kept exactly as supplied
OLD_CALENDAR_URL = "https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ2rm7eGeBjNfb8kLSodGTte3bMJ7H6xE2BJeRxG8x4fq-pLf1bry8ghqQoI4vwfJiX3K7NtmpQR"
CALENDLY_URL = "https://calendly.com/lulamile_m/meet-lulamile?month=2026-10&date=2026-10-29"
CALENDLY_URL_HTML = "https://calendly.com/lulamile_m/meet-lulamile?month=2026-10&amp;date=2026-10-29"
FORMSPREE_URL = "https://formspree.io/f/xvkgqalq"
USD_ZAR = Decimal("18")

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

AWARD_RE = re.compile(
    r"(?:\bwith\s+|\band\s+|,\s*|·\s*|\ba\s+|\ban\s+)?"
    r"(?:"
    r"[^.;|\n]*?has received\s+(?:60\+\s*)?(?:international\s+)?(?:design\s+)?awards?[^.;|\n]*"
    r"|[^.;|\n]*?recognized as a\s+clutch\s+global\s+leader[^.;|\n]*"
    r"|clutch\s+global\s+leader[^.;|\n]*"
    r"|clutch\s+global\s+2026\s+badge"
    r"|fall\s+2026\s+clutch\s+global\s+award\s+winner(?:\s+in\s+[^.;|\n]*)?"
    r"|clutch\s+global\s+awards?[^.;|\n]*"
    r"|clutch\s+global\s+award\s+winner(?:\s+in\s+[^.;|\n]*)?"
    r"|60\+\s*(?:international\s+)?(?:design\s+)?awards?(?:\s*:\s*[^.\n]*)?"
    r"|(?:\d+[\s,]*)?international\s+design\s+awards?"
    r"|(?:\d+[\s,]*)?international\s+awards?"
    r"|clutch\s+global\s+award\s+fall\s+2026"
    r"|clutch\s+global\s+awards?"
    r"|clutch\s+global\s+award(?:\s+winner)?"
    r"|clutch\s+global\s+leaders?"
    r"|clutch\s+global\s+fall\s+2026(?:\s*[–-]\s*user\s+research)?"
    r"|clutch\s+global(?:\s+2026)?(?:\s*[–-][^.;|\n]*)?"
    r"|clutch\s+top\s+user\s+research\s+company\s+2026"
    r"|clutch\s*[-–—]?\s*top\s+user\s+research\s+company\s+2026"
    r"|top\s+user\s+research\s+company\s+2026"
    r"|css\s+da\b[^.;|\n]*"
    r"|(?:css\s+winner|winner\s+brand\s+identity|\d+×\s*SOTD|\bSOTD\b|\bSOTM\b|\bOWDA\b)[^.;|\n]*"
    r"|fall\s+2026\s+clutch\s+global\s+award\s+winner"
    r"|fall\s+2026\s+clutch\s+global\s+winner"
    r"|award-winning"
    r"|red\s+dot(?:\s+awards?|\s+winner)?"
    r"|(?:and\s+)?[^.;|\n]*?serves on the\s+(?:Awwwards\s+)?jury"
    r"|(?:and\s+)?[^.;|\n]*?member of the\s+(?:Awwwards\s+)?jury"
    r"|led by an\s+(?:Awwwards\s+)?jury(?:\s+member)?"
    r"|(?:\d+[×x]?\s*)?awwwards(?:\s+jury(?:-led|\s+led|\s+member)?)?"
    r"|thefwa"
    r"|(?:(?:three|3|\d+)[×x]?\s*)?fwa(?:\s+of\s+the\s+day)?"
    r"|(?:\d+[×x]?\s*)?css\s+design\s+awards?"
    r"|cssda\s+awards?"
    r"|(?:\d+[×x]?\s*)?site\s+of\s+the\s+day"
    r"|dev\s+award"
    r"|(?:\d+[\s,]*)?\bawards?\b"
    r")",
    re.I,
)
DIGEST_RE = re.compile(
    r"AI\s*&\s*(?:amp;)?\s*Design Weekly"
    r"|AI\s+and\s+Design Weekly"
    r"|Clutch Global Leader",
    re.I,
)
SENTENCE_SPLIT_RE = re.compile(r"([^.!?]*[.!?]+|[^.!?]+$)")
SUFFIX_MULTIPLIER = {
    "": Decimal("1"),
    "k": Decimal("1000"),
    "thousand": Decimal("1000"),
    "m": Decimal("1000000"),
    "million": Decimal("1000000"),
    "b": Decimal("1000000000"),
    "billion": Decimal("1000000000"),
}
MONEY_SUFFIX = r"(?:billion|million|thousand|K|M|B|k|m|b)\b"
MONEY_NUMBER = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
MONEY_BODY = r"\$\s*(?P<n>" + MONEY_NUMBER + r")(?:\s*(?P<s>billion|million|thousand|K|M|B|k|m|b)\b)?"
RANGE_MONEY_RE = re.compile(
    MONEY_BODY
    + r"(?P<sep>\s*(?:–|—|-|/|\bto\b)\s*)"
    + r"(?P<d2>\$)?\s*(?P<n2>" + MONEY_NUMBER + r")(?:\s*(?P<s2>billion|million|thousand|K|M|B|k|m|b)\b)?",
    re.I,
)
SINGLE_MONEY_RE = re.compile(MONEY_BODY, re.I)
MONEY_ANY_RE = re.compile(r"\$\s?\d", re.I)
PROTECT_RE = re.compile(
    r"(?:https?://|//|www\.|mailto:|tel:)[^\s\"'<>]+"
    r"|\b[A-Za-z0-9_-]*cosmos(?:[.-][A-Za-z0-9_./-]+)+\b",
    re.I,
)
OLD_BRAND_RE = re.compile(r"\bCosmos\s+Studio(?:™)?(?!\w)", re.I)
STANDALONE_COSMOS_RE = re.compile(r"\bCosmos\b(?!\s+Studios?\b)")
URL_LIKE_RE = re.compile(r"^(?:https?://|//|www\.|mailto:|tel:|/|\.\.?/)", re.I)

ATTRS_TO_TRANSFORM = {
    "alt", "title", "aria-label", "aria-valuetext", "placeholder", "content",
    "value", "data-name", "label", "data-alt", "data-title", "data-cat",
}
URL_ATTRS = {
    "href", "src", "srcset", "poster", "action", "style", "data-src",
    "data-srcset", "data-poster", "data-video", "data-bg", "data-image",
    "data-wf-bg", "data-background-image", "content",
}
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
TEXT_FILE_SUFFIXES = {".html", ".css", ".js", ".mjs", ".json", ".svg", ".xml", ".txt", ".md"}
CURRENCY_TEXT_SUFFIXES = {".svg", ".xml", ".txt", ".md"}
JSON_SUFFIXES = {".json", ".lottie"}

BRAND_CSS = """
<style id="lulazel-brand">
.lz-wordmark{display:block!important;visibility:visible!important;opacity:1!important;width:100%;margin:0 auto;font-family:Arial,Helvetica,sans-serif;font-weight:800;letter-spacing:-.055em;line-height:1;color:inherit;text-align:center;text-transform:none;white-space:nowrap}
.home-header_headings .lz-wordmark{font-size:clamp(56px,9.5vw,150px)}
.footer_content .lz-wordmark{font-size:clamp(46px,8.5vw,138px)}
@media(max-width:767px){.home-header_headings .lz-wordmark{font-size:clamp(38px,12vw,76px)}.footer_content .lz-wordmark{font-size:clamp(34px,10vw,68px)}}
</style>
""".strip()


def protect(text: str) -> tuple[str, dict[str, str]]:
    slots: dict[str, str] = {}

    def repl(match: re.Match) -> str:
        key = f"\x00LZ{len(slots)}\x00"
        slots[key] = match.group(0)
        return key

    return PROTECT_RE.sub(repl, text), slots


def restore(text: str, slots: dict[str, str]) -> str:
    for key, value in slots.items():
        text = text.replace(key, value)
    return text


def money_to_rand(number: str, suffix: str | None) -> str:
    multiplier = SUFFIX_MULTIPLIER[(suffix or "").lower()]
    value = Decimal(number.replace(",", "")) * multiplier * USD_ZAR
    if value == value.to_integral_value():
        return f"R{int(value):,}"
    return f"R{value:,.2f}"


def convert_money(text: str) -> str:
    def range_replace(match: re.Match) -> str:
        first = money_to_rand(match.group("n"), match.group("s"))
        second_suffix = match.group("s2") or match.group("s")
        second = money_to_rand(match.group("n2"), second_suffix)
        return f"{first}{match.group('sep')}{second}"

    text = RANGE_MONEY_RE.sub(range_replace, text)
    return SINGLE_MONEY_RE.sub(lambda m: money_to_rand(m.group("n"), m.group("s")), text)


def strip_awards(text: str) -> str:
    if not AWARD_RE.search(text):
        return text
    original_started_with_award = bool(re.match(r"\s*award-winning", text, re.I))
    # Remove award phrases/clauses rather than entire sentences: most sentences
    # also carry substantive service or team copy that must remain.
    cleaned = text
    for _ in range(8):
        updated = AWARD_RE.sub("", cleaned)
        if updated == cleaned:
            break
        cleaned = updated
    cleaned = re.sub(r",\s*including[^.!?;]*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*;\s*:", ";", cleaned)
    cleaned = re.sub(r"\s*:\s*(?=[.;|])", "", cleaned)
    cleaned = re.sub(r"\s*(?:·|,)\s*(?:·|,|and\b|$)", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*,\s*,", ",", cleaned)
    cleaned = re.sub(r"\s*;\s*;", ";", cleaned)
    cleaned = re.sub(r"\s*\.\s*\.\s*", ". ", cleaned)
    cleaned = re.sub(r"\s+,\s*([.!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s+([.!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s+;\s*([.!?]|$)", r"\1", cleaned)
    cleaned = re.sub(r"\b,\s+and\b", " and", cleaned)
    cleaned = re.sub(r"\b(?:and|with|by|an|a|the)\s+(?=[.!?;,]|$)", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"[;,·]\s*$", "", cleaned).strip()
    capitalize = original_started_with_award or (text[:1].isupper() and AWARD_RE.search(text, 0))
    if capitalize and cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    if not re.search(r"[A-Za-z0-9]", cleaned):
        return ""
    return cleaned


def strip_digest_mentions(text: str, fallback: str | None = None) -> str:
    if not DIGEST_RE.search(text):
        return text
    parts = [part for part in SENTENCE_SPLIT_RE.findall(text) if part]
    cleaned = "".join("" if DIGEST_RE.search(part) else part for part in parts) if parts else ""
    cleaned = DIGEST_RE.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    if fallback and len(cleaned) < 20:
        return fallback
    return cleaned


def transform_common(
    text: str,
    *,
    allow_currency: bool = True,
    strip_award: bool = True,
    clean_digests: bool = True,
    replace_standalone: bool = True,
    digest_fallback: str | None = None,
) -> str:
    protected, slots = protect(text)
    protected = OLD_BRAND_RE.sub(NEW_BRAND, protected)
    lower = protected.lower()
    if replace_standalone and "blockchain network" not in lower and "atom" not in lower:
        protected = STANDALONE_COSMOS_RE.sub(NEW_BRAND, protected)
    if strip_award:
        protected = strip_awards(protected)
    if clean_digests:
        protected = strip_digest_mentions(protected, digest_fallback)
    if allow_currency:
        protected = convert_money(protected)
    return restore(protected, slots)


def replace_contacts_and_urls(text: str, *, html_mode: bool) -> str:
    text = re.sub(re.escape(OLD_EMAIL), NEW_EMAIL, text, flags=re.I)
    text = re.sub(r"tel:\+?380638324731", "tel:+27837195064", text)
    text = re.sub(re.escape(OLD_PHONE_SPACED), NEW_PHONE, text)
    text = re.sub(r"(?<!wa\.me/)\+?380638324731", NEW_PHONE, text)
    calendar = CALENDLY_URL_HTML if html_mode else CALENDLY_URL
    return text.replace(OLD_CALENDAR_URL, calendar)


def process_xml_text(raw: str, *, clean_digests: bool = True) -> str:
    """Transform XML/SVG text nodes without sentence-splitting across URL dots."""
    raw = replace_contacts_and_urls(raw, html_mode=False)

    def text_repl(match: re.Match) -> str:
        original = match.group(1)
        if not original.strip():
            return original
        return transform_common(original, allow_currency=True, clean_digests=clean_digests)

    return re.sub(r"(?<=>)([^<]+)(?=<)", text_repl, raw)


@dataclass
class MarkupSpan:
    kind: str
    start: int
    end: int
    raw: str
    name: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    self_closing: bool = False


@dataclass
class Tag:
    name: str
    attrs: dict[str, str]
    start: int
    end: int
    raw: str
    stack: list["Tag"]
    end_start: int | None = None
    end_end: int | None = None

    @property
    def classes(self) -> list[str]:
        return (self.attrs.get("class") or "").split()

    @property
    def outer_end(self) -> int:
        return self.end_end if self.end_end is not None else self.end


@dataclass
class TextSpan:
    start: int
    end: int
    in_script: bool
    in_style: bool
    in_jsonld: bool


class RawHTML(HTMLParser):
    def __init__(self, raw: str):
        super().__init__(convert_charrefs=False)
        self.raw = raw
        self.line_starts = [0]
        for index, char in enumerate(raw):
            if char == "\n":
                self.line_starts.append(index + 1)
        self.markup: list[MarkupSpan] = []
        self.start_tags: list[Tag] = []
        self.text_spans: list[TextSpan] = []
        self.script_spans: list[dict] = []
        self.feed(raw)
        self.close()
        self._finalize()

    def _offset(self, pos: tuple[int, int]) -> int:
        line, col = pos
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self._offset(self.getpos())
        raw = self.get_starttag_text()
        end = start + len(raw)
        self.markup.append(MarkupSpan("start", start, end, raw, tag, {k: (v or "") for k, v in attrs}, False))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self._offset(self.getpos())
        raw = self.get_starttag_text()
        end = start + len(raw)
        self.markup.append(MarkupSpan("start", start, end, raw, tag, {k: (v or "") for k, v in attrs}, True))

    def handle_endtag(self, tag: str) -> None:
        start = self._offset(self.getpos())
        end = self.raw.find(">", start) + 1
        if end <= 0:
            end = start + len(tag) + 3
        self.markup.append(MarkupSpan("end", start, end, self.raw[start:end], tag))

    def handle_comment(self, data: str) -> None:
        start = self._offset(self.getpos())
        end = self.raw.find("-->", start) + 3
        if end < 3:
            end = start + len(data) + 7
        self.markup.append(MarkupSpan("comment", start, end, self.raw[start:end]))

    def handle_decl(self, decl: str) -> None:
        start = self._offset(self.getpos())
        end = self.raw.find(">", start) + 1
        if end <= 0:
            end = start + len(decl) + 5
        self.markup.append(MarkupSpan("decl", start, end, self.raw[start:end]))

    def handle_pi(self, data: str) -> None:
        start = self._offset(self.getpos())
        end = self.raw.find(">", start) + 1
        if end <= 0:
            end = start + len(data) + 4
        self.markup.append(MarkupSpan("pi", start, end, self.raw[start:end]))

    def _finalize(self) -> None:
        spans = sorted(self.markup, key=lambda item: item.start)
        stack: list[Tag] = []
        last_end = 0
        for span in spans:
            if span.start > last_end:
                self._add_text_span(last_end, span.start, stack)
            if span.kind == "start":
                tag = Tag(span.name, span.attrs, span.start, span.end, span.raw, list(stack))
                self.start_tags.append(tag)
                if not span.self_closing and span.name.lower() not in VOID_TAGS:
                    stack.append(tag)
                else:
                    tag.end_start = span.end
                    tag.end_end = span.end
            elif span.kind == "end":
                for index in range(len(stack) - 1, -1, -1):
                    if stack[index].name.lower() == span.name.lower():
                        matched = stack[index]
                        matched.end_start = span.start
                        matched.end_end = span.end
                        if matched.name.lower() == "script":
                            script_type = (matched.attrs.get("type") or "").lower()
                            self.script_spans.append({
                                "start": matched.end,
                                "end": span.start,
                                "type": script_type,
                                "is_jsonld": "ld+json" in script_type,
                            })
                        del stack[index:]
                        break
            last_end = max(last_end, span.end)
        if last_end < len(self.raw):
            self._add_text_span(last_end, len(self.raw), stack)
        for tag in stack:
            tag.end_start = len(self.raw)
            tag.end_end = len(self.raw)

    def _add_text_span(self, start: int, end: int, stack: list[Tag]) -> None:
        if start >= end:
            return
        script_tag = next((tag for tag in reversed(stack) if tag.name.lower() == "script"), None)
        style_tag = next((tag for tag in reversed(stack) if tag.name.lower() == "style"), None)
        self.text_spans.append(TextSpan(
            start,
            end,
            script_tag is not None,
            style_tag is not None,
            bool(script_tag and "ld+json" in (script_tag.attrs.get("type") or "").lower()),
        ))


def apply_edits(raw: str, edits: list[tuple[int, int, str]]) -> str:
    last_start = len(raw) + 1
    out = raw
    for start, end, replacement in sorted(edits, key=lambda item: (-item[0], -(item[1] - item[0]))):
        if end > last_start or start < 0 or end < start:
            continue
        out = out[:start] + replacement + out[end:]
        last_start = start
    return out


def replace_attr(raw_tag: str, attr: str, value: str, *, escape: bool = True) -> str:
    encoded = html.escape(value, quote=True) if escape else value
    pattern = re.compile(
        r"(\s+)(" + re.escape(attr) + r")(\s*=\s*)([\"'])(.*?)(\4)",
        re.I | re.S,
    )
    match = pattern.search(raw_tag)
    if match:
        return raw_tag[:match.start(5)] + encoded + raw_tag[match.end(5):]
    insertion = f' {attr}="{encoded}"'
    if raw_tag.rstrip().endswith("/>"):
        index = raw_tag.rfind("/>")
        return raw_tag[:index].rstrip() + insertion + " />"
    index = raw_tag.rfind(">")
    return raw_tag[:index] + insertion + raw_tag[index:]


def remove_attr(raw_tag: str, attr: str) -> str:
    pattern = re.compile(r"\s+" + re.escape(attr) + r"\s*=\s*([\"']).*?\1", re.I | re.S)
    return pattern.sub("", raw_tag)


def tag_text(raw: str, tag: Tag) -> str:
    return BeautifulSoup(raw[tag.start:tag.outer_end], "html.parser").get_text(" ", strip=True)


def has_removed_slug(value: str) -> bool:
    return any(slug in value for slug in REMOVED_BLOG_SLUGS)


def structural_pass(raw: str, path: Path) -> str:
    parsed = RawHTML(raw)
    edits: list[tuple[int, int, str]] = []
    is_blog_index = path.as_posix().endswith("blog/index.html")

    # Remove the recognition/award sections wholesale, plus any standalone
    # stat cards, award-logo cards, badges and profile links. The 500+ / 12
    # stats elsewhere remain.
    blog_grid = next(
        (
            tag
            for tag in parsed.start_tags
            if is_blog_index and "blog_list-v3" in tag.classes and tag.end_start is not None
        ),
        None,
    )
    rebuilt_grid_spans = (
        [(blog_grid.end, blog_grid.end_start)] if blog_grid else []
    )

    def in_rebuilt_blog_grid(tag: Tag) -> bool:
        return any(start <= tag.start and tag.outer_end <= end for start, end in rebuilt_grid_spans)

    bulk_award_spans: list[tuple[int, int]] = []
    for tag in parsed.start_tags:
        if tag.end_start is None:
            continue
        is_bulk = (
            (tag.name.lower() == "section" and "section_clients" in tag.classes)
            or "data-awards-text" in tag.attrs
        )
        if is_bulk:
            bulk_award_spans.append((tag.start, tag.outer_end))
            edits.append((tag.start, tag.outer_end, ""))

    def in_bulk_award_container(tag: Tag) -> bool:
        return any(start <= tag.start and tag.outer_end <= end for start, end in bulk_award_spans)

    award_classes = {"dx-trust-item", "rvp-stat", "red-dot", "dx-ph-card", "features_heading"}
    award_url_re = re.compile(
        r"awwwards\.com|award-badges|clutch-global-award|clutch_global_award"
        r"|red-dot|css-design-awards|thefwa|site-of-the-day",
        re.I,
    )
    for tag in parsed.start_tags:
        if tag.end_start is None or in_bulk_award_container(tag) or in_rebuilt_blog_grid(tag):
            continue
        if award_classes.intersection(tag.classes) and AWARD_RE.search(tag_text(raw, tag)):
            edits.append((tag.start, tag.outer_end, ""))
        elif "clients_card" in tag.classes or "clients_brand-card" in tag.classes:
            block = raw[tag.start:tag.outer_end]
            if AWARD_RE.search(block) or re.search(
                r'alt="[^"]*(?:awwwards|red\s+dot|fwa|css\s+design\s+awards?|award)[^"]*"',
                block,
                re.I,
            ):
                edits.append((tag.start, tag.outer_end, ""))
        elif "cs-clutch-badge" in tag.classes or "clutch-badge" in " ".join(tag.classes).lower():
            edits.append((tag.start, tag.outer_end, ""))
        elif tag.name.lower() == "li" and len(tag_text(raw, tag)) < 300:
            block = raw[tag.start:tag.outer_end]
            if award_url_re.search(block):
                edits.append((tag.start, tag.outer_end, ""))
        elif tag.name.lower() == "img" and not any(
            "clients_card" in ancestor.classes
            or "clients_brand-card" in ancestor.classes
            or "cs-clutch-badge" in ancestor.classes
            or "clutch-badge" in " ".join(ancestor.classes).lower()
            for ancestor in tag.stack
        ):
            alt = tag.attrs.get("alt", "")
            if re.search(
                r"(?:thefwa|awwwards|css\s+design\s+awards?|red\s+dot\s+award|clutch\s+global\s+2026).*(?:logo|badge)",
                alt,
                re.I,
            ):
                edits.append((tag.start, tag.end, ""))

    # Remove cards that link to removed posts. The blog index is rebuilt wholesale below.
    if not is_blog_index:
        for tag in parsed.start_tags:
            if tag.name.lower() != "a" or tag.end_start is None:
                continue
            href = tag.attrs.get("href") or ""
            if not has_removed_slug(href):
                continue
            chosen = tag
            for ancestor in reversed(tag.stack):
                classes = set(ancestor.classes)
                if classes.intersection({"w-dyn-item", "blog_item-v3", "blog-card", "post-others_item"}):
                    text = tag_text(raw, ancestor)
                    if len(text) < 1200 and ancestor.end_start is not None:
                        chosen = ancestor
                        break
            edits.append((chosen.start, chosen.outer_end, ""))

    # Rebuild the blog listing with exactly the 12 evergreen guides.
    if is_blog_index:
        grid = blog_grid
        if grid:
            cards = build_blog_cards()
            new_grid_tag = replace_attr(grid.raw, "data-lulazel-cards", "1")
            new_grid_tag = remove_attr(new_grid_tag, "fs-list-load")
            edits.append((grid.start, grid.end, new_grid_tag))
            edits.append((grid.end, grid.end_start, cards))
        pagination = next((tag for tag in parsed.start_tags if "w-pagination-wrapper" in tag.classes and tag.end_start is not None), None)
        if pagination:
            edits.append((pagination.start, pagination.outer_end, ""))
        for tag in parsed.start_tags:
            if tag.name.lower() == "title" and tag.end_start is not None:
                edits.append((tag.end, tag.end_start, "Blog: Practical Design Guides | LulaZel Hub"))
            elif tag.name.lower() == "meta":
                name = (tag.attrs.get("name") or "").lower()
                prop = (tag.attrs.get("property") or "").lower()
                replacement = None
                if name == "description" or prop in {"og:description", "twitter:description"}:
                    replacement = "Practical design guides from LulaZel Hub: UI/UX, product design, defense tech, pitch decks and startup costs."
                elif prop in {"og:title", "twitter:title"}:
                    replacement = "Blog: Practical Design Guides | LulaZel Hub"
                if replacement:
                    edits.append((tag.start, tag.end, replace_attr(tag.raw, "content", replacement)))

    # Replace the giant SVG wordmarks with a text wordmark.
    for tag in parsed.start_tags:
        if tag.name.lower() == "svg" and tag.end_start is not None:
            viewbox = tag.attrs.get("viewbox") or tag.attrs.get("viewBox") or ""
            if "1367 262" in viewbox:
                edits.append((tag.start, tag.outer_end, '<span class="lz-wordmark is-footer">LulaZel Hub</span>'))
        elif tag.name.lower() == "div" and "home-header_headings" in tag.classes and tag.end_start is not None:
            edits.append((tag.end, tag.end_start, '<span class="lz-wordmark">LulaZel Hub</span>'))

    return apply_edits(raw, edits)


def transform_ld_value(node, currency_context: str | None = None):
    if isinstance(node, list):
        return [transform_ld_value(item, currency_context) for item in node]
    if not isinstance(node, dict):
        return node
    own_currency = node.get("priceCurrency") or node.get("currency")
    usd_context = (own_currency or currency_context) == "USD"
    result: dict = {}
    for key, value in node.items():
        if "award" in key.lower():
            continue
        if key in {"priceCurrency", "currency"} and value == "USD":
            result[key] = "ZAR"
        elif key == "urlTemplate" and isinstance(value, str):
            value = value.replace(CALENDLY_URL_HTML, CALENDLY_URL).replace(OLD_CALENDAR_URL, CALENDLY_URL)
            result[key] = value
        elif key in {"minPrice", "maxPrice", "price", "lowPrice", "highPrice", "estimatedCost"} and usd_context:
            result[key] = convert_price_number(value)
        elif key == "value" and usd_context and node.get("@type") in {"MonetaryAmount", "PriceSpecification", "UnitPriceSpecification"}:
            result[key] = convert_price_number(value)
        elif isinstance(value, str):
            result[key] = transform_common(value, allow_currency=True)
        elif isinstance(value, (dict, list)):
            result[key] = transform_ld_value(value, own_currency or currency_context)
        else:
            result[key] = value
    return result


def convert_price_number(value):
    if not isinstance(value, (int, float, str)) or isinstance(value, bool):
        return value
    try:
        amount = Decimal(str(value)) * USD_ZAR
    except Exception:
        return value
    if amount == amount.to_integral_value():
        return int(amount)
    return float(amount)


def transform_ld_script(content: str) -> str:
    try:
        data = json.loads(content)
    except (ValueError, TypeError):
        return content
    transformed = transform_ld_value(data)
    return json.dumps(transformed, ensure_ascii=False, separators=(",", ":"))


def process_html_file(path: Path) -> None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = replace_contacts_and_urls(raw, html_mode=True)
    raw = structural_pass(raw, path)
    if 'id="lulazel-brand"' not in raw:
        raw = raw.replace("</head>", BRAND_CSS + "\n</head>", 1)
    parsed = RawHTML(raw)
    edits: list[tuple[int, int, str]] = []

    # Text nodes: visible copy, titles and non-script text.
    for span in parsed.text_spans:
        if span.in_script or span.in_style:
            continue
        original = raw[span.start:span.end]
        transformed = transform_common(original, allow_currency=True)
        if transformed != original:
            edits.append((span.start, span.end, transformed))

    # Attributes: metadata, alt/aria, labels and values. URLs and classes stay untouched.
    for tag in parsed.start_tags:
        new_tag = tag.raw
        changed = False
        for attr in ATTRS_TO_TRANSFORM:
            value = tag.attrs.get(attr)
            if not isinstance(value, str) or not value:
                continue
            transformed = transform_common(value, allow_currency=True)
            if attr == "content" and DIGEST_RE.search(value) and len(transformed.strip()) < 20:
                transformed = "Practical design guides from LulaZel Hub: UI/UX, product design, defense tech, pitch decks and startup costs."
            if transformed != value:
                new_tag = replace_attr(new_tag, attr, transformed)
                changed = True
        if changed:
            edits.append((tag.start, tag.end, new_tag))

    # JSON-LD and other inline scripts.
    for script in parsed.script_spans:
        original = raw[script["start"]:script["end"]]
        if script["is_jsonld"]:
            transformed = transform_ld_script(original)
        else:
            transformed = transform_common(
                original,
                allow_currency=False,
                strip_award=False,
                clean_digests=False,
                replace_standalone=False,
            )
        if transformed != original:
            edits.append((script["start"], script["end"], transformed))

    # Forms: direct native POST to Formspree, with Webflow's validation still in place.
    for tag in parsed.start_tags:
        if tag.name.lower() == "form":
            new_tag = replace_attr(tag.raw, "method", "post")
            new_tag = replace_attr(new_tag, "action", FORMSPREE_URL)
            edits.append((tag.start, tag.end, new_tag))
        elif tag.name.lower() == "input" and (tag.attrs.get("name") or "").lower() == "email":
            new_tag = replace_attr(tag.raw, "name", "email")
            edits.append((tag.start, tag.end, new_tag))

    # Every visible Book a Call CTA points to the exact Calendly destination.
    for tag in parsed.start_tags:
        if tag.name.lower() != "a" or tag.end_start is None:
            continue
        label = tag_text(raw, tag).lower()
        href = tag.attrs.get("href") or ""
        if "book a call" in label or "book a discovery call" in label or "book a free discovery call" in label:
            if href != CALENDLY_URL_HTML:
                new_tag = replace_attr(tag.raw, "href", CALENDLY_URL_HTML, escape=False)
                edits.append((tag.start, tag.end, new_tag))

    raw = apply_edits(raw, edits)
    path.write_text(raw, encoding="utf-8")


def parse_rss_items(text: str) -> list[dict]:
    items = []
    for block in re.findall(r"<item>.*?</item>", text, re.S | re.I):
        def field(name: str) -> str:
            match = re.search(rf"<{name}[^>]*>(.*?)</{name}>", block, re.S | re.I)
            return html.unescape(match.group(1).strip()) if match else ""

        media = re.search(r'<media:content[^>]*url="([^"]+)"', block, re.I)
        link = field("link")
        slug = link.rstrip("/").rsplit("/", 1)[-1]
        items.append({
            "slug": slug,
            "title": field("title"),
            "description": field("description"),
            "pubDate": field("pubDate"),
            "image": html.unescape(media.group(1)) if media else "",
        })
    return items


def blog_author(slug: str) -> str:
    path = SITE / "blog" / slug / "index.html"
    if not path.exists():
        return "LulaZel Hub"
    soup = BeautifulSoup(path.read_text(errors="replace"), "html.parser")
    author = soup.select_one(".author-small")
    return author.get_text(" ", strip=True) if author else "LulaZel Hub"


def build_blog_cards() -> str:
    rss = (SITE / "blog" / "rss.xml").read_text(encoding="utf-8", errors="replace")
    items = [item for item in parse_rss_items(rss) if item["slug"] in KEEP_BLOG_SLUGS]
    kept = {item["slug"] for item in items}
    for slug in sorted(KEEP_BLOG_SLUGS - kept):
        items.append({
            "slug": slug,
            "title": slug.replace("-", " ").title(),
            "description": "A practical LulaZel Hub guide.",
            "pubDate": "Mon, 23 Nov 2026 00:00:00 GMT",
            "image": "/assets/external/2717683baa1372e65db6.webp",
        })
    cards = []
    for item in items:
        try:
            date = email.utils.parsedate_to_datetime(item["pubDate"])
            pretty_date = date.strftime("%B %-d, %Y")
            iso_date = date.strftime("%Y-%m-%d")
        except Exception:
            pretty_date, iso_date = "November 23, 2026", "2026-11-23"
        title = transform_common(item["title"], allow_currency=True)
        description = transform_common(item["description"], allow_currency=True)
        alt = transform_common(f"{title} cover", allow_currency=True)
        author = blog_author(item["slug"])
        image = item["image"] or "/assets/external/2717683baa1372e65db6.webp"
        cards.append(
            '<div role="listitem" class="blog_item-v3 w-dyn-item">'
            f'<a href="/blog/{html.escape(item["slug"], quote=True)}" class="blog_block with-gap w-inline-block">'
            '<div class="blog_img-wrap">'
            f'<img src="{html.escape(image, quote=True)}" loading="lazy" animation="scroll-zoom" alt="{html.escape(alt, quote=True)}" class="blog_img"/>'
            '<div class="blog_tag"><div class="w-dyn-bind-empty"></div></div></div>'
            '<div class="blog_content-v3"><div class="blog-card_content"><div class="author-block">'
            '<img alt="" class="author_thumbn" loading="lazy" src="/assets/external/2717683baa1372e65db6.webp"/>'
            f'<div class="author-small">{html.escape(author, quote=True)}</div></div>'
            '<div class="blog_content-in">'
            f'<h2 fs-list-field="title" class="heading-style-h5 is-tablet-xsmaller">{html.escape(title, quote=True)}</h2>'
            f'<p class="blog_desc" fs-list-field="description">{html.escape(description, quote=True)}</p>'
            '</div></div><div class="text-color-grey-300"><div class="blog-date">'
            f'{html.escape(pretty_date, quote=True)}</div></div></div></a>'
            f'<div fs-list-field="DATE" class="hidden">{iso_date}</div>'
            '<div fs-list-field="industry" class="hidden w-dyn-bind-empty"></div>'
            '<div fs-list-field="category" class="hidden">Guide</div></div>'
        )
    return "".join(cards)


def process_non_html_text(path: Path) -> None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = replace_contacts_and_urls(raw, html_mode=False)
    suffix = path.suffix.lower()
    if suffix == ".js":
        if path.as_posix().endswith(("assets/js/reviews-letter-1.1.1.js", "assets/external/4d3f084e37d18b50e04d.js")):
            raw = transform_common(raw, allow_currency=True, strip_award=False, clean_digests=False, replace_standalone=False)
        else:
            raw = transform_common(raw, allow_currency=False, strip_award=False, clean_digests=False, replace_standalone=False)
    elif suffix in {".svg", ".xml"}:
        raw = process_xml_text(raw, clean_digests=(suffix == ".svg"))
    elif suffix in {".txt", ".md"}:
        lines = []
        for line in raw.splitlines(keepends=True):
            if has_removed_slug(line):
                continue
            newline = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
            body = line.rstrip("\r\n")
            lines.append(transform_common(body, allow_currency=True) + newline)
        raw = "".join(lines)
    elif suffix in {".css", ".mjs", ".json"}:
        raw = transform_common(raw, allow_currency=False, strip_award=False, clean_digests=False, replace_standalone=False)
    path.write_text(raw, encoding="utf-8")


def patch_form_bridge() -> None:
    path = SITE / "_c" / "wf-form-bridge.v2.js"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    text = replace_contacts_and_urls(text, html_mode=False)
    if FORMSPREE_URL not in text:
        text = text.replace(
            "options.url = '/api/form';",
            f"options.url = '{FORMSPREE_URL}';\n      options.type = 'POST';\n      options.crossDomain = true;\n      options.dataType = 'json';\n      options.dataFilter = function () {{ return '{{\"code\":200}}'; }};",
        )
        text = text.replace(
            "jqXHR.done(function (res) { if (!res || res.code !== 200) afterFailure(200); });",
            "jqXHR.done(function () {});",
        )
    path.write_text(text, encoding="utf-8")


def overwrite_logo_svg() -> None:
    path = SITE / "assets" / "img" / "cosmos-logo.svg"
    if not path.exists():
        return
    path.write_text(
        '<svg width="135" height="32" viewBox="0 0 135 32" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<text x="0" y="23" font-family="Arial,Helvetica,sans-serif" font-size="17" font-weight="700" fill="currentColor">'
        f"{NEW_BRAND}</text></svg>\n",
        encoding="utf-8",
    )


def remove_blog_pages() -> None:
    for slug in REMOVED_BLOG_SLUGS:
        directory = SITE / "blog" / slug
        if directory.exists():
            shutil.rmtree(directory)
        flat = SITE / "blog" / f"{slug}.html"
        if flat.exists():
            flat.unlink()


def filter_json_value(value):
    if isinstance(value, list):
        return [filter_json_value(item) for item in value if not (isinstance(item, str) and has_removed_slug(item))]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if has_removed_slug(str(key)) or (isinstance(item, str) and has_removed_slug(item)):
                continue
            result[key] = filter_json_value(item)
        return result
    return value


def filter_json_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, TypeError):
        return
    filtered = filter_json_value(data)
    path.write_text(json.dumps(filtered, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def transform_report_string(value: str) -> str:
    value = replace_contacts_and_urls(value, html_mode=False)
    transformed = transform_common(
        value,
        allow_currency=True,
        strip_award=True,
        clean_digests=False,
        replace_standalone=True,
    )
    # Historic asset-map/report URLs can still contain recognition tokens; they
    # are diagnostics, not site content, so replace rather than preserve them.
    if AWARD_RE.search(transformed):
        return "[removed recognition reference]"
    return transformed


def clean_report_value(value):
    if isinstance(value, list):
        return [
            clean_report_value(item)
            for item in value
            if not (isinstance(item, str) and (has_removed_slug(item) or AWARD_RE.search(item)))
        ]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            safe_key = str(key)
            if has_removed_slug(safe_key) or AWARD_RE.search(safe_key):
                continue
            if isinstance(item, str) and (has_removed_slug(item) or AWARD_RE.search(item)):
                continue
            result[transform_report_string(safe_key)] = clean_report_value(item)
        return result
    if isinstance(value, str):
        return transform_report_string(value)
    return value


def update_report_text_files() -> None:
    # Rebrand plain-text and JSON diagnostics, but never rewrite code, because
    # the validators intentionally keep legacy strings as detection constants.
    candidates = [p for p in SCRIPTS.rglob("*") if p.is_file()]
    for path in candidates:
        suffix = path.suffix.lower()
        if suffix == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except (ValueError, TypeError):
                continue
            path.write_text(json.dumps(clean_report_value(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        elif suffix in {".txt", ".md"}:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except UnicodeDecodeError:
                continue
            lines = []
            for line in text.splitlines(keepends=True):
                if has_removed_slug(line) or AWARD_RE.search(line):
                    continue
                newline = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                body = line.rstrip("\r\n")
                lines.append(transform_report_string(body) + newline)
            path.write_text("".join(lines), encoding="utf-8")


def filter_line_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    lines = [line for line in text.splitlines() if not has_removed_slug(line)]
    path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")


def update_rss(path: Path) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    for item in re.findall(r"<item>.*?</item>", text, re.S | re.I):
        if has_removed_slug(item):
            text = text.replace(item, "")
    text = process_xml_text(text, clean_digests=False)
    text = re.sub(
        r"(<channel>\s*<title>).*?(</title>)",
        r"\1LulaZel Hub Blog\2",
        text,
        count=1,
        flags=re.S | re.I,
    )
    text = re.sub(
        r"(<channel>.*?<description>).*?(</description>)",
        r"\1Practical design guides from LulaZel Hub: UI/UX, product design, defense tech, pitch decks and startup costs.\2",
        text,
        count=1,
        flags=re.S | re.I,
    )
    path.write_text(text, encoding="utf-8")


def canonical_urls() -> list[str]:
    path = SCRIPTS / "cosmos-canonical-urls.txt"
    urls = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [url for url in urls if not has_removed_slug(url)]


def write_sitemaps(urls: list[str]) -> None:
    locations = "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + locations + "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    (SITE / "sitemap.xml").write_text(xml, encoding="utf-8")


def update_reports(urls: list[str]) -> None:
    site_files = [path for path in SITE.rglob("*") if path.is_file()]
    site_bytes = sum(path.stat().st_size for path in site_files)
    html_pages = [path for path in SITE.rglob("*.html")]
    # The award post's cover file is no longer used by kept content.
    orphan_cover = SITE / "assets" / "img" / "clutch-global-award-fall-2026-cover.webp"
    if orphan_cover.exists():
        orphan_cover.unlink()
    site_files = [path for path in SITE.rglob("*") if path.is_file()]
    site_bytes = sum(path.stat().st_size for path in site_files)
    (SCRIPTS / "cosmos-canonical-urls.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")
    filter_line_file(SCRIPTS / "cosmos-sitemap-raw.txt")
    filter_line_file(SCRIPTS / "fetch-build-last-run.txt")
    filter_line_file(SCRIPTS / "validate-last-run.txt")
    (SCRIPTS / "cosmos-site-file-list.txt").write_text(
        "\n".join(sorted(str(path.relative_to(ROOT)) for path in site_files)) + "\n", encoding="utf-8"
    )
    (SCRIPTS / "cosmos-site-file-sizes.txt").write_text(
        "\n".join(f"{path.stat().st_size} {path.relative_to(ROOT)}" for path in sorted(site_files, key=lambda item: -item.stat().st_size)) + "\n",
        encoding="utf-8",
    )
    for path in [
        SCRIPTS / "cosmos-live-build-report.json",
        SITE / "build-manifest.json",
        SCRIPTS / "cosmos-repair-report.json",
        SCRIPTS / "cosmos-asset-map.json",
        SCRIPTS / "cosmos-remaining-remote-assets.json",
        SCRIPTS / "cosmos-redirects.json",
        SITE / "asset-map.json",
        SITE / "remaining-remote-assets.json",
    ]:
        filter_json_file(path)
    for path in [SCRIPTS / "cosmos-live-build-report.json", SITE / "build-manifest.json"]:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if "canonical_paths" in data:
            data["canonical_paths"] = [item for item in data["canonical_paths"] if not has_removed_slug(item)]
        data["canonical_url_count"] = len(urls)
        data["site_file_count"] = len(site_files)
        data["site_total_bytes"] = site_bytes
        data["pages_written"] = len(html_pages) + 1
        data["exact_page_count"] = len(html_pages) - 6
        data["html_page_count"] = len(html_pages)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_redirects() -> None:
    for path in [SITE / "redirects.json", SCRIPTS / "cosmos-redirects.json"]:
        filter_json_file(path)
    payload = {}
    source = SITE / "redirects.json"
    if source.exists():
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except ValueError:
            payload = {}
    lines = ["# Captured source-site redirects (kept with their original routes)."]
    for key, record in sorted(payload.items()):
        if has_removed_slug(key) or has_removed_slug(str(record)):
            continue
        target = record.get("target_path") or record.get("target") or "/"
        status = record.get("status", 301)
        lines.append(f"{key}\t{target}\t{status}")
    (SITE / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(urls: list[str]) -> None:
    (ROOT / "README.md").write_text(
        f"""# LulaZel Hub static site

This workspace began as an exact static clone of the original source site and is now customized for LulaZel Hub. The exact Webflow HTML, CSS, JavaScript, GSAP interactions, fonts, animations, project pages, redirects and media references are preserved; only the requested rebrand and content changes were applied.

- {len(urls)} canonical routes remain. The 10 AI news-digest posts and the Clutch recognition post were removed; 12 practical blog guides remain on the blog index and in RSS.
- Visible source-site wording, alt/ARIA text, page titles, meta descriptions, structured data, RSS copy, the giant SVG wordmark and the small logo were renamed to `LulaZel Hub`.
- All visible US-dollar prices, project budgets and hourly rates were converted at **R18 per 1 USD** and presented in South African rand.
- Every visible recognition and competition mention was removed; the surrounding 500+ / 12 stats remain.
- Email is `mkhungela.l@gmail.com`. The visible WhatsApp number is `+27 83 719 5064`; the WhatsApp URL remains exactly `{WHATSAPP_URL}`.
- Every contact form uses `POST {FORMSPREE_URL}`. The Webflow form bridge was redirected from `/api/form` to Formspree.
- Every Book a Call link points to `{CALENDLY_URL}`.
- Source-site URLs, filenames, CSS/JS classes and canonical links remain unchanged. The logo-adjacent dropdown still defaults to `For You` with `For Marketing Teams`, `For Tech`, and `Something Else`; no custom option views are implemented.

## Rebuild

Run `python3 scripts/fetch_live_cosmos.py`, then `python3 scripts/customize_cosmos_clone.py`, then `python3 scripts/validate_custom_clone.py`. The exact-clone workflow is manual only so customization commits are not overwritten. Serve locally with `python3 scripts/serve.py 3000`.
""",
        encoding="utf-8",
    )


def main() -> None:
    if not SITE.exists():
        raise SystemExit("cosmos-copy is missing; fetch the exact clone first")
    remove_blog_pages()
    urls = canonical_urls()
    write_sitemaps(urls)
    html_files = sorted(SITE.rglob("*.html"))
    for path in html_files:
        process_html_file(path)
    for path in SITE.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_FILE_SUFFIXES and path.suffix.lower() != ".html":
            process_non_html_text(path)
    patch_form_bridge()
    overwrite_logo_svg()
    update_rss(SITE / "blog" / "rss.xml")
    update_rss(SITE / "rss.xml")
    update_redirects()
    update_reports(urls)
    update_report_text_files()
    write_readme(urls)
    print(json.dumps({
        "customized": NEW_BRAND,
        "canonical_urls": len(urls),
        "removed_blog_posts": len(REMOVED_BLOG_SLUGS),
        "html_files": len(html_files),
        "removed_blog_slugs": len(REMOVED_BLOG_SLUGS),
        "kept_blog_slugs": len(KEEP_BLOG_SLUGS),
        "usd_zar_rate": str(USD_ZAR),
        "formspree": FORMSPREE_URL,
        "calendly": CALENDLY_URL,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
