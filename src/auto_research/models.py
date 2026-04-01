from __future__ import annotations

import re

from dataclasses import asdict, dataclass, field
from typing import Literal

_VERSION_SUFFIX = re.compile(r"^(?P<base>.+)v(?P<version>\d+)$")
_NEW_STYLE_ARXIV_ID = re.compile(r"^\d{4}\.\d{4,5}(?:v\d+)?$")
_OLD_STYLE_ARXIV_ID = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*/\d{7}(?:v\d+)?$")

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


def validate_arxiv_id(arxiv_id: str) -> str:
    """Validate arXiv ids before they are used as filesystem paths or persisted."""
    if not isinstance(arxiv_id, str):
        raise ValueError("Invalid arxiv_id: expected string")

    raw = arxiv_id
    arxiv_id = arxiv_id.strip()
    if raw != arxiv_id:
        raise ValueError(f"Invalid arxiv_id: {raw!r}")

    if not arxiv_id:
        raise ValueError("Invalid arxiv_id: empty")

    if arxiv_id in {".", ".."}:
        raise ValueError(f"Invalid arxiv_id: {arxiv_id!r}")

    if any(char in arxiv_id for char in ("\x00", "\n", "\r", "\t")):
        raise ValueError(f"Invalid arxiv_id: {arxiv_id!r}")

    if "/" in arxiv_id and any(part in {".", ".."} for part in arxiv_id.split("/")):
        raise ValueError(f"Invalid arxiv_id: {arxiv_id!r}")

    if _NEW_STYLE_ARXIV_ID.fullmatch(arxiv_id) or _OLD_STYLE_ARXIV_ID.fullmatch(arxiv_id):
        return arxiv_id

    raise ValueError(f"Invalid arxiv_id: {arxiv_id!r}")
