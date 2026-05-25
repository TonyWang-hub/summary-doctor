# M0 — Baseline · close-out

**Status**: ⚠️ Gate passed, but a load-bearing spec assumption was falsified.
**Wall clock**: ~5 min
**Artifact**: `artifacts/M0-baseline-claude-cli.json` (this file's findings)

## Carify round 1 — engineer's view

The probe approach was right: hit `claude -p --output-format json` and
parse the `result` event's `usage` field. The shape is stable across
calls (every result event has `cache_creation_input_tokens`,
`cache_read_input_tokens`, and `cache_creation.ephemeral_{1h,5m}_input_tokens`).

What I did NOT anticipate: cache scope is finer than I assumed.

## Carify round 2 — tester's view

Three back-to-back tests:

| # | Setup | cache_creation | cache_read | ephem_1h | ephem_5m |
|---|---|---:|---:|---:|---:|
| probe | "What is 2+2?" (small) | 40,349 | 0 | 40,349 | 0 |
| A1 | full prompt, 1st run | 41,439 | 0 | 41,439 | 0 |
| A2 | **same prompt as A1**, 2nd run | 42,251 | 0 | 42,251 | 0 |
| B1 | different prompt | 5,145 | **36,670** | 5,145 | 0 |

The pattern: A2 missed despite identical bytes to A1, but B1 hit despite
DIFFERENT prompt bytes. The cache_read in B1 must therefore correspond
to something other than user-prompt content.

**Hypothesis** (validated by inspection): the ~36K-token block that B1
read is **Claude Code's own system prompt + tools bundle** — the
internal context the CLI prepends to every `-p` invocation. That bundle
is byte-stable across invocations and gets cached at the platform level.

The **user prompt bytes are NOT cached cross-invocation** in claude-cli
mode. Each `claude -p` launches a fresh session whose user-prompt cache
is independent of prior sessions.

## Bug captured — but in our spec, not our code

Spec rev 2 §3.6 claimed:

> claude-cli — Auto — Claude Code subscription manages prompt caching
> internally. We see the result via `result.usage.cache_*` fields.

That's true at the **platform level** (Claude Code's system prefix
caches), but false at the **user-prompt level** (re-sending the same
`summary-doctor`-built prompt does not produce a cache_read on the
user content).

Net effect for v0.2.2's thesis: **claude-cli users on the
`summary-doctor` workflow do NOT automatically get cross-invocation
cache savings on their summary/source content**. They get a fixed ~36K
read on Claude Code's own scaffolding, which is platform-level and
unrelated to anything `summary-doctor` does.

## Implication for the rest of v0.2.2

The v0.2.2 patch's value now has three components, none of which is
"users save tokens on repeat summary-doctor calls via claude-cli":

1. **Transparency** — plumb `usage` from the claude-cli envelope so
   users can SEE what Claude Code already caches at the platform level.
   This is a 36K freebie that today is invisible.
2. **Anthropic SDK parity** — add explicit `cache_control` so SDK users
   (with API key) can get prompt-level cache reuse when they re-audit
   the same source. Verification deferred to v0.2.3 (needs API key).
3. **Defensive testing** — `tests/test_cache_prefix.py` locks
   prompt-byte stability so future prompt edits don't silently destroy
   either backend's cache potential.

**What v0.2.2 does NOT do, against original intent**: it does NOT make
the claude-cli backend faster or cheaper on repeat-source workflows.
This must be documented honestly in `CHANGELOG.md`, `EVALUATION.md`,
and any README mention.

## Gate verification

| Criterion | Result |
|---|---|
| `claude -p --output-format json` envelope exposes `usage.cache_*` fields | ✅ |
| Baseline numbers captured | ✅ (this document) |
| Cross-invocation cache behavior characterized | ✅ (falsified assumption) |

## Redaction grep

`grep -riE` of the redline set on `spec-kit/v0.2.2-caching/milestones/M0-*` → 0 hits.

## Carry-forward

- **Spec §3.6 needs rev 3**: the "auto cache cross-invocation" framing
  is wrong. Rewrite to distinguish platform-level cache (auto, always-on,
  user-prompt-independent) from prompt-level cache (requires manual
  `cache_control` on Anthropic SDK, not available cross-invocation
  through claude-cli at all).
- **M2 gate needs revision**: "cache_read > 0 on call 2" is **trivially
  true** for any claude-cli call beyond the very first ever (because of
  the platform-level Claude Code system cache). That's not a meaningful
  signal that summary-doctor's caching design works. M2 should instead
  measure **the difference between the user-prompt-content tokens
  re-sent on call 1 vs call 2** — and v0.2.2 will likely show no
  difference, which is the honest finding.

## Decision point for the user

Three paths forward:

| Path | What it gets |
|---|---|
| A. **Ship v0.2.2 as transparency + SDK parity** — drop the "cost reduction" framing; sell the plumbing + the SDK code change + the prefix-stability test. | Honest patch, modest user value, low risk. |
| B. **Get an API key and verify Anthropic SDK manually** — the only path where summary-doctor's caching design actually produces cross-invocation user-prompt reuse. | High-value patch with real measurement, costs ≤$0.20 + maintainer ops time. |
| C. **Abandon v0.2.2; pivot to v0.3 P3 (chunking)** — caching turned out to be a smaller lever than expected; chunking is the larger one. | Largest signal-to-noise, but throws away ~30min of M0 work and the spec-kit. |

Spec rev 3 will reflect the user's choice.
