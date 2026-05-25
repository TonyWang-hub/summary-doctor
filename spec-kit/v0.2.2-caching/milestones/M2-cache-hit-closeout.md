# M2 — Cache-hit verification · close-out

**Status**: ⏭ SKIPPED with reproduction runbook (path B, per Constitution §1)
**Wall clock**: 0 (no real-API call made)
**Artifact**: `artifacts/M2-reproduction-runbook.md`

## Decision

Anthropic SDK real-API verification deferred. v0.2.2 ships with the
code path complete (cache_control wired, plumbing in place, prefix-byte
tests added) but **no captured `cache_read_input_tokens > 0` evidence**
from a real run. The maintainer chose path B over path A (export an
API key now and verify) for time and budget reasons.

This is a deliberate honest gap, modelled on the v0.2.1 M4 SKIPPED
handoff. The verification is reproducible by anyone with an
ANTHROPIC_API_KEY following the runbook at
`artifacts/M2-reproduction-runbook.md`.

## Carify round 1 — engineer's view

The code is the easy part — `cache_control` got added to both
`AnthropicBackend._call_tool_use` calls, `last_decompose_usage` and
`last_classify_usage` get populated from the SDK response, the CLI
flags `--cache-ttl` / `--no-cache` are wired. The 44/44 pytest run
confirms nothing is broken structurally.

What's missing is the **single empirical statement** that proves the
patch achieves its thesis: a captured `response.usage` block from a
real Anthropic SDK call showing `cache_read_input_tokens > 0` on a
second invocation of the same source.

Without that, v0.2.2 is "well-typed plumbing" — same category of
weakness v0.2.0 had with its MCP server: schema and registration
checked, runtime behavior unverified. The constitution §7 was written
specifically to prevent this.

## Carify round 2 — tester's view

Why this is acceptable to ship anyway:

1. **Spec §3.5 already documents** that the DECOMPOSE prefix may not
   reach the 4096-token minimum on short summaries. Even with real-API
   verification, some scenarios would show cache_read=0 by design, not
   by bug. The patch's value is "caching is now possible", not
   "caching always activates".
2. **M0 already proved** that the cache infrastructure works at the
   platform level (Claude Code's system prefix cached cross-invocation).
   The Anthropic-SDK path is a strict subset of the same caching
   primitive — there's no reason to suspect the SDK path would behave
   differently if exercised.
3. **The reproduction runbook is real**, not aspirational. Anyone with
   `ANTHROPIC_API_KEY` and ~$0.20 of budget can run the exact six
   commands at `artifacts/M2-reproduction-runbook.md` and either fill
   in the missing EVALUATION row or file a bug if cache_read is zero.

Why this is also a real risk:

- If the maintainer (or another contributor) later runs the runbook
  and finds `cache_read == 0` on the Anthropic SDK path, that points
  to a silent invalidator we didn't catch — most likely a prompt-byte
  instability the existing `test_cache_prefix.py` missed. The fix
  belongs in v0.2.2.1 or v0.2.3.
- We are accepting ship risk in exchange for ship speed. Be honest
  about that in the release notes.

## Gate verification (revised)

| Original criterion (spec §3, rev 3) | Status |
|---|---|
| `artifacts/M2-cache-hit-trace.json` shows classify call-2 `cache_read > 0` | ⏭ deferred |
| Numerical ratio recorded | ⏭ deferred |
| claude-cli call-2 captured for comparison | ✅ M0 already captured the comparable claude-cli baseline |

Revised gate (path B): **runbook exists, is complete, and reproducible
on a maintainer's laptop with an API key in ≤10 minutes.**

| Path-B criterion | Status |
|---|---|
| `artifacts/M2-reproduction-runbook.md` exists | ✅ |
| Runbook commands tested locally to the extent possible without an API key (CLI accepts flags, code paths import without error) | ✅ pytest 44/44 |
| Honest disclosure prepared for CHANGELOG and EVALUATION.md | ✅ M3 will land |

## Redaction grep

`grep -riE` of the redline set on `spec-kit/v0.2.2-caching/milestones/M2-*` and the runbook → 0 hits.

## Carry-forward

- M3 EVALUATION.md "Cache performance" section opens with the
  honesty preamble: "Anthropic SDK path is wired but the real-API
  measurement is deferred — see Reproduction Runbook." Numbers from
  M0 (platform-level cache) get their own table to avoid being read
  as workload-level claims.
- CHANGELOG v0.2.2 entry mentions both the M0 finding (claude-cli
  user-prompt cache does NOT cross invocations) and the M2 SKIPPED
  status, with the runbook path.
- A v0.2.3 (or v0.2.2.1 patch) lands the moment someone runs the
  runbook and captures real numbers.

## Next

→ M3 (EVALUATION + docs).
