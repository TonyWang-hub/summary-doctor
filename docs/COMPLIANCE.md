# Compliance Crosswalk

> A reference mapping of `summary-doctor`'s 4-class output (`exact` /
> `softened` / `reversed` / `fabricated` + per-claim citations) to
> requirements drawn from public regulatory texts and frameworks.
>
> **Disclaimer.** This is engineering documentation, not legal advice.
> The tool emits citations, not verdicts. Whether the tool's output is
> appropriate evidence for any specific regulatory obligation is a
> determination for your counsel and compliance team. Consult them
> before relying on this crosswalk in a compliance posture.

The 4 labels are the only product surface referenced below. The tool's
JSON output additionally includes the matched source paragraph, a
confidence score, and a per-run report identifier — these are referred
to as the "audit record" in the mapping tables.

---

## EU AI Act

The EU AI Act ((Regulation (EU) 2024/1689)) entered into force on
1 August 2024 with staggered application dates. The articles below are
the ones most often invoked when discussing AI summarization
faithfulness.

### Article 13 — Transparency and provision of information to deployers

> "High-risk AI systems shall be designed and developed in such a way
> as to ensure that their operation is sufficiently transparent to
> enable deployers to interpret a system's output and use it
> appropriately."
>
> — Article 13(1). Source: <https://artificialintelligenceact.eu/article/13/>

| Article 13 requirement                                      | Audit record element that may be referenced |
| ----------------------------------------------------------- | ------------------------------------------- |
| Interpretability of output                                   | Per-claim label + rationale + quoted source paragraph |
| Instructions for use including "level of accuracy"           | Aggregate counts of `reversed` / `fabricated` per run |
| Information about known or foreseeable risks                 | Documented limits in [`MOCK-LIMITS.md`](MOCK-LIMITS.md) and the "What it is not" section of the README |

### Article 15 — Accuracy, robustness and cybersecurity

> "High-risk AI systems shall be designed and developed in such a way
> that they achieve an appropriate level of accuracy, robustness, and
> cybersecurity, and that they perform consistently in those respects
> throughout their lifecycle."
>
> — Article 15(1). Source: <https://artificialintelligenceact.eu/article/15/>

| Article 15 requirement                              | Audit record element that may be referenced |
| --------------------------------------------------- | ------------------------------------------- |
| Quantitative accuracy metric across runs            | Divergence rate, `reversed` rate, `fabricated` rate per run |
| Lifecycle accuracy monitoring                       | Run-over-run JSON reports archived with timestamps |
| Per-claim explainability                            | Matched source paragraph + rationale field per claim |

### Article 50 — Transparency obligations for providers and deployers of certain AI systems

> "Providers of AI systems, including general-purpose AI systems,
> generating synthetic audio, image, video or text content, shall
> ensure that the outputs of the AI system are marked in a
> machine-readable format and detectable as artificially generated or
> manipulated."
>
> — Article 50(2). Source: <https://artificialintelligenceact.eu/article/50/>

| Article 50 requirement                                                | Audit record element that may be referenced |
| --------------------------------------------------------------------- | ------------------------------------------- |
| Detectability of AI-generated text                                    | The audit report itself is a third-party-readable derivation showing AI-summary vs source divergence |
| Disclosure of synthetic content to natural persons                    | The 4-label distribution surfaces `fabricated` segments as candidate disclosure points |

The Code of Practice that operationalizes Article 50 watermarking has
been progressing through multiple drafts; the final text may revise
specific technical requirements. Treat this row as the most likely to
need revision.

---

## NIST AI Risk Management Framework

The NIST AI RMF 1.0 (2023-01-26) and the companion Generative AI
Profile NIST-AI-600-1 (2024-07-26) provide a voluntary framework that
is widely referenced in US federal procurement and contracting.

Source: <https://www.nist.gov/itl/ai-risk-management-framework>

### MEASURE function

The MEASURE function calls for AI systems to be analyzed, assessed,
benchmarked, and monitored. The Generative AI Profile lists
**confabulation** (model output presented as fact that is not grounded
in source material) as a distinct risk category requiring measurement.

| MEASURE sub-area as discussed in NIST-AI-600-1 | Audit record element that may be referenced |
| ---------------------------------------------- | ------------------------------------------- |
| Performance measurement                         | Aggregate label distribution per run        |
| Validity and reliability                        | Per-claim citation map showing source grounding |
| Explainability and interpretability             | Rationale + matched paragraph per labeled claim |
| Confabulation (GenAI Profile)                   | Explicit `fabricated` label count           |

### MANAGE function

The MANAGE function expects organizations to prioritize, respond to,
and recover from identified AI risks. The audit JSON record provides
a per-run artifact suitable for an internal AI-incident review
process.

| MANAGE concern                            | Audit record element that may be referenced |
| ----------------------------------------- | ------------------------------------------- |
| Documented response to identified risks   | JSON report retained with timestamp and input hashes |
| Continuous monitoring                     | Periodic `make` re-run on representative summaries |

