from __future__ import annotations

from auto_research.automation import PipelineConfig, run_daily_pipeline
from auto_research.models import RegistryEntry
from auto_research.openai_client import SummaryArtifact


class FakeLLMClient:
    def rank_candidates(self, *, profile, candidates, top_k):
        return [
            type("Ranked", (), {"paper_id": candidates[0].arxiv_id, "priority_score": 90, "reason": "best match"})
        ]

    def summarize_paper(self, *, profile, entry):
        return SummaryArtifact(
            paper_id=entry.arxiv_id,
            title=entry.title,
            confidence="medium",
            relevance_band=entry.relevance_band,
            opportunity_label="read-now",
            one_sentence_summary="One sentence.",
            problem="Problem.",
            proposed_solution="Solution.",
            claimed_contributions=["Contribution"],
            evidence_basis=["Abstract"],
            limitations=["Limitation"],
            relevance_to_profile="Relevant.",
            analyst_notes="Worth reading.",
        )


def test_run_daily_pipeline_writes_report_and_ris(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    (workspace / "profile").mkdir(parents=True, exist_ok=True)
    (workspace / "profile" / "interest-profile.md").write_text(
        """# Research Interest Profile

## Core Interests
- npu compiler

## Soft Boundaries
- operator fusion

## Exclusions
- irrelevant

## Current-Phase Bias
- good problems with weak solutions

## Evaluation Heuristics
- prefer hardware-aware work

## Open Questions
- how to choose fusion boundaries
""",
        encoding="utf-8",
    )

    entry = RegistryEntry(
        arxiv_id="2603.23566v1",
        title="AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization",
        summary="Operator optimization on Ascend NPUs.",
        pdf_url="https://arxiv.org/pdf/2603.23566v1",
        published_at="2026-03-24T08:54:53Z",
        updated_at="2026-03-24T08:54:53Z",
        relevance_band="high-match",
        source="arxiv",
    )

    monkeypatch.setattr("auto_research.automation.run_intake", lambda **kwargs: [entry])

    result = run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-02",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    artifact_path = workspace / "papers" / "2603.23566" / "problem-solution.md"
    assert artifact_path.exists()
    assert result.report_path == workspace / "reports" / "daily" / "2026-04-02.md"
    assert result.ris_path == workspace / "exports" / "zotero" / "2026-04-02.ris"
    ris_text = result.ris_path.read_text(encoding="utf-8")
    assert "TY  - UNPB" in ris_text
    assert "AscendOptimizer" in ris_text


def test_run_daily_pipeline_respects_existing_summary(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    stable_dir = workspace / "papers" / "2603.23566"
    stable_dir.mkdir(parents=True, exist_ok=True)
    (workspace / "profile").mkdir(parents=True, exist_ok=True)
    (workspace / "profile" / "interest-profile.md").write_text(
        """# Research Interest Profile

## Core Interests
- npu compiler

## Soft Boundaries
- operator fusion

## Exclusions
- irrelevant

## Current-Phase Bias
- good problems with weak solutions

## Evaluation Heuristics
- prefer hardware-aware work

## Open Questions
- how to choose fusion boundaries
""",
        encoding="utf-8",
    )

    existing = stable_dir / "problem-solution.md"
    existing.write_text(
        """---
paper_id: "2603.23566v1"
title: "Existing"
confidence: "medium"
relevance_band: "high-match"
opportunity_label: "read-now"
---

# One-Sentence Summary
Existing

# Problem
Existing

# Proposed Solution
Existing

# Claimed Contributions
- Existing

# Evidence Basis
- Abstract

# Limitations
- Existing

# Relevance to Profile
Existing

# Analyst Notes
Existing
""",
        encoding="utf-8",
    )

    entry = RegistryEntry(
        arxiv_id="2603.23566v1",
        title="AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization",
        summary="Operator optimization on Ascend NPUs.",
        pdf_url="https://arxiv.org/pdf/2603.23566v1",
        published_at="2026-03-24T08:54:53Z",
        updated_at="2026-03-24T08:54:53Z",
        relevance_band="high-match",
        source="arxiv",
    )

    monkeypatch.setattr("auto_research.automation.run_intake", lambda **kwargs: [entry])

    result = run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-02",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    assert existing.read_text(encoding="utf-8").startswith("---\npaper_id: \"2603.23566v1\"")
    assert result.report_path.exists()
