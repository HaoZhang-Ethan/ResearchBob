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

ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_RELEVANCE = {"high-match", "adjacent", "low-priority"}
ALLOWED_OPPORTUNITY = {"read-now", "follow-up", "skip", "manual-review"}


def parse_extraction_document(text: str) -> dict[str, str]:
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if frontmatter_match is None:
        raise ValueError("Missing YAML frontmatter")

    data: dict[str, str] = {}
    for line in frontmatter_match.group(1).splitlines():
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip().strip('"')
    return data


def validate_extraction_document(text: str) -> list[str]:
    errors: list[str] = []

    try:
        frontmatter = parse_extraction_document(text)
    except ValueError as exc:
        return [str(exc)]

    for key in REQUIRED_FRONTMATTER_KEYS:
        if not frontmatter.get(key):
            errors.append(f"Missing frontmatter key: {key}")

    if frontmatter.get("confidence") not in ALLOWED_CONFIDENCE:
        errors.append("Invalid confidence value")
    if frontmatter.get("relevance_band") not in ALLOWED_RELEVANCE:
        errors.append("Invalid relevance_band value")
    if frontmatter.get("opportunity_label") not in ALLOWED_OPPORTUNITY:
        errors.append("Invalid opportunity_label value")

    for heading in REQUIRED_HEADINGS:
        if f"# {heading}\n" not in text:
            errors.append(f"Missing heading: {heading}")

    return errors