The specific MEASURE sub-area numbering above paraphrases the GenAI
Profile; refer to the NIST PDF for the canonical sub-item identifiers
before citing them in your own compliance documentation.

---

## SEC 2026 Examination Priorities

The SEC's Division of Examinations publishes annual exam priorities
for registered investment advisers and broker-dealers. The 2026
priorities continue to list AI-related risks, with **AI hallucinations**
named among the categories of concern alongside AI washing, conflicts
of interest, fraud and market manipulation, and systemic risks.

Source (firm summary; cite the official SEC document for compliance
purposes): <https://www.goodwinlaw.com/en/insights/publications/2025/12/alerts-privateequity-pif-2026-sec-exam-priorities-for-registered-investment-advisers>

| Examination focus area               | Audit record element that may be referenced |
| ------------------------------------ | ------------------------------------------- |
| AI hallucination risk in adviser-generated client communications and research | Per-claim citation map for AI-summarized research output; archived JSON reports per generation |

This row is intentionally narrow: the SEC priorities are an
examination scoping document, not a binding rule that the audit
record can on its own satisfy. The artifact may form part of a
broader supervisory record.

---

## China — Interim Measures for Generative AI Service Management

The Interim Measures (《生成式人工智能服务管理暂行办法》) took effect
on 15 August 2023 and apply to generative AI services provided to the
public within mainland China. The articles below are the ones most
directly relevant to AI-summary faithfulness.

Source (official text in Chinese): <https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm>

### Article 4 — Content truthfulness and accuracy

> "采取有效措施……提高生成内容的准确性和可靠性。"
> ("Take effective measures … to improve the accuracy and reliability
> of generated content.")
>
> — Article 4 (excerpt; unofficial translation).

| Article 4 requirement                       | Audit record element that may be referenced |
| ------------------------------------------- | ------------------------------------------- |
| Accuracy of generated content               | `reversed` and `fabricated` rates per run   |
| Reliability of generated content            | Per-claim source-paragraph mapping          |

### Article 8 — Data labeling quality

> Article 8 covers training data and labeling quality, including
> sampling-based verification of labels.

| Article 8 requirement                       | Audit record element that may be referenced |
| ------------------------------------------- | ------------------------------------------- |
| Training data labeling rules                | **Not applicable.** The tool does not train models and has no role in training-data labeling. |

### Article 17 — Service identification and labeling of generated content

> Article 17 (read together with the Measures' provisions on content
> labeling) requires identifiable labels on generated content where
> applicable.

| Article 17 requirement                            | Audit record element that may be referenced |
| ------------------------------------------------- | ------------------------------------------- |
| Identifiable labels for generated content         | The per-claim citation map can sit alongside (not replace) the provider's own labeling |

### GB/T 45654-2025 and GB/T 45674-2025

Two TC260-developed national standards published in 2025:

- GB/T 45654-2025 — generative AI service basic security requirements,
  including provisions on truthfulness / accuracy / objectivity /
  diversity of content.
- GB/T 45674-2025 — data labeling safety specifications.

| Standard provision (paraphrased; consult the official PDF)        | Audit record element that may be referenced |
| ----------------------------------------------------------------- | ------------------------------------------- |
| Content truthfulness self-assessment                              | Aggregate label distribution, `fabricated` rate |
| Per-output explainability                                          | Per-claim rationale + matched paragraph     |

GB/T-series numbering and the precise clause text should be confirmed
against the official SAMR / TC260 publication before being cited in a
filing.

---

## How to use this crosswalk in practice

The tool produces a Markdown report and a JSON report per run. A
typical workflow that uses these artifacts as part of a compliance
posture has three steps:

1. **Pre-deployment.** Run `summary-doctor` against a representative
   sample of summaries the deployed system is expected to produce.
   Archive both the input (summary + source) and the output reports.
   Use the aggregate label distribution as a baseline accuracy figure.

2. **Production.** Insert `summary-doctor` as a gate between the
   AI-summarization step and the downstream consumer (publication,
   filing, customer report). Configure the gate to flag `reversed`
   and `fabricated` for human review.

3. **Audit trail.** Retain the Markdown and JSON reports per
   generation, with timestamps and input hashes. The retained
   artifacts let a reviewer reconstruct what was checked and what was
   flagged.

The audit record on its own does not establish compliance with any
specific regulation. It is one input among several (data governance,
model documentation, incident response) that a compliance function
would assemble.

---

## What this crosswalk is not

- It is not legal advice. It is a reference mapping.
- It does not imply that running `summary-doctor` satisfies any
  specific obligation. Whether an obligation is satisfied depends on
  the regulator, the use case, and the broader controls in place.
- It does not constitute a claim of certification. There is no
  certification scheme this tool is being offered against.
- It may go out of date. The EU AI Act Code of Practice, NIST sub-item
  numbering, SEC examination priorities, and China TC260 standards
  each have known forthcoming updates; revisit this document before
  relying on a row.

For the tool's own limits and design rationale, see
[`SPEC.md`](SPEC.md), [`MOCK-LIMITS.md`](MOCK-LIMITS.md), and
[`SELF-AUDIT.md`](SELF-AUDIT.md).
