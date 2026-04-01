from __future__ import annotations

import re

from dataclasses import asdict, dataclass, field
from typing import Literal

_VERSION_SUFFIX = re.compile(r"^(?P<base>.+)v(?P<version>\d+)$")

RelevanceBand = Literal["high-match", "adjacent", "low-priority"]
Confidence = Literal["high", "medium", "low"]
OpportunityLabel = Literal["read-now", "follow-up", "skip", "manual-review"]


@dataclass(slots=True)
class InterestProfile:
    core_interests: list[str] = field(default_factory=list)
    soft_boundaries: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    current_phase_bias: list[str] = field(default_factory=list)
    evaluation_heuristics: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RegistryEntry:
    arxiv_id: str
    title: str
    summary: str
    pdf_url: str
    published_at: str
    updated_at: str
    relevance_band: RelevanceBand
    source: str

    @property
    def stable_id(self) -> str:
        match = _VERSION_SUFFIX.match(self.arxiv_id)
        return match.group("base") if match else self.arxiv_id

    @property
    def version_number(self) -> int:
        match = _VERSION_SUFFIX.match(self.arxiv_id)
        return int(match.group("version")) if match else 0

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
