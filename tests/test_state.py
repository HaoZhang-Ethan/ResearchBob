from __future__ import annotations

from auto_research.state import PaperState, load_paper_state, update_paper_state, write_paper_state


def test_load_paper_state_returns_default_for_missing_file(tmp_path) -> None:
    state = load_paper_state(tmp_path / "state.json")
    assert state == PaperState()


def test_write_and_reload_paper_state(tmp_path) -> None:
    path = tmp_path / "state.json"
    original = PaperState(
        status="pdf_downloaded",
        last_attempt_at="2026-04-02T00:00:00Z",
        last_error="",
        failure_kind="",
        analysis_version=2,
        source_updated_at="2026-04-02T00:00:00Z",
    )
    write_paper_state(path, original)
    loaded = load_paper_state(path)
    assert loaded == original


def test_update_paper_state_overwrites_selected_fields(tmp_path) -> None:
    path = tmp_path / "state.json"
    write_paper_state(path, PaperState())
    updated = update_paper_state(path, status="analysis_failed", last_error="boom", failure_kind="ValueError")
    assert updated.status == "analysis_failed"
    assert updated.last_error == "boom"
    assert updated.failure_kind == "ValueError"
    assert updated.analysis_version == 1
