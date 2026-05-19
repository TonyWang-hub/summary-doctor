"""Claude CLI backend — reuse a Claude Code subscription via the `claude` CLI.

Why this backend
----------------

The `anthropic` backend requires an `ANTHROPIC_API_KEY` and is billed per
token. Users who already have a Claude Code subscription can instead drive
the local `claude` binary in non-interactive (`-p` / `--print`) mode, which
reuses the subscription's auth and quota. From the end user's perspective
this is "$0 marginal audit cost".

Differences vs the SDK backend
------------------------------

The `claude` CLI does NOT expose the SDK's `tool_use` structured-output
mechanism. We therefore cannot force the model to emit a JSON object that
matches our schema. Instead we:

1. Prepend a strict system prompt insisting on JSON-only output and pass it
   via `--append-system-prompt`.
2. Send the actual user prompt on stdin (so we don't have to worry about
   shell-escaping large summaries / source texts).
3. Request `--output-format json` so the CLI wraps the model's reply in a
   small envelope from which we extract a `result` string.
4. Parse the `result` first with `json.loads` (strict). If that fails we
   fall back to a lenient extractor that pulls the first balanced
   `[...]` (decompose) or `{...}` (classify) substring and re-parses.
5. Validate against the same shape contract used by the SDK backend so
   downstream pipeline code is identical.

All failure modes — missing CLI, timeout, non-zero exit, no JSON-shaped
content, wrong shape — raise `RuntimeError` with a single-line message
that names the failing stage (`decompose` / `classify`).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

from summary_doctor.prompts import (
    CLASSIFY_PROMPT,
    DECOMPOSE_PROMPT,
    LABELS,
)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

# `claude --model` accepts aliases like `haiku` / `sonnet` / `opus` as well
# as full model IDs. We pass whatever the user supplied through unchanged
# so they can pin a specific dated build if they want.
DEFAULT_MODEL_ALIAS = "haiku"

# Per-call timeout. Decompose/classify on Haiku for short English text
# typically returns in <15s, but Chinese sources, longer pieces, or the
# Opus model can push the round-trip past 60s. 120s is a conservative
# default; callers can tighten it via the dataclass field.
DEFAULT_TIMEOUT_SECONDS = 120

# System prompt appended on every call. The base prompts in `prompts.py`
# already say "return JSON only", but the CLI path needs an extra belt
# because there is no tool_use to enforce shape.
_JSON_ONLY_SYSTEM = (
    "You are operating in a non-interactive JSON pipeline. Return ONLY the "
    "JSON value requested by the user prompt — no prose, no markdown, no "
    "code fences, no leading or trailing commentary. The first character "
    "of your response MUST be '[' or '{' and the last character MUST be "
    "']' or '}'. Do not call any tools. Do not edit files. Do not run "
    "shell commands."
)


# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------


@dataclass
class ClaudeCliBackend:
    """Backend that shells out to the `claude` CLI in `--print` mode."""

    model_id: str = DEFAULT_MODEL_ALIAS
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    # Path to the `claude` executable; resolved once in __post_init__.
    _claude_path: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        path = shutil.which("claude")
        if not path:
            raise RuntimeError(
                "claude CLI not found on PATH. Install Claude Code from "
                "https://claude.com/claude-code (or run `npm i -g "
                "@anthropic-ai/claude-code`) and ensure `claude --version` "
                "works before using --backend claude-cli."
            )
        self._claude_path = path

    # -- public API --------------------------------------------------------

    def decompose(self, summary_text: str, *, lang: str) -> list[str]:
        prompt = DECOMPOSE_PROMPT.format(lang=lang, summary=summary_text)
        raw = self._invoke(prompt=prompt, stage="decompose")
        parsed = _parse_json_loose(raw, expect="array", stage="decompose")
        if not isinstance(parsed, list) or not all(isinstance(c, str) for c in parsed):
            raise RuntimeError(
                "decompose-bad-shape: claude-cli returned non-list-of-strings"
            )
        return [c.strip() for c in parsed if c and c.strip()]

    def classify(
        self, claims: list[str], source_text: str, *, lang: str
    ) -> list[dict]:
        prompt = CLASSIFY_PROMPT.format(
            lang=lang,
            claims=json.dumps(claims, ensure_ascii=False),
            source=source_text,
        )
        raw = self._invoke(prompt=prompt, stage="classify")
        parsed = _parse_json_loose(raw, expect="array", stage="classify")
        if not isinstance(parsed, list):
            raise RuntimeError(
                "classify-bad-shape: claude-cli did not return a JSON array"
            )
        validated: list[dict] = []
        for i, item in enumerate(parsed):
            if not isinstance(item, dict):
                raise RuntimeError(
                    f"classify-bad-shape: audits[{i}] is not an object"
                )
            label = item.get("label")
            if label not in LABELS:
                raise RuntimeError(
                    f"classify-bad-label: audits[{i}].label={label!r} "
                    f"not in {list(LABELS)}"
                )
            validated.append(
                {
                    "claim": item.get("claim", ""),
                    "matched_paragraph": item.get("matched_paragraph"),
                    "label": label,
                    "confidence": int(item.get("confidence", 0)),
                    "rationale": item.get("rationale", ""),
                }
            )
        return validated

    # -- internals ---------------------------------------------------------

    def _invoke(self, *, prompt: str, stage: str) -> str:
        """Run one `claude -p` call. Return the model's textual response.

        We pass the prompt via stdin so we don't have to escape multi-line
        content as an argv argument. `--output-format json` makes the CLI
        emit a small JSON envelope from which we extract the `result`
        string; if the envelope is missing or malformed we fall back to
        using stdout verbatim.
        """
        argv = [
            self._claude_path,
            "-p",
            "--output-format", "json",
            "--model", self.model_id,
            "--append-system-prompt", _JSON_ONLY_SYSTEM,
        ]
        try:
            proc = subprocess.run(
                argv,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"{stage}-timeout: claude CLI did not return within "
                f"{self.timeout_seconds}s"
            ) from e
        except FileNotFoundError as e:
            # Race: PATH lookup succeeded in __post_init__ but binary moved.
            raise RuntimeError(
                f"{stage}-claude-missing: {self._claude_path} not executable"
            ) from e

        if proc.returncode != 0:
            stderr_tail = (proc.stderr or "").strip().splitlines()[-3:]
            raise RuntimeError(
                f"{stage}-claude-exit-{proc.returncode}: "
                f"{' | '.join(stderr_tail) or '(no stderr)'}"
            )

        stdout = (proc.stdout or "").strip()
        if not stdout:
            raise RuntimeError(f"{stage}-empty-output: claude CLI produced no stdout")

        # Try to peel the `--output-format json` envelope. Two shapes seen
        # in the wild:
        #   (a) single dict with a `result` string (older CLI / some flags)
        #   (b) JSON array of stream events (current CLI); the final
        #       `{"type":"result","result":"...","is_error":...}` carries
        #       the model's textual reply.
        try:
            envelope = json.loads(stdout)
            if isinstance(envelope, dict) and isinstance(envelope.get("result"), str):
                return envelope["result"].strip()
            if isinstance(envelope, list):
                for item in reversed(envelope):
                    if (
                        isinstance(item, dict)
                        and item.get("type") == "result"
                        and isinstance(item.get("result"), str)
                    ):
                        return item["result"].strip()
        except json.JSONDecodeError:
            pass
        # Fallback: treat stdout itself as the model reply.
        return stdout


# ---------------------------------------------------------------------------
# Lenient JSON extraction
# ---------------------------------------------------------------------------


def _parse_json_loose(text: str, *, expect: str, stage: str) -> Any:
    """Parse `text` as JSON, with a one-shot fallback that strips code
    fences and extracts the first balanced JSON value.

    `expect` is "array" or "object" — it tells us which opener / closer
    pair to look for in the fallback path.
    """
    text = text.strip()
    if not text:
        raise RuntimeError(f"{stage}-no-json: model returned empty text")

    # Strip a single layer of markdown code fence if present, e.g.
    # ```json\n[...]\n```  or  ```\n[...]\n```
    fenced = re.match(r"^```(?:json)?\s*\n(.*)\n```\s*$", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    # Strict first.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Loose: scan for the first balanced [...] or {...}.
    opener, closer = ("[", "]") if expect == "array" else ("{", "}")
    extracted = _extract_first_balanced(text, opener=opener, closer=closer)
    if extracted is None:
        # Try the other shape in case the model returned the wrong wrapper.
        alt_open, alt_close = ("{", "}") if expect == "array" else ("[", "]")
        extracted = _extract_first_balanced(text, opener=alt_open, closer=alt_close)
    if extracted is None:
        snippet = text[:200].replace("\n", " ")
        raise RuntimeError(
            f"{stage}-no-json: could not locate a JSON {expect} in model output "
            f"(first 200 chars: {snippet!r})"
        )
    try:
        return json.loads(extracted)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{stage}-bad-json: extracted candidate is not valid JSON: {e!s}"
        ) from e


def _extract_first_balanced(text: str, *, opener: str, closer: str) -> str | None:
    """Return the first balanced `opener`...`closer` substring in `text`,
    or None if no balanced span exists. Tracks string literals so braces
    inside strings don't break the balance count.
    """
    start = text.find(opener)
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None
