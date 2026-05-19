"""Anthropic Claude backend.

Requires the `anthropic` SDK and the ANTHROPIC_API_KEY env var.
Install: `pip install anthropic`.

Design choices
--------------

1. Structured output via `tool_use`.

   We define two tools — `submit_claim_list` for decompose and
   `submit_claim_audit` for classify — and require the model to invoke
   them by setting `tool_choice={"type": "tool", "name": ...}`. The
   tool's `input` is consumed directly. We never parse free-text JSON,
   which avoids the "model wrapped JSON in prose / code fence" failure
   mode that plagues bare-text backends.

2. Retry with exponential backoff.

   Each model call is wrapped in a small retry helper. We retry on
   transient transport errors (HTTP 429 rate-limit, HTTP 5xx overload,
   raw connection errors) up to `max_retries` times with base delay
   `retry_base_seconds`. We do NOT retry on 4xx auth / validation
   errors — those will not get better.

3. Model fallback.

   If the primary model (default Haiku 4.5) raises a non-retryable
   structural failure (no tool_use block, malformed tool input,
   InvalidJSON-style parse error), we fall back ONCE to a stronger
   model (default Opus 4.7). After one fallback attempt we give up
   and raise.

4. All failures surface as `RuntimeError` with a clear, single-line
   message that names the failing stage.
"""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from summary_doctor.prompts import (
    CLAIM_AUDIT_TOOL_SCHEMA,
    CLAIM_LIST_TOOL_SCHEMA,
    CLASSIFY_PROMPT,
    DECOMPOSE_PROMPT,
    LABELS,
)


# ---------------------------------------------------------------------------
# Retry / fallback configuration
# ---------------------------------------------------------------------------

# Primary model for both stages. Cheap, fast, good enough for most audits.
DEFAULT_PRIMARY_MODEL = "claude-haiku-4-5-20251001"

# Fallback model used after a structural failure on the primary.
# Stronger model, slower / pricier — we only invoke it once per call.
DEFAULT_FALLBACK_MODEL = "claude-opus-4-7"

# Retry policy for transient transport errors.
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_SECONDS = 2.0
DEFAULT_RETRY_MAX_SECONDS = 30.0


def _is_retryable_error(exc: BaseException) -> bool:
    """Return True if the error looks transient (rate limit, overload, net).

    We match on (a) the SDK's typed exception classes when available, and
    (b) on `status_code` / class names as a string fallback so we don't
    require a specific anthropic SDK version.
    """
    # Best-effort SDK-typed matching.
    try:
        from anthropic import (  # type: ignore
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            RateLimitError,
        )

        if isinstance(
            exc,
            (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError),
        ):
            return True
    except Exception:
        pass

    status = getattr(exc, "status_code", None)
    if isinstance(status, int) and (status == 429 or 500 <= status < 600):
        return True

    name = type(exc).__name__.lower()
    if any(tok in name for tok in ("ratelimit", "timeout", "connection", "overload")):
        return True
    return False


