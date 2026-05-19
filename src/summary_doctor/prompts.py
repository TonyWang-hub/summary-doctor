"""Prompts and structured output schema for the summary-audit pipeline.

Design notes
------------

This module is the single source of truth for what we ask the model to do.
Two prompts are exported:

  DECOMPOSE_PROMPT  — split a summary into atomic assertive claims.
  CLASSIFY_PROMPT   — label each claim against the source (4-way taxonomy).

The label taxonomy is fixed and deliberately small:

  exact      : the source supports the claim (paraphrase OK).
  softened   : the direction is preserved, but qualifiers / strength / scope
               were dropped or weakened. The summary still points the reader
               in the same direction as the source, just with less nuance.
  reversed   : the source contradicts or inverts the claim. The reader walks
               away with the *opposite* conclusion from what the source says.
  fabricated : the source contains nothing supporting the claim. The summary
               introduces a new entity, number, or assertion out of thin air.

The boundary that hurts most in practice is `softened` vs `reversed`, so the
classify prompt spells it out explicitly and the few-shot examples cover it
from both sides.

Schema
------

CLAIM_AUDIT_TOOL_SCHEMA is the JSON Schema for the Anthropic `tool_use`
contract. Backends that support tool-use force the model to return data
through this tool, which avoids the "model wrapped JSON in prose" failure
mode. Backends that cannot use tool-use can still rely on the prompt's
"return only JSON" instruction as a fallback.
"""

from __future__ import annotations

# Allowed labels — kept in one place so backends can validate.
LABELS = ("exact", "softened", "reversed", "fabricated")


# ---------------------------------------------------------------------------
# DECOMPOSE
# ---------------------------------------------------------------------------

DECOMPOSE_PROMPT = """You are an assistant that splits a summary into atomic
assertive claims. A claim is a SINGLE declarative statement that could be
checked against a source.

Rules:
- One claim per array element. Do not merge two facts with "and".
- Keep proper nouns, numbers, dates, and units verbatim.
- Drop rhetorical filler ("In conclusion", "Notably") and pure opinion words
  with no checkable content ("This is fascinating").
- If the summary contains a compound sentence with two checkable facts,
  emit two claims.
- Preserve the original language of each claim. Do not translate.

Output contract:
- Return ONLY a JSON array of strings.
- No prose, no markdown, no code fences, no trailing commentary.

---
Worked examples (synthetic, for illustration only):

Summary:
"A 2021 university study reported that brief outdoor walks improved short-term
recall in adults by 14% on average, although the effect faded after one week."

Expected output:
[
  "A 2021 university study reported that brief outdoor walks improved short-term recall in adults by 14% on average.",
  "The recall effect faded after one week."
]

Summary:
"The new compiler is faster and uses less memory than the previous version."

Expected output:
[
  "The new compiler is faster than the previous version.",
  "The new compiler uses less memory than the previous version."
]
---

Language hint: {lang}

Summary:
---
{summary}
---
"""


# ---------------------------------------------------------------------------
# CLASSIFY
# ---------------------------------------------------------------------------

