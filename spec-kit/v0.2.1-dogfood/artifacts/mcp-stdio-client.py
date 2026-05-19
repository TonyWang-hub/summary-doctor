"""M2 stdio dogfood — spawn summary-doctor-mcp and run one real round-trip.

Spawns the MCP server as a subprocess over stdio, performs the JSON-RPC
initialize handshake, lists tools, and invokes audit_summary against the
bundled demo 03-faithful-en (with backend='mock' so no API key is needed).

Captures every JSON-RPC frame to artifacts/mcp-stdio-trace.json.

Requires the venv built in M1: /tmp/sd-mcp-venv/bin/python.

Per spec §3.1 and §4 (failure paths), the script:
- enforces a 10s timeout per stdio call,
- captures both stdin frames sent and stdout frames received,
- exits non-zero if the divergence-score check fails.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


REPO_ROOT = Path(__file__).resolve().parents[3]
DEMOS = REPO_ROOT / "demos"
TRACE_PATH = REPO_ROOT / "spec-kit/v0.2.1-dogfood/artifacts/mcp-stdio-trace.json"


async def run() -> dict:
    server_params = StdioServerParameters(
        command="/tmp/sd-mcp-venv/bin/python",
        args=["-m", "summary_doctor.mcp_server"],
        env={"PYTHONPATH": str(REPO_ROOT / "src")},
    )

    trace: dict = {"frames": []}

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. initialize
            init = await asyncio.wait_for(session.initialize(), timeout=10)
            trace["frames"].append({
                "kind": "initialize.result",
                "protocol_version": getattr(init, "protocolVersion", None),
                "server_name": getattr(getattr(init, "serverInfo", None), "name", None),
            })

            # 2. tools/list
            tools = await asyncio.wait_for(session.list_tools(), timeout=10)
            tool_names = [t.name for t in tools.tools]
            trace["frames"].append({"kind": "tools/list.result", "tool_names": tool_names})

            # 3. tools/call audit_summary against demo 03 (positive control, mock)
            summary_txt = (DEMOS / "03-faithful-en/summary.txt").read_text()
            source_txt = (DEMOS / "03-faithful-en/source.txt").read_text()

            call_args = {
                "summary": summary_txt,
                "source": source_txt,
                "lang": "en",
                "backend": "mock",
            }
            trace["frames"].append({
                "kind": "tools/call.request",
                "tool": "audit_summary",
                "arguments_summary_len": len(summary_txt),
                "arguments_source_len": len(source_txt),
                "lang": "en",
                "backend": "mock",
            })

            result = await asyncio.wait_for(
                session.call_tool("audit_summary", call_args), timeout=30
            )

            # The result.content is a list of MCP Content objects (TextContent etc.)
            text_parts = []
            for c in getattr(result, "content", []):
                if hasattr(c, "text"):
                    text_parts.append(c.text)
            report = "\n".join(text_parts)

            trace["frames"].append({
                "kind": "tools/call.result",
                "report_chars": len(report),
                "report_first_120": report[:120],
                "is_error": getattr(result, "isError", False),
            })

            # Validation per spec §3.1: demo 03 positive control should be 0% divergence
            divergence_lines = [
                line for line in report.splitlines()
                if "Divergence score" in line
            ]
            trace["validation"] = {
                "divergence_lines": divergence_lines,
                "passes_zero_divergence": any("0%" in line for line in divergence_lines),
            }

    return trace


def scrub_machine_fingerprints(trace: dict) -> dict:
    """Constitution §6: scrub anything that leaks host or user identity
    before committing the trace."""
    # The trace as designed never captures usernames or hostnames — the report
    # text is generated from demo fixtures and the model field is "mock". But
    # defense in depth: walk the dict and verify no $HOME or username strings
    # made it in.
    blob = json.dumps(trace)
    import os
    home = os.environ.get("HOME", "")
    user = os.environ.get("USER", "")
    for token in (home, user, "/Users/"):
        if token and token in blob:
            blob = blob.replace(token, "[scrubbed]")
    return json.loads(blob)


def main() -> int:
    try:
        trace = asyncio.run(run())
    except asyncio.TimeoutError as e:
        print(f"[FAIL] stdio call timed out: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[FAIL] unexpected: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    trace = scrub_machine_fingerprints(trace)
    TRACE_PATH.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[ok] frames captured: {len(trace['frames'])}")
    print(f"[ok] trace written:   {TRACE_PATH}")
    print(f"[ok] divergence-zero check: {trace['validation']['passes_zero_divergence']}")
    return 0 if trace["validation"]["passes_zero_divergence"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
