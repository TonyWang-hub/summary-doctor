# Changelog

All notable changes to this project are documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] — 2026-05-25

Prompt caching patch. Adds `cache_control` to the Anthropic SDK backend
path, plumbs `usage` from both backends so callers can verify cache hits,
locks prompt-byte stability via a new test file. Built via SDD under
`spec-kit/v0.2.2-caching/` — five milestones, two carify rounds each,
honest documentation of an assumption that was falsified during M0.

### Added

- `AnthropicBackend`: new `cache_ttl` field (default `"5m"`, accepts
  `"1h"` or `None`); passes top-level `cache_control={"type": "ephemeral", "ttl": ...}`
  on every `client.messages.create` call. Cache scope is prompt-prefix
  bytes + model + API key, persists across SDK calls within TTL.
- CLI: `--cache-ttl {5m,1h}` and `--no-cache` flags. Ignored by
  claude-cli and mock backends (which can't control external cache).
- Both backends now expose `last_decompose_usage` and
  `last_classify_usage` (dict | None) — populated after each call.
  Includes `cache_creation_input_tokens` and `cache_read_input_tokens`
  when caching is active.
- `tests/test_cache_prefix.py` — 8 tests locking prefix-byte stability:
  byte-stable rendering of DECOMPOSE_PROMPT / CLASSIFY_PROMPT,
  deterministic tool-schema serialisation, placeholder-set guard, and
  forbidden-token check (no `datetime.now`, `uuid4`, `time.time`,
  `request_id` in any prompt template).
- 44 pytest pass + 5 skipped (was 36 + 5 in v0.2.1).

### Documented (M0 finding worth shipping with the patch)

M0 falsified a load-bearing v0.2.2 spec assumption: **`claude-cli`
backend does NOT cache user-prompt content across invocations**.
Empirically tested — same long prompt sent in two consecutive
`claude -p` invocations produces `cache_read_input_tokens = 0` on the
second call. Claude Code's platform-level system+tools prefix (~36K
tokens) DOES cache cross-invocation, but that is independent of any
`summary-doctor` workload.

Net effect: the Anthropic SDK path (with the new `cache_control`) is
the only path that delivers cross-invocation user-prompt cache reuse
on `summary-doctor` workflows. `claude-cli` users get no workload-level
cache benefit and never did — v0.2.2 documents that honestly rather
than implying otherwise.

See `docs/EVALUATION.md` § Cache performance (v0.2.2) for the empirical
table and `spec-kit/v0.2.2-caching/milestones/M0-baseline-closeout.md`
for the three-test evidence trail.

### Deferred (honest gap)

The Anthropic SDK code path is wired but **not yet verified with a real
API call**. The maintainer chose to ship the code with a reproduction
runbook (`spec-kit/v0.2.2-caching/artifacts/M2-reproduction-runbook.md`)
rather than block release on a $0.20 API budget. Same honest-gap pattern
as v0.2.1 M4 SKIPPED.

If you have an `ANTHROPIC_API_KEY` and ~10 minutes, the runbook produces
the missing `cache_read_input_tokens > 0` evidence and unlocks a v0.2.2.1
patch that fills in the empty EVALUATION row.

### Known limits (rolled forward)

- DECOMPOSE prompts are often <4096 tokens (Haiku 4.5 cache minimum).
  Caching silently no-ops below that threshold; CLASSIFY prompts
  usually clear it once a non-trivial source is included.
- Python 3.14 still not supported by the `mcp` Python SDK 1.27.1 — use
  Python 3.10-3.13 for the `[mcp]` extra. (Same as v0.2.1.)

## [0.2.1] — 2026-05-20

Dogfood patch release. v0.2.0 shipped MCP server + Skill manifest + 21
documentation URLs, none of which had been exercised end-to-end. This
release closes that gap and fixes a real bug uncovered during the
process. Built using a Spec-Driven Development (SDD) workflow with all
artefacts versioned under `spec-kit/v0.2.1-dogfood/`.

