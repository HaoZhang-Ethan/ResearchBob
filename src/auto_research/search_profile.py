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


def validate_search_profile(profile: SearchProfile) -> SearchProfile:
    if not profile.direction.strip():
        raise ValueError("direction must be non-empty")
    if not profile.canonical_topic.strip():
        raise ValueError("canonical_topic must be non-empty")
    if not profile.seed_queries:
        raise ValueError("seed_queries must contain at least one query")
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
    payload = json.loads(path.read_text(encoding="utf-8"))
    profile = SearchProfile(**payload)
    return validate_search_profile(profile)
