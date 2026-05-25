# M2 reproduction runbook — Anthropic SDK cache_read verification

> v0.2.2 ships with the code path complete but **no captured
> `cache_read_input_tokens > 0` evidence** from a real Anthropic API
> call. This runbook is the reproducible procedure for filling that
> gap. Estimated cost: **~$0.10–$0.20 of Anthropic API spend**.
> Estimated time: **~10 minutes**.

## Why this matters

The whole point of v0.2.2 is that **repeat-source audits via the
Anthropic SDK backend** should pay drastically less on the second call
than the first, via prompt caching. The code adds `cache_control` at
the top level of every `client.messages.create()` call. Whether that
actually produces a `cache_read_input_tokens > 0` is a runtime
question — `pytest` can't answer it.

## Prerequisites

1. An `ANTHROPIC_API_KEY` with at least $1 of budget.
2. Python 3.10–3.13 (the `anthropic` SDK supports up to 3.13 — Python
   3.14 is not supported as of mcp 1.27.1; see v0.2.1 M1 close-out).
   The reused `/tmp/sd-mcp-venv` from v0.2.1 has anthropic ≥0.40 — use
   that if it still exists.
3. The summary-doctor repo at v0.2.2 (or HEAD with v0.2.2 changes).

## The six commands

Open a fresh shell at the repo root.

```bash
# 1. Activate / build a Python 3.12 venv with the anthropic SDK.
#    Reuse the v0.2.1 venv if it survived:
test -x /tmp/sd-mcp-venv/bin/python || /opt/homebrew/bin/python3.12 -m venv /tmp/sd-mcp-venv
/tmp/sd-mcp-venv/bin/pip install --quiet -e '.[anthropic]'

# 2. Set the API key in THIS shell only (do not commit, do not export
#    globally):
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Prepare the same-source pair we use as the canonical repeat-source
#    scenario in the self-audit workflow:
cat docs/SPEC.md docs/ROADMAP.md > /tmp/sd-source.txt
wc -c /tmp/sd-source.txt README.md   # expect ~7KB + ~12KB (both well over 4096 tokens)

# 4. First call — expect cache_creation > 0, cache_read = 0:
PYTHONPATH=src /tmp/sd-mcp-venv/bin/python -m summary_doctor README.md \
    --original /tmp/sd-source.txt \
    --lang en \
    --backend anthropic \
    --cache-ttl 5m \
    --model claude-haiku-4-5-20251001 \
    --out /tmp/sd-m2-call1.md

# 5. Second call — expect cache_read > 0 if v0.2.2 thesis holds:
PYTHONPATH=src /tmp/sd-mcp-venv/bin/python -m summary_doctor README.md \
    --original /tmp/sd-source.txt \
    --lang en \
    --backend anthropic \
    --cache-ttl 5m \
    --model claude-haiku-4-5-20251001 \
    --out /tmp/sd-m2-call2.md

# 6. Inspect both runs' last_usage. The CLI does not currently print
#    usage; pull it from the JSON sidecar (Pipeline plumbing planned
#    for v0.2.2.1) or run the SDK directly via:
PYTHONPATH=src /tmp/sd-mcp-venv/bin/python <<'PY'
from summary_doctor.backends import get_backend
from summary_doctor.pipeline import Pipeline

backend = get_backend(mock=False, backend="anthropic",
                     model="claude-haiku-4-5-20251001", cache_ttl="5m")
p = Pipeline(backend=backend, lang="en")

# Call 1
p.run(summary_ref="README.md", source_ref="/tmp/sd-source.txt")
call1_classify = backend.last_classify_usage

# Call 2
p.run(summary_ref="README.md", source_ref="/tmp/sd-source.txt")
call2_classify = backend.last_classify_usage

import json
print("call1 classify usage:")
print(json.dumps(call1_classify, indent=2))
print("call2 classify usage:")
print(json.dumps(call2_classify, indent=2))

# The thesis: call2's cache_read_input_tokens > 0
PY
```

## Expected output (thesis-holds case)

```
call1 classify usage:
{
  "input_tokens": ...,           # most of the prompt
  "cache_creation_input_tokens": <large>,  # write to cache
  "cache_read_input_tokens": 0,            # nothing to read yet
  "output_tokens": ...
}
call2 classify usage:
{
  "input_tokens": <small>,                 # only the variable suffix
  "cache_creation_input_tokens": 0,        # already cached
  "cache_read_input_tokens": <large>,      # served from cache ✓
  "output_tokens": ...
}
```

## Outcomes

| Result | Action |
|---|---|
| **call2 cache_read > 0**: thesis confirmed | Update `docs/EVALUATION.md` "Cache performance" table with the actual numbers. Ship v0.2.2.1 (or amend v0.2.2 release notes). |
| **call2 cache_read = 0**: silent invalidator | Capture both calls' request bodies (set `httpx` logging on the SDK client, or use SDK debug mode). Diff them byte-by-byte. The first difference is the invalidator. Fix prompts.py or anthropic.py. Re-run. |
| **call2 cache_read > 0 for classify but not decompose**: expected | Decompose prompt is often <4096 tokens (cache minimum on Haiku 4.5). Document in EVALUATION.md as known limit, not as bug. |
| **Both calls error out**: SDK / model / API issue | Check `ANTHROPIC_API_KEY` validity, check model id `claude-haiku-4-5-20251001` is still active, check anthropic SDK version `>=0.40`. |

## What to do with the captured numbers

1. Update `docs/EVALUATION.md` "Cache performance" section.
2. Add the captured `usage` dicts to `spec-kit/v0.2.2-caching/artifacts/M2-cache-hit-trace.json`.
3. If thesis confirmed: ship as v0.2.2.1 patch with "M2 verified" note.
4. If thesis broken: ship as v0.2.2.1 patch with the fix + the captured
   bisection that found the invalidator.

## Pipeline plumbing TODO (v0.2.2.1)

Currently `backend.last_classify_usage` is set on the backend object but
NOT exposed in the JSON sidecar that summary-doctor writes. Step 6
above works around this by re-calling Pipeline.run programmatically.
The proper fix is a one-line change in `pipeline.py` to attach usage
to the Report. Deferred to v0.2.2.1 to keep this patch's surface area
minimal.
