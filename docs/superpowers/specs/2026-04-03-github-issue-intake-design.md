# GitHub Issue Intake Design

Status: Draft for implementation
Date: 2026-04-03

## Summary

Build a local intake flow that reads GitHub issues from the current repository, extracts structured demand from a lightweight markdown template, and writes the result into a stable workspace tree keyed by `direction + GitHub username`.

The flow should let one user repeatedly submit issues for the same direction, while local runs keep a per-issue history and refresh a cumulative summary for that user-direction pair.

## Goals

- Read issue requests from the current GitHub repository by using the local `gh` CLI
- Support a lightweight issue template with only one required machine-readable field: `direction`
- Persist issue requests under a stable directory shaped by `direction + GitHub username`
- Preserve each issue as an individual request record
- Rebuild a cumulative summary for the same user and direction on each sync
- Support optional git add, commit, and push for generated intake artifacts
- Remain resilient if the repository is renamed on GitHub

## Non-Goals

- Running issue intake inside GitHub Actions
- Supporting multiple repositories in the first version
- Enforcing a rigid issue body schema beyond `direction`
- Auto-merging issue demand into the paper selection profile in the first version
- Processing issue comments, reactions, or project metadata in the first version

## User Workflow

### 1. Submit an Issue

The user opens an issue in this repository with markdown frontmatter:

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

Rules:

- `direction` is required
- The GitHub issue title remains free-form and acts as the human-readable request title
- Body sections are optional and may vary in content
- The raw body should still be preserved even if some sections are missing

### 2. Run Local Sync

The operator runs a new CLI command locally:

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace --push
```

The command should:

1. discover the GitHub repository from the local git remote by default
2. fetch issue data through `gh`
3. parse valid issue requests
4. write or update workspace artifacts
5. optionally stage, commit, and push only intake-owned files

## Workspace Layout

The workspace gains a new subtree:

```text
research-workspace/
  issue-intake/
    <direction-slug>/
      <github-username>/
        profile.json
        summary.md
        requests/
          <issue-number>.md
```

The directory contract is:

- `<direction-slug>` comes from the parsed `direction`
- `<github-username>` comes from the issue author login
- `requests/<issue-number>.md` stores the normalized representation of that issue
- `summary.md` stores the cumulative summary for that user and direction
- `profile.json` stores machine-readable sync metadata

## Data Model

### Request Artifact

Each issue should be normalized into one markdown file at:

`research-workspace/issue-intake/<direction>/<user>/requests/<issue-number>.md`

The file should contain:

- issue number
- issue title
- issue state
- author login
- direction
- created time
- updated time
- source URL
- extracted sections when available
- original body for fallback traceability

### Profile Metadata

`profile.json` should include:

- `direction`
- `github_username`
- `last_synced_at`
- `latest_issue_updated_at`
- `processed_issues`

`processed_issues` should map issue number to the last seen GitHub `updatedAt` value so the sync can skip unchanged items.

### Summary Artifact

`summary.md` should be regenerated from all request files for the same user-direction directory.

The summary should include:

- direction
- GitHub username
- request count
- active issue list
- merged background themes
- merged requirements
- merged constraints
- recent notes

The first version should prefer deterministic concatenation and deduplication over model-generated summarization.

## Repository Discovery

The sync should not hardcode the repository name.

Default behavior:

- inspect the current git remote
- derive `owner/repo` from the GitHub remote URL

Override behavior:

- allow `--repo owner/repo` to bypass remote parsing

This keeps the workflow working after a repository rename as long as the local remote is updated.

## GitHub Intake Mechanics

The implementation should use `gh` as the transport layer.

Recommended commands:

- `gh issue list --repo <owner/repo> --limit <n> --state open --json number,title,body,author,createdAt,updatedAt,url,state`
- optionally `--state all` when the CLI asks for all issues

The first version should default to `open` issues only.

Reliability requirements:

- fail clearly if `gh` is unavailable
- fail clearly if the user is not authenticated
- fail clearly if repository discovery fails
- ignore issues whose body does not contain valid frontmatter with `direction`

## Parsing Rules

### Frontmatter

Accepted format:

- body starts with YAML frontmatter
- frontmatter contains `direction`

Validation rules:

- reject empty `direction`
- normalize direction to a filesystem-safe slug
- preserve the original direction value in request content if normalization changes spelling

### Body Sections

The parser should look for common markdown headings:

- `Background`
- `Requirements`
- `Constraints`
- `Notes`

Rules:

- section extraction is best-effort, not mandatory
- if a section is absent, store an empty value
- always preserve the full raw body

## Sync Semantics

For each parsed issue:

1. compute the target directory from `direction + username`
2. load `profile.json` if it exists
3. compare stored `updatedAt` with the current GitHub value
4. create or update `requests/<issue-number>.md` when needed
5. update `profile.json`
6. regenerate `summary.md`

Behavior details:

- a new issue in the same user-direction pair creates a new request file and refreshes the shared summary
- an edited issue overwrites only its own request file, then refreshes the shared summary
- issues from the same user but different directions go to different directories
- issues from different users but the same direction go to sibling directories under that direction

## CLI Surface

Add a new command:

- `auto-research sync-issues`

Recommended arguments:

- `--workspace`, default `research-workspace`
- `--repo`, optional override for `owner/repo`
- `--state`, choices `open` or `all`, default `open`
- `--limit`, positive integer, default a practical cap such as `100`
- `--push`, optional git push after artifact changes

CLI output should report:

- how many issues were inspected
- how many valid intake issues were parsed
- how many request files changed
- which summary directories were refreshed

## Git Automation

When `--push` is enabled:

- stage only `research-workspace/issue-intake/`
- commit only if staged content changed
- use a deterministic commit message such as `chore: sync issue intake 2026-04-03`
- push to the current branch

This should not stage unrelated workspace outputs.

## Architecture

Add a new module:

- `src/auto_research/github_intake.py`

Responsibilities:

- parse git remote into `owner/repo`
- call `gh`
- parse issue frontmatter and markdown sections
- write request artifacts, profile metadata, and summaries
- optionally stage/commit/push intake outputs

CLI integration:

- extend `src/auto_research/cli.py` with `sync-issues`

Workspace integration:

- update `src/auto_research/workspace.py` so `ensure_workspace()` creates `issue-intake`

## Testing Strategy

Tests should cover:

- workspace initialization creates the new `issue-intake` subtree
- repository parsing handles common GitHub remote URL forms
- parser accepts valid frontmatter and rejects missing direction
- sync creates the expected direction-user directory layout
- repeated sync updates only changed issues
- summary regeneration reflects multiple issues for the same user-direction pair
- CLI command validates invalid limits and surfaces sync failures
- git staging for push mode is limited to the intake subtree

`gh` access should be mocked through `subprocess.run` boundaries so tests stay offline.

## Reliability Rules

- Never delete existing request files for issues that are absent from the current fetch result in the first version
- Never write outside the workspace intake subtree except for explicit git commands
- Prefer deterministic file formats over LLM-generated content
- Keep request artifacts readable by humans and machines
- Tolerate partial section parsing as long as direction and raw body are preserved

## Open Questions

- Whether closed issues should later be mirrored into summary status by default
- Whether future versions should add labels or milestones as optional metadata
- Whether user-direction summaries should eventually produce downstream profile patches automatically
