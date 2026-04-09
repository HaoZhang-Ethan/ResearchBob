import os
import sys
import json
import errno
import shutil
import time
from pathlib import Path
from subprocess import run
from threading import Thread

import pytest

from auto_research.cli import main as cli_main
from auto_research.models import RegistryEntry
from auto_research.registry import (
    load_registry,
    merge_registry_entries,
    RegistryCorruptionError,
    write_registry,
)
from auto_research.workspace import ensure_direction_workspace, ensure_workspace


def test_ensure_workspace_creates_phase1_directories(tmp_path) -> None:
    root = ensure_workspace(tmp_path / "research-workspace")

    assert (root / "profile").is_dir()
    assert (root / "papers").is_dir()
    assert (root / "reports" / "daily").is_dir()
    assert (root / "reports" / "manual").is_dir()
    assert (root / "issue-intake").is_dir()


def test_ensure_workspace_creates_shared_and_direction_roots(tmp_path) -> None:
    root = ensure_workspace(tmp_path / "research-workspace")

    assert (root / "issue-intake").is_dir()
    assert (root / "directions").is_dir()


def test_ensure_direction_workspace_creates_direction_local_directories(tmp_path) -> None:
    root = ensure_direction_workspace(tmp_path / "research-workspace", "llm-agents")

    assert root == tmp_path / "research-workspace" / "directions" / "llm-agents"
    assert (root / "profile").is_dir()
    assert (root / "papers").is_dir()
    assert (root / "reports" / "daily").is_dir()
    assert (root / "reports" / "manual").is_dir()
    assert (root / "reports" / "longterm").is_dir()
    assert (root / "exports" / "zotero").is_dir()
    assert (root / "pipeline").is_dir()


def test_ensure_direction_workspace_rejects_symlinked_direction_root(tmp_path) -> None:
    workspace_root = tmp_path / "research-workspace"
    ensure_workspace(workspace_root)
    outside = tmp_path / "outside-direction"
    outside.mkdir(parents=True, exist_ok=True)
    symlink_root = workspace_root / "directions" / "llm-agents"
    os.symlink(outside, symlink_root)

    with pytest.raises(OSError, match="symlink"):
        ensure_direction_workspace(workspace_root, "llm-agents")


def test_ensure_direction_workspace_rejects_absolute_direction(tmp_path) -> None:
    workspace_root = tmp_path / "research-workspace"
    ensure_workspace(workspace_root)

    with pytest.raises(ValueError, match="direction"):
        ensure_direction_workspace(workspace_root, "/etc/passwd")


def test_ensure_direction_workspace_rejects_traversal_direction(tmp_path) -> None:
    workspace_root = tmp_path / "research-workspace"
    ensure_workspace(workspace_root)

    with pytest.raises(ValueError, match="direction"):
        ensure_direction_workspace(workspace_root, "..")


def test_ensure_direction_workspace_rejects_dangling_symlinked_direction_root(tmp_path) -> None:
    workspace_root = tmp_path / "research-workspace"
    ensure_workspace(workspace_root)
    target = tmp_path / "dangling-direction"
    target.mkdir(parents=True, exist_ok=True)
    symlink_root = workspace_root / "directions" / "llm-agents"
    os.symlink(target, symlink_root)
    target.rmdir()

    with pytest.raises(OSError, match="symlink"):
        ensure_direction_workspace(workspace_root, "llm-agents")


