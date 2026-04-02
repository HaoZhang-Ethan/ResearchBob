import os
from pathlib import Path

import httpx
import json
import pytest

from auto_research import intake as intake_module
from auto_research.arxiv import ArxivClient
from auto_research.cli import main
from auto_research.intake import build_query_from_profile, run_intake
from auto_research.models import RegistryEntry
from auto_research.profile import load_interest_profile
from auto_research.workspace import ensure_workspace


FIXTURE_XML = Path("tests/fixtures/arxiv_feed.xml").read_text(encoding="utf-8")


def test_build_query_from_profile_uses_core_and_soft_topics() -> None:
    profile = load_interest_profile(Path("tests/fixtures/interest_profile.md"))

    query = build_query_from_profile(profile)

    assert "distributed systems for ML serving" in query
    assert "systems papers adjacent to inference efficiency" in query


def test_build_query_from_profile_escapes_embedded_quotes() -> None:
    query = build_query_from_profile(
        load_interest_profile(Path("tests/fixtures/interest_profile.md"))
    )
    assert '\\"' not in query

    quoted_query = build_query_from_profile(
        intake_module.InterestProfile(
            core_interests=['systems for "LLM serving"'],
            soft_boundaries=['adjacent "scheduling" work'],
        )
    )

    assert 'all:"systems for \\"LLM serving\\""' in quoted_query
    assert 'all:"adjacent \\"scheduling\\" work"' in quoted_query


def test_arxiv_client_parses_atom_feed() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=FIXTURE_XML)
    )
    client = ArxivClient(httpx.Client(transport=transport), "https://example.test/api/query")

    entries = client.fetch_recent("distributed systems", max_results=2)

    assert [entry.arxiv_id for entry in entries] == ["2501.00001v1", "2501.00002v1"]
    assert entries[0].relevance_band == "adjacent"


def test_arxiv_client_requests_submitted_date_sorting() -> None:
    seen_params: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_params.update(dict(request.url.params))
        return httpx.Response(200, text=FIXTURE_XML)

    transport = httpx.MockTransport(handler)
    client = ArxivClient(httpx.Client(transport=transport), "https://example.test/api/query")

    client.fetch_recent("distributed systems", max_results=2)

    assert seen_params["sortBy"] == "submittedDate"
    assert seen_params["sortOrder"] == "descending"


def test_arxiv_client_retries_on_transient_timeout() -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise httpx.ReadTimeout("slow")
        return httpx.Response(200, text=FIXTURE_XML)

    client = ArxivClient(httpx.Client(transport=httpx.MockTransport(handler)), "https://example.test/api/query")
    entries = client.fetch_recent("distributed systems", max_results=2)

    assert attempts["count"] == 3
    assert [entry.arxiv_id for entry in entries] == ["2501.00001v1", "2501.00002v1"]


def test_arxiv_client_parses_legacy_slash_style_id() -> None:
    xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/solv-int/9901001v2</id>
    <updated>2026-01-03T00:00:00Z</updated>
    <published>2026-01-01T00:00:00Z</published>
    <title>Legacy Paper</title>
    <summary>Legacy summary.</summary>
    <link title="pdf" href="http://arxiv.org/pdf/solv-int/9901001v2"/>
  </entry>
