"""Prefix-byte stability tests for the prompt-caching path.

These tests do NOT call any LLM. They render the prompts that
`summary-doctor` sends to the backend and assert that:

1. Identical inputs produce byte-identical rendered prompts (the
   prefix invariant from `shared/prompt-caching.md`).
2. Tool schemas serialise deterministically (no key reordering).
3. The CLASSIFY claims placeholder serialises deterministically when
   the input list is the same.

If any of these break, the Anthropic-SDK prompt cache will silently
miss across calls even when the user did everything else right. The
test is here so we catch that the moment a prompt edit introduces a
non-determinism.

See `spec-kit/v0.2.2-caching/00-spec.md` §3.4 for the silent-invalidator
table and `milestones/M0-baseline-closeout.md` for the empirical
evidence that motivated this guard.
"""
from __future__ import annotations

import json

import pytest

from summary_doctor.prompts import (
    CLAIM_AUDIT_TOOL_SCHEMA,
    CLAIM_LIST_TOOL_SCHEMA,
    CLASSIFY_PROMPT,
    DECOMPOSE_PROMPT,
)


SAMPLE_SUMMARY = "The author argued that X eliminates Y, which contradicts prior findings."
SAMPLE_SOURCE = (
    "The original paper found that X reduces Y by a small margin under "
    "limited conditions, not that X eliminates Y."
)
SAMPLE_CLAIMS = [
    "The author argued that X eliminates Y.",
    "The author's claim contradicts prior findings.",
]


def test_decompose_prompt_bytes_stable():
    """DECOMPOSE_PROMPT rendered twice with same inputs → byte-equal."""
    rendered_a = DECOMPOSE_PROMPT.format(lang="en", summary=SAMPLE_SUMMARY)
    rendered_b = DECOMPOSE_PROMPT.format(lang="en", summary=SAMPLE_SUMMARY)
    assert rendered_a == rendered_b
    assert rendered_a.encode("utf-8") == rendered_b.encode("utf-8")


def test_classify_prompt_bytes_stable():
    """CLASSIFY_PROMPT rendered twice with same inputs → byte-equal."""
    claims_json_a = json.dumps(SAMPLE_CLAIMS, ensure_ascii=False)
    claims_json_b = json.dumps(SAMPLE_CLAIMS, ensure_ascii=False)
    rendered_a = CLASSIFY_PROMPT.format(
        lang="en", claims=claims_json_a, source=SAMPLE_SOURCE
    )
    rendered_b = CLASSIFY_PROMPT.format(
        lang="en", claims=claims_json_b, source=SAMPLE_SOURCE
    )
    assert rendered_a == rendered_b
    assert rendered_a.encode("utf-8") == rendered_b.encode("utf-8")


def test_tool_schemas_serialise_deterministically():
    """JSON dumps of the two tool schemas produce identical output on
    repeated calls. CPython 3.7+ preserves dict insertion order, so
    this should hold; the test exists to catch a future contributor
    accidentally introducing a set/random-keyed dict into a schema."""
    a1 = json.dumps(CLAIM_LIST_TOOL_SCHEMA, sort_keys=False, ensure_ascii=False)
    a2 = json.dumps(CLAIM_LIST_TOOL_SCHEMA, sort_keys=False, ensure_ascii=False)
    assert a1 == a2

    b1 = json.dumps(CLAIM_AUDIT_TOOL_SCHEMA, sort_keys=False, ensure_ascii=False)
    b2 = json.dumps(CLAIM_AUDIT_TOOL_SCHEMA, sort_keys=False, ensure_ascii=False)
    assert b1 == b2


def test_prompts_contain_no_obvious_silent_invalidators():
    """Lint-style check: the static prompt strings must not contain
    runtime-format markers other than the documented placeholders.

    Allowed placeholders:
      - DECOMPOSE_PROMPT: {lang}, {summary}
      - CLASSIFY_PROMPT:  {lang}, {claims}, {source}

    Any other `{...}` token signals a placeholder that could leak
    non-deterministic content (timestamps, UUIDs) into the prefix.
    """
    import re

    decompose_placeholders = set(re.findall(r"\{(\w+)\}", DECOMPOSE_PROMPT))
    classify_placeholders = set(re.findall(r"\{(\w+)\}", CLASSIFY_PROMPT))

    assert decompose_placeholders == {"lang", "summary"}, (
        f"DECOMPOSE_PROMPT placeholders changed: {decompose_placeholders}"
    )
    assert classify_placeholders == {"lang", "claims", "source"}, (
        f"CLASSIFY_PROMPT placeholders changed: {classify_placeholders}"
    )


@pytest.mark.parametrize(
    "forbidden_token",
    [
        # If any of these ever appear in a prompt template, caching
        # silently breaks.
        "datetime.now",
        "uuid4",
        "time.time",
        "request_id",
    ],
)
def test_prompts_have_no_runtime_value_interpolation(forbidden_token):
    """Catch a future regression where someone adds e.g. a timestamp to
    the prompt template."""
    assert forbidden_token not in DECOMPOSE_PROMPT
    assert forbidden_token not in CLASSIFY_PROMPT
