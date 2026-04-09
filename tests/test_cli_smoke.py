import os
import sys
from subprocess import run

from auto_research.cli import main as cli_main


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
    assert "daily-pipeline" in result.stdout


def test_sync_issues_cli_runs_and_reports_summary(monkeypatch, capsys, tmp_path) -> None:
    class Result:
        inspected_issue_count = 3
        parsed_issue_count = 2
        changed_request_count = 1
        refreshed_summaries = [tmp_path / "research-workspace" / "issue-intake" / "llm-agents" / "alice" / "summary.md"]

    monkeypatch.setattr("auto_research.cli.sync_issues", lambda config: Result())

    exit_code = cli_main(["sync-issues", "--workspace", str(tmp_path / "research-workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "inspected_issues=3" in captured.out
    assert "parsed_issues=2" in captured.out
    assert "changed_requests=1" in captured.out


def test_sync_issues_cli_rejects_invalid_limit(capsys) -> None:
    exit_code = cli_main(["sync-issues", "--limit", "0"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Invalid --limit" in captured.err


def test_build_parser_includes_sync_issues_command() -> None:
    result = run(
        [sys.executable, "-m", "auto_research.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert result.returncode == 0
    assert "sync-issues" in result.stdout


def test_finalize_github_cli_runs(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(
        "auto_research.cli.finalize_github",
        lambda workspace, direction=None: {
            "status": "completed",
            "label": "2026-04-04",
            "consumed_issue_numbers": [12],
        },
    )

    exit_code = cli_main(["finalize-github", "--workspace", str(tmp_path / "research-workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "status=completed" in captured.out
    assert "consumed_issues=1" in captured.out


def test_build_parser_includes_finalize_github_command() -> None:
    result = run(
        [sys.executable, "-m", "auto_research.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert result.returncode == 0
    assert "finalize-github" in result.stdout


def test_daily_pipeline_cli_passes_direction(monkeypatch, capsys, tmp_path) -> None:
    captured = {}

    def fake_run_daily_pipeline(config):
        captured["direction"] = config.direction
        return type("Result", (), {"report_path": tmp_path / "report.md", "ris_path": tmp_path / "out.ris"})()

    monkeypatch.setattr("auto_research.cli.run_daily_pipeline", fake_run_daily_pipeline)

    exit_code = cli_main(
        ["daily-pipeline", "--workspace", str(tmp_path / "research-workspace"), "--direction", "llm-agents"]
    )

    assert exit_code == 0
    assert captured["direction"] == "llm-agents"


def test_finalize_github_cli_passes_direction(monkeypatch, capsys, tmp_path) -> None:
    captured = {}

    def fake_finalize_github(workspace, direction=None):
        captured["direction"] = direction
        return {"status": "completed", "label": "2026-04-09", "consumed_issue_numbers": [12]}

    monkeypatch.setattr("auto_research.cli.finalize_github", fake_finalize_github)

    exit_code = cli_main(
        ["finalize-github", "--workspace", str(tmp_path / "research-workspace"), "--direction", "llm-agents"]
    )

    assert exit_code == 0
    assert captured["direction"] == "llm-agents"
