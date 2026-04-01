from pathlib import Path

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
