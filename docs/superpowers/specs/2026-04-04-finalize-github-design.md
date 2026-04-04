# Finalize GitHub Design

Status: Draft for implementation
Date: 2026-04-04

## Summary

Split GitHub post-processing out of `daily-pipeline` into a new `finalize-github` command so paper discovery and summarization can run in one network environment while GitHub push/comment/close can run later in another.

This is specifically intended for environments where arXiv/model access and GitHub access require different proxy settings.

## Goals

- Let `daily-pipeline` finish without requiring GitHub connectivity
- Persist enough metadata after a successful run so GitHub post-processing can be retried later
- Add a new `finalize-github` command that performs `git push`, issue comment, and issue close
- Prevent duplicate comment/close work on already finalized runs
- Keep the command deterministic and easy to retry

## Non-Goals

- Re-running paper intake or summarization inside `finalize-github`
- Recomputing which issues were consumed during finalize time
- Supporting multiple pending finalize records in the first version
- Reopening issues or undoing a finalize run

## Workflow

### Step 1: Run the daily pipeline

```bash
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace
```

Expected behavior:

- generate the normal paper summary artifacts
- if fallback profile generation was used, collect GitHub finalize metadata
- write finalize metadata to a local state file
- do not require GitHub connectivity in this step

### Step 2: Run GitHub finalize later

```bash
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace
```

Expected behavior:

1. read the local finalize state file
2. stop if it is missing
3. stop if the file says finalize already completed
4. run `git push`
5. if push succeeds, comment on consumed issues
6. close issues whose comment step succeeded
7. mark the finalize file as completed

## Finalize State File

Persist finalize metadata to:

`research-workspace/pipeline/github-finalize.json`

Suggested fields:

- `label`
- `repo`
- `report_path`
- `daily_summary_path`
- `used_fallback_profile`
- `consumed_issue_numbers`
- `source_keys`
- `status`
- `created_at`
- `finalized_at`

Status values:

- `pending`
- `completed`

## Creation Rules

`daily-pipeline` should write the finalize state file only when:

- the run completed successfully
- fallback profile generation was used
- at least one consumed issue number is available

If fallback profile generation was not used:

- either do not create the file
- or create it with a clear state that `finalize-github` treats as non-actionable

The first version should prefer not creating the file unless there is actual GitHub work to do.

## Finalize Command Behavior

### Missing File

If `research-workspace/pipeline/github-finalize.json` does not exist:

- return a clear error
- explain that there is no pending GitHub finalize work

### Already Finalized

If the file exists and `status` is `completed`:

- do not repeat push/comment/close
- print a clear message that the run was already finalized

### Pending Finalize

If the file exists and `status` is `pending`:

- run `git push`
- abort if push fails
- comment on consumed issues
- close issues whose comment succeeded
- update `status` to `completed`
- write `finalized_at`

## Failure Handling

### Push Failure

If `git push` fails:

- stop immediately
- do not comment or close issues
- keep the state file `pending`

This lets the operator fix network conditions and retry later.

### Comment Failure

If commenting on one issue fails:

- skip closing that issue
- continue with other issues
- still allow finalize to complete if the rest succeed

### Close Failure

If closing one issue fails:

- record a warning
- continue with other issues
- still allow finalize to complete

The first version may still mark finalize as completed once the command finishes its best-effort pass, as long as the operator saw warnings.

## CLI Surface

Add a new command:

- `auto-research finalize-github`

Recommended arguments:

- `--workspace`, default `research-workspace`

Optional future arguments:

- `--force`
- `--repo`

The first version does not require these optional flags.

## Architecture

Recommended implementation split:

- `src/auto_research/automation.py`
  write the finalize metadata file after successful pipeline runs when fallback profile generation was used
- `src/auto_research/github_intake.py`
  reuse existing GitHub comment/close helpers and add any small shared finalize helpers if needed
- `src/auto_research/cli.py`
  add `finalize-github`

## Testing Strategy

Tests should cover:

- successful fallback pipeline run writes a pending finalize file
- pipeline runs without fallback profile do not create pending finalize work
- `finalize-github` fails clearly when the state file is missing
- `finalize-github` skips repeated work when the state file is already completed
- `finalize-github` runs push then issue comment then issue close
- push failure leaves the state file pending
- comment failure skips close for that issue
- close failure does not crash finalize

## Reliability Rules

- never let `daily-pipeline` require GitHub connectivity for normal content generation
- never close issues inside `finalize-github` before a successful `git push`
- never repeat finalized work unless an explicit future force mode is added
- keep the finalize state file human-readable and easy to inspect

## Open Questions

- whether future versions should support multiple pending finalize files keyed by label
- whether future versions should store partial per-issue finalize outcomes in the state file
