# Demo 1 — Reversal + fabrication (English)

This demo is synthetic. Any resemblance to specific real speakers, talks,
hospitals, or organizations is unintended.

## Expected audit

| Claim from summary | Expected label | Why |
|---|---|---|
| "LLMs reduce radiologist workload" | **reversed** | Source says LLM drafting *did not* reduce overall workload |
| "essentially eliminates radiologist shortages" | **reversed** | Source explicitly rejects this framing |
| "80% concordance rate" | exact | Source has the same figure |
| "did not translate into proportional gain in clinical throughput" | exact (or softened) | Source says throughput stayed roughly flat |
| "new bottleneck is the supply of GPU compute" | **fabricated** | Source never mentions GPU supply; it says judgment is the scarce resource |

## How to run

```bash
summary-doctor demos/01-reversal-en/summary.txt \
  --original demos/01-reversal-en/source.txt \
  --lang en --mock
```

`--mock` is heuristic and may not catch all reversals. The Anthropic backend
(`--mock` removed, `ANTHROPIC_API_KEY` exported) is the calibrated path.
