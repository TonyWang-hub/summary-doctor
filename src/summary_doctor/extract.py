"""Minimal HTML → plain text fallback.

For real-world pages we recommend running through `defuddle` or `trafilatura`
first; this module exists so the CLI works with zero extra deps for the v0.1
demo loop.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser


_DROP_TAGS = {"script", "style", "noscript", "header", "footer", "nav", "aside"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _DROP_TAGS:
            self._skip_depth += 1
        elif tag in {"p", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div", "section"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _DROP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div", "section"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self.parts.append(data)


def to_plain_text(raw: str) -> str:
    looks_html = "<html" in raw[:4096].lower() or re.search(r"<(p|div|article|body)\b", raw[:4096], re.I)
    if not looks_html:
        return _normalize(raw)
    extractor = _TextExtractor()
    try:
        extractor.feed(raw)
    except Exception:
        return _normalize(raw)
    return _normalize("".join(extractor.parts))


def _normalize(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
