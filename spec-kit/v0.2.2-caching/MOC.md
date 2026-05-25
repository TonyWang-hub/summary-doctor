# v0.2.2 caching — MOC (entry point)

> Add Anthropic prompt caching to the SDK backend. Thesis: when the same
> source is audited multiple times (self-audit, batch re-runs, future
> per-claim CLI flag), token cost drops ≥80% on the second call onwards.

## Entry order

1. **[constitution.md](constitution.md)** — 7 rules. Inherits v0.2.1's 6 + 1 new caching-specific.
2. **[00-spec.md](00-spec.md)** — thesis, problems, prefix-cache invariants, interface contracts, failure paths.
3. **[01-plan.md](01-plan.md)** — 5 milestones with gates.
4. **[02-tasks.md](02-tasks.md)** — granular checklist.
5. **milestones/** — per-milestone close-outs (filled as we go).
6. **artifacts/** — captured usage logs, EVALUATION delta tables.

## Current status

| Milestone | Status | Gate |
|---|---|---|
| M0 baseline cost capture | not started | record token usage for a representative repeat-source scenario without caching |
| M1 cache_control wiring | not started | tools + DECOMPOSE_PROMPT prefix + CLASSIFY_PROMPT prefix cacheable; tests pass |
| M2 cache-hit verification | not started | `cache_read_input_tokens > 0` on second-call observable via real claude-cli or anthropic SDK |
| M3 EVALUATION delta + docs | not started | docs/EVALUATION.md gets cache-hit row; docs/PROMPT-ENGINEERING.md updated; README mentions caching |
| M4 release | not started | `gh release view v0.2.2` returns a valid URL |

## Why SDD this

A 1-day patch that touches prompt assembly and a backend public class is
exactly where v0.2.1's `tempfile` bug came from — schema/registration
tests passed, no one exercised the hot path end-to-end. SDD gives this
the same dogfood-before-release discipline.

Two specific reasons this needs the scaffold:

1. **Prefix-cache invariants are silent.** `cache_read_input_tokens: 0`
   does not raise — it just means a byte invalidator slipped in. The
   spec encodes those invariants explicitly so the implementation has
   a target to verify, not an assumption.
2. **The thesis is empirical.** "Cost drops ≥80%" is a measurement, not
   a code-review claim. EVALUATION.md needs a before/after row, which
   means M0 captures the before number first.

## Anti-thesis (worth flagging up front)

If `summary-doctor` is mostly used in the "audit one summary against one
source, once" workflow — which is what every bundled demo exercises —
then **caching has zero ROI**. The cache write costs 1.25× more than the
uncached call, and there's no second call to read it back. Only the
self-audit and batch re-run paths benefit.

The spec is honest about this. M3 documents that caching is off by
default for one-shot audits and opt-in for repeat-source workflows.
