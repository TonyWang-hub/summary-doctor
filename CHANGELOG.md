# Changelog

All notable changes to this project are documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.2.0]: https://github.com/TonyWang-hub/summary-doctor/releases/tag/v0.2.0
[0.1.0]: https://github.com/TonyWang-hub/summary-doctor/releases/tag/v0.1.0
