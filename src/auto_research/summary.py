from __future__ import annotations

from pathlib import Path

from auto_research.bilingual import extract_english_markdown, render_bilingual_document
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
                "analysis": extract_english_markdown(analysis_path.read_text(encoding="utf-8")),
            }
        )
    return items


def _list_or_default(items: list[str], *, default: str) -> list[str]:
    return items if items else [default]


def render_daily_summary_markdown(
    *,
    label: str,
    payload: dict[str, object],
    translated_payload: dict[str, object],
) -> str:
    chinese_lines = [
        f"# 每日想法总结: {label}",
        "",
        "## 今日核心判断",
        str(translated_payload["headline"]),
        "",
        "## 关键结论",
    ]
    chinese_lines.extend(f"- {item}" for item in _list_or_default(translated_payload["top_takeaways"], default="无"))
    chinese_lines.extend(["", "## 好问题，弱方案"])
    chinese_lines.extend(
        f"- {item}" for item in _list_or_default(translated_payload["good_problem_weak_solution"], default="无")
    )
    chinese_lines.extend(["", "## 值得继续想"])
    chinese_lines.extend(
        f"- {item}" for item in _list_or_default(translated_payload["worth_further_thought"], default="无")
    )
    chinese_lines.extend(["", "## 重复出现的主题"])
    chinese_lines.extend(
        f"- {item}" for item in _list_or_default(translated_payload.get("recurring_themes", []), default="无")
    )
    chinese_lines.extend(["", "## 需要手动补 PDF"])
    chinese_lines.extend(
        f"- {item}" for item in _list_or_default(translated_payload.get("needs_manual_pdf", []), default="无")
    )
    chinese_lines.extend(["", "## 失败 / 需要重试"])
    chinese_lines.extend(
        f"- {item}" for item in _list_or_default(translated_payload["failed_or_retry"], default="无")
    )

    english_lines = [
        f"# Daily Idea Summary: {label}",
        "",
        "## Headline",
        str(payload["headline"]),
        "",
        "## Top Takeaways",
    ]
    english_lines.extend(f"- {item}" for item in payload["top_takeaways"])
    english_lines.extend(["", "## Good Problem, Weak Solution"])
    english_lines.extend(f"- {item}" for item in payload["good_problem_weak_solution"])
    english_lines.extend(["", "## Worth Further Thought"])
    english_lines.extend(f"- {item}" for item in payload["worth_further_thought"])
    english_lines.extend(["", "## Recurring Themes"])
    themes = payload.get("recurring_themes", [])
    if themes:
        english_lines.extend(f"- {item}" for item in themes)
    else:
        english_lines.append("- None")
    english_lines.extend(["", "## Needs Manual PDF"])
    manual_pdf = payload.get("needs_manual_pdf", [])
    if manual_pdf:
        english_lines.extend(f"- {item}" for item in manual_pdf)
    else:
        english_lines.append("- None")
    english_lines.extend(["", "## Failed / Needs Retry"])
    failed = payload["failed_or_retry"]
    if failed:
        english_lines.extend(f"- {item}" for item in failed)
    else:
        english_lines.append("- None")
    return render_bilingual_document(chinese_lines=chinese_lines, english_lines=english_lines)


def write_daily_summary(
    *,
    path: Path,
    label: str,
    payload: dict[str, object],
    translated_payload: dict[str, object],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_daily_summary_markdown(label=label, payload=payload, translated_payload=translated_payload),
        encoding="utf-8",
    )
    return path
