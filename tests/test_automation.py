from __future__ import annotations

import json
from pathlib import Path

import pytest

from auto_research.automation import PipelineConfig, finalize_github, run_daily_pipeline
from auto_research.models import RegistryEntry
from auto_research.openai_client import IssueProfileArtifacts, OpenAIResponsesClient, SummaryArtifact
from auto_research.retrieval import RetrievedCandidate
from auto_research.search_profile import SearchProfile, write_search_profile
from auto_research.workspace import ensure_direction_workspace, ensure_workspace


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

    def build_issue_profiles(self, *, direction: str, issue_texts: list[str]) -> IssueProfileArtifacts:
        del issue_texts
        profile = SearchProfile(
            direction=direction,
            canonical_topic="llm agents",
            aliases=["agent systems"],
            related_terms=["orchestration"],
            exclude_terms=["pure benchmark"],
            preferred_problem_types=["system design"],
            preferred_system_axes=["tool use"],
            retrieval_hints=["prefer recent papers"],
            seed_queries=["llm agents system design"],
            source_preferences=["arxiv"],
        )
        return IssueProfileArtifacts(
            interest_profile_markdown=(
                "# Research Interest Profile\n\n"
                "> Auto-generated from GitHub issue intake.\n\n"
                "## Core Interests\n- llm agents\n\n"
                "## Soft Boundaries\n- orchestration\n\n"
                "## Exclusions\n- pure benchmark papers\n\n"
                "## Current-Phase Bias\n- strong system design\n\n"
                "## Evaluation Heuristics\n- prefer recent papers\n\n"
                "## Open Questions\n- how should agent memory be structured?\n"
            ),
            search_profile=profile,
        )

    def retrieve_web_candidates(self, *, search_profile: SearchProfile, limit: int) -> list[dict[str, object]]:
        del search_profile, limit
        return []


