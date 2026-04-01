from __future__ import annotations

import re


REQUIRED_FRONTMATTER_KEYS = (
    "paper_id",
    "title",
    "confidence",
    "relevance_band",
    "opportunity_label",
)

REQUIRED_HEADINGS = (
    "One-Sentence Summary",
    "Problem",
    "Proposed Solution",
    "Claimed Contributions",
    "Evidence Basis",
    "Limitations",
    "Relevance to Profile",
    "Analyst Notes",
)
LIST_HEADINGS = {
    "Claimed Contributions",
    "Evidence Basis",
    "Limitations",
}

ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_RELEVANCE = {"high-match", "adjacent", "low-priority"}
ALLOWED_OPPORTUNITY = {"read-now", "follow-up", "skip", "manual-review"}
VALID_BULLET_PATTERN = re.compile(r"-\s+\S.*")
PLACEHOLDER_BULLET_PATTERN = re.compile(r"-\s*")
SECTION_PATTERN = re.compile(
    r"^# (?P<heading>[^\n]+)\n(?P<body>.*?)(?=^# |\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_extraction_document(text: str) -> dict[str, str]:
    normalized_text = _normalize_newlines(text)
    frontmatter_match = re.match(r"^---\n(.*?)\n---(?:\n|$)", normalized_text, re.DOTALL)
    if frontmatter_match is None:
        raise ValueError("Missing YAML frontmatter")

    data: dict[str, str] = {}
    for line in frontmatter_match.group(1).splitlines():
        key, _, value = line.partition(":")
        data[key.strip()] = _strip_optional_quotes(value.strip())
    return data


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _iter_sections(text: str) -> list[tuple[str, str]]:
    normalized_text = _normalize_newlines(text)
    return [
        (match.group("heading").strip(), match.group("body").strip())
        for match in SECTION_PATTERN.finditer(normalized_text)
    ]


def _strip_optional_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _list_section_lines(body: str) -> list[str]:
    return [line.strip() for line in body.splitlines() if line.strip()]


def _section_uses_bullet_format(heading: str, body: str) -> bool:
    if heading not in LIST_HEADINGS:
        return True
    return all(
        VALID_BULLET_PATTERN.fullmatch(line) or PLACEHOLDER_BULLET_PATTERN.fullmatch(line)
        for line in _list_section_lines(body)
    )


def _section_has_content(heading: str, body: str) -> bool:
    if not body:
        return False
    if heading not in LIST_HEADINGS:
        return True

    return any(
        VALID_BULLET_PATTERN.fullmatch(line) for line in _list_section_lines(body)
    )


def validate_extraction_document(text: str) -> list[str]:
    errors: list[str] = []
    sections: dict[str, str] = {}
    duplicate_headings: list[str] = []

    try:
        frontmatter = parse_extraction_document(text)
    except ValueError as exc:
        return [str(exc)]

    for heading, body in _iter_sections(text):
        if heading in sections:
            duplicate_headings.append(heading)
            continue
        sections[heading] = body

    for key in REQUIRED_FRONTMATTER_KEYS:
        if not frontmatter.get(key):
            errors.append(f"Missing frontmatter key: {key}")

    if frontmatter.get("confidence") not in ALLOWED_CONFIDENCE:
        errors.append("Invalid confidence value")
    if frontmatter.get("relevance_band") not in ALLOWED_RELEVANCE:
        errors.append("Invalid relevance_band value")
    if frontmatter.get("opportunity_label") not in ALLOWED_OPPORTUNITY:
        errors.append("Invalid opportunity_label value")

    for heading in sorted(set(duplicate_headings)):
        errors.append(f"Duplicate heading: {heading}")

    for heading in REQUIRED_HEADINGS:
        if heading not in sections:
            errors.append(f"Missing heading: {heading}")
            continue
        if not _section_uses_bullet_format(heading, sections[heading]):
            errors.append(f"Section contains non-bullet content: {heading}")
            continue
        if not _section_has_content(heading, sections[heading]):
            errors.append(f"Section has no content: {heading}")

    return errors
