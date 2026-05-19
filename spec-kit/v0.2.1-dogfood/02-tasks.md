# v0.2.1 dogfood — Tasks

Granular task breakdown. Each task is independently executable, has a single
verifiable output, and references the milestone gate it contributes to.

## Convention

- `[ ]` = not started · `[~]` = in progress · `[x]` = done
- `→ artifact:` = the file or git diff that proves the task is done
- `← gate:` = the milestone gate this task feeds

## M0 — Baseline

- [ ] **T0.1** Snapshot git state. `git rev-parse HEAD` + `git status --porcelain`. → `artifacts/M0-baseline.txt` line 1-3. ← M0 gate.
- [ ] **T0.2** Record pytest baseline. `PYTHONPATH=src python3 -m pytest tests/ -q` tail 3 lines. → `artifacts/M0-baseline.txt` line 4-6. ← M0 gate.
- [ ] **T0.3** Confirm `mcp` package is absent. `pip show mcp 2>&1 | head -2`. → `artifacts/M0-baseline.txt` line 7-8. ← M0 gate.

## M1 — MCP install + smoke

- [ ] **T1.1** Read PyPI metadata for `mcp`. `WebFetch https://pypi.org/pypi/mcp/json` summarising Python version classifiers + latest stable. → notes in `artifacts/M1-install-and-smoke.md` §1.
- [ ] **T1.2** Decide install strategy: `--user --break-system-packages` on system Python (3.14) vs a clean venv on 3.12. → decision recorded in `artifacts/M1-install-and-smoke.md` §2.
- [ ] **T1.3** Execute the chosen install. Record `pip install` output. → `artifacts/M1-install-and-smoke.md` §3.
- [ ] **T1.4** Re-run MCP pytests. `PYTHONPATH=src python3 -m pytest tests/test_mcp_server.py -v`. Expected: previously 5 skipped now pass. → `artifacts/M1-install-and-smoke.md` §4. ← M1 gate.
- [ ] **T1.5** If T1.4 fails (FastMCP API drift / import error), patch `src/summary_doctor/mcp_server.py` minimally and re-run. → diff captured in `artifacts/M1-install-and-smoke.md` §5.

## M2 — MCP stdio dogfood

- [ ] **T2.1** Read `mcp_server.py` end-to-end. Confirm `main()` calls stdio entrypoint. → no artifact; informs T2.2.
- [ ] **T2.2** Write `artifacts/mcp-stdio-client.py` — a minimal stdio JSON-RPC client (~80 lines). Spawns `summary-doctor-mcp` subprocess; sends `initialize` → `tools/list` → `tools/call audit_summary` against demo 03 with `backend="mock"`. → file.
- [ ] **T2.3** Run `mcp-stdio-client.py` and capture every frame. → `artifacts/mcp-stdio-trace.json`.
- [ ] **T2.4** Validate the trace: `audit_summary` reply contains a markdown report whose `Divergence score: 0%` line is present. → `artifacts/M2-validation.md`. ← M2 gate.
- [ ] **T2.5** If T2.4 fails, fix `mcp_server.py` (not the test, not the client). Re-run T2.3 + T2.4.

## M3 — URL audit

- [ ] **T3.1** Extract every URL from `docs/USE-CASES.md` and `docs/COMPLIANCE.md`. `grep -oE 'https?://[^ )]+' docs/USE-CASES.md docs/COMPLIANCE.md | sort -u`. → `artifacts/url-list.txt`.
- [ ] **T3.2** For each URL, `WebFetch` and record HTTP status (or "fetched OK" if WebFetch only returns content). Rate-limit ≤ 1 RPS. → `artifacts/url-audit.md` table.
- [ ] **T3.3** For each URL that returned non-2xx, try `https://web.archive.org/web/*/<url>` and record. → same artifact.
- [ ] **T3.4** Patch USE-CASES.md / COMPLIANCE.md: annotate inline with `[archived: ...]` or remove claims that depended on dead URLs. → git diff. ← M3 gate.

## M4 — Human Skill handoff

- [ ] **T4.1** Write `artifacts/M4-human-runbook.md` — a 3-step runbook for the maintainer (copy SKILL.md, open Claude Code, type test prompt). → file.
- [ ] **T4.2** Maintainer follows the runbook (out of AI's reach). → `artifacts/skill-session.md` (pasted by maintainer).
- [ ] **T4.3** AI reviews the session transcript: did the Skill trigger? did the agent call `summary-doctor` with sensible arguments? → assessment in `artifacts/M4-assessment.md`. ← M4 gate.
- [ ] **T4.4** If Skill did NOT trigger, open a v0.2.2 issue ("tune Skill trigger keywords") with the negative-result transcript attached.

## M5 — Release

- [ ] **T5.1** Update `CHANGELOG.md` with v0.2.1 entry. Honest about which gates passed and which were skipped.
- [ ] **T5.2** Bump `pyproject.toml` version `0.2.0` → `0.2.1`.
- [ ] **T5.3** Final redaction grep across full repo. Expected: 0 hits on the redline list.
- [ ] **T5.4** Final pytest run. Expected: all previously passing tests still pass.
- [ ] **T5.5** `git add` only intended files (no `eval/results/`, no `docs/launch/`, no Python `__pycache__`). Commit.
- [ ] **T5.6** `git push origin main`. Tag `v0.2.1`. `gh release create v0.2.1` with notes. ← M5 gate.

## Cross-cutting

- [ ] **TX.1** Every milestone closes with a redaction grep. 0 hits required. (Constitution §4)
- [ ] **TX.2** Any action that mutates remote state (git push, gh release, GitHub API write) requires user confirmation in the running session. (Constitution §5)
- [ ] **TX.3** Artifacts that capture stdio / network traces are scrubbed of hostname / username / API keys before commit.
