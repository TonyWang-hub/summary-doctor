# v0.2.1 dogfood — Plan

Five milestones. Each has a single, testable gate. No milestone starts until the previous one's gate passes.

## M0 — Baseline (snapshot the starting state)

**Inputs**: v0.2.0 tag (commit `8807db9`).

**Actions**:
- `git status` clean.
- `pytest -q` records baseline: 36 pass + 5 skip.
- `pip show mcp` confirms package is NOT installed (this is the gap we are closing).

**Gate**: baseline numbers recorded in `artifacts/M0-baseline.txt`.

**Owner**: main thread (AI). **Effort**: 5 min AI.

---

## M1 — MCP install + smoke

**Inputs**: Spec §3.1 + §6 open assumptions.

**Carify round 1** (engineer): does `mcp>=0.9.0` resolve? Does it support Python 3.14? Does FastMCP signature match `mcp_server.py`?

**Carify round 2** (tester): if `pip install` fails on 3.14, what is the recovery (venv on 3.12)? If FastMCP API drift breaks import, do we pin or patch?

**Actions**:
1. Inspect PyPI for the actual `mcp` package metadata + supported Python versions.
2. Attempt `pip install --user --break-system-packages 'mcp>=0.9.0'` OR set up a clean venv at `/tmp/sd-mcp-venv/`.
3. Re-run `pytest tests/test_mcp_server.py -v` — verify 5-previously-skipped tests now pass.
4. Record results in `artifacts/M1-install-and-smoke.md`.

**Gate**: 5 previously-skipped MCP tests now pass. If not, M1 fails and we write a documented fallback in CHANGELOG (e.g. "MCP support requires Python 3.12 venv").

**Owner**: main thread. **Effort**: 15-30 min AI.

---

## M2 — MCP stdio dogfood (one real round-trip)

**Inputs**: M1 passed; the `mcp` package + `summary-doctor-mcp` entry point are working.

**Carify round 1** (engineer): subprocess.Popen + thread-based read loop or asyncio? How do we frame JSON-RPC over the stdio transport? Timeouts (10s per call) for hung handshake.

**Carify round 2** (tester): kill-switch (server hangs → kill -9 + cleanup); empty stdin (must not crash); malformed JSON (must respond with error, not exit); EOF on the read side (must not panic).

**Actions**:
1. Write `spec-kit/v0.2.1-dogfood/artifacts/mcp-stdio-client.py` — a minimal stdio MCP client that:
   - Spawns `summary-doctor-mcp` as a subprocess.
   - Sends `initialize` → `tools/list` → `tools/call audit_summary` against demo 03 (`mock` backend, no key required).
   - Captures each frame to `artifacts/mcp-stdio-trace.json`.
2. Validate the captured response: `audit_summary` returns a markdown report whose `Divergence score` line equals 0%.
3. If anything fails, **fix `mcp_server.py`** then re-run — do not retry blindly.

**Gate**: a real captured JSON-RPC trace where `audit_summary` returns a valid Divergence-0% report on demo 03. Stored in `artifacts/mcp-stdio-trace.json`.

**Owner**: main thread. **Effort**: 30-60 min AI.

---

## M3 — URL audit on public docs

**Inputs**: M2 passed (or independent — M3 can be run in parallel with M2 if M2 is blocked).

**Carify round 1** (engineer): rate-limit ≤ 1 RPS, respect `robots.txt`, follow redirects up to 5 hops.

**Carify round 2** (tester): how do we classify "paywalled but legitimate" vs "404 dead"? What does the doc say when a primary source is gone?

**Actions**:
1. Extract every URL from `docs/USE-CASES.md` and `docs/COMPLIANCE.md` to `artifacts/url-list.txt`.
2. For each URL, `WebFetch` it and record HTTP status + final URL.
3. For each non-2xx:
   - Try `web.archive.org/web/*/<url>`.
   - If archive 2xx, annotate inline in the doc with `[archived: ...]`.
   - If no archive, find a primary alternative; if none, **remove the claim** that depends on the URL.
4. Write `artifacts/M3-url-audit.md` with the full table.
5. Patch USE-CASES.md / COMPLIANCE.md with any inline annotations.

**Gate**: every URL in the two docs is either HTTP 2xx, annotated `[archived: ...]`, or removed.

**Owner**: main thread. **Effort**: 30-60 min AI.

---

## M4 — Human Skill handoff

**Inputs**: M2 passed.

**Carify round 1** (engineer): the AI agent cannot drive Claude Code or Claude Desktop. The human has to:
- Copy `skills/summary-doctor/` to `~/.claude/skills/summary-doctor/` (or symlink).
- Open a fresh Claude Code session.
- Type a prompt like *"Can you audit this AI summary against the source paragraph below?"*
- Observe whether the Skill is invoked.
- Paste the session transcript into `artifacts/skill-session.md`.

**Carify round 2** (tester): if Skill does NOT trigger, that's data — the trigger keywords need tuning. Document the negative result honestly.

**Actions**:
1. **AI side**: write a clear runbook in `artifacts/M4-human-runbook.md` (3 steps + 1 expected-output template + 1 fallback if it doesn't trigger).
2. **Human side**: maintainer follows the runbook.
3. Maintainer pastes session transcript into `artifacts/skill-session.md`.
4. If Skill triggers → mark M4 passed.
5. If Skill does NOT trigger → record the negative result + open a v0.2.2 issue ("tune Skill triggers").

**Gate**: `artifacts/skill-session.md` exists and is non-empty.

**Owner**: human (maintainer) + AI (runbook author). **Effort**: 5 min human + 10 min AI.

---

## M5 — v0.2.1 release

**Inputs**: M1-M4 all passed (or M4 documented honestly as a known gap if the maintainer skipped it).

**Actions**:
1. Update `CHANGELOG.md` with v0.2.1 entry — listing exactly which dogfood checks passed and which were skipped.
2. Bump `pyproject.toml` version to `0.2.1`.
3. Commit `spec-kit/v0.2.1-dogfood/` (the SDD artifacts) plus any patches from M3.
4. Push, tag `v0.2.1`, create GitHub Release.

**Gate**: `gh release view v0.2.1` returns a valid release URL.

**Owner**: main thread. **Effort**: 15 min AI.

---

## Effort summary

| Milestone | AI time | Human time | Wall clock |
|---|---|---|---|
| M0 baseline | 5 min | 0 | 5 min |
| M1 install + smoke | 15-30 min | 0 | 15-30 min |
| M2 stdio dogfood | 30-60 min | 0 | 30-60 min |
| M3 URL audit | 30-60 min | 0 | 30-60 min |
| M4 human Skill handoff | 10 min | 5-15 min | 30 min (waiting) |
| M5 release | 15 min | 5 min (push confirm) | 20 min |
| **Total** | **~2 h** | **~20 min** | **~3 h** (with M3/M4 overlap) |
