from __future__ import annotations


NAVIGATION_LINE = "[中文版](#chinese-version) | [English](#english-version)"
CHINESE_ANCHOR = '<a id="chinese-version"></a>'
ENGLISH_ANCHOR = '<a id="english-version"></a>'
CHINESE_TITLE = "## Chinese Version"
ENGLISH_TITLE = "## English Version"


def _strip_leading_blank_lines(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def _extract_language_markdown(text: str, *, anchor: str, title: str, other_anchor: str | None = None) -> str:
    if anchor not in text:
        return text.strip() if anchor == ENGLISH_ANCHOR else ""

    fragment = text.split(anchor, 1)[1].lstrip()
    if other_anchor is not None and other_anchor in fragment:
        fragment = fragment.split(other_anchor, 1)[0]

    lines = fragment.splitlines()
    if lines and lines[0].strip() == title:
        lines = lines[1:]
    lines = _strip_leading_blank_lines(lines)
    return "\n".join(lines).strip()


def render_bilingual_document(
    *,
    chinese_lines: list[str],
    english_lines: list[str],
    frontmatter_lines: list[str] | None = None,
) -> str:
    lines: list[str] = []
    if frontmatter_lines:
        lines.extend(frontmatter_lines)
        lines.append("")

    lines.extend(
        [
            NAVIGATION_LINE,
            "",
            CHINESE_ANCHOR,
            "",
            CHINESE_TITLE,
            "",
        ]
    )
    lines.extend(chinese_lines)
    lines.extend(
        [
            "",
            ENGLISH_ANCHOR,
            "",
            ENGLISH_TITLE,
            "",
        ]
    )
    lines.extend(english_lines)
    return "\n".join(lines).rstrip() + "\n"


def extract_chinese_markdown(text: str) -> str:
    return _extract_language_markdown(
        text,
        anchor=CHINESE_ANCHOR,
        title=CHINESE_TITLE,
        other_anchor=ENGLISH_ANCHOR,
    )


def extract_english_markdown(text: str) -> str:
    return _extract_language_markdown(
        text,
        anchor=ENGLISH_ANCHOR,
        title=ENGLISH_TITLE,
    )
