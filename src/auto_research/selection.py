from __future__ import annotations

import re
from dataclasses import dataclass

from auto_research.models import InterestProfile, RegistryEntry


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9+-]*")


@dataclass(slots=True)
class RankedCandidate:
    paper_id: str
    priority_score: int
    reason: str


def _keywords(phrases: list[str]) -> set[str]:
    tokens: set[str] = set()
    for phrase in phrases:
        for token in TOKEN_PATTERN.findall(phrase.lower()):
            if len(token) >= 3:
                tokens.add(token)
    return tokens


def heuristic_score(profile: InterestProfile, entry: RegistryEntry) -> int:
    text = f"{entry.title} {entry.summary}".lower()
    core = _keywords(profile.core_interests)
    soft = _keywords(profile.soft_boundaries)
    exclusion = _keywords(profile.exclusions)
    score = 0

    for token in core:
        if token in text:
            score += 3
    for token in soft:
        if token in text:
            score += 1
    for token in exclusion:
        if token in text:
            score -= 4

    if entry.relevance_band == "high-match":
        score += 3
    elif entry.relevance_band == "adjacent":
        score += 1
    else:
        score -= 3

    return score


def prefilter_candidates(
    profile: InterestProfile,
    entries: list[RegistryEntry],
    limit: int,
) -> list[RegistryEntry]:
    ranked = sorted(
        entries,
        key=lambda entry: (heuristic_score(profile, entry), entry.updated_at),
        reverse=True,
    )
    return ranked[:limit]
