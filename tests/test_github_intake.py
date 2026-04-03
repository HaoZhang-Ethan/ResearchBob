from __future__ import annotations

import subprocess

import pytest

from auto_research.github_intake import (
    GitHubIssue,
    IssueParseError,
    IssueSyncConfig,
    _stage_commit_push_issue_intake,
    fetch_github_issues,
    parse_github_repo,
    parse_issue_body,
    sync_issues,
)
from auto_research.workspace import ensure_workspace


def test_parse_github_repo_accepts_https_remote() -> None:
    assert parse_github_repo("https://github.com/example/research.git") == "example/research"


def test_parse_issue_body_requires_direction_frontmatter() -> None:
    with pytest.raises(IssueParseError, match="direction"):
        parse_issue_body("## Requirements\n- missing frontmatter\n")


def test_sync_issues_writes_direction_and_user_artifacts(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    issues = [
        GitHubIssue(
            number=12,
            title="Track multi-agent papers",
            body="---\ndirection: llm-agents\n---\n\n## Requirements\n- focus on coordination\n",
            author_login="alice",
            created_at="2026-04-03T10:00:00Z",
            updated_at="2026-04-03T11:00:00Z",
            url="https://github.com/example/research/issues/12",
            state="OPEN",
        )
    ]

    result = sync_issues(
        IssueSyncConfig(workspace=workspace, repo="example/research"),
        fetcher=lambda repo, state, limit: issues,
    )

    request_path = workspace / "issue-intake" / "llm-agents" / "alice" / "requests" / "12.md"
    assert request_path.exists()
    assert result.changed_request_count == 1


def test_sync_issues_skips_unchanged_request_files(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    issues = [
        GitHubIssue(
            number=12,
            title="Track multi-agent papers",
            body="---\ndirection: llm-agents\n---\n\n## Requirements\n- focus on coordination\n",
            author_login="alice",
            created_at="2026-04-03T10:00:00Z",
            updated_at="2026-04-03T11:00:00Z",
            url="https://github.com/example/research/issues/12",
            state="OPEN",
        )
    ]

    first = sync_issues(
        IssueSyncConfig(workspace=workspace, repo="example/research"),
        fetcher=lambda repo, state, limit: issues,
    )
    second = sync_issues(
        IssueSyncConfig(workspace=workspace, repo="example/research"),
        fetcher=lambda repo, state, limit: issues,
    )

    assert first.changed_request_count == 1
    assert second.changed_request_count == 0


def test_fetch_github_issues_uses_gh_json_output(monkeypatch) -> None:
    def fake_run(cmd, capture_output, text, check):
        assert cmd == [
            "gh",
            "issue",
            "list",
            "--repo",
            "example/research",
            "--state",
            "open",
            "--limit",
            "5",
            "--json",
            "number,title,body,author,createdAt,updatedAt,url,state",
        ]
        assert capture_output is True
        assert text is True
        assert check is True
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout='[{"number":12,"title":"Track multi-agent papers","body":"---\\ndirection: llm-agents\\n---","author":{"login":"alice"},"createdAt":"2026-04-03T10:00:00Z","updatedAt":"2026-04-03T11:00:00Z","url":"https://github.com/example/research/issues/12","state":"OPEN"}]',
            stderr="",
        )

    monkeypatch.setattr("auto_research.github_intake.subprocess.run", fake_run)

    issues = fetch_github_issues(repo="example/research", state="open", limit=5)

    assert len(issues) == 1
    assert issues[0].author_login == "alice"
    assert issues[0].number == 12


def test_stage_issue_intake_only_targets_issue_intake_subtree(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    workspace = repo_root / "research-workspace"
    ensure_workspace(workspace)
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check, capture_output=False, text=False):
        calls.append(cmd)
        if cmd[:4] == ["git", "diff", "--cached", "--quiet"]:
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("auto_research.github_intake.subprocess.run", fake_run)

    _stage_commit_push_issue_intake(workspace, "2026-04-03")

    assert calls[0] == ["git", "add", "-f", str(workspace / "issue-intake")]
    assert ["git", "commit", "-m", "chore: sync issue intake 2026-04-03"] in calls
    assert ["git", "push"] in calls
