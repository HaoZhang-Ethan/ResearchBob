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

If `research-workspace/profile/interest-profile.md` is missing, `daily-pipeline` will attempt to synthesize it from `research-workspace/issue-intake/` before the run continues.

When that fallback path is used and the run succeeds, the workflow can also comment on and close the consumed GitHub issues on a best-effort basis.

If GitHub access needs a different network environment than arXiv/model access, use:

```bash
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace
```

## GitHub Issue Intake

Use `sync-issues` when you want to pull structured demand from GitHub issues in the current repository.

Scope and reliability:

- this entry only feeds the daily paper summary workflow
- it is not an on-demand paper analysis interface
- because the automation runs on a personal laptop, sync time and summary delivery time are not guaranteed

User-side view:

- if you are only using the service as a requester, you only need to submit an issue in the required format
- you do not need to care how the deployment side runs or schedules the intake workflow

Deployment-side view:

- the deployment side must run `sync-issues` locally to pull requests from GitHub
- this is a best-effort laptop deployment, so schedule and delivery time are inherently unstable

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

## Prompt-Based Local Deployment

If you want an AI assistant to help deploy this workflow locally, you can paste:

```text
Please help me set up this repository as a local daily paper summary workflow on my machine.

Repository path: /path/to/ResearchBob
Workspace path: /path/to/ResearchBob/research-workspace

Tasks:
1. Initialize the workspace if needed.
2. Tell me which environment variables or `.env.local` values I still need to provide.
3. Verify the CLI commands for `daily-pipeline` and `sync-issues`.
4. Show me the exact command to run the daily paper summary locally.
5. Show me an optional cron example.

Important constraints:
- This deployment is only for the daily paper summary workflow.
- GitHub issue intake is best-effort because the automation runs on a laptop, not always-on infrastructure.
```

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
