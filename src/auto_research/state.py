from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_STATUS = "discovered"


@dataclass(slots=True)
class PaperState:
    status: str = DEFAULT_STATUS
    last_attempt_at: str = ""
    last_error: str = ""
    analysis_version: int = 1
    source_updated_at: str = ""


def load_paper_state(path: Path) -> PaperState:
    if not path.exists():
        return PaperState()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("state.json must contain a JSON object")
    return PaperState(
        status=str(payload.get("status", DEFAULT_STATUS)),
        last_attempt_at=str(payload.get("last_attempt_at", "")),
        last_error=str(payload.get("last_error", "")),
        analysis_version=int(payload.get("analysis_version", 1)),
        source_updated_at=str(payload.get("source_updated_at", "")),
    )


def write_paper_state(path: Path, state: PaperState) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2, sort_keys=True), encoding="utf-8")
    return path


def update_paper_state(path: Path, **updates: object) -> PaperState:
    state = load_paper_state(path)
    for key, value in updates.items():
        if not hasattr(state, key):
            raise ValueError(f"Unknown state field: {key}")
        setattr(state, key, value)
    write_paper_state(path, state)
    return state
