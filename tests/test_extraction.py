from pathlib import Path

from auto_research.cli import main as cli_main
from auto_research.extraction import parse_extraction_document, validate_extraction_document


FIXTURE_PATH = Path("tests/fixtures/problem_solution.md")


def test_parse_extraction_document_reads_frontmatter() -> None:
    parsed = parse_extraction_document(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert parsed["paper_id"] == "2501.00001v1"
    assert parsed["confidence"] == "high"
    assert parsed["opportunity_label"] == "follow-up"


def test_validate_extraction_document_rejects_missing_sections() -> None:
    errors = validate_extraction_document(
        "---\n"
        'paper_id: "2501.00001v1"\n'
        'title: "Paper"\n'
        'confidence: "high"\n'
        'relevance_band: "high-match"\n'
        'opportunity_label: "read-now"\n'
        "---\n\n"
        "# One-Sentence Summary\ntext\n"
    )

    assert "Missing heading: Problem" in errors
    assert "Missing heading: Proposed Solution" in errors


def test_validate_extraction_document_rejects_empty_section_body() -> None:
    errors = validate_extraction_document(
        "---\n"
        'paper_id: "2501.00001v1"\n'
        'title: "Paper"\n'
        'confidence: "high"\n'
        'relevance_band: "high-match"\n'
        'opportunity_label: "read-now"\n'
        "---\n\n"
        "# One-Sentence Summary\nSummary text.\n\n"
        "# Problem\n\n"
        "# Proposed Solution\nSolution text.\n\n"
        "# Claimed Contributions\n- contribution\n\n"
        "# Evidence Basis\n- Abstract\n\n"
        "# Limitations\n- narrow evaluation\n\n"
        "# Relevance to Profile\nRelevant.\n\n"
        "# Analyst Notes\nNotes.\n"
    )

    assert "Section has no content: Problem" in errors


def test_validate_extraction_cli_prints_errors_to_stderr(tmp_path, capsys) -> None:
    artifact_path = tmp_path / "problem-solution.md"
    artifact_path.write_text(
        "---\n"
        'paper_id: "2501.00001v1"\n'
        'title: "Paper"\n'
        'confidence: "high"\n'
        'relevance_band: "high-match"\n'
        'opportunity_label: "read-now"\n'
        "---\n\n"
        "# One-Sentence Summary\nSummary text.\n\n"
        "# Problem\n\n"
        "# Proposed Solution\nSolution text.\n\n"
        "# Claimed Contributions\n- contribution\n\n"
        "# Evidence Basis\n- Abstract\n\n"
        "# Limitations\n- narrow evaluation\n\n"
        "# Relevance to Profile\nRelevant.\n\n"
        "# Analyst Notes\nNotes.\n",
        encoding="utf-8",
    )

    exit_code = cli_main(["validate-extraction", str(artifact_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Section has no content: Problem" in captured.err
    assert captured.out == ""
