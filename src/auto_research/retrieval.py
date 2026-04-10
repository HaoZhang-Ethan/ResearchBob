from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RetrievedCandidate:
    paper_id: str
    title: str
    summary: str
    pdf_url: str
    landing_page_url: str
    source_family: str
    discovery_sources: list[str] = field(default_factory=list)


def _normalized_title(title: str) -> str:
    return " ".join(title.split()).casefold()


def merge_retrieved_candidates(
    *,
    arxiv_candidates: list[RetrievedCandidate],
    web_candidates: list[RetrievedCandidate],
) -> list[RetrievedCandidate]:
    merged: list[RetrievedCandidate] = []
    by_paper_id: dict[str, RetrievedCandidate] = {}
    by_title: dict[str, RetrievedCandidate] = {}

    for candidate in arxiv_candidates + web_candidates:
        key = candidate.paper_id.strip()
        normalized_title = _normalized_title(candidate.title)
        existing = by_paper_id.get(key) if key else by_title.get(normalized_title)
        if existing is None:
            merged.append(candidate)
            if key:
                by_paper_id[key] = candidate
            by_title[normalized_title] = candidate
            continue

        for source in candidate.discovery_sources:
            if source not in existing.discovery_sources:
                existing.discovery_sources.append(source)

        if not existing.pdf_url and candidate.pdf_url:
            existing.pdf_url = candidate.pdf_url

        if "arxiv_api" in candidate.discovery_sources and candidate.landing_page_url:
            existing.landing_page_url = candidate.landing_page_url

    return merged

