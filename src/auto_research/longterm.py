from __future__ import annotations

from pathlib import Path


def update_longterm_summary(
    *,
    path: Path,
    daily_report_path: Path,
    selected_titles: list[str],
    selected_summaries: list[str] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = ""
    if path.exists():
        previous = path.read_text(encoding="utf-8").strip()

    lines = [
        "# Long-Term Summary",
        "",
        "## Latest Update Source",
        f"- Daily report: `{daily_report_path.name}`",
        "",
        "## Newly Selected Papers",
    ]
    if selected_titles:
        lines.extend(f"- {title}" for title in selected_titles)
    else:
        lines.append("- None")

    if selected_summaries:
        lines.extend(
            [
                "",
                "## Current Problem Clusters",
                "- Operator Fusion / Fusion Boundaries",
                "- Instruction Scheduling / Kernel Execution",
                "- Hardware-Aware Compiler Decisions",
                "",
                "## New Insights",
            ]
        )
        lines.extend(f"- {summary}" for summary in selected_summaries)

    if previous:
        lines.extend(["", "## Previous Snapshot", previous])

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
