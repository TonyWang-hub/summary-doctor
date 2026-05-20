# M4 — Skill manual dogfood · close-out

**Status**: ⏭ skipped (honest gap, per Constitution §1)
**Wall clock**: 0 (maintainer decision)
**Artifact**: `artifacts/skill-session.md` (one-liner SKIPPED record)

## Carify round 1 — engineer's view

This milestone is the only one that requires a human actor — the AI agent
cannot drive Claude Code or Claude Desktop sessions from inside its own
process. The runbook was therefore designed so the human path is **5
minutes if taken** and **honestly documentable if skipped**.

The cost of skipping: we ship v0.2.1 not knowing whether the Skill
manifest's trigger keywords (`"audit this AI summary"`, `"check if this
summary is faithful"`, `"any fabricated citation?"`, etc.) are strong
enough for Claude Code's Skill-discovery surface to pick the manifest
up. The structural side (file present, frontmatter valid, manifest
under the 1.5 KB ceiling) was already covered by M1's pytest run.

## Carify round 2 — tester's view

Spec §4 anticipated this exact failure path:

> Human Skill dogfood (M4) impossible (no Claude Code on machine) →
> downgrade to "Skill manifest validated by structural lint only" and
> document the gap in CHANGELOG honestly.

The gate criterion was *evidence captured*, not *Skill triggered* —
"M4 SKIPPED" is itself the evidence.

## Gate verification (spec §3.2)

| Criterion | Result |
|---|---|
| `artifacts/skill-session.md` exists and is non-empty | ✅ contains the SKIPPED record |
| If outcome was C (Skill did not trigger), file a v0.2.2 issue | N/A — not run |
| Honest documentation in CHANGELOG | → M5 (T5.1) |

## Carry-forward

- CHANGELOG.md v0.2.1 entry must explicitly note: "M4 SKIPPED — Skill
  manifest validated by structural lint (12/12 mcp pytest) only; trigger
  keywords NOT exercised in a live Claude Code session."
- Optional v0.2.2 issue: "Verify Skill triggers in a live Claude Code
  session" — leave the runbook (`artifacts/M4-human-runbook.md`) in
  the repo as the reproduction recipe.

## Redaction grep (constitution §4)

`grep -riE` of the redline set on `artifacts/skill-session.md` and this
close-out → 0 hits.

## Next

→ M5 (release). Awaiting maintainer authorisation per Constitution §5
(push / tag / `gh release create` are irreversible).
