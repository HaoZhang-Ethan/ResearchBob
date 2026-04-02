from __future__ import annotations

from auto_research.automation import PipelineConfig, run_daily_pipeline
from auto_research.models import RegistryEntry
from auto_research.openai_client import OpenAIResponsesClient, SummaryArtifact


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

    def detailed_analyze_paper(self, *, profile, entry, pdf_text):
        return {
            "one_paragraph_summary": "Detailed summary.",
            "problem": "Detailed problem.",
            "solution": "Detailed solution.",
            "key_mechanism": "Detailed mechanism.",
            "assumptions": "Detailed assumptions.",
            "strengths": "Detailed strengths.",
            "weaknesses": "Detailed weaknesses.",
            "what_is_missing": "Detailed missing.",
            "why_it_matters": "Detailed relevance.",
            "follow_up_ideas": "Detailed follow-up.",
        }

    def summarize_daily_findings(self, *, profile, analyses, failed_items):
        return {
            "headline": "Interesting NPU compiler papers today.",
            "top_takeaways": ["Fusion and scheduling remain tightly coupled."],
            "good_problem_weak_solution": ["Some papers expose good operator problems."],
            "worth_further_thought": ["Consider a schedule-aware fusion cost model."],
            "recurring_themes": ["Operator fusion and scheduling co-dependence."],
            "failed_or_retry": failed_items,
        }

    def update_longterm_findings(self, *, profile, previous_summary, analyses, daily_summary):
        return "# Rolling Themes\n\n- Operator fusion remains central.\n"


def test_openai_client_uses_env_base_url(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://example.test:8080")

    client = OpenAIResponsesClient(client=object())

    assert client._base_url == "http://example.test:8080/responses"


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
    monkeypatch.setattr(
        "auto_research.automation.download_pdf",
        lambda **kwargs: kwargs["destination"].write_bytes(b"%PDF-1.4\nExample text\n"),
    )
    monkeypatch.setattr(
        "auto_research.automation.build_detailed_analysis",
        lambda **kwargs: (
            "Example extracted PDF text",
            {
                "one_paragraph_summary": "Detailed summary.",
                "problem": "Detailed problem.",
                "solution": "Detailed solution.",
                "key_mechanism": "Detailed mechanism.",
                "assumptions": "Detailed assumptions.",
                "strengths": "Detailed strengths.",
                "weaknesses": "Detailed weaknesses.",
                "what_is_missing": "Detailed missing.",
                "why_it_matters": "Detailed relevance.",
                "follow_up_ideas": "Detailed follow-up.",
            },
        ),
    )

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
    detailed_path = workspace / "papers" / "2603.23566" / "detailed-analysis.md"
    state_path = workspace / "papers" / "2603.23566" / "state.json"
    assert artifact_path.exists()
    assert detailed_path.exists()
    assert state_path.exists()
    assert result.report_path == workspace / "reports" / "daily" / "2026-04-02.md"
    assert result.daily_summary_path == workspace / "reports" / "daily" / "2026-04-02-summary.md"
    assert result.bundle_path == workspace / "reports" / "daily" / "2026-04-02-bundle.json"
    assert result.longterm_summary_path == workspace / "reports" / "longterm" / "longterm-summary.md"
    assert result.ris_path == workspace / "exports" / "zotero" / "2026-04-02.ris"
    assert result.history_path == workspace / "pipeline" / "run-history.jsonl"
    ris_text = result.ris_path.read_text(encoding="utf-8")
    assert "TY  - UNPB" in ris_text
    assert "AscendOptimizer" in ris_text
    assert result.daily_summary_path.exists()
    assert result.bundle_path.exists()
    assert result.history_path.exists()
    assert "Interesting NPU compiler papers today." in result.daily_summary_path.read_text(encoding="utf-8")
    assert "Recurring Themes" in result.daily_summary_path.read_text(encoding="utf-8")
    assert "Rolling Themes" in result.longterm_summary_path.read_text(encoding="utf-8")
    assert "2603.23566v1" in result.bundle_path.read_text(encoding="utf-8")
    assert "selected_count" in result.history_path.read_text(encoding="utf-8")


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
    monkeypatch.setattr(
        "auto_research.automation.download_pdf",
        lambda **kwargs: kwargs["destination"].write_bytes(b"%PDF-1.4\nExample text\n"),
    )
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


def test_run_daily_pipeline_backfills_manual_pdf(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    paper_dir = workspace / "papers" / "2603.23566"
    paper_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = paper_dir / "source.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nManual text\n")
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
    monkeypatch.setattr(
        "auto_research.automation.download_pdf",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("download should not be called")),
    )
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

    assert (paper_dir / "detailed-analysis.md").exists()
    assert result.longterm_summary_path.exists()
