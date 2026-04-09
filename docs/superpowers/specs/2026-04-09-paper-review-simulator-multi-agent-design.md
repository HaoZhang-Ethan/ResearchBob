# Paper Review Simulator Multi-Agent Design

Status: Draft for implementation
Date: 2026-04-09

## Summary

Refactor `paper-review-simulator` from a single mixed-mode reviewer into a committee-style review workflow. The new skill should first analyze the paper's topic, infer what kind of review committee it would likely be assigned to, generate `3 broad-field reviewers + 2 niche-field reviewers`, and only then run five independent reviews plus one independent AE synthesis.

The core behavioral change is not only a new report format. The skill should explicitly prefer isolated agents or fresh sessions for the five reviewers and the AE whenever the environment supports them. If isolation is unavailable, the skill should still emulate the same staged workflow in one session without leaking reviewer opinions forward.

## Goals

- Analyze the paper before reviewing and infer a plausible committee composition
- Generate five reviewer assignments:
  - three broad-field reviewers
  - two niche-field reviewers
- For each reviewer, produce:
  - a reviewer task profile
  - reviewer-specific evaluation priorities
- Run five detailed reviews independently
- Require a `10-point overall score` from each reviewer
- Create an AE stage that reads the paper and all five reviews
- Require the AE to produce:
  - a final assessment
  - a final `10-point` score
  - a consensus summary
  - an evaluation of whether each reviewer was objective and well-calibrated
- Output one integrated report with sections for theme analysis, reviewer assignments, all five reviews, and AE synthesis
- Preserve support for revision follow-up by comparing a revised draft against prior concerns

## Non-Goals

- Predicting the exact real-world reviewers of a venue
- Reproducing venue-specific review forms or decision rubrics exactly
- Running citation lookup or external literature search by default
- Averaging scores mechanically without AE judgment
- Turning the skill into a paper-writing or rebuttal-writing skill

## User Workflow

### 1. User Supplies a Paper Package

The skill should accept the existing paper package inputs:

- title
- abstract
- introduction / motivation
- claimed contributions
- method overview
- experiment summary
- related work / baseline notes
- author worries or likely confusion points

The existing lightweight input template should remain valid, but it should be expanded to mention the committee-style workflow and optional venue/context hints.

### 2. Skill Performs Topic Triage

Before any reviewer is created, the skill should infer:

- the paper's main topic
- the likely parent field
- the important subfields
- what reviewer mix would plausibly be assigned
- which review risks are broad-field versus niche-field concerns

This stage should produce a short `committee assignment rationale` that explains why the paper would likely receive these five reviewer types.

### 3. Skill Generates Reviewer Assignment Sheets

The skill should create five assignment sheets before asking for any full review.

Each assignment sheet must include:

- `reviewer id`
- `reviewer type` (`broad` or `niche`)
- `task profile`
- `area expertise`
- `primary review lens`
- `key questions this reviewer will care about`
- `likely acceptance bar`

The five assignments should be differentiated and non-redundant. They should not all ask the same questions in different words.

### 4. Skill Runs Five Independent Reviews

Each reviewer should receive:

- the paper package
- the global committee rationale
- only that reviewer's assignment sheet

Each reviewer should not see:

- other reviewers' assignments
- other reviewers' comments
- AE synthesis

The review outputs should be written as if they were produced independently.

### 5. Skill Runs an Independent AE Synthesis

The AE should receive:

- the paper package
- the committee rationale
- the five completed reviews

The AE should not simply average the scores. The AE should interpret agreement, disagreement, paper strength, and reviewer quality before issuing a final assessment.

## Committee Construction Rules

### Broad-Field Reviewers

The three broad-field reviewers should represent researchers who are credible within the larger parent area and who care about:

- problem significance
- framing
- novelty boundary
- clarity
- methodological plausibility
- overall venue fit

They may have distinct emphases, but they should read like reviewers from the same broad area rather than domain outsiders.

### Niche-Field Reviewers

The two niche-field reviewers should represent subcommunity experts closest to the paper's technical core.

They should care more about:

- technical depth
- missing baselines
- hidden assumptions
- ablations or controls
- evaluation design
- whether the claimed contribution is actually new within the narrow subfield

The niche reviewers should be chosen dynamically from the paper topic rather than from a fixed archetype list.

## Review Stage Contract

Each reviewer should output the following sections in order.

### 1. Reviewer Snapshot

- reviewer id
- reviewer type
- expertise summary
- primary lens

### 2. Scorecard

Each reviewer should provide `0-10` scores for:

- originality
- technical soundness
- empirical support
- clarity
- significance / fit
- overall score

The reviewer may use decimals, but the scale must remain `10-point`.

### 3. Summary Verdict

A short paragraph stating whether the paper appears promising, borderline, or weak from that reviewer's perspective.

### 4. Strengths

Concrete strengths, not generic praise.

