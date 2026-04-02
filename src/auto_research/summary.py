from __future__ import annotations

from pathlib import Path

from auto_research.models import RegistryEntry


def load_detailed_analysis_texts(workspace: Path, entries: list[RegistryEntry]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for entry in entries:
        paper_dir = workspace / "papers" / entry.stable_id.replace("/", "_")
        analysis_path = paper_dir / "detailed-analysis.md"
        if not analysis_path.exists():
            continue
        items.append(
            {
                "paper_id": entry.arxiv_id,
                "title": entry.title,
                "analysis": analysis_path.read_text(encoding="utf-8"),
            }
        )
    return items


def render_daily_summary_markdown(*, label: str, payload: dict[str, object]) -> str:
    lines = [
        f"# Daily Idea Summary: {label}",
        "",
        "## Headline",
        str(payload["headline"]),
        "",
        "## Top Takeaways",
    ]
    lines.extend(f"- {item}" for item in payload["top_takeaways"])
    lines.extend(["", "## Good Problem, Weak Solution"])
    lines.extend(f"- {item}" for item in payload["good_problem_weak_solution"])
    lines.extend(["", "## Worth Further Thought"])
    lines.extend(f"- {item}" for item in payload["worth_further_thought"])
    lines.extend(["", "## Recurring Themes"])
    themes = payload.get("recurring_themes", [])
    if themes:
        lines.extend(f"- {item}" for item in themes)
    else:
        lines.append("- None")
    lines.extend(["", "## Failed / Needs Retry"])
    failed = payload["failed_or_retry"]
    if failed:
        lines.extend(f"- {item}" for item in failed)
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_daily_summary(*, path: Path, label: str, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_daily_summary_markdown(label=label, payload=payload), encoding="utf-8")
    return path
