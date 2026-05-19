#!/usr/bin/env python3
"""Run summary-doctor across every bundled demo on multiple backends and
emit a comparison table.

Usage
-----

    PYTHONPATH=src python3 eval/run-eval.py                 # mock only
    PYTHONPATH=src python3 eval/run-eval.py --with-cli      # mock + claude-cli haiku
    PYTHONPATH=src python3 eval/run-eval.py --with-cli --cli-model opus

Output goes to stdout as a Markdown table. Per-demo JSON sidecars land in
`eval/results/<backend>/<demo>.json`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMOS = ROOT / "demos"
RESULTS = ROOT / "eval" / "results"


def run_one(demo: Path, *, backend: str, cli_model: str, lang: str) -> dict:
    out_dir = RESULTS / backend
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md = out_dir / f"{demo.name}.md"
    out_json = out_md.with_suffix(out_md.suffix + ".json")

    cmd = [
        sys.executable,
        "-m",
        "summary_doctor",
        str(demo / "summary.txt"),
        "--original",
        str(demo / "source.txt"),
        "--lang",
        lang,
        "--out",
        str(out_md),
    ]
    if backend == "mock":
        cmd.append("--mock")
    elif backend == "claude-cli-haiku":
        cmd.extend(["--backend", "claude-cli", "--model", cli_model])
    else:
        raise RuntimeError(f"unknown backend: {backend}")

    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout).strip()[-400:]}
    return json.loads(out_json.read_text(encoding="utf-8"))


def label_dist(audits: list[dict]) -> dict[str, int]:
    out = {"exact": 0, "softened": 0, "reversed": 0, "fabricated": 0}
    for a in audits:
        label = a.get("label")
        if label in out:
            out[label] += 1
    return out


def fmt_row(name: str, claims: int, div: int, dist: dict[str, int]) -> str:
    return (
        f"| `{name}` | {claims} | {div}% | "
        f"{dist['exact']} | {dist['softened']} | "
        f"**{dist['reversed']}** | **{dist['fabricated']}** |"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-cli", action="store_true", help="Also run claude-cli backend")
    ap.add_argument("--cli-model", default="haiku", help="Model alias for claude-cli (haiku/sonnet/opus)")
    args = ap.parse_args()

    backends = ["mock"]
    if args.with_cli:
        backends.append("claude-cli-haiku")

    demos = sorted(d for d in DEMOS.iterdir() if d.is_dir())

    print("# summary-doctor demo-set evaluation\n")
    for backend in backends:
        print(f"## Backend: `{backend}`\n")
        print("| Demo | Claims | Divergence | `exact` | `softened` | `reversed` | `fabricated` |")
        print("|---|--:|--:|--:|--:|--:|--:|")
        agg_claims = 0
        agg_div_sum = 0
        agg_dist = {"exact": 0, "softened": 0, "reversed": 0, "fabricated": 0}
        for demo in demos:
            lang = "zh" if demo.name.endswith("-zh") else "en"
            print(f"  -> {demo.name} on {backend}...", file=sys.stderr, flush=True)
            data = run_one(demo, backend=backend, cli_model=args.cli_model, lang=lang)
            if "error" in data:
                print(f"| `{demo.name}` | ERROR | — | — | — | — | — |")
                print(f"    ERROR: {data['error'][:160]}", file=sys.stderr)
                continue
            audits = data["audits"]
            dist = label_dist(audits)
            print(fmt_row(demo.name, len(audits), data["divergence_score"], dist))
            agg_claims += len(audits)
            agg_div_sum += data["divergence_score"]
            for k, v in dist.items():
                agg_dist[k] += v
        if demos:
            print(
                "| **total** | "
                f"{agg_claims} | {agg_div_sum // len(demos)}% avg | "
                f"{agg_dist['exact']} | {agg_dist['softened']} | "
                f"**{agg_dist['reversed']}** | **{agg_dist['fabricated']}** |"
            )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
