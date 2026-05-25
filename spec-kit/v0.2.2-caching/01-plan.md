# v0.2.2 caching — Plan

5 milestones, ~3-5 hours AI + ~20 min human. Each has a single gate; no milestone starts until the previous one passes.

## M0 — Baseline cost capture

**Goal**: capture token usage for a single self-audit run **without** caching, so we have a delta to measure against in M3.

**Carify R1**: which scenario reflects the repeat-source workflow most honestly? Answer: running `make self-audit` (which audits README against SPEC+ROADMAP using claude-cli) twice in a row. But claude-cli doesn't surface cache usage. So we run the *Anthropic SDK backend* on the same README/SPEC+ROADMAP pair twice — that's the true measurement substrate.

**Carify R2**: small risk that someone reads M0 numbers as "the price of v0.2.1" and freaks out. Annotate the artefact: this is one specific repeat-source scenario, not a typical audit.

**Rev 2 — M0 uses claude-cli; no API key required.**

**Actions**:
1. Probe `claude -p --output-format json` once with a small prompt to confirm `result.usage.cache_*` fields are present in the envelope.
2. Capture the raw JSON envelope of a single audit against `(README, SPEC+ROADMAP)` via claude-cli (haiku) — this is the "before plumbing" baseline. The `result` text we already use; the `usage` block is what we plumb in M1.
3. Run a second audit on the same pair. Compare usage numbers. **Expect**: call 1 has `cache_creation > 0`, call 2 has `cache_read > 0` (Claude Code is already auto-caching). If both calls show `cache_read = 0`, that itself is the finding — document it.
4. Save both raw envelopes to `artifacts/M0-baseline-claude-cli.json`.

**Gate**: M0 artifact exists; the `usage.cache_*` field structure is confirmed accessible from outside the SDK; baseline numbers recorded.

**Effort**: 15-20 min AI + 0 min human.

## M1 — plumbing + cache_control wiring

**Goal**: add `cache_control` to both AnthropicBackend calls; add CLI flag; add prefix-byte guard test.

**Carify R1**: top-level vs manual placement? Top-level — see spec §3.2.
**Carify R1**: 5min vs 1h default? 5min — see spec §3.3.
**Carify R2**: how do we prevent a future contributor from adding `datetime.now()` to a prompt and silently breaking caching? `tests/test_cache_prefix.py` renders both prompts twice, asserts byte-identical output.
**Carify R2**: what if the CLI flag is `--no-cache`? Make sure pytest still works (mock backend ignores cache flags; AnthropicBackend honours them).

**Rev 2 — M1 now does both plumbing (claude-cli usage extraction) and Anthropic SDK cache_control.**