### Fixed

- **MCP `audit_summary` tool crashed on non-trivial inputs.** The tool
  was passing raw summary / source text into `Pipeline.run()` as a
  `_ref`, which then called `Path(text).exists()`. On macOS APFS a
  filename longer than 255 bytes raises `OSError 63 (File name too
  long)` inside `stat()` instead of returning `False`, so any real
  summary (>255 chars) errored out before reaching the pipeline.
  Fixed by materialising the raw strings into
  `tempfile.NamedTemporaryFile`s and passing the paths in. Pipeline
  semantics unchanged. v0.2.0 shipped with this bug because the v0.2.0
  MCP tests only checked schema and registration, not end-to-end
  behaviour.

### Verified

| Gate | Status | Evidence |
|---|---|---|
| `pip install -e '.[mcp]'` on supported Python (3.10–3.13) | ✅ | M1 in a Python 3.12 venv |
| 5 previously-skipped MCP tests | ✅ 5/5 → 12/12 | `artifacts/M1-install-and-smoke.md` |
| MCP stdio round-trip end-to-end | ✅ 3635-char report, Divergence 0% on demo 03 | `artifacts/mcp-stdio-trace.json` |
| 21 USE-CASES + COMPLIANCE URLs reachable | ✅ 17 direct 2xx + 4 archived via Wayback | `artifacts/url-audit.md` |
| Skill manifest triggered in a live Claude Code session | ⏭ **SKIPPED** | `artifacts/skill-session.md` — maintainer chose not to run; structural lint (12/12 mcp pytest) only |

### Added (the SDD trail)

- `spec-kit/v0.2.1-dogfood/` — full SDD record committed alongside the
  release: spec, plan, tasks, constitution, MOC, five milestone
  close-outs, captured stdio trace, URL audit table, human runbook.
- `docs/USE-CASES.md` — four URLs (Justia docket, ABA Op. 512, NewsGuard
  monitor, Seyfarth ChatGPT-case update) annotated with their Wayback
  Machine snapshots. The original anti-bot / timeout responses are
  documented in `artifacts/url-audit.md`.

### Known limits (rolled forward)

- M4 skipped: Skill manifest trigger keywords are NOT exercised
  end-to-end in a live Claude Code session. Re-runnable via
  `spec-kit/v0.2.1-dogfood/artifacts/M4-human-runbook.md`. A
  v0.2.2 issue may be filed once this is run.
- Python 3.14 is NOT supported by the `mcp` Python SDK (1.27.1).
  Use Python 3.10 / 3.11 / 3.12 / 3.13 for the `[mcp]` extra.

## [0.2.0] — 2026-05-19

Distribution layer + use-case & compliance docs. Decided after a three-route
deep-research synthesis (commercial competitors / domain pain / ecosystem
integration); the bet is that **distribution beats new features** at this
stage and the moat is "0 direct competitors on the 4-label + citations
form factor".

### Added

#### MCP server + Claude Code Skill (distribution layer)

- `src/summary_doctor/mcp_server.py` — FastMCP wrapper exposing three tools
  - `audit_summary(summary, source, lang, backend, model) -> markdown report`
  - `get_demo(demo_name) -> {summary, source, readme, expected_labels}`
  - `list_labels() -> dict` (the four-label taxonomy with usage hints)
- `skills/summary-doctor/SKILL.md` (1.5 KB) — Claude Code Skill manifest with
  positive + negative triggers; `skills/summary-doctor/README.md` covers
  install paths (`~/.claude/skills/` global vs project-local `.claude/skills/`)
- `pyproject.toml`: new `[project.optional-dependencies] mcp = ["mcp>=0.9.0"]`
  and `[project.scripts] summary-doctor-mcp = "summary_doctor.mcp_server:main"`
- README + zh-README: "MCP server" + "Claude Code Skill" sections with
  Claude Desktop / Cursor / Zed / Continue.dev config snippets

#### Two new demos (12 → 14)