def test_openai_client_uses_env_base_url(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://example.test:8080")

    client = OpenAIResponsesClient(client=object())

    assert client._base_url == "http://example.test:8080/responses"


def test_run_daily_pipeline_writes_outputs_under_direction_workspace(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
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
            direction="llm-agents",
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    assert result.report_path == direction_root / "reports" / "daily" / "2026-04-09.md"
    assert result.ris_path == direction_root / "exports" / "zotero" / "2026-04-09.ris"
    assert result.history_path == direction_root / "pipeline" / "run-history.jsonl"

    # Regression: pipeline helpers may call ensure_workspace(execution_workspace). That must
    # not create nested shared-workspace roots inside the direction workspace.
    assert not (direction_root / "issue-intake").exists()
    assert not (direction_root / "directions").exists()


def test_run_daily_pipeline_canonicalizes_direction_label(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
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
            direction="LLM Agents",
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    assert result.report_path == direction_root / "reports" / "daily" / "2026-04-09.md"
    assert not (workspace / "directions" / "LLM Agents").exists()


def test_manual_pdf_upload_does_not_resume_metadata_only_candidate(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
""",
        encoding="utf-8",
    )

    selected_candidate = RetrievedCandidate(
        paper_id="2603.23566v1",
        title="Selected Paper",
        summary="Selected summary.",
        pdf_url="https://example.test/selected.pdf",
        landing_page_url="https://example.test/selected",
        source_family="arxiv",
        discovery_sources=["arxiv_api"],
    )
    metadata_only_candidate = RetrievedCandidate(
        paper_id="2603.99999v1",
        title="Metadata Only",
        summary="No PDF URL, should not resume unless previously queued.",
        pdf_url="",
        landing_page_url="https://example.test/metadata-only",
        source_family="web",
        discovery_sources=["agent_web"],
    )

    class PicksSelectedFirst(FakeLLMClient):
        def rank_candidates(self, *, profile, candidates, top_k):
            target = next(item for item in candidates if item.arxiv_id == selected_candidate.paper_id)
            return [type("Ranked", (), {"paper_id": target.arxiv_id, "priority_score": 90, "reason": "best"})]

    monkeypatch.setattr(
        "auto_research.automation.run_hybrid_retrieval",
        lambda **kwargs: [selected_candidate, metadata_only_candidate],
    )
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

    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            top_k=1,
            prefilter_limit=10,
            max_results=10,
            label="2026-04-09",
        ),
        llm_client=PicksSelectedFirst(),
    )

    # Operator manually provides a PDF for a paper that was never selected/queued for analysis retry.
    stable_id = "2603.99999"
    (direction_root / "papers" / stable_id / "source.pdf").parent.mkdir(parents=True, exist_ok=True)
    (direction_root / "papers" / stable_id / "source.pdf").write_bytes(b"%PDF-1.4\nmanual\n")
    assert not (direction_root / "papers" / stable_id / "state.json").exists()

    monkeypatch.setattr(
        "auto_research.automation.run_hybrid_retrieval",
        lambda **kwargs: [selected_candidate],
    )
    result = run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            top_k=1,
            prefilter_limit=10,
            max_results=10,
            label="2026-04-10",
        ),
        llm_client=PicksSelectedFirst(),
    )

    # Regression: manual PDFs should only resume papers that were previously queued (state.json exists in retry state).
    assert [entry.arxiv_id for entry in result.selected_entries] == [selected_candidate.paper_id]


def test_run_daily_pipeline_synthesizes_issue_profiles_and_attempts_hybrid_retrieval(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    # Only issue-intake input exists; direction-local profile/search-profile should be synthesized.
    issue_summary = workspace / "issue-intake" / "llm-agents" / "tester" / "summary.md"
    issue_summary.parent.mkdir(parents=True, exist_ok=True)
    issue_summary.write_text("# Issue Intake Summary\n\n- Prefer agent systems papers.\n", encoding="utf-8")

    direction_root = workspace / "directions" / "llm-agents"
    interest_path = direction_root / "profile" / "interest-profile.md"
    search_path = direction_root / "profile" / "search-profile.json"
    assert not interest_path.exists()
    assert not search_path.exists()

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

    class IssueAwareClient(FakeLLMClient):
        def __init__(self) -> None:
            self.web_calls = 0
            self.issue_profile_calls = 0

        def build_issue_profiles(self, *, direction: str, issue_texts: list[str]) -> IssueProfileArtifacts:
            self.issue_profile_calls += 1
            profile = SearchProfile(
                direction=direction,
                canonical_topic="llm agents",
                aliases=["agent systems"],
                related_terms=["tool use"],
                exclude_terms=["pure benchmark"],
                preferred_problem_types=["system design"],
                preferred_system_axes=["orchestration"],
                retrieval_hints=["prefer recent systems papers"],
                seed_queries=["llm agents system design"],
                source_preferences=["arxiv", "semantic scholar"],
            )
            return IssueProfileArtifacts(
                interest_profile_markdown=(
                    "# Research Interest Profile\n\n## Core Interests\n- llm agents\n\n## Soft Boundaries\n- orchestration\n\n"
                    "## Exclusions\n- pure benchmark papers\n\n## Current-Phase Bias\n- strong system design\n\n"
                    "## Evaluation Heuristics\n- prefer recent papers\n\n## Open Questions\n- how should agent memory be structured?\n"
                ),
                search_profile=profile,
            )

        def retrieve_web_candidates(self, *, search_profile: SearchProfile, limit: int) -> list[dict[str, object]]:
            self.web_calls += 1
            return []

    client = IssueAwareClient()
    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=client,
    )

    assert interest_path.exists()
    assert search_path.exists()
    assert client.issue_profile_calls == 1
    assert client.web_calls == 1


def test_run_daily_pipeline_preserves_existing_interest_profile_when_only_search_profile_missing(
    tmp_path, monkeypatch
) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    issue_summary = workspace / "issue-intake" / "llm-agents" / "tester" / "summary.md"
    issue_summary.parent.mkdir(parents=True, exist_ok=True)
    issue_summary.write_text("# Issue Intake Summary\n\n- Prefer agent systems papers.\n", encoding="utf-8")

    direction_root = workspace / "directions" / "llm-agents"
    interest_path = direction_root / "profile" / "interest-profile.md"
    search_path = direction_root / "profile" / "search-profile.json"
    interest_path.parent.mkdir(parents=True, exist_ok=True)
    original_interest = (
        "# Research Interest Profile\n\n"
        "## Core Interests\n- llm agents (SENTINEL)\n\n"
        "## Soft Boundaries\n- orchestration\n\n"
        "## Exclusions\n- pure benchmark papers\n\n"
        "## Current-Phase Bias\n- strong system design\n\n"
        "## Evaluation Heuristics\n- prefer recent papers\n\n"
        "## Open Questions\n- how should agent memory be structured?\n"
    )
    interest_path.write_text(original_interest, encoding="utf-8")
    assert not search_path.exists()

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

    class TracksIssueProfiles(FakeLLMClient):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def build_issue_profiles(self, *, direction: str, issue_texts: list[str]) -> IssueProfileArtifacts:
            self.calls += 1
            return super().build_issue_profiles(direction=direction, issue_texts=issue_texts)

    llm_client = TracksIssueProfiles()
    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=llm_client,
    )

    assert search_path.exists()
    assert interest_path.read_text(encoding="utf-8") == original_interest
    assert llm_client.calls == 1


def test_run_daily_pipeline_resumed_papers_preserve_metadata_from_first_run(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
""",
        encoding="utf-8",
    )

    arxiv_entry = RegistryEntry(
        arxiv_id="2603.23566v1",
        title="AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization",
        summary="Operator optimization on Ascend NPUs.",
        pdf_url="",
        published_at="2026-03-24T08:54:53Z",
        updated_at="2026-03-25T08:54:53Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    candidate = RetrievedCandidate(
        paper_id="2603.23566v1",
        title=arxiv_entry.title,
        summary=arxiv_entry.summary,
        pdf_url="",
        landing_page_url="https://arxiv.org/abs/2603.23566v1",
        source_family="arxiv",
        discovery_sources=["arxiv_api"],
    )

    monkeypatch.setattr(
        "auto_research.automation.run_hybrid_retrieval",
        lambda **kwargs: type(
            "HybridResult",
            (),
            {"candidates": [candidate], "arxiv_entries": [arxiv_entry]},
        )(),
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

    llm_client = FakeLLMClient()
    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            top_k=1,
            prefilter_limit=10,
            max_results=10,
            label="2026-04-09",
        ),
        llm_client=llm_client,
    )

    stable_id = "2603.23566"
    paper_dir = direction_root / "papers" / stable_id
    assert (paper_dir / "state.json").exists()
    assert (paper_dir / "metadata.json").exists()

    # Operator provides the missing PDF.
    (paper_dir / "source.pdf").write_bytes(b"%PDF-1.4\nmanual\n")

    monkeypatch.setattr("auto_research.automation.run_hybrid_retrieval", lambda **kwargs: [])

    result = run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            label="2026-04-10",
        ),
        llm_client=llm_client,
    )

    resumed = next(entry for entry in result.selected_entries if entry.arxiv_id == arxiv_entry.arxiv_id)
    assert resumed.summary == arxiv_entry.summary
    assert resumed.published_at == arxiv_entry.published_at
    assert resumed.updated_at == arxiv_entry.updated_at
    assert resumed.relevance_band == arxiv_entry.relevance_band
    assert resumed.source == arxiv_entry.source


