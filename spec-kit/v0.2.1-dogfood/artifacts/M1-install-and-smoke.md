# M1 — MCP install + smoke · run log

## §1 PyPI metadata (T1.1)

`WebFetch https://pypi.org/pypi/mcp/json` returned:
- Latest stable: **1.27.1**
- Supported Python versions: **3.10, 3.11, 3.12, 3.13** (no 3.14)
- Install size: ~211 KB wheel
- `FastMCP` class confirmed present

## §2 Install-strategy decision (T1.2)

Open assumption #3 in `00-spec.md` was that Python 3.14 (the system Python on this machine) might be supported. **Falsified by §1**: mcp 1.27.1 stops at 3.13. Per `01-plan.md` M1 fallback, we go to a venv.

System has `/opt/homebrew/bin/python3.12` (3.12.3). We use it. No need to bring up 3.13.

## §3 Install execution (T1.3)

```bash
/opt/homebrew/bin/python3.12 -m venv /tmp/sd-mcp-venv
/tmp/sd-mcp-venv/bin/pip install --quiet 'mcp>=0.9.0' pytest 'anthropic>=0.40'
```

Result: silent OK (only pip's own "new release available" notice). `mcp` import works; `from mcp.server.fastmcp import FastMCP` import works.

## §4 Test results (T1.4)

```bash
PYTHONPATH=src /tmp/sd-mcp-venv/bin/python -m pytest tests/test_mcp_server.py -v
```

Result: **12 passed, 0 skipped** in 0.34s.

Test inventory:
1. `test_module_imports_cleanly` ✅
2. `test_install_hint_mentions_mcp_extra` ✅
3. `test_demos_root_resolves_to_bundled_demos` ✅
4. `test_parse_expected_labels_returns_label_rows` ✅
5. `test_parse_expected_labels_handles_missing_table_gracefully` ✅
6. `test_build_server_raises_without_mcp_dependency` ✅
7. `test_main_exits_2_without_mcp_dependency` ✅
8. `test_build_server_constructs_when_mcp_present` ✅ ← was skipped in baseline
9. `test_tools_registered_with_expected_names` ✅ ← was skipped in baseline
10. `test_list_labels_payload_shape` ✅ ← was skipped in baseline
11. `test_get_demo_returns_summary_and_source` ✅ ← was skipped in baseline
12. `test_get_demo_rejects_unknown_name` ✅ ← was skipped in baseline

## §5 Source patches (T1.5)

None required. `mcp_server.py` imported cleanly against `mcp` 1.27.1 and FastMCP signature matched. `build_server()` returned a populated server object on first try.

## Gate verification

| Gate criterion | Result |
|---|---|
| 5 previously-skipped MCP tests now pass | ✅ all 5 + 7 existing = 12 pass |
| pyproject `[mcp]` extras installable on a supported Python | ✅ venv on 3.12 |
| No source code changes required to make tests pass | ✅ |

## Carry-forward

- **README update needed**: `pip install -e '.[mcp]'` requires Python 3.10-3.13. Add this constraint near the MCP server section. Falls under M3 / M5 (doc patch).
- M2 must use the same venv (`/tmp/sd-mcp-venv`) and `PYTHONPATH=/Users/tony/Documents/work/ai/cloud_gh_project/summary-doctor/src` to talk to the MCP server.