- `demos/13-academic-peer-review-en/` — synthetic literature-review case
  surfacing fabricated citations + reversed findings + softened scope
- `demos/14-legal-mata-style-en/` — synthetic federal-court sanctions order
  case surfacing fabricated case citations + reversed holding

Both demos are 100% synthetic content. Their `README.md` files link out to
real public events (Stanford peer-review AI-modification study, Mata v.
Avianca docket #54, ABA Formal Opinion 512, etc.) only as background.

#### Public docs

- `docs/USE-CASES.md` — three case studies (academic peer review / legal /
  news) with ≥2 independent public sources per case + 4-label mappings +
  CLI snippets + links to the matching demos
- `docs/COMPLIANCE.md` — regulatory crosswalk: EU AI Act Articles 13 / 15 / 50,
  NIST AI RMF MEASURE + MANAGE (with GenAI Profile NIST-AI-600-1
  confabulation sub-item), SEC 2026 Examination Priorities, China
  *Interim Measures* Articles 4 / 8 / 17 + GB/T 45654-2025 / 45674-2025
- Disclaimer in COMPLIANCE.md states this is engineering reference, not
  legal advice, and not a product claim

### Changed

- README first-screen banner reflects "14 demos" (was "9 demos")
- Tests: 27 → 36 passing (+5 skipped when `mcp` package not installed) —
  added MCP smoke tests and demo-13/14 high-signal invariants

### Decisions deliberately deferred

- Chrome extension → v0.4 (MV3 + Chrome Web Store review + Native Messaging
  Host on Windows is a tarpit; bookmarklet + local daemon is the cheaper
  alternative)
- Compliance audit-report SaaS productisation → v0.3+ pending traction
- Cross-language alignment → v0.2 included as a forward-looking demo only;
  proper alignment lands in a later release

### Known limits (rolled forward from v0.1)

- Causal-direction inversion remains Haiku's weakest mode; recommend
  `--model opus` (or claude-cli with opus) for cases where causal-flip is
  in scope.
- `claude-cli` backend Haiku occasionally emits invalid JSON on long
  Chinese sources — opus first-try succeeds on those cases; documented in
  `docs/EVALUATION.md`.

## [0.1.0] — 2026-05-19

First public release.

### Added

#### Core pipeline

- Five-stage pipeline: **input → extract → decompose → map+classify → report**
- Four-class label taxonomy: `exact` / `softened` / `reversed` / `fabricated`
- Markdown + JSON dual output with confidence and rationale per claim
- Citation-map output design (the tool does not emit verdicts — it maps each claim back to a source paragraph and leaves the call to the reader)

#### Backends (3)

- **Mock** — heuristic pipeline-tester, no API key, offline, deterministic. Designed for CI smoke tests and pipeline regression detection.
- **Anthropic SDK** — production path via the `anthropic` Python SDK. Uses `tool_use` structured output (forces well-formed JSON via `tool_choice`), exponential-backoff retry on rate-limit / overload, and one-shot Haiku → Opus model fallback on structural failure.
- **Claude CLI** — shells out to `claude -p` to reuse a Claude Code subscription. $0 marginal cost. Three-layer JSON tolerance (envelope → fence → balanced bracket scan), 120 s default timeout.

#### CLI

- Positional `summary` (file path / URL / stdin), required `--original` (source), optional `--lang`, `--out`, `--model`, `--backend`, `--mock`
- Exit codes: `0` success, `1` pipeline failure, `2` source unfetchable

#### Demos (12 bundled, all synthetic)

| # | Demo | Failure mode |
|---|---|---|
| 01 | `01-reversal-en` | Reversed claims + a fabricated GPU-supply red herring |
| 02 | `02-softening-zh` | Softened qualifiers + one reversed claim |
| 03 | `03-faithful-en` | Positive control — should produce mostly `exact` |
| 04 | `04-cherry-picking-en` | Cherry-picking — softened by dropping qualifiers |
| 05 | `05-causal-inversion-zh` | Causal direction flipped (X → Y vs Y → X) |
| 06 | `06-scope-creep-en` | Scope creep — narrow finding stated as universal |
| 07 | `07-temporal-error-en` | Year / date fabricated outside source |
| 08 | `08-fabricated-stats-zh` | Numeric statistics invented |
| 09 | `09-faithful-zh` | Chinese positive control |
| 10 | `10-quote-out-of-context-en` | Verbatim quote with qualifying clause removed |
| 11 | `11-number-exaggeration-zh` | 10× magnitude exaggeration (8% → 80%) |
| 12 | `12-cross-language-en-zh` | EN source + ZH summary (v0.2 forward-looking case) |

All demo data is synthetic; any resemblance to specific real speakers, talks, or organisations is unintended.

#### Tooling

- `demos/run-demo.sh` — auto-discovers every demo directory under `demos/`, runs the full set in mock mode with coloured headlines and a summary table
- `eval/run-eval.py` — reproducible mock-vs-claude-cli comparison with per-demo label distribution
- `make self-audit-mock` / `make self-audit` / `make self-audit-opus` — three cost/fidelity tiers for auditing the project's own README against `SPEC.md` + `ROADMAP.md`

#### Documentation

- `README.md` + `README.zh-CN.md` (bilingual)
- `docs/SPEC.md` — full design rationale and state machine
- `docs/ROADMAP.md` — v0.1 / v0.2 / v0.3 plans
- `docs/PROMPT-ENGINEERING.md` — design principles, the softened↔reversed boundary, "bad prompt smells", how to change a prompt safely
- `docs/EVALUATION.md` — methodology + mock-vs-claude-cli numbers across the 12-demo set
- `docs/MOCK-LIMITS.md` — failure modes of the mock heuristic, why it should never be used for real audits
- `docs/SELF-AUDIT.md` — how to run, how to read the report, known limits
- `docs/RECORDING-GIF.md` — how to re-record `docs/demo.gif`

#### Prompt design

- `DECOMPOSE_PROMPT`: 2 worked examples + atomic-claim rules
- `CLASSIFY_PROMPT`: **6 worked examples** (one for each label, plus two reversed cases — English negation flip and Chinese causal-direction flip) and an explicit softened-vs-reversed boundary rule

#### Quality gates

- 27 pytest cases: 9 high-signal demos × invariants, 2 positive controls, cross-language smoke, 11 prompt-shape tests, plus back-compat
- CI: GitHub Actions matrix on Python 3.10 / 3.11 / 3.12
- Issue templates: bug-report, feature-request, demo-case (for calibration-sample submission)
- Pull-request template with redaction checklist

### Known limits

- `claude-cli` backend can produce JSON-parse failures on long Chinese sources with Haiku; the documented fix is `--model opus`.
- Causal-direction inversion is the model's hardest failure mode; the Haiku prompt covers it explicitly but recall is still below the other classes (see `docs/EVALUATION.md`).
- Cross-language alignment (EN source + ZH summary, or vice versa) is a forward-looking demo only — v0.2 work item.
- Mock self-audit on README routinely reports ~60% divergence; this is an artefact of running a sentence-boundary heuristic over Markdown that was never structured as a summary-source pair. See `docs/SELF-AUDIT.md`.

### Security and privacy

- All demo data is synthetic. No real-person or company references anywhere in the repository.
- `docs/launch/` (private promotion material) is `.gitignore`d.
- The Claude CLI backend never logs the user's prompt or response text; all I/O is in-process.

[0.2.2]: https://github.com/TonyWang-hub/summary-doctor/releases/tag/v0.2.2
[0.2.1]: https://github.com/TonyWang-hub/summary-doctor/releases/tag/v0.2.1
[0.2.0]: https://github.com/TonyWang-hub/summary-doctor/releases/tag/v0.2.0
[0.1.0]: https://github.com/TonyWang-hub/summary-doctor/releases/tag/v0.1.0
