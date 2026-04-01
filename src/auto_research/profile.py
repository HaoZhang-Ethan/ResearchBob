from __future__ import annotations

import re
from pathlib import Path

from auto_research.models import InterestProfile

SECTION_NAMES = (
    "Core Interests",
    "Soft Boundaries",
    "Exclusions",
    "Current-Phase Bias",
    "Evaluation Heuristics",
    "Open Questions",
)


def _section_pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        rf"^## {re.escape(name)}\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )


def _extract_bullets(body: str) -> list[str]:
    bullets: list[str] = []
    for line in body.splitlines():
        if not line.startswith("- "):
            continue
        content = line[2:].strip()
        if content:
            bullets.append(content)
    return bullets


def validate_interest_profile_text(text: str) -> list[str]:
    errors: list[str] = []

    for section in SECTION_NAMES:
        matches = list(_section_pattern(section).finditer(text))
        if not matches:
            errors.append(f"Missing section: {section}")
            continue
        if len(matches) > 1:
            errors.append(f"Duplicate section: {section}")
        match = matches[0]
        if not _extract_bullets(match.group("body")):
            errors.append(f"Section has no bullet items: {section}")

    return errors


def parse_interest_profile_text(text: str) -> InterestProfile:
    errors = validate_interest_profile_text(text)
    if errors:
        raise ValueError("\n".join(errors))

    sections = {
        section: _extract_bullets(_section_pattern(section).search(text).group("body"))
        for section in SECTION_NAMES
    }

    return InterestProfile(
        core_interests=sections["Core Interests"],
        soft_boundaries=sections["Soft Boundaries"],
        exclusions=sections["Exclusions"],
        current_phase_bias=sections["Current-Phase Bias"],
        evaluation_heuristics=sections["Evaluation Heuristics"],
        open_questions=sections["Open Questions"],
    )


def load_interest_profile(path: Path) -> InterestProfile:
    return parse_interest_profile_text(path.read_text(encoding="utf-8"))