CLASSIFY_PROMPT = """You are an audit assistant. For each claim in the list,
find the SINGLE most relevant paragraph in the source and label the claim
with EXACTLY ONE of the four labels below.

Label taxonomy:

  exact      — the source supports the claim. Paraphrase, reordering, and
               minor wording differences are fine. The reader of the claim
               and the reader of the source would draw the same conclusion.
  softened   — direction is preserved but qualifiers, scope, or strength
               were dropped or weakened. The summary points the same way
               as the source, just with less nuance.
                 e.g. source: "X helps in narrow lab conditions";
                      claim:  "X helps."
                 e.g. source: "Y may reduce risk for some patients";
                      claim:  "Y reduces risk."
  reversed   — source CONTRADICTS or INVERTS the claim. The reader of the
               claim would walk away with the OPPOSITE conclusion from what
               the source actually says. This includes flipped polarity,
               flipped causal direction, and flipped magnitude (e.g.
               "increases" stated as "decreases").
                 e.g. source: "X did NOT reduce error rates";
                      claim:  "X reduced error rates."
                 e.g. source: "Y increases the cost";
                      claim:  "Y lowers the cost."
  fabricated — the source contains NO content supporting the claim. The
               claim introduces a new entity, number, mechanism, or fact
               that has no anchor anywhere in the source.

Boundary rule (softened vs reversed):
- If the direction is the same (positive vs positive, negative vs negative,
  helps vs helps) but the claim drops scope or qualifiers → softened.
- If the direction is FLIPPED, even subtly (added or removed negation,
  swapped subject/object of an effect, "increase" ↔ "decrease",
  "did" ↔ "did not") → reversed.
- When unsure between softened and reversed, prefer the more conservative
  label that the source can actually support; flag your uncertainty by
  lowering `confidence`.

Reasoning protocol:
- Reason about each claim step-by-step IN YOUR HEAD before emitting output.
- Do NOT include your internal reasoning in the output. The `rationale`
  field is a one-sentence summary, NOT a chain-of-thought transcript.

Output contract — return ONLY a JSON array of objects, no prose, no
markdown, no code fences. Each object MUST contain these keys:

  - claim              (string, verbatim from the input list)
  - matched_paragraph  (string up to 400 chars verbatim from the source,
                        or null if no paragraph matches)
  - label              (one of: "exact", "softened", "reversed", "fabricated")
  - confidence         (integer 0-100, your certainty in the label)
  - rationale          (one short sentence, max ~30 words)

You produce a citation map, not a verdict. The reader makes the final call.

---
Worked examples (synthetic, for illustration only):

Example A — softened
  Source paragraph:
    "In a controlled laboratory study with 24 healthy volunteers, drinking
    chamomile tea before bed reduced reported sleep-onset latency by an
    average of 6 minutes. The authors caution that the effect was small and
    did not reach significance for participants over 60."
  Claim:
    "Chamomile tea helps people fall asleep faster."
  Correct label: softened
  Why: direction matches ("reduced latency" ≈ "faster"), but the claim
  drops the lab-only scope, the small effect size, and the age caveat.

Example B — reversed
  Source paragraph:
    "Contrary to popular belief, our trial found that the new app did NOT
    improve adherence to medication schedules; adherence in the app group
    was slightly lower than in the control group."
  Claim:
    "The new app improved medication adherence."
  Correct label: reversed
  Why: source explicitly says the app did NOT improve adherence (and was
  slightly worse); the claim asserts the opposite direction.

Example C — fabricated
  Source: an article about urban bike-lane policy that never discusses
  hardware, GPUs, or compute.
  Claim:
    "The study identified GPU supply as the main bottleneck."
  Correct label: fabricated
  Why: the source contains no discussion of GPUs or supply bottlenecks at
  all; the claim is unanchored.

Example D — exact
  Source paragraph:
    "Across three independent replications, the team observed a 22%
    reduction in defect rates after introducing the peer-review checklist."
  Claim:
    "Introducing the peer-review checklist reduced defect rates by about 22%."
  Correct label: exact
  Why: paraphrase with matching number and direction.
---

Language hint: {lang}

Claims (JSON array):
{claims}

Source:
---
{source}
---
"""


# ---------------------------------------------------------------------------
# Tool schema for Anthropic `tool_use` structured output
# ---------------------------------------------------------------------------

# JSON Schema for one audit object.
_AUDIT_ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "claim": {
            "type": "string",
            "description": "The claim text, verbatim from the input list.",
        },
        "matched_paragraph": {
            "type": ["string", "null"],
            "description": (
                "Up to 400 characters verbatim from the source paragraph "
                "that best matches the claim, or null if no paragraph "
                "supports or contradicts the claim."
            ),
        },
        "label": {
            "type": "string",
            "enum": list(LABELS),
            "description": "Exactly one of: exact, softened, reversed, fabricated.",
        },
        "confidence": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Integer 0-100 reflecting certainty in the label.",
        },
        "rationale": {
            "type": "string",
            "description": "One short sentence explaining the label; not a chain-of-thought.",
        },
    },
    "required": ["claim", "matched_paragraph", "label", "confidence", "rationale"],
}


# Top-level tool exposed to the model. The model must invoke this tool
# exactly once; its `audits` argument is what we consume.
CLAIM_AUDIT_TOOL_SCHEMA = {
    "name": "submit_claim_audit",
    "description": (
        "Submit the per-claim audit results. You MUST call this tool exactly "
        "once with an `audits` array containing one object per input claim, "
        "in the same order. Do not return any audits as plain text."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "audits": {
                "type": "array",
                "minItems": 0,
                "items": _AUDIT_ITEM_SCHEMA,
                "description": "Per-claim audit objects, same order as input claims.",
            },
        },
        "required": ["audits"],
    },
}


# Tool used to return the decompose step's claim list.
CLAIM_LIST_TOOL_SCHEMA = {
    "name": "submit_claim_list",
    "description": (
        "Submit the atomic claims extracted from the summary. You MUST call "
        "this tool exactly once with a `claims` array of strings."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "claims": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "description": "Atomic assertive claims, one per array element.",
            },
        },
        "required": ["claims"],
    },
}
