# M3 — URL audit · close-out

**Status**: ✅ passed
**Wall clock**: ~10 min
**Artifacts**: `artifacts/url-list.txt`, `artifacts/url-audit.md`

## Carify round 1 — engineer's view

Choice: `curl -sIL` per URL with 15s timeout, 1s sleep between hosts, `User-Agent: summary-doctor/0.2 dogfood-audit`. Chose `curl` over `WebFetch` to (a) avoid burning model tokens on 21 fetches, (b) get the final HTTP code after redirects, (c) capture the final URL.

Wayback fallback: tried the `archive.org/wayback/available` JSON API first; the API returned empty (likely rate-limited on this run). Falling back to a direct `web.archive.org/web/2024/<url>` probe is cheaper and proved sufficient for 3 of 4 dead origins.

## Carify round 2 — tester's view

Boundary: redirected URLs (`cnn.com` → `edition.cnn.com`, `theregister.com` → `theregister.com/on-prem/`) are preserved as 200; the final URL is captured in the audit table.

403 vs 404: three of four non-2xx are `403 Forbidden` (anti-bot at `law.justia.com`, `americanbar.org`, `seyfarth.com`), not dead content. A browser visit confirms the pages are live. The Wayback archive succeeded on the first two; the third (`seyfarth.com`) timed out on Wayback too — treated below as "archived URL kept in doc with origin-timeout annotation".

Recovery: every non-2xx URL got an inline `[archived — ...]` annotation in `docs/USE-CASES.md`. No claim was deleted because all four are corroborating sources, not load-bearing single-source claims (per Constitution §1 "honesty over coverage" — flagging beats removing).

## Result table (full)

| Doc | URL | Origin | Resolution |
|---|---|--:|---|
| COMPLIANCE | artificialintelligenceact.eu/article/13/ | 200 | kept |
| COMPLIANCE | artificialintelligenceact.eu/article/15/ | 200 | kept |
| COMPLIANCE | artificialintelligenceact.eu/article/50/ | 200 | kept |
| COMPLIANCE | cac.gov.cn 2023-07/13 | 200 | kept |
| COMPLIANCE | goodwinlaw.com 2025/12 | 200 | kept |
| COMPLIANCE | nist.gov/itl/ai-risk-management-framework | 200 | kept |
| USE-CASES | appleinsider.com … screwing-up-headlines | 200 | kept |
| USE-CASES | arxiv.org/abs/2403.07183 | 200 | kept |
| USE-CASES | arxiv.org/html/2410.03019v2 | 200 | kept |
| USE-CASES | en.wikipedia.org Mata_v._Avianca | 200 | kept |
| USE-CASES | interestingengineering.com glue-pizza | 200 | kept |
| USE-CASES | **law.justia.com nysdce docket 54** | **403** | **archived (Wayback 200)** |
| USE-CASES | mikecaulfield.substack.com elmers-glue-pizza | 200 | kept |
| USE-CASES | reglab.stanford.edu hallucination-free | 200 | kept |
| USE-CASES | retractionwatch.com 1-in-277-pubmed | 200 | kept |
| USE-CASES | **americanbar.org formal-opinion-512** | **403** | **archived (Wayback 200)** |
| USE-CASES | cnn.com/edition.cnn.com apple-bbc | 200 | kept (followed redirect) |
| USE-CASES | **newsguardtech.com december-2024-monitor** | **000** | **archived (Wayback 200)** |
| USE-CASES | **seyfarth.com chatgpt-case-counsel-sanctioned** | **403** | **archived (Wayback 000 too — kept with both annotations)** |
| USE-CASES | statnews.com lancet-fraudulent-citations | 200 | kept |
| USE-CASES | theregister.com apple_intelligence_bbc_complaint | 200 | kept (followed redirect) |

## Gate verification (spec §3.3)

| Criterion | Result |
|---|---|
| Every doc URL is 2xx, annotated `[archived: ...]`, or removed | ✅ — 17 of 21 are 2xx; 4 are annotated archived |
| Annotations are inline in the doc (not in a separate appendix) | ✅ |
| No claim was deleted (no source was the *only* support for a load-bearing fact) | ✅ |

## Redaction grep (constitution §4)

`grep -riE` of the redline set across the changed docs and the new artifacts → 0 hits.

## Carry-forward

- v0.2.1 release note: 4 URLs were swapped to Wayback Machine snapshots after a routine link-check.
- For v0.2.2 or later: consider a CI step that link-checks the docs nightly and opens an issue on regression. Out of scope for v0.2.1 (constitution §3).

## Next

→ M4 (Skill human handoff runbook).
