from __future__ import annotations

from pathlib import Path

from auto_research.models import RegistryEntry


def _clean(value: str) -> str:
    return " ".join(value.split())


def export_ris(entries: list[RegistryEntry], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    for entry in entries:
        lines.extend(
            [
                "TY  - UNPB",
                f"ID  - {entry.arxiv_id}",
                f"TI  - {_clean(entry.title)}",
                f"AB  - {_clean(entry.summary)}",
                f"UR  - {entry.pdf_url}",
                f"DA  - {entry.published_at[:10]}",
                "ER  -",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
