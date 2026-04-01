from __future__ import annotations

import json
from pathlib import Path

from auto_research.arxiv import ArxivClient
from auto_research.models import InterestProfile, RegistryEntry
from auto_research.profile import load_interest_profile
from auto_research.registry import load_registry, merge_registry_entries, write_registry
from auto_research.workspace import ensure_workspace


def build_query_from_profile(profile: InterestProfile) -> str:
    query_terms = profile.core_interests + profile.soft_boundaries[:2]
    return " OR ".join(f'all:"{term}"' for term in query_terms)


def _paper_directory_name(entry: RegistryEntry) -> str:
    return entry.stable_id.replace("/", "_")


def run_intake(workspace: Path, profile_path: Path, max_results: int = 25) -> list[RegistryEntry]:
    ensure_workspace(workspace)
    profile = load_interest_profile(profile_path)
    query = build_query_from_profile(profile)
    incoming = ArxivClient().fetch_recent(query, max_results=max_results)

    normalized: list[RegistryEntry] = []
    for entry in incoming:
        relevance_band = "high-match"
        if any(term.lower() in entry.summary.lower() for term in profile.soft_boundaries):
            relevance_band = "adjacent"
        if any(term.lower() in entry.summary.lower() for term in profile.exclusions):
            relevance_band = "low-priority"

        normalized.append(
            RegistryEntry(
                arxiv_id=entry.arxiv_id,
                title=entry.title,
                summary=entry.summary,
                pdf_url=entry.pdf_url,
                published_at=entry.published_at,
                updated_at=entry.updated_at,
                relevance_band=relevance_band,
                source=entry.source,
            )
        )

    registry_path = workspace / "papers" / "registry.jsonl"
    merged = merge_registry_entries(load_registry(registry_path), normalized)
    write_registry(registry_path, merged)

    for entry in normalized:
        paper_dir = workspace / "papers" / _paper_directory_name(entry)
        paper_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = paper_dir / "metadata.json"
        metadata_path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")

    return normalized
