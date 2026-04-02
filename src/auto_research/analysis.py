from __future__ import annotations

from pathlib import Path

from auto_research.models import InterestProfile, RegistryEntry
from auto_research.openai_client import OpenAIResponsesClient
from auto_research.pdf import extract_text_from_pdf


def render_detailed_analysis_markdown(
    *,
    entry: RegistryEntry,
    summary_markdown: str,
    detailed_sections: dict[str, str],
) -> str:
    lines = [
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
        summary_markdown.strip(),
        "",
    ]
    return "\n".join(lines)


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
