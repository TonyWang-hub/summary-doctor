# Demo 7 — Temporal error (English)

This demo is synthetic. PROTO-K is a fictional protocol; any resemblance to
specific real protocols, labs, or vendors is unintended.

## Failure mode

**Temporal error**: the summary preserves the *structure* of the source
(protocol proposed → reference implementation → redesign → adoption) but
silently shifts two of the three dates. The shifts are small (3 years and
−3 years), the surrounding narrative still reads coherently, and a reader
without the source in front of them has no way to catch the error.

## Expected audit

| Claim from summary | Expected label | Why |
|---|---|---|
| "PROTO-K was first proposed in 2014" | **fabricated** (or reversed) | Source says **2017**. The 2014 date does not appear anywhere in source. |
| "A reference implementation followed in 2019" | exact | Source has the same year |
| "The 2022 redesign was the first revision to support dynamic membership and treat partitions as recoverable state" | exact | Source has the same finding |
| "Wide industry adoption began in 2020" | **fabricated** (or reversed) | Source says "late 2023, two years after the v2 redesign". The 2020 date is impossible given the 2022 v2 timing. |

## Why this is hard

Temporal errors are a high-stakes failure mode for AI summaries (citing
prior work as having been published earlier or later than it actually was).
They are difficult for a polarity-and-keywords auditor because:
- numbers and dates do not have polarity
- the surrounding sentence is still grammatically and topically aligned with
  the source paragraph
A real auditor needs to extract date-bound claims and cross-check the
specific number, not just keyword overlap.

## How to run

```bash
summary-doctor demos/07-temporal-error-en/summary.txt \
  --original demos/07-temporal-error-en/source.txt \
  --lang en --mock
```
