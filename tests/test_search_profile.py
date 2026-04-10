from pathlib import Path
import json

import pytest

from auto_research.search_profile import (
    SearchProfile,
    load_search_profile,
    write_search_profile,
    validate_search_profile,
)


def test_search_profile_round_trips_json(tmp_path) -> None:
    path = tmp_path / "search-profile.json"
    profile = SearchProfile(
        direction="fl-sys",
        canonical_topic="federated learning systems",
        aliases=["federated systems", "federated learning"],
        related_terms=["client orchestration", "communication-efficient training"],
        exclude_terms=["pure theory"],
        preferred_problem_types=["systems scalability"],
        preferred_system_axes=["heterogeneity", "reliability"],
        retrieval_hints=["prefer systems papers over theory-only papers"],
        seed_queries=[
            "federated learning systems",
            "client orchestration in federated learning",
        ],
        source_preferences=["arxiv", "semantic scholar", "openalex"],
    )

    write_search_profile(path, profile)

    assert load_search_profile(path) == profile


def test_validate_search_profile_rejects_empty_seed_queries() -> None:
    profile = SearchProfile(
        direction="fl-sys",
        canonical_topic="federated learning systems",
        aliases=["federated learning"],
        related_terms=["client orchestration"],
        exclude_terms=[],
        preferred_problem_types=["systems scalability"],
        preferred_system_axes=["heterogeneity"],
        retrieval_hints=["prefer systems papers"],
        seed_queries=[],
        source_preferences=["arxiv"],
    )

    with pytest.raises(ValueError, match="seed_queries"):
        validate_search_profile(profile)


def test_validate_search_profile_rejects_blank_seed_query() -> None:
    profile = SearchProfile(
        direction="fl-sys",
        canonical_topic="federated learning systems",
        aliases=["federated learning"],
        related_terms=["client orchestration"],
        exclude_terms=[],
        preferred_problem_types=["systems scalability"],
        preferred_system_axes=["heterogeneity"],
        retrieval_hints=["prefer systems papers"],
        seed_queries=["   "],
        source_preferences=["arxiv"],
    )

    with pytest.raises(ValueError, match="seed_queries"):
        validate_search_profile(profile)


def test_load_search_profile_rejects_non_object_json(tmp_path: Path) -> None:
    path = tmp_path / "search-profile.json"
    path.write_text(json.dumps(["not an object"]))

    with pytest.raises(ValueError, match="payload"):
        load_search_profile(path)


def test_load_search_profile_rejects_wrong_field_types(tmp_path: Path) -> None:
    path = tmp_path / "search-profile.json"
    payload = {
        "direction": 1,
        "canonical_topic": "federated learning systems",
        "seed_queries": ["client orchestration"],
    }
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="direction"):
        load_search_profile(path)


def test_load_search_profile_rejects_alias_items(tmp_path: Path) -> None:
    path = tmp_path / "search-profile.json"
    payload = {
        "direction": "fl-sys",
        "canonical_topic": "federated learning systems",
        "seed_queries": ["client orchestration"],
        "aliases": ["systems", 1],
    }
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="aliases"):
        load_search_profile(path)
