# Evaluation

How summary-doctor's labels compare across backends on the bundled demo
set. Numbers below come from a real run on **2026-05-19**.

> ⚠️ These are descriptive comparisons against a small, synthetic, single-
> annotator demo set. Treat them as a **calibration baseline**, not a
> precision claim about real-world AI summaries.

## Methodology

Every demo under `demos/` ships with three files:

- `summary.txt` — the AI summary under audit
- `source.txt` — the source material
- `README.md` declaring the per-claim **ground-truth label** assigned by a
  human reviewer (the author of the demo case)

For each backend we run summary-doctor over every demo, parse the resulting
JSON sidecar, and report (a) number of claims, (b) divergence score, and
(c) label distribution.

### Why a synthetic demo set

We need cases where the ground truth is unambiguous and we are free to
publish them. Real public summaries fail both tests: the ground truth is
contested, and redistribution is rarely cleanly licensed. The demo set is
therefore synthetic and clearly marked as such.

### Metrics

| Metric | Definition |
|---|---|
| **Claims** | how many atomic claims the backend extracted from the summary |
| **Divergence** | `(reversed + fabricated + 0.5·softened) / total` — higher = more deviation from source |
| **Label distribution** | `exact / softened / reversed / fabricated` per demo |

`reversed` and `fabricated` are the high-stakes labels — those are what we
ultimately care about.

## Backends compared

| Backend | What it is | Marginal cost | When you'd use it |
|---|---|---|---|
| `mock` | heuristic pipeline tester (no LLM) | $0, offline | CI, pipeline regression, smoke tests |
| `claude-cli` haiku | shells out to `claude -p`, reuses subscription | $0 marginal (subscription) | personal pre-publish checks |
| `claude-cli` opus | same wrapper, stronger model | higher subscription draw | nuanced reversals, Chinese / long sources |
| `anthropic` (SDK) | direct API via `tool_use` | per-token billed | production, scripted bulk runs |

The `anthropic` SDK backend uses tool-use structured output and is the
recommended path for production. We do not include its numbers below
because the SDK and the CLI route to the same models — the CLI wrapper is
just an auth path.

## Results — demo set (n=12 cases, 2026-05-19 run, post-prompt-fix)

Reproduce with:

```bash
PYTHONPATH=src python3 eval/run-eval.py            # mock only
PYTHONPATH=src python3 eval/run-eval.py --with-cli # mock + claude-cli haiku
```

### Backend: `mock`

| Demo | Claims | Divergence | `exact` | `softened` | `reversed` | `fabricated` |
|---|--:|--:|--:|--:|--:|--:|
| `01-reversal-en` | 9 | 72% | 2 | 1 | **6** | **0** |
| `02-softening-zh` | 3 | 50% | 0 | 3 | **0** | **0** |
| `03-faithful-en` | 7 | 0% | 7 | 0 | **0** | **0** |
| `04-cherry-picking-en` | 9 | 56% | 4 | 0 | **5** | **0** |
| `05-causal-inversion-zh` | 4 | 88% | 0 | 1 | **0** | **3** |
| `06-scope-creep-en` | 7 | 57% | 3 | 0 | **4** | **0** |
| `07-temporal-error-en` | 10 | 20% | 8 | 0 | **2** | **0** |
| `08-fabricated-stats-zh` | 6 | 100% | 0 | 0 | **0** | **6** |
| `09-faithful-zh` | 3 | 0% | 3 | 0 | **0** | **0** |
| `10-quote-out-of-context-en` | 9 | 38% | 5 | 0 | **3** | **1** |
| `11-number-exaggeration-zh` | 5 | 79% | 0 | 0 | **0** | **4** |
| `12-cross-language-en-zh` | 14 | 100% | 0 | 0 | **0** | **12** |
| **total** | 86 | 57% avg | 32 | 5 | **20** | **26** |

### Backend: `claude-cli` (Haiku 4.5 default; Opus 4.7 for three Chinese cases)

