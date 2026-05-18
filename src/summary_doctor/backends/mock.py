"""Canned backend for offline pipeline validation and demos.

Heuristic, not magic: splits the summary into sentences and pattern-matches
keywords to decide a label. Good enough to demo the report format without an
API key. Real audits use the Anthropic backend.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


_NEGATION_TOKENS = {
    "zh": ["不", "没", "无", "未", "并非", "反而", "相反", "并不"],
    "en": [" not ", " no ", " never ", " without ", " neither ", " nor "],
}


@dataclass
class MockBackend:
    model_id: str = "mock"

    def decompose(self, summary_text: str, *, lang: str) -> list[str]:
        text = summary_text.strip()
        sentences = re.split(r"(?<=[。！？!?\.])\s+|\n+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 4]

    def classify(self, claims: list[str], source_text: str, *, lang: str) -> list[dict]:
        results: list[dict] = []
        source_lower = source_text.lower()
        paras = [p.strip() for p in re.split(r"\n{2,}", source_text) if p.strip()]
        for c in claims:
            label, conf, matched, rationale = self._classify_one(c, source_lower, paras)
            results.append(
                {
                    "claim": c,
                    "matched_paragraph": matched,
                    "label": label,
                    "confidence": conf,
                    "rationale": rationale,
                }
            )
        return results

    def _classify_one(
        self,
        claim: str,
        source_lower: str,
        paras: list[str],
    ) -> tuple[str, int, str | None, str]:
        keywords = [w for w in re.findall(r"[A-Za-z\u4e00-\u9fff]{2,}", claim) if len(w) >= 2]
        keywords = keywords[:8]
        if not keywords:
            return ("fabricated", 30, None, "No content tokens to anchor against source.")

        best_para = None
        best_overlap = 0
        for p in paras:
            p_lower = p.lower()
            overlap = sum(1 for k in keywords if k.lower() in p_lower)
            if overlap > best_overlap:
                best_overlap = overlap
                best_para = p

        ratio = best_overlap / max(1, len(keywords))
        if ratio < 0.25 or best_para is None:
            return ("fabricated", 60, None, f"Only {best_overlap}/{len(keywords)} keywords match any source paragraph.")

        claim_negated = self._has_negation(claim)
        source_negated = self._has_negation(best_para)
        polarity_mismatch = claim_negated != source_negated
        if polarity_mismatch and ratio >= 0.5:
            return (
                "reversed",
                70,
                best_para[:400],
                f"Polarity mismatch with strong keyword overlap ({best_overlap}/{len(keywords)}).",
            )
        if polarity_mismatch:
            return (
                "softened",
                45,
                best_para[:400],
                f"Possible polarity mismatch but weak keyword overlap ({best_overlap}/{len(keywords)}); mock heuristic not confident.",
            )
        if ratio >= 0.6:
            return ("exact", 80, best_para[:400], f"{best_overlap}/{len(keywords)} keywords align with source paragraph.")
        return (
            "softened",
            55,
            best_para[:400],
            f"Partial keyword overlap ({best_overlap}/{len(keywords)}); claim may lose qualifiers.",
        )

    @staticmethod
    def _has_negation(text: str) -> bool:
        t = text
        for tok in _NEGATION_TOKENS["zh"]:
            if tok in t:
                return True
        t_lower = " " + t.lower() + " "
        for tok in _NEGATION_TOKENS["en"]:
            if tok in t_lower:
                return True
        return False
