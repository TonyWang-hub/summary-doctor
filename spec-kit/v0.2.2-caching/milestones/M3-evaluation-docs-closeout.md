# M3 — EVALUATION + docs · close-out

**Status**: ✅ passed
**Wall clock**: ~15 min
**Artifact**: changes to EVALUATION.md / PROMPT-ENGINEERING.md / README.md / README.zh-CN.md / CHANGELOG.md

## Carify R1 — engineer's view

Doc strategy: explicit acknowledgement that the M0 finding (claude-cli no workload-level cache) is a load-bearing result, not a footnote. EVALUATION.md gets a dedicated "Cache performance (v0.2.2)" section that:
- documents what was wired (per-backend table)
- discloses real-API verification is deferred to the runbook
- shows the M0 numbers verbatim so anyone can audit our reasoning

README mentions caching in 1 line + link. zh-README mirrored.
CHANGELOG separates "Added" from "Documented (M0 finding worth shipping)" from "Deferred (honest gap)".
PROMPT-ENGINEERING adds a cache-prefix-stability section explaining the 4 invariants the new test file locks.

## Carify R2 — tester's view

- EVALUATION.md table separates two backends with explicit "did vs didn't" verification. Reader can't accidentally conflate.
- M0 numbers (claude-cli) are in their own sub-table with explicit interpretation. Hard to misread as "v0.2.2 thesis confirmed".
- CHANGELOG opens with the M0 finding, not the code change — sets the right expectation order.
- Reproduction runbook linked from EVALUATION + CHANGELOG so it's discoverable from both ship surfaces.

## Gate verification

| Criterion | Result |
|---|---|
| `docs/EVALUATION.md` has "Cache performance" section | ✅ inserted before "Limits of this evaluation" |
| Numbers match M0 artifact exactly (no rounding hype) | ✅ values copied verbatim from artifacts/M0-baseline-claude-cli.json |
| README + zh-README mention caching honestly | ✅ 1 line each + link to EVALUATION section |
| CHANGELOG v0.2.2 entry covers Added + Documented + Deferred | ✅ |
| PROMPT-ENGINEERING addendum on cache invariants | ✅ |
| pyproject version bumped 0.2.1 → 0.2.2 | ✅ |

## Redaction grep

`grep -riE` of the redline set on the changed files → 0 hits (verified before commit).

## Next

→ M4 (release). Requires explicit user authorisation per Constitution §5.
