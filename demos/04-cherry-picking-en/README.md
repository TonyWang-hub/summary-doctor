# Demo 4 — Cherry-picking (English)

This demo is synthetic. Any resemblance to specific real panels, districts,
or organizations is unintended.

## Failure mode

**Selective citation**: the summary lifts only the source sentences that
support a one-sided pro-coding-block read, and drops the equity warning, the
"net negative on math" data point, and the explicit "no long-term evidence"
caveat. Each surviving sentence is technically faithful, but the *aggregate*
picture flips from "conditional support with three open risks" to "qualified
endorsement".

## Expected audit

| Claim from summary | Expected label | Why |
|---|---|---|
| "measurable lift in willingness to attempt multi-step problems" | exact | Source has the same finding |
| "consistently across all three pilot districts" | exact | Source says the same |
| "districts that invested in teacher training saw measurable benefit" | **softened** | Source pairs this with the contrapositive (under-investment caused *net negative* on math) — summary drops the negative branch |
| "a primary-school coding block can be defended in a rollout plan" | **softened** (or reversed) | Source says "conditional support, not endorsement" and requires equity gap + training cost + modest evidence all be addressed — summary strips every qualifier |
| (missing) equity-gap warning | — | Cherry-picking is partly a *what's missing* failure; the audit per-claim view will not flag absent content. The reader is expected to notice the omission from the per-claim list being short. |

The hardest part of cherry-picking is that every surviving sentence may match
the source verbatim. A per-claim auditor that only scores *what is present*
will under-report the failure. This demo exists to make that limitation
visible.

## How to run

```bash
summary-doctor demos/04-cherry-picking-en/summary.txt \
  --original demos/04-cherry-picking-en/source.txt \
  --lang en --mock
```
