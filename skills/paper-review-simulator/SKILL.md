---
name: paper-review-simulator
description: Use when Codex should simulate a committee-style paper review before submission, especially when the author wants topic-aware reviewer assignment, independent reviewer perspectives, AE synthesis, and calibration checks on reviewer objectivity.
---

# Paper Review Simulator

## Overview

Use this skill to simulate a committee-style review before submission. The skill first analyzes the paper topic, infers committee assignment, generates `3 broad-field reviewers + 2 niche-field reviewers`, then runs five independent reviews plus one AE synthesis.

## Workflow

1. Read the paper package and the author's concerns.
2. Read `skills/paper-review-simulator/references/reviewer-modes.md` so you are grounded in the committee roles (broad, niche, AE) before assigning reviewers or drafting reviews.
3. Perform topic triage and write a short, reviewer-safe `committee assignment rationale`.
4. Generate five private reviewer assignment sheets:
   - reviewers `1-3`: `broad`
   - reviewers `4-5`: `niche`
5. Consolidate those private sheets into the AE-safe `Reviewer Assignment Sheet` (author-facing summary of the final assignments, never shown to reviewer voices) before reviewers begin their drafts; in isolated-agent setups the AE-safe sheet can be created right after the private sheets because reviewers never see it, while in fallback mode you must wait until all five reviewer drafts complete and only then materialize the sheet just before the AE stage.
6. Prefer isolated agents or fresh sessions for each reviewer and for the AE when the environment supports them.
7. Run reviewer 1 through reviewer 5 independently.
8. Run one AE review using the paper package, the reviewer-safe committee rationale, the consolidated `Reviewer Assignment Sheet`, and all five completed reviews.
9. Emit the final report in this exact order:
   - `Paper Theme Summary`
   - `Committee Assignment Rationale`
   - `Reviewer Assignment Sheet`
   - `Reviewer 1 Detailed Review`
   - `Reviewer 2 Detailed Review`
   - `Reviewer 3 Detailed Review`
   - `Reviewer 4 Detailed Review`
   - `Reviewer 5 Detailed Review`
   - `AE Meta-Review`

## Paper Theme Summary

The `Paper Theme Summary` should describe the high-level research question, the core domain, key contributions, and why the work matters. Keep this section focused on the paper's story and evidence; defer reviewer-role reasoning, risk balancing, and assignment logic to the `Committee Assignment Rationale` so the two sections stay distinct.

## Context Separation Contract

Keep these artifacts distinct:

- `reviewer-safe committee rationale`: shared context about topic, parent field, and broad-vs-niche risk split; no reviewer-specific private lenses
- `private reviewer assignment sheet` (per reviewer): working input for one reviewer only
- `Reviewer Assignment Sheet` (final report section): one author-facing, AE-safe consolidated summary of all five assignments that reviewer voices do not see

Visibility rules:

- each reviewer sees only their own private assignment sheet plus the reviewer-safe committee rationale
- no reviewer sees other reviewers' private assignment sheets
- the final consolidated `Reviewer Assignment Sheet` is for the user-facing report and the AE stage, while remaining hidden from reviewer voices

## Committee Assignment Rationale Contract

The `Committee Assignment Rationale` must:

- explain paper theme, likely parent field, key subfields, and why `3 broad + 2 niche` is appropriate
- distinguish broad-field risks vs niche-field risks
- stay reviewer-safe: do not reveal reviewer IDs, private reviewer roles, or reviewer-specific primary lenses

## Reviewer Assignment Sheet Contract

Before any detailed review text, define all five reviewer assignments in one `Reviewer Assignment Sheet` section.

Each reviewer assignment must include:

- `reviewer id`
- `reviewer type` (`broad` or `niche`)
- `task profile`
- `area expertise`
- `primary review lens`
- `key questions this reviewer will care about`
- `likely acceptance bar`

Assignment rules:

- reviewers `1-3` must be broad-field and non-redundant
- reviewers `4-5` must be niche-field and tied to the paper's technical core
- reviewer priorities should be differentiated, not restatements of one another

## Private Reviewer Assignment Sheet Contract

Each private reviewer assignment sheet must define:

- `reviewer id`
- `reviewer type` (`broad` or `niche`)
- `area expertise`
- `primary review lens` that maps directly to a subset of the paper, claims, or risks
- `critical tasks` (what this reviewer must inspect or validate)
- `key questions this reviewer will care about`
- `likely acceptance bar` plus any calibration notes

