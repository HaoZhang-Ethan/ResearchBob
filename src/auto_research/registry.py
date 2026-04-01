from __future__ import annotations

import json
from pathlib import Path

from auto_research.models import RegistryEntry


def load_registry(path: Path) -> list[RegistryEntry]:
    if not path.exists():
        return []

    entries: list[RegistryEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(RegistryEntry(**json.loads(line)))
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
