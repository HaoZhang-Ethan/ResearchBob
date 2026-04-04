# Finalize GitHub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split GitHub push/comment/close out of `daily-pipeline` into a new `finalize-github` command, with a persisted `research-workspace/pipeline/github-finalize.json` state file so summarize-time and GitHub-time can run in different network environments.

**Architecture:** Have `daily-pipeline` write pending finalize metadata after a successful fallback-driven run, then add a dedicated finalize path in `automation.py` and expose it through `cli.py`. Reuse the existing GitHub comment/close helpers and keep finalize state deterministic and retryable.

**Tech Stack:** Python 3.12, standard library `json`/`subprocess`/`pathlib`, existing `auto_research` modules, pytest

---

### Task 1: Add failing tests for finalize state creation

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/automation.py`

- [ ] **Step 1: Write a failing test that fallback-driven pipeline runs create `github-finalize.json`**

```python
def test_run_daily_pipeline_writes_pending_finalize_state(tmp_path, monkeypatch) -> None:
    ...
    run_daily_pipeline(...)
    finalize_path = workspace / "pipeline" / "github-finalize.json"
    assert finalize_path.exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_writes_pending_finalize_state -v`
Expected: FAIL because the state file is not written yet

- [ ] **Step 3: Write a failing test that manual-profile runs do not create finalize state**

```python
def test_run_daily_pipeline_without_fallback_skips_finalize_state(tmp_path, monkeypatch) -> None:
    ...
    assert not (workspace / "pipeline" / "github-finalize.json").exists()
```

- [ ] **Step 4: Run the manual-profile state test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_without_fallback_skips_finalize_state -v`
Expected: FAIL because finalize state behavior is not implemented yet

- [ ] **Step 5: Implement finalize-state writing helpers**

```python
def _write_github_finalize_state(...):
    ...
```

- [ ] **Step 6: Run focused tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_writes_pending_finalize_state tests/test_automation.py::test_run_daily_pipeline_without_fallback_skips_finalize_state -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py tests/test_automation.py
git commit -m "feat: persist pending github finalize state"
```

### Task 2: Add failing tests for `finalize-github` execution path

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/automation.py`

- [ ] **Step 1: Write a failing test that finalize runs push, comment, close, and marks state completed**

```python
def test_finalize_github_runs_push_then_issue_updates(tmp_path, monkeypatch) -> None:
    ...
```

- [ ] **Step 2: Run the finalize success test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_finalize_github_runs_push_then_issue_updates -v`
Expected: FAIL because `finalize_github()` does not exist yet

- [ ] **Step 3: Write a failing test that missing finalize state errors clearly**

```python
def test_finalize_github_fails_when_state_missing(tmp_path) -> None:
    ...
```

- [ ] **Step 4: Run the missing-state test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_finalize_github_fails_when_state_missing -v`
Expected: FAIL because the command path is not implemented yet

- [ ] **Step 5: Implement `finalize_github()` and state loading/updating**

```python
def finalize_github(workspace: Path) -> dict[str, object]:
    ...
```

- [ ] **Step 6: Run focused finalize tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_finalize_github_runs_push_then_issue_updates tests/test_automation.py::test_finalize_github_fails_when_state_missing -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py tests/test_automation.py
git commit -m "feat: add finalize github command path"
```

### Task 3: Add failing tests for retry and failure rules

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/automation.py`

- [ ] **Step 1: Write a failing test that completed finalize state does not repeat work**

```python
def test_finalize_github_skips_completed_state(tmp_path, monkeypatch) -> None:
    ...
```

- [ ] **Step 2: Run the completed-state test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_finalize_github_skips_completed_state -v`
Expected: FAIL because completed-state handling is not implemented yet

- [ ] **Step 3: Write a failing test that push failure keeps state pending and skips issue actions**

```python
def test_finalize_github_push_failure_leaves_state_pending(tmp_path, monkeypatch) -> None:
    ...
```

- [ ] **Step 4: Run the push-failure test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_finalize_github_push_failure_leaves_state_pending -v`
Expected: FAIL because push-failure behavior is not implemented yet

- [ ] **Step 5: Implement completed-state and push-failure handling**

```python
if state["status"] == "completed":
    return ...
```

- [ ] **Step 6: Run focused retry tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_finalize_github_skips_completed_state tests/test_automation.py::test_finalize_github_push_failure_leaves_state_pending -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py tests/test_automation.py
git commit -m "test: cover github finalize retry rules"
```

### Task 4: Wire CLI and refresh docs

**Files:**
- Modify: `src/auto_research/cli.py`
- Modify: `tests/test_cli_smoke.py`
- Modify: `README.md`
- Modify: `docs/local-automation-usage.md`

- [ ] **Step 1: Write failing CLI tests for `finalize-github`**

```python
def test_finalize_github_cli_runs(monkeypatch, capsys, tmp_path) -> None:
    ...
```

- [ ] **Step 2: Run the CLI tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_cli_smoke.py::test_finalize_github_cli_runs tests/test_cli_smoke.py::test_build_parser_includes_finalize_github_command -v`
Expected: FAIL because the CLI command is not registered yet

- [ ] **Step 3: Implement CLI wiring and update docs**

```python
finalize_parser = subparsers.add_parser("finalize-github")
finalize_parser.add_argument("--workspace", default="research-workspace")
```

- [ ] **Step 4: Run the full targeted verification suite**

Run: `PYTHONPATH=src pytest tests/test_profile.py tests/test_github_intake.py tests/test_automation.py tests/test_cli_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_research/cli.py tests/test_cli_smoke.py README.md docs/local-automation-usage.md src/auto_research/automation.py tests/test_automation.py
git commit -m "docs: add finalize github workflow"
```
