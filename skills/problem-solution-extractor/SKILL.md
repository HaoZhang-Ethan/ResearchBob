---
name: problem-solution-extractor
description: Produce a structured problem-solution artifact for a specific paper. Use when Codex needs to summarize a paper's core problem, proposed solution, contributions, limitations, evidence basis, confidence, and relevance to the active research profile.
---

# Workflow

1. Read the target paper's `metadata.json`.
2. If a PDF or richer text is available, use it. If not, say so and lower confidence if necessary.
3. Write `problem-solution.md` using `assets/problem-solution-template.md`.
4. Separate author claims, analyst inference, and uncertainty.
5. Use `manual-review` when the paper is too ambiguous to summarize cleanly.
6. Run `python skills/problem-solution-extractor/scripts/validate_problem_solution.py <path-to-problem-solution.md>`.
