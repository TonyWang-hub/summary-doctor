# Use Cases

> Real-world failure modes that `summary-doctor` is designed to catch.
>
> Each case below references public events with at least two independent
> sources, names the failure-mode label the tool would produce, and points
> to the bundled demo that best illustrates the pattern.

`summary-doctor` outputs one of four labels per claim:

- `exact` — supported almost verbatim by the source
- `softened` — direction preserved, qualifiers / strength lost
- `reversed` — claim inverts or contradicts the source's position
- `fabricated` — no support anywhere in the source

The three workflows below show where `reversed` and `fabricated` matter
most.

---

## 1. Academic peer review and literature summarization

### What goes wrong in public

In March 2024 a Stanford-led study (Liang et al., arXiv:2403.07183)
measured token-frequency shifts in ICLR 2024 and NeurIPS 2023 peer
reviews and estimated that **6.5%–16.9% of reviews were substantially
AI-modified**. Replication and extension followed in arXiv:2410.03019.

The downstream problem is well-documented:

- **System-level failure cascade** — a NeurIPS 2025 failure-mode
  taxonomy paper (arXiv:2602.05930) documents AI-authored papers with
  fabricated citations passing AI-assisted reviewers that did not
  verify the references.
- **Population-scale rise in fabricated citations** — Retraction Watch
  (2026-05-07) and STAT News, jointly reporting on a Lancet-cited
  analysis, found roughly **1 in 277 PubMed-indexed papers in 2026**
  showed fabricated references, a step-change versus the prior trend.

Sources:

- <https://arxiv.org/abs/2403.07183>
- <https://arxiv.org/html/2410.03019v2>
- <https://retractionwatch.com/2026/05/07/one-in-277-pubmed-indexed-papers-in-2026-shows-fabricated-references-says-analysis/>
- <https://www.statnews.com/2026/05/07/lancet-study-finds-steep-rise-fraudulent-citations-academic-papers/>

### Typical failure modes (and what `summary-doctor` labels them)

| Failure                                                | Label        |
| ------------------------------------------------------ | ------------ |
| Cited paper does not exist or wrong authors            | `fabricated` |
| Direction of finding flipped ("X reduced Y" → "X did not reduce Y") | `reversed`   |
| Strong qualifier dropped ("in a small pilot" → omitted)| `softened`   |

### Recommended workflow

```bash
# audit an AI-summarized literature review against the paper PDFs (text form)
summary-doctor literature-review.md \
  --original paper-corpus.txt \
  --lang en \
  --backend anthropic --model haiku
```

Two practical patterns:

1. Reviewers paste the model-generated summary as the input file and
   the canonical preprint text as `--original`; the report is then
   attached to the review record.
2. Editors batch-run summarized abstracts across a journal's recent
   submissions and archive the JSON reports for audit trail.

### Matching demos

- [`demos/03-faithful-en`](../demos/03-faithful-en) — positive control
  (mostly `exact`), useful as a baseline before running the audit on
  a real literature review.
- [`demos/13-academic-peer-review-en`](../demos/13-academic-peer-review-en)
  — preprint summary with one reversed finding and one fabricated
  citation. (Planned, see [`ROADMAP.md`](ROADMAP.md).)

---

## 2. Legal AI fabricating cases (Mata-style)

### What goes wrong in public

In *Mata v. Avianca, Inc.* (S.D.N.Y., June 22, 2023) the court imposed
Rule 11 sanctions on counsel after a ChatGPT-generated brief submitted
six non-existent cases ("Varghese", "Shaboon", "Petersen", "Martinez",
"Durden", "Miller") that the judge described as "gibberish". This is
the most-cited reference case for AI-fabricated legal authority.

Sources:

- <https://en.wikipedia.org/wiki/Mata_v._Avianca,_Inc.>
- <https://web.archive.org/web/2024/https://www.seyfarth.com/news-insights/update-on-the-chatgpt-case-counsel-who-submitted-fake-cases-are-sanctioned.html> [archived — origin timeout]
- <https://web.archive.org/web/2024/https://law.justia.com/cases/federal/district-courts/new-york/nysdce/1:2022cv01461/575368/54/> [archived — origin 403]

The problem is not anecdotal:

- **Stanford RegLab (Magesh et al., May 2024)** found commercial legal
  research tools (Lexis+ AI, Westlaw AI-Assisted Research) hallucinated
  in **17%–34% of queries**, despite vendor marketing of
  "hallucination-free" linked citations. <https://reglab.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools/>
- **ABA Formal Opinion 512 (July 29, 2024)** now requires lawyers to
  ensure the accuracy of all generative-AI outputs related to client
  representation before they are used in judicial proceedings.
  <https://web.archive.org/web/2024/https://www.americanbar.org/news/abanews/aba-news-archives/2024/07/aba-issues-first-ethics-guidance-ai-tools/> [archived — origin 403]

