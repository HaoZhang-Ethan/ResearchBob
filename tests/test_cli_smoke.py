import os
import sys
from subprocess import run


def test_cli_help_lists_phase1_commands() -> None:
    result = run(
        [sys.executable, "-m", "auto_research.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert result.returncode == 0
    assert "init-workspace" in result.stdout
    assert "validate-profile" in result.stdout
    assert "intake" in result.stdout
    assert "validate-extraction" in result.stdout
    assert "compose-report" in result.stdout
