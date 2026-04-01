from pathlib import Path

import httpx
import json

from auto_research import intake as intake_module
from auto_research.arxiv import ArxivClient
from auto_research.cli import main
from auto_research.intake import build_query_from_profile, run_intake
from auto_research.models import RegistryEntry
from auto_research.profile import load_interest_profile


FIXTURE_XML = Path("tests/fixtures/arxiv_feed.xml").read_text(encoding="utf-8")


def test_build_query_from_profile_uses_core_and_soft_topics() -> None:
    profile = load_interest_profile(Path("tests/fixtures/interest_profile.md"))

    query = build_query_from_profile(profile)

    assert "distributed systems for ML serving" in query
    assert "systems papers adjacent to inference efficiency" in query


def test_arxiv_client_parses_atom_feed() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=FIXTURE_XML)
    )
    client = ArxivClient(httpx.Client(transport=transport), "https://example.test/api/query")

    entries = client.fetch_recent("distributed systems", max_results=2)

    assert [entry.arxiv_id for entry in entries] == ["2501.00001v1", "2501.00002v1"]
    assert entries[0].relevance_band == "adjacent"


def test_validate_profile_rejects_directory(tmp_path, capsys) -> None:
    directory = tmp_path / "profile_dir"
    directory.mkdir()

    result = main(["validate-profile", str(directory)])

    assert result == 1
    captured = capsys.readouterr()
    assert "Profile path is not a file" in captured.err


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
