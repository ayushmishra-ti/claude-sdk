#!/usr/bin/env python3
"""
Run a small batch of new_exp prompts against Cloud Run endpoint.

Run from repo root (agent_sdk_v2):
  python new_exp/test_batch.py
  python new_exp/test_batch.py --limit 5          # first 5
  python new_exp/test_batch.py --random 20        # random 20
  python new_exp/test_batch.py -r 20 -i data/grade-5-ela-benchmark.json

Default endpoint: https://inceptagentic-skill-mcq-lanzf3jtla-uc.a.run.app
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Paths
REPO_ROOT = Path(__file__).resolve().parents[1]
NEW_EXP = REPO_ROOT / "new_exp"
OUTPUT_DIR = NEW_EXP / "output"
OUTPUT_JSON = OUTPUT_DIR / "batch_results.json"

# Default Cloud Run endpoint
DEFAULT_ENDPOINT = "https://inceptagentic-skill-mcq-lanzf3jtla-uc.a.run.app"


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


async def run_batch(
    prompts: list[dict],
    limit: int | None,
    random_sample: int | None,
    endpoint: str,
    verbose: bool,
    input_file: str = "",
) -> dict:
    """Run generation for each prompt via Cloud Run endpoint."""
    if random_sample:
        prompts = random.sample(prompts, min(random_sample, len(prompts)))
    elif limit:
        prompts = prompts[:limit]

    generated = []
    errors = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, req in enumerate(prompts):
            skills = req.get("skills", {})
            standard_id = skills.get("substandard_id", "?")
            qtype = req.get("type", "?")
            print(f"[{i+1}/{len(prompts)}] {standard_id} ({qtype})")

            try:
                resp = await client.post(f"{endpoint}/generate", json=req)
                if verbose:
                    print(f"  Status: {resp.status_code}")

                if resp.status_code != 200:
                    error_msg = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
                    errors.append({"request": req, "error": error_msg})
                    print(f"  FAIL: HTTP {resp.status_code}")
                    continue

                data = resp.json()
                items = data.get("generated_content", [])
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

            except httpx.TimeoutException:
                errors.append({"request": req, "error": "Request timeout"})
                print("  ERROR: timeout")
            except Exception as e:
                errors.append({"request": req, "error": str(e)})
                print(f"  ERROR: {e}")

    return {
        "generated_content": generated,
        "errors": errors,
        "metadata": {
            "source": "new_exp/test_batch.py",
            "endpoint": endpoint,
            "input_file": input_file,
            "total": len(prompts),
            "success": len(generated),
            "failed": len(errors),
            "timestamp": datetime.now().isoformat(),
        },
    }


def main():
    default_input = REPO_ROOT / "data" / "grade-5-ela-benchmark.json"
    parser = argparse.ArgumentParser(description="Run new_exp batch against Cloud Run endpoint")
    parser.add_argument("--input", "-i", type=Path, default=default_input, help="Input JSONL or JSON file")
    parser.add_argument("--limit", "-n", type=int, default=None, help="First N prompts")
    parser.add_argument("--random", "-r", type=int, default=None, help="Random N prompts")
    parser.add_argument("--endpoint", "-e", type=str, default=DEFAULT_ENDPOINT, help=f"Cloud Run endpoint (default: {DEFAULT_ENDPOINT})")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
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

    sample_info = ""
    if args.random:
        sample_info = f" (random {args.random})"
    elif args.limit:
        sample_info = f" (first {args.limit})"

    print(f"Loaded {len(prompts)} prompts from {prompts_path}{sample_info}")
    print(f"Endpoint: {args.endpoint}")
    print()

    data = asyncio.run(run_batch(prompts, args.limit, args.random, args.endpoint, args.verbose, input_file=str(prompts_path)))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = args.output if args.output.is_absolute() else OUTPUT_DIR / args.output.name
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"\nSaved to {out_path}")
    print(f"  Success: {data['metadata']['success']}/{data['metadata']['total']}")
    print(f"  Next: python new_exp/eval.py -i {out_path}")


if __name__ == "__main__":
    main()
