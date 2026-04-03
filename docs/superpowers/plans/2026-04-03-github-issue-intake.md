# GitHub Issue Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a local `sync-issues` workflow that reads GitHub issues via `gh`, stores them under `research-workspace/issue-intake/<direction>/<github-username>/`, maintains per-issue request files plus a cumulative summary, and optionally commits/pushes the generated intake artifacts.

**Architecture:** Add a focused `github_intake` module that handles repository discovery, issue parsing, deterministic artifact writing, and optional git automation. Extend workspace initialization and CLI parsing so the new flow fits the existing local-automation structure without coupling it to the paper pipeline.

**Tech Stack:** Python 3.12, standard library `json`/`subprocess`/`re`, existing `auto_research` package, pytest

---

### Task 1: Add workspace and parser coverage first

**Files:**
- Modify: `src/auto_research/workspace.py`
- Modify: `tests/test_workspace.py`
- Create: `tests/test_github_intake.py`

- [ ] **Step 1: Write failing workspace test for the new intake subtree**

```python
def test_ensure_workspace_creates_phase1_directories(tmp_path) -> None:
    root = ensure_workspace(tmp_path / "research-workspace")

    assert (root / "issue-intake").is_dir()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_workspace.py::test_ensure_workspace_creates_phase1_directories -v`
Expected: FAIL because `issue-intake` is not created yet

- [ ] **Step 3: Write failing parser tests for repo discovery and issue parsing**

```python
def test_parse_github_repo_accepts_https_remote() -> None:
    assert parse_github_repo("https://github.com/example/research.git") == "example/research"


def test_parse_issue_body_requires_direction_frontmatter() -> None:
    with pytest.raises(IssueParseError):
        parse_issue_body("## Requirements\n- missing frontmatter\n")
```

- [ ] **Step 4: Run parser tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_parse_github_repo_accepts_https_remote tests/test_github_intake.py::test_parse_issue_body_requires_direction_frontmatter -v`
Expected: FAIL because `auto_research.github_intake` and related functions do not exist yet

- [ ] **Step 5: Implement the minimal workspace update and parser scaffolding**

```python
PHASE1_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
    "issue-intake",
)
```

```python
class IssueParseError(ValueError):
    pass


def parse_github_repo(remote_url: str) -> str:
    ...


def parse_issue_body(body: str) -> ParsedIssueBody:
    ...
```

- [ ] **Step 6: Run the focused tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_workspace.py::test_ensure_workspace_creates_phase1_directories tests/test_github_intake.py::test_parse_github_repo_accepts_https_remote tests/test_github_intake.py::test_parse_issue_body_requires_direction_frontmatter -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/workspace.py tests/test_workspace.py tests/test_github_intake.py src/auto_research/github_intake.py
git commit -m "feat: add github issue intake parsing primitives"
```

### Task 2: Add sync artifact writing with red-green coverage

**Files:**
- Modify: `src/auto_research/github_intake.py`
- Modify: `tests/test_github_intake.py`

- [ ] **Step 1: Write a failing sync test for directory layout and request artifacts**

```python
def test_sync_issues_writes_direction_and_user_artifacts(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    issues = [build_issue(number=12, direction="llm-agents", author="alice")]

    result = sync_issues(
        IssueSyncConfig(workspace=workspace, repo="example/research"),
        fetcher=lambda repo, state, limit: issues,
    )

    request_path = workspace / "issue-intake" / "llm-agents" / "alice" / "requests" / "12.md"
    assert request_path.exists()
    assert result.changed_request_count == 1
```