Keep each private sheet focused on the assigned lens and avoid restating other reviewers' priorities; these sheets feed the consolidated `Reviewer Assignment Sheet` that the AE consults once the reviews finish.

## Reviewer Output Contract

Each reviewer section (`Reviewer N Detailed Review`) must include these subsections in order:

1. `Reviewer Snapshot`
2. `Scorecard`
3. `Summary Verdict`
4. `Strengths`
5. `Weaknesses and Major Concerns`
6. `Detailed Comments`
7. `Confidence`

Scoring contract:

- use `0-10` scoring (decimals allowed) for:
  - originality
  - technical soundness
  - empirical support
  - clarity
  - significance / fit
  - overall score
- the `overall score` must stay on a `10-point` scale
- `significance / fit` meaning:
  - if venue is provided: fit to that venue plus likely impact in that community
  - if venue is not provided: fit to a strong general ML/AI conference bar, judged by problem importance, likely reader interest, and practical/research impact
- `Confidence` meaning:
  - confidence in this reviewer's own judgment quality, based on expertise match and evidence completeness
  - report as `0-10` with a one-line justification

## AE Output Contract

The AE receives only the paper package, the reviewer-safe committee rationale, the consolidated `Reviewer Assignment Sheet`, and the five completed reviews before drafting any synthesis, so it can check whether each reviewer stuck to their assigned focus.

`AE Meta-Review` must include these subsections in order:

1. `AE Summary`
2. `Consensus and Disagreement`
3. `Final Score`
4. `Reviewer Quality Audit`
5. `Final Recommendation`

AE scoring contract:

- provide `final score /10` and `confidence`
- do not compute only a mechanical average; use paper evidence plus reviewer evidence
- include an explicit objectivity and calibration audit for reviewers 1 through 5
- AE `confidence` meaning:
  - confidence in the AE's integrated final judgment quality after weighing paper evidence and reviewer quality
  - report as `0-10` with a one-line justification

## Independence Rules

Treat independence as a hard requirement when isolated agents or fresh sessions are available; fallback mode is a best-effort emulation that still stages the same sequential reviews while trying not to leak prior content.

- use isolated agents or fresh sessions for reviewers and AE whenever supported
- each reviewer sees only:
  - the paper package
  - the reviewer-safe committee rationale
  - that reviewer's private assignment sheet
- reviewers must not see:
  - other reviewer assignments
  - other reviewer outputs
  - AE synthesis
- AE sees:
  - paper package
  - reviewer-safe committee rationale
  - the consolidated `Reviewer Assignment Sheet`
  - all five completed reviews
- AE must not draft reviewer opinions on reviewers' behalf

## Fallback Mode

If isolated agents or fresh sessions are unavailable, run the same staged protocol in one session:

1. topic triage
2. five private reviewer assignment sheets
3. reviewer 1 review
4. reviewer 2 review
5. reviewer 3 review
6. reviewer 4 review
7. reviewer 5 review
8. consolidate the private sheets into the AE-safe `Reviewer Assignment Sheet` (do not expose this to reviewer drafts)
9. AE synthesis

Fallback constraints:

- keep reviewer voices independent and differentiated
- avoid leaking prior reviewer conclusions into later reviewer reasoning
- preserve the same final section order and output contracts

## Input Guidance

If the user does not know how to package inputs, direct them to [review-input-template.md](assets/review-input-template.md).

Preferred inputs:

- title
- abstract
- introduction / motivation
- claimed contributions
- method overview
- experiment summary
- related work / baseline notes
- author worries or likely confusion points
- optional: target venue or review context
- optional: where the author expects misreading
- optional: requested emphasis (positioning, experiments, clarity)

## Revision Loop

Revision mode uses a **delta/update output**, not a full fresh committee report.

The delta output must include the following sections:

1. `Revision Summary` describing the core paper changes and how they impact the key claims.
2. `Reviewer Deltas` listing each reviewer, the updated status of their major concerns (`resolved`, `partially resolved`, `unresolved`), and the evidence for the status.
3. `AE Update` stating whether the overall outcome changed materially, any shifts in calibration/objectivity, and a `Final Recommendation` if it moved.
4. `Next Steps` (optional) advising the author on targeted follow-up or clarifications.

When the user provides a revised draft:

- compare the revision against prior major reviewer concerns
- mark each concern as `resolved`, `partially resolved`, or `unresolved`
- preserve reviewer identity when possible and report per-reviewer deltas
- include an AE update stating whether the overall outcome changed materially
- only regenerate a full fresh committee report if the paper scope changed substantially
