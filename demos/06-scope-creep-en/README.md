# Demo 6 — Scope creep (English)

This demo is synthetic. Any resemblance to specific real trials, products,
suppliers, or guidelines is unintended.

## Failure mode

**Scope creep**: the source establishes a *narrow* finding (one specific
fermented whole-grain product, pre-diabetic overweight adults aged 55–70,
12-week window, surrogate biomarker not clinical endpoint) and devotes a
full paragraph to the three boundaries. The summary drops every boundary,
turning a narrow conditional result into an unconditional claim about
"fermented whole-grain products" in general.

## Expected audit

| Claim from summary | Expected label | Why |
|---|---|---|
| "substituting daily refined-grain breakfast with fermented whole-grain breakfast product produced a significant reduction in fasting glucose at week 12" | **softened** | Source has this finding only for the specific enrolled population (pre-diabetic, BMI 27–32, age 55–70). Summary drops the population qualifier — same fact, much broader claim. |
| "fermented whole-grain products did not cause clinically significant GI adverse events" | **softened** | Source says "*within the trial population*" and "*the single fermented whole-grain product from one supplier*"; summary pluralizes to "products" — category-level claim from a single-product trial. |
| "the result is encouraging enough to motivate a larger replication trial" | exact (or softened) | Source says the same, but appends "and that it is not sufficient evidence for population-level dietary guidance" — the latter half is missing. |

## Why this is hard

Scope creep typically passes a literal fact-check: every keyword is in the
source. What is missing is the *qualifier* — population scope, product scope,
endpoint scope. A per-claim auditor that scores polarity and keyword overlap
will tend to mark these as `exact`. Detecting scope creep needs an auditor
that asks "did the summary preserve every restrictive qualifier from the
source?", which is the kind of judgment the calibrated Anthropic backend is
expected to make.

## How to run

```bash
summary-doctor demos/06-scope-creep-en/summary.txt \
  --original demos/06-scope-creep-en/source.txt \
  --lang en --mock
```
