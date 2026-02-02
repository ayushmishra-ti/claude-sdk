---
name: ela-fill-in-constraints
description: Enforces strict ambiguity prevention for fill-in-the-blank ELA questions. Use ONLY when generating fill-in type questions to ensure exactly one defensible correct answer.
---

# ELA Fill-in Constraints

Specialized constraints for fill-in-the-blank questions to eliminate ambiguity and ensure single-answer validity.

## When to Use

- Question type is `fill-in`
- Standard is `L.*` (Language) — fill-in is NOT valid for other standard types
- Need to prevent "multiple plausible answers" failures

## Core Principle

Design questions where the **grammatical structure itself constrains the answer to ONE possibility**.

## Ambiguity Prevention Strategies

### 1. Use Structural Constraints
Leverage grammar patterns that have only one valid completion:
- Correlative conjunction pairs (first half given → second half required)
- Verb forms with explicit tense specification in the prompt
- Fixed grammatical patterns that permit only one form

### 2. Provide Clear Context Signals
Include time markers or grammatical cues that point to a single answer:
- Temporal phrases that establish tense
- Parallel structure that dictates form
- Antecedents that determine agreement

### 3. Word Bank Strategy
**Do NOT add "(Word choices: ...)" to the question text by default.** Use structural constraints first.
Include a word bank ONLY when:
- The blank could reasonably accept multiple valid forms
- Structural constraints alone are insufficient

Do NOT include a word bank when:
- Correlative pairs constrain the answer (neither → nor)
- Explicit tense instruction + base verb is given
- Grammatical structure permits only one form

### 4. Parenthetical Verb Hints
When testing verb conjugation, provide the base form in parentheses:
- "Yesterday, we ________ (go) to the beach" → "went"
- Student applies transformation, doesn't guess the word

### 5. Limit Blank Scope
- Use a single blank targeting ONE skill only
- Don't combine verb tense + spelling in same blank

### 6. Control Semantic Ambiguity
- Avoid contexts where synonyms could work (big/large)
- Unless choices are explicitly constrained

### 7. Use Requirement Language
Explicitly state what to supply:
- "Use the past perfect form"
- "Use the correlative conjunction that completes the pair"

### 8. Remove Optional Modifiers
Avoid blanks that could accept optional adverbs/adjectives without changing grammar.

### 9. Use Grammatical Forcing Functions
Make the blank part of a structure that enforces form:
- Auxiliary + participle
- Parallel verb list

### 10. Ensure Single Valid Agreement
Check number/person agreement so only one verb/pronoun can fit.

### 11. Avoid Open-Class Word Blanks
If the blank could be any noun/verb/adjective, it's too open unless tightly constrained.

### 12. Avoid Contextual Vagueness
Provide enough context to resolve tense/time/person clearly.

### 13. Shorten Sentence Length
Long, complex sentences introduce alternate valid parses.

### 14. Avoid Outside Knowledge
Keep the answer inside grammar/structure, not fact recall.

### 15. Self-Verification Rule
If a second grammatical completion feels plausible, add more constraints or a word bank.

## Quality Gate Checklist

Before finalizing, verify:
- [ ] One blank, one skill
- [ ] Only one grammatical completion is valid
- [ ] No synonym alternatives possible
- [ ] Agreement forces the answer
- [ ] Context cues establish tense/mood
- [ ] Prompt explicitly states required form (if needed)

## Self-Test

Ask: **"Could a different word fit here grammatically?"**
- If YES → add constraints or a word bank
- If NO → the structure is sufficient

## Fill-in Format Requirements

- NO `answer_options` field
- `answer` is the expected text (single word or short phrase)
- Clear blank using underscores (______)
- Include `additional_details` with standard ID
- Include `acceptable_alternatives` array
- Explanation MUST NOT reference option letters (A/B/C/D)
- Explanation should teach the underlying rule

## Reference

For high-quality fill-in examples demonstrating these patterns, see:
`.claude/reference/fill-in-examples.md`

This file contains grade-specific examples showing:
- Correlative conjunction completion (Pattern A)
- Explicit tense instruction + base verb (Pattern B)
- Parenthetical verb hints (Pattern C)
- Time marker + parallel structure (Pattern D)
- Perfect tense with temporal boundary (Pattern E)
