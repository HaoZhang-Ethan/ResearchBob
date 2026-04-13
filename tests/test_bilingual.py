from __future__ import annotations

from auto_research.bilingual import extract_english_markdown, render_bilingual_document


def test_render_bilingual_document_places_chinese_before_english() -> None:
    text = render_bilingual_document(
        chinese_lines=[
            "### 一句话总结",
            "中文总结。",
        ],
        english_lines=[
            "# One-Sentence Summary",
            "English summary.",
        ],
        frontmatter_lines=[
            "---",
            'paper_id: "2501.00001v1"',
            "---",
        ],
    )

    assert text.startswith('---\npaper_id: "2501.00001v1"\n---\n\n')
    assert "[中文版](#chinese-version) | [English](#english-version)" in text
    assert '<a id="chinese-version"></a>' in text
    assert '<a id="english-version"></a>' in text
    assert text.index("## Chinese Version") < text.index("## English Version")
    assert text.index("### 一句话总结") < text.index("# One-Sentence Summary")


def test_extract_english_markdown_returns_english_block_from_bilingual_text() -> None:
    text = render_bilingual_document(
        chinese_lines=[
            "### 问题",
            "中文问题。",
        ],
        english_lines=[
            "# Problem",
            "English problem.",
            "",
            "# Proposed Solution",
            "English solution.",
        ],
    )

    extracted = extract_english_markdown(text)

    assert extracted.startswith("# Problem\nEnglish problem.")
    assert "# Proposed Solution\nEnglish solution." in extracted
    assert "中文问题" not in extracted
    assert "## English Version" not in extracted


def test_extract_english_markdown_returns_original_text_for_legacy_file() -> None:
    text = "# Long-Term Summary\n\n## Current Rolling Summary\nLegacy english only.\n"

    assert extract_english_markdown(text) == text.strip()


def test_extract_english_markdown_strips_legacy_frontmatter_when_no_anchor_exists() -> None:
    text = (
        "---\n"
        'paper_id: "2501.00001v1"\n'
        'title: "Legacy Paper"\n'
        "---\n\n"
        "# One-Sentence Summary\n"
        "Legacy english summary.\n"
    )

    extracted = extract_english_markdown(text)

    assert extracted.startswith("# One-Sentence Summary")
    assert "Legacy english summary." in extracted
    assert 'paper_id: "2501.00001v1"' not in extracted
