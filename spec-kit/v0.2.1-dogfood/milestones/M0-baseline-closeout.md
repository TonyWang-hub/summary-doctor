# M0 — Baseline · close-out

**Status**: ✅ passed
**Wall clock**: 2 min
**Artifact**: `artifacts/M0-baseline.txt`

## Carify round 1 — engineer's view

M0 is a snapshot, not a code change. The risk is *taking the wrong
snapshot*: capturing state after some hidden modification, or omitting
a dimension that later milestones depend on.

Captured dimensions:
- Git HEAD + branch + ahead/behind origin
- Working-tree porcelain
- Full pytest output (35 + 5 skip)
- `pip show mcp` to confirm package absence

## Carify round 2 — tester's view

Boundary cases checked:
- pytest exit code reflected (0 = all green; skips do not fail)
- redaction grep ran across `spec-kit/` only (the new directory) — 1 hit is `constitution.md` itself, listing the redline tokens *as the rule*. Documented exception (the rule must name what it forbids).

Recovery: M0 is idempotent. Re-run produces the same snapshot if no state has shifted.

## Gate verification

| Gate criterion | Result |
|---|---|
| baseline numbers recorded in artifacts/M0-baseline.txt | ✅ |
| pytest pre-state captured | ✅ 36 passed, 5 skipped |
| mcp package absence confirmed | ✅ "Package(s) not found: mcp" |

## Findings carried forward

- `36 passed, 5 skipped` is the bar M1 must hold or improve. M1 should turn the 5 skips into passes.
- Branch is +1 ahead of origin/main (the SDD scaffold commit `984450a`). No push until M5.
- Redaction grep on `spec-kit/` yielded the constitution self-reference only. Rule needs no fix.

## Next

→ M1 (mcp install + smoke). See `milestones/M1-...` once written.