| Demo | Model | Claims | Divergence | `exact` | `softened` | `reversed` | `fabricated` | Notes |
|---|---|--:|--:|--:|--:|--:|--:|---|
| `01-reversal-en` | Haiku | 6 | 67% | 2 | 0 | **3** | **1** | Caught GPU-supply fabrication that mock missed |
| `02-softening-zh` | **Opus** | 3 | 50% | 1 | 1 | **1** | **0** | Haiku's JSON output failed parse — Opus succeeded first try |
| `03-faithful-en` | Haiku | 5 | 0% | 5 | 0 | **0** | **0** | Positive control clean |
| `04-cherry-picking-en` | Haiku | 5 | 40% | 2 | 2 | **0** | **1** | Found softened where mock over-flagged as reversed |
| `05-causal-inversion-zh` | **Opus** | 4 | 50% | 0 | 2 | **2** | **0** | Haiku missed causal flip (0 reversed even after few-shot fix); Opus caught both |
| `06-scope-creep-en` | Haiku | 3 | 50% | 0 | 3 | **0** | **0** | Correctly labelled all three as softened scope-creep |
| `07-temporal-error-en` | Haiku | 7 | 29% | 5 | 0 | **2** | **0** | Date errors labelled reversed (defensible alternative: fabricated) |
| `08-fabricated-stats-zh` | **Opus** | 7 | 79% | 1 | 1 | **1** | **4** | Strong fabricated recall on invented stats |
| `09-faithful-zh` | Haiku | 4 | 0% | 4 | 0 | **0** | **0** | Chinese positive control clean |
| `10-quote-out-of-context-en` | Haiku | 6 | 75% | 1 | 1 | **4** | **0** | Strongly surfaced the removed-clause reversals |
| `11-number-exaggeration-zh` | **Opus** | 6 | 67% | 1 | 1 | **3** | **1** | Caught 10× magnitude flip + one fabricated assertion |
| `12-cross-language-en-zh` | Haiku | 9 | 28% | 6 | 1 | **2** | **0** | Even unannounced cross-lang produced sane labels on the Anthropic backend |
| **total** | mixed | 65 | 44% avg | 32 | 12 | **18** | **7** | 9 / 12 Haiku, 3 / 12 Opus |

### Cross-backend observations

1. **Anthropic backends produce fewer, better-bounded claims.** Mock used
   a sentence-boundary heuristic and over-split (86 claims across 12 demos);
   the Anthropic models produced 65 (~25% fewer) and the splits look more
   atomic on inspection.
2. **Mock over-flags `reversed` on softening / scope-creep cases.**
   Demos 04 / 06 are softened in ground truth, but mock returned 5 / 4
   `reversed` respectively. Anthropic Haiku correctly demoted these to
   `softened` (3/3 softened on demo 06; 2 softened + 1 fabricated on 04).
3. **Anthropic Haiku catches fabrications mock misses.** Demo 01's GPU-supply
   red herring (mock: 0 fabricated; Haiku: 1 fabricated) and demo 10's
   removed-qualifier reversals (mock would have over-flagged; Haiku gave 4
   reversed + 1 softened on the actual offending claims).
4. **Haiku is unreliable on long Chinese sources.** Three demos
   (02 / 08 / 11) produced invalid JSON inside the `audits` array on Haiku,
   each on a different parse error position; retries did not converge. Opus
   succeeded on first try for all three. We document this as a v0.1 known
   limit and recommend `--model opus` for nuanced Chinese cases until v0.2
   lands a stricter structured-output path for the CLI backend.
5. **Causal-direction inversion is the model's weakest failure mode** —
   and few-shot prompting at the Haiku tier is insufficient. Haiku
   returned 0 / 6 reversed on demo 05 even after the
   `prompts.py` worked-example for causal-direction flip landed. Opus
   on the same prompt caught 2 / 4 reversed claims. Implication: ship
   Opus as the recommended default for any audit where causal-direction
   inversion is plausible, until a Haiku-specific calibration pass is
   designed in v0.2.
6. **Cross-language (EN source / ZH summary) is unexpectedly graceful on
   the Anthropic backend.** Demo 12, designed as a forward-looking v0.2
   stress test, drew sane labels on Haiku (2 reversed + 1 softened + 6
   exact). Mock returned all-fabricated as expected. Cross-language
   alignment is still a v0.2 target — the Anthropic numbers here are an
   under-promise, not a v0.1 feature claim.

## Cache performance (v0.2.2)

v0.2.2 wires Anthropic prompt caching into the `anthropic` backend
(`cache_control={"type": "ephemeral"}` on every `messages.create` call,
with a `--cache-ttl {5m,1h}` knob and a `--no-cache` opt-out). v0.2.2
also plumbs the `usage` block from both the `anthropic` and
`claude-cli` backends into the per-call `last_*_usage` attributes
(see `spec-kit/v0.2.2-caching/00-spec.md` §3.6).

### What the caching wiring delivers, by backend

