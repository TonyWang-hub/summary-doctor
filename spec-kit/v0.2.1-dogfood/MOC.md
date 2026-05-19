# v0.2.1 dogfood — MOC (entry point)

> Closes the implementation-status gap from v0.2.0: turn the things we
> *wrote* (MCP server, Skill manifest, URL-heavy docs) into things we have
> actually *run*.

## Entry order

1. **[constitution.md](constitution.md)** — 6 rules. Read first.
2. **[00-spec.md](00-spec.md)** — 3 problems, state machine, interface contracts, failure paths.
3. **[01-plan.md](01-plan.md)** — 5 milestones with gates and effort estimates.
4. **[02-tasks.md](02-tasks.md)** — granular checklist.
5. **milestones/** — per-milestone close-out notes (filled as we go).
6. **artifacts/** — captured traces, baselines, runbooks, session transcripts.

## Current status (as of write-time, before execution)

| Milestone | Status | Gate |
|---|---|---|
| M0 baseline | not started | git clean + pytest baseline recorded |
| M1 mcp install + smoke | not started | 5 previously-skipped MCP tests pass |
| M2 stdio dogfood | not started | real JSON-RPC trace with Divergence 0% on demo 03 |
| M3 URL audit | not started | every doc URL 2xx, annotated, or removed |
| M4 human Skill handoff | not started | session transcript exists |
| M5 release | not started | `gh release view v0.2.1` works |

## Why SDD this

A 3-hour patch release does not strictly require SDD overhead. We use it
here because:

1. The gap being closed (*we said we tested, we did not*) is exactly the
   class of mistake SDD is designed to prevent. Doing the recovery
   ad-hoc would repeat the failure mode.
2. The artifacts produced (stdio trace, URL audit table, Skill session
   transcript) become a reproducible quality bar for every later release
   — not just v0.2.1.
3. Constitution §1 ("honesty over coverage") is operational, not
   aspirational, only if the artifacts are committed alongside the
   release. SDD makes that automatic.
