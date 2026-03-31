# ArXiv Research Scout Skill Suite Design

Status: Draft for review
Date: 2026-03-31
Owner: Codex + user

## 1. Summary

This document specifies a modular skill suite for continuously scouting new arXiv papers, extracting their core research problems and solutions, and producing reports that help a single researcher browse, shortlist, and revisit promising ideas. The system is intended to support a recurring workflow rather than a one-off search. It should function as an always-on research intake pipeline with explicit human review loops.

The design prioritizes four properties:

1. Accuracy over coverage when summarizing papers
2. Persistent user-specific research interest modeling
3. Daily operational usefulness with low manual friction
4. Explicit uncertainty handling instead of overconfident analysis

The first production milestone should support a single user, arXiv as the only source, a daily report cadence, and manual triggering. Later milestones may extend the suite to deeper scoring, commenting, and idea expansion.

## 2. Problem Statement

There is substantial value in discovering research problems early, even when the current paper's solution is weak, incremental, or poorly executed. In many cases, the most useful signal is not whether a paper is excellent, but whether it reveals:

- a problem the researcher had not been tracking,
- a potentially important problem with an unsatisfying solution,
- a paper whose framing is weak but whose underlying opportunity is real,
- a direction worth revisiting before it matures into a polished conference publication.

The system should therefore not behave like a generic literature summarizer. It should behave like a research scout:

- continuously watch a relevant frontier,
- filter it using a persistent but not overly rigid interest profile,
- extract problem and solution accurately,
- flag uncertainty and potential weaknesses,
- surface a compact report that supports human judgment and idea selection.

## 3. Goals

- Maintain a persistent, continuously updateable single-user research interest profile
- Use the profile to guide arXiv paper intake without making the filter so strict that adjacent opportunities are missed
- Run in two modes:
  - Daily mode: generate a report every day
  - Manual mode: allow user-triggered reruns with temporary overrides
- Normalize and deduplicate incoming papers before deeper analysis
- Produce structured paper summaries focused on problem, solution, contribution, limitations, and relevance
- Preserve evidence awareness and confidence labeling in every analysis artifact
- Produce reports that support fast browsing, triage, and shortlist creation
- Keep outputs useful enough that the user can directly review them rather than rewrite them from scratch

## 4. Non-Goals for the First Milestone

- Supporting multiple users or team-wide shared profiles
- Supporting non-arXiv sources as first-class inputs
- Building a full autonomous idea-generation or research-planning agent
- Providing citation-perfect peer review quality for every paper without human oversight
- Fully automating publishability judgments
- Replacing human reading for borderline, ambiguous, or low-confidence papers

These may be addressed later, but they should not complicate the first design.

## 5. Design Principles

### 5.1 Scientific Rigor

The system should separate extracted claims from inferred judgments. Whenever possible, it should distinguish:

- what the paper explicitly states,
- what the system infers from the paper,
- what remains uncertain.

This distinction is essential for preventing fluent but unsupported summaries.

### 5.2 Accuracy First

The system should prefer abstention or lower confidence over polished but unreliable output. A shorter correct summary is better than a confident but distorted summary.

### 5.3 Persistent but Permeable Interest Modeling

The research profile should guide relevance ranking, not act as a brittle hard filter. The system should preserve a controlled amount of exploratory breadth so that adjacent but worthwhile papers are not discarded too early.

### 5.4 Human-in-the-Loop by Design

The pipeline should accelerate research review, not hide uncertainty. Human feedback should be cheap to provide and should improve future runs.

### 5.5 Artifact Transparency

The system should store intermediate artifacts in inspectable files so the user can audit how a report was produced. The first version should prefer transparent file-based state over opaque internal state or database-only designs.

## 6. Scope and Constraints

### 6.1 User Model

- Single user only
- One persistent long-term profile
- The profile evolves over time through explicit conversation and feedback

### 6.2 Source Scope

- Source: arXiv only
- The system may later add conference proceedings and published papers, but that is out of scope for the first milestone

### 6.3 Report Cadence

- Daily automated report
- Manual report generation with temporary overrides

### 6.4 Output Bias

The system should be optimized for identifying:

- promising problems,
- weak or incomplete solutions to good problems,
- papers worth deeper follow-up,
- papers safe to skip,
- papers requiring manual verification because the analysis is uncertain.

## 7. System Architecture

The suite should be decomposed into six skills with explicit contracts. These skills are logically separate even if only a subset is implemented in the first milestone.

