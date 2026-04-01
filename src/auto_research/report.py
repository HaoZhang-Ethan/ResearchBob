from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from auto_research.extraction import parse_extraction_document
from auto_research.workspace import ensure_workspace


SECTION_TITLES = {
    "read-now": "Top Papers to Read Now",
    "follow-up": "Promising Problems, Weak Solutions",
    "skip": "Papers Likely Safe to Skip",
    "manual-review": "Papers Requiring Manual Verification",
}


def _paper_directories(workspace: Path) -> list[Path]:
    papers_root = workspace / "papers"
    return [path for path in papers_root.iterdir() if path.is_dir()]


def compose_report(workspace: Path, mode: str, label: str) -> Path:
    ensure_workspace(workspace)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for paper_dir in _paper_directories(workspace):
        artifact_path = paper_dir / "problem-solution.md"
        if not artifact_path.exists():
            continue
        text = artifact_path.read_text(encoding="utf-8")
        frontmatter = parse_extraction_document(text)
        grouped[frontmatter["opportunity_label"]].append(frontmatter)

    lines = [f"# Research Scout Report: {label}", ""]
    for label_key in ("read-now", "follow-up", "skip", "manual-review"):
        lines.append(f"## {SECTION_TITLES[label_key]}")
        entries = grouped.get(label_key, [])
        if not entries:
            lines.append("- None")
        else:
            for entry in entries:
                lines.append(
                    f'- **{entry["title"]}** (`{entry["paper_id"]}`, confidence: {entry["confidence"]}, relevance: {entry["relevance_band"]})'
                )
        lines.append("")

    report_dir = workspace / "reports" / mode
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{label}.md"
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path
