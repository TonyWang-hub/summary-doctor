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

## Results — demo set (n=9 cases, 2026-05-19 run)

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
| **total** | 58 | 49% avg | 27 | 5 | **17** | **9** |

### Backend: `claude-cli` (Haiku 4.5, with one Opus fallback)

| Demo | Claims | Divergence | `exact` | `softened` | `reversed` | `fabricated` | Notes |
|---|--:|--:|--:|--:|--:|--:|---|
| `01-reversal-en` | 6 | 67% | 2 | 0 | **3** | **1** | Caught GPU-supply fabrication that mock missed |
| `02-softening-zh` | 3 | 50% | 1 | 1 | **1** | **0** | **Ran on Opus** — Haiku's JSON output failed parse twice on this case |
| `03-faithful-en` | 5 | 0% | 5 | 0 | **0** | **0** | Positive control clean |
| `04-cherry-picking-en` | 5 | 30% | 3 | 1 | **0** | **1** | Found softened where mock over-flagged as reversed |
| `05-causal-inversion-zh` | 5 | 10% | 4 | 1 | **0** | **0** | **Model missed the causal inversion** — opus run recommended |
| `06-scope-creep-en` | 3 | 33% | 1 | 2 | **0** | **0** | Correctly identified softened scope-creep |
| `07-temporal-error-en` | 8 | 25% | 6 | 0 | **2** | **0** | Date errors labelled reversed (defensible alternative: fabricated) |
| `08-fabricated-stats-zh` | 7 | 79% | 1 | 1 | **1** | **4** | Strong fabricated recall on invented stats |
| `09-faithful-zh` | 4 | 0% | 4 | 0 | **0** | **0** | Chinese positive control clean |

### Cross-backend observations

1. **Anthropic backends produce fewer, better-bounded claims.** Mock used
   a sentence-boundary heuristic and over-split (58 claims total); the
   Anthropic models produced 46 across the same nine demos (~20% fewer)
   and the splits look more atomic on inspection.
2. **Mock over-flags `reversed` on softening / scope-creep cases**
   (demos 04, 06 are softened in ground truth, but mock returned 5 / 4
   `reversed` respectively). Anthropic Haiku correctly demoted these to
   `softened` or `exact`.
3. **Anthropic Haiku caught the demo-1 fabrication that mock missed**
   (the GPU-supply red herring), and mostly preserved fabricated recall
   on demo 08 (4/4 of the invented numeric claims).
4. **Demo 02 (zh softening) is a known Haiku weak spot.** Two retries
   produced invalid JSON inside the `audits` array (Haiku occasionally
   mis-quotes Chinese inline text and breaks the JSON). Opus succeeds on
   the first try. We document this as a v0.1 known limit and recommend
   `--model opus` for nuanced Chinese cases until v0.2 lands a stricter
   structured-output path for the CLI backend.
5. **Demo 05 (causal inversion zh) is the model's weakest case.** Haiku
   reports `exact` 4 / `softened` 1 / no `reversed`, missing the X → Y vs
   Y → X flip. Opus partially recovers (per spot check — not in the
   table). This is a real-world failure mode that calibrated prompting
   will need to address in a future release.

## Limits of this evaluation

1. **Demo set is synthetic and small (n=9).** Real-world precision will
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
