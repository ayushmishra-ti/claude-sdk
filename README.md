# Skill Architecture Experiment

## Overview

This folder contains a **responsibility-based** skill architecture for ELA question generation. The goal is to reduce context window usage and instruction conflicts by splitting the monolithic skill into composable sub-skills.

## Architecture

We use **3 skills** and **4 reference files**:

### Skills

| Skill | When Loaded | Purpose |
|-------|-------------|---------|
| `ela-question-core` | Every request | Output formats, routing, RL/RI/W.* questions |
| `ela-grammar-l-standards` | L.* standards only | Grammar constraints → reads `grammar-rules.md` |
| `ela-fill-in-constraints` | Fill-in type only | Ambiguity prevention → reads `fill-in-examples.md` |

### Reference Files

| File | Used by | Content |
|------|---------|---------|
| `curriculum.md` | ela-question-core | Standard scope, assessment boundaries, misconceptions |
| `passage-reference.md` | ela-question-core | RL.*/RI.* passage generation + quality rules |
| `grammar-rules.md` | ela-grammar-l-standards | Grammar definitions by grade (K-12) |
| `fill-in-examples.md` | ela-fill-in-constraints | Fill-in patterns and examples |

### Skill Loading by Request

| Request | Skills Loaded |
|---------|---------------|
| MCQ for RL.6.4 (Reading) | `ela-question-core` only |
| MCQ for L.3.1.A (Grammar) | `ela-question-core` + `ela-grammar-l-standards` |
| Fill-in for L.5.1.B (Grammar) | `ela-question-core` + `ela-grammar-l-standards` + `ela-fill-in-constraints` |
| MCQ for W.6.2.C (Writing) | `ela-question-core` only |

**Key insight:** Non-L.* standards don't load grammar rules at all.

## Folder Structure

```
new_exp/
├── .claude/
│   ├── reference/
│   │   ├── curriculum.md          # Standard scope, assessment boundaries
│   │   ├── passage-reference.md   # RL.*/RI.* generation + quality rules
│   │   ├── grammar-rules.md       # L.* grammar definitions
│   │   └── fill-in-examples.md    # Fill-in patterns
│   └── skills/
│       ├── ela-question-core/SKILL.md
│       ├── ela-grammar-l-standards/SKILL.md
│       └── ela-fill-in-constraints/SKILL.md
├── output/                        # Generated results
├── deploy.sh                      # Deploy to Cloud Run
├── test_batch.py                  # Run batch against endpoint
├── eval.py                        # Evaluate results
└── README.md
```

## Testing

### Run batch against Cloud Run endpoint

```bash
# Random 20 prompts (default: data/grade-5-ela-benchmark.json)
python new_exp/test_batch.py -r 20

# First 10 prompts
python new_exp/test_batch.py -n 10

# Different benchmark
python new_exp/test_batch.py -i data/grade-8-ela-benchmark.jsonl -r 20

# Custom endpoint
python new_exp/test_batch.py -r 20 --endpoint https://other-url.run.app
```

**Default endpoint:** `https://inceptagentic-skill-mcq-lanzf3jtla-uc.a.run.app`  
**Default input:** `data/grade-5-ela-benchmark.json`

**Flags:**
- `-i` / `--input` — Input JSONL or JSON file
- `-r` / `--random` — Random N prompts
- `-n` / `--limit` — First N prompts
- `-e` / `--endpoint` — Cloud Run endpoint
- `-o` / `--output` — Output path (default: `output/batch_results.json`)

### Evaluate results

```bash
python new_exp/eval.py -i new_exp/output/batch_results.json -o new_exp/output
```

## Deployment (Cloud Run)

Deploy **new_exp** skills to Cloud Run:

**Target:** `https://inceptagentic-skill-mcq-lanzf3jtla-uc.a.run.app`

From repo root (**agent_sdk_v2**):

```bash
# Authenticate if needed
gcloud auth login
gcloud config set project eternal-aspect-485115-e3

# Deploy
bash new_exp/deploy.sh
```

**What it does:**
- Builds with `Dockerfile.new_exp` (bundles `src/` + `new_exp/.claude/`)
- Deploys to Cloud Run service `inceptagentic-skill-mcq`
- Requires `ANTHROPIC_API_KEY` secret in Secret Manager

## Why This Architecture

### Problem with Monolithic Skills

The original `ela-question-generation/SKILL.md` contained all rules in one file:
- Grammar rules (L.*)
- Passage rules (RL./RI.*)
- Fill-in constraints
- Scenario rules (W.*)

**Issue:** Every request loaded ALL rules, causing instruction conflicts and higher token usage.

### How Claude SDK Works

1. Claude sees all skill **names and descriptions** (YAML frontmatter)
2. Claude decides which skills to invoke based on the prompt
3. **Only invoked skills** are fully loaded into context
4. Unused skills contribute only ~25 tokens (metadata only)

Splitting skills = real token savings + fewer instruction conflicts.

### Research Backing

Based on "When Single-Agent with Skills Replace Multi-Agent Systems" (arxiv.org/abs/2601.04748):
- Skill selection accuracy is optimal with **8-20 skills**
- Fine-grained, disjoint skills reduce ambiguity

## Expected Improvements

1. **Reduced instruction conflicts** — Grammar rules won't leak into non-grammar questions
2. **Lower token usage** — Only relevant skills loaded per request
3. **Better debuggability** — Easy to trace which skill caused an issue
4. **Improved evaluation scores** — Tighter guardrails, less ambiguity