def _retry_call(
    fn: Callable[[], Any],
    *,
    max_retries: int,
    base_seconds: float,
    max_seconds: float,
) -> Any:
    """Call `fn()` with exponential backoff on retryable transport errors.

    Non-retryable exceptions are re-raised on the first attempt. The final
    retryable failure is re-raised with attempt count noted.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except BaseException as exc:  # noqa: BLE001 — we re-raise below
            if not _is_retryable_error(exc):
                raise
            last_exc = exc
            if attempt >= max_retries:
                break
            delay = min(max_seconds, base_seconds * (2 ** attempt))
            # Small jitter so concurrent retries don't synchronise.
            delay += random.uniform(0, delay * 0.1)
            time.sleep(delay)
    raise RuntimeError(
        f"anthropic-transport-failed after {max_retries + 1} attempts: {last_exc!r}"
    ) from last_exc


class _StructuralBackendError(RuntimeError):
    """Raised when the model returned a non-retryable but structurally
    broken response (missing tool_use, malformed JSON in tool input,
    wrong shape). Triggers model fallback."""


# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------


@dataclass
class AnthropicBackend:
    model_id: str = DEFAULT_PRIMARY_MODEL
    fallback_model_id: str = DEFAULT_FALLBACK_MODEL
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_base_seconds: float = DEFAULT_RETRY_BASE_SECONDS
    retry_max_seconds: float = DEFAULT_RETRY_MAX_SECONDS
    decompose_max_tokens: int = 2048
    classify_max_tokens: int = 4096
    # Cached client; lazily initialised on first call.
    _client: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "anthropic SDK not installed. Run: pip install anthropic"
            ) from e
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Export your key or use --mock for offline demo."
            )

    # -- public API --------------------------------------------------------

    def decompose(self, summary_text: str, *, lang: str) -> list[str]:
        prompt = DECOMPOSE_PROMPT.format(lang=lang, summary=summary_text)
        result = self._call_with_fallback(
            prompt=prompt,
            tool=CLAIM_LIST_TOOL_SCHEMA,
            max_tokens=self.decompose_max_tokens,
            stage="decompose",
        )
        claims = result.get("claims")
        if not isinstance(claims, list) or not all(isinstance(c, str) for c in claims):
            raise RuntimeError(
                "decompose-bad-shape: tool returned 'claims' that was not a list of strings"
            )
        # Drop empties just in case the model emitted whitespace strings.
        return [c.strip() for c in claims if c and c.strip()]

    def classify(
        self, claims: list[str], source_text: str, *, lang: str
    ) -> list[dict]:
        prompt = CLASSIFY_PROMPT.format(
            lang=lang,
            claims=json.dumps(claims, ensure_ascii=False),
            source=source_text,
        )
        result = self._call_with_fallback(
            prompt=prompt,
            tool=CLAIM_AUDIT_TOOL_SCHEMA,
            max_tokens=self.classify_max_tokens,
            stage="classify",
        )
        audits = result.get("audits")
        if not isinstance(audits, list):
            raise RuntimeError(
                "classify-bad-shape: tool returned 'audits' that was not a list"
            )
        validated: list[dict] = []
        for i, item in enumerate(audits):
            if not isinstance(item, dict):
                raise RuntimeError(f"classify-bad-shape: audits[{i}] is not an object")
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

    def _get_client(self) -> Any:
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic()
        return self._client

    def _call_with_fallback(
        self,
        *,
        prompt: str,
        tool: dict,
        max_tokens: int,
        stage: str,
    ) -> dict:
        """Run a tool-use call against the primary model; on structural
        failure, retry once on the fallback model."""
        try:
            return self._call_tool_use(
                prompt=prompt,
                tool=tool,
                max_tokens=max_tokens,
                model=self.model_id,
                stage=stage,
            )
        except _StructuralBackendError as primary_exc:
            if self.fallback_model_id and self.fallback_model_id != self.model_id:
                try:
                    return self._call_tool_use(
                        prompt=prompt,
                        tool=tool,
                        max_tokens=max_tokens,
                        model=self.fallback_model_id,
                        stage=stage,
                    )
                except _StructuralBackendError as fb_exc:
                    raise RuntimeError(
                        f"{stage}-failed-after-fallback: "
                        f"primary={self.model_id} err={primary_exc}; "
                        f"fallback={self.fallback_model_id} err={fb_exc}"
                    ) from fb_exc
            raise RuntimeError(
                f"{stage}-failed: primary={self.model_id} err={primary_exc}"
            ) from primary_exc

    def _call_tool_use(
        self,
        *,
        prompt: str,
        tool: dict,
        max_tokens: int,
        model: str,
        stage: str,
    ) -> dict:
        """One tool-use call against a specific model, with retry on
        transient transport errors. Returns the tool's `input` dict."""
        client = self._get_client()

        def _do_call() -> Any:
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                tools=[tool],
                tool_choice={"type": "tool", "name": tool["name"]},
                messages=[{"role": "user", "content": prompt}],
            )

        msg = _retry_call(
            _do_call,
            max_retries=self.max_retries,
            base_seconds=self.retry_base_seconds,
            max_seconds=self.retry_max_seconds,
        )

        return _extract_tool_input(msg, tool_name=tool["name"], stage=stage)


def _extract_tool_input(msg: Any, *, tool_name: str, stage: str) -> dict:
    """Pull the `input` dict out of the first matching `tool_use` block.

    Raises `_StructuralBackendError` (which the caller catches to trigger
    fallback) if the model did not invoke our tool, or invoked it with a
    non-dict input.
    """
    content = getattr(msg, "content", None) or []
    for block in content:
        btype = getattr(block, "type", None)
        if btype == "tool_use" and getattr(block, "name", None) == tool_name:
            tool_input = getattr(block, "input", None)
            if isinstance(tool_input, dict):
                return tool_input
            # Some SDK versions may give us raw JSON text. Try to parse.
            if isinstance(tool_input, str):
                try:
                    parsed = json.loads(tool_input)
                except json.JSONDecodeError as e:
                    raise _StructuralBackendError(
                        f"{stage}-bad-tool-json: {e!s}"
                    ) from e
                if isinstance(parsed, dict):
                    return parsed
            raise _StructuralBackendError(
                f"{stage}-bad-tool-input-type: {type(tool_input).__name__}"
            )
    raise _StructuralBackendError(
        f"{stage}-no-tool-use: model did not invoke {tool_name!r}"
    )
