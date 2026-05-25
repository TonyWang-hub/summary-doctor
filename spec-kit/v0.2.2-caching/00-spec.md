# v0.2.2 caching — Spec (rev 3)

> **Rev 3 — 2026-05-25 post-M0**: M0 falsified the rev-2 assumption that
> claude-cli silently caches user-prompt content across invocations.
> Empirically: only Claude Code's **platform-level** system+tools prefix
> (~36K tokens) caches cross-invocation; **user-prompt content does
> NOT**. See `milestones/M0-baseline-closeout.md` for the three-test
> evidence trail. Rev 3 corrects §3.6 and re-aims M2 at Anthropic SDK
> verification (only path that can actually deliver user-prompt cache
> reuse on `summary-doctor` workflows). M2 requires an API key; cost
> budget ≤$0.20.



> **Rev 2 — 2026-05-25 restructure.** Claude Code subscription's
> `claude -p --output-format json` envelope already exposes
> `usage.cache_creation_input_tokens` / `cache_read_input_tokens` (see
> §3.6) — the subscription is silently using prompt caching today.
> v0.2.2 therefore restructures to: (a) measure and document the cache
> savings users on the claude-cli backend already get; (b) wire
> explicit `cache_control` on the Anthropic SDK backend so it reaches
> parity; (c) lock prefix-byte stability so future prompt edits don't
> silently break cache. M2 verification runs on claude-cli (free, no
> API key needed); Anthropic SDK manual `cache_control` verification
> becomes a v0.2.3 follow-up.

> **Goal**: in a repeat-source workflow (self-audit, batch re-runs),
> document and measure the ≥80% input-token reduction that the
> claude-cli backend already provides via Claude Code's built-in
> caching, AND wire equivalent `cache_control` on the Anthropic SDK
> backend.
>
> **Scope**: both backends — claude-cli (measure + document existing
> behaviour, plumb `usage` from envelope) + anthropic SDK (add explicit
> `cache_control`).
>
> **Anti-scope**: prompt engineering changes, new demos, RAG/chunking
> for long sources (that's v0.3 P3), per-claim batch CLI flag (separate
> feature).

## 1. The three problems we solve

