import json

import pytest

from auto_research.openai_client import OpenAIResponsesClient
from auto_research.search_profile import SearchProfile


def test_build_issue_profiles_returns_interest_and_search_profiles(monkeypatch) -> None:
    client = OpenAIResponsesClient(api_key="test-key", client=object())

    monkeypatch.setattr(
        client,
        "_request",
        lambda **kwargs: {
            "interest_profile_markdown": "# Research Interest Profile\n\n## Core Interests\n- federated learning systems\n\n## Soft Boundaries\n- client orchestration\n\n## Exclusions\n- pure theory\n\n## Current-Phase Bias\n- systems scalability\n\n## Evaluation Heuristics\n- prefer systems papers\n\n## Open Questions\n- how to manage heterogeneity\n",
            "search_profile": {
                "direction": "fl-sys",
                "canonical_topic": "federated learning systems",
                "aliases": ["federated learning"],
                "related_terms": ["client orchestration"],
                "exclude_terms": ["pure theory"],
                "preferred_problem_types": ["systems scalability"],
                "preferred_system_axes": ["heterogeneity"],
                "retrieval_hints": ["prefer systems papers"],
                "seed_queries": ["federated learning systems", "client orchestration in federated learning"],
                "source_preferences": ["arxiv", "semantic scholar", "openalex"],
            },
        },
    )

    result = client.build_issue_profiles(
        direction="fl-sys",
        issue_texts=["Prefer FL systems papers with strong systems content."],
    )

    assert "Research Interest Profile" in result.interest_profile_markdown
    assert result.search_profile.canonical_topic == "federated learning systems"


def test_retrieve_web_candidates_returns_structured_candidates(monkeypatch) -> None:
    client = OpenAIResponsesClient(api_key="test-key", client=object())

    monkeypatch.setattr(
        client,
        "_request",
        lambda **kwargs: {
            "candidates": [
                {
                    "title": "Systems Heterogeneity in Federated Learning",
                    "authors": ["A. Researcher"],
                    "year": 2025,
                    "arxiv_id": "",
                    "landing_page_url": "https://example.test/paper",
                    "pdf_url": "",
                    "source_family": "semantic_scholar",
                    "relevance_reason": "Direct systems relevance",
                }
            ]
        },
    )

    profile = SearchProfile(
        direction="fl-sys",
        canonical_topic="federated learning systems",
        aliases=["federated learning"],
        related_terms=["client orchestration"],
        exclude_terms=[],
        preferred_problem_types=["systems scalability"],
        preferred_system_axes=["heterogeneity"],
        retrieval_hints=["prefer systems papers"],
        seed_queries=["federated learning systems"],
        source_preferences=["arxiv", "semantic scholar"],
    )

    candidates = client.retrieve_web_candidates(search_profile=profile, limit=5)

    assert candidates[0]["source_family"] == "semantic_scholar"
    assert candidates[0]["title"] == "Systems Heterogeneity in Federated Learning"


def test_retrieve_web_candidates_enables_web_search_tool_and_propagates_limit(monkeypatch) -> None:
    client = OpenAIResponsesClient(api_key="test-key", client=object())
    captured: dict[str, object] = {}

    def _capture_request(**kwargs):
        captured.update(kwargs)
        return {"candidates": []}

    monkeypatch.setattr(client, "_request", _capture_request)

    profile = SearchProfile(
        direction="fl-sys",
        canonical_topic="federated learning systems",
        aliases=["federated learning"],
        related_terms=["client orchestration"],
        exclude_terms=[],
        preferred_problem_types=["systems scalability"],
        preferred_system_axes=["heterogeneity"],
        retrieval_hints=["prefer systems papers"],
        seed_queries=["federated learning systems"],
        source_preferences=["arxiv", "semantic scholar"],
    )

    client.retrieve_web_candidates(search_profile=profile, limit=5)

    payload = json.loads(captured["input_payload"])
    assert payload["limit"] == 5

    tools = captured["tools"]
    assert any(tool.get("type") == "web_search" for tool in tools)


def test_build_issue_profiles_raises_value_error_on_blank_seed_queries(monkeypatch) -> None:
    client = OpenAIResponsesClient(api_key="test-key", client=object())

    monkeypatch.setattr(
        client,
        "_request",
        lambda **kwargs: {
            "interest_profile_markdown": "# Research Interest Profile\n\n## Core Interests\n- federated learning systems\n",
            "search_profile": {
                "direction": "fl-sys",
                "canonical_topic": "federated learning systems",
                "aliases": ["federated learning"],
                "related_terms": ["client orchestration"],
                "exclude_terms": [],
                "preferred_problem_types": ["systems scalability"],
                "preferred_system_axes": ["heterogeneity"],
                "retrieval_hints": ["prefer systems papers"],
                "seed_queries": [],
                "source_preferences": ["arxiv"],
            },
        },
    )

    with pytest.raises(ValueError):
        client.build_issue_profiles(
            direction="fl-sys",
            issue_texts=["Prefer FL systems papers with strong systems content."],
        )
