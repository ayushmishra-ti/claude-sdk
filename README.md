# Skill Architecture Experiment

## Overview

This folder contains an experimental **responsibility-based** skill architecture for ELA question generation. The goal is to reduce context window usage and instruction conflicts by splitting the monolithic skill into composable sub-skills.

## Why We Made This Decision

### Problem with Monolithic Skills

Our original `ela-question-generation/SKILL.md` contained all rules in one file:
- Grammar rules (for L.* standards)
- Passage rules (for RL./RI.* standards)
- Fill-in constraints
- Scenario rules (for W.* standards)

**Issue:** Every question generation loaded ALL rules, even when only a subset applied. This caused:
- Instruction conflicts (grammar rules bleeding into non-grammar questions)
- Higher token usage
- Harder debugging when scores dropped

### Research Backing

Based on the paper "When Single-Agent with Skills Replace Multi-Agent Systems" (arxiv.org/abs/2601.04748):
- Skill selection accuracy is optimal with **8-20 skills**
- Beyond that threshold, semantic confusability causes sharp accuracy drops
- Fine-grained, disjoint skills reduce ambiguity and improve evaluation alignment

### How Claude SDK Works

1. Claude sees all available skill **names and descriptions** (from YAML frontmatter)
2. Claude decides which skills to invoke based on the prompt
3. **Only invoked skills** are fully loaded into context
4. Unused skills contribute only ~25 tokens (metadata only)

This means splitting skills = real token savings + fewer instruction conflicts.

## Architecture: Responsibility-Based vs Type-Based

We chose **responsibility-based** splitting over type-based:

| Approach | Structure | Trade-off |
|----------|-----------|-----------|
| **Type-based** | `ela-mcq/`, `ela-fill-in/`, `ela-msq/` | Simpler routing, but grammar rules duplicated in each |
| **Responsibility-based** | `ela-question-core/`, `ela-grammar-l-standards/`, `ela-fill-in-constraints/` | Single source of truth, composable, no duplication |

### When Each Skill Loads

| Request | Skills Loaded |
|---------|---------------|
| MCQ for RL.6.4 (Reading) | `ela-question-core` only |
| MCQ for L.3.1.A (Grammar) | `ela-question-core` + `ela-grammar-l-standards` |
| Fill-in for L.5.1.B (Grammar) | `ela-question-core` + `ela-grammar-l-standards` + `ela-fill-in-constraints` |
| MCQ for W.6.2.C (Writing) | `ela-question-core` only |

**Key insight:** Non-L.* standards don't load grammar rules at all, reducing irrelevant constraints.

## Folder Structure (SDK-aligned)

Reference lives **inside** `.claude` so SKILL.md can reference it per the [Agent Skills SDK](https://docs.anthropic.com). No reference at project root.

```
new_exp/
├── .claude/
│   ├── reference/                 # Reference files (SKILL.md points here)
│   │   ├── README.md              # Index and usage
│   │   ├── curriculum.md          # Standard scope, assessment boundaries
│   │   ├── common-rules.md        # All question types
│   │   ├── grammar-rules.md       # L.* only
│   │   ├── passage-guidelines.md  # RL.*/RI.* passage generation
│   │   ├── passage-rules.md       # RL.*/RI.* evaluation
│   │   ├── fill-in-rules.md       # Fill-in only
│   │   ├── fill-in-examples.md    # Fill-in patterns
│   │   ├── mcq-msq-rules.md       # MCQ/MSQ
│   │   └── README-1-common.md, README-2-type-specific.md, README-3-reference.md
│   └── skills/
│       ├── ela-question-core/
│       │   └── SKILL.md           # Core: schema, formats, routing, RL/RI/W.*
│       ├── ela-grammar-l-standards/
│       │   └── SKILL.md           # L.* only: grammar constraints, .claude/reference/grammar-rules.md
│       └── ela-fill-in-constraints/
│           └── SKILL.md           # Fill-in only: ambiguity prevention, .claude/reference/fill-in-examples.md
├── HOW_SKILLS_WORK.md             # How SDK + routing + reference work (read this)
├── test_prompts.json              # Sample prompts
├── COMPARISON.md                  # How to test both setups
└── reference/                     # DEPRECATED: use .claude/reference/ (kept for backward compatibility)
```

**See [HOW_SKILLS_WORK.md](HOW_SKILLS_WORK.md)** for step-by-step flow, routing, and SDK checklist.

## Workflow

```
User Prompt: "Generate MCQ for CCSS.ELA-LITERACY.RL.6.4"
                            │
                            ▼
              ┌─────────────────────────┐
              │  Claude sees all skills │
              │  (names + descriptions) │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Claude decides:        │
              │  "This is RL.* standard │
              │   → need core only"     │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Only ela-question-core │
              │  SKILL.md is loaded     │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Question generated     │
              │  without grammar rules  │
              │  polluting context      │
              └─────────────────────────┘
```

## Expected Improvements

1. **Reduced instruction conflicts** - Grammar rules won't leak into non-grammar questions
2. **Lower token usage** - Only relevant skills loaded per request
3. **Better debuggability** - Easy to trace which skill caused an issue
4. **Improved evaluation scores** - Tighter guardrails, less ambiguity

## Limitations

- If benchmark is heavily L.* standards, type-based might be simpler
- More skills invoked for L.* fill-in questions (3 skills vs 1)
- Skill descriptions must be clearly distinct to avoid selection errors

## Deployment (Cloud Run)

Deploy **new_exp** to the MCQ skill service (same API as parent, uses `new_exp/.claude/skills/`):

**Target:** `https://inceptagentic-skill-mcq-413562643011.us-central1.run.app/generate`

From repo root (**agent_sdk_v2**):

```bash
bash new_exp/deploy.sh
```

- Build uses `Dockerfile.new_exp` and `cloudbuild-new_exp.yaml` (repo root).
- Image bundles parent `src/` and **new_exp** `.claude/` (ela-question-core, ela-grammar-l-standards, ela-fill-in-constraints).
- Requires `gcloud` and project `413562643011`; secret `ANTHROPIC_API_KEY` must exist in Secret Manager.

## Running with the SDK

When using the SDK with this experiment, set **`cwd`** to **`new_exp`** (or the repo root that contains `new_exp`) so the SDK discovers `.claude/skills/` and skills can Read `.claude/reference/` correctly.

```python
options = ClaudeAgentOptions(
    cwd="/path/to/new_exp",  # or path/to/agent_sdk_v2 with skills under new_exp/.claude/
    setting_sources=["user", "project"],
    allowed_tools=["Skill", "Read", ...]
)
```

## Testing

- **test_prompts.json** — Sample requests (MCQ L.*, Fill-in L.*, MCQ RL.*) to run against both monolithic and new_exp.
- **COMPARISON.md** — How to run both setups, compare InceptBench scores, and decide which is better for your use case.

## Next Steps

1. Test on sample prompts to verify correct skill selection
2. Compare evaluation scores against monolithic approach (see COMPARISON.md)
3. Measure actual token usage difference
4. Iterate on skill descriptions if selection accuracy is low
