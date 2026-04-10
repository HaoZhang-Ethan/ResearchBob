from __future__ import annotations

import subprocess

import pytest

from auto_research.search_profile import load_search_profile
from auto_research.github_intake import (
    FallbackProfileResult,
    GitHubIssue,
    IssueParseError,
    IssueSyncConfig,
    _stage_commit_push_issue_intake,
    build_fallback_profile_from_issue_intake,
    discover_issue_directions,
    close_issue,
    comment_on_issue,
    fetch_github_issues,
    parse_github_repo,
    parse_issue_body,
    render_profile_from_issue_intake,
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


def test_discover_issue_directions_returns_only_usable_direction_roots(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    usable = workspace / "issue-intake" / "llm-agents" / "alice"
    ignored = workspace / "issue-intake" / "robotics" / "bob"
    (usable / "requests").mkdir(parents=True, exist_ok=True)
    (usable / "summary.md").write_text("# Issue Intake Summary: llm-agents / alice\n", encoding="utf-8")
    ignored.mkdir(parents=True, exist_ok=True)

    assert discover_issue_directions(workspace) == ["llm-agents"]


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


def test_render_profile_from_issue_intake_summaries(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    summary_dir = workspace / "issue-intake" / "llm-agents" / "alice"
    (summary_dir / "requests").mkdir(parents=True, exist_ok=True)
    (summary_dir / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)

## Requirements
- prefer strong system design
- focus on memory and orchestration

## Constraints
- avoid pure benchmark papers

## Notes
- how should agent memory be structured?
""",
        encoding="utf-8",
    )

    markdown = render_profile_from_issue_intake(workspace, direction="llm-agents")

    assert "llm-agents / alice" in markdown
    assert "## Core Interests" in markdown
    assert "## Open Questions" in markdown


def test_render_profile_from_issue_intake_rejects_empty_workspace(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    with pytest.raises(ValueError, match="issue intake"):
        render_profile_from_issue_intake(workspace, direction="llm-agents")


def test_build_fallback_profile_collects_issue_numbers(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    request_dir = workspace / "issue-intake" / "llm-agents" / "alice" / "requests"
    request_dir.mkdir(parents=True, exist_ok=True)
    (request_dir.parent / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)
""",
        encoding="utf-8",
    )
    (request_dir / "12.md").write_text(
        """---
issue_number: 12
title: "Track multi-agent papers"
state: "OPEN"
author_login: "alice"
direction: "llm-agents"
normalized_direction: "llm-agents"
created_at: "2026-04-03T10:00:00Z"
updated_at: "2026-04-03T11:00:00Z"
url: "https://github.com/example/research/issues/12"
---
""",
        encoding="utf-8",
    )

    result = build_fallback_profile_from_issue_intake(
        workspace,
        direction="llm-agents",
        repo="example/research",
    )

    assert isinstance(result, FallbackProfileResult)
    assert result.repo == "example/research"
    assert result.issue_numbers == [12]
    assert result.source_keys == ["llm-agents/alice"]


def test_build_fallback_profile_from_issue_intake_canonicalizes_direction_label(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    request_dir = workspace / "issue-intake" / "llm-agents" / "alice" / "requests"
    request_dir.mkdir(parents=True, exist_ok=True)
    (request_dir.parent / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)
""",
        encoding="utf-8",
    )

    result = build_fallback_profile_from_issue_intake(
        workspace,
        direction="LLM Agents",
        repo="example/research",
    )

    assert result.direction == "llm-agents"
    assert result.source_keys == ["llm-agents/alice"]


def test_build_fallback_profile_from_issue_intake_uses_only_requested_direction(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    llm_dir = workspace / "issue-intake" / "llm-agents" / "alice" / "requests"
    robo_dir = workspace / "issue-intake" / "robotics" / "bob" / "requests"
    llm_dir.mkdir(parents=True, exist_ok=True)
    robo_dir.mkdir(parents=True, exist_ok=True)

    (llm_dir.parent / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)

## Requirements
- prefer strong system design
- focus on memory and orchestration
""",
        encoding="utf-8",
    )
    (robo_dir.parent / "summary.md").write_text(
        """# Issue Intake Summary: robotics / bob

- Direction: `robotics`
- GitHub Username: `bob`
- Request Count: 1

## Active Issues
- #34: Track robot grasping papers (OPEN)
""",
        encoding="utf-8",
    )
    (llm_dir / "12.md").write_text(
        """---
issue_number: 12
title: "Track multi-agent papers"
state: "OPEN"
author_login: "alice"
direction: "llm-agents"
normalized_direction: "llm-agents"
created_at: "2026-04-03T10:00:00Z"
updated_at: "2026-04-03T11:00:00Z"
url: "https://github.com/example/research/issues/12"
---
""",
        encoding="utf-8",
    )
    (robo_dir / "34.md").write_text(
        """---
issue_number: 34
title: "Track robot grasping papers"
state: "OPEN"
author_login: "bob"
direction: "robotics"
normalized_direction: "robotics"
created_at: "2026-04-03T10:00:00Z"
updated_at: "2026-04-03T11:00:00Z"
url: "https://github.com/example/research/issues/34"
---
""",
        encoding="utf-8",
    )

    result = build_fallback_profile_from_issue_intake(
        workspace,
        direction="llm-agents",
        repo="example/research",
    )

    assert "llm-agents / alice" in result.markdown
    assert "robotics / bob" not in result.markdown
    assert result.issue_numbers == [12]
    assert result.source_keys == ["llm-agents/alice"]


def test_comment_on_issue_uses_gh_issue_comment(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, capture_output, text, check):
        calls.append(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("auto_research.github_intake.subprocess.run", fake_run)

    comment_on_issue(repo="example/research", issue_number=12, body="done")

    assert calls == [["gh", "issue", "comment", "12", "--repo", "example/research", "--body", "done"]]


def test_close_issue_uses_gh_issue_close(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, capture_output, text, check):
        calls.append(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("auto_research.github_intake.subprocess.run", fake_run)

    close_issue(repo="example/research", issue_number=12)

    assert calls == [["gh", "issue", "close", "12", "--repo", "example/research"]]



def test_build_fallback_profile_from_issue_intake_rejects_blank_direction(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    with pytest.raises(ValueError, match="direction"):
        build_fallback_profile_from_issue_intake(workspace, direction="")


def test_build_fallback_profile_from_issue_intake_rejects_traversal_direction(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    with pytest.raises(ValueError, match="direction"):
        build_fallback_profile_from_issue_intake(workspace, direction="../escaped")


def test_build_fallback_profile_from_issue_intake_rejects_absolute_direction(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    with pytest.raises(ValueError, match="direction"):
        build_fallback_profile_from_issue_intake(workspace, direction="/etc/passwd")


def test_generate_direction_profiles_from_issue_intake_writes_interest_and_search_profiles(tmp_path) -> None:
    from auto_research.github_intake import generate_direction_profiles_from_issue_intake

    workspace = tmp_path / "research-workspace"
    request_dir = workspace / "issue-intake" / "fl-sys" / "alice" / "requests"
    request_dir.mkdir(parents=True, exist_ok=True)
    (request_dir.parent / "summary.md").write_text(
        "# Issue Intake Summary: fl-sys / alice\n\n## Active Issues\n- #5: FL Sys (OPEN)\n",
        encoding="utf-8",
    )
    (request_dir / "5.md").write_text(
        "---\nissue_number: 5\ntitle: \"FL Sys\"\n---\n\n# Requirements\nPrefer systems papers.\n",
        encoding="utf-8",
    )

    class FakeClient:
        def build_issue_profiles(self, *, direction: str, issue_texts: list[str]):
            from auto_research.openai_client import IssueProfileArtifacts
            from auto_research.search_profile import SearchProfile

            return IssueProfileArtifacts(
                interest_profile_markdown=(
                    "# Research Interest Profile\n\n## Core Interests\n- federated learning systems\n\n## Soft Boundaries\n"
                    "- client orchestration\n\n## Exclusions\n- pure theory\n\n## Current-Phase Bias\n- systems scalability\n\n"
                    "## Evaluation Heuristics\n- prefer systems papers\n\n## Open Questions\n- how to manage heterogeneity\n"
                ),
                search_profile=SearchProfile(
                    direction="fl-sys",
                    canonical_topic="federated learning systems",
                    aliases=["federated learning"],
                    related_terms=["client orchestration"],
                    exclude_terms=["pure theory"],
                    preferred_problem_types=["systems scalability"],
                    preferred_system_axes=["heterogeneity"],
                    retrieval_hints=["prefer systems papers"],
                    seed_queries=["federated learning systems"],
                    source_preferences=["arxiv", "semantic scholar"],
                ),
            )

    interest_path, search_path = generate_direction_profiles_from_issue_intake(
        workspace=workspace,
        direction="fl-sys",
        client=FakeClient(),
    )

    assert interest_path.exists()
    assert search_path.exists()
    assert load_search_profile(search_path).canonical_topic == "federated learning systems"