### 5. Weaknesses and Major Concerns

Ordered from most important to least important. These should include likely misunderstandings as well as true flaws.

### 6. Detailed Comments

Actionable reviewer-style comments that explain the reasoning behind the score.

### 7. Confidence

The reviewer should state how well the paper matches their expertise and how confident they are in their judgment.

## AE Stage Contract

The AE should output the following sections in order.

### 1. AE Summary

- brief paper assessment
- overall paper quality
- likely decision posture

### 2. Consensus and Disagreement

The AE should summarize:

- where reviewers agree
- where reviewers disagree
- whether disagreement comes from paper ambiguity, evidence gaps, or reviewer calibration differences

### 3. Final Score

The AE should provide:

- `final score /10`
- `confidence`

The AE should explain the score using reviewer evidence plus direct reading of the paper.

### 4. Reviewer Quality Audit

For each reviewer, the AE should state:

- whether the review was objective
- whether the reviewer focused on the right issues
- whether the reviewer over-indexed on a narrow concern
- whether the reviewer appears too lenient, too harsh, or well-calibrated

### 5. Final Recommendation

The AE should end with a concise integrated recommendation that explains the decisive acceptance or rejection factors.

## Independence Rules

The skill should treat independence as a first-class requirement rather than a suggestion.

Preferred execution order:

1. create five fresh reviewer agents or new sessions
2. create one fresh AE agent or new session
3. keep reviewer contexts isolated from each other
4. keep AE isolated from the main session except for the paper package and completed reviews

The skill text should explicitly say:

- use isolated agents or fresh sessions when supported
- do not let reviewer outputs influence each other
- do not let the AE draft reviewer opinions on their behalf
- do not let the AE rely only on score averaging

## Fallback Mode

If the environment does not support multiple agents or fresh sessions, the skill should still follow the same staged protocol in one session:

1. topic triage
2. reviewer assignment sheets
3. reviewer 1 review
4. reviewer 2 review
5. reviewer 3 review
6. reviewer 4 review
7. reviewer 5 review
8. AE synthesis

Fallback-mode instructions should explicitly require the model to avoid leaking previous reviewer conclusions into the next reviewer voice. The report should still read as five differentiated reviewers plus one AE.

## Final Report Contract

The final report should be emitted in this order:

1. `Paper Theme Summary`
2. `Committee Assignment Rationale`
3. `Reviewer Assignment Sheet`
4. `Reviewer 1 Detailed Review`
5. `Reviewer 2 Detailed Review`
6. `Reviewer 3 Detailed Review`
7. `Reviewer 4 Detailed Review`
8. `Reviewer 5 Detailed Review`
9. `AE Meta-Review`

The `Reviewer Assignment Sheet` section should list all five reviewer profiles and review priorities before the detailed reviews begin.

The AE section should contain:

- final score
- final written judgment
- reviewer quality audit for reviewers 1 through 5

## Revision Loop

The existing revision loop should be preserved but adapted to the committee structure.

When the user brings back a revised draft:

- compare against prior reviewer concerns
- mark each major concern as `resolved`, `partially resolved`, or `unresolved`
- preserve reviewer identity when possible
- allow the AE to state whether the revision changed the overall outcome materially

The revision pass does not need to regenerate an entirely new committee if the same review package is still the right reference point. It may reuse the prior five-reviewer framing unless the paper changed scope substantially.

## Required Skill File Changes

### `SKILL.md`

Replace the current single mixed-mode workflow with the staged committee workflow. The description should be rewritten to emphasize the triggering condition rather than summarize the process in too much detail.

### `references/reviewer-modes.md`

Replace the current `top-conference reviewer + strict technical reviewer` framing with a reviewer construction reference that distinguishes:

- broad-field reviewer expectations
- niche-field reviewer expectations
- AE expectations
- independence and anti-contamination rules

### `assets/review-input-template.md`

Keep the current paper input structure, but add optional fields for:

- target venue or review context
- why the author thinks this paper may be misread
- whether the user wants extra focus on positioning, experiments, or clarity

### `agents/openai.yaml`

Update the prompt wording so the user-facing description matches the new committee-style simulation rather than the old single-reviewer behavior.

## Verification Plan

The skill update should be verified with at least one paper-shaped pressure scenario.

Verification goals:

- confirm the workflow starts with topic triage rather than immediate criticism
- confirm it creates `3 broad + 2 niche` reviewer assignments
- confirm each reviewer produces a differentiated review and score
- confirm the AE reads the paper plus all five reviews
- confirm the AE audits reviewer objectivity rather than only summarizing content
- confirm fallback instructions remain coherent in a single-session environment

## Resolved Design Decisions

The final design assumes:

- reviewer identities are generated dynamically from the paper topic
- AE sees both the original paper and all five reviews
- isolated agents or fresh sessions are preferred, but single-session fallback is allowed
