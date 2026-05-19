# Demo 13 — Academic peer-review summarization (English)

This demo is synthetic. The source and summary are entirely invented for
the purpose of illustrating one failure shape — AI summaries of academic
literature that reverse a direction-of-effect finding, fabricate a
citation, and quietly drop the scope condition that was attached to the
real finding. The fictional citation "Smith et al., 2024, *Journal of
Synthetic Reviews*" is obvious-by-design; any resemblance to a real paper,
journal, or author is unintended.

## Why this failure shape matters in academic peer review

Empirical work has documented that AI-modified text and AI-assisted
review writing are now a measurable fraction of submitted peer reviews,
and that AI-generated literature reviews can contain plausible-looking
citations that do not exist. The real public events listed below
established the baseline; this synthetic demo is one stylized instance.

| Real public event | What happened | Source URL |
|---|---|---|
| ICLR 2024 / EMNLP / NeurIPS 2023 peer reviews — 6.5–16.9% substantially AI-modified | Stanford-led token-frequency analysis on conference review corpora detected systematic AI-text contamination across 4 ML venues. Replicated in a 2024 follow-up. | <https://arxiv.org/abs/2403.07183> |
| Fabricated references in 1-in-277 PubMed-indexed papers in 2026 | Lancet / Retraction Watch joint analysis found a steep rise in fraudulent or non-existent citations in indexed biomedical literature. | <https://retractionwatch.com/2026/05/07/one-in-277-pubmed-indexed-papers-in-2026-shows-fabricated-references-says-analysis/> |
| AI text detectability in peer review — follow-up study | A 2024 follow-up paper extended the Liang et al. methodology to more venues and confirmed the corpus-level signal. | <https://arxiv.org/html/2410.03019v2> |

The pattern across the three events: AI-written summaries of academic
text are now common enough that the *direction*, *scope*, and *citation
list* of a literature review can no longer be assumed to match the
underlying papers without an audit step.

## Expected audit

The summary in this demo carries four distinct failure shapes mixed in
with two control claims that the source actually supports.

| Claim from summary | Expected label | Why |
|---|---|---|
| "targeted written feedback ... did not reduce peer-review turnaround time" | **reversed** | The source says targeted feedback paired with a structured rubric *reduced* turnaround by 18 percent. The summary inverts the direction. |
| "targeted feedback in fact increased turnaround time relative to free-form feedback" | **reversed** | Direct inversion of the source's 18 percent reduction finding. |
| "an earlier randomized trial of monetary honoraria for reviewers, conducted across seventeen mathematics journals (Jones, 2023), produced a 41 percent increase in on-time submission rates" | **fabricated** | No honoraria trial, no seventeen mathematics journals, no 41 percent figure, and no Jones 2023 citation appears anywhere in the source. The citation is invented. |
| "targeted feedback paired with a structured rubric reduces peer-review turnaround time for all reviewer cohorts ... making the intervention suitable as a general policy recommendation" | **softened** (scope creep) | The source restricts the effect to early-career reviewers and warns explicitly against generalizing the 18 percent figure outside that subgroup. The summary drops the scope condition and the explicit caution. |
| "The original controlled study enrolled 142 participants from a single mid-sized research institution." | exact | Source has the same figure and the same institutional framing. |
| "in the 2024 controlled study with 142 participants" (preamble fragment) | exact | Matches source verbatim. |

`reversed` and `fabricated` are the high-signal labels — at least one of
each must appear for this demo to be considered "live".

## Why this is hard

The reversal here is one polarity word ("reduced" → "did not reduce" /
"increased"). A reader who skims and trusts the citation list does not
notice it. The fabricated citation looks structurally identical to a real
academic citation; the failure is only detectable by checking whether the
cited paper exists in the source. The softened claim is the subtlest of
the three — it preserves the direction of the effect, so polarity-only
auditors will mark it `exact`, missing that the scope was silently
generalized from "early-career reviewers" to "all reviewer cohorts".

## How to run

```bash
summary-doctor demos/13-academic-peer-review-en/summary.txt \
  --original demos/13-academic-peer-review-en/source.txt \
  --lang en --mock
```

`--mock` is heuristic and may collapse the fabricated citation into
`softened` (the cited names share enough surface tokens with the source
that keyword overlap rises above the `fabricated` floor). The Anthropic
backend (`--mock` removed, `ANTHROPIC_API_KEY` exported) is the calibrated
path and is expected to recover the citation-fabrication label.
