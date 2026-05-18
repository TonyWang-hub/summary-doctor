from __future__ import annotations

from typing import Protocol


class Backend(Protocol):
    model_id: str

    def decompose(self, summary_text: str, *, lang: str) -> list[str]:
        """Split summary into atomic assertive claims."""
        ...

    def classify(
        self,
        claims: list[str],
        source_text: str,
        *,
        lang: str,
    ) -> list[dict]:
        """For each claim, return dict with keys:
        claim, matched_paragraph, label, confidence, rationale.
        """
        ...
