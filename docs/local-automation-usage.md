# Local Automation Usage

## Required Environment

Set:

- `OPENAI_API_KEY`
- optionally `AUTO_RESEARCH_MODEL`

Example:

```bash
export OPENAI_API_KEY=...
export AUTO_RESEARCH_MODEL=gpt-5.2
```

## Manual Run

From the repo root:

```bash
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace --push
```

Or use the wrapper:

```bash
PYTHONPATH=src python scripts/daily_pipeline.py
```

## GitHub Issue Intake

Use `sync-issues` when you want to pull structured demand from GitHub issues in the current repository.

Issue template:

```md
---
direction: llm-agents
---

## Background
...

## Requirements
...

## Constraints
...

## Notes
...
```

Manual run:

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
```

Push generated intake artifacts:

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace --push
```

Behavior:

1. derives the repository from the current git remote unless `--repo` is provided
2. fetches issues through `gh`
3. writes grouped artifacts under `research-workspace/issue-intake/<direction>/<github-username>/`
4. keeps one request file per issue and refreshes a cumulative `summary.md`

## What It Does

The pipeline:

1. runs intake
2. prefilters candidates
3. asks the model to rank Top K candidates
4. generates `problem-solution.md` for the selected set
5. composes a daily report
6. exports Zotero RIS
7. optionally commits and pushes generated outputs

## Cron Example

Run every day at 09:00:

```cron
0 9 * * * cd /Users/zhanghao/Project/AutoResearch && OPENAI_API_KEY=... AUTO_RESEARCH_MODEL=gpt-5.2 PYTHONPATH=src python scripts/daily_pipeline.py >> /tmp/auto-research-daily.log 2>&1
```
