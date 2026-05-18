DECOMPOSE_PROMPT = """You are an assistant that splits a summary into atomic
assertive claims. A claim is a single declarative statement that could be
checked against a source.

Language hint: {lang}

Return ONLY a JSON array of strings. No prose, no markdown.

Summary:
---
{summary}
---
"""


CLASSIFY_PROMPT = """You are an audit assistant. For each claim in the list,
find the most relevant paragraph in the source and label the claim with ONE of:

- "exact"      : source supports the claim (paraphrase OK)
- "softened"   : direction is preserved but qualifiers or strength are lost
- "reversed"   : source contradicts or inverts the claim
- "fabricated" : source does not contain anything supporting the claim

Rules:
- Quote the matched paragraph verbatim (max 400 characters). If none, return null.
- Confidence is an integer 0-100 reflecting your certainty.
- Rationale is one short sentence explaining the label.
- You output a citation map, not a verdict. The reader will judge.

Language hint: {lang}

Return ONLY a JSON array of objects with keys:
  claim, matched_paragraph, label, confidence, rationale.
No prose, no markdown.

Claims (JSON):
{claims}

Source:
---
{source}
---
"""
