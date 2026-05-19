---
name: summary-doctor
description: Audit an AI summary against its source. Returns per-claim labels (exact / softened / reversed / fabricated) with verbatim citations. Trigger when the user shares BOTH an AI summary (notification summary, AI overview, LLM TLDR) AND a source (URL, file, pasted text) AND asks "is this summary accurate?", "audit this summary", "check if this summary is faithful", "any fabricated citation?", "what did the speaker actually say?". Do NOT trigger when the user wants a new summary, or when only one side is given.
allowed-tools: Read, Bash(summary-doctor:*), Bash(uvx:*), WebFetch
model: claude-haiku-4-5
---

# summary-doctor

## Quickstart

```bash
summary-doctor <summary> --original <source> --backend claude-cli --out /tmp/audit.md
```

Then `Read` `/tmp/audit.md`. Or call the `audit_summary` MCP tool.

## Steps

1. Readback summary + source ref in one line.
2. Refuse if only one side is provided.
3. Run CLI / MCP. Use `--backend claude-cli --model haiku` if no `ANTHROPIC_API_KEY`.
4. Present:
   - Counts (e.g. "3 reversed / 1 fabricated / 8 exact").
   - Top 1-2 high-signal claims (`reversed` > `fabricated` > `softened`).
   - Quote matched source paragraph verbatim — never paraphrase.
5. Close: "Citation mapping, not a verdict. Reader decides."

## Rules

- Lead with counts, not narrative.
- Quote source verbatim for `reversed` / `fabricated`.
- Confidence < 60 → say "low confidence".
- Paywalled / audio / video source → stop.
