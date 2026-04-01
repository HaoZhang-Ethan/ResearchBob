from __future__ import annotations

import json
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
VERSION_SUFFIX_PATTERN = re.compile(r"^(?P<base>.+)v\d+$")
PRIMARY_ARTIFACT_NAME = "problem-solution.md"
ARTIFACT_GLOB = "problem-solution*.md"
METADATA_NAME = "metadata.json"


def _paper_directories(workspace: Path) -> list[Path]:
    papers_root = workspace / "papers"
    return sorted(
        (path for path in papers_root.iterdir() if path.is_dir() and not path.is_symlink()),
        key=lambda path: path.name,
    )


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


def _noted_entry(frontmatter: dict[str, str], reason: str) -> dict[str, str]:
    return {**frontmatter, "note": reason}


def _named_invalid_entry(paper_dir: Path, artifact_name: str, reason: str) -> dict[str, str]:
    return {
        "paper_id": paper_dir.name,
        "title": artifact_name,
        "confidence": "invalid",
        "relevance_band": "unknown",
        "note": reason,
    }


def _stable_paper_id(paper_id: str) -> str:
    match = VERSION_SUFFIX_PATTERN.match(paper_id)
    return match.group("base") if match else paper_id


def _expected_directory_name(paper_id: str) -> str:
    return _stable_paper_id(paper_id).replace("/", "_")


def _expected_directory_names(paper_id: str) -> set[str]:
    return {
        _stable_paper_id(paper_id).replace("/", "_"),
        paper_id.replace("/", "_"),
    }


def _load_metadata_arxiv_id(paper_dir: Path) -> tuple[str | None, str | None]:
    metadata_path = paper_dir / METADATA_NAME
    if metadata_path.is_symlink():
        return None, f"Refusing to read symlinked {METADATA_NAME}"
    if not metadata_path.exists():
        return None, None

    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"Unable to read {METADATA_NAME}: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"Invalid {METADATA_NAME}: {exc.msg}"

    arxiv_id = payload.get("arxiv_id")
    if not isinstance(arxiv_id, str) or not arxiv_id:
        return None, f"{METADATA_NAME} is missing arxiv_id"

    return arxiv_id, None


def _manual_review_reason(
    paper_dir: Path,
    frontmatter: dict[str, str],
) -> str | None:
    reasons: list[str] = []
    paper_id = frontmatter["paper_id"]

    if frontmatter["relevance_band"] == "low-priority":
        reasons.append("Artifact has low-priority relevance")

    expected_names = _expected_directory_names(paper_id)
    if paper_dir.name not in expected_names:
        reasons.append(
            f'Artifact paper_id "{paper_id}" does not match containing directory "{paper_dir.name}"'
        )

    metadata_arxiv_id, metadata_error = _load_metadata_arxiv_id(paper_dir)
    if metadata_error is not None:
        reasons.append(metadata_error)
    elif metadata_arxiv_id is not None and metadata_arxiv_id != paper_id:
        reasons.append(
            f'Artifact paper_id "{paper_id}" does not match metadata arxiv_id "{metadata_arxiv_id}"'
        )

    if not reasons:
        return None

    return "; ".join(reasons)


def _load_report_entry(paper_dir: Path) -> tuple[str, dict[str, str]] | None:
    artifact_path = paper_dir / PRIMARY_ARTIFACT_NAME
    if artifact_path.is_symlink():
        return "manual-review", _invalid_entry(paper_dir, "Refusing to read symlinked artifact")
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
    review_reason = _manual_review_reason(paper_dir, frontmatter)
    if review_reason is not None:
        return "manual-review", _noted_entry(frontmatter, review_reason)

    return frontmatter["opportunity_label"], {**frontmatter, "note": ""}


def _load_conflict_entries(paper_dir: Path) -> list[tuple[str, dict[str, str]]]:
    entries: list[tuple[str, dict[str, str]]] = []

    for artifact_path in sorted(paper_dir.glob(ARTIFACT_GLOB), key=lambda path: path.name):
        if artifact_path.is_symlink():
            reason = "Unexpected artifact file present; Refusing to read symlinked artifact"
            entries.append(
                ("manual-review", _named_invalid_entry(paper_dir, artifact_path.name, reason))
            )
            continue
        if artifact_path.name == PRIMARY_ARTIFACT_NAME or not artifact_path.is_file():
            continue

        try:
            text = artifact_path.read_text(encoding="utf-8")
        except OSError as exc:
            reason = f"Unexpected artifact file present; Unable to read artifact: {exc}"
            entries.append(
                ("manual-review", _named_invalid_entry(paper_dir, artifact_path.name, reason))
            )
            continue

        errors = validate_extraction_document(text)
        reason = "Unexpected artifact file present"
        if errors:
            reason = f"{reason}; {'; '.join(errors)}"
        entries.append(
            ("manual-review", _named_invalid_entry(paper_dir, artifact_path.name, reason))
        )

    return entries


def compose_report(workspace: Path, mode: str, label: str) -> Path:
    if mode not in ALLOWED_MODES:
        raise ValueError(f"Invalid report mode: {mode}")

    ensure_workspace(workspace)
    safe_label = _validate_report_label(label)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for paper_dir in _paper_directories(workspace):
        loaded_entry = _load_report_entry(paper_dir)
        if loaded_entry is None:
            pass
        else:
            opportunity_label, entry = loaded_entry
            grouped[opportunity_label].append(entry)

        for opportunity_label, entry in _load_conflict_entries(paper_dir):
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
                    line = f"{line} - note: {entry['note']}"
                lines.append(line)
        lines.append("")

    report_dir = workspace / "reports" / mode
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{safe_label}.md"
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path
