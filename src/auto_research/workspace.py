from __future__ import annotations

from pathlib import Path

PHASE1_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
    "issue-intake",
    "directions",
)

_ALLOWED_SYMLINK_ANCESTORS = {
    Path("/tmp"),
    Path("/var"),
}


DIRECTION_WORKSPACE_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
    "reports/longterm",
    "exports/zotero",
    "pipeline",
)


def _refuse_symlinked_ancestor(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.parts[0])
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            if current in _ALLOWED_SYMLINK_ANCESTORS:
                continue
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


def ensure_direction_workspace(root: Path, direction: str) -> Path:
    workspace = ensure_workspace(root)
    direction_root = workspace / "directions" / direction

    for relative_path in DIRECTION_WORKSPACE_DIRECTORIES:
        current = direction_root
        for part in Path(relative_path).parts:
            current = current / part
            if current.is_symlink():
                raise OSError(f"Refusing to use symlinked workspace directory: {current}")
            current.mkdir(parents=True, exist_ok=True)

    return direction_root
