#!/usr/bin/env python3
"""
Run a small batch of new_exp prompts and save results to output/batch_results.json.

Run from repo root (agent_sdk_v2):
  python new_exp/test_batch.py
  python new_exp/test_batch.py --limit 2

Uses SKILLS_ROOT=new_exp so the SDK loads .claude/skills/ from new_exp.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Run from repo root: python new_exp/test_batch.py
REPO_ROOT = Path(__file__).resolve().parents[1]
NEW_EXP = REPO_ROOT / "new_exp"
OUTPUT_DIR = NEW_EXP / "output"
OUTPUT_JSON = OUTPUT_DIR / "batch_results.json"

sys.path.insert(0, str(REPO_ROOT / "src"))
os.environ["SKILLS_ROOT"] = "new_exp"

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env", override=False)
except ImportError:
    pass


def load_prompts(path: Path) -> list[dict]:
    """Load prompts: JSONL (one JSON per line) or JSON (array or object with prompts/requests list)."""
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    text = path.read_text(encoding="utf-8").strip()
    if path.suffix.lower() == ".jsonl":
        requests = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                requests.append(json.loads(line))
        return requests

    # .json: array of requests or object with list
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("prompts", "requests", "items"):
            if key in data and isinstance(data[key], list):
                lst = data[key]
                # If each item has "request", use that
                return [x.get("request", x) for x in lst]
        if "generated_content" in data:
            # Wrong file (output shape); use request from each if present
            return [x.get("request", x) for x in data["generated_content"] if x.get("request")]
    raise ValueError(f"Unsupported JSON shape: need list or dict with 'prompts'/'requests' list")


async def run_batch(prompts: list[dict], limit: int | None, verbose: bool, input_file: str = "") -> dict:
    """Run generation for each prompt; return same shape as scripts/generate_batch.py."""
    from agentic_pipeline_sdk import generate_one_agentic

    if limit:
        prompts = prompts[:limit]

    generated = []
    errors = []
    for i, req in enumerate(prompts):
        skills = req.get("skills", {})
        standard_id = skills.get("substandard_id", "?")
        qtype = req.get("type", "?")
        print(f"[{i+1}/{len(prompts)}] {standard_id} ({qtype})")
        try:
            result = await generate_one_agentic(req, verbose=verbose)
            if result.get("success"):
                items = result.get("generatedContent", {}).get("generated_content", [])
                if items:
                    generated.append({
                        "id": items[0].get("id", ""),
                        "request": req,
                        "content": items[0].get("content", {}),
                    })
                    print("  OK")
                else:
                    errors.append({"request": req, "error": "No content in response"})
                    print("  FAIL: no content")
            else:
                errors.append({"request": req, "error": result.get("error", "Unknown")})
                print(f"  FAIL: {result.get('error', '')[:60]}")
        except Exception as e:
            errors.append({"request": req, "error": str(e)})
            print(f"  ERROR: {e}")

    return {
        "generated_content": generated,
        "errors": errors,
        "metadata": {
            "source": "new_exp/test_batch.py",
            "skills_root": "new_exp",
            "input_file": input_file,
            "total": len(prompts),
            "success": len(generated),
            "failed": len(errors),
            "timestamp": datetime.now().isoformat(),
        },
    }


def main():
    default_input = NEW_EXP / "test_prompts.jsonl"
    parser = argparse.ArgumentParser(description="Run new_exp batch and save to output/batch_results.json")
    parser.add_argument("--input", "-i", type=Path, default=default_input, help="Input JSONL or JSON file (benchmark or prompts)")
    parser.add_argument("--limit", "-n", type=int, default=None, help="Limit number of prompts (e.g. first 20)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose SDK logs")
    parser.add_argument("--output", "-o", type=Path, default=OUTPUT_JSON, help="Output JSON path")
    args = parser.parse_args()

    # Resolve input relative to cwd then repo root
    prompts_path = args.input if args.input.is_absolute() else (Path.cwd() / args.input)
    if not prompts_path.exists():
        prompts_path = REPO_ROOT / args.input
    if not prompts_path.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        prompts = load_prompts(prompts_path)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(prompts)} prompts from {prompts_path}")
    print(f"SKILLS_ROOT=new_exp -> skills from {NEW_EXP / '.claude' / 'skills'}")
    print()

    data = asyncio.run(run_batch(prompts, args.limit, args.verbose, input_file=str(prompts_path)))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = args.output if args.output.is_absolute() else OUTPUT_DIR / args.output.name
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"\nSaved to {out_path}")
    print(f"  Success: {data['metadata']['success']}/{data['metadata']['total']}")
    print(f"  Next: python new_exp/eval.py -i new_exp/output/batch_results.json")


if __name__ == "__main__":
    main()
