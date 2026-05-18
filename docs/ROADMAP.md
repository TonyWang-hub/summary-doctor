# Roadmap

## v0.1 (MVP — this release)

- [x] 5-stage pipeline (input → extract → decompose → map+classify → report)
- [x] `--mock` mode for offline pipeline validation
- [x] Anthropic Claude backend (Haiku 4.5 default, Opus 4.7 escalation)
- [x] 4-class labels with citations
- [x] Markdown + JSON output
- [x] 3 public demo cases (no private data)
- [ ] Self-audit CI step

## v0.2

- [ ] Cross-language alignment (zh ↔ en)
- [ ] ASR for audio/video summaries
- [ ] Chunked source handling (>200k tokens)
- [ ] Confidence calibration on a labeled benchmark

## v0.3

- [ ] Chrome / Edge extension: intercept "AI summary" cards on common platforms
- [ ] Batch mode: audit a folder of summaries against a corpus
- [ ] Skill manifest for Claude Code / Cursor integration

## Out of scope (now and likely forever)

- Author / publisher reputation scoring
- "Truth oracle" verdicts — this tool emits citations, not verdicts
- Real-time stream auditing
