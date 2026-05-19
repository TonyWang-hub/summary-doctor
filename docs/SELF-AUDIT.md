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

## Status

| Version | Self-audit |
|---|---|
| v0.1 | shipped — three `make` targets (mock / claude-cli haiku / claude-cli opus) |
| v0.1.1 (planned) | tighten the source set (include CONTRIBUTING.md, MOCK-LIMITS.md), and optionally allow an `anthropic`-SDK backend when a secret is configured |
| v0.2 (planned) | extend to audit `README.zh-CN.md` against the same source |

## How to run

Three Make targets are provided so the cost / fidelity trade-off is
explicit at the command line:

```bash
# Heuristic mock backend — no auth, no API spend, runs in seconds.
# Good for CI smoke tests and "does the pipeline still wire up?" checks.
make self-audit-mock

# Default. Uses the `claude` CLI with the haiku alias, so it reuses your
# Claude Code subscription auth instead of an API key. Seconds to a minute.
make self-audit

# Same path, but opus instead of haiku. Slower, more accurate on the
# softened / reversed boundary. Use when you want to triage divergence,
# not when you just want a smoke test.
make self-audit-opus
```

Output paths:

| Target              | Output                                          |
|---------------------|-------------------------------------------------|
| `self-audit-mock`   | `/tmp/sd-self-audit-mock.md` (overwritten)      |
| `self-audit`        | `eval/self-audit/<timestamp>-haiku.md`          |
| `self-audit-opus`   | `eval/self-audit/<timestamp>-opus.md`           |

The `claude-cli` targets write timestamped files into `eval/self-audit/`
(gitignored) so you can diff successive runs and see whether a change to
README or SPEC moved the divergence number. Mock runs stay in `/tmp/`
because the heuristic output is not worth diffing.

If `claude` is not on the PATH, `make self-audit` fails fast with a
pointer back to this doc. `make self-audit-mock` does not need it.

## Reading the report

The report contains:

- A header with the model name, language hint, claim count, and
  divergence percentage.
- A label distribution table.
- A per-claim block with the matched paragraph (or "no match") and a
  one-line rationale.

Two notes on what the numbers mean here, **specifically because the input
is a README rather than a third-party AI summary**:

1. **Mock on README routinely reports ~60% divergence.** That is expected,
   not a bug. The mock backend is a keyword-overlap-plus-polarity
   heuristic tuned for synthetic summary/source pairs. The README has
   large sections (install, license, contributing) the SPEC does not
   mention, so the mock backend labels them `fabricated`. Likewise, the
   README's "what it is not" section reads as polarity inversion of the
   spec's "what it is" section, which trips the `reversed` heuristic.
   Both are artefacts of using the mock backend on the wrong shape of
   input. Use `make self-audit` (claude-cli) for a label distribution
   that is meaningful to act on.
2. **`reversed` spikes are the signal to look at.** Even on the
   claude-cli backend, the absolute divergence number on a self-audit is
   not a quality target — the README and SPEC overlap by design. What is
   useful is *change* across runs: a `reversed` count that suddenly
   jumps after a README rewrite is worth a manual look at the diff.

## Known limits (also of the real-backend run)

1. **README ≠ AI summary.** The intended input is a third-party AI
   summary of a source. The README is hand-written and shares the same
   authors as the spec. Calibration numbers from self-audit do not
   generalise to real audits and should not be quoted as such.
2. **One-sided source.** SPEC + ROADMAP are not the only authoritative
   documents in the repo (CONTRIBUTING.md, MOCK-LIMITS.md, this file all
   contribute). README claims about contributing or about mock limits
   will look `fabricated` against the SPEC + ROADMAP slice. A future
   iteration may concatenate more of `docs/` as the source.
3. **Real-backend false positives.** Even with `--backend claude-cli`,
   the README is not a single-claim-per-line summary — it has prose,
   code blocks, a roadmap table, and badges. The decomposition stage
   will sometimes promote a code-block fragment or a table cell to a
   "claim", and those will look `fabricated` against the spec because
   the spec does not duplicate the README's UX prose. Treat individual
   claim labels as suggestions to read the matched paragraph, not as
   ground truth.
4. **No assertions on the output.** None of the self-audit targets fail
   the build on a divergence threshold. That is intentional in v0.1 —
   once the numbers stabilise we can add sanity gates (e.g. "fail if
   `reversed` count > 10% of claims on the claude-cli run").

## Will it ever be a CI step?

Not today. Two reasons:

1. **Auth.** The default target shells out to the `claude` CLI, which
   requires interactive Claude Code subscription auth. CI runners do not
   have that auth, and using a real API key in CI raises a secret-handling
   bar this project has not crossed yet.
2. **No threshold.** Until the divergence numbers stabilise across runs,
   "fail the build on X" is arbitrary. CI gating without a calibrated
   threshold creates flaky red runs and trains contributors to ignore the
   signal.

A reasonable v0.1.1 path: keep `make self-audit-mock` runnable in CI as a
zero-cost smoke test (does the pipeline still wire up end-to-end?), and
treat `make self-audit` / `make self-audit-opus` as developer-local
commands invoked before tagging a release. If the project later opts into
an `anthropic`-SDK CI run, it should be a separate workflow guarded by a
repository secret and skipped on forks.
