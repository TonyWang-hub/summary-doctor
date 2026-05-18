from pathlib import Path

from summary_doctor.backends.mock import MockBackend
from summary_doctor.pipeline import Pipeline


DEMOS = Path(__file__).resolve().parents[1] / "demos"


def _run(demo: str) -> dict:
    p = Pipeline(backend=MockBackend(), lang="auto")
    report = p.run(
        summary_ref=str(DEMOS / demo / "summary.txt"),
        source_ref=str(DEMOS / demo / "source.txt"),
    )
    return {
        "labels": [a.label for a in report.audits],
        "divergence": report.divergence_score(),
        "headline": report.headline(),
    }


def test_demo1_reversal_detects_at_least_one_reversed():
    result = _run("01-reversal-en")
    assert "reversed" in result["labels"] or "fabricated" in result["labels"], (
        f"demo1 must flag at least one reversed/fabricated; got {result['labels']}"
    )
    assert result["divergence"] >= 20, f"demo1 divergence should be ≥20, got {result['divergence']}"


def test_demo3_faithful_has_low_divergence():
    result = _run("03-faithful-en")
    assert "reversed" not in result["labels"], (
        f"demo3 (positive control) must not produce reversed; got {result['labels']}"
    )


def test_report_markdown_renders():
    p = Pipeline(backend=MockBackend(), lang="auto")
    report = p.run(
        summary_ref=str(DEMOS / "03-faithful-en" / "summary.txt"),
        source_ref=str(DEMOS / "03-faithful-en" / "source.txt"),
    )
    md = report.markdown
    assert "# Summary Audit Report" in md
    assert "## Per-claim audit" in md
    json_str = report.json_str
    assert '"audits"' in json_str
