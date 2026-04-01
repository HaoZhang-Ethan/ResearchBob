---
name: report-composer
description: Compose concise daily or manual research scout reports from existing paper artifacts. Use when Codex should turn validated problem-solution files into a browsing-oriented shortlist with read-now, follow-up, skip, and manual-review sections.
---

# Workflow

1. Read all available `problem-solution.md` artifacts for the requested window.
2. Trust `opportunity_label` only if the artifact passes validation.
3. Run `python skills/report-composer/scripts/compose_report.py --workspace research-workspace --mode daily --label 2026-03-31` or use `manual` mode with a custom label.
4. Inspect the generated report and add 2 to 5 lines of commentary only if the user asked for a narrative layer.
5. Keep the report short enough that a researcher can review it in a few minutes.
