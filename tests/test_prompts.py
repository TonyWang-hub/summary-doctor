"""Unit tests for prompt rendering and tool schema shape.

These tests are pure-Python: they do NOT import the anthropic SDK and do
NOT make any network calls. They protect two contracts:

  1. The prompt templates accept the documented placeholders and substitute
     them correctly (lang / summary / source / claims).
  2. The tool schemas conform to a JSON Schema draft we can validate
     without external dependencies (basic structural check).
"""

from __future__ import annotations

import json
import re

from summary_doctor.prompts import (
    CLAIM_AUDIT_TOOL_SCHEMA,
    CLAIM_LIST_TOOL_SCHEMA,
    CLASSIFY_PROMPT,
    DECOMPOSE_PROMPT,
    LABELS,
)


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------


def test_decompose_prompt_substitutes_lang_and_summary():
    rendered = DECOMPOSE_PROMPT.format(
        lang="en",
        summary="The new compiler is faster and uses less memory.",
    )
    assert "Language hint: en" in rendered
    assert "The new compiler is faster and uses less memory." in rendered
    # No unfilled placeholders should remain.
    assert "{lang}" not in rendered
    assert "{summary}" not in rendered


def test_decompose_prompt_handles_unicode_summary():
    summary = "在受控实验中，方法 X 让响应时间缩短了 12%。"
    rendered = DECOMPOSE_PROMPT.format(lang="zh", summary=summary)
    assert summary in rendered
    assert "Language hint: zh" in rendered


def test_classify_prompt_substitutes_all_placeholders():
    claims_json = json.dumps(
        [
            "A 2021 study showed X improved Y by 14%.",
            "The effect faded after one week.",
        ],
        ensure_ascii=False,
    )
    rendered = CLASSIFY_PROMPT.format(
        lang="en",
        claims=claims_json,
        source="Paragraph one.\n\nParagraph two.",
    )
    assert "Language hint: en" in rendered
    assert claims_json in rendered
    assert "Paragraph one." in rendered
    assert "Paragraph two." in rendered
    for placeholder in ("{lang}", "{claims}", "{source}"):
        assert placeholder not in rendered, f"unfilled placeholder: {placeholder}"


def test_classify_prompt_mentions_all_four_labels():
    # The four-way taxonomy is load-bearing; if a label name drifts the
    # backend's enum validation will reject perfectly good model output.
    for label in LABELS:
        assert label in CLASSIFY_PROMPT, f"label {label!r} missing from prompt"


def test_classify_prompt_has_softened_vs_reversed_boundary_rule():
    # The boundary rule is the highest-signal piece of the prompt; if a
    # refactor accidentally drops it, the model wobbles between softened
    # and reversed. Lock it in with a structural assertion.
    pattern = re.compile(r"softened\s+vs\s+reversed", re.IGNORECASE)
    assert pattern.search(CLASSIFY_PROMPT), "softened vs reversed boundary rule missing"


def test_classify_prompt_covers_causal_direction_flip():
    # Causal-direction inversion ("A→B" surfaced as "B→A") is a fail mode
    # we observed on a smaller model: it labels the flip as exact or
    # softened because the same entities appear. The prompt must explicitly
    # cover both English and 中文 phrasing so the model treats causal
    # flips as `reversed` regardless of source language.
    assert "causal" in CLASSIFY_PROMPT.lower(), (
        "CLASSIFY_PROMPT must mention 'causal' direction flips explicitly"
    )
    assert "因果" in CLASSIFY_PROMPT, (
        "CLASSIFY_PROMPT must mention 因果 direction flips for 中文 sources"
    )


def test_classify_prompt_keeps_chain_of_thought_out_of_output():
    # We tell the model to reason internally but not emit reasoning to
    # the output. If this contract drifts, audit reports balloon in size.
    assert "rationale" in CLASSIFY_PROMPT
    assert "do not include" in CLASSIFY_PROMPT.lower() or "do NOT include" in CLASSIFY_PROMPT


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


def _assert_json_serialisable(obj) -> None:
    # JSON Schema definitions are themselves JSON-serialisable; if they
    # aren't, the SDK will reject them at request time.
    json.dumps(obj)


def test_claim_list_tool_schema_basic_shape():
    schema = CLAIM_LIST_TOOL_SCHEMA
    _assert_json_serialisable(schema)
    assert schema["name"] == "submit_claim_list"
    assert isinstance(schema["description"], str) and schema["description"]
    input_schema = schema["input_schema"]
    assert input_schema["type"] == "object"
    assert "claims" in input_schema["properties"]
    assert input_schema["properties"]["claims"]["type"] == "array"
    assert input_schema["properties"]["claims"]["items"]["type"] == "string"
    assert "claims" in input_schema["required"]


def test_claim_audit_tool_schema_required_fields_match_label_taxonomy():
    schema = CLAIM_AUDIT_TOOL_SCHEMA
    _assert_json_serialisable(schema)
    assert schema["name"] == "submit_claim_audit"

    input_schema = schema["input_schema"]
    assert input_schema["type"] == "object"
    assert "audits" in input_schema["required"]

    item = input_schema["properties"]["audits"]["items"]
    assert item["type"] == "object"

    required = set(item["required"])
    assert required == {
        "claim",
        "matched_paragraph",
        "label",
        "confidence",
        "rationale",
    }, f"unexpected required field set: {required}"

    # label must be a closed enum equal to LABELS.
    label_prop = item["properties"]["label"]
    assert set(label_prop["enum"]) == set(LABELS)

    # confidence must be a bounded integer.
    conf = item["properties"]["confidence"]
    assert conf["type"] == "integer"
    assert conf["minimum"] == 0
    assert conf["maximum"] == 100

    # matched_paragraph must accept null (we use it as the "no match" signal).
    mp = item["properties"]["matched_paragraph"]
    mp_types = mp["type"] if isinstance(mp["type"], list) else [mp["type"]]
    assert "null" in mp_types
    assert "string" in mp_types


def test_tool_schemas_disallow_extra_properties():
    # additionalProperties: False guards against the model smuggling
    # extra keys (e.g. a chain-of-thought field) into structured output.
    assert CLAIM_LIST_TOOL_SCHEMA["input_schema"]["additionalProperties"] is False
    assert CLAIM_AUDIT_TOOL_SCHEMA["input_schema"]["additionalProperties"] is False
    item = CLAIM_AUDIT_TOOL_SCHEMA["input_schema"]["properties"]["audits"]["items"]
    assert item["additionalProperties"] is False


def test_labels_constant_is_closed_set():
    # Defensive: pipeline.py also enumerates these labels; if anyone adds
    # a 5th label here without updating the pipeline, the schema and the
    # report renderer drift apart silently.
    assert LABELS == ("exact", "softened", "reversed", "fabricated")
