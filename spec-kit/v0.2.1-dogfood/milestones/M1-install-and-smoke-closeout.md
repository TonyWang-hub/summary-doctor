# M1 — MCP install + smoke · close-out

**Status**: ✅ passed (with deviation from spec §8 open assumption #3)
**Wall clock**: 4 min
**Artifact**: `artifacts/M1-install-and-smoke.md`

## Carify round 1 — engineer's view

**Concurrency / asyncio**: FastMCP uses asyncio internally. The smoke tests do not stress this — they only verify import + registration. Stress-testing the async loop is M2's job.

**Python version compatibility**: spec §8 open assumption #3 was naïve. The right thing to do was check supported Python versions *before* writing pyproject `mcp>=0.9.0`. We escaped because a 3.12 was already on the box.

**Environment isolation**: deliberately used `/tmp/sd-mcp-venv` instead of `--break-system-packages` so the system 3.14 install stays clean.

## Carify round 2 — tester's view

**Boundary**: `build_server()` invoked with `mcp` package present (passes) and absent (also passes, by raising clearly). Both paths exercised by tests 6/7 vs 8.

**Recovery**: if the install failed mid-way (partial extras), tests 6/7 would still pass (designed to detect a missing `mcp`). The clean-vs-broken state diff was observable.

**Observability**: every step was captured to the run log (`M1-install-and-smoke.md`). Re-running the milestone is deterministic.

## Gate verification

✅ 5 previously-skipped tests now pass.
✅ Install reproducible from spec §8 assumption falsification → §2 decision.
✅ Zero source-code patches needed (T1.5 a no-op).

## Deviation logged

- **Spec §8 assumption #3 was wrong**: mcp does NOT support Python 3.14. Action: M3 must add a note to README ("MCP support requires Python 3.10–3.13").

## Findings carried forward

- M2 uses `/tmp/sd-mcp-venv/bin/python` with `PYTHONPATH=src` to spawn the MCP server.
- README needs a Python-version-constraint note for the MCP section (queued for M3 doc patches).
- 5 → 0 skipped is the M5 release-note delta. Note in CHANGELOG.

## Redaction grep (constitution §4)

`grep -riE` of the redline set across `spec-kit/v0.2.1-dogfood/` files added/edited in M1 (M1 close-out + artifact) → 0 hits.

## Next

→ M2 (stdio dogfood). Plan: write a minimal stdio JSON-RPC client at `artifacts/mcp-stdio-client.py`, spawn `summary-doctor-mcp` via the venv, run one real `audit_summary` round-trip against demo 03.
