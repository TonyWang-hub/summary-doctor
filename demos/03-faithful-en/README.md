# Demo 3 — Faithful summary (English)

This is a positive control. A well-written summary should yield mostly `exact`
labels and a low divergence score. If the tool returns many `reversed` /
`fabricated` labels here, the tool itself is mis-calibrated.

## Expected audit

All claims → `exact`. Divergence score expected ≤ 10%.

## How to run

```bash
summary-doctor demos/03-faithful-en/summary.txt \
  --original demos/03-faithful-en/source.txt \
  --lang en --mock
```