| # | Problem | Acceptance criterion |
|---|---|---|
| 1 | The Anthropic SDK backend re-sends the full prompt prefix (tools + DECOMPOSE/CLASSIFY system instructions + source text) every audit. For the self-audit workflow (one repo's README+SPEC+ROADMAP audited weekly via three Makefile targets), the same ~3-5K token prefix is reprocessed every run. | A captured `response.usage` showing `cache_read_input_tokens > 0` on the second call of a same-source scenario. Artefact at `artifacts/cache-hit-trace.json`. |
| 2 | The thesis "cost drops ≥80%" is empirical, not architectural. We cannot ship "now with caching!" without a measurement. | `docs/EVALUATION.md` gets a new row showing input_tokens / cache_creation / cache_read totals for: (a) single-call (no cache benefit, +25% writes), (b) repeat-call ≥2 (≥80% read benefit on the prefix portion). Both rows captured from real runs. |
| 3 | Prefix-cache invariants are silent — any byte change before the breakpoint silently returns zero reads, with no error. The implementation needs explicit invariants encoded in code, not assumed. | `tests/test_cache_prefix.py` (new) asserts: (a) DECOMPOSE/CLASSIFY prefix renders bit-identically across calls when only the variable inputs change; (b) tool schemas serialise deterministically (no key reorder); (c) no timestamp/UUID/`json.dumps` without `sort_keys=True` in the rendered prefix. |

## 2. State machine

```
[M0 baseline]  →  [M1 cache_control wiring]  →  [M2 cache-hit verification]  →  [M3 EVALUATION + docs]  →  [M4 release]
       │                  │                            │                              │                       │
   capture pre-      cache_control on              live SDK call shows           EVALUATION.md +         tag + notes
   caching tokens    tools + system blocks         cache_read > 0                README updated
```

Each milestone has a single testable gate.

## 3. Interface contracts (what gets cached)

### 3.1 Prefix structure (rendered order — must not be reordered)

```
┌────────────────────────────────────────────────────────────────┐
│ tools: [CLAIM_LIST_TOOL_SCHEMA] (decompose)                    │ ← cacheable
│ tools: [CLAIM_AUDIT_TOOL_SCHEMA] (classify)                    │ ← cacheable
│ system:  (none — DECOMPOSE/CLASSIFY are user-side)             │
│ messages[0].content[0].text:  DECOMPOSE_PROMPT  with {lang}    │ ← cacheable up to source
│                      .text:  CLASSIFY_PROMPT  with {lang}      │   "Source:" line
│                                              + claims (JSON)   │ ← VARIABLE — cache breakpoint goes BEFORE this
│                                              + source text     │ ← cacheable ONLY when same source is re-audited
│ messages[N].content:  (subsequent turns, none in our case)     │
└────────────────────────────────────────────────────────────────┘
```

Two distinct prefixes need cache breakpoints — one for decompose, one for classify. They run as two separate API calls, so they cache independently.

### 3.2 cache_control placement decision

Per `claude-api` skill authoritative reference, two valid forms:

| Form | When to use |
|---|---|
| **top-level** `cache_control={"type": "ephemeral"}` on `messages.create()` | Default — auto-places on the last cacheable block. Simplest. Use this. |
| **manual** `cache_control` on a specific content block | Only if we need to cache the prefix *up to a specific point* (e.g. cache the prompt but not the source). For v0.2.2 we want to cache *up to and including* the source where possible — top-level is correct. |

**Decision: use top-level auto-caching.** Simpler, matches the recommended path, and the prefix-byte invariants in §3.4 ensure it works.

### 3.3 TTL choice

| TTL | Write cost | Read cost | Break-even | Use case |
|---|---|---|---|---|
| 5min `{"type": "ephemeral"}` | 1.25× | 0.1× | 2 calls | self-audit (within a single dev session) |
| 1h `{"type": "ephemeral", "ttl": "1h"}` | 2× | 0.1× | 3 calls | nightly CI self-audit, batch eval runs |

**Decision: default 5min, expose `cache_ttl` parameter for 1h opt-in.** Most users will run self-audit interactively in <5 min windows. CI gets the opt-in flag.

### 3.4 Prefix-byte invariants (the silent invalidators)

For caching to actually work, the rendered prefix must be bit-identical across calls except for the variable trailing portion. Audit the prompt assembly path for these silent invalidators:

| Pattern | Status in `prompts.py` (as of v0.2.1) | Action |
|---|---|---|
| Timestamp / `datetime.now()` in prompt | None | ✅ verify |
| UUID / random ID in prompt | None | ✅ verify |
| `json.dumps(claims)` for CLASSIFY without `sort_keys=True` | Currently `json.dumps(claims, ensure_ascii=False)` in `anthropic.py` | ⚠️ claims is a list of strings — order matters semantically (preserve), but check no dict serialisation slips in |
| Tool schema dict key order | `CLAIM_LIST_TOOL_SCHEMA` / `CLAIM_AUDIT_TOOL_SCHEMA` are Python dict literals → CPython 3.7+ preserves insertion order → deterministic across runs | ✅ confirmed by spec; M1 adds a guard test |
| Model identity | `model_id` is passed through; same model across the two calls in a run | ✅ |
| Floating `tool_choice` change | We always pass `tool_choice={"type": "tool", "name": ...}` with a fixed name per stage | ✅ stable per stage |

### 3.5 Minimum tokens to be cacheable

Both default (`claude-haiku-4-5-20251001`) and fallback (`claude-opus-4-7`) need **4096 tokens minimum** in the prefix to actually cache. Per `claude-api` skill authoritative reference.

| Stage | Typical prefix size | Cacheable? |
|---|---|---|
| DECOMPOSE | tool schema (~500 tokens) + DECOMPOSE_PROMPT static + 2 worked examples (~1200 tokens) + summary (varies) | ⚠️ Often **<4096 tokens** for short summaries — silently NOT cached. Documented in MOCK-LIMITS-style note. |
| CLASSIFY | tool schema (~1500 tokens) + CLASSIFY_PROMPT static + 6 worked examples (~3000 tokens) + claims (varies) + source (varies) | ✅ Usually >4096 tokens once a non-trivial source is included. |

**Implication**: classify benefits from caching; decompose mostly doesn't. M2 captures both stages' actual sizes from a real run.

### 3.6 claude-cli (auto) vs Anthropic SDK (manual)

| Backend | How cache is controlled | What v0.2.2 does |
|---|---|---|
| `claude-cli` | **Platform-level only** — Claude Code's internal system+tools prefix (~36K tokens) caches cross-invocation automatically. **User-prompt content does NOT cache cross-invocation** through `claude -p` (M0 empirically). We see usage via `result.usage.cache_*` fields. | (a) `claude_cli.py._invoke` plumbs `usage` from envelope for transparency; (b) `Pipeline` / `Report` carry usage forward; (c) `eval/run-eval.py` surfaces cache numbers; (d) M2 verifies platform-level cache visible but explicitly documents that user-prompt content does NOT cache cross-invocation. |
| `anthropic` SDK | **Manual** — we set `cache_control={"type": "ephemeral", "ttl": ...}` on `messages.create()`. Cache scope is **prompt-prefix bytes + model + API key**, persists across SDK calls within TTL. | (a) Add `cache_ttl` field on backend; (b) Pass `cache_control` at top level on both `decompose` and `classify`; (c) **M2 primary verification path** — needs API key, ≤$0.20 budget, real `cache_read > 0` on call 2 with same source. |

**Implication for M2 (revised post-M0)**: Anthropic SDK is the only path that can deliver cross-invocation user-prompt cache reuse on `summary-doctor` workflows. claude-cli changes ship as transparency + parity, not as workload caching.

## 4. Failure paths

| Failure | Recovery |
|---|---|
| `cache_read_input_tokens` is 0 across all repeat calls | Diff the rendered request bodies byte-for-byte between call 1 and call 2 (capture both). The first byte difference is the invalidator. Fix prompt assembly or `cache_control` placement. |
| Anthropic SDK version doesn't expose `cache_control` parameter on `messages.create()` | Anthropic SDK has had `cache_control` since the prompt caching beta — but check installed version is recent enough. M1 first task pins or checks `anthropic>=0.40`. |
| 4096-token min not met on classify stage | Document honestly in EVALUATION.md ("caching only activates on sources ≥X chars"). Don't pad prompts to reach the threshold. |
| `cache_ttl="1h"` rejected by API | Older SDK / model didn't support 1h. Fall back to 5min and log a warning. (Per skill ref, all current Claude models support both.) |

## 5. Out of scope

- claude-cli backend caching (the subscription handles caching opaquely; we cannot control it from outside).
- RAG / semantic chunking for long sources (v0.3 P3).
- Per-claim batch CLI flag (separate feature; would change the audit flow).
- Mock backend changes (mock has no model, nothing to cache).

## 6. Carify rounds

### Round 1 — engineer's view

- Default behaviour: should caching be opt-in or always-on for the Anthropic backend? **Always-on.** The 1.25× write premium on a one-shot audit is acceptable cost for the option value of cache reuse on repeat. We add a `--no-cache` escape hatch.
- Where does the `cache_control` parameter physically go in our code? `AnthropicBackend.decompose()` and `AnthropicBackend.classify()` — they're the only call sites. Pass `cache_control={"type": "ephemeral"}` as a top-level kwarg to `client.messages.create()`.
- How do we expose the TTL knob? `--cache-ttl 5m|1h` CLI flag, mirrored on the backend dataclass.
- What if the prefix is <4096 tokens? Pass `cache_control` anyway — the API silently no-ops. No special-case code.

### Round 2 — tester's view

- Boundary: empty source. The classify prompt still has the static prefix + tool schema, which should be near the 4096 threshold. Test captures usage for this case.
- Boundary: source ≥200K tokens. Prompt pipeline already truncates to 200K head; caching applies to the truncated head. No special handling.
- Recovery: M2 retry logic — if first call shows `cache_creation > 0` but second shows `cache_read == 0`, that's the silent invalidator. Capture both request bodies and bisect.
- Observability: backend's `_call_with_fallback` already raises with clear error messages. Add cache-related fields to the logged response (`cache_creation`, `cache_read`) so eval/run-eval.py can show them.

## 7. Deliverables

- `src/summary_doctor/backends/claude_cli.py`: `_invoke` extracts `usage` from envelope's `type: "result"` event; expose via `last_usage` attribute on backend.
- `src/summary_doctor/backends/anthropic.py`: `cache_control={"type": "ephemeral", "ttl": ...}` added to both API calls; `cache_ttl` field on `AnthropicBackend`.
- `src/summary_doctor/pipeline.py` + `Report`: optional `usage` carried through, exposed in JSON sidecar.
- `src/summary_doctor/cli.py`: `--cache-ttl {5m,1h}` and `--no-cache` flags (anthropic backend only — claude-cli ignores).
- `tests/test_cache_prefix.py`: new file, verifies prefix-byte invariants (no timestamps, deterministic tool schemas, no UUID).
- `eval/run-eval.py`: surfaces `cache_creation_input_tokens` and `cache_read_input_tokens` in the per-demo report.
- `docs/EVALUATION.md`: new "Cache performance" section with claude-cli numbers + anthropic SDK note.
- `docs/PROMPT-ENGINEERING.md`: short addendum on cache invariants.
- `README.md` + `README.zh-CN.md`: one-line mention in "Mock vs Anthropic" decision table.
- `CHANGELOG.md` v0.2.2 entry — honest about Anthropic SDK path being code-only, claude-cli path being measurement + plumbing.

## 8. Open assumptions

1. Anthropic SDK installed in the working venv is ≥0.40 (the version we pinned in `[anthropic]` extras). M1 verifies.
2. `claude-haiku-4-5-20251001` and `claude-opus-4-7` both accept `cache_control` parameter. Per skill reference, yes.
3. The current CLASSIFY prefix exceeds 4096 tokens once a real source is included. M2 measures and confirms or reports honestly.
4. We can run a small number of paid Anthropic API calls (≤$0.20) to capture M2 evidence. (claude-cli subscription does not expose cache metadata to us.)
