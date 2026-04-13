from __future__ import annotations

from pathlib import Path

from auto_research.bilingual import render_bilingual_document
from auto_research.models import InterestProfile, RegistryEntry
from auto_research.openai_client import OpenAIResponsesClient
from auto_research.pdf import extract_text_from_pdf


def render_detailed_analysis_markdown(
    *,
    entry: RegistryEntry,
    english_summary_markdown: str,
    chinese_summary_markdown: str,
    detailed_sections: dict[str, str],
    translated_sections: dict[str, object],
) -> str:
    chinese_lines = [
        "### 标题",
        entry.title,
        "",
        "### 元数据",
        f"- paper_id: `{entry.arxiv_id}`",
        f"- pdf_url: {entry.pdf_url}",
        f"- relevance_band: `{entry.relevance_band}`",
        "",
        "### 详细总结",
        str(translated_sections["one_paragraph_summary"]),
        "",
        "### 问题",
        str(translated_sections["problem"]),
        "",
        "### 方案",
        str(translated_sections["solution"]),
        "",
        "### 关键机制",
        str(translated_sections["key_mechanism"]),
        "",
        "### 假设",
        str(translated_sections["assumptions"]),
        "",
        "### 优势",
        str(translated_sections["strengths"]),
        "",
        "### 弱点",
        str(translated_sections["weaknesses"]),
        "",
        "### 仍然缺失的部分",
        str(translated_sections["what_is_missing"]),
        "",
        "### 为什么与当前方向相关",
        str(translated_sections["why_it_matters"]),
        "",
        "### 可继续推进的想法",
        str(translated_sections["follow_up_ideas"]),
        "",
        "### 关联短摘要",
        chinese_summary_markdown.strip(),
    ]
    english_lines = [
        f"# {entry.title}",
        "",
        "## Metadata",
        f"- paper_id: `{entry.arxiv_id}`",
        f"- pdf_url: {entry.pdf_url}",
        f"- relevance_band: `{entry.relevance_band}`",
        "",
        "## Detailed Summary",
        detailed_sections["one_paragraph_summary"],
        "",
        "## Problem",
        detailed_sections["problem"],
        "",
        "## Solution",
        detailed_sections["solution"],
        "",
        "## Key Mechanism",
        detailed_sections["key_mechanism"],
        "",
        "## Assumptions",
        detailed_sections["assumptions"],
        "",
        "## Strengths",
        detailed_sections["strengths"],
        "",
        "## Weaknesses",
        detailed_sections["weaknesses"],
        "",
        "## What Is Missing",
        detailed_sections["what_is_missing"],
        "",
        "## Why It Matters To Profile",
        detailed_sections["why_it_matters"],
        "",
        "## Possible Follow-Up Ideas",
        detailed_sections["follow_up_ideas"],
        "",
        "## Linked Short Summary",
        english_summary_markdown.strip(),
    ]
    return render_bilingual_document(
        chinese_lines=chinese_lines,
        english_lines=english_lines,
    )


def build_detailed_analysis(
    *,
    client: OpenAIResponsesClient,
    profile: InterestProfile,
    entry: RegistryEntry,
    pdf_path: Path,
) -> tuple[str, dict[str, str]]:
    pdf_text = extract_text_from_pdf(pdf_path)
    sections = client.detailed_analyze_paper(profile=profile, entry=entry, pdf_text=pdf_text)
    return pdf_text, sections
