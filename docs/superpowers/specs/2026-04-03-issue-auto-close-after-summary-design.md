# Issue Auto-Close After Summary Design

Status: Draft for implementation
Date: 2026-04-03

## Summary

Extend the daily paper pipeline so that when a missing profile is synthesized from `issue-intake/` and the pipeline run completes successfully, the pipeline comments on and closes the open GitHub issues that contributed to that synthesized profile.

This gives the GitHub issue intake workflow a clear end state without requiring manual issue cleanup.

## Goals

- Close only the issues that were actually consumed by the fallback profile generation for the current successful pipeline run
- Leave a short comment before closing each issue
- Keep issue closing best-effort so summary generation still succeeds even if GitHub operations fail
- Use the local `gh` CLI so the workflow stays aligned with the current intake transport

## Non-Goals

- Closing issues when the pipeline used an existing hand-authored profile
- Closing issues that were not part of the current fallback profile source set
- Reopening issues automatically
- Tracking paper-level matching between issue requests and selected papers in the first version

## Trigger Rules

Issue auto-close should run only when all of the following are true:

- `daily-pipeline` completed successfully
- the pipeline had to generate `research-workspace/profile/interest-profile.md` because it was missing
- the generated profile recorded at least one source `direction + github_username` pair
- the mapped GitHub issues are currently open

If any of the above is false:

- do not attempt issue closing

## Consumption Definition

For the first version, an issue counts as “consumed” when:

- its request directory participated in the fallback profile generation
- that fallback profile was used by the current successful `daily-pipeline` run

This intentionally avoids more complex paper-level attribution in the first version.

## Source Mapping

The fallback profile generation step should expose enough metadata for later closing:

- source `direction + github_username` directories used
- the individual issue numbers belonging to those directories
- the repository identifier used for the run

This metadata may be returned directly from helper functions or stored in a small structured object during the run.

## GitHub Closing Behavior

For each consumed issue that is still open:

1. post a comment
2. close the issue

Recommended comment content:

- say that the request has been incorporated into the completed daily paper summary workflow
- include the pipeline label or date
- optionally include the generated report path and summary path

The comment should be concise and deterministic.

## Transport

Use `gh` for both comment and close actions.

Recommended commands:

- `gh issue comment <number> --repo <owner/repo> --body <comment>`
- `gh issue close <number> --repo <owner/repo>`

Repository resolution should follow the existing intake pattern:

- default to current git remote parsing
- still allow reuse of an explicit `owner/repo` when already known inside the run

## Failure Handling

GitHub comment or close failures must not fail the entire daily pipeline after outputs are already generated.

Rules:

- record warnings in-process when comment fails
- skip close if comment fails in the same attempt
- record warnings when close fails
- continue the pipeline completion path

This keeps the paper summary workflow primary and issue closing secondary.

## Existing Profile Behavior

If `research-workspace/profile/interest-profile.md` already existed before the run:

- do not auto-close any issues

This avoids accidentally closing issues that were not the actual driver of the current report.

## Architecture

Recommended implementation split:

- `src/auto_research/github_intake.py`
  add helpers for collecting issue numbers from source directories and calling `gh` comment/close commands
- `src/auto_research/automation.py`
  preserve fallback-profile metadata during the run and trigger auto-close after successful completion

## Testing Strategy

Tests should cover:

- successful fallback run comments on and closes the expected issue numbers
- existing manual profile skips auto-close entirely
- pipeline failure before completion skips auto-close
- comment failure prevents close for that issue but does not fail the run
- close failure records a warning and does not fail the run
- only issues from the source directories used in fallback generation are targeted

All GitHub operations should be mocked through `subprocess.run`.

## Reliability Rules

- never close issues unless the current run both used fallback profile generation and completed successfully
- never fail the completed summary run only because issue close cleanup failed
- never target issues outside the source directories used for the fallback profile
- keep comment text deterministic and easy to audit

## Open Questions

- whether future versions should add labels instead of closing issues immediately
- whether future versions should write close-status metadata back into `issue-intake/`
