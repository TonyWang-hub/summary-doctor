# v0.2.1 dogfood — Spec

> **Goal**: turn the implementation-status gap honestly identified at the end
> of v0.2.0 ("code written, never dogfooded") into a v0.2.1 patch release
> where every claim in the README about MCP / Skill / docs is backed by
> an actual run.
>
> **Scope**: only the dogfood gap. No new features. No new demos. No new
> docs. Tighten what already exists.
>
> **Anti-scope**: anything from v0.3 (Obsidian plugin, evidence-pack PDF,
> Phoenix/Ragas/DeepEval adapters, etc.) — deferred.

## 1. The three problems we solve

| # | Problem | Acceptance criterion |
|---|---|---|
| 1 | The MCP server has never actually started. We don't know whether `summary-doctor-mcp` binds stdio, whether `audit_summary` returns a valid markdown report end-to-end, or whether tool schemas are accepted by an MCP client. | (a) `pip install -e '.[mcp]'` succeeds; (b) the 5 currently-skipped MCP pytest cases pass; (c) a minimal stdio client (NOT Claude Desktop) successfully invokes `audit_summary` against demo 03 and gets back a markdown report whose `divergence_score` is 0%. |
| 2 | The Skill manifest at `skills/summary-doctor/SKILL.md` has never been loaded by Claude Code. We don't know whether the trigger keywords are right, whether `allowed-tools` is honoured, or whether the description fits in the Skill discovery surface. | A documented Claude Code session log showing the Skill being invoked on a synthetic prompt and the agent calling `summary-doctor` with sensible arguments. Logged to `spec-kit/v0.2.1-dogfood/artifacts/skill-session.md`. **Must be run by the human maintainer** — Claude Desktop / Claude Code cannot be driven from inside this agent process. |
| 3 | USE-CASES.md cites 15 URLs and COMPLIANCE.md cites 6+; none have been click-verified by the maintainer. Broken citations directly contradict our own "citations, not verdicts" claim. | Every URL in USE-CASES.md and COMPLIANCE.md returns HTTP 2xx (or 3xx → 2xx) on `WebFetch`, OR is explicitly flagged as "archived / paywalled / region-locked" in the doc itself. |

## 2. State machine

```
[M0 baseline]  →  [M1 mcp install + smoke]  →  [M2 mcp stdio dogfood]  →  [M3 doc url audit]  →  [M4 human handoff]
       │                  │                          │                          │                        │
   git clean         pip extras OK             one real round-trip       URLs verified or flagged    user runs Skill in CC
       │                  │                          │                          │                        │
       └──────────────────┴──────────────────────────┴──────────────────────────┴────────────────────────┘
                                                 │
                                          [M5 v0.2.1 release]
                                                 │
                                            tag + notes
```

Each milestone has a specific **gate** that must pass before the next starts.

## 3. Interface contracts (what gets dogfooded)

### 3.1 MCP server stdio contract

The MCP server speaks JSON-RPC 2.0 over stdio per the Model Context Protocol spec. The minimal handshake we test:

```jsonc
// → server  (initialize)
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"sd-dogfood","version":"0.0.1"}}}
// ← server
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{...},"serverInfo":{...}}}

// → server  (tools/list)
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
// ← server
{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"audit_summary",...},{"name":"get_demo",...},{"name":"list_labels",...}]}}

// → server  (tools/call)
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"audit_summary","arguments":{"summary":"...","source":"...","lang":"en","backend":"mock"}}}
// ← server
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"# Summary Audit Report ..."}]}}
```

### 3.2 Skill manifest contract

A Claude Code session that mentions phrases like *"audit this AI summary"* or *"check if this summary is faithful"* should auto-load `skills/summary-doctor/SKILL.md` and propose calling the `summary-doctor` CLI with appropriate arguments.

### 3.3 URL audit contract

For each URL cited in USE-CASES.md and COMPLIANCE.md, one of:
- HTTP 2xx → kept as-is
- HTTP 3xx → final destination is 2xx → kept as-is
- HTTP 4xx / 5xx / timeout → replaced with a primary alternative OR flagged
- Paywall / region-lock → annotated inline with `[paywalled]` / `[region-locked]`

## 4. Failure paths

| Failure | Recovery |
|---|---|
| `pip install '.[mcp]'` fails on Python 3.14 | downgrade `mcp` constraint OR document Python 3.10-3.12 support window in README |
| `mcp` package import works but FastMCP signature changed | pin `mcp>=0.9,<1.0` AND update `mcp_server.py` to match |
| Stdio handshake hangs | wrap subprocess call in 10s timeout, log stderr, report which method blocked |
| `audit_summary` returns malformed markdown | this is a real bug — fix `mcp_server.py` then re-run M2 |
| A URL in USE-CASES.md is 404 | first try `web.archive.org` snapshot; if that fails, replace with a primary alternative; if no alternative, remove the claim that relied on it |
| Human Skill dogfood (M4) impossible (no Claude Code on machine) | downgrade to "Skill manifest validated by structural lint only" and document the gap in CHANGELOG honestly |

## 5. Out of scope (v0.2.1)

- Obsidian plugin
- Chrome extension
- Evidence-pack PDF generator
- Phoenix / Ragas / DeepEval adapter
- Cross-language alignment
- New demos
- Anything from B-path SaaS plans

These are v0.3+ items per `docs/launch/research/00-synthesis.md`.

## 6. Carify rounds (per Constitution §2)

### Round 1 — engineer's view (concurrency / timeouts / interfaces)
- `mcp` package may use `asyncio`; need to confirm whether `mcp_server.py` mixes sync and async safely.
- Stdio subprocess with `subprocess.Popen` + thread-based read loop — must guard against EOF on either pipe.
- `summary-doctor-mcp` entry point: does it inherit env (e.g. `ANTHROPIC_API_KEY`)? For dogfood we use `backend="mock"` so no key needed.
- URL audit must respect `robots.txt` and rate-limit (≤ 1 RPS).

### Round 2 — tester's view (boundaries / recovery / observability)
- Boundary: empty stdin (server shouldn't crash).
- Boundary: malformed JSON-RPC frame (server should reply with error code, not exit).
- Recovery: kill -9 server — pytest fixture must cleanup.
- Observability: each stdio frame logged to artifacts/ for replay; URLs and HTTP codes recorded.

## 7. Deliverables

By the end of M5:
- `pyproject.toml` `[mcp]` extras installable on the current Python.
- `tests/test_mcp_server.py` — 0 skipped (was 5 skipped because of missing `mcp`).
- `spec-kit/v0.2.1-dogfood/artifacts/mcp-stdio-trace.json` — captured stdio frames from M2.
- `spec-kit/v0.2.1-dogfood/artifacts/url-audit.md` — per-URL HTTP status.
- `spec-kit/v0.2.1-dogfood/artifacts/skill-session.md` — only if human ran M4; otherwise documented gap.
- `CHANGELOG.md` v0.2.1 entry, honest about which parts were dogfooded by AI vs human.
- GitHub Release v0.2.1.

## 8. Open assumptions (to validate before M1 starts)

1. `mcp>=0.9.0` actually pins the Python SDK package on PyPI (NOT a name collision).
2. FastMCP's `Server.run_stdio()` (or equivalent) does not require an event loop already running.
3. Python 3.14 (currently installed) is supported by the `mcp` Python SDK. If not, M1 includes downgrading to a venv on 3.12.
