# Constitution — v0.2.1 dogfood

Six rules. No exceptions without an explicit recorded amendment in this file.

## §1 Honesty over coverage

If a dogfood step cannot be completed by the AI agent (e.g. Claude Desktop integration, human-driven Claude Code session), the gap is **documented in `CHANGELOG.md` and the README** rather than papered over. Stating "we tested it" when we did not is the worst possible outcome — it directly contradicts the project's own "citations, not verdicts" thesis.

## §2 Two carify rounds before any code change

For every milestone, two rounds of carification are written into the milestone doc:
1. **Engineer's view**: concurrency, timeouts, interfaces, environment.
2. **Tester's view**: boundaries, recovery, observability, kill-switch.

Only after both rounds may a code change land. This rule was inherited from the wider project constitution and applies here unchanged.

## §3 No drive-by improvements

This patch release is **only** about closing the v0.2.0 dogfood gap. We do not:
- Refactor unrelated code.
- Tighten unrelated tests.
- Add new demos.
- Rewrite docs that are not part of M3.
- Touch the prompt design (the v0.2.0 6-example prompt was already evaluated).

If we discover an unrelated bug, we file an issue and move on.

## §4 Redaction discipline (carried over from v0.1)

No file under `cloud_gh_project/summary-doctor/` may contain the redline tokens listed in `feedback_github_public_push_pii_sop.md` (王卓, dmall, cabinx, cloud_kg, 蒋林泉, 天猫, dataluma, InfoQ, etc.). Every milestone closes with a `grep` of the full list. Zero hits required.

## §5 Reversibility before authority

Any action that affects state outside the local working tree (GitHub Release, force push, repo delete, gh API mutation) requires explicit user confirmation. Local edits and local test runs are free. The bar is **whether the action is reversible** — not whether it has been authorised in a prior turn.

## §6 SDD artifacts stay versioned

This `spec-kit/v0.2.1-dogfood/` directory is committed alongside the v0.2.1 release. SDD artifacts are part of the project's engineering record — not internal scratch. Anyone reading the repo at v0.2.1 should be able to reconstruct exactly what we tested and what we did not.

If a milestone produces artifacts that contain sensitive material (e.g. machine fingerprints, hostnames captured in stdio traces), they are scrubbed before commit.
