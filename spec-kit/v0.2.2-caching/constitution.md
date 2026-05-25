# Constitution — v0.2.2 caching

Inherits the six rules from `spec-kit/v0.2.1-dogfood/constitution.md`
verbatim. Adds one rule specific to this patch.

## §1–§6 (inherited)

1. Honesty over coverage
2. Two carify rounds before any code change
3. No drive-by improvements
4. Redaction discipline
5. Reversibility before authority
6. SDD artefacts stay versioned

Read those first.

## §7 (new) — Cache-hit is a measured signal, not a code claim

For this patch, "caching works" means **`cache_read_input_tokens > 0` on
the second call in a repeat-source scenario, captured to an artefact**.
Not "the code compiles", not "the tests pass", not "the cache_control
parameter is present in the request body".

Implications:

- M2 gate requires a real captured Anthropic-SDK response showing
  `usage.cache_read_input_tokens > 0`. No green CI here is a proxy.
- EVALUATION.md's caching row is filled from the artefact, not from a
  README example.
- If the artefact shows zero cache reads, the patch failed even if
  pytest is green. Diagnose, fix, re-capture — do not ship.

This is exactly the v0.2.0 → v0.2.1 lesson restated for v0.2.2:
**schema-level success doesn't imply runtime success.**
