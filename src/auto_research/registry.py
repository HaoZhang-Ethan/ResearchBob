from __future__ import annotations

import json
from pathlib import Path

from auto_research.models import RegistryEntry


class RegistryCorruptionError(RuntimeError):
    def __init__(self, path: Path, line_number: int, message: str) -> None:
        self.path = path
        self.line_number = line_number
        self.message = message
        super().__init__(f"{path} line {line_number}: {message}")


_REQUIRED_FIELDS: tuple[str, ...] = (
    "arxiv_id",
    "title",
    "summary",
    "pdf_url",
    "published_at",
    "updated_at",
    "relevance_band",
    "source",
)
_ALLOWED_RELEVANCE_BANDS = {"high-match", "adjacent", "low-priority"}


def load_registry(path: Path) -> list[RegistryEntry]:
    if not path.exists():
        return []

    entries: list[RegistryEntry] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        raw_line = line.strip()
        if not raw_line:
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise RegistryCorruptionError(path, line_number, f"malformed JSON: {exc.msg}") from exc

        if not isinstance(payload, dict):
            raise RegistryCorruptionError(path, line_number, "row must be a JSON object")

        missing = [field for field in _REQUIRED_FIELDS if field not in payload]
        if missing:
            raise RegistryCorruptionError(
                path,
                line_number,
                f"missing required fields: {', '.join(sorted(missing))}",
            )

        non_string_fields = [
            field for field in _REQUIRED_FIELDS if not isinstance(payload.get(field), str)
        ]
        if non_string_fields:
            raise RegistryCorruptionError(
                path,
                line_number,
                f"invalid field types (expected strings): {', '.join(sorted(non_string_fields))}",
            )

        relevance_band = payload.get("relevance_band")
        if relevance_band not in _ALLOWED_RELEVANCE_BANDS:
            raise RegistryCorruptionError(
                path,
                line_number,
                f"invalid relevance_band: {relevance_band}",
            )

        try:
            entries.append(RegistryEntry(**payload))
        except TypeError as exc:
            raise RegistryCorruptionError(path, line_number, f"schema mismatch: {exc}") from exc
    return entries


def write_registry(path: Path, entries: list[RegistryEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(entry.to_dict(), sort_keys=True) for entry in entries)
    path.write_text(f"{payload}\n" if payload else "", encoding="utf-8")


def merge_registry_entries(
    existing: list[RegistryEntry], incoming: list[RegistryEntry]
) -> list[RegistryEntry]:
    merged: dict[str, RegistryEntry] = {}

    def consider(entry: RegistryEntry) -> None:
        current = merged.get(entry.stable_id)
        if current is None:
            merged[entry.stable_id] = entry
            return

        if current.updated_at < entry.updated_at:
            merged[entry.stable_id] = entry
            return

        if (
            current.updated_at == entry.updated_at
            and entry.version_number >= current.version_number
        ):
            merged[entry.stable_id] = entry

    for entry in existing:
        consider(entry)

    for entry in incoming:
        consider(entry)

    ordered = sorted(merged.values(), key=lambda item: item.version_number, reverse=True)
    ordered = sorted(ordered, key=lambda item: item.stable_id)
    ordered = sorted(ordered, key=lambda item: item.updated_at, reverse=True)
    return ordered