- [ ] **Step 2: Run the sync test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_sync_issues_writes_direction_and_user_artifacts -v`
Expected: FAIL because `sync_issues()` and result types are not implemented yet

- [ ] **Step 3: Write a failing sync test for re-running unchanged issues**

```python
def test_sync_issues_skips_unchanged_request_files(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    issues = [build_issue(number=12, direction="llm-agents", author="alice")]

    first = sync_issues(IssueSyncConfig(workspace=workspace, repo="example/research"), fetcher=lambda *_: issues)
    second = sync_issues(IssueSyncConfig(workspace=workspace, repo="example/research"), fetcher=lambda *_: issues)

    assert first.changed_request_count == 1
    assert second.changed_request_count == 0
```

- [ ] **Step 4: Run the unchanged sync test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_sync_issues_skips_unchanged_request_files -v`
Expected: FAIL because incremental sync metadata is incomplete

- [ ] **Step 5: Implement minimal sync writing, metadata persistence, and deterministic summary rendering**

```python
@dataclass(slots=True)
class IssueSyncConfig:
    workspace: Path
    repo: str | None = None
    state: str = "open"
    limit: int = 100
    push: bool = False


def sync_issues(
    config: IssueSyncConfig,
    *,
    fetcher: IssueFetcher | None = None,
) -> IssueSyncResult:
    ...
```

- [ ] **Step 6: Run focused sync tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_sync_issues_writes_direction_and_user_artifacts tests/test_github_intake.py::test_sync_issues_skips_unchanged_request_files -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/github_intake.py tests/test_github_intake.py
git commit -m "feat: add github issue sync artifacts"
```

### Task 3: Add `gh` transport and git automation behavior

**Files:**
- Modify: `src/auto_research/github_intake.py`
- Modify: `tests/test_github_intake.py`

- [ ] **Step 1: Write failing tests for `gh` invocation and intake-only git staging**

```python
def test_fetch_github_issues_uses_gh_json_output(monkeypatch) -> None:
    ...


def test_stage_issue_intake_only_targets_issue_intake_subtree(tmp_path, monkeypatch) -> None:
    ...
```

- [ ] **Step 2: Run the transport tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_fetch_github_issues_uses_gh_json_output tests/test_github_intake.py::test_stage_issue_intake_only_targets_issue_intake_subtree -v`
Expected: FAIL because `gh` transport and intake-only stage/push helpers are not fully implemented yet

- [ ] **Step 3: Implement `gh` JSON fetch, current-repo discovery, and intake-only stage/commit/push helpers**

```python
def discover_github_repo(cwd: Path | None = None) -> str:
    ...


def fetch_github_issues(*, repo: str, state: str, limit: int) -> list[GitHubIssue]:
    ...


def _stage_commit_push_issue_intake(workspace: Path, label: str) -> None:
    ...
```

- [ ] **Step 4: Run focused transport tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_fetch_github_issues_uses_gh_json_output tests/test_github_intake.py::test_stage_issue_intake_only_targets_issue_intake_subtree -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_research/github_intake.py tests/test_github_intake.py
git commit -m "feat: add github issue intake transport and git sync"
```

### Task 4: Wire the CLI and validate command behavior

**Files:**
- Modify: `src/auto_research/cli.py`
- Modify: `tests/test_cli_smoke.py`
- Modify: `tests/test_github_intake.py`

- [ ] **Step 1: Write failing CLI tests for `sync-issues` success and invalid limit handling**

```python
def test_sync_issues_cli_runs_and_reports_summary(monkeypatch, capsys, tmp_path) -> None:
    ...


def test_sync_issues_cli_rejects_invalid_limit(capsys) -> None:
    exit_code = cli_main(["sync-issues", "--limit", "0"])
    assert exit_code == 1
```

- [ ] **Step 2: Run the CLI tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_cli_smoke.py::test_sync_issues_cli_runs_and_reports_summary tests/test_cli_smoke.py::test_sync_issues_cli_rejects_invalid_limit -v`
Expected: FAIL because the CLI subcommand does not exist yet

- [ ] **Step 3: Implement the CLI entrypoint and error handling**

```python
sync_issues_parser = subparsers.add_parser("sync-issues")
sync_issues_parser.add_argument("--workspace", default="research-workspace")
sync_issues_parser.add_argument("--repo")
sync_issues_parser.add_argument("--state", choices=("open", "all"), default="open")
sync_issues_parser.add_argument("--limit", type=int, default=100)
sync_issues_parser.add_argument("--push", action="store_true")
```

- [ ] **Step 4: Run focused CLI tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_cli_smoke.py::test_sync_issues_cli_runs_and_reports_summary tests/test_cli_smoke.py::test_sync_issues_cli_rejects_invalid_limit -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_research/cli.py tests/test_cli_smoke.py tests/test_github_intake.py
git commit -m "feat: add sync-issues cli command"
```

### Task 5: Run full verification and refresh docs

**Files:**
- Modify: `README.md`
- Modify: `docs/local-automation-usage.md`

- [ ] **Step 1: Write failing doc-facing CLI smoke expectation if needed**

```python
def test_build_parser_includes_sync_issues_command() -> None:
    parser = build_parser()
    assert "sync-issues" in parser.format_help()
```

- [ ] **Step 2: Run the doc-facing smoke test to verify it fails if not already covered**

Run: `PYTHONPATH=src pytest tests/test_cli_smoke.py::test_build_parser_includes_sync_issues_command -v`
Expected: FAIL before CLI wiring, PASS once the command exists

- [ ] **Step 3: Update user docs for issue template, sync command, and repo-rename behavior**

```md
### GitHub Issue Intake

Use `sync-issues` to pull issue requests from the current repository through `gh`.
```

- [ ] **Step 4: Run the full targeted verification suite**

Run: `PYTHONPATH=src pytest tests/test_workspace.py tests/test_github_intake.py tests/test_cli_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/local-automation-usage.md tests/test_workspace.py tests/test_github_intake.py tests/test_cli_smoke.py src/auto_research/workspace.py src/auto_research/github_intake.py src/auto_research/cli.py
git commit -m "docs: document github issue intake workflow"
```
