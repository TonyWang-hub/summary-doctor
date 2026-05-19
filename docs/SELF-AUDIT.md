# Self-audit

## Why

If summary-doctor is a tool for catching AI summaries that diverge from
their source, the project should be willing to point that tool at itself.
Self-audit is the simplest dogfood loop available: run the v0.1 pipeline on
this repository's own surface text and see whether it behaves the way the
documentation claims it does.

This is not a correctness proof — it is a smoke test for "does the tool run
end-to-end against a non-demo input, and does the report look sane?".

## What gets audited

The audit treats `README.md` as the **summary** under test and the
concatenation of `docs/SPEC.md` + `docs/ROADMAP.md` as the **source**. The
choice is deliberate:

- `README.md` is the document most likely to drift away from the design
  over time (marketing language, optimistic claims, stale roadmap bullets).
- `SPEC.md` + `ROADMAP.md` together form the closest thing the repository
  has to an authoritative design statement.

This is a stretch of the tool's intended use case. Concretely, the README
is not a third-party AI summary of the spec — it is a hand-written
document that overlaps with the spec by design. Expect a high `exact`
count and a non-trivial `fabricated` count for README sentences that talk
about install / contributing / license (things the spec does not mention).

## How to run it

```bash
make self-audit
```

What the target does:

1. Concatenate `docs/SPEC.md` and `docs/ROADMAP.md` into a temp file.
2. Run summary-doctor over `README.md` against that temp file in `--mock`
   mode and English-language hint.
3. Write the report to `/tmp/sd-self-audit.md` (plus a JSON sidecar).
4. Clean up the temp source file.

No API key is required; the `--mock` backend is used so the target stays
runnable in CI without secrets. The trade-off is that the labels are the
heuristic mock labels, not calibrated detector output. See
[`MOCK-LIMITS.md`](MOCK-LIMITS.md) for what the mock backend can and
cannot tell you.

## Reading the report

The report at `/tmp/sd-self-audit.md` will contain:

- A header with the model name, language hint, claim count, and
  divergence percentage.
- A label distribution table.
- A per-claim block with the matched paragraph (or "no match") and a
  one-line rationale.

You are looking for two things:

1. **The pipeline ran to completion.** No exceptions, no empty report.
2. **The label distribution is plausible.** Some `exact` (the README does
   echo the spec), some `fabricated` (the README has install / license /
   contributing sections the spec does not), and `reversed` should be
   relatively rare — if it spikes, that is a signal the README has drifted
   from the spec and is worth a manual look.

## Status

| Version | Self-audit |
|---|---|
| v0.1 | runnable via `make self-audit`, mock backend only |
| v0.1.1 (planned) | wire into CI; optionally allow `--backend anthropic` when a secret is configured |
| v0.2 (planned) | extend to audit `README.zh-CN.md` against the same source |

## Limits of self-audit

1. **README ≠ AI summary.** The intended input is a third-party AI summary
   of a source. The README is hand-written and shares the same authors as
   the spec. Calibration numbers from self-audit do not generalise.
2. **Mock backend only (today).** Labels are heuristic. A real LLM run
   would produce different (and probably more useful) labels — but is
   gated on having an API key in CI.
3. **One-sided source.** SPEC + ROADMAP are not the only authoritative
   documents in the repo (CONTRIBUTING.md, MOCK-LIMITS.md, this file all
   contribute). A future iteration may concatenate the entire `docs/`
   directory as the source.
4. **No assertions on the output.** The current target produces a report
   but does not fail the build on any specific divergence threshold. That
   is intentional for v0.1.1 — once the numbers stabilise we can add
   sanity gates (e.g. "fail if `reversed` count > 10% of claims").
