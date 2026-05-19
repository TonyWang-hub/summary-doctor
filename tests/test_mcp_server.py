"""Smoke tests for the MCP server module.

These tests deliberately do NOT start the MCP server over stdio. They only:
- verify the module imports cleanly (with or without the `mcp` package),
- verify the install-hint path raises a useful error when `mcp` is missing,
- verify tool wiring + schema basics when `mcp` is installed,
- verify the helper functions (demo discovery, label parsing) work against
  the bundled demos directory without touching the network or any LLM.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


def test_module_imports_cleanly():
    """`import summary_doctor.mcp_server` must not raise, even when the
    optional `mcp` dependency is missing — the import path falls back to
    a stored exception that is surfaced only on actual server start."""
    mod = importlib.import_module("summary_doctor.mcp_server")
    assert hasattr(mod, "main")
    assert hasattr(mod, "build_server")
    assert hasattr(mod, "_INSTALL_HINT")
    assert "pip install" in mod._INSTALL_HINT


def test_install_hint_mentions_mcp_extra():
    from summary_doctor import mcp_server

    assert "[mcp]" in mcp_server._INSTALL_HINT
    assert "summary-doctor" in mcp_server._INSTALL_HINT


def test_demos_root_resolves_to_bundled_demos():
    from summary_doctor.mcp_server import _demos_root, _list_demo_names

    root = _demos_root()
    assert root.exists(), f"demos root should exist at {root}"
    names = _list_demo_names()
    # v0.1 ships 12 bundled demos
    assert len(names) >= 12
    assert "01-reversal-en" in names
    assert "03-faithful-en" in names


def test_parse_expected_labels_returns_label_rows():
    from summary_doctor.mcp_server import _demos_root, _parse_expected_labels

    readme = (_demos_root() / "01-reversal-en" / "README.md").read_text(
        encoding="utf-8"
    )
    rows = _parse_expected_labels(readme)
    assert rows, "expected at least one parsed label row from demo 01"
    labels_found = {r["expected_label"] for r in rows}
    # demo 01 has reversed + fabricated + exact in its expected table
    assert "reversed" in labels_found
    assert "fabricated" in labels_found


def test_parse_expected_labels_handles_missing_table_gracefully():
    from summary_doctor.mcp_server import _parse_expected_labels

    assert _parse_expected_labels("# title with no table") == []


def _require_mcp() -> None:
    try:
        import mcp.server.fastmcp  # noqa: F401
    except ImportError:
        pytest.skip("mcp package not installed; install with `pip install -e '.[mcp]'`")


def test_build_server_raises_without_mcp_dependency(monkeypatch):
    """If FastMCP is unavailable, build_server() must raise RuntimeError
    with the install hint — not crash with NameError or AttributeError."""
    from summary_doctor import mcp_server

    monkeypatch.setattr(mcp_server, "FastMCP", None)
    monkeypatch.setattr(
        mcp_server, "_IMPORT_ERROR", ImportError("mcp not installed")
    )
    with pytest.raises(RuntimeError) as excinfo:
        mcp_server.build_server()
    assert "[mcp]" in str(excinfo.value)


def test_main_exits_2_without_mcp_dependency(monkeypatch, capsys):
    from summary_doctor import mcp_server

    monkeypatch.setattr(mcp_server, "FastMCP", None)
    with pytest.raises(SystemExit) as excinfo:
        mcp_server.main()
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "pip install" in err


def test_build_server_constructs_when_mcp_present():
    _require_mcp()
    from summary_doctor.mcp_server import build_server

    server = build_server()
    assert server is not None


def test_tools_registered_with_expected_names():
    """audit_summary, get_demo, list_labels must all be registered."""
    _require_mcp()
    from summary_doctor.mcp_server import build_server

    server = build_server()
    # FastMCP exposes registered tools via _tool_manager / list_tools().
    # We probe defensively because the API has shifted across mcp SDK
    # versions; both shapes (manager attribute or async list_tools) are
    # acceptable. Tests only assert presence, not internal layout.
    tool_names: set[str] = set()
    manager = getattr(server, "_tool_manager", None)
    if manager is not None:
        tools = getattr(manager, "_tools", None) or getattr(manager, "tools", None)
        if isinstance(tools, dict):
            tool_names.update(tools.keys())
        elif isinstance(tools, (list, tuple)):
            for t in tools:
                name = getattr(t, "name", None)
                if name:
                    tool_names.add(name)
    if not tool_names:
        # Fall back to async list_tools() if exposed.
        list_tools = getattr(server, "list_tools", None)
        if list_tools is not None:
            import asyncio

            try:
                result = asyncio.get_event_loop().run_until_complete(list_tools())
            except RuntimeError:
                result = asyncio.new_event_loop().run_until_complete(list_tools())
            for t in result:
                name = getattr(t, "name", None) or (
                    t.get("name") if isinstance(t, dict) else None
                )
                if name:
                    tool_names.add(name)
    expected = {"audit_summary", "get_demo", "list_labels"}
    missing = expected - tool_names
    assert not missing, (
        f"tools not registered: {missing}; found {tool_names}"
    )


def test_list_labels_payload_shape():
    """Smoke-call list_labels via the underlying helper to verify the
    payload shape used by clients."""
    _require_mcp()
    # The tool callable is wrapped by FastMCP; easiest path is to rebuild
    # the same dict the tool returns by calling a fresh build_server and
    # invoking the registered tool function if reachable. As a safer
    # alternative we reconstruct by inspecting list_labels() output via
    # an in-process call site.
    from summary_doctor.mcp_server import build_server

    server = build_server()
    manager = getattr(server, "_tool_manager", None)
    assert manager is not None, "FastMCP changed its internal layout"
    tools = getattr(manager, "_tools", None) or getattr(manager, "tools", {})
    # tools is a dict[name -> Tool] in current FastMCP; each Tool has a
    # `.fn` callable.
    if isinstance(tools, dict) and "list_labels" in tools:
        tool = tools["list_labels"]
        fn = getattr(tool, "fn", None) or getattr(tool, "func", None)
        if fn is not None:
            payload = fn()
            assert "labels" in payload
            assert "disclaimer" in payload
            assert "demos" in payload
            names = {entry["name"] for entry in payload["labels"]}
            assert names == {"exact", "softened", "reversed", "fabricated"}


def test_get_demo_returns_summary_and_source():
    _require_mcp()
    from summary_doctor.mcp_server import build_server

    server = build_server()
    manager = getattr(server, "_tool_manager", None)
    assert manager is not None
    tools = getattr(manager, "_tools", None) or getattr(manager, "tools", {})
    if isinstance(tools, dict) and "get_demo" in tools:
        tool = tools["get_demo"]
        fn = getattr(tool, "fn", None) or getattr(tool, "func", None)
        if fn is not None:
            payload = fn(demo_name="03-faithful-en")
            assert payload["name"] == "03-faithful-en"
            assert payload["summary"].strip()
            assert payload["source"].strip()
            assert isinstance(payload["expected_labels"], list)


def test_get_demo_rejects_unknown_name():
    _require_mcp()
    from summary_doctor.mcp_server import build_server

    server = build_server()
    manager = getattr(server, "_tool_manager", None)
    assert manager is not None
    tools = getattr(manager, "_tools", None) or getattr(manager, "tools", {})
    if isinstance(tools, dict) and "get_demo" in tools:
        tool = tools["get_demo"]
        fn = getattr(tool, "fn", None) or getattr(tool, "func", None)
        if fn is not None:
            with pytest.raises(ValueError):
                fn(demo_name="does-not-exist")
