from __future__ import annotations

from pathlib import Path

from auto_research.bilingual import extract_english_markdown, render_bilingual_document


SECTION_HEADERS = (
    "## Latest Update Source",
    "## Newly Selected Papers",
    "## Current Problem Clusters",
    "## New Insights",
    "## Technical Trend Analysis",
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
    translated_selected_summaries: list[str] | None = None,
    technical_trend_analysis: str | None = None,
    translated_technical_trend_analysis: str | None = None,
    generated_summary: str | None = None,
    translated_generated_summary: str | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = ""
    if path.exists():
        previous = extract_english_markdown(path.read_text(encoding="utf-8")).strip()
    previous_clusters = _extract_previous_block(previous, "## Current Problem Clusters")
    previous_insights = _extract_previous_block(previous, "## New Insights")
    previous_trends = _extract_previous_block(previous, "## Technical Trend Analysis")
    previous_rolling = _extract_previous_block(previous, "## Current Rolling Summary")

    english_lines = [
        "# Long-Term Summary",
        "",
        "## Latest Update Source",
        f"- Daily report: `{daily_report_path.name}`",
        "",
        "## Newly Selected Papers",
    ]
    if selected_titles:
        english_lines.extend(f"- {title}" for title in selected_titles)
    else:
        english_lines.append("- None")

    english_lines.extend(["", "## Current Problem Clusters"])
    if selected_summaries:
        english_lines.extend(
            [
                "- Operator Fusion / Fusion Boundaries",
                "- Instruction Scheduling / Kernel Execution",
                "- Hardware-Aware Compiler Decisions",
            ]
        )
    elif previous_clusters:
        english_lines.extend(previous_clusters.splitlines())
    else:
        english_lines.append("- None")

    english_lines.extend(["", "## New Insights"])
    if selected_summaries:
        english_lines.extend(f"- {summary}" for summary in selected_summaries)
    elif previous_insights:
        english_lines.extend(previous_insights.splitlines())
    else:
        english_lines.append("- None")

    english_lines.extend(["", "## Technical Trend Analysis"])
    if technical_trend_analysis:
        english_lines.append(technical_trend_analysis)
    elif previous_trends:
        english_lines.append(previous_trends)
    else:
        english_lines.append("No technical trend analysis yet.")

    if generated_summary:
        english_lines.extend(["", "## Current Rolling Summary", generated_summary])
    else:
        english_lines.extend(["", "## Current Rolling Summary"])
        if previous_rolling:
            english_lines.append(previous_rolling)
        else:
            english_lines.append("No rolling summary yet.")

    chinese_lines = [
        "# 长期总结",
        "",
        "## 最近更新来源",
        f"- 日报: `{daily_report_path.name}`",
        "",
        "## 新纳入论文",
    ]
    if selected_titles:
        chinese_lines.extend(f"- {title}" for title in selected_titles)
    else:
        chinese_lines.append("- 无")

    chinese_lines.extend(["", "## 当前问题簇"])
    if selected_summaries:
        chinese_lines.extend(
            [
                "- 算子融合 / 融合边界",
                "- 指令调度 / 内核执行",
                "- 面向硬件的编译决策",
            ]
        )
    elif previous_clusters:
        chinese_lines.extend(previous_clusters.splitlines())
    else:
        chinese_lines.append("- 无")

    chinese_lines.extend(["", "## 新发现"])
    if translated_selected_summaries:
        chinese_lines.extend(f"- {summary}" for summary in translated_selected_summaries)
    elif selected_summaries:
        chinese_lines.extend(f"- {summary}" for summary in selected_summaries)
    elif previous_insights:
        chinese_lines.extend(previous_insights.splitlines())
    else:
        chinese_lines.append("- 无")

    chinese_lines.extend(["", "## 技术趋势分析"])
    if translated_technical_trend_analysis:
        chinese_lines.append(translated_technical_trend_analysis)
    elif technical_trend_analysis:
        chinese_lines.append(technical_trend_analysis)
    else:
        chinese_lines.append("暂无技术趋势分析。")

    chinese_lines.extend(["", "## 当前滚动总结"])
    if translated_generated_summary:
        chinese_lines.append(translated_generated_summary)
    elif generated_summary:
        chinese_lines.append(generated_summary)
    elif previous_rolling:
        chinese_lines.append(previous_rolling)
    else:
        chinese_lines.append("暂无滚动总结。")

    path.write_text(
        render_bilingual_document(chinese_lines=chinese_lines, english_lines=english_lines),
        encoding="utf-8",
    )
    return path
