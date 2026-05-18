from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from summary_doctor.backends.base import Backend
from summary_doctor.extract import to_plain_text


Label = Literal["exact", "softened", "reversed", "fabricated"]


@dataclass
class ClaimAudit:
    claim: str
    matched_paragraph: str | None
    label: Label
    confidence: int
    rationale: str

    def as_dict(self) -> dict:
        return {
            "claim": self.claim,
            "matched_paragraph": self.matched_paragraph,
            "label": self.label,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


@dataclass
class Report:
    audits: list[ClaimAudit]
    summary_chars: int
    source_chars: int
    model: str
    lang: str
    notes: list[str] = field(default_factory=list)

    def divergence_score(self) -> int:
        if not self.audits:
            return 0
        bad = sum(1 for a in self.audits if a.label in ("reversed", "fabricated"))
        soft = sum(1 for a in self.audits if a.label == "softened")
        return round(100 * (bad + 0.5 * soft) / len(self.audits))

    def headline(self) -> str:
        n = len(self.audits)
        rev = sum(1 for a in self.audits if a.label == "reversed")
        fab = sum(1 for a in self.audits if a.label == "fabricated")
        return (
            f"{n} claims · divergence {self.divergence_score()}% · "
            f"reversed {rev} · fabricated {fab}"
        )

    @property
    def markdown(self) -> str:
        lines: list[str] = []
        lines.append("# Summary Audit Report")
        lines.append("")
        lines.append(f"- Model: `{self.model}`")
        lines.append(f"- Language: `{self.lang}`")
        lines.append(f"- Claims analyzed: **{len(self.audits)}**")
        lines.append(f"- Divergence score: **{self.divergence_score()}%**")
        lines.append("")
        lines.append("> ⚠️ This is a citation map, not a verdict. ")
        lines.append("> `fabricated` may be false-positive if source retrieval was partial. ")
        lines.append("> The reader makes the final call.")
        lines.append("")
        if self.notes:
            lines.append("## Notes")
            for n in self.notes:
                lines.append(f"- {n}")
            lines.append("")
        counts = {label: 0 for label in ("exact", "softened", "reversed", "fabricated")}
        for a in self.audits:
            counts[a.label] += 1
        lines.append("## Label distribution")
        lines.append("")
        lines.append("| Label | Count |")
        lines.append("|-------|------:|")
        for label in ("exact", "softened", "reversed", "fabricated"):
            lines.append(f"| `{label}` | {counts[label]} |")
        lines.append("")
        lines.append("## Per-claim audit")
        lines.append("")
        for i, a in enumerate(self.audits, 1):
            lines.append(f"### Claim {i} — `{a.label}` (confidence {a.confidence})")
            lines.append("")
            lines.append("**Summary claim:**")
            lines.append("")
            lines.append(f"> {a.claim}")
            lines.append("")
            lines.append("**Matched source paragraph:**")
            lines.append("")
            if a.matched_paragraph:
                lines.append(f"> {a.matched_paragraph}")
            else:
                lines.append("> _(no matching paragraph found in source)_")
            lines.append("")
            lines.append(f"**Rationale:** {a.rationale}")
            lines.append("")
        return "\n".join(lines)

    @property
    def json_str(self) -> str:
        return json.dumps(
            {
                "model": self.model,
                "lang": self.lang,
                "summary_chars": self.summary_chars,
                "source_chars": self.source_chars,
                "divergence_score": self.divergence_score(),
                "headline": self.headline(),
                "audits": [a.as_dict() for a in self.audits],
                "notes": self.notes,
            },
            ensure_ascii=False,
            indent=2,
        )


class Pipeline:
    """5-stage state machine: input → extract → decompose → map+classify → report."""

    def __init__(self, backend: Backend, lang: str = "auto"):
        self.backend = backend
        self.lang = lang

    def run(self, summary_ref: str, source_ref: str) -> Report:
        summary_raw = self._fetch(summary_ref)
        source_raw = self._fetch(source_ref)

        summary_text = to_plain_text(summary_raw)
        source_text = to_plain_text(source_raw)

        notes: list[str] = []
        if len(source_text) > 200_000:
            notes.append(
                f"Source is large ({len(source_text)} chars); v0.1 sends head 200k. "
                "Chunked handling lands in v0.2."
            )
            source_text = source_text[:200_000]

        claims = self.backend.decompose(summary_text, lang=self.lang)
        audits_raw = self.backend.classify(claims, source_text, lang=self.lang)

        audits = [
            ClaimAudit(
                claim=a["claim"],
                matched_paragraph=a.get("matched_paragraph"),
                label=a["label"],
                confidence=int(a.get("confidence", 0)),
                rationale=a.get("rationale", ""),
            )
            for a in audits_raw
        ]

        return Report(
            audits=audits,
            summary_chars=len(summary_text),
            source_chars=len(source_text),
            model=self.backend.model_id,
            lang=self.lang,
            notes=notes,
        )

    @staticmethod
    def _fetch(ref: str) -> str:
        if ref == "-":
            import sys
            return sys.stdin.read()
        parsed = urlparse(ref)
        if parsed.scheme in ("http", "https"):
            req = Request(
                ref,
                headers={
                    "User-Agent": "summary-doctor/0.1 (+https://github.com/)",
                },
            )
            try:
                with urlopen(req, timeout=15) as resp:
                    return resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
            except Exception as e:
                raise RuntimeError(f"source-unfetchable: {ref} ({e})") from e
        p = Path(ref)
        if not p.exists():
            raise FileNotFoundError(ref)
        return p.read_text(encoding="utf-8")
