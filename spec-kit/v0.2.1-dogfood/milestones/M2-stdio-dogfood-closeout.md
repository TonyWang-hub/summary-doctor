# M2 — MCP stdio dogfood · close-out

**Status**: ✅ passed (after a real bug fix)
**Wall clock**: ~30 min
**Artifacts**: `artifacts/mcp-stdio-client.py`, `artifacts/mcp-stdio-trace.json`

## Carify round 1 — engineer's view

The MCP `mcp` client SDK already wraps the stdio JSON-RPC dance behind `ClientSession.initialize() / list_tools() / call_tool()`. We deliberately used the SDK rather than hand-rolling JSON-RPC frames because:

1. The goal is to exercise the **same** code path a real Claude Desktop client would use, not to test our framing parser.
2. The SDK already enforces protocol-version negotiation, which catches version-drift bugs early.
3. The SDK is what every published MCP server example uses; if a downstream contributor copy-pastes a client, they will use the SDK.

Timeouts: 10s per stdio call (`asyncio.wait_for`); 30s for `tools/call` because the pipeline involves decompose + classify even on the mock backend.

Spawn vector: `command=/tmp/sd-mcp-venv/bin/python`, `args=["-m", "summary_doctor.mcp_server"]`, `env={"PYTHONPATH": "<repo>/src"}`. Deliberately bypassed the `summary-doctor-mcp` shim entry point so the trace is unambiguous about which interpreter ran.

## Carify round 2 — tester's view

Boundary cases:
- Empty stdin: not exercised; the SDK opens stdio without sending raw bytes first. ✅
- Long input: the demo 03 summary is 350 chars / source 596 chars. This itself **uncovered the real bug** (see §"Bug captured" below).
- Async cleanup: `stdio_client` context manager guarantees subprocess cleanup. Verified by running the client twice in a row — no zombie processes.

Recovery:
- The first run captured an actual error frame (`is_error=true`, `[Errno 63] File name too long`). We did NOT retry blindly per `02-tasks.md` T2.5: "fix `mcp_server.py` (not the test, not the client)". The fix was a one-paragraph patch to the `audit_summary` tool.
- Second run produced the expected 0%-divergence report on demo 03.

Observability: trace file is JSON, hostname/user-scrubbed before write (defense in depth in `mcp-stdio-client.py:scrub_machine_fingerprints`).

## Bug captured (real value of this milestone)

**Symptom**: first stdio run returned `is_error=true` with content `[Errno 63] File name too long: 'The author describes a three-stage evaluation framew...'`.

**Root cause**: `audit_summary` MCP tool was passing raw text as `summary_ref` / `source_ref` into `Pipeline.run()`, which then called `Path(raw_text).exists()`. On macOS APFS, `Path.exists()` calls `stat()` and `stat()` raises `OSError 63` (file name too long) for any filename > 255 bytes instead of returning False. A 350-char summary blob is well past that limit.

This was **shipped in v0.2.0** undetected because no test exercised the MCP tool end-to-end on a non-trivial input. The skipped MCP tests in v0.2.0 only checked schema and registration, not behaviour.

**Fix** (applied to `src/summary_doctor/mcp_server.py:audit_summary`):
- Materialise the raw `summary` and `source` strings into `tempfile.NamedTemporaryFile`s,
- Pass the file paths to `pipeline.run()`,
- Clean up the temp files in a `try/finally`.

We did NOT change `pipeline.run()` itself — its `_ref` semantics (path / URL / `-` for stdin) are correct for the CLI; the MCP layer is just the adapter.

## Gate verification (spec §3.1)

| Criterion | Result |
|---|---|
| `summary-doctor-mcp` binds stdio listener | ✅ subprocess spawned, no crash |
| `initialize` handshake completes | ✅ protocol_version 2025-11-25, server_name "summary-doctor" |
| `tools/list` returns the 3 documented tools | ✅ `[audit_summary, get_demo, list_labels]` |
| `audit_summary` returns markdown report | ✅ 3635 chars |
| Divergence score 0% on demo 03 positive control | ✅ `- Divergence score: **0%**` |
| Trace captured for reproducibility | ✅ `artifacts/mcp-stdio-trace.json` |

## Redaction grep (constitution §4)

`grep -riE` of the redline set on `spec-kit/v0.2.1-dogfood/artifacts/` (the new files added this milestone) → 0 hits.

The scrub-on-write hook in `mcp-stdio-client.py` (`scrub_machine_fingerprints`) replaces `$HOME`, `$USER`, and `/Users/` with `[scrubbed]` to keep the trace shareable.

## Carry-forward

- M5 release note: v0.2.1 fixes a v0.2.0 MCP-server crash on non-trivial inputs. Frame this honestly as "the MCP tool was never exercised end-to-end before v0.2.1".
- The fix used `tempfile` not `stdin` because MCP itself owns the process stdin. Worth a one-line comment in the code (already added).
- M3 (URL audit) is the next milestone; can run independently.

## Next

→ M3 (URL audit).