</feed>
"""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=xml_text)
    )
    client = ArxivClient(httpx.Client(transport=transport), "https://example.test/api/query")

    entries = client.fetch_recent("legacy", max_results=1)

    assert [entry.arxiv_id for entry in entries] == ["solv-int/9901001v2"]


def test_validate_profile_rejects_directory(tmp_path, capsys) -> None:
    directory = tmp_path / "profile_dir"
    directory.mkdir()

    result = main(["validate-profile", str(directory)])

    assert result == 1
    captured = capsys.readouterr()
    assert "Profile path is not a file" in captured.err


def test_validate_profile_rejects_symlinked_file(tmp_path, capsys) -> None:
    real_profile = tmp_path / "real-profile.md"
    real_profile.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    symlink_profile = tmp_path / "profile-link.md"
    os.symlink(real_profile, symlink_profile)

    result = main(["validate-profile", str(symlink_profile)])

    assert result == 1
    captured = capsys.readouterr()
    assert "symlink" in captured.err.lower()


def test_validate_profile_handles_read_errors(monkeypatch, tmp_path, capsys) -> None:
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text("placeholder", encoding="utf-8")

    original_read_text = Path.read_text

    def patched_read_text(self: Path, encoding: str = "utf-8", errors: str | None = None) -> str:
        if self == profile_path:
            raise OSError("boom")
        return original_read_text(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", patched_read_text)

    result = main(["validate-profile", str(profile_path)])

    assert result == 1
    captured = capsys.readouterr()
    assert "Unable to read profile: boom" in captured.err


def test_validate_profile_prints_content_errors_to_stderr(tmp_path, capsys) -> None:
    profile_path = tmp_path / "bad-profile.md"
    profile_path.write_text("# invalid\n", encoding="utf-8")

    result = main(["validate-profile", str(profile_path)])

    assert result == 1
    captured = capsys.readouterr()
    assert "Missing section: Core Interests" in captured.err
    assert captured.out == ""


def test_intake_cli_uses_workspace_relative_default_profile(tmp_path, monkeypatch, capsys) -> None:
    calls: list[dict[str, object]] = []

    def fake_run_intake(workspace: Path, profile_path: Path, max_results: int) -> list[RegistryEntry]:
        calls.append(
            {
                "workspace": workspace,
                "profile_path": profile_path,
                "max_results": max_results,
            }
        )
        return []

    monkeypatch.setattr("auto_research.cli.run_intake", fake_run_intake)

    workspace = tmp_path / "custom-workspace"
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    result = main(["intake", "--workspace", str(workspace), "--max-results", "7"])

    assert result == 0
    assert calls == [
        {
            "workspace": workspace,
            "profile_path": profile_path,
            "max_results": 7,
        }
    ]
    captured = capsys.readouterr()
    assert "ingested 0 papers" in captured.out


def test_intake_cli_handles_missing_default_profile(tmp_path, capsys) -> None:
    workspace = tmp_path / "fresh-workspace"

    result = main(["intake", "--workspace", str(workspace)])

    assert result == 1
    captured = capsys.readouterr()
    assert "Unable to read intake profile:" in captured.err


@pytest.mark.parametrize("max_results", ["0", "-4"])
def test_intake_cli_rejects_non_positive_max_results(tmp_path, capsys, max_results) -> None:
    workspace = tmp_path / "fresh-workspace"

    result = main(["intake", "--workspace", str(workspace), "--max-results", max_results])

    assert result == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "max-results" in captured.err
    assert "positive" in captured.err.lower()
    assert "Unable to read intake profile:" not in captured.err


def test_intake_cli_fails_cleanly_when_httpx_client_init_fails(
    tmp_path, monkeypatch, capsys
) -> None:
    def broken_client(*args, **kwargs):
        raise ImportError("Using SOCKS proxy, but socks support is missing")

    monkeypatch.setattr("auto_research.arxiv.httpx.Client", broken_client)

    workspace = ensure_workspace(tmp_path / "research-workspace")
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = main(["intake", "--workspace", str(workspace), "--max-results", "1"])

    assert result == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Intake failed:" in captured.err
    assert "httpx" in captured.err.lower() or "proxy" in captured.err.lower()


def test_intake_cli_rejects_symlinked_profile_path(tmp_path, monkeypatch, capsys) -> None:
    calls: list[dict[str, object]] = []

    def fake_run_intake(workspace: Path, profile_path: Path, max_results: int) -> list[RegistryEntry]:
        calls.append(
            {
                "workspace": workspace,
                "profile_path": profile_path,
                "max_results": max_results,
            }
        )
        return []

    monkeypatch.setattr("auto_research.cli.run_intake", fake_run_intake)

    workspace = tmp_path / "research-workspace"
    real_profile = tmp_path / "real-profile.md"
    real_profile.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    symlink_profile = tmp_path / "profile-link.md"
    os.symlink(real_profile, symlink_profile)

    result = main(
        [
            "intake",
            "--workspace",
            str(workspace),
            "--profile",
            str(symlink_profile),
            "--max-results",
            "1",
        ]
    )

    assert result == 1
    assert calls == []
    captured = capsys.readouterr()
    assert "symlink" in captured.err.lower()


def test_intake_cli_handles_malformed_profile(tmp_path, capsys) -> None:
    workspace = tmp_path / "research-workspace"
    profile_path = tmp_path / "bad-profile.md"
    profile_path.write_text("# not a valid profile\n", encoding="utf-8")

    result = main(
        ["intake", "--workspace", str(workspace), "--profile", str(profile_path)]
    )

    assert result == 1
    captured = capsys.readouterr()
    assert "Invalid intake profile:" in captured.err


def test_intake_cli_reports_invalid_arxiv_id_as_data_error(tmp_path, monkeypatch, capsys) -> None:
    workspace = tmp_path / "research-workspace"
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    bad_entry = RegistryEntry(
        arxiv_id="..",
        title="Bad arXiv id",
        summary="This should never ingest",
        pdf_url="http://example.org/bad.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [bad_entry]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    result = main(
        [
            "intake",
            "--workspace",
            str(workspace),
            "--profile",
            str(profile_path),
            "--max-results",
            "1",
        ]
    )

    assert result == 1
    captured = capsys.readouterr()
    assert "Invalid intake data:" in captured.err
    assert "arxiv_id" in captured.err.lower()


def test_intake_cli_handles_network_failures(tmp_path, monkeypatch, capsys) -> None:
    workspace = tmp_path / "research-workspace"
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    def fake_run_intake(workspace: Path, profile_path: Path, max_results: int) -> list[RegistryEntry]:
        raise httpx.ConnectError("network down")

    monkeypatch.setattr("auto_research.cli.run_intake", fake_run_intake)

    result = main(
        ["intake", "--workspace", str(workspace), "--profile", str(profile_path)]
    )

    assert result == 1
    captured = capsys.readouterr()
    assert "Unable to fetch arXiv papers: network down" in captured.err


def test_intake_deduplicates_multiple_versions_in_single_fetch(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    entry_v1 = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Paper v1",
        summary="summary v1",
        pdf_url="http://example.org/v1.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    entry_v2 = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Paper v2",
        summary="summary v2",
        pdf_url="http://example.org/v2.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry_v1, entry_v2]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    entries = run_intake(workspace, profile_path, max_results=2)

    assert [entry.arxiv_id for entry in entries] == [entry_v2.arxiv_id]
    registry_rows = [
        json.loads(line)
        for line in (workspace / "papers" / "registry.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [row["arxiv_id"] for row in registry_rows] == [entry_v2.arxiv_id]


def test_intake_rejects_symlinked_registry_before_writing_metadata(
    tmp_path, monkeypatch
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    outside_registry = tmp_path / "outside-registry.jsonl"
    outside_registry.write_text("", encoding="utf-8")

    registry_path = workspace / "papers" / "registry.jsonl"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(outside_registry, registry_path)

    entry = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Paper v1",
        summary="summary v1",
        pdf_url="http://example.org/v1.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    stable_dir = workspace / "papers" / entry.stable_id.replace("/", "_")
    with pytest.raises(OSError, match="symlinked registry"):
        run_intake(workspace, profile_path, max_results=1)

    assert not (stable_dir / "metadata.json").exists()


def test_intake_does_not_partially_write_metadata_when_late_destination_is_invalid(
    tmp_path, monkeypatch
) -> None:
    workspace = tmp_path / "research-workspace"
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    entry_a = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Paper A",
        summary="summary a",
        pdf_url="http://example.org/a.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    entry_b = RegistryEntry(
        arxiv_id="2501.00002v1",
        title="Paper B",
        summary="summary b",
        pdf_url="http://example.org/b.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry_a, entry_b]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    # Make the *second* metadata destination invalid. Legacy behavior would write A's
    # metadata, then error on B, leaving partial state behind.
    stable_dir_b = workspace / "papers" / entry_b.stable_id.replace("/", "_")
    stable_dir_b.mkdir(parents=True, exist_ok=True)
    (stable_dir_b / "metadata.json").mkdir()

    with pytest.raises(OSError, match="metadata"):
        run_intake(workspace, profile_path, max_results=2)

    stable_dir_a = workspace / "papers" / entry_a.stable_id.replace("/", "_")
    assert not (stable_dir_a / "metadata.json").exists()
    assert not (workspace / "papers" / "registry.jsonl").exists()


def test_intake_reuses_stable_directory_for_version_updates(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    entry_v1 = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Paper v1",
        summary="summary v1",
        pdf_url="http://example.org/v1.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    entry_v2 = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Paper v2",
        summary="summary v2",
        pdf_url="http://example.org/v2.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    responses = iter([[entry_v1], [entry_v2]])

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return next(responses)

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    run_intake(workspace, profile_path, max_results=1)
    run_intake(workspace, profile_path, max_results=1)

    papers_dir = workspace / "papers"
    stable_dir = papers_dir / entry_v2.stable_id.replace("/", "_")
    assert stable_dir.is_dir()
    assert (stable_dir / "metadata.json").exists()

    directories = sorted(
        path.name for path in papers_dir.iterdir() if path.is_dir()
    )
    assert directories == [stable_dir.name]

    metadata = json.loads((stable_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["arxiv_id"] == entry_v2.arxiv_id


def test_intake_migrates_legacy_versioned_directory(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    entry_v2 = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Paper v2",
        summary="summary v2",
        pdf_url="http://example.org/v2.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    legacy_dir = workspace / "papers" / "2501.00001v1"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "problem-solution.md").write_text("legacy artifact", encoding="utf-8")

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry_v2]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    run_intake(workspace, profile_path, max_results=1)

    stable_dir = workspace / "papers" / entry_v2.stable_id.replace("/", "_")
    assert stable_dir.is_dir()
    assert (stable_dir / "problem-solution.md").read_text(encoding="utf-8") == "legacy artifact"
    assert not legacy_dir.exists()


def test_intake_preserves_conflicting_legacy_files_during_migration(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    entry_v2 = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Paper v2",
        summary="summary v2",
        pdf_url="http://example.org/v2.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    stable_dir = workspace / "papers" / "2501.00001"
    stable_dir.mkdir(parents=True, exist_ok=True)
    (stable_dir / "problem-solution.md").write_text("stable artifact", encoding="utf-8")

    legacy_dir = workspace / "papers" / "2501.00001v1"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "problem-solution.md").write_text("legacy artifact", encoding="utf-8")

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry_v2]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    run_intake(workspace, profile_path, max_results=1)

    migrated_conflict = stable_dir / "problem-solution.migrated-from-2501.00001v1.md"
    assert (stable_dir / "problem-solution.md").read_text(encoding="utf-8") == "stable artifact"
    assert migrated_conflict.read_text(encoding="utf-8") == "legacy artifact"
    assert not legacy_dir.exists()


def test_intake_keeps_metadata_on_latest_version_after_downgrade_rerun(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    profile_source = Path("tests/fixtures/interest_profile.md")
    profile_path = tmp_path / "interest_profile.md"
    profile_path.write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")

    entry_v2 = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Paper v2",
        summary="summary v2",
        pdf_url="http://example.org/v2.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )
    entry_v1 = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Paper v1",
        summary="summary v1",
        pdf_url="http://example.org/v1.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )

    responses = iter([[entry_v2], [entry_v1]])

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return next(responses)

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    run_intake(workspace, profile_path, max_results=1)
    run_intake(workspace, profile_path, max_results=1)

    stable_dir = workspace / "papers" / entry_v2.stable_id.replace("/", "_")
    metadata = json.loads((stable_dir / "metadata.json").read_text(encoding="utf-8"))
    registry_rows = [
        json.loads(line)
        for line in (workspace / "papers" / "registry.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert metadata["arxiv_id"] == entry_v2.arxiv_id
    assert [row["arxiv_id"] for row in registry_rows] == [entry_v2.arxiv_id]


def test_run_intake_rejects_symlinked_stable_paper_directory(tmp_path, monkeypatch) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)

    stable_dir = workspace / "papers" / "2501.00001"
    os.symlink(outside_dir, stable_dir)

    entry = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Paper v1",
        summary="summary v1",
        pdf_url="http://example.org/v1.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    with pytest.raises(OSError, match="symlink"):
        run_intake(workspace, profile_path, max_results=1)

    assert not (outside_dir / "metadata.json").exists()


def test_run_intake_ignores_symlinked_legacy_paper_directory(tmp_path, monkeypatch) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    outside_dir = tmp_path / "outside-legacy"
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "outside.txt").write_text("do not migrate", encoding="utf-8")

    legacy_dir = workspace / "papers" / "2501.00001v1"
    os.symlink(outside_dir, legacy_dir)

    entry = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Paper v2",
        summary="summary v2",
        pdf_url="http://example.org/v2.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    run_intake(workspace, profile_path, max_results=1)

    stable_dir = workspace / "papers" / "2501.00001"
    assert stable_dir.is_dir()
    assert not stable_dir.is_symlink()
    assert (outside_dir / "outside.txt").exists()
    assert not (stable_dir / "outside.txt").exists()


def test_intake_cli_reports_corrupt_registry_instead_of_profile_error(
    tmp_path, monkeypatch, capsys
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    registry_path = workspace / "papers" / "registry.jsonl"
    registry_path.write_text("not json\n", encoding="utf-8")

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return []

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    result = main(["intake", "--workspace", str(workspace), "--max-results", "1"])

    assert result == 1
    captured = capsys.readouterr()
    assert "registry" in captured.err.lower()
    assert "Invalid intake profile" not in captured.err


def test_run_intake_rejects_symlinked_metadata_child_without_touching_target(
    tmp_path, monkeypatch
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    outside_target = tmp_path / "outside-metadata.json"
    outside_target.write_text('{"do_not_touch": true}\n', encoding="utf-8")

    paper_dir = workspace / "papers" / "2501.00001"
    paper_dir.mkdir(parents=True, exist_ok=True)
    os.symlink(outside_target, paper_dir / "metadata.json")

    entry = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Paper v1",
        summary="summary v1",
        pdf_url="http://example.org/v1.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    with pytest.raises(OSError, match="symlink"):
        run_intake(workspace, profile_path, max_results=1)

    assert outside_target.read_text(encoding="utf-8") == '{"do_not_touch": true}\n'


def test_run_intake_rejects_invalid_arxiv_id_before_path_derivation(
    tmp_path, monkeypatch
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    invalid_entry = RegistryEntry(
        arxiv_id="..",
        title="Bad id",
        summary="invalid id should be rejected",
        pdf_url="http://example.org/bad.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [invalid_entry]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    with pytest.raises(ValueError, match="arxiv"):
        run_intake(workspace, profile_path, max_results=1)

    assert not (workspace / "metadata.json").exists()


def test_run_intake_does_not_persist_registry_when_paper_directory_validation_fails(
    tmp_path, monkeypatch
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    from auto_research.registry import write_registry

    registry_path = workspace / "papers" / "registry.jsonl"
    write_registry(
        registry_path,
        [
            RegistryEntry(
                arxiv_id="2501.12345v1",
                title="Existing",
                summary="existing summary",
                pdf_url="http://example.org/existing.pdf",
                published_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-01T00:00:00Z",
                relevance_band="adjacent",
                source="arxiv",
            )
        ],
    )
    before = registry_path.read_text(encoding="utf-8")

    entry_ok = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Paper ok",
        summary="summary ok",
        pdf_url="http://example.org/ok.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    entry_bad = RegistryEntry(
        arxiv_id="2501.00002v1",
        title="Paper bad",
        summary="summary bad",
        pdf_url="http://example.org/bad.pdf",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )

    outside_dir = tmp_path / "outside-stable-dir"
    outside_dir.mkdir(parents=True, exist_ok=True)
    os.symlink(outside_dir, workspace / "papers" / "2501.00002")

    def fake_arxiv_client(*args, **kwargs):
        class FakeClient:
            def fetch_recent(self, *args: object, **kwargs: object) -> list[RegistryEntry]:
                return [entry_ok, entry_bad]

        return FakeClient()

    monkeypatch.setattr(intake_module, "ArxivClient", fake_arxiv_client)

    with pytest.raises(OSError, match="symlink"):
        run_intake(workspace, profile_path, max_results=2)

    assert registry_path.read_text(encoding="utf-8") == before
