"""Anthropic Claude backend.

Requires `anthropic` SDK and ANTHROPIC_API_KEY env var.
Install: `pip install anthropic`
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

from summary_doctor.prompts import DECOMPOSE_PROMPT, CLASSIFY_PROMPT


@dataclass
class AnthropicBackend:
    model_id: str = "claude-haiku-4-5-20251001"

    def __post_init__(self) -> None:
        try:
            from anthropic import Anthropic  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "anthropic SDK not installed. Run: pip install anthropic"
            ) from e
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Export your key or use --mock for offline demo."
            )

    def _client(self):
        from anthropic import Anthropic
        return Anthropic()

    def decompose(self, summary_text: str, *, lang: str) -> list[str]:
        client = self._client()
        prompt = DECOMPOSE_PROMPT.format(lang=lang, summary=summary_text)
        msg = client.messages.create(
            model=self.model_id,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in msg.content if hasattr(block, "text"))
        return _parse_json_list(text)

    def classify(self, claims: list[str], source_text: str, *, lang: str) -> list[dict]:
        client = self._client()
        prompt = CLASSIFY_PROMPT.format(
            lang=lang,
            claims=json.dumps(claims, ensure_ascii=False),
            source=source_text,
        )
        msg = client.messages.create(
            model=self.model_id,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in msg.content if hasattr(block, "text"))
        return _parse_json_list(text)


def _parse_json_list(text: str) -> list:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise RuntimeError(f"backend returned non-JSON output: {text[:200]}")
    return json.loads(text[start : end + 1])
