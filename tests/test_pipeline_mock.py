"""Pipeline smoke tests against the bundled demos using the mock backend.

The mock backend is a small heuristic, not the calibrated path. These tests
verify:
  - the pipeline end-to-end (load → decompose → classify → report) works
  - high-signal failure-mode demos surface *some* warning label
    (reversed OR fabricated, plus a non-trivial divergence floor)
  - the positive controls do not produce any reversed/fabricated label

We deliberately do *not* assert exact label distributions per demo. The mock
backend can mislabel the *type* of failure (e.g. flag a causal-inversion as
fabricated rather than reversed) — that is expected and is itself part of why
the calibrated Anthropic backend exists. The tests only assert that the
high-signal demos do *not* go silent.
"""
from pathlib import Path

import pytest

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
        "report": report,
    }


# --- high-signal demos -------------------------------------------------------
# Each entry: (demo_dir, min_high_signal_count, min_divergence)
# high-signal == reversed OR fabricated. The mock may mislabel the *kind* of
# failure but must not return all-exact on a known-bad summary.
HIGH_SIGNAL_DEMOS = [
    ("01-reversal-en", 1, 20),
    ("02-softening-zh", 0, 20),  # softening mode: divergence-only floor
    ("04-cherry-picking-en", 1, 20),
    ("05-causal-inversion-zh", 1, 20),
    ("06-scope-creep-en", 1, 20),
    ("07-temporal-error-en", 1, 10),
    ("08-fabricated-stats-zh", 1, 30),
]

POSITIVE_CONTROLS = [
    ("03-faithful-en", 10),
    ("09-faithful-zh", 10),
]


@pytest.mark.parametrize("demo,min_high,min_div", HIGH_SIGNAL_DEMOS)
def test_high_signal_demo_does_not_go_silent(demo, min_high, min_div):
    result = _run(demo)
    labels = result["labels"]
    high_signal = sum(1 for label in labels if label in ("reversed", "fabricated"))
    assert high_signal >= min_high, (
        f"{demo}: mock backend was expected to surface ≥{min_high} reversed/fabricated label(s); "
        f"got {labels}"
    )
    assert result["divergence"] >= min_div, (
        f"{demo}: divergence should be ≥{min_div}, got {result['divergence']}; labels={labels}"
    )


@pytest.mark.parametrize("demo,max_div", POSITIVE_CONTROLS)
def test_positive_control_stays_clean(demo, max_div):
    result = _run(demo)
    labels = result["labels"]
    assert "reversed" not in labels, (
        f"{demo} (positive control): must not produce reversed; got {labels}"
    )
    assert "fabricated" not in labels, (
        f"{demo} (positive control): must not produce fabricated; got {labels}"
    )
    assert result["divergence"] <= max_div, (
        f"{demo} (positive control): divergence should be ≤{max_div}, got {result['divergence']}; "
        f"labels={labels}"
    )


# --- back-compat: keep the original named tests for any external runner -----

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


def test_all_bundled_demos_have_required_files():
    """Sanity check: every demo dir contains the three expected files."""
    demos = sorted(p for p in DEMOS.iterdir() if p.is_dir())
    assert len(demos) >= 7, f"expected at least 7 demo directories; found {len(demos)}"
    for d in demos:
        assert (d / "source.txt").exists(), f"missing source.txt in {d}"
        assert (d / "summary.txt").exists(), f"missing summary.txt in {d}"
        assert (d / "README.md").exists(), f"missing README.md in {d}"
