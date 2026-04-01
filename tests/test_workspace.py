import os
import sys
from subprocess import run

from auto_research.models import RegistryEntry
from auto_research.registry import (
    load_registry,
    merge_registry_entries,
    write_registry,
)
from auto_research.workspace import ensure_workspace


def test_ensure_workspace_creates_phase1_directories(tmp_path) -> None:
    root = ensure_workspace(tmp_path / "research-workspace")

    assert (root / "profile").is_dir()
    assert (root / "papers").is_dir()
    assert (root / "reports" / "daily").is_dir()
    assert (root / "reports" / "manual").is_dir()


def test_registry_entry_stable_id_handles_slash_ids() -> None:
    entry = RegistryEntry(
        arxiv_id="solv-int/9901001v2",
        title="Legacy ID",
        summary="legacy stable id test",
        pdf_url="https://arxiv.org",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )

    assert entry.stable_id == "solv-int/9901001"


def test_merge_registry_entries_keeps_latest_version() -> None:
    old = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Older version",
        summary="old",
        pdf_url="https://arxiv.org/pdf/2501.00001v1",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    new = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Newer version",
        summary="new",
        pdf_url="https://arxiv.org/pdf/2501.00001v2",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-03T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    merged = merge_registry_entries([old], [new])

    assert len(merged) == 1
    assert merged[0].arxiv_id == "2501.00001v2"
    assert merged[0].relevance_band == "high-match"


def test_merge_registry_entries_handles_duplicates_in_existing() -> None:
    earlier = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Earlier older version",
        summary="earlier",
        pdf_url="https://arxiv.org/pdf/2501.00001v1",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    later = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Later version",
        summary="later",
        pdf_url="https://arxiv.org/pdf/2501.00001v2",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-03T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    merged = merge_registry_entries([later, earlier], [])

    assert len(merged) == 1
    assert merged[0].arxiv_id == "2501.00001v2"
    assert merged[0].summary == "later"


def test_merge_registry_entries_prefers_newer_version_on_updated_at_tie() -> None:
    older = RegistryEntry(
        arxiv_id="2501.00003v1",
        title="Older tie version",
        summary="older tie",
        pdf_url="https://arxiv.org/pdf/2501.00003v1",
        published_at="2026-01-02T00:00:00Z",
        updated_at="2026-01-05T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    newer = RegistryEntry(
        arxiv_id="2501.00003v2",
        title="Newer tie version",
        summary="newer tie",
        pdf_url="https://arxiv.org/pdf/2501.00003v2",
        published_at="2026-01-02T00:00:00Z",
        updated_at="2026-01-05T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    merged = merge_registry_entries([older], [newer])
    assert merged[0].arxiv_id == "2501.00003v2"

    merged_reverse = merge_registry_entries([newer], [older])
    assert merged_reverse[0].arxiv_id == "2501.00003v2"


def test_merge_registry_entries_orders_equal_timestamps_deterministically() -> None:
    alpha = RegistryEntry(
        arxiv_id="2501.00010v1",
        title="Alpha paper",
        summary="alpha",
        pdf_url="https://arxiv.org/pdf/2501.00010v1",
        published_at="2026-01-02T00:00:00Z",
        updated_at="2026-01-06T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    beta = RegistryEntry(
        arxiv_id="2501.00011v1",
        title="Beta paper",
        summary="beta",
        pdf_url="https://arxiv.org/pdf/2501.00011v1",
        published_at="2026-01-02T00:00:00Z",
        updated_at="2026-01-06T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    merged = merge_registry_entries([beta, alpha], [])
    merged_reverse = merge_registry_entries([alpha, beta], [])

    assert [entry.stable_id for entry in merged] == [
        "2501.00010",
        "2501.00011",
    ]
    assert [entry.stable_id for entry in merged_reverse] == [
        "2501.00010",
        "2501.00011",
    ]


def test_merge_registry_entries_refreshes_metadata_on_exact_tie() -> None:
    existing = RegistryEntry(
        arxiv_id="2501.00020v2",
        title="Exact tie paper",
        summary="stale metadata",
        pdf_url="https://arxiv.org/pdf/2501.00020v2",
        published_at="2026-01-02T00:00:00Z",
        updated_at="2026-01-07T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    incoming = RegistryEntry(
        arxiv_id="2501.00020v2",
        title="Exact tie paper",
        summary="refreshed metadata",
        pdf_url="https://arxiv.org/pdf/2501.00020v2",
        published_at="2026-01-02T00:00:00Z",
        updated_at="2026-01-07T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    merged = merge_registry_entries([existing], [incoming])

    assert len(merged) == 1
    assert merged[0].arxiv_id == "2501.00020v2"
    assert merged[0].relevance_band == "high-match"
    assert merged[0].summary == "refreshed metadata"


def test_registry_write_load_round_trip(tmp_path) -> None:
    entry = RegistryEntry(
        arxiv_id="2501.00002v1",
        title="Round trip",
        summary="serialization test",
        pdf_url="https://arxiv.org/pdf/2501.00002v1",
        published_at="2026-02-01T00:00:00Z",
        updated_at="2026-02-01T00:00:00Z",
        relevance_band="low-priority",
        source="arxiv",
    )
    path = tmp_path / "papers" / "registry.jsonl"

    write_registry(path, [entry])
    loaded = load_registry(path)

    assert loaded == [entry]


def test_cli_init_workspace_creates_requested_directory(tmp_path) -> None:
    target = tmp_path / "custom-workspace"
    result = run(
        [
            sys.executable,
            "-m",
            "auto_research.cli",
            "init-workspace",
            "--workspace",
            str(target),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert result.returncode == 0
    assert (target / "profile").is_dir()
    assert (target / "reports" / "daily").is_dir()
