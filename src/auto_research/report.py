from __future__ import annotations

import re

from collections import defaultdict
from pathlib import Path

from auto_research.extraction import (
    parse_extraction_document,
    validate_extraction_document,
)
from auto_research.workspace import ensure_workspace


SECTION_TITLES = {
    "read-now": "Top Papers to Read Now",
    "follow-up": "Promising Problems, Weak Solutions",
    "skip": "Papers Likely Safe to Skip",
    "manual-review": "Papers Requiring Manual Verification",
}
ALLOWED_MODES = {"daily", "manual"}
VALID_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _paper_directories(workspace: Path) -> list[Path]:
    papers_root = workspace / "papers"
    return sorted((path for path in papers_root.iterdir() if path.is_dir()), key=lambda path: path.name)


def _validate_report_label(label: str) -> str:
    if not VALID_LABEL_PATTERN.fullmatch(label):
        raise ValueError(f"Invalid report label: {label}")
    return label


def _invalid_entry(paper_dir: Path, reason: str) -> dict[str, str]:
    return {
        "paper_id": paper_dir.name,
        "title": paper_dir.name,
        "confidence": "invalid",
        "relevance_band": "unknown",
        "note": reason,
    }


def _load_report_entry(paper_dir: Path) -> tuple[str, dict[str, str]] | None:
    artifact_path = paper_dir / "problem-solution.md"
    if not artifact_path.exists():
        return None

    try:
        text = artifact_path.read_text(encoding="utf-8")
    except OSError as exc:
        return "manual-review", _invalid_entry(paper_dir, f"Unable to read artifact: {exc}")

    errors = validate_extraction_document(text)
    if errors:
        return "manual-review", _invalid_entry(paper_dir, "; ".join(errors))

    frontmatter = parse_extraction_document(text)
    return frontmatter["opportunity_label"], {**frontmatter, "note": ""}


def compose_report(workspace: Path, mode: str, label: str) -> Path:
    if mode not in ALLOWED_MODES:
        raise ValueError(f"Invalid report mode: {mode}")

    ensure_workspace(workspace)
    safe_label = _validate_report_label(label)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for paper_dir in _paper_directories(workspace):
        loaded_entry = _load_report_entry(paper_dir)
        if loaded_entry is None:
            continue
        opportunity_label, entry = loaded_entry
        grouped[opportunity_label].append(entry)

    lines = [f"# Research Scout Report: {safe_label}", ""]
    for label_key in ("read-now", "follow-up", "skip", "manual-review"):
        lines.append(f"## {SECTION_TITLES[label_key]}")
        entries = grouped.get(label_key, [])
        if not entries:
            lines.append("- None")
        else:
            for entry in entries:
                line = (
                    f'- **{entry["title"]}** (`{entry["paper_id"]}`, '
                    f'confidence: {entry["confidence"]}, relevance: {entry["relevance_band"]})'
                )
                if entry["note"]:
                    line = f"{line} - invalid artifact: {entry['note']}"
                lines.append(line)
        lines.append("")

    report_dir = workspace / "reports" / mode
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{safe_label}.md"
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path