### Typical failure modes (and what `summary-doctor` labels them)

| Failure                                                          | Label        |
| ---------------------------------------------------------------- | ------------ |
| Cited case does not exist on the docket                          | `fabricated` |
| Holding misstated as opposite outcome                            | `reversed`   |
| Narrow holding presented as general rule                         | `softened`   |

### Recommended workflow

```bash
# audit an AI-drafted case brief against the actual docket / opinion text
summary-doctor draft-brief.md \
  --original opinion-and-docket.txt \
  --lang en \
  --backend anthropic --model opus
```

Patterns observed in production-style use:

1. Solo and small-firm practitioners run the audit between drafting
   and filing; any `fabricated` label triggers a manual citation check.
2. The JSON output is retained as an internal record showing that an
   audit step occurred prior to submission — useful when responding
   to standing orders that require disclosure of AI use.

### Matching demos

- [`demos/14-legal-mata-style-en`](../demos/14-legal-mata-style-en) —
  reproduction fixture using only public docket text and a deliberately
  fabricated case citation; output should include at least one
  `fabricated` label. (Planned, see [`ROADMAP.md`](ROADMAP.md).)

---

## 3. AI news summaries softening or reversing the headline

### What goes wrong in public

Two events in 2024 made AI news-summarization failures highly visible:

- **Apple Intelligence + BBC, December 2024.** A push notification
  summarized a BBC News story as "Luigi Mangione shoots himself",
  which was not in the original report. BBC filed a formal complaint;
  Reporters Without Borders called for the feature to be withdrawn;
  Apple later paused the news-summarization feature.
- **Google AI Overviews, May 2024.** AI Overviews advised mixing glue
  into pizza sauce (traced to an eleven-year-old Reddit joke) and
  recommended eating rocks (traced to a satirical post). Google
  published a post-mortem describing the synthesis failure.

Sources:

- <https://www.theregister.com/2024/12/17/apple_intelligence_bbc_complaint/>
- <https://www.cnn.com/2024/12/19/media/apple-intelligence-news-bbc-headline/index.html>
- <https://appleinsider.com/articles/25/01/03/apple-intelligence-summaries-are-still-screwing-up-headlines>
- <https://interestingengineering.com/market-monitoring/glue-pizza-eat-rocks-google-ai-search>
- <https://mikecaulfield.substack.com/p/the-elmers-glue-pizza-error-is-more>

NewsGuard's December 2024 monitor found leading chatbots had a
**combined 62% fail rate** when prompted with provably false news
claims (40.33% repeated misinformation, 21.67% non-response).
<https://web.archive.org/web/2024/https://www.newsguardtech.com/ai-monitor/december-2024-ai-misinformation-monitor/> [archived — origin timeout]

### Typical failure modes (and what `summary-doctor` labels them)

| Failure                                                                       | Label        |
| ----------------------------------------------------------------------------- | ------------ |
| Outcome stated as opposite of what the article reported                       | `reversed`   |
| Headline-level claim with no supporting passage in the article                | `fabricated` |
| Direct quote retained but the immediately-following clarifier dropped         | `reversed`   |
| Conditional / hedged claim reported as definitive                             | `softened`   |

### Recommended workflow

```bash
# audit an AI news digest against the originating article text
summary-doctor ai-news-digest.md \
  --original article.txt \
  --lang en \
  --backend anthropic --model haiku
```

Useful patterns:

1. Newsroom integrity teams compare AI-summarized digests against the
   articles they syndicate before publication and block items with
   `reversed` labels above a configured threshold.
2. End users running the tool locally on their daily digest catch the
   quote-out-of-context pattern that is hardest to spot by eye.

### Matching demos

- [`demos/02-softening-zh`](../demos/02-softening-zh) — softened
  qualifiers plus one reversed claim, in Chinese.
- [`demos/10-quote-out-of-context-en`](../demos/10-quote-out-of-context-en)
  — exact quote retained but the trailing clarifier dropped, flipping
  the meaning. This is the closest analog to the Apple Intelligence
  failure pattern.

---

## Notes

- All demos are synthetic. They are designed to surface the labels named
  above; they are not reproductions of any specific real article,
  speaker, or case.
- The tool emits **citations, not verdicts**. The labels are a triage
  signal; final judgement remains with the human reader. See the
  project README's "Why citations, not verdicts" section.
- For the limits of the heuristic mock backend, see
  [`MOCK-LIMITS.md`](MOCK-LIMITS.md). For evaluation methodology, see
  [`EVALUATION.md`](EVALUATION.md).
