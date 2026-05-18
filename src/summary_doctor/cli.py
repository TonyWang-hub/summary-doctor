import argparse
import sys
from datetime import datetime
from pathlib import Path

from summary_doctor.pipeline import Pipeline
from summary_doctor.backends import get_backend


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="summary-doctor",
        description=(
            "Audit AI-generated summaries against their source material. "
            "Detect reversals, fabrications, and cherry-picking — with citations, not verdicts."
        ),
    )
    p.add_argument("summary", help="Summary file path, URL, or '-' for stdin")
    p.add_argument("--original", required=True, help="Source file path or URL")
    p.add_argument("--lang", choices=["zh", "en", "auto"], default="auto")
    p.add_argument(
        "--out",
        default=None,
        help="Report output path (default: ./summary-audit-<timestamp>.md)",
    )
    p.add_argument(
        "--model",
        default="claude-haiku-4-5-20251001",
        help="LLM model id (Anthropic). Use claude-opus-4-7 for highest quality.",
    )
    p.add_argument(
        "--mock",
        action="store_true",
        help="Skip LLM calls; return a canned demo report. Useful for pipeline tests.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_path = Path(
        args.out
        or f"summary-audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    )

    backend = get_backend(mock=args.mock, model=args.model)
    pipeline = Pipeline(backend=backend, lang=args.lang)

    try:
        report = pipeline.run(summary_ref=args.summary, source_ref=args.original)
    except FileNotFoundError as e:
        print(f"[error] file not found: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        msg = str(e)
        if "source-unfetchable" in msg:
            print(f"[error] {msg}", file=sys.stderr)
            return 2
        print(f"[error] pipeline failed: {msg}", file=sys.stderr)
        return 1

    out_path.write_text(report.markdown, encoding="utf-8")
    json_path = out_path.with_suffix(out_path.suffix + ".json")
    json_path.write_text(report.json_str, encoding="utf-8")
    print(f"[ok] report: {out_path}")
    print(f"[ok] json:   {json_path}")
    print(f"[summary] {report.headline()}")
    return 0
