# Local Automation Pipeline Design

Status: Draft for implementation
Date: 2026-04-02

## Summary

Build a local, scheduled pipeline that:

1. reads the persistent research profile,
2. fetches new arXiv candidates,
3. ranks candidates in two stages,
4. selects Top K papers,
5. generates short `problem-solution.md` artifacts for the selected set using the OpenAI Responses API,
6. composes a daily report,
7. exports the selected set as a Zotero-compatible RIS file,
8. optionally commits and pushes the generated artifacts back to GitHub.

The first implementation should optimize for reliability and simple operation on a developer laptop.

## Goals

- Run locally on a daily schedule
- Use the existing `research-workspace/` structure
- Keep the ranking step cheap compared with full summarization
- Generate only Top K summaries
- Export RIS for Zotero import
- Support automatic `git add/commit/push`
- Keep model choice configurable

## Non-Goals

- Full PDF ingestion and full-text extraction in the first version
- GitHub Actions automation in the first version
- Multi-user workspaces
- Direct Zotero API synchronization

## Architecture

The pipeline should be implemented as a new module plus a CLI entrypoint:

- `src/auto_research/automation.py`
  Orchestrates the end-to-end daily run.
- `src/auto_research/openai_client.py`
  Minimal Responses API wrapper using `httpx`.
- `src/auto_research/ris.py`
  RIS export helpers.
- `src/auto_research/selection.py`
  Lightweight candidate ranking and Top K selection helpers.

CLI entrypoint:

- `auto-research daily-pipeline`

Wrapper script:

- `scripts/daily_pipeline.py`

## Pipeline Steps

### 1. Intake

Call existing intake logic against the configured workspace and profile.

### 2. Stage-1 Ranking

Use cheap signals from existing metadata:

- title
- abstract
- profile match heuristics
- recency

Produce a small candidate pool for model-based ranking.

### 3. Stage-2 Ranking

Use the OpenAI Responses API to rank the prefiltered candidates and select Top K.

Expected structured output:

- per-paper score
- short reason
- final Top K list

### 4. Summary Generation

For each Top K paper:

- if `problem-solution.md` already exists and overwrite is disabled, skip
- otherwise generate a short structured artifact from title + abstract + metadata
- validate the artifact with the existing extraction validator

### 5. Report

Run existing report composition after Top K summaries are materialized.

### 6. RIS Export

Export the selected Top K set to:

- `research-workspace/exports/zotero/<label>.ris`

### 7. Git Automation

If enabled:

- stage only generated workspace and export artifacts
- create a dated commit if there are changes
- push to the current branch

## Model Strategy

The pipeline should accept a configurable model name and default to an env var, e.g.:

- `AUTO_RESEARCH_MODEL`

The summarization prompts should target concise, structured extraction rather than long prose.

## Reliability Rules

- Do not overwrite existing summaries by default
- Validate model-generated artifacts before saving them
- Fail clearly if API key or model configuration is missing
- Keep ranking and summarization separate
- Restrict git staging to pipeline-owned outputs

## Outputs

- `research-workspace/papers/registry.jsonl`
- `research-workspace/papers/<id>/metadata.json`
- `research-workspace/papers/<id>/problem-solution.md`
- `research-workspace/reports/daily/<date>.md`
- `research-workspace/exports/zotero/<date>.ris`

## Open Questions

- Whether Top K should be selected from all fresh candidates or a recency-limited window
- Whether summaries should eventually upgrade from abstract-only to PDF-assisted extraction
