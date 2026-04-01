from pathlib import Path

from auto_research.cli import main as cli_main
from auto_research.profile import (
    load_interest_profile,
    parse_interest_profile_text,
    validate_interest_profile_text,
)


FIXTURE_PATH = Path("tests/fixtures/interest_profile.md")


def test_load_interest_profile_reads_required_sections() -> None:
    profile = load_interest_profile(FIXTURE_PATH)

    assert "distributed systems for ML serving" in profile.core_interests
    assert "systems papers adjacent to inference efficiency" in profile.soft_boundaries
    assert "pure cryptography" in profile.exclusions


def test_validate_interest_profile_flags_missing_sections() -> None:
    errors = validate_interest_profile_text(
        "# Research Interest Profile\n\n## Core Interests\n- one topic\n"
    )

    assert errors == [
        "Missing section: Soft Boundaries",
        "Missing section: Exclusions",
        "Missing section: Current-Phase Bias",
        "Missing section: Evaluation Heuristics",
        "Missing section: Open Questions",
    ]


def test_validate_interest_profile_rejects_template_placeholders() -> None:
    template = Path(
        "skills/research-interest-profile/assets/interest-profile-template.md"
    ).read_text()

    errors = validate_interest_profile_text(template)

    assert errors == [
        "Section has no bullet items: Core Interests",
        "Section has no bullet items: Soft Boundaries",
        "Section has no bullet items: Exclusions",
        "Section has no bullet items: Current-Phase Bias",
        "Section has no bullet items: Evaluation Heuristics",
        "Section has no bullet items: Open Questions",
    ]


def test_validate_profile_cli_missing_file(tmp_path, capsys) -> None:
    missing = tmp_path / "interest-profile.md"

    exit_code = cli_main(["validate-profile", str(missing)])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "Profile path does not exist" in captured.err


def test_validate_profile_cli_rejects_undecodable_utf8(tmp_path, capsys) -> None:
    profile_path = tmp_path / "interest-profile.md"
    profile_path.write_bytes(b"\xff\xfe\xfd not utf-8\n")

    exit_code = cli_main(["validate-profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "utf-8" in captured.err.lower()
    assert "Traceback" not in captured.err


def test_validate_interest_profile_detects_duplicate_headings() -> None:
    text = """# Research Interest Profile

## Core Interests
- topic

## Core Interests
- topic two

## Soft Boundaries
- boundary

## Exclusions
- exclusion

## Current-Phase Bias
- bias

## Evaluation Heuristics
- heuristic

## Open Questions
- question
"""

    errors = validate_interest_profile_text(text)

    assert errors == ["Duplicate section: Core Interests"]


def test_validate_interest_profile_rejects_unexpected_headings() -> None:
    text = """# Research Interest Profile

## Core Interests
- topic

## Soft Boundaries
- boundary

## Exclusions
- exclusion

## Current-Phase Bias
- bias

## Evaluation Heuristics
- heuristic

## Open Questions
- question

## Notes
- stray heading
"""

    errors = validate_interest_profile_text(text)

    assert errors == ["Unexpected section: Notes"]


def test_validate_interest_profile_rejects_stray_prose_in_section() -> None:
    text = """# Research Interest Profile

## Core Interests
- topic
This line should not be here.

## Soft Boundaries
- boundary

## Exclusions
- exclusion

## Current-Phase Bias
- bias

## Evaluation Heuristics
- heuristic

## Open Questions
- question
"""

    errors = validate_interest_profile_text(text)

    assert errors == ["Section contains non-bullet content: Core Interests"]


def test_interest_profile_parsing_accepts_crlf_line_endings() -> None:
    crlf_text = FIXTURE_PATH.read_text(encoding="utf-8").replace("\n", "\r\n")

    assert validate_interest_profile_text(crlf_text) == []
    profile = parse_interest_profile_text(crlf_text)
    assert "distributed systems for ML serving" in profile.core_interests
