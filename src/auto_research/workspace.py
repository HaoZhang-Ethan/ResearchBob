from __future__ import annotations

from pathlib import Path

PHASE1_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
)


def _refuse_symlinked_ancestor(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.parts[0])
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise OSError(f"Refusing to use workspace root with symlinked ancestor: {current}")


def ensure_workspace(root: Path) -> Path:
    _refuse_symlinked_ancestor(root)
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