### 7.1 `research-interest-profile`

Purpose:
Maintain and refine the user's persistent research interest profile through dialogue.

Responsibilities:

- Elicit stable interests, recent shifts, exclusions, and adjacent exploratory directions
- Update the long-lived profile artifact
- Preserve both focus and exploratory breadth
- Incorporate explicit user feedback after reports

### 7.2 `paper-intake-and-normalize`

Purpose:
Fetch candidate papers from arXiv and convert them into a normalized candidate pool.

Responsibilities:

- Query arXiv using the active profile and operational parameters
- Normalize metadata
- Deduplicate papers
- Record provenance and retrieval timestamps
- Produce a stable registry for downstream analysis

### 7.3 `problem-solution-extractor`

Purpose:
Transform a candidate paper into a structured analysis focused on the paper's core research problem and proposed solution.

Responsibilities:

- Extract a concise summary of the paper
- Identify the main problem and proposed solution
- Record contribution claims and likely limitations
- Note evidence basis for key judgments
- Label confidence

### 7.4 `paper-ranker-and-commenter`

Purpose:
Evaluate analyzed papers and attach concise quality judgments and comments.

Responsibilities:

- Score novelty, problem importance, solution quality, and credibility
- Write review-style comments
- Flag papers whose problem is stronger than their solution
- Route promising cases toward deeper exploration

This skill is part of the overall suite but can be deferred until the core pipeline is stable.

### 7.5 `idea-gap-explorer`

Purpose:
Generate follow-up directions for papers whose problems appear interesting but whose current solutions appear weak, incomplete, or improvable.

Responsibilities:

- Identify likely gaps in the current solution
- Suggest alternative directions
- Distinguish easy extensions from more ambitious ideas
- Produce question prompts for human follow-up

This skill should not be part of the default daily pipeline in the first milestone.

### 7.6 `report-composer`

Purpose:
Assemble intermediate artifacts into actionable daily or manual research reports.

Responsibilities:

- Produce browsing-oriented reports rather than narrative essays
- Surface top papers, skip candidates, uncertain cases, and follow-up candidates
- Preserve traceability from report entries back to per-paper artifacts

## 8. Shared Workspace and File Contracts

The first version should use a transparent file-based workspace.

Recommended structure:

```text
research-workspace/
├── profile/
│   └── interest-profile.md
├── papers/
│   ├── registry.jsonl
│   └── <arxiv-id>/
│       ├── metadata.json
│       ├── problem-solution.md
│       ├── review.md
│       └── ideas.md
└── reports/
    ├── daily/
    └── manual/
```

### 8.1 Core Contract Rules

- `interest-profile.md` is the only long-lived user preference artifact
- `registry.jsonl` is the canonical candidate paper registry
- Each paper gets a directory keyed by an arXiv identifier or other stable normalized identifier
- Downstream artifacts should not overwrite upstream artifacts
- Re-running analysis should be idempotent when inputs have not changed
- Reports should be reproducible from stored artifacts

## 9. Interest Profile Specification

The interest profile is central to the system and should not be reduced to a flat keyword list.

It should contain at least the following sections:

### 9.1 Core Interests

Stable themes the user actively wants tracked.

### 9.2 Soft Boundaries

Adjacent or exploratory areas that are not central but should still be considered. This section operationalizes the user's requirement that the scope should not be too rigid.

### 9.3 Exclusions

Areas currently considered low value, irrelevant, or overly noisy.

### 9.4 Current-Phase Bias

A declaration of what the user currently values more, such as:

- important new problems,
- weak solutions to strong problems,
- practical system ideas,
- theory-heavy work,
- fast-follow opportunities,
- conference-ready depth versus exploratory inspiration.

### 9.5 Evaluation Heuristics

Short statements describing what the user tends to reward or penalize. Example dimensions include:

- problem importance,
- clarity of formulation,
- simplicity of solution,
- experimental credibility,
- systems practicality,
- likelihood that the idea space remains under-explored.

### 9.6 Open Questions

A running list of partly formed interests or unresolved curiosities. This section keeps the profile adaptive rather than prematurely fixed.

## 10. Intake and Normalization Workflow

The intake skill should perform the following steps:

1. Read the latest interest profile
2. Translate the profile into retrieval criteria
3. Fetch candidate papers from arXiv for the active window
4. Normalize metadata fields
5. Deduplicate against prior runs
6. Assign a preliminary relevance label
7. Write results into `registry.jsonl` and per-paper `metadata.json`

