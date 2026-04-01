from __future__ import annotations

from pathlib import Path

PHASE1_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
)


def ensure_workspace(root: Path) -> Path:
    if root.is_symlink():
        raise OSError(f"Refusing to use symlinked workspace root: {root}")

    root.mkdir(parents=True, exist_ok=True)

    for relative_path in PHASE1_DIRECTORIES:
        current = root
        for part in Path(relative_path).parts:
            current = current / part
            if current.is_symlink():
                raise OSError(f"Refusing to use symlinked workspace directory: {current}")
            current.mkdir(parents=True, exist_ok=True)

    return root