| Backend | Cross-invocation user-prompt cache? | Evidence |
|---|---|---|
| `claude-cli` (subscription) | **No.** Empirically tested. Same user prompt re-sent in a fresh `claude -p` invocation produces `cache_read_input_tokens = 0`. Claude Code's platform-level system+tools prefix (~36K tokens) DOES cache cross-invocation, but that is independent of `summary-doctor`'s workload. | M0 baseline run: see `spec-kit/v0.2.2-caching/artifacts/M0-baseline-claude-cli.json`. |
| `anthropic` SDK + `cache_control` | **Code path wired; not yet verified with a real API call.** Cache should activate when the rendered prefix is ≥4096 tokens (Haiku 4.5 / Opus 4.7 minimum). The DECOMPOSE prompt is often <4096 tokens for short summaries — caching silently no-ops there. The CLASSIFY prompt usually exceeds the minimum once a non-trivial source is included. | Reproduction runbook: `spec-kit/v0.2.2-caching/artifacts/M2-reproduction-runbook.md`. ~$0.20 to verify. |

### Why no real numbers yet

The v0.2.2 patch shipped the code path complete (44/44 pytest, prefix-stability guard tests, CLI flags, plumbing through both backends) but **deferred the real-API verification** to anyone with an `ANTHROPIC_API_KEY` who runs the runbook. Constitution §1 (honesty over coverage) applies: rather than ship a cache_read number that nobody captured from a real call, the patch ships honest "verification pending" and a reproducible procedure.

### Honest numbers from M0 (claude-cli, platform-level only)

For reference, what M0 captured from `claude -p --output-format json`:

| Call | input_tokens | cache_creation | cache_read | Interpretation |
|---|--:|--:|--:|---|
| probe ("What is 2+2?") | 9 | 40,349 | 0 | first invocation; Claude Code system prefix written to cache |
| A1 (same long prompt as A2) | 9 | 41,439 | 0 | new invocation; user prompt newly cached |
| A2 (**identical bytes to A1**) | 9 | 42,251 | **0** | new invocation; **user-prompt cache did NOT hit** — confirms claude-cli per-invocation isolation |
| B1 (different prompt) | 9 | 5,145 | **36,670** | new invocation but DIFFERENT prompt; the cache_read corresponds to Claude Code's platform-level system+tools prefix, **NOT to summary-doctor user-prompt content** |

These numbers are **not** the v0.2.2 thesis. They're the M0 finding that motivated the rev-3 honest scope: claude-cli users do not get cross-invocation user-prompt cache savings, full stop. Any "cache_read" they see is platform-level freebie.

The Anthropic SDK path is the only one that could deliver workload-level cache reuse. That verification is deferred.

## Limits of this evaluation

1. **Demo set is synthetic and small (n=12).** Real-world precision will
   differ — natural summaries have run-on rhetoric, embedded quotes, and
   editorial framing that the demos do not reproduce.
2. **Ground truth is single-annotator.** No inter-annotator agreement
   measured yet. Treat published numbers as one reviewer's calibration.
3. **No formal accuracy / P/R table.** This document reports descriptive
   label distributions per demo, not per-claim accuracy versus ground
   truth. A confusion matrix lands when the demo set grows past n=20 and
   we add a `--ground-truth` flag to the CLI.
4. **No cross-language eval.** The Chinese demos run with `--lang zh`
   only; cross-language alignment lands in v0.2 (see ROADMAP).
5. **No adversarial set.** We do not yet have cases designed to attack
   the classifier (e.g., source contains the exact phrasing of a
   reversed claim because the source itself was quoting an opposing
   view).
6. **`claude-cli` is non-deterministic.** The same demo on Haiku may
   produce different claim counts and label distributions across runs.
   Where we observed instability (demo 02), the table notes the model
   actually used.

## Contributing new evaluation samples

Open an issue using `.github/ISSUE_TEMPLATE/demo-case.yml`. The template
asks for:

- Synthetic source text (no real speakers / organisations)
- Synthetic summary with at least one claim per label of interest
- Ground-truth label per claim, with a one-line rationale

PRs that bundle a new demo under `demos/NN-<slug>/` and update
`demos/run-demo.sh` are especially welcome.

## Reproducing the table

```bash
# mock only (fast, deterministic, no auth)
PYTHONPATH=src python3 eval/run-eval.py

# mock + claude-cli haiku (reuses Claude Code subscription)
PYTHONPATH=src python3 eval/run-eval.py --with-cli

# raise the model for nuanced cases
PYTHONPATH=src python3 eval/run-eval.py --with-cli --cli-model opus
```

Per-demo JSON sidecars land under `eval/results/<backend>/<demo>.json`.