### 10.1 Deduplication Rules

The system should treat duplicate detection as a first-class concern. At minimum it should account for:

- exact arXiv identifier matches,
- repeated ingestion from overlapping time windows,
- version updates of the same arXiv paper,
- repeated manual reruns.

### 10.2 Preliminary Relevance Bands

To avoid premature over-filtering, the intake stage should assign one of three coarse bands:

- high match,
- adjacent but potentially interesting,
- low priority.

Low-priority papers may be omitted from default extraction, but the system should support retaining them in the registry for auditability or later review.

## 11. Problem-Solution Extraction Protocol

This skill is the accuracy-critical center of the first milestone.

For each paper, it should produce a structured artifact with at least:

- one-sentence summary,
- research problem,
- proposed solution,
- claimed contributions,
- likely limitations,
- evidence basis,
- confidence,
- relevance to the active interest profile.

### 11.1 Evidence Basis

The artifact should record where the interpretation mainly came from, for example:

- abstract,
- introduction,
- method section,
- experiments,
- conclusion.

This does not require long quotations. It requires provenance-aware summarization.

### 11.2 Confidence Labels

Every extraction should include one of:

- high,
- medium,
- low.

Interpretation:

- `high`: the problem and solution are stated clearly and the analysis is well supported by the available text
- `medium`: the likely interpretation is coherent, but some ambiguity remains
- `low`: the problem or solution is unclear, underspecified, domain-specific, or likely to be misread without direct human inspection

### 11.3 Abstention Policy

When a paper cannot be summarized reliably, the system should not invent clarity. It should explicitly state that the analysis is uncertain and route the paper to manual review.

### 11.4 Extraction Discipline

The extractor should explicitly separate:

- author claims,
- system inference,
- critique or suspected weakness.

This reduces the risk of presenting speculation as fact.

## 12. Reporting Workflow

The system should support two operational modes.

### 12.1 Daily Mode

Default cadence:

- Run once per day
- Process newly retrieved arXiv papers within the active window
- Generate a concise report for review

Default report sections:

- top papers to read now,
- promising problems but weak or incomplete solutions,
- papers likely safe to skip,
- papers requiring manual verification,
- candidates for deeper follow-up.

### 12.2 Manual Mode

Manual mode should reuse the same pipeline with temporary parameter overrides such as:

- a longer time window,
- temporary topic emphasis,
- inclusion of more adjacent papers,
- re-analysis of specific papers,
- regeneration of a report from existing artifacts.

Manual mode should not introduce a separate logic path unless strictly necessary.

### 12.3 First-Milestone Prioritization Logic

The first milestone does not yet require a full scoring skill, but the report still needs to surface papers whose problems appear more promising than their current solutions. In Phase 1, this should be handled conservatively using extraction-time judgments and explicit uncertainty labels rather than pretending that a mature ranking model already exists.

The report composer may therefore use:

- relevance to the active profile,
- confidence of extraction,
- stated limitations,
- signs that the problem is meaningful even if the solution seems incomplete,
- explicit flags that a judgment is tentative rather than fully scored.

## 13. Quality and Reliability Requirements

This system is only useful if the user can trust the summaries enough to review them directly.

The following reliability requirements should therefore be treated as design constraints, not optional refinements.

### 13.1 Calibrated Confidence

The system should avoid uniformly confident outputs. Confidence should correlate with evidence quality and clarity of the paper.

### 13.2 Explicit Uncertainty Routing

Low-confidence papers should be placed into a separate report section instead of being mixed with reliable summaries.

### 13.3 Observation vs Inference Separation

Reports and per-paper artifacts should distinguish:

- extracted facts,
- analytical interpretation,
- speculative opportunity statements.

### 13.4 Conservative Defaults

If there is a tension between recall and precision in summary quality, the first milestone should favor precision in the report's top-ranked entries.

### 13.5 Auditability

A user should be able to move from a report entry back to the corresponding paper artifact and understand why the system made that judgment.

### 13.6 Controlled Opportunism

Because the system is intended to find opportunity, it should be allowed to surface papers that are imperfect but strategically interesting. However, it should do so explicitly. A paper should never be treated as a strong opportunity unless the artifact makes clear whether that conclusion comes from direct evidence, analytic inference, or speculative follow-up reasoning.

## 14. Human Feedback Loop

