from __future__ import annotations

from pathlib import Path


SECTION_HEADERS = (
    "## Latest Update Source",
    "## Newly Selected Papers",
    "## Current Problem Clusters",
    "## New Insights",
    "## Current Rolling Summary",
)


def _extract_previous_block(text: str, header: str) -> str:
    if header not in text:
        return ""
    start = text.index(header) + len(header)
    rest = text[start:]
    next_positions = [rest.find(other) for other in SECTION_HEADERS if other in rest]
    next_positions = [pos for pos in next_positions if pos >= 0]
    end = min(next_positions) if next_positions else len(rest)
    return rest[:end].strip()


def update_longterm_summary(
    *,
    path: Path,
    daily_report_path: Path,
    selected_titles: list[str],
    selected_summaries: list[str] | None = None,
    generated_summary: str | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = ""
    if path.exists():
        previous = path.read_text(encoding="utf-8").strip()
    previous_clusters = _extract_previous_block(previous, "## Current Problem Clusters")
    previous_insights = _extract_previous_block(previous, "## New Insights")

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

    lines.extend(["", "## Current Problem Clusters"])
    if selected_summaries:
        lines.extend(
            [
                "- Operator Fusion / Fusion Boundaries",
                "- Instruction Scheduling / Kernel Execution",
                "- Hardware-Aware Compiler Decisions",
            ]
        )
    elif previous_clusters:
        lines.extend(previous_clusters.splitlines())
    else:
        lines.append("- None")

    lines.extend(["", "## New Insights"])
    if selected_summaries:
        lines.extend(f"- {summary}" for summary in selected_summaries)
    elif previous_insights:
        lines.extend(previous_insights.splitlines())
    else:
        lines.append("- None")

    if generated_summary:
        lines.extend(["", "## Current Rolling Summary", generated_summary])
    else:
        previous_rolling = _extract_previous_block(previous, "## Current Rolling Summary")
        lines.extend(["", "## Current Rolling Summary"])
        if previous_rolling:
            lines.append(previous_rolling)
        else:
            lines.append("No rolling summary yet.")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
