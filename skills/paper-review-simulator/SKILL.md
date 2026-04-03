---
name: paper-review-simulator
description: Simulate mixed-mode reviewer feedback for a paper draft before submission. Use when Codex should critique a paper, section, rebuttal draft, or revision plan by first acting like a top-conference reviewer for story, novelty, positioning, and contribution framing, and then like a strict technical reviewer for assumptions, baselines, logic, experiments, and misunderstanding risks. Especially use when the author wants reviewer comments, likely confusion points, author-response ideas, revision checklists, and sentence-level write-back suggestions.
---

# Paper Review Simulator

## Overview

Use this skill to pressure-test a paper before submission by treating the model as a skeptical reviewer. The skill should not stop at criticism; it should produce reviewer comments, author response ideas, a revision checklist, and sentence-level wording suggestions that can be written back into the draft.

## Workflow

1. Read the paper draft or the provided paper sections.
2. Read the user-provided related work, baseline notes, and explicit concerns.
3. Review in **mixed mode**:
   - first as a top-conference reviewer focused on story, novelty, positioning, and contribution boundaries
   - then as a strict technical reviewer focused on assumptions, baselines, logic, evidence, and likely misunderstanding
4. Produce four outputs in order:
   - `reviewer comments`
   - `author response ideas`
   - `revision checklist`
   - `write-back phrasing`
5. If the user provides a revised draft later, compare the new version against the previous concerns and explicitly mark each major issue as `resolved`, `partially resolved`, or `unresolved`.

## Reviewer Modes

Read [reviewer-modes.md](references/reviewer-modes.md) before reviewing.

### Mode 1: Top-Conference Reviewer

Focus on:

- whether the problem is important enough
- whether the story is coherent
- whether novelty is clear
- whether the contribution boundary is scoped correctly
- whether the paper is overclaiming

### Mode 2: Strict Technical Reviewer

Focus on:

- hidden assumptions
- whether the method actually supports the claim
- whether the baselines are sufficient
- where a reviewer is likely to misunderstand the method
- what parts of the paper would trigger “I do not buy this”

## Output Contract

### 1. Reviewer Comments

- 3 to 7 concrete reviewer comments
- ordered by severity or importance
- phrased in a realistic reviewer style
- explicitly call out likely confusion or misunderstanding, not only true flaws

### 2. Author Response Ideas

- explain how the author could answer each major concern
- if the concern is valid, say what should change rather than pretending it can be argued away
- if the concern is mainly a misunderstanding, say exactly what framing or explanation should be added

### 3. Revision Checklist

- actionable checklist items
- phrased as edits the author can make
- prefer precise edits over vague advice

### 4. Write-Back Phrasing

- provide sentence-level or short-paragraph wording suggestions
- only for the most important misunderstandings or weak framings
- keep the suggestions easy to paste back into the draft and then edit

## Input Guidance

If the user does not know how to package inputs, tell them to use [review-input-template.md](assets/review-input-template.md).

Prefer these inputs when available:

- title
- abstract
- introduction / motivation
- claimed contributions
- method overview
- experiment summary
- related work / baseline notes
- the author's own worries about likely reviewer confusion

## Revision Loop

If the user comes back with a revised draft:

1. compare against the previous concerns
2. explicitly mark each concern as:
   - `resolved`
   - `partially resolved`
   - `unresolved`
3. only add new comments if the revision introduces new weaknesses or still leaves ambiguity
