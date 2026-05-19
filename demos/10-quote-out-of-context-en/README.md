## Failure mode

**Quote out of context**: the summary lifts the scientist's one headline
sentence verbatim ("a city-wide plastic carrier-bag ban does reduce visible
shoreline litter within the first eighteen months") and drops the
immediately-following clarification that fences this finding behind three
specific preconditions. The summary then escalates the lifted sentence into
a general endorsement, and inverts the economist's actual point —
the economist said the three preconditions *do not hold* in two-thirds of
the sample, while the summary reports the opposite. The moderator's
closing line is also fabricated: the source explicitly says the panel did
*not* land on "works or does not work".

## Expected audit

| Claim from summary | Expected label | Why |
|---|---|---|
| "a city-wide plastic carrier-bag ban does reduce visible shoreline litter within the first eighteen months" | **softened** | The sentence is present in the source verbatim, but only as the conditional half of a sentence whose clarification reverses the conclusion under three boundary conditions. Lifting the headline alone loses the qualifiers. |
| "The panel therefore endorsed plastic carrier-bag bans as an effective municipal environmental policy" | **reversed** | Source explicitly says the panel's consensus was *not* "bans work or do not work" and that policy is context-conditional. |
| "curbside soft-plastic recovery is now standard infrastructure across the small inland municipalities in their study sample" | **reversed** | Source says the opposite: none of the three preconditions hold in roughly two-thirds of those municipalities. |
| "the moderator confirmed at the close that the panel reached a clear consensus in favor of plastic carrier-bag bans" | **fabricated** | No such statement appears in source; the moderator's actual closing line is the opposite. |

## Why this is hard

Quote-out-of-context is the failure mode where every individual word in the
lifted sentence is real, the lifted sentence is even attributable to the
correct speaker, and yet the *meaning* once detached from its clarifier is
the opposite of the speaker's position. A polarity-only auditor sees the
words match and is tempted to mark `exact`. The correct label requires the
auditor to notice that the source attaches a clarifier within the same
paragraph that flips the conclusion under boundary conditions, and that the
clarifier is missing from the summary. This is the boundary between
`exact` and `softened`, and it is one of the hardest calls in summary
faithfulness.

## How to run

```bash
summary-doctor demos/10-quote-out-of-context-en/summary.txt \
  --original demos/10-quote-out-of-context-en/source.txt \
  --lang en --mock
```
