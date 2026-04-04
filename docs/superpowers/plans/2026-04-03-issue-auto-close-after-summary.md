# Issue Auto-Close After Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When `daily-pipeline` uses fallback profile generation from `issue-intake/` and completes successfully, comment on and close the open GitHub issues that contributed to that fallback profile, without failing the summary run if GitHub cleanup fails.

**Architecture:** Extend `github_intake.py` to return structured fallback-profile source metadata and to expose small `gh` helpers for issue comment/close. Update `automation.py` to preserve fallback metadata through the run and trigger best-effort auto-close only after the pipeline finishes successfully.

**Tech Stack:** Python 3.12, standard library `dataclasses`/`subprocess`/`pathlib`, existing `auto_research` modules, pytest

---

### Task 1: Add failing tests for fallback source metadata and GitHub close helpers

**Files:**
- Modify: `tests/test_github_intake.py`
- Modify: `src/auto_research/github_intake.py`

- [ ] **Step 1: Write a failing test that fallback profile generation exposes consumed issue numbers**

```python
def test_build_fallback_profile_collects_issue_numbers(tmp_path) -> None:
    ...
    result = build_fallback_profile_from_issue_intake(workspace)
    assert result.issue_numbers == [12]
```

- [ ] **Step 2: Run the metadata test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_build_fallback_profile_collects_issue_numbers -v`
Expected: FAIL because the structured fallback result does not exist yet

- [ ] **Step 3: Write failing tests for issue comment and close transport**

```python
def test_comment_on_issue_uses_gh_issue_comment(monkeypatch) -> None:
    ...


def test_close_issue_uses_gh_issue_close(monkeypatch) -> None:
    ...
```

- [ ] **Step 4: Run the transport tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_comment_on_issue_uses_gh_issue_comment tests/test_github_intake.py::test_close_issue_uses_gh_issue_close -v`
Expected: FAIL because the helpers do not exist yet

- [ ] **Step 5: Implement structured fallback metadata and GitHub close helpers**

```python
@dataclass(slots=True)
class FallbackProfileResult:
    markdown: str
    repo: str | None
    issue_numbers: list[int]
    source_keys: list[str]


def build_fallback_profile_from_issue_intake(workspace: Path, repo: str | None = None) -> FallbackProfileResult:
    ...


def comment_on_issue(*, repo: str, issue_number: int, body: str) -> None:
    ...


def close_issue(*, repo: str, issue_number: int) -> None:
    ...
```

- [ ] **Step 6: Run focused tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_build_fallback_profile_collects_issue_numbers tests/test_github_intake.py::test_comment_on_issue_uses_gh_issue_comment tests/test_github_intake.py::test_close_issue_uses_gh_issue_close -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/github_intake.py tests/test_github_intake.py
git commit -m "feat: expose fallback issue metadata and gh close helpers"
```

### Task 2: Add failing pipeline tests for successful auto-close and manual-profile skip

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/automation.py`

- [ ] **Step 1: Write a failing pipeline test for successful fallback run auto-closing consumed issues**

```python
def test_run_daily_pipeline_auto_closes_consumed_issues(tmp_path, monkeypatch) -> None:
    ...
    assert comments == [(repo, 12, ...)]
    assert closes == [(repo, 12)]
```

- [ ] **Step 2: Run the auto-close pipeline test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_auto_closes_consumed_issues -v`
Expected: FAIL because the pipeline does not trigger issue closing yet

- [ ] **Step 3: Write a failing test that existing manual profiles skip auto-close**

```python
def test_run_daily_pipeline_skips_auto_close_with_existing_profile(tmp_path, monkeypatch) -> None:
    ...
    assert comments == []
    assert closes == []
```

- [ ] **Step 4: Run the manual-profile test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_skips_auto_close_with_existing_profile -v`
Expected: FAIL because the skip behavior is not wired yet

- [ ] **Step 5: Implement fallback metadata plumbing and success-only auto-close trigger**

```python
def _auto_close_consumed_issues(...):
    ...
```

- [ ] **Step 6: Run focused pipeline tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_auto_closes_consumed_issues tests/test_automation.py::test_run_daily_pipeline_skips_auto_close_with_existing_profile -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py tests/test_automation.py
git commit -m "feat: auto close consumed github issues after summary"
```

### Task 3: Add failure-tolerance tests before refining behavior

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/automation.py`

- [ ] **Step 1: Write a failing test that comment failure skips close and does not fail the run**

```python
def test_run_daily_pipeline_tolerates_issue_comment_failure(tmp_path, monkeypatch) -> None:
    ...
```

- [ ] **Step 2: Run the comment-failure test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_tolerates_issue_comment_failure -v`
Expected: FAIL because failure handling is not implemented yet

- [ ] **Step 3: Write a failing test that close failure does not fail the run**

```python
def test_run_daily_pipeline_tolerates_issue_close_failure(tmp_path, monkeypatch) -> None:
    ...
```

- [ ] **Step 4: Run the close-failure test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_tolerates_issue_close_failure -v`
Expected: FAIL because best-effort warnings are not implemented yet

- [ ] **Step 5: Implement warning-based failure tolerance**

```python
try:
    comment_on_issue(...)
except Exception as exc:
    warnings.append(...)
    continue
```

- [ ] **Step 6: Run focused failure-tolerance tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_tolerates_issue_comment_failure tests/test_automation.py::test_run_daily_pipeline_tolerates_issue_close_failure -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py tests/test_automation.py
git commit -m "test: cover best effort issue auto close"
```

### Task 4: Update docs and run full targeted verification

**Files:**
- Modify: `README.md`
- Modify: `docs/local-automation-usage.md`

- [ ] **Step 1: Update docs to explain that fallback-consumed issues are commented on and closed after a successful run**

```md
When `daily-pipeline` auto-generates a missing profile from `issue-intake/`, a successful run can comment on and close the consumed issues.
```

- [ ] **Step 2: Run the full targeted verification suite**

Run: `PYTHONPATH=src pytest tests/test_profile.py tests/test_github_intake.py tests/test_automation.py tests/test_cli_smoke.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add README.md docs/local-automation-usage.md src/auto_research/github_intake.py src/auto_research/automation.py tests/test_github_intake.py tests/test_automation.py
git commit -m "docs: describe issue auto close after summary"
```
