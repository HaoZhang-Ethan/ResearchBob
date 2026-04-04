# Issue Intake Profile Fallback Design

Status: Draft for implementation
Date: 2026-04-03

## Summary

Extend the daily paper pipeline so that when `research-workspace/profile/interest-profile.md` is missing, the pipeline can deterministically synthesize a replacement profile from `research-workspace/issue-intake/` and continue running.

This keeps the GitHub issue intake path operational without requiring a manually authored profile first.

## Goals

- Allow `daily-pipeline` to proceed when the profile file is missing
- Generate `research-workspace/profile/interest-profile.md` automatically from issue intake artifacts
- Reuse the existing profile markdown structure so the rest of the pipeline stays unchanged
- Keep the generation deterministic and offline in the first version
- Preserve source provenance inside the generated profile

## Non-Goals

- Rebuilding the profile on every pipeline run
- Overwriting a hand-authored profile file
- Using an LLM to generate the fallback profile in the first version
- Supporting per-user or per-direction isolated daily pipelines in the first version

## Trigger Rules

The fallback should run only when all of the following are true:

- `daily-pipeline` is invoked
- `research-workspace/profile/interest-profile.md` does not exist
- `research-workspace/issue-intake/` contains at least one usable intake directory

If the profile file already exists:

- do not regenerate it
- do not overwrite it
- continue using the existing file

If the profile file is missing and no usable issue intake data exists:

- fail clearly
- explain that there is neither an existing profile nor issue intake data to synthesize one

## Data Sources

The fallback reads from:

- `research-workspace/issue-intake/<direction>/<github-username>/summary.md`
- optionally `research-workspace/issue-intake/<direction>/<github-username>/requests/*.md` when summary content is too thin

Each `<direction>/<github-username>/` directory acts as one source unit.

## Merge Strategy

The generated profile should aggregate all available user-direction intake directories under the current workspace.

### Source Inventory

At the top of the generated profile, include:

- an explicit note that the file was auto-generated
- generation time
- the list of source `direction + github_username` pairs used

### Section Mapping

Map intake information into the existing profile structure:

- `Core Interests`
  include direction names and repeated high-signal topics from summaries or requests
- `Soft Boundaries`
  include adjacent but non-core areas mentioned in summaries or requests
- `Exclusions`
  include clearly negative constraints such as “avoid pure benchmark papers”
- `Current-Phase Bias`
  include active preferences repeatedly emphasized in recent requests
- `Evaluation Heuristics`
  include ranking preferences such as recency, implementation detail, or open-source availability
- `Open Questions`
  include exploratory questions and unresolved themes extracted from background and notes

### Multi-User Handling

- do not embed GitHub usernames into every bullet
- do keep usernames in the provenance block at the top
- aggregate all sources into one workspace-level profile because the current pipeline is still single-workspace

### Conflict Handling

- preserve both sides when requests conflict
- when a preference is too ambiguous or conflicting to become a hard constraint, place it in `Soft Boundaries` or `Open Questions`
- keep the first version simple and deterministic; do not introduce weighting or ranking rules beyond basic deduplication

## File Format

The generated file should still validate under the existing profile validator.

Expected structure:

```md
# Research Interest Profile

> Auto-generated from GitHub issue intake on 2026-04-03T12:34:56Z.
> Sources:
> - llm-agents / alice
> - agent-memory / bob

## Core Interests
- ...

## Soft Boundaries
- ...

## Exclusions
- ...

## Current-Phase Bias
- ...

## Evaluation Heuristics
- ...

## Open Questions
- ...
```

## Daily Pipeline Integration

Add a preflight step before the pipeline loads the profile:

1. resolve the target profile path
2. if the file exists, continue normally
3. if the file is missing, attempt to synthesize it from `issue-intake/`
4. validate the generated profile text
5. write the file to `research-workspace/profile/interest-profile.md`
6. continue the pipeline with the generated file

If validation fails:

- do not continue
- raise a clear error explaining that fallback profile generation produced invalid output

## Architecture

Recommended implementation split:

- `src/auto_research/github_intake.py`
  add helpers for reading intake directories and rendering a fallback profile
- `src/auto_research/automation.py`
  add the preflight profile fallback hook before loading the profile

No CLI surface change is required for the first version because the behavior is automatic inside `daily-pipeline`.

## Testing Strategy

Tests should cover:

- missing profile plus usable issue-intake data generates a valid profile file
- existing profile file is never overwritten by fallback generation
- missing profile plus empty issue-intake fails with a clear error
- generated profile includes provenance lines for source directories
- generated profile passes the existing profile validator
- `daily-pipeline` continues successfully after fallback generation when the rest of the pipeline is mocked

## Reliability Rules

- never overwrite an existing profile file
- never generate a profile outside the workspace profile directory
- never require network access for fallback generation
- prefer deterministic text extraction and deduplication over clever heuristics
- keep the generated profile readable enough for later manual editing

## Open Questions

- whether future versions should support regenerating the profile on demand
- whether a dedicated `build-profile-from-issues` command should later be added for manual control
