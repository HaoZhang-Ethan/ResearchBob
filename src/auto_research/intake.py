from __future__ import annotations

import json
import re
import shutil
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


def _merge_directory_contents(source: Path, destination: Path) -> None:
    for child in source.iterdir():
        target = destination / child.name
        if not target.exists():
            child.rename(target)
            continue

        if child.is_dir() and target.is_dir():
            _merge_directory_contents(child, target)
            child.rmdir()
            continue

        if child.is_dir():
            shutil.rmtree(child)
            continue

        child.unlink()

    source.rmdir()


def _paper_directory(workspace: Path, entry: RegistryEntry) -> Path:
    papers_root = workspace / "papers"
    stable_dir = papers_root / _paper_directory_name(entry)
    legacy_name_pattern = re.compile(rf"^{re.escape(stable_dir.name)}v\d+$")

    legacy_dirs = [
        path
        for path in papers_root.iterdir()
        if path.is_dir() and path.name != stable_dir.name and legacy_name_pattern.fullmatch(path.name)
    ] if papers_root.exists() else []

    if legacy_dirs and not stable_dir.exists():
        stable_dir.mkdir(parents=True, exist_ok=True)

    for legacy_dir in legacy_dirs:
        _merge_directory_contents(legacy_dir, stable_dir)

    stable_dir.mkdir(parents=True, exist_ok=True)
    return stable_dir


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

    for entry in merged:
        paper_dir = _paper_directory(workspace, entry)
        metadata_path = paper_dir / "metadata.json"
        metadata_path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")

    return normalized
