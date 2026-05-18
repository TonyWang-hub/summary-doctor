# summary-doctor

> **Your AI summary may be lying. This catches the reversals, fabrications, and cherry-picking — with citations, not verdicts.**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](docs/ROADMAP.md)
[![PRs: welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)

LLM-generated summaries of public talks, interviews, and articles are now mass-distributed on social platforms. Anecdotal evidence and a growing literature on LLM faithfulness suggest that **a non-trivial fraction of claims in such summaries can diverge from the source material** — sometimes outright reversing the speaker's position.

There is currently no open tool that maps each claim in a summary back to the source and labels the faithfulness. **This project is that tool.**

```
┌──────────────────────────────────────────────────────────────┐
│  AI summary                source material                   │
│       │                          │                           │
│       └────────┬─────────────────┘                           │
│                ▼                                             │
│       summary-doctor  →  per-claim label + quoted citation   │
│                                                              │
│   exact · softened · reversed · fabricated                   │
└──────────────────────────────────────────────────────────────┘
```

---

## Why "citations, not verdicts"

We do **not** decide whether a summary is "true" or "false". The tool outputs a mapping with the matched source paragraph quoted verbatim, plus a 4-class label and a confidence. **The human reader makes the final call.**

This matters because:

1. LLM-auditing-LLM has same-origin bias. Outputting citations sidesteps the "who audits the auditor" problem.
2. `fabricated` may be a false positive when source retrieval is partial (paywall, OCR failure, chunked context). The reader sees the matched paragraph (or "no match") and decides.

See [`docs/SPEC.md`](docs/SPEC.md) for the full design rationale.

---

## Install

```bash
pip install -e .                  # core
pip install -e '.[anthropic]'     # with Anthropic SDK
```

Python 3.10+ required.

---

## 30-second quickstart

```bash
# 1. dry-run with the bundled demo (no API key needed)
summary-doctor demos/01-reversal-en/summary.txt \
  --original demos/01-reversal-en/source.txt \
  --lang en --mock

# 2. real audit with Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...
summary-doctor demos/01-reversal-en/summary.txt \
  --original demos/01-reversal-en/source.txt \
  --lang en
```

Output:

```
[ok] report: summary-audit-20260518-211103.md
[ok] json:   summary-audit-20260518-211103.md.json
[summary] 9 claims · divergence 67% · reversed 4 · fabricated 0
```

The markdown report shows, for each claim:

```markdown
### Claim 3 — `reversed` (confidence 75)

**Summary claim:**
> AI agents do not increase communication overhead

**Matched source paragraph:**
> ...every additional agent in the loop is one more participant whose
> intent and state must be kept in sync with humans and with other agents.
> The number of communication channels therefore continues to grow...

**Rationale:** Polarity mismatch with strong keyword overlap (7/8).
```

---

## The 4 labels

| Label | Definition |
|-------|-----------|
| `exact` | Summary claim is supported almost verbatim by source. |
| `softened` | Summary preserves direction but loses qualifiers / strength. |
| **`reversed`** | Summary inverts or contradicts the source's position. |
| **`fabricated`** | Summary claim has no support anywhere in source. |

`reversed` and `fabricated` are the high-signal labels you want to act on.

---

## What it is not

- It is not a truth oracle. It is a **citation mapper**.
- It is not a real-time stream auditor.
- It is not a publisher / author reputation system. Different problem.

The `--mock` backend is a heuristic pipeline-tester, **not** a calibrated detector. Use the Anthropic backend for real audits. See [`docs/MOCK-LIMITS.md`](docs/MOCK-LIMITS.md).

---

## How it works (5-stage pipeline)

```
[1 input]  →  [2 extract]  →  [3 decompose]  →  [4 map+classify]  →  [5 report]
   ↓             ↓                ↓                  ↓                  ↓
 url/file    plain text       claim list         labeled pairs     md + json
```

Stages 3 and 4 call an LLM (Anthropic Claude by default). Stages 1, 2, 5 are deterministic. See [`docs/SPEC.md`](docs/SPEC.md) for full state machine, failure paths, and out-of-scope items.

---

## Demos

Three bundled cases live under [`demos/`](demos/). All demos are **synthetic** — any resemblance to specific real speakers, talks, or organizations is unintended.

| Demo | Language | Designed to surface |
|------|----------|---------------------|
| `01-reversal-en` | English | Reversed claims + fabricated claim (GPU bottleneck) |
| `02-softening-zh` | 中文 | Softened qualifiers + a reversed claim |
| `03-faithful-en` | English | Positive control — should produce mostly `exact` |

---

## Roadmap

- v0.1 (this release): CLI, 5-stage pipeline, Claude backend, 3 demos.
- v0.2: Cross-language alignment, chunked sources, audio/video via ASR.
- v0.3: Chrome extension, Claude Code / Cursor Skill manifest, batch mode.

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Self-audit (lands in v0.1.1)

To keep this project honest, CI will run `summary-doctor` against the repository's own README claims (`make self-audit`). Limits of self-audit are kept honest in [`docs/MOCK-LIMITS.md`](docs/MOCK-LIMITS.md).

---

## Contributing

The most useful contributions right now:

1. Public-domain demo cases in **other languages** (especially low-resource).
2. Failure-mode examples where the Anthropic backend produces `reversed` but the source actually supports the claim — these calibrate the prompts.
3. Browser extension prototypes for the v0.3 milestone.

PRs welcome. Please open an issue first for anything beyond a typo fix or new demo case.

---

## License

[MIT](LICENSE)
