# summary-doctor · SPEC v0.1

> Audit AI-generated summaries against their source material.
> Detect reversals, fabrications, and cherry-picking — with citations, not verdicts.

## Why this exists

LLM-assisted summaries of public talks, interviews, and articles are now mass-distributed on social platforms. Anecdotal evidence — and a growing literature on LLM faithfulness — suggests that a non-trivial fraction of claims in such summaries can diverge from the source material, sometimes outright reversing the speaker's position.

There is currently no open tool that maps a summary's claims back to source paragraphs and labels each claim by faithfulness category. This project is that tool.

The tool does **not** decide whether a summary is "true" or "false". It outputs a mapping with quoted source paragraphs so the reader judges.

## The 3 problems we solve

| # | Problem | Acceptance criterion |
|---|---------|---------------------|
| 1 | No tool maps summary claims → source paragraphs with category labels | Given summary + source, output 4-class labels (exact / softened / **reversed** / **fabricated**) with quoted citations |
| 2 | Verdicts without evidence are not trustworthy | Every label carries (a) the summary sentence, (b) the matched source paragraph (or "no match"), (c) a confidence 0–100, (d) a one-line rationale |
| 3 | "LLM auditing LLM" is itself suspect | Output is a **mapping + citation table**, not a binary verdict. The human reader makes the final call. |

## Interface

```bash
summary-doctor <summary>  --original <url|file>  [--lang zh|en]
                                                 [--out report.md]
                                                 [--model claude-opus-4-7|claude-haiku-4-5-20251001]
                                                 [--mock]
```

- `<summary>`: file path, URL, or `-` for stdin
- `--original`: file path or URL of the source material
- `--lang`: language hint (default: auto)
- `--out`: report output path (default: `./summary-audit-<timestamp>.md`)
- `--model`: LLM backend (default: claude-haiku-4-5 for cost)
- `--mock`: skip LLM calls, return canned demo report (for testing the pipeline)

Outputs:
- Markdown report at `--out`
- JSON sidecar at `<--out>.json`
- Exit code: 0 = ran successfully, 1 = pipeline error, 2 = source unfetchable

## 5-stage state machine

```
[1 input]  →  [2 extract]  →  [3 decompose]  →  [4 map+classify]  →  [5 report]
   ↓             ↓                ↓                  ↓                  ↓
 url/file    plain text       claim list         labeled pairs     md + json
```

| Stage | Input | Output | LLM? |
|-------|-------|--------|------|
| 1. input | CLI args | raw summary + raw source | no |
| 2. extract | raw (html/md/txt) | plain text | optional (defuddle-style cleanup) |
| 3. decompose | summary plain text | list of N claims (assertive statements) | yes |
| 4. map+classify | claims + source text | per claim: (matched_paragraph, label, confidence, rationale) | yes |
| 5. report | labeled pairs | markdown + json | no |

## Classification labels (4 classes)

| Label | Definition | Example |
|-------|-----------|---------|
| `exact` | Summary claim is supported almost verbatim by source | "The author said X" → source: "X" |
| `softened` | Summary preserves direction but loses qualifiers / strength | source: "always X under condition Y" → summary: "X" |
| **`reversed`** | Summary inverts or contradicts the source's position | source: "Z does increase X" → summary: "Z does not increase X" |
| **`fabricated`** | Summary claim has no support in source | summary contains entire concepts source never mentioned |

`reversed` and `fabricated` are the high-signal labels — they correspond to the failure modes that motivated this project.

## Failure paths

| Failure | Behavior |
|---------|----------|
| Source URL returns 403 / paywalled | Exit 2; suggest user paste plain text via `--original -` |
| Source is audio/video | Out of scope for v0.1; report exits with "ASR not supported in v0.1" |
| Cross-language (summary EN, source ZH) | v0.1: warn + best-effort; v0.2: add translation alignment layer |
| LLM rate limit | Exponential backoff (max 3), then degrade to weaker model |
| Source too long (>200k tokens) | v0.1: chunk by paragraph; warn user about chunking |

## Skeptic grilling (recorded so we don't forget)

| Role | Pushback | Response |
|------|----------|----------|
| Skeptic | LLM auditing LLM is same-origin bias | Tool emits **citations**, not verdicts. Reader judges. |
| Counterparty | Will social-media readers use a CLI? | v0.1 = CLI + Skill. v0.2 plans a browser extension that intercepts "AI summary" cards. |
| Source auditor | Are the bundled demos representative? | v0.1 ships with three synthetic demos covering reversal, softening, and a positive control. Real audits should rely on the Anthropic backend against actual sources. |

## Out of scope for v0.1

- Audio/video summaries (needs ASR)
- Cross-language alignment (zh ↔ en)
- Browser extension UI
- Multi-summary comparison
- Author / publisher reputation scoring (separate problem)

## Confidence and limits (disclosed in every report)

Every report includes a header block:

```
⚠️ Limits of this audit:
- Detection is LLM-based; precision is bounded by the LLM's reading comprehension.
- 'fabricated' label may produce false positives if source has supporting material that wasn't retrieved (e.g., paywall, OCR failure).
- Tool is a mapping aid, not a truth oracle.
```

## Self-audit

To keep this project honest, the repository runs `summary-doctor` against its own README claims as a CI step (lands in v0.1.1, see Roadmap). Limits of self-audit will be documented in `docs/SELF-AUDIT.md` once implemented.
