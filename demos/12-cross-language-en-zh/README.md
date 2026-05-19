# Demo 12 — Cross-language (EN source → 中文 summary)

This demo is synthetic. Any resemblance to specific real researchers,
clusters, or audits is unintended.

## Failure mode

**Cross-language boundary test**: the source is English, the AI-generated
summary is in **Chinese**. Cross-language alignment is on the v0.2
roadmap (see [`docs/ROADMAP.md`](../../docs/ROADMAP.md)); this demo is a
forward-looking test fixture for that milestone. Under v0.1 the `--mock`
backend does not align tokens across languages, so divergence scoring may
under-report — the demo is here to make that limitation visible, not to
claim the mock backend handles it.

The summary contains a mix:

- two faithful items (cooling-water 2.4×; embodied carbon 38–46%)
- one **reversed** item: the summary says delay scheduling is "a general
  decarbonisation approach applicable to all scientific computing
  clusters", while the source explicitly warns *not* to quote the figure
  as a generic expected outcome
- one **fabricated** item: the summary says "embodied carbon does not
  meaningfully affect total emissions; the focus should be on operational
  carbon" — the source says exactly the opposite (embodied and
  operational are of *comparable magnitude*; the speaker explicitly
  rejects the framing that hardware is clean)

## Expected audit (when v0.2 cross-language is online)

| Claim from summary | Expected label | Why |
|---|---|---|
| "集群冷却基础设施的实际耗水量是此前公开盘点数字的 2.4 倍" | exact | Source: "roughly 2.4 times the previously reported number" |
| "硬件制造环节的'内含碳'占六年服役期总排放的 38% 到 46%" | exact | Source: "between 38 and 46 percent of lifetime emissions" |
| "延迟调度是适用于所有科学计算集群的通用降排方案" | **reversed** | Source: "the figure should not be quoted as a generic expected outcome"; the speaker explicitly limits to one grid, one season |
| "硬件制造导致的内含碳并不会对总排放产生明显影响，真正的减排重点应当放在运行阶段" | **fabricated** (or reversed) | Source: embodied and operational are of "comparable magnitude"; the speaker explicitly rejects "running compute is dirty and building hardware is clean" |

## Why this is hard

Under v0.1, the mock backend pattern-matches keywords character-by-character
and has no cross-language lexicon. Many of the Chinese summary claims will
fail to match an English source paragraph at all, which the mock backend
labels as `fabricated` for *all* claims — including the two that are
actually faithful. That is a false-positive failure mode of the mock
backend, not of the project: it correctly *does not go silent* on a
known-bad cross-language summary, but it cannot tell the faithful claims
apart from the truly fabricated ones.

The pipeline-level test for this demo therefore only asserts:

- the pipeline does not crash on EN + ZH input
- at least one high-signal label (`reversed` or `fabricated`) surfaces

This makes the v0.1 → v0.2 boundary visible in the test suite.

## How to run

```bash
summary-doctor demos/12-cross-language-en-zh/summary.txt \
  --original demos/12-cross-language-en-zh/source.txt \
  --lang auto --mock
```