The user should be able to improve future runs with lightweight feedback. The system should support at least the following feedback types:

- increase attention to this topic,
- decrease attention to this topic,
- this summary was inaccurate,
- this paper is more relevant than the system thought,
- this paper is less relevant than the system thought,
- this paper deserves deeper idea exploration,
- future reports should be more specific on this dimension.

Feedback should update either:

- the long-term interest profile,
- per-paper artifacts,
- or future report ordering behavior.

## 15. Failure Modes and Edge Cases

The design should explicitly account for the following cases:

### 15.1 Profile Drift

The user's interests may shift over time. The profile skill should revise rather than merely append new interests, otherwise the profile will become bloated and non-discriminative.

### 15.2 Over-Filtering

If the system filters too aggressively, it may miss adjacent but important opportunities. Soft boundaries and adjacent-match bands are therefore mandatory.

### 15.3 Under-Filtering

If the system keeps too many papers, the user will stop reading reports. Report composition must therefore prioritize ranking and triage, even in the first milestone.

### 15.4 Ambiguous Papers

Some papers are poorly written, highly specialized, or difficult to parse from summary-level evidence. The system should route these to manual verification rather than forcing false clarity.

### 15.5 Incomplete Source Access

If only partial text is available or retrieval fails, the system should degrade gracefully and record reduced confidence.

### 15.6 Reprocessing and Idempotency

Daily and manual runs may overlap in time windows. The normalization layer should prevent artifact explosion, duplication, and silent inconsistency.

### 15.7 Excessive Novelty Bias

Not every valuable paper is highly novel. The system should not equate novelty with usefulness. The target is research opportunity detection, not novelty worship.

## 16. Evaluation Framework

The first milestone should be evaluated with lightweight but explicit quality checks. The goal is not benchmark perfection; the goal is to ensure the reports are accurate enough to be operationally useful.

### 16.1 Extraction Accuracy Audit

On a recurring sample of papers, the user should be able to inspect whether the extracted problem and solution are materially correct.

Suggested audit questions:

- Did the summary identify the actual primary problem?
- Did it correctly characterize the proposed solution?
- Did it avoid inventing claims not supported by the paper?
- Did it capture major limitations when they were visible?

### 16.2 Confidence Calibration Audit

Confidence should be meaningful rather than decorative.

Expected pattern:

- high-confidence summaries should rarely require major correction,
- low-confidence summaries should contain a visibly higher rate of ambiguity,
- uncertain papers should be routed away from the top trusted section of the report.

### 16.3 Top-of-Report Utility

The most important report slices should be judged by usefulness, not only formal correctness.

Suggested checks:

- Are the top papers genuinely worth reading more often than random intake items?
- Are skip recommendations usually safe?
- Are "promising problem, weak solution" cases worth human follow-up at a useful rate?

### 16.4 Review Burden

The report should compress the daily intake rather than shift equivalent work onto the user in a different format.

Suggested checks:

- Can the user review the top report sections quickly?
- Does the uncertain section remain bounded rather than exploding in size?
- Are reports concise enough to support sustained daily use?

## 17. Phased Delivery Plan

### Phase 1: Core Daily Scout

Implement:

- `research-interest-profile`
- `paper-intake-and-normalize`
- `problem-solution-extractor`
- `report-composer`

Expected outcome:

- a persistent profile,
- daily and manual arXiv intake,
- structured problem-solution artifacts,
- a report the user can browse directly.

### Phase 2: Ranking and Comments

Implement:

- `paper-ranker-and-commenter`

Expected outcome:

- more explicit prioritization,
- short review-style comments,
- better shortlist generation.

### Phase 3: Idea Expansion

Implement:

- `idea-gap-explorer`

Expected outcome:

- targeted ideation on papers whose problems matter more than their current solutions.

## 18. Acceptance Criteria for the First Milestone

The first milestone should be considered successful only if all of the following are true:

- A single user can maintain a persistent interest profile over time
- The system can run in both daily mode and manual mode
- The system ingests and deduplicates arXiv papers into a stable registry
- Each analyzed paper includes problem, solution, limitations, evidence basis, and confidence
- Reports clearly separate reliable cases from uncertain ones
- Reports are concise enough to browse quickly
- The user can identify promising problems and likely weak-solution papers without redoing the entire analysis manually

## 19. Recommended Next Step

After this design is reviewed and approved, the next artifact should be an implementation plan that decomposes Phase 1 into concrete tasks, files, tests, and execution order.
