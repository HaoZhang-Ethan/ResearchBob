from __future__ import annotations

import json

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class SearchProfile:
    direction: str
    canonical_topic: str
    aliases: list[str] = field(default_factory=list)
    related_terms: list[str] = field(default_factory=list)
    exclude_terms: list[str] = field(default_factory=list)
    preferred_problem_types: list[str] = field(default_factory=list)
    preferred_system_axes: list[str] = field(default_factory=list)
    retrieval_hints: list[str] = field(default_factory=list)
    seed_queries: list[str] = field(default_factory=list)
    source_preferences: list[str] = field(default_factory=list)


def _ensure_payload_shape(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def _ensure_str_field(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _ensure_list_of_str(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings")
    for index, entry in enumerate(value):
        if not isinstance(entry, str):
            raise ValueError(f"{field_name}[{index}] must be a string")
    return value


def validate_search_profile(profile: SearchProfile) -> SearchProfile:
    _ensure_str_field(profile.direction, "direction")
    _ensure_str_field(profile.canonical_topic, "canonical_topic")
    aliases = _ensure_list_of_str(profile.aliases, "aliases")
    _ensure_list_of_str(profile.related_terms, "related_terms")
    _ensure_list_of_str(profile.exclude_terms, "exclude_terms")
    _ensure_list_of_str(profile.preferred_problem_types, "preferred_problem_types")
    _ensure_list_of_str(profile.preferred_system_axes, "preferred_system_axes")
    _ensure_list_of_str(profile.retrieval_hints, "retrieval_hints")
    seed_queries = _ensure_list_of_str(profile.seed_queries, "seed_queries")
    _ensure_list_of_str(profile.source_preferences, "source_preferences")

    if not profile.direction.strip():
        raise ValueError("direction must be non-empty")
    if not profile.canonical_topic.strip():
        raise ValueError("canonical_topic must be non-empty")
    if not seed_queries:
        raise ValueError("seed_queries must contain at least one query")
    for query in seed_queries:
        if not query.strip():
            raise ValueError("seed_queries must contain non-empty strings")

    return profile


def write_search_profile(path: Path, profile: SearchProfile) -> Path:
    validate_search_profile(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(profile), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_search_profile(path: Path) -> SearchProfile:
    payload_raw = json.loads(path.read_text(encoding="utf-8"))
    payload = _ensure_payload_shape(payload_raw)

    _ensure_str_field(payload.get("direction"), "direction")
    _ensure_str_field(payload.get("canonical_topic"), "canonical_topic")

    list_fields = [
        "aliases",
        "related_terms",
        "exclude_terms",
        "preferred_problem_types",
        "preferred_system_axes",
        "retrieval_hints",
        "seed_queries",
        "source_preferences",
    ]
    for field_name in list_fields:
        if field_name in payload:
            _ensure_list_of_str(payload[field_name], field_name)

    profile = SearchProfile(**payload)
    return validate_search_profile(profile)
