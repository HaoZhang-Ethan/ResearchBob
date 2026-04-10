from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_STATUS = "discovered"
VALID_STATUSES = {
    "discovered",
    "pdf_downloaded",
    "pdf_failed",
    "analysis_done",
    "analysis_failed",
    "needs_retry",
    "manual_required",
    "manual_uploaded",
}


@dataclass(slots=True)
class PaperState:
    status: str = DEFAULT_STATUS
    last_attempt_at: str = ""
    last_error: str = ""
    failure_kind: str = ""
    analysis_version: int = 1
    source_updated_at: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_paper_state(path: Path) -> PaperState:
    if not path.exists():
        return PaperState()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("state.json must contain a JSON object")
    state = PaperState(
        status=str(payload.get("status", DEFAULT_STATUS)),
        last_attempt_at=str(payload.get("last_attempt_at", "")),
        last_error=str(payload.get("last_error", "")),
        failure_kind=str(payload.get("failure_kind", "")),
        analysis_version=int(payload.get("analysis_version", 1)),
        source_updated_at=str(payload.get("source_updated_at", "")),
    )
    if state.status not in VALID_STATUSES:
        raise ValueError(f"Unknown paper state status: {state.status}")
    return state


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
    if state.status not in VALID_STATUSES:
        raise ValueError(f"Unknown paper state status: {state.status}")
    write_paper_state(path, state)
    return state