def test_ensure_workspace_rejects_symlinked_root(tmp_path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir(parents=True, exist_ok=True)
    symlink_root = tmp_path / "workspace-link"
    os.symlink(outside, symlink_root)

    with pytest.raises(OSError, match="symlink"):
        ensure_workspace(symlink_root)


def test_ensure_workspace_rejects_symlinked_phase_directory(tmp_path) -> None:
    root = tmp_path / "research-workspace"
    root.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside-papers"
    outside.mkdir(parents=True, exist_ok=True)
    os.symlink(outside, root / "papers")

    with pytest.raises(OSError, match="symlink"):
        ensure_workspace(root)


def test_ensure_workspace_rejects_workspace_root_with_symlinked_ancestor(tmp_path) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir(parents=True, exist_ok=True)
    symlink_parent = tmp_path / "symlink-parent"
    os.symlink(real_parent, symlink_parent)

    with pytest.raises(OSError, match="symlink"):
        ensure_workspace(symlink_parent / "research-workspace")


def test_init_workspace_cli_accepts_tmp_root(capsys) -> None:
    tmp_root = Path("/tmp")
    if not tmp_root.exists():
        pytest.skip("requires /tmp support")

    workspace = tmp_root / f"auto-research-test-{time.time_ns()}"
    try:
        exit_code = cli_main(["init-workspace", "--workspace", str(workspace)])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.err == ""
        assert (workspace / "profile").is_dir()
        assert (workspace / "papers").is_dir()
        assert (workspace / "reports" / "daily").is_dir()
        assert (workspace / "reports" / "manual").is_dir()
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_init_workspace_cli_rejects_symlinked_ancestor_path(tmp_path, capsys) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir(parents=True, exist_ok=True)
    symlink_parent = tmp_path / "symlink-parent"
    os.symlink(real_parent, symlink_parent)

    exit_code = cli_main(["init-workspace", "--workspace", str(symlink_parent / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Unable to initialize workspace" in captured.err
    assert "symlink" in captured.err.lower()


def test_load_registry_rejects_symlinked_parent_directory(tmp_path) -> None:
    real_dir = tmp_path / "real-registry"
    real_dir.mkdir(parents=True, exist_ok=True)
    symlink_dir = tmp_path / "registry-link"
    os.symlink(real_dir, symlink_dir)
    (real_dir / "registry.jsonl").write_text("", encoding="utf-8")

    with pytest.raises(OSError, match="symlink"):
        load_registry(symlink_dir / "registry.jsonl")


def test_write_registry_rejects_symlinked_parent_directory(tmp_path) -> None:
    real_dir = tmp_path / "real-registry"
    real_dir.mkdir(parents=True, exist_ok=True)
    symlink_dir = tmp_path / "registry-link"
    os.symlink(real_dir, symlink_dir)

    with pytest.raises(OSError, match="symlink"):
        write_registry(symlink_dir / "registry.jsonl", [])


def test_registry_accepts_tmp_root_workspace() -> None:
    tmp_root = Path("/tmp")
    if not tmp_root.exists():
        pytest.skip("requires /tmp support")

    workspace = tmp_root / f"auto-research-registry-test-{time.time_ns()}"
    try:
        ensure_workspace(workspace)
        registry_path = workspace / "papers" / "registry.jsonl"
        entry = RegistryEntry(
            arxiv_id="2501.00001v1",
            title="Temp Root Registry",
            summary="temp root registry test",
            pdf_url="https://arxiv.org/pdf/2501.00001v1",
            published_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            relevance_band="adjacent",
            source="arxiv",
        )

        write_registry(registry_path, [entry])
        loaded = load_registry(registry_path)

        assert [item.arxiv_id for item in loaded] == ["2501.00001v1"]
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_load_registry_reports_invalid_utf8_as_corruption(tmp_path) -> None:
    registry_path = tmp_path / "registry.jsonl"
    registry_path.write_bytes(b"\xff\n")

    with pytest.raises(RegistryCorruptionError, match="UTF-8") as excinfo:
        load_registry(registry_path)

    assert excinfo.value.path == registry_path
    assert excinfo.value.line_number == 1


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


def test_write_registry_rejects_symlinked_destination(tmp_path) -> None:
    outside = tmp_path / "outside-registry.jsonl"
    outside.write_text("do not touch\n", encoding="utf-8")

    path = tmp_path / "papers" / "registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(outside, path)

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

    with pytest.raises(OSError, match="symlink"):
        write_registry(path, [entry])

    assert outside.read_text(encoding="utf-8") == "do not touch\n"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="requires os.mkfifo support")
def test_load_registry_rejects_fifo_targets(tmp_path) -> None:
    fifo_path = tmp_path / "registry.jsonl"
    os.mkfifo(fifo_path)

    # If the implementation accidentally opens the FIFO for reading, it would block
    # until a writer attaches. Provide a short-lived writer so this test never hangs.
    def poke_writer() -> None:
        deadline = time.monotonic() + 0.25
        while time.monotonic() < deadline:
            try:
                fd = os.open(fifo_path, os.O_WRONLY | os.O_NONBLOCK)
            except OSError as exc:
                if exc.errno == errno.ENXIO:
                    time.sleep(0.005)
                    continue
                return
            else:
                os.close(fd)
                return

    thread = Thread(target=poke_writer, daemon=True)
    thread.start()
    try:
        with pytest.raises(OSError, match="non-regular|fifo|Refusing"):
            load_registry(fifo_path)
    finally:
        thread.join(timeout=1)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="requires os.mkfifo support")
def test_write_registry_rejects_fifo_targets(tmp_path) -> None:
    fifo_path = tmp_path / "registry.jsonl"
    os.mkfifo(fifo_path)

    # Keep a FIFO reader open so accidental writers don't block.
    reader_fd = os.open(fifo_path, os.O_RDONLY | os.O_NONBLOCK)
    try:
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

        with pytest.raises(OSError, match="non-regular|fifo|Refusing"):
            write_registry(fifo_path, [entry])
    finally:
        os.close(reader_fd)


def test_load_registry_raises_typed_error_on_malformed_json(tmp_path) -> None:
    path = tmp_path / "papers" / "registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json\n", encoding="utf-8")

    with pytest.raises(RegistryCorruptionError, match="line 1"):
        load_registry(path)


def test_load_registry_raises_typed_error_on_schema_invalid_row(tmp_path) -> None:
    path = tmp_path / "papers" / "registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"arxiv_id":"2501.00001v1"}\n', encoding="utf-8")

    with pytest.raises(RegistryCorruptionError, match="missing"):
        load_registry(path)


def test_load_registry_raises_typed_error_on_invalid_arxiv_id(tmp_path) -> None:
    path = tmp_path / "papers" / "registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "arxiv_id": "..",
                "title": "Bad ID",
                "summary": "bad id",
                "pdf_url": "https://arxiv.org/pdf/2501.00001v1",
                "published_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "relevance_band": "adjacent",
                "source": "arxiv",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RegistryCorruptionError, match="arxiv_id"):
        load_registry(path)


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
