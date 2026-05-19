# Prompt engineering notes

This document is the design log for the two LLM-facing prompts used by
summary-doctor: `DECOMPOSE_PROMPT` (stage 3) and `CLASSIFY_PROMPT` (stage 4).
If you want to change behaviour, the lever is here — not in heuristics.

## Four guiding principles

1. **Citations, not verdicts.** Every prompt explicitly tells the model that
   its job is to emit a citation map. The reader judges. The prompt never asks
   "is this summary true?" — only "what does the source say about this claim?".
2. **4-class output, no escapes.** The classifier must pick one of
   `exact / softened / reversed / fabricated`. No "uncertain", no free-text.
   This forces a useful answer even when the source is ambiguous; the
   `confidence` field absorbs the wobble.
3. **Structured tool-use shape.** Both prompts return JSON only, with a fixed
   key set. No prose, no markdown. This makes the pipeline parser strict and
   the downstream report deterministic.
4. **Language-aware, not language-fluent.** The prompt takes a `{lang}` hint
   so the model knows whether negation cues are `not / never` or `不 / 没 / 未`.
   We do not currently translate; we align within one language.

## `DECOMPOSE_PROMPT` — splitting into atomic claims

Source (`src/summary_doctor/prompts.py`):

```python
DECOMPOSE_PROMPT = """You are an assistant that splits a summary into atomic
assertive claims. A claim is a single declarative statement that could be
checked against a source.

Language hint: {lang}

Return ONLY a JSON array of strings. No prose, no markdown.

Summary:
---
{summary}
---
"""
```

### Why atomic

A multi-clause sentence ("X is fast, but Y is the real bottleneck") contains
two checkable propositions. If we hand the whole sentence to the classifier,
the model averages the two and we lose signal on the part that actually
diverges from the source.

### Known failure modes

- **Over-splitting long compound sentences.** When the summary uses long
  parenthetical clauses, atomic decomposition can fragment a single argument
  into 4–5 micro-claims, several of which lose their qualifier ("under
  condition Z"). Downstream this inflates the `softened` count.
- **Numbered lists in the summary.** If the summary already contains
  "1. … 2. … 3. …", the model sometimes returns the numbering as part of the
  claim string. The pipeline tolerates this but it hurts diffability.
- **Rhetorical questions.** "Is X really the bottleneck?" is not assertive,
  but some models emit it as a claim. Acceptable for now — the classifier
  will tend to label these `fabricated` or low-confidence `softened`.

## `CLASSIFY_PROMPT` — mapping + labelling

Source (`src/summary_doctor/prompts.py`):

```python
CLASSIFY_PROMPT = """You are an audit assistant. For each claim in the list,
find the most relevant paragraph in the source and label the claim with ONE of:

- "exact"      : source supports the claim (paraphrase OK)
- "softened"   : direction is preserved but qualifiers or strength are lost
- "reversed"   : source contradicts or inverts the claim
- "fabricated" : source does not contain anything supporting the claim

Rules:
- Quote the matched paragraph verbatim (max 400 characters). If none, return null.
- Confidence is an integer 0-100 reflecting your certainty.
- Rationale is one short sentence explaining the label.
- You output a citation map, not a verdict. The reader will judge.
"""
```

### The hardest boundary: `softened` vs `reversed`

These two labels collide whenever a qualifier flips polarity. Consider:

- Source: "X often outperforms Y, *though not in production environments*."
- Summary: "X outperforms Y."

Is that `softened` (we lost the qualifier) or `reversed` (the qualifier was
the whole point)? The prompt currently treats this as `softened` because the
direction is preserved at the headline level. A future revision may add a
"qualifier-bearing" sub-label, but only after we have ≥50 labelled cases on
both sides.

### Few-shot selection (not yet in the prompt)

The current prompt is zero-shot. Adding few-shots is on the roadmap; the
selection rule will be:

- One canonical example per label (4 total).
- Each example shows claim + matched paragraph + label + rationale.
- Examples must be synthetic — no real speakers, no real organisations.

### Chain-of-thought

The prompt nudges CoT only through the `rationale` field. We deliberately
do *not* ask for a `<thinking>` block: it inflates tokens by 3–5× and the
gains on a 4-class task are marginal.

## How to change a prompt and validate

1. Edit `src/summary_doctor/prompts.py`.
2. Run `make demo` and confirm pipeline still parses the JSON cleanly.
3. Run `bash demos/run-demo.sh` (all three demos under the mock backend).
4. Check the label distribution per demo against `docs/MOCK-LIMITS.md`
   invariants (demo 1 expects non-zero `reversed`; demo 3 expects zero).
5. If you have an API key, re-run with `--model claude-haiku-4-5-20251001`
   and compare against the previous run. Treat any flipped label as a
   regression candidate, then triage.

## Bad prompt smells (don't do these)

1. **Asking for a verdict.** "Is this summary trustworthy?" — collapses the
   4-class signal into one bit and inherits the auditor LLM's biases.
2. **Letting the model invent labels.** "Use one of these labels or invent a
   new one if needed." — fragments the report and breaks downstream parsing.
3. **Omitting the citation requirement.** Without `matched_paragraph`, the
   tool degenerates into "LLM auditing LLM" — exactly what we set out to avoid.
4. **Mixing languages in the prompt body.** The prompt is English; the
   `{lang}` hint tells the model which language the *content* is in. Mixing
   instruction language with content language confuses smaller models.
5. **Inviting prose.** Any wording like "explain your reasoning" without a
   JSON schema attached produces markdown that breaks the parser.
6. **Implicit confidence.** Without an explicit 0–100 `confidence` field,
   models default to overconfident "high" and the report loses calibration.
7. **Source paragraph paraphrase.** If the prompt allows "summarise the
   matched paragraph", we lose the verbatim citation guarantee — and with
   it, the entire reason this tool exists.
