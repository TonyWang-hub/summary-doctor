# v0.2.2 caching — Tasks

Granular checklist. Each task is independently executable with a single verifiable output.

## M0 — Baseline

- [ ] **T0.1** Confirm ANTHROPIC_API_KEY is available in the session env. `! export ANTHROPIC_API_KEY=sk-ant-...` if not.
- [ ] **T0.2** Verify `/tmp/sd-mcp-venv/bin/pip show anthropic` shows ≥0.40. If absent, `pip install 'anthropic>=0.40'` in the venv.
- [ ] **T0.3** Run `summary-doctor README.md --original <SPEC+ROADMAP cat> --lang en --backend anthropic` twice without any cache_control. Capture both `response.usage` blocks. → `artifacts/M0-baseline-no-cache.json`. ← M0 gate.

## M1 — cache_control wiring

- [ ] **T1.1** Add `cache_ttl: Literal["5m","1h"] | None = "5m"` field to `AnthropicBackend`. Default 5m.
- [ ] **T1.2** Update both decompose and classify call sites in `anthropic.py` to pass top-level `cache_control={"type": "ephemeral"}` (+ `"ttl": "1h"` when `cache_ttl == "1h"`).
- [ ] **T1.3** Add `--cache-ttl` and `--no-cache` flags to `cli.py`. Thread through `get_backend`.
- [ ] **T1.4** Update `backends/__init__.py` `get_backend` signature to accept and forward `cache_ttl`.
- [ ] **T1.5** Write `tests/test_cache_prefix.py` with three tests: decompose byte-stability, classify byte-stability, tool schema deterministic serialisation.
- [ ] **T1.6** Run `pytest tests/ -q` — all green (36+ tests).
- [ ] **T1.7** Run `summary-doctor --help` — verify new flags appear. ← M1 gate.

## M2 — Cache-hit verification

- [ ] **T2.1** Patch `eval/run-eval.py` to surface `cache_creation_input_tokens` and `cache_read_input_tokens` per run in its JSON output. Tiny diff.
- [ ] **T2.2** Run two consecutive `summary-doctor` invocations on README → (SPEC+ROADMAP), with `--backend anthropic --cache-ttl 5m`. Capture each `response.usage`.
- [ ] **T2.3** Write `artifacts/M2-cache-hit-trace.json` containing both calls' usage blocks + computed ratio.
- [ ] **T2.4** Verify second call's classify usage shows `cache_read_input_tokens > 0`. ← M2 gate.
- [ ] **T2.5** If T2.4 fails: capture full request bodies of both calls to `artifacts/M2-prefix-diff/{call1,call2}.txt`. Bisect for invalidator byte. Fix and re-run T2.2-T2.4.

## M3 — EVALUATION + docs

- [ ] **T3.1** Add "Cache performance" section to `docs/EVALUATION.md`. Numbers from T2.3 artefact verbatim.
- [ ] **T3.2** Add "Don't break the cache prefix" addendum to `docs/PROMPT-ENGINEERING.md`. Link `shared/prompt-caching.md` external reference.
- [ ] **T3.3** Add one-line caching mention to README's "Mock vs Anthropic" decision table. Mirror to `README.zh-CN.md`.
- [ ] **T3.4** Update `CHANGELOG.md` with v0.2.2 entry including the M2 number. ← M3 gate.

## M4 — Release

- [ ] **T4.1** Bump `pyproject.toml` version 0.2.1 → 0.2.2.
- [ ] **T4.2** Final redaction grep across all changed files. 0 hits.
- [ ] **T4.3** Final `pytest tests/ -q` — all green.
- [ ] **T4.4** AskUserQuestion for push authorization (per constitution §5).
- [ ] **T4.5** `git add` only the v0.2.2 changes. Commit.
- [ ] **T4.6** `git push origin main`.
- [ ] **T4.7** `git tag v0.2.2`. Push tag.
- [ ] **T4.8** `gh release create v0.2.2` with notes containing the M2 cache-hit number. ← M4 gate.

## Cross-cutting

- [ ] **TX.1** Each milestone closes with a redaction grep. 0 hits required. (Constitution §4)
- [ ] **TX.2** M4 push/tag/release require explicit user authorization. (Constitution §5)
- [ ] **TX.3** Constitution §7 — M2 gate is `cache_read > 0` measured, not `code compiles`. No proxy signals.