**Actions**:
1. `claude_cli.py._invoke`: alongside extracting `result.result` text, also extract `result.usage` from the same envelope item. Set `self.last_decompose_usage` / `self.last_classify_usage` on the backend instance (side channel — don't change `decompose()` / `classify()` return signatures).
2. `Pipeline`: expose backend's `last_usage` snapshot on `Report` so it lands in JSON sidecar.
3. `AnthropicBackend.__init__`: add `cache_ttl: Literal["5m", "1h"] | None = "5m"` field. `None` = caching disabled.
4. `AnthropicBackend._call_with_fallback` (or the two callers): if `self.cache_ttl is not None`, pass top-level `cache_control={"type": "ephemeral", "ttl": "1h" if self.cache_ttl == "1h" else None}` (omit `ttl` for 5m default per SDK convention). Also capture `response.usage.cache_*` into `last_usage` for parity.
5. `cli.py`: add `--cache-ttl {5m,1h}` and `--no-cache` flags. Threaded only into anthropic backend (claude-cli ignores; that's fine).
6. `backends/__init__.py`: thread `cache_ttl` through `get_backend`.
7. `tests/test_cache_prefix.py`: new file. Three tests:
   - `test_decompose_prompt_bytes_stable`: render DECOMPOSE_PROMPT twice with same inputs, assert byte-equal.
   - `test_classify_prompt_bytes_stable`: same for CLASSIFY_PROMPT.
   - `test_tool_schemas_serialise_deterministically`: `json.dumps(CLAIM_AUDIT_TOOL_SCHEMA, sort_keys=False)` twice, assert equal.
8. `tests/test_mcp_server.py` + `tests/test_pipeline_mock.py` still pass (mock backend doesn't see cache flag).

**Gate**: pytest passes; `python -m summary_doctor --help` shows the new flags; claude-cli backend captures `last_usage` after a real call (verified in M2).

**Effort**: 90-120 min AI.

## M2 — Cache-hit verification (Anthropic SDK, primary post-rev3)

**Goal**: prove `cache_read_input_tokens > 0` on the second `summary-doctor` invocation against the same source, captured to a JSON artefact. Verification via **Anthropic SDK** (needs API key, ≤$0.20). Claude-cli path can only show platform-level cache (not workload cache, per M0).

**Carify R1**: which call do we cache-verify on? Both decompose and classify — but classify is the one likely above 4096 tokens. Decompose may silently no-op. Document both honestly.
**Carify R1**: do we use the venv from v0.2.1-dogfood/M1 (`/tmp/sd-mcp-venv`)? Yes if anthropic is installed there; otherwise fresh install.
**Carify R2**: what if cache_read is 0 across both stages? That's the silent-invalidator path — capture request bodies, diff them, find the byte difference.
**Carify R2**: budget cap? We expect <$0.20 total. Bail if cost approaches $1.

**Rev 3 — uses Anthropic SDK; requires API key (~$0.20 budget).**

**Actions**:
1. Activate M1 code changes locally (plumbing + new test + cache_control wiring).
2. User exports `ANTHROPIC_API_KEY` to session.
3. Install `anthropic` SDK in working venv if not present: `pip install 'anthropic>=0.40'`.
4. Run two consecutive `summary-doctor README.md --original /tmp/sd-source.txt --backend anthropic --cache-ttl 5m --model claude-haiku-4-5-20251001`.
5. With M1 plumbing in place, both runs' `usage` is captured on JSON sidecar.
6. Capture both runs' JSON sidecars to `artifacts/M2-cache-hit-trace.json`.
7. Assert: second run's classify-stage `cache_read_input_tokens > 0`. Record the ratio `cache_read / (cache_creation + cache_read + input_tokens)` on call 2.
8. If assertion fails (cache_read == 0): per Constitution §7, this is a real finding not a code bug — capture both request bodies (full text) to `artifacts/M2-prefix-diff/{call1,call2}.txt`, bisect for the byte-level invalidator, fix prompts.py or anthropic.py, re-run. Document the bisection finding in `milestones/M2-*-closeout.md`.
9. Also run claude-cli backend twice for comparison — to demonstrate platform-level cache visible but workload cache absent (the rev-3 honesty point).

**Gate**: `artifacts/M2-cache-hit-trace.json` shows Anthropic SDK classify call-2 `cache_read_input_tokens > 0`. claude-cli call-2 also captured (expected: cache_read same as call-1 platform-level, no workload cache).

**Effort**: 30-60 min AI + 1 min human (export key).

## M3 — EVALUATION delta + docs

**Goal**: turn the M2 numbers into a credible README/EVALUATION row, and document the cache invariants for future contributors.

**Carify R1**: the cost-saving claim — "≥80% on repeat" — needs to be a measurement, not a rounded marketing number. Use the actual M2 ratio.
**Carify R2**: how does this interact with the existing EVALUATION.md "Cross-backend observations"? Add a new subsection — don't restructure the existing tables.

**Actions**:
1. `docs/EVALUATION.md`: new "Cache performance" section with M2 numbers verbatim + interpretation. Note where caching does NOT help (small summaries, decompose stage often <4096 tokens).
2. `docs/PROMPT-ENGINEERING.md`: short addendum "Don't break the cache prefix" — link to `shared/prompt-caching.md` philosophy.
3. `README.md` + `README.zh-CN.md`: one sentence in the "Mock vs Anthropic" table — "Repeat-source workflows benefit from automatic prompt caching (-≥80% on repeat input tokens)."
4. `CHANGELOG.md`: v0.2.2 entry — what shipped, what was deliberately not changed, the captured M2 numbers.

**Gate**: EVALUATION.md numbers match M2 artefact exactly (no rounding hype).

**Effort**: 45-60 min AI.

## M4 — Release

**Goal**: bump version, tag, push, GitHub Release.

**Actions**:
1. `pyproject.toml`: version `0.2.1` → `0.2.2`.
2. Final redaction grep across all changed files.
3. Final pytest run — all green.
4. Commit M1-M3 changes (one or two commits, no mixing of code + spec).
5. `git push origin main` (with `GIT_HTTP_LOW_SPEED_LIMIT=0` if push hangs).
6. Tag `v0.2.2`. Push tag.
7. `gh release create v0.2.2` with notes including the M2 number.

**Gate**: `gh release view v0.2.2` returns a valid URL.

**Effort**: 15 min AI + explicit user authorization for push/tag/release.

## Effort summary

| Milestone | AI time | Human time |
|---|---|---|
| M0 baseline | 15-30 min | 1 min |
| M1 wiring | 60-90 min | 0 |
| M2 verification | 30-60 min | 1 min |
| M3 EVALUATION + docs | 45-60 min | 0 |
| M4 release | 15 min | 5 min (push authorization) |
| **Total** | **~3-4 h** | **~5 min** (only push authorization at M4) |
