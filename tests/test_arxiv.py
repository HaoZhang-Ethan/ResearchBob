from pathlib import Path

import httpx

from auto_research.arxiv import ArxivClient
from auto_research.cli import main
from auto_research.intake import build_query_from_profile
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
