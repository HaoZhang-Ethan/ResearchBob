# Direction-Isolated Automation Design

Status: Draft for implementation
Date: 2026-04-09

## Summary

Restructure the GitHub-issue-driven research workflow so that `direction` becomes the isolation boundary for all generated research artifacts.

GitHub issue intake already lands under `research-workspace/issue-intake/<direction>/...`, but the downstream pipeline still synthesizes a single global profile and writes reports, exports, paper state, and finalize state into shared workspace directories. That mixes unrelated research directions together.

This design moves all downstream automation outputs into per-direction sub-workspaces under `research-workspace/directions/<direction>/...` and requires automation commands to operate on one direction at a time.

## Goals

- Make `direction` the canonical partition key for automated research runs
- Prevent papers, reports, exports, pipeline state, and fallback profiles from mixing across directions
- Keep GitHub issue intake as the root source of truth for requested directions
- Allow one repository to serve multiple unrelated research directions safely
- Keep the resulting directory layout explicit and easy to inspect manually

## Non-Goals

- Automatically migrating existing mixed global artifacts into direction-specific workspaces
- Preserving compatibility with implicit multi-direction fallback generation
- Inferring direction from GitHub usernames, repository names, or historical artifact locations
- Deduplicating papers across directions in the first version
- Building a scheduler that runs all directions automatically in one command

## Problem Statement

Today the flow behaves like this:

1. `sync-issues` writes requests under `research-workspace/issue-intake/<direction>/<github-username>/`
2. `daily-pipeline` can auto-generate a single `research-workspace/profile/interest-profile.md`
3. The pipeline writes shared outputs under global `papers/`, `reports/`, `exports/`, and `pipeline/`

This means a request for direction `A` can influence the same profile, candidate pool, reports, and exports as direction `B`, even when the user explicitly does not want those topics mixed.

## Directory Model

The root workspace should separate raw intake from per-direction execution state:

```text
research-workspace/
  issue-intake/
    <direction>/
      <github-username>/
        profile.json
        summary.md
        requests/*.md

  directions/
    <direction>/
      profile/interest-profile.md
      papers/
      reports/daily/
      reports/manual/
      reports/longterm/
      exports/zotero/
      pipeline/
```

Rules:

- `issue-intake/` remains the shared inbound request area
- `directions/<direction>/` is the execution root for that direction
- all generated research artifacts for a direction must stay inside its execution root
- different directions must never share profile files, paper registry/state, reports, exports, or finalize state

## Direction Identity

`direction` comes from the GitHub issue frontmatter and is normalized with the existing slugification rules.

The normalized direction slug is used for:

- `research-workspace/issue-intake/<direction>/...`
- `research-workspace/directions/<direction>/...`
- CLI selection and state lookup

GitHub usernames remain useful only as request provenance inside a direction. They must not define storage boundaries for pipeline outputs.

## Command Behavior

### `sync-issues`

No change to its purpose:

- fetch GitHub issues
- parse `direction`
- write request artifacts under `research-workspace/issue-intake/<direction>/<github-username>/`

It does not generate direction workspaces or run research automation.

### `daily-pipeline`

Add `--direction <slug>`.

Behavior:

- when `--direction` is provided, run only that direction
- resolve the execution root as `research-workspace/directions/<direction>/`
- keep using `research-workspace/issue-intake/<direction>/` as the fallback source when needed

If `--direction` is omitted:

- if exactly one usable direction exists in `issue-intake/`, auto-select it
- if multiple directions exist, fail with a clear error requiring explicit `--direction`
- if no usable direction exists and no profile was explicitly supplied, fail clearly

### `compose-report`

Add `--direction <slug>` and write to:

- `research-workspace/directions/<direction>/reports/daily/<label>.md`
- `research-workspace/directions/<direction>/reports/manual/<label>.md`

### `finalize-github`

Add `--direction <slug>` and only read/write finalize state for that direction.

It must not inspect or act on issue numbers from any other direction.

## Fallback Profile Generation

Fallback generation changes from global aggregation to single-direction synthesis.

New rule:

- when `daily-pipeline --direction <x>` needs a profile and `research-workspace/directions/<x>/profile/interest-profile.md` is missing
- synthesize that profile only from `research-workspace/issue-intake/<x>/`

Implications:

- do not aggregate multiple directions into one fallback profile
- do keep aggregating multiple GitHub users inside the same direction
- do preserve source provenance with `direction/user` lines
- do collect consumed issue numbers only from that direction

Expected generated path:

- `research-workspace/directions/<direction>/profile/interest-profile.md`

## Execution Root Resolution

Introduce a small workspace-resolution layer that can answer:

- what is the shared workspace root
- what is the execution root for a given direction
- what is the intake root for a given direction

Recommended helper behavior:

- `ensure_workspace(root)` continues to guarantee root-level shared directories such as `issue-intake/`
- a new helper resolves `root / "directions" / <direction>` and ensures the execution subdirectories exist there
- downstream modules that currently write to `workspace / "papers"` or `workspace / "reports"` should receive the direction execution root instead of the shared root

This keeps most modules unchanged once they are pointed at the direction-specific root.

## Finalize State

Move pending GitHub finalize state from the shared location into the direction execution root:

- old: `research-workspace/pipeline/github-finalize.json`
- new: `research-workspace/directions/<direction>/pipeline/github-finalize.json`

State should include:

- the direction slug
- the direction-local report and summary paths
- the issue numbers consumed for that direction only
- the GitHub repo
- pending/completed status fields

`finalize-github --direction <x>` must push once, then comment/close only the issue numbers recorded in that direction-local state file.

## Data Migration Strategy

Do not automatically migrate the old shared directories:

- `research-workspace/profile/`
- `research-workspace/papers/`
- `research-workspace/reports/`
- `research-workspace/exports/`
- `research-workspace/pipeline/`

Reason:

- those locations may already contain mixed-direction data
- automatic migration would assign ambiguous artifacts to one direction without reliable provenance

Compatibility policy:

- leave historical global artifacts untouched
- stop relying on them for new automated direction runs
- document that new direction-isolated automation writes only into `research-workspace/directions/<direction>/`

## Testing Strategy

Tests should cover:

- `daily-pipeline --direction <x>` generates fallback profile only from `issue-intake/<x>/`
- multiple directions present plus missing `--direction` fails clearly
- one direction present plus missing `--direction` auto-selects that direction
- reports, daily summaries, longterm summaries, bundle files, RIS exports, and run history all write under `directions/<direction>/`
- paper metadata and derived analysis artifacts are stored under `directions/<direction>/papers/`
- finalize state is written and consumed per direction
- consumed issue numbers for direction `A` never include requests from direction `B`
- `sync-issues` still writes summaries and requests to the existing intake layout

## Reliability Rules

- never mix direction-local pipeline outputs across directories
- never generate a fallback profile from more than one direction in a single run
- never infer storage partitioning from GitHub usernames
- fail fast when multiple directions exist but the command target is ambiguous
- preserve deterministic path selection from normalized direction slugs

## Open Questions

- whether a future `run-all-directions` command should orchestrate one-direction-at-a-time runs
- whether a manual migration tool should later help archive or inspect legacy shared artifacts
