from __future__ import annotations

from pathlib import Path

PHASE1_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
)


def ensure_workspace(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)

    for relative_path in PHASE1_DIRECTORIES:
        (root / relative_path).mkdir(parents=True, exist_ok=True)

    return root
