---
name: ela-question-core
description: Generate K-12 ELA assessment questions (MCQ, MSQ, Fill-in) as valid JSON. Use this skill for ANY ELA question generation request. Routes to specialized skills based on standard type.
---

# ELA Question Core

Foundation skill for generating K-12 ELA assessment questions aligned to Common Core standards.

## When to Use

- Generate ANY ELA question (MCQ, MSQ, Fill-in)
- Standard ID provided (e.g., `CCSS.ELA-LITERACY.L.3.1.A`)
- Create assessment items for ELA / Common Core

## Reference Files (under .claude)

All reference files live in **`.claude/reference/`** (paths relative to project root when `cwd` is this project). Read only what applies:

| When | Read |
|------|------|
| RL.*/RI.* (passage required) | `.claude/reference/passage-reference.md` |
| L.* (grammar) | Invoke **ela-grammar-l-standards** (it reads `.claude/reference/grammar-rules.md`) |
| Fill-in type | Invoke **ela-fill-in-constraints** (it reads `.claude/reference/fill-in-examples.md`) |
| Standard scope / curriculum | `.claude/reference/curriculum.md` (optional) |

## Routing: Invoke Specialized Skills

Based on the standard family, invoke additional specialized skills:

| Standard | Action |
|----------|--------|
| `L.*` (Language) | **Also invoke** `ela-grammar-l-standards` skill |
| Fill-in question type | **Also invoke** `ela-fill-in-constraints` skill |
| `RL.*` (Reading Literature) | Read `.claude/reference/passage-reference.md`, generate narrative passage |
| `RI.*` (Reading Informational) | Read `.claude/reference/passage-reference.md`, generate informational passage |
| `W.*` (Writing) | Use scenario-based questions only (see below) |

## Output Formats

### MCQ (Multiple Choice) - Single Correct Answer

```json
{
  "id": "l_3_1_a_mcq_easy_001",
  "content": {
    "answer": "B",
    "question": "Which word in this sentence is a noun? The cat sleeps on the soft bed.",
    "image_url": [],
    "answer_options": [
      {"key": "A", "text": "sleeps"},
      {"key": "B", "text": "cat"},
      {"key": "C", "text": "soft"},
      {"key": "D", "text": "on"}
    ],
    "answer_explanation": "A noun names a person, place, thing, or animal. 'Cat' names an animal, so it is a noun."
  }
}
```

### MCQ with Passage (for RL.*/RI.* standards)

```json
{
  "id": "rl_6_4_mcq_easy_001",
  "content": {
    "passage": "The passage text goes here...",
    "answer": "C",
    "question": "Based on the passage, what does the word 'accumulate' most likely mean?",
    "image_url": [],
    "answer_options": [
      {"key": "A", "text": "disappear quickly"},
      {"key": "B", "text": "change color"},
      {"key": "C", "text": "gather together"},
      {"key": "D", "text": "move apart"}
    ],
    "answer_explanation": "Context explanation here."
  }
}
```

### MSQ (Multiple Select) - Multiple Correct Answers

```json
{
  "id": "l_3_1_a_msq_medium_001",
  "content": {
    "answer": ["A", "D"],
    "question": "Read this sentence: 'The happy dog ran quickly to the park.' Which words are nouns? Select all that apply.",
    "image_url": [],
    "answer_options": [
      {"key": "A", "text": "dog"},
      {"key": "B", "text": "ran"},
      {"key": "C", "text": "quickly"},
      {"key": "D", "text": "park"}
    ],
    "answer_explanation": "Nouns name people, places, things, or animals. 'Dog' names an animal and 'park' names a place."
  }
}
```

### Fill-in (Fill in the Blank)

```json
{
  "id": "l_3_1_d_fillin_easy_001",
  "content": {
    "answer": "went",
    "question": "Complete the sentence with the correct past tense form of 'go':\n\nYesterday, Maria ______ to the library to return her books.",
    "image_url": [],
    "additional_details": "CCSS.ELA-LITERACY.L.3.1.D",
    "acceptable_alternatives": ["went"],
    "answer_explanation": "The word 'Yesterday' tells us the action happened in the past. The verb 'go' has an irregular past tense form. Instead of adding -ed, we change 'go' to 'went' to show past tense."
  }
}
```

## ID Generation

From `CCSS.ELA-LITERACY.L.3.1.A`:
1. Take part after `CCSS.ELA-LITERACY.` → `L.3.1.A`
2. Lowercase and replace `.` with `_` → `l_3_1_a`
3. Append `_<type>_<difficulty>_001`

## Grade Level Guidelines

| Grade | Age | Vocabulary |
|-------|-----|------------|
| K | 5-6 | Simple sight words |
| 1-2 | 6-8 | Common everyday words |
| 3-5 | 8-11 | Grade-level vocabulary |
| 6-8 | 11-14 | Academic vocabulary |
| 9-12 | 14-18 | Sophisticated, literary terms |

## Difficulty Definitions

- **Easy**: Recall, one concept, familiar words
- **Medium**: Apply a rule, compare options
- **Hard**: Multiple concepts, subtle wording

## W.* (Writing) Standards - Scenario-Based Only

Writing standards are performance-based. Use scenario-based questions only.

| Standard | Focus | Question Approach |
|----------|-------|-------------------|
| W.*.1 | Persuasive writing | "Which claim best supports..." |
| W.*.2 | Explanatory writing | "Which transition best connects..." |
| W.*.3 | Story writing | "Which detail best develops..." |
| W.*.4-6 | Planning/revising | "What should the writer do next..." |
| W.*.7-9 | Research skills | "Which source is most credible..." |

## Quality Checklist

- [ ] Only ONE correct answer (MCQ/Fill-in) OR all selected correct (MSQ)
- [ ] All distractors are clearly wrong for specific reasons
- [ ] Vocabulary matches grade level
- [ ] `image_url` is `[]`
- [ ] Exactly 4 options (A, B, C, D) for MCQ/MSQ

## Critical Rules

- `image_url` is ALWAYS `[]`
- **FINAL OUTPUT MUST BE VALID JSON**
- For RL.*/RI.*: Include passage in `passage` field
- For Fill-in: NO `answer_options` field