def test_run_daily_pipeline_with_explicit_profile_path_does_not_synthesize_issue_profiles_or_finalize(
    tmp_path, monkeypatch
) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    # Issue-intake exists for the direction, but this run uses an explicit override profile path.
    issue_summary = workspace / "issue-intake" / "llm-agents" / "tester" / "summary.md"
    issue_summary.parent.mkdir(parents=True, exist_ok=True)
    issue_summary.write_text("# Issue Intake Summary\n\n- Prefer agent systems papers.\n", encoding="utf-8")

    override_profile = tmp_path / "override-interest-profile.md"
    override_profile.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
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

    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            profile_path=override_profile,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    direction_root = workspace / "directions" / "llm-agents"
    assert not (direction_root / "profile" / "interest-profile.md").exists()
    assert not (direction_root / "profile" / "search-profile.json").exists()
    assert not (direction_root / "pipeline" / "github-finalize.json").exists()
def test_run_daily_pipeline_infers_direction_from_single_direction_profile(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
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
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    assert result.report_path == direction_root / "reports" / "daily" / "2026-04-09.md"
    assert result.ris_path == direction_root / "exports" / "zotero" / "2026-04-09.ris"
    assert result.history_path == direction_root / "pipeline" / "run-history.jsonl"


def test_run_daily_pipeline_infers_direction_from_profile_path(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
""",
        encoding="utf-8",
    )
    other_profile = workspace / "directions" / "robotics" / "profile" / "interest-profile.md"
    other_profile.parent.mkdir(parents=True, exist_ok=True)
    other_profile.write_text(profile_path.read_text(encoding="utf-8"), encoding="utf-8")
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
            profile_path=profile_path,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    assert result.report_path == direction_root / "reports" / "daily" / "2026-04-09.md"


def test_run_daily_pipeline_infers_direction_from_cli_relative_profile_path(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
""",
        encoding="utf-8",
    )
    other_profile = workspace / "directions" / "robotics" / "profile" / "interest-profile.md"
    other_profile.parent.mkdir(parents=True, exist_ok=True)
    other_profile.write_text(profile_path.read_text(encoding="utf-8"), encoding="utf-8")

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

    # CLI invocations often pass paths like `research-workspace/directions/<dir>/profile/interest-profile.md`.
    cli_style_path = Path("research-workspace/directions/llm-agents/profile/interest-profile.md")
    result = run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            profile_path=cli_style_path,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    assert result.report_path == direction_root / "reports" / "daily" / "2026-04-09.md"


def test_run_daily_pipeline_push_stages_direction_workspace(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction = "llm-agents"
    direction_root = workspace / "directions" / direction
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
""",
        encoding="utf-8",
    )

    staged: list[Path] = []

    monkeypatch.setattr("auto_research.automation.run_intake", lambda **kwargs: [])
    monkeypatch.setattr("auto_research.automation._stage_commit_push", lambda w, l: staged.append(w))

    run_daily_pipeline(
        PipelineConfig(workspace=workspace, direction=direction, label="2026-04-09", push=True),
        llm_client=FakeLLMClient(),
    )

    assert staged == [direction_root]


def test_run_daily_pipeline_requires_direction_when_multiple_issue_directions_exist(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    (workspace / "issue-intake" / "llm-agents" / "alice").mkdir(parents=True, exist_ok=True)
    (workspace / "issue-intake" / "llm-agents" / "alice" / "summary.md").write_text(
        "# Issue Intake Summary\n", encoding="utf-8"
    )
    (workspace / "issue-intake" / "robotics" / "bob").mkdir(parents=True, exist_ok=True)
    (workspace / "issue-intake" / "robotics" / "bob" / "summary.md").write_text(
        "# Issue Intake Summary\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="--direction"):
        run_daily_pipeline(PipelineConfig(workspace=workspace, label="2026-04-09"), llm_client=FakeLLMClient())


def test_run_daily_pipeline_writes_report_and_ris(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction = "npu-compiler"
    direction_root = workspace / "directions" / direction
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
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
            direction=direction,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-02",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    artifact_path = direction_root / "papers" / "2603.23566" / "problem-solution.md"
    detailed_path = direction_root / "papers" / "2603.23566" / "detailed-analysis.md"
    state_path = direction_root / "papers" / "2603.23566" / "state.json"
    assert artifact_path.exists()
    assert detailed_path.exists()
    assert state_path.exists()
    assert result.report_path == direction_root / "reports" / "daily" / "2026-04-02.md"
    assert result.daily_summary_path == direction_root / "reports" / "daily" / "2026-04-02-summary.md"
    assert result.bundle_path == direction_root / "reports" / "daily" / "2026-04-02-bundle.json"
    assert result.longterm_summary_path == direction_root / "reports" / "longterm" / "longterm-summary.md"
    assert result.ris_path == direction_root / "exports" / "zotero" / "2026-04-02.ris"
    assert result.history_path == direction_root / "pipeline" / "run-history.jsonl"
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
    ensure_workspace(workspace)
    direction = "npu-compiler"
    stable_dir = workspace / "directions" / direction / "papers" / "2603.23566"
    stable_dir.mkdir(parents=True, exist_ok=True)
    profile_path = workspace / "directions" / direction / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
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
            direction=direction,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-02",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )


def test_run_daily_pipeline_generates_profile_from_issue_intake(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction_root = workspace / "directions" / "llm-agents"
    summary_dir = workspace / "issue-intake" / "llm-agents" / "alice"
    (summary_dir / "requests").mkdir(parents=True, exist_ok=True)
    (summary_dir / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)

## Requirements
- prefer strong system design
- focus on memory and orchestration

## Constraints
- avoid pure benchmark papers

## Notes
- how should agent memory be structured?
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

    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-03",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    profile_path = direction_root / "profile" / "interest-profile.md"
    assert profile_path.exists()
    assert "Auto-generated from GitHub issue intake" in profile_path.read_text(encoding="utf-8")


def test_run_daily_pipeline_generates_profile_from_requested_direction_issue_intake(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    request_dir = workspace / "issue-intake" / "llm-agents" / "alice" / "requests"
    request_dir.mkdir(parents=True, exist_ok=True)
    (request_dir.parent / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)

## Requirements
- prefer strong system design
""",
        encoding="utf-8",
    )
    (workspace / "issue-intake" / "robotics" / "bob" / "requests").mkdir(parents=True, exist_ok=True)
    ((workspace / "issue-intake" / "robotics" / "bob") / "summary.md").write_text(
        """# Issue Intake Summary: robotics / bob

- Direction: `robotics`
- GitHub Username: `bob`
- Request Count: 1

## Active Issues
- #34: Track robot grasping papers (OPEN)
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

    run_daily_pipeline(
        PipelineConfig(workspace=workspace, direction="llm-agents", top_k=1, prefilter_limit=5, max_results=5, label="2026-04-09"),
        llm_client=FakeLLMClient(),
    )

    profile_path = workspace / "directions" / "llm-agents" / "profile" / "interest-profile.md"
    assert profile_path.exists()
    search_path = workspace / "directions" / "llm-agents" / "profile" / "search-profile.json"
    assert search_path.exists()
    assert json.loads(search_path.read_text(encoding="utf-8"))["direction"] == "llm-agents"
    assert not (workspace / "directions" / "robotics").exists()


def test_run_daily_pipeline_writes_pending_finalize_state(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    request_dir = workspace / "issue-intake" / "llm-agents" / "alice" / "requests"
    request_dir.mkdir(parents=True, exist_ok=True)
    (request_dir.parent / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)
""",
        encoding="utf-8",
    )
    (request_dir / "12.md").write_text(
        """---
issue_number: 12
title: "Track multi-agent papers"
state: "OPEN"
author_login: "alice"
direction: "llm-agents"
normalized_direction: "llm-agents"
created_at: "2026-04-03T10:00:00Z"
updated_at: "2026-04-03T11:00:00Z"
url: "https://github.com/example/research/issues/12"
---
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
    monkeypatch.setattr("auto_research.automation.discover_github_repo", lambda cwd=None: "example/research")
    monkeypatch.setattr("auto_research.automation.comment_on_issue", lambda **kwargs: None)
    monkeypatch.setattr("auto_research.automation.close_issue", lambda **kwargs: None)

    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-04",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    finalize_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    assert finalize_path.exists()


def test_run_daily_pipeline_without_fallback_skips_finalize_state(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction = "llm-agents"
    profile_path = workspace / "directions" / direction / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
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

    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction=direction,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-04",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    assert not (workspace / "directions" / direction / "pipeline" / "github-finalize.json").exists()


def test_finalize_github_runs_push_then_issue_updates(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_direction_workspace(workspace, "llm-agents")
    state_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    state_path.write_text(
        """{
  "label": "2026-04-04",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-04T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "auto_research.automation.subprocess.run",
        lambda cmd, cwd, check: calls.append(("push", cmd)) or None,
    )
    monkeypatch.setattr(
        "auto_research.automation.comment_on_issue",
        lambda *, repo, issue_number, body: calls.append(("comment", repo, issue_number, body)),
    )
    monkeypatch.setattr(
        "auto_research.automation.close_issue",
        lambda *, repo, issue_number: calls.append(("close", repo, issue_number)),
    )

    result = finalize_github(workspace, direction="llm-agents")

    assert result["status"] == "completed"
    assert calls[0] == ("push", ["git", "push"])
    assert calls[1][0] == "comment"
    assert calls[2] == ("close", "example/research", 12)


def test_finalize_github_reads_direction_local_state(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_direction_workspace(workspace, "llm-agents")
    state_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    state_path.write_text(
        """{
  "direction": "llm-agents",
  "label": "2026-04-09",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-09T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )
    calls = []

    monkeypatch.setattr("auto_research.automation.subprocess.run", lambda cmd, cwd, check: calls.append(("push", cmd)) or None)
    monkeypatch.setattr("auto_research.automation.comment_on_issue", lambda *, repo, issue_number, body: calls.append(("comment", repo, issue_number)))
    monkeypatch.setattr("auto_research.automation.close_issue", lambda *, repo, issue_number: calls.append(("close", repo, issue_number)))

    result = finalize_github(workspace, direction="llm-agents")

    assert result["status"] == "completed"
    assert calls[0] == ("push", ["git", "push"])
    assert calls[1] == ("comment", "example/research", 12)
    assert calls[2] == ("close", "example/research", 12)


def test_finalize_github_fails_when_state_missing(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    with pytest.raises(ValueError, match="No pending GitHub finalize work"):
        finalize_github(workspace, direction="llm-agents")


def test_finalize_github_missing_state_does_not_create_direction_tree(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    missing_dir = workspace / "directions" / "missing-dir"
    assert not missing_dir.exists()

    with pytest.raises(ValueError, match="No pending GitHub finalize work"):
        finalize_github(workspace, direction="missing-dir")

    assert not missing_dir.exists()


def test_finalize_github_rejects_traversal_direction(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    # If finalize_github naively accepts traversal-like directions, it could look up state outside
    # the intended `directions/<dir>/...` tree. Create a tempting state file at that escaped path.
    escape_dir = workspace / "escape"
    escape_dir.mkdir(parents=True, exist_ok=True)
    state_path = escape_dir / "pipeline" / "github-finalize.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        """{
  "direction": "escape",
  "label": "2026-04-09",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-09T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )

    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        "auto_research.automation.subprocess.run",
        lambda cmd, cwd, check, **kwargs: calls.append(("push", cmd)) or None,
    )
    monkeypatch.setattr(
        "auto_research.automation.comment_on_issue",
        lambda *, repo, issue_number, body: calls.append(("comment", repo, issue_number)),
    )
    monkeypatch.setattr(
        "auto_research.automation.close_issue",
        lambda *, repo, issue_number: calls.append(("close", repo, issue_number)),
    )

    with pytest.raises(ValueError, match="Invalid direction"):
        finalize_github(workspace, direction="../escape")

    assert calls == []


def test_finalize_github_rejects_symlinked_direction_root(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    # Create a real directory holding a pending finalize state...
    target = tmp_path / "target-direction"
    (target / "pipeline").mkdir(parents=True, exist_ok=True)
    (target / "pipeline" / "github-finalize.json").write_text(
        """{
  "direction": "llm-agents",
  "label": "2026-04-09",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-09T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )

    # ...but point `directions/llm-agents` at it via a symlink.
    symlink_root = workspace / "directions" / "llm-agents"
    symlink_root.symlink_to(target, target_is_directory=True)
    assert symlink_root.is_symlink()

    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        "auto_research.automation.subprocess.run",
        lambda cmd, cwd, check, **kwargs: calls.append(("push", cmd)) or None,
    )
    monkeypatch.setattr(
        "auto_research.automation.comment_on_issue",
        lambda *, repo, issue_number, body: calls.append(("comment", repo, issue_number)),
    )
    monkeypatch.setattr(
        "auto_research.automation.close_issue",
        lambda *, repo, issue_number: calls.append(("close", repo, issue_number)),
    )

    with pytest.raises(OSError, match="symlink"):
        finalize_github(workspace, direction="llm-agents")

    assert calls == []


def test_finalize_github_rejects_symlinked_pipeline_dir(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    direction_root = workspace / "directions" / "llm-agents"
    direction_root.mkdir(parents=True, exist_ok=True)

    target = tmp_path / "pipeline-target"
    (target / "pipeline").mkdir(parents=True, exist_ok=True)
    (target / "pipeline" / "github-finalize.json").write_text(
        """{
  "direction": "llm-agents",
  "label": "2026-04-09",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-09T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )

    pipeline_dir = direction_root / "pipeline"
    pipeline_dir.symlink_to(target / "pipeline", target_is_directory=True)
    assert pipeline_dir.is_symlink()

    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        "auto_research.automation.subprocess.run",
        lambda cmd, cwd, check, **kwargs: calls.append(("push", cmd)) or None,
    )
    monkeypatch.setattr(
        "auto_research.automation.comment_on_issue",
        lambda *, repo, issue_number, body: calls.append(("comment", repo, issue_number)),
    )
    monkeypatch.setattr(
        "auto_research.automation.close_issue",
        lambda *, repo, issue_number: calls.append(("close", repo, issue_number)),
    )

    with pytest.raises(OSError, match="symlink"):
        finalize_github(workspace, direction="llm-agents")

    assert calls == []


def test_finalize_github_skips_completed_state(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_direction_workspace(workspace, "llm-agents")
    state_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    state_path.write_text(
        """{
  "label": "2026-04-04",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "completed",
  "created_at": "2026-04-04T00:00:00Z",
  "finalized_at": "2026-04-04T01:00:00Z"
}
""",
        encoding="utf-8",
    )
    calls: list[str] = []

    monkeypatch.setattr(
        "auto_research.automation.subprocess.run",
        lambda **kwargs: calls.append("push") or None,
    )

    result = finalize_github(workspace, direction="llm-agents")

    assert result["status"] == "completed"
    assert calls == []


def test_finalize_github_push_failure_leaves_state_pending(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_direction_workspace(workspace, "llm-agents")
    state_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    state_path.write_text(
        """{
  "label": "2026-04-04",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-04T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )
    actions: list[str] = []

    def fail_push(cmd, cwd, check):
        actions.append("push")
        raise RuntimeError("push failed")

    monkeypatch.setattr("auto_research.automation.subprocess.run", fail_push)
    monkeypatch.setattr(
        "auto_research.automation.comment_on_issue",
        lambda **kwargs: actions.append("comment"),
    )
    monkeypatch.setattr(
        "auto_research.automation.close_issue",
        lambda **kwargs: actions.append("close"),
    )

    with pytest.raises(RuntimeError, match="push failed"):
        finalize_github(workspace, direction="llm-agents")

    state = state_path.read_text(encoding="utf-8")
    assert '"status": "pending"' in state
    assert actions == ["push"]


def test_run_daily_pipeline_writes_finalize_state_instead_of_closing_issues(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    request_dir = workspace / "issue-intake" / "llm-agents" / "alice" / "requests"
    request_dir.mkdir(parents=True, exist_ok=True)
    (request_dir.parent / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)

## Requirements
- prefer strong system design
""",
        encoding="utf-8",
    )
    (request_dir / "12.md").write_text(
        """---
issue_number: 12
title: "Track multi-agent papers"
state: "OPEN"
author_login: "alice"
direction: "llm-agents"
normalized_direction: "llm-agents"
created_at: "2026-04-03T10:00:00Z"
updated_at: "2026-04-03T11:00:00Z"
url: "https://github.com/example/research/issues/12"
---
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
    monkeypatch.setattr("auto_research.automation.discover_github_repo", lambda cwd=None: "example/research")

    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-03",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    state_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    assert state_path.exists()
    state = state_path.read_text(encoding="utf-8")
    assert '"repo": "example/research"' in state
    assert '"consumed_issue_numbers": [' in state
    assert '12' in state


def test_run_daily_pipeline_fails_when_profile_missing_and_no_issue_intake(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    with pytest.raises(ValueError, match="issue intake"):
        run_daily_pipeline(
            PipelineConfig(
                workspace=workspace,
                direction="llm-agents",
                top_k=1,
                prefilter_limit=5,
                max_results=5,
                label="2026-04-03",
                push=False,
            ),
            llm_client=FakeLLMClient(),
        )


def test_run_daily_pipeline_preserves_existing_profile(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction = "llm-agents"
    profile_path = workspace / "directions" / direction / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    valid_profile_text = """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
"""
    profile_path.write_text(valid_profile_text, encoding="utf-8")

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

    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction=direction,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-03",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    assert profile_path.read_text(encoding="utf-8") == valid_profile_text


def test_run_daily_pipeline_with_existing_profile_skips_finalize_state(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction = "llm-agents"
    profile_path = workspace / "directions" / direction / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
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
    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction=direction,
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-03",
            push=False,
        ),
        llm_client=FakeLLMClient(),
    )

    assert not (workspace / "directions" / direction / "pipeline" / "github-finalize.json").exists()


def test_finalize_github_tolerates_issue_comment_failure(tmp_path, monkeypatch, capsys) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_direction_workspace(workspace, "llm-agents")
    state_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    state_path.write_text(
        """{
  "label": "2026-04-04",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-04T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )
    closes: list[tuple[str, int]] = []

    monkeypatch.setattr("auto_research.automation.subprocess.run", lambda cmd, cwd, check: None)
    monkeypatch.setattr(
        "auto_research.automation.comment_on_issue",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("comment failed")),
    )
    monkeypatch.setattr(
        "auto_research.automation.close_issue",
        lambda *, repo, issue_number: closes.append((repo, issue_number)),
    )

    result = finalize_github(workspace, direction="llm-agents")

    captured = capsys.readouterr()
    assert result["status"] == "completed"
    assert closes == []
    assert "warning" in captured.err.lower()


def test_finalize_github_tolerates_issue_close_failure(tmp_path, monkeypatch, capsys) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_direction_workspace(workspace, "llm-agents")
    state_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    state_path.write_text(
        """{
  "label": "2026-04-04",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-04T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )
    comments: list[tuple[str, int, str]] = []

    monkeypatch.setattr("auto_research.automation.subprocess.run", lambda cmd, cwd, check: None)
    monkeypatch.setattr(
        "auto_research.automation.comment_on_issue",
        lambda *, repo, issue_number, body: comments.append((repo, issue_number, body)),
    )
    monkeypatch.setattr(
        "auto_research.automation.close_issue",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("close failed")),
    )

    result = finalize_github(workspace, direction="llm-agents")

    captured = capsys.readouterr()
    assert result["status"] == "completed"
    assert comments and comments[0][1] == 12
    assert "warning" in captured.err.lower()


def test_ensure_profile_exists_rejects_invalid_generated_profile(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    profile_path = workspace / "profile" / "interest-profile.md"

    monkeypatch.setattr(
        "auto_research.automation.build_fallback_profile_from_issue_intake",
        lambda workspace, direction, repo=None: type(
            "Fallback",
            (),
            {
                "markdown": "# Research Interest Profile\n\n## Core Interests\n- only one section\n",
                "repo": repo,
                "issue_numbers": [],
                "source_keys": [],
            },
        )(),
    )

    from auto_research.automation import _ensure_profile_exists

    with pytest.raises(ValueError, match="Generated invalid fallback interest profile"):
        _ensure_profile_exists(workspace, "llm-agents", profile_path)


def test_run_daily_pipeline_backfills_manual_pdf(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction = "npu-compiler"
    paper_dir = workspace / "directions" / direction / "papers" / "2603.23566"
    paper_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = paper_dir / "source.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nManual text\n")
    profile_path = workspace / "directions" / direction / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
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
            direction=direction,
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


def test_run_daily_pipeline_preserves_candidate_when_pdf_missing(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    direction_root = workspace / "directions" / "fl-sys"
    ensure_direction_workspace(workspace, "fl-sys")
    (direction_root / "profile" / "interest-profile.md").write_text(
        "# Research Interest Profile\n\n## Core Interests\n- federated learning systems\n\n## Soft Boundaries\n- client orchestration\n\n## Exclusions\n- pure theory\n\n## Current-Phase Bias\n- systems scalability\n\n## Evaluation Heuristics\n- prefer systems papers\n\n## Open Questions\n- how to manage heterogeneity\n",
        encoding="utf-8",
    )
    write_search_profile(
        direction_root / "profile" / "search-profile.json",
        SearchProfile(
            direction="fl-sys",
            canonical_topic="federated learning systems",
            aliases=["federated learning"],
            related_terms=["client orchestration"],
            exclude_terms=["pure theory"],
            preferred_problem_types=["systems scalability"],
            preferred_system_axes=["heterogeneity"],
            retrieval_hints=["prefer systems papers"],
            seed_queries=["federated learning systems"],
            source_preferences=["arxiv", "semantic scholar"],
        ),
    )

    candidate = RetrievedCandidate(
        paper_id="2501.00001v1",
        title="Federated Learning Systems at Scale",
        summary="Systems paper.",
        pdf_url="",
        landing_page_url="https://example.test/paper",
        source_family="semantic_scholar",
        discovery_sources=["agent_web"],
    )

    monkeypatch.setattr("auto_research.automation.run_hybrid_retrieval", lambda **kwargs: [candidate])

    run_daily_pipeline(
        PipelineConfig(workspace=workspace, direction="fl-sys", label="2026-04-10"),
        llm_client=FakeLLMClient(),
    )

    metadata_text = (direction_root / "papers" / "2501.00001" / "metadata.json").read_text(
        encoding="utf-8"
    )
    summary_text = (direction_root / "reports" / "daily" / "2026-04-10-summary.md").read_text(
        encoding="utf-8"
    )

    assert '\"pdf_status\": \"manual_required\"' in metadata_text
    assert "Needs Manual PDF" in summary_text
    assert "Federated Learning Systems at Scale" in summary_text


def test_run_daily_pipeline_clears_manual_pdf_when_local_pdf_present(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    direction_root = workspace / "directions" / "fl-sys"
    ensure_direction_workspace(workspace, "fl-sys")
    (direction_root / "profile" / "interest-profile.md").write_text(
        "# Research Interest Profile\n\n## Core Interests\n- federated learning systems\n\n## Soft Boundaries\n- client orchestration\n\n## Exclusions\n- pure theory\n\n## Current-Phase Bias\n- systems scalability\n\n## Evaluation Heuristics\n- prefer systems papers\n\n## Open Questions\n- how to manage heterogeneity\n",
        encoding="utf-8",
    )
    write_search_profile(
        direction_root / "profile" / "search-profile.json",
        SearchProfile(
            direction="fl-sys",
            canonical_topic="federated learning systems",
            aliases=["federated learning"],
            related_terms=["client orchestration"],
            exclude_terms=["pure theory"],
            preferred_problem_types=["systems scalability"],
            preferred_system_axes=["heterogeneity"],
            retrieval_hints=["prefer systems papers"],
            seed_queries=["federated learning systems"],
            source_preferences=["arxiv", "semantic scholar"],
        ),
    )

    paper_dir = direction_root / "papers" / "2501.00001"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "metadata.json").write_text(
        '{"arxiv_id": "2501.00001v1", "title": "Federated Learning Systems at Scale", "pdf_status": "manual_required"}\n',
        encoding="utf-8",
    )
    (paper_dir / "source.pdf").write_bytes(b"%PDF-1.4\nmanual\n")

    candidate = RetrievedCandidate(
        paper_id="2501.00001v1",
        title="Federated Learning Systems at Scale",
        summary="Systems paper.",
        pdf_url="",
        landing_page_url="https://example.test/paper",
        source_family="semantic_scholar",
        discovery_sources=["agent_web"],
    )
    monkeypatch.setattr("auto_research.automation.run_hybrid_retrieval", lambda **kwargs: [candidate])
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

    run_daily_pipeline(
        PipelineConfig(workspace=workspace, direction="fl-sys", label="2026-04-10"),
        llm_client=FakeLLMClient(),
    )

    metadata_text = (paper_dir / "metadata.json").read_text(encoding="utf-8")
    summary_text = (direction_root / "reports" / "daily" / "2026-04-10-summary.md").read_text(
        encoding="utf-8"
    )

    assert '"pdf_status": "manual_required"' not in metadata_text
    assert "Federated Learning Systems at Scale" not in summary_text


def test_run_daily_pipeline_resumes_after_manual_pdf_upload(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    direction_root = ensure_direction_workspace(workspace, "fl-sys")
    paper_dir = direction_root / "papers" / "2501.00001"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (direction_root / "profile" / "interest-profile.md").write_text(
        "# Research Interest Profile\n\n## Core Interests\n- federated learning systems\n\n## Soft Boundaries\n- client orchestration\n\n## Exclusions\n- pure theory\n\n## Current-Phase Bias\n- systems scalability\n\n## Evaluation Heuristics\n- prefer systems papers\n\n## Open Questions\n- how to manage heterogeneity\n",
        encoding="utf-8",
    )
    (paper_dir / "metadata.json").write_text(
        json.dumps(
            {
                "arxiv_id": "2501.00001v1",
                "title": "Federated Learning Systems at Scale",
                "summary": "Systems paper.",
                "pdf_url": "",
                "landing_page_url": "https://example.test/paper",
                "discovery_sources": ["agent_web"],
                "source_family": "semantic_scholar",
                "pdf_status": "manual_required",
                "pdf_source": "unknown",
                "first_seen_at": "2026-04-10T00:00:00Z",
                "last_checked_at": "2026-04-10T00:00:00Z",
                "manual_pdf_note": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (paper_dir / "state.json").write_text(
        json.dumps(
            {
                "status": "needs_retry",
                "last_attempt_at": "2026-04-10T00:00:00Z",
                "last_error": "PDF missing",
                "failure_kind": "manual_required",
                "analysis_version": 1,
                "source_updated_at": "2026-04-10T00:00:00Z",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (paper_dir / "source.pdf").write_bytes(b"%PDF-1.4\nManual text\n")

    monkeypatch.setattr("auto_research.automation.run_hybrid_retrieval", lambda **kwargs: [])
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

    llm_client = FakeLLMClient()
    captured: dict[str, object] = {}
    original_summarize_daily = llm_client.summarize_daily_findings

    def _capture_daily_summary(*, profile, analyses, failed_items):
        captured["analyses"] = analyses
        captured["failed_items"] = failed_items
        return original_summarize_daily(profile=profile, analyses=analyses, failed_items=failed_items)

    monkeypatch.setattr(llm_client, "summarize_daily_findings", _capture_daily_summary)

    result = run_daily_pipeline(
        PipelineConfig(workspace=workspace, direction="fl-sys", label="2026-04-11"),
        llm_client=llm_client,
    )

    assert (paper_dir / "problem-solution.md").exists()
    assert '"status": "analysis_done"' in (paper_dir / "state.json").read_text(encoding="utf-8")
    assert '"pdf_status": "manual_uploaded"' in (paper_dir / "metadata.json").read_text(encoding="utf-8")
    assert any(entry.arxiv_id == "2501.00001v1" for entry in result.selected_entries)

    bundle = json.loads(result.bundle_path.read_text(encoding="utf-8"))
    assert any(item["paper_id"] == "2501.00001v1" for item in bundle["selected_papers"])

    history_lines = result.history_path.read_text(encoding="utf-8").splitlines()
    last_record = json.loads(history_lines[-1])
    assert "2501.00001v1" in last_record["selected_ids"]

    analyses = captured.get("analyses")
    assert isinstance(analyses, list)
    assert len(analyses) == 1
    assert analyses[0]["paper_id"] == "2501.00001v1"


def test_run_daily_pipeline_preserves_arxiv_published_updated_and_relevance(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
""",
        encoding="utf-8",
    )

    entry = RegistryEntry(
        arxiv_id="2603.23566v1",
        title="AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization",
        summary="Operator optimization on Ascend NPUs.",
        pdf_url="https://arxiv.org/pdf/2603.23566v1",
        published_at="2026-03-24T08:54:53Z",
        updated_at="2026-03-25T08:54:53Z",
        relevance_band="adjacent",
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
            direction="llm-agents",
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    assert result.selected_entries[0].published_at == "2026-03-24T08:54:53Z"
    assert result.selected_entries[0].updated_at == "2026-03-25T08:54:53Z"
    assert result.selected_entries[0].relevance_band == "adjacent"


def test_run_hybrid_retrieval_raises_on_invalid_search_profile(tmp_path, monkeypatch) -> None:
    from auto_research.automation import run_hybrid_retrieval

    workspace = tmp_path / "research-workspace"
    direction_root = workspace / "directions" / "fl-sys"
    ensure_direction_workspace(workspace, "fl-sys")
    (direction_root / "profile" / "interest-profile.md").write_text(
        "# Research Interest Profile\n\n## Core Interests\n- federated learning systems\n\n## Soft Boundaries\n- client orchestration\n\n## Exclusions\n- pure theory\n\n## Current-Phase Bias\n- systems scalability\n\n## Evaluation Heuristics\n- prefer systems papers\n\n## Open Questions\n- how to manage heterogeneity\n",
        encoding="utf-8",
    )
    (direction_root / "profile" / "search-profile.json").write_text(
        "{this is not valid json",
        encoding="utf-8",
    )

    monkeypatch.setattr("auto_research.automation.run_intake", lambda **kwargs: [])

    with pytest.raises(ValueError, match="search-profile"):
        run_hybrid_retrieval(
            workspace=direction_root,
            profile_path=direction_root / "profile" / "interest-profile.md",
            llm_client=FakeLLMClient(),
            max_results=3,
        )


def test_run_daily_pipeline_prefers_enriched_pdf_url_over_arxiv_fallback(tmp_path, monkeypatch) -> None:
    from auto_research.automation import HybridRetrievalResult

    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
""",
        encoding="utf-8",
    )

    arxiv_entry = RegistryEntry(
        arxiv_id="2603.23566v1",
        title="AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization",
        summary="Operator optimization on Ascend NPUs.",
        pdf_url="",
        published_at="2026-03-24T08:54:53Z",
        updated_at="2026-03-25T08:54:53Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    merged_candidate = RetrievedCandidate(
        paper_id="2603.23566v1",
        title="AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization",
        summary="Web says PDF exists.",
        pdf_url="https://example.test/paper.pdf",
        landing_page_url="https://example.test/paper",
        source_family="arxiv",
        discovery_sources=["arxiv_api", "agent_web"],
    )

    monkeypatch.setattr(
        "auto_research.automation.run_hybrid_retrieval",
        lambda **kwargs: HybridRetrievalResult(
            candidates=[merged_candidate],
            arxiv_entries=[arxiv_entry],
        ),
    )

    downloaded: list[str] = []

    def fake_download_pdf(*, client, url: str, destination: Path) -> None:
        downloaded.append(url)
        destination.write_bytes(b"%PDF-1.4\nExample text\n")

    monkeypatch.setattr("auto_research.automation.download_pdf", fake_download_pdf)
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

    run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    assert downloaded == ["https://example.test/paper.pdf"]
    paper_dir = direction_root / "papers" / "2603.23566"
    assert (paper_dir / "source.pdf").exists()
    state_text = (paper_dir / "state.json").read_text(encoding="utf-8")
    assert "needs_retry" not in state_text
