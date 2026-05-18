# Limits of the `--mock` backend

The mock backend exists so the pipeline runs end-to-end with no API key and no
network calls. It is **not** a substitute for an LLM-backed audit.

## What it does

1. Splits the summary at sentence boundaries (`. ! ? 。 ！ ？` and blank lines).
2. For each claim, scores keyword overlap against each source paragraph.
3. Compares negation polarity (`not / no / never` in English; `不 / 没 / 无 / 未` in Chinese) between the claim and the best-matching paragraph.
4. Emits a label based on overlap ratio and polarity match.

## What it gets wrong (by design)

| Failure mode | Why |
|---|---|
| Long compound sentences are split at `.` and `,` | Subordinate clauses with `not` get classified independently and misfire as `reversed` |
| "X is insufficient for Y" vs "X does not imply Y" | Mock only checks token-level negation; semantic equivalents are missed |
| Cross-paragraph context | Mock matches one paragraph at a time; claims that need multi-paragraph context will be mis-anchored |
| Paraphrase | Mock relies on keyword overlap; aggressive paraphrasing inflates `fabricated` |

## What to use instead

For any non-trivial audit, run with the Anthropic backend:

```bash
export ANTHROPIC_API_KEY=sk-...
summary-doctor <summary> --original <source>   # no --mock
```

Recommended models:

- `claude-haiku-4-5-20251001` (default) — cheap, fast, fine for ≤10k tokens of source
- `claude-opus-4-7` — for nuanced reversals, soft-vs-reversed boundary cases, or long sources

## How to read mock output

Treat mock output as a smoke test:
- Demo 1 (reversal): mock should produce **non-zero** `reversed` count.
- Demo 2 (softening): mock should produce **non-zero** `softened` count.
- Demo 3 (faithful positive control): mock should produce **zero** `reversed` and `fabricated`.

If those three invariants hold, the pipeline is wired correctly. The absolute
divergence numbers are not meaningful in mock mode.
