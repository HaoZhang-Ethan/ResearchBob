from pathlib import Path

from auto_research.cli import main as cli_main
from auto_research.profile import load_interest_profile, validate_interest_profile_text


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
