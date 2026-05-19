"""MCP server entry point for summary-doctor.

Thin FastMCP facade that exposes three tools:

- ``audit_summary``: full pipeline audit, returns a markdown report.
- ``get_demo``: returns the bundled demo content (summary + source + expected
  labels) so MCP clients can preview the tool without burning tokens.
- ``list_labels``: returns the 4-class label taxonomy and when each label
  applies.

All tools call into :mod:`summary_doctor.pipeline` and the existing backends.
The MCP server adds no behavioral fork.

Run via the ``summary-doctor-mcp`` console script (installed when this
package is installed with the ``[mcp]`` extra).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# --- FastMCP import with friendly fallback -----------------------------------

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore
except ImportError as _import_err:  # pragma: no cover - exercised manually
    _IMPORT_ERROR: Exception | None = _import_err
    FastMCP = None  # type: ignore[assignment]
else:
    _IMPORT_ERROR = None


_INSTALL_HINT = (
    "summary-doctor MCP server requires the `mcp` Python package.\n"
    "Install it with:\n"
    "\n"
    "    pip install -e '.[mcp]'\n"
    "\n"
    "or, from PyPI once published:\n"
    "\n"
    "    pip install 'summary-doctor[mcp]'\n"
    "\n"
    "See docs/launch/research/D-ecosystem-integration.md for client config "
    "snippets (Claude Desktop, Cursor, Zed, Continue.dev)."
)


# --- helpers -----------------------------------------------------------------

_VALID_BACKENDS = ("anthropic", "claude-cli", "mock")
_VALID_LANGS = ("zh", "en", "auto")


def _demos_root() -> Path:
    """Return the bundled ``demos/`` directory next to this package."""
    # src/summary_doctor/mcp_server.py -> repo_root/demos
    return Path(__file__).resolve().parents[2] / "demos"


def _list_demo_names() -> list[str]:
    root = _demos_root()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


# README expected-label table is the source of truth for "expected_labels".
# It lives in each demo's README.md as a markdown table. We parse it
# defensively — if parsing fails the field is returned as ``[]`` rather than
# raising, because get_demo's primary value is the summary+source pair.
_LABEL_PATTERN = re.compile(r"`?(exact|softened|reversed|fabricated)`?", re.IGNORECASE)


def _parse_expected_labels(readme_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in readme_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        # skip header / separator rows
        if cells[0].lower().startswith(("claim from summary", "总结中的论点", "---", ":-")):
            continue
        if set(cells[0]).issubset({"-", ":", " "}):
            continue
        claim = cells[0]
        label_cell = cells[1]
        match = _LABEL_PATTERN.search(label_cell)
        if not match:
            continue
        rows.append({"claim": claim, "expected_label": match.group(1).lower()})
    return rows


# --- server construction -----------------------------------------------------


def build_server() -> Any:
    """Construct the FastMCP server instance.

    Kept as a function so tests can import the module without instantiating
    the server, and so the entry point can wire stdio transport explicitly.
    """
    if FastMCP is None:
        raise RuntimeError(_INSTALL_HINT) from _IMPORT_ERROR

    mcp = FastMCP("summary-doctor")

    @mcp.tool()
    def audit_summary(
        summary: str,
        source: str,
        lang: str = "auto",
        backend: str = "anthropic",
        model: str = "claude-haiku-4-5-20251001",
    ) -> str:
        """Audit an AI-generated summary against its source material.

        Returns a Markdown report with per-claim labels:
        ``exact`` / ``softened`` / ``reversed`` / ``fabricated``. Each
        claim is paired with the matched source paragraph, a confidence
        score 0-100, and a one-line rationale.

        Use this tool when the user shares an AI summary (notification
        summary, AI overview, LLM-generated TLDR) **alongside** the source
        material and asks a faithfulness question — *not* when the user
        wants a new summary.

        Args:
            summary: The AI-generated summary text (raw text, file path,
                or URL). Pass the prose, not a description of it.
            source: Source material — raw text, file path, or URL of the
                original article / transcript.
            lang: Language hint. One of ``"zh"``, ``"en"``, ``"auto"``.
                Defaults to ``"auto"``.
            backend: Backend to call. One of ``"anthropic"`` (Anthropic
                SDK + API key), ``"claude-cli"`` (shell out to ``claude``
                CLI, reuses Claude Code subscription), or ``"mock"`` (no
                LLM call, heuristic only — for smoke tests).
            model: LLM model id. For ``anthropic`` backend a full model
                slug like ``claude-haiku-4-5-20251001`` (default) or
                ``claude-opus-4-7``; for ``claude-cli`` aliases ``haiku``
                / ``sonnet`` / ``opus`` are accepted.

        Returns:
            Markdown report. Includes headline counts, per-claim audit
            blocks with verbatim source quotes, and the standard
            "citation map, not a verdict" disclaimer.
        """
        if lang not in _VALID_LANGS:
            raise ValueError(
                f"lang must be one of {_VALID_LANGS}, got {lang!r}"
            )
        if backend not in _VALID_BACKENDS:
            raise ValueError(
                f"backend must be one of {_VALID_BACKENDS}, got {backend!r}"
            )

        # Imported lazily so the module imports cleanly even when optional
        # backend dependencies (e.g. anthropic SDK) are absent.
        import tempfile
        from summary_doctor.backends import get_backend
        from summary_doctor.pipeline import Pipeline

        be = get_backend(mock=(backend == "mock"), backend=backend, model=model)
        pipeline = Pipeline(backend=be, lang=lang)

        # Pipeline.run accepts a file path / URL / stdin reference, so when
        # the caller hands us raw text (the common case for MCP and SDK
        # callers) we materialise it through temporary files. We use temp
        # files instead of stdin because MCP itself owns stdin on this
        # process.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as summary_f, tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as source_f:
            summary_f.write(summary)
            source_f.write(source)
            summary_path = summary_f.name
            source_path = source_f.name

        try:
            report = pipeline.run(
                summary_ref=summary_path, source_ref=source_path
            )
        finally:
            import os
            for p in (summary_path, source_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass

        return report.markdown

    @mcp.tool()
    def get_demo(demo_name: str) -> dict:
        """Return the contents of a bundled demo case (no LLM call).

        Lets MCP clients preview what summary-doctor inputs and expected
        outputs look like without burning tokens. The audit pipeline is
        multi-stage and slow, so a no-op preview path matters.

        Args:
            demo_name: Directory name under ``demos/``. Use
                :func:`list_labels` callers' UX or call this tool with
                ``demo_name=""`` to receive the catalog of valid names
                (returned in the error message).

        Returns:
            Dict with keys:
              - ``name``: the demo directory name.
              - ``summary``: contents of ``summary.txt``.
              - ``source``: contents of ``source.txt``.
              - ``readme``: contents of ``README.md`` (description +
                expected labels table).
              - ``expected_labels``: list of ``{claim, expected_label}``
                parsed from the README table. Empty list if parsing
                fails — README text remains the source of truth.
        """
        root = _demos_root()
        available = _list_demo_names()
        if not demo_name or demo_name not in available:
            raise ValueError(
                f"unknown demo_name {demo_name!r}; available: {available}"
            )
        demo_dir = root / demo_name
        summary_path = demo_dir / "summary.txt"
        source_path = demo_dir / "source.txt"
        readme_path = demo_dir / "README.md"
        for p in (summary_path, source_path, readme_path):
            if not p.exists():
                raise FileNotFoundError(f"demo {demo_name} missing file: {p.name}")
        readme_text = readme_path.read_text(encoding="utf-8")
        return {
            "name": demo_name,
            "summary": summary_path.read_text(encoding="utf-8"),
            "source": source_path.read_text(encoding="utf-8"),
            "readme": readme_text,
            "expected_labels": _parse_expected_labels(readme_text),
        }

    @mcp.tool()
    def list_labels() -> dict:
        """Return the 4-class label taxonomy used by summary-doctor.

        Call this when the agent needs to explain output to a user, or
        when picking which label to act on. ``reversed`` and
        ``fabricated`` are the high-signal labels.

        Returns:
            Dict with keys:
              - ``labels``: list of 4 entries, each with ``name``,
                ``definition``, ``when_it_applies``, and ``action``.
              - ``demos``: list of available demo names (use with
                :func:`get_demo`).
              - ``disclaimer``: the standard "citation map, not a
                verdict" line.
        """
        return {
            "labels": [
                {
                    "name": "exact",
                    "definition": (
                        "Summary claim is supported almost verbatim by "
                        "the source."
                    ),
                    "when_it_applies": (
                        "Keyword overlap is high and polarity, "
                        "qualifiers, and scope all match the source."
                    ),
                    "action": "No action needed.",
                },
                {
                    "name": "softened",
                    "definition": (
                        "Summary preserves the direction of the claim "
                        "but drops qualifiers, hedges, or scope limits "
                        "present in the source."
                    ),
                    "when_it_applies": (
                        "Scope creep, cherry-picking, dropped "
                        "preconditions, or removed uncertainty bands."
                    ),
                    "action": (
                        "Surface the missing qualifier verbatim from "
                        "the source so the reader can re-attach it."
                    ),
                },
                {
                    "name": "reversed",
                    "definition": (
                        "Summary inverts or contradicts the source's "
                        "position."
                    ),
                    "when_it_applies": (
                        "Polarity flip, causal-direction flip, or "
                        "negation-stripping while keyword overlap "
                        "remains high."
                    ),
                    "action": (
                        "High-signal. Quote both the summary claim "
                        "and the source paragraph and flag the "
                        "polarity mismatch."
                    ),
                },
                {
                    "name": "fabricated",
                    "definition": (
                        "Summary claim has no support anywhere in "
                        "source."
                    ),
                    "when_it_applies": (
                        "Invented statistics, invented dates, "
                        "invented quotes, or claims about topics the "
                        "source never mentions."
                    ),
                    "action": (
                        "High-signal. May be false-positive when "
                        "source retrieval was partial (paywall, OCR "
                        "failure, chunking). Confirm the source is "
                        "complete before acting."
                    ),
                },
            ],
            "demos": _list_demo_names(),
            "disclaimer": (
                "This is a citation mapping, not a verdict. The reader "
                "makes the final call."
            ),
        }

    return mcp


def main() -> None:
    """Console-script entry point.

    Starts the FastMCP server over stdio transport, which is what all
    documented MCP clients (Claude Desktop, Cursor, Cline, Zed,
    Continue.dev) speak by default.
    """
    if FastMCP is None:
        # Print to stderr and exit non-zero so the parent MCP client gets a
        # clear signal rather than a silent crash.
        import sys

        print(_INSTALL_HINT, file=sys.stderr)
        sys.exit(2)
    server = build_server()
    server.run()


if __name__ == "__main__":  # pragma: no cover
    main()
