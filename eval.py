#!/usr/bin/env python3
"""
Evaluate new_exp batch_results.json (structure check + optional InceptBench).

Run from repo root (agent_sdk_v2):
  python new_exp/eval.py
  python new_exp/eval.py -i new_exp/output/batch_results.json -o new_exp/output

Writes:
  - output/eval_results.json   (per-item validation + InceptBench if available)
  - output/eval_summary.json  (counts and pass rate)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NEW_EXP = REPO_ROOT / "new_exp"
DEFAULT_INPUT = NEW_EXP / "output" / "batch_results.json"
DEFAULT_OUTPUT_DIR = NEW_EXP / "output"


def validate_item(item: dict) -> dict:
    """Validate one generated item (structure only). Returns {valid, errors[]}."""
    errors = []
    content = item.get("content") or {}
    req = item.get("request") or {}

    if not item.get("id"):
        errors.append("missing id")
    if not content.get("question"):
        errors.append("missing content.question")
    if content.get("image_url") is not None and content.get("image_url") != []:
        errors.append("image_url must be []")
    qtype = req.get("type", "mcq")
    if qtype in ("mcq", "msq"):
        opts = content.get("answer_options") or []
        if len(opts) != 4:
            errors.append(f"answer_options must have 4 items, got {len(opts)}")
        if not content.get("answer"):
            errors.append("missing answer")
    if qtype == "fill-in":
        if content.get("answer_options"):
            errors.append("fill-in must not have answer_options")
        if not content.get("answer") and not content.get("acceptable_alternatives"):
            errors.append("fill-in must have answer or acceptable_alternatives")
    if not content.get("answer_explanation"):
        errors.append("missing answer_explanation")

    return {"valid": len(errors) == 0, "errors": errors}


async def run_inceptbench_item(item: dict) -> dict | None:
    """Run InceptBench on one item; return evaluation dict or None."""
    payload = {
        "generated_content": [{
            "id": item.get("id", ""),
            "content": json.dumps(item.get("content", {})) if isinstance(item.get("content"), dict) else str(item.get("content", {})),
            "request": {
                "grade": (item.get("request") or {}).get("grade", "3"),
                "subject": (item.get("request") or {}).get("subject", "ela"),
                "type": (item.get("request") or {}).get("type", "mcq"),
                "difficulty": (item.get("request") or {}).get("difficulty", "easy"),
                "skills": (item.get("request") or {}).get("skills", {}),
            },
        }]
    }
    import tempfile
    with tempfile.TemporaryDirectory(prefix="incept_") as td:
        in_path = Path(td) / "in.json"
        out_path = Path(td) / "out.json"
        in_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        cmd = [sys.executable, "-m", "inceptbench", "evaluate", str(in_path), "-o", str(out_path)]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            if proc.returncode != 0 or not out_path.exists():
                return None
            data = json.loads(out_path.read_text(encoding="utf-8"))
            ev = data.get("evaluations", {})
            if item.get("id") in ev:
                return ev[item["id"]]
            if data.get("results") and isinstance(data["results"][0], dict):
                return data["results"][0]
            return data.get("overall") or data
        except (FileNotFoundError, asyncio.TimeoutError, json.JSONDecodeError):
            return None


def main():
    parser = argparse.ArgumentParser(description="Evaluate new_exp batch_results.json")
    parser.add_argument("--input", "-i", type=Path, default=DEFAULT_INPUT, help="Input JSON (batch_results.json)")
    parser.add_argument("--output-dir", "-o", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--inceptbench", action="store_true", default=True, help="Run InceptBench if installed (default: True)")
    parser.add_argument("--no-inceptbench", action="store_false", dest="inceptbench", help="Skip InceptBench, structure-only")
    args = parser.parse_args()

    if args.output_dir.suffix:
        args.output_dir = args.output_dir.parent

    if not args.input.exists():
        print(f"Error: {args.input} not found. Run: python new_exp/test_batch.py", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.input.read_text(encoding="utf-8"))
    items = data.get("generated_content", [])
    if not items:
        print("No generated_content to evaluate.", file=sys.stderr)
        sys.exit(0)

    print(f"Evaluating {len(items)} items from {args.input}")
    results = []
    for i, item in enumerate(items):
        vid = validate_item(item)
        row = {
            "id": item.get("id", ""),
            "substandard_id": (item.get("request") or {}).get("skills", {}).get("substandard_id", ""),
            "type": (item.get("request") or {}).get("type", ""),
            "structure_valid": vid["valid"],
            "structure_errors": vid["errors"],
        }
        if args.inceptbench:
            ev = asyncio.run(run_inceptbench_item(item))
            row["inceptbench"] = ev
            if ev:
                overall = ev.get("overall") or {}
                score = overall.get("score_100") or (overall.get("score") and round(overall["score"] * 100, 2))
                row["score_100"] = score
                row["passed"] = score is not None and score >= 85
            else:
                row["score_100"] = None
                row["passed"] = False
        results.append(row)
        status = "OK" if vid["valid"] else "INVALID"
        if args.inceptbench and row.get("score_100") is not None:
            status += f" {row['score_100']}%"
        print(f"  [{i+1}/{len(items)}] {row['id']} {status}")

    # Summary
    valid_count = sum(1 for r in results if r["structure_valid"])
    pass_count = sum(1 for r in results if r.get("passed")) if args.inceptbench else None
    summary = {
        "total": len(items),
        "structure_valid": valid_count,
        "structure_invalid": len(items) - valid_count,
        "inceptbench_passed": pass_count,
        "inceptbench_run": args.inceptbench,
        "timestamp": datetime.now().isoformat(),
    }
    if pass_count is not None and len(items):
        summary["pass_rate_pct"] = round(pass_count / len(items) * 100, 1)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.output_dir / "eval_results.json"
    summary_path = args.output_dir / "eval_summary.json"
    results_path.write_text(json.dumps({"items": results}, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nResults: {results_path}")
    print(f"Summary: {summary_path}")
    print(f"  Structure: {valid_count}/{len(items)} valid")
    if pass_count is not None:
        print(f"  InceptBench pass (≥85%): {pass_count}/{len(items)} ({summary.get('pass_rate_pct')}%)")


if __name__ == "__main__":
    main()
