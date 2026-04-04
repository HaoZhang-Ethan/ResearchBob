# Issue Intake Profile Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `daily-pipeline` automatically generate `research-workspace/profile/interest-profile.md` from `research-workspace/issue-intake/` when the profile file is missing, then continue the pipeline without overwriting an existing manual profile.

**Architecture:** Add deterministic issue-intake readers and profile rendering helpers in `github_intake.py`, then call them from a small preflight hook in `automation.py` before the pipeline loads the profile. Reuse the existing profile validator so the generated profile stays compatible with the rest of the workflow.

**Tech Stack:** Python 3.12, standard library `json`/`pathlib`/`datetime`, existing `auto_research` modules, pytest

---

### Task 1: Add failing tests for fallback profile generation primitives

**Files:**
- Modify: `tests/test_github_intake.py`
- Modify: `tests/test_profile.py`
- Modify: `src/auto_research/github_intake.py`

- [ ] **Step 1: Write a failing test for rendering a valid profile from issue-intake directories**

```python
def test_render_profile_from_issue_intake_summaries(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    summary_dir = workspace / "issue-intake" / "llm-agents" / "alice"
    (summary_dir / "requests").mkdir(parents=True, exist_ok=True)
    (summary_dir / "summary.md").write_text(...)

    markdown = render_profile_from_issue_intake(workspace)

    assert validate_interest_profile_text(markdown) == []
    assert "llm-agents / alice" in markdown
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_render_profile_from_issue_intake_summaries -v`
Expected: FAIL because the rendering helper does not exist yet

- [ ] **Step 3: Write a failing test for empty issue-intake fallback**

```python
def test_render_profile_from_issue_intake_rejects_empty_workspace(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    with pytest.raises(ValueError, match="issue intake"):
        render_profile_from_issue_intake(workspace)
```

- [ ] **Step 4: Run the empty-workspace test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_render_profile_from_issue_intake_rejects_empty_workspace -v`
Expected: FAIL because the fallback helper does not exist yet

- [ ] **Step 5: Implement the minimal issue-intake reader and profile renderer**

```python
def render_profile_from_issue_intake(workspace: Path) -> str:
    ...
```

- [ ] **Step 6: Run focused tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_render_profile_from_issue_intake_summaries tests/test_github_intake.py::test_render_profile_from_issue_intake_rejects_empty_workspace -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/github_intake.py tests/test_github_intake.py tests/test_profile.py
git commit -m "feat: render fallback profile from issue intake"
```

### Task 2: Add daily-pipeline fallback coverage before implementation

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/automation.py`

- [ ] **Step 1: Write a failing pipeline test for missing profile plus available issue-intake**

```python
def test_run_daily_pipeline_generates_profile_from_issue_intake(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    ...
    result = run_daily_pipeline(...)
    assert (workspace / "profile" / "interest-profile.md").exists()
```

- [ ] **Step 2: Run the pipeline fallback test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_generates_profile_from_issue_intake -v`
Expected: FAIL because the pipeline still requires a pre-existing profile file

- [ ] **Step 3: Write a failing pipeline test for missing profile and empty issue-intake**

```python
def test_run_daily_pipeline_fails_when_profile_missing_and_no_issue_intake(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)

    with pytest.raises(ValueError, match="issue intake"):
        run_daily_pipeline(...)
```

- [ ] **Step 4: Run the empty-input pipeline test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_fails_when_profile_missing_and_no_issue_intake -v`
Expected: FAIL with the current missing-file behavior or because the new fallback hook is absent

- [ ] **Step 5: Implement the preflight fallback hook in the pipeline**

```python
def _ensure_profile_exists(workspace: Path, profile_path: Path) -> Path:
    ...
```

- [ ] **Step 6: Run focused pipeline tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_generates_profile_from_issue_intake tests/test_automation.py::test_run_daily_pipeline_fails_when_profile_missing_and_no_issue_intake -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py tests/test_automation.py
git commit -m "feat: add daily pipeline profile fallback"
```

### Task 3: Add overwrite protection and validation coverage

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `tests/test_github_intake.py`
- Modify: `src/auto_research/automation.py`
- Modify: `src/auto_research/github_intake.py`

- [ ] **Step 1: Write a failing test that existing manual profiles are not overwritten**

```python
def test_run_daily_pipeline_preserves_existing_profile(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    profile_path = workspace / "profile" / "interest-profile.md"
    profile_path.write_text(valid_profile_text, encoding="utf-8")
    ...
    run_daily_pipeline(...)
    assert profile_path.read_text(encoding="utf-8") == valid_profile_text
```

- [ ] **Step 2: Run the overwrite-protection test to verify behavior**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_preserves_existing_profile -v`
Expected: PASS only after fallback logic correctly checks file existence before generation

- [ ] **Step 3: Write a failing test that generated profile text is validated before use**

```python
def test_ensure_profile_exists_rejects_invalid_generated_profile(tmp_path, monkeypatch) -> None:
    ...
```

- [ ] **Step 4: Run the validation test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_ensure_profile_exists_rejects_invalid_generated_profile -v`
Expected: FAIL because validation enforcement is not wired yet

- [ ] **Step 5: Implement validation and overwrite protection refinements**

```python
errors = validate_interest_profile_text(markdown)
if errors:
    raise ValueError(...)
```

- [ ] **Step 6: Run focused protection tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_preserves_existing_profile tests/test_automation.py::test_ensure_profile_exists_rejects_invalid_generated_profile -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py src/auto_research/github_intake.py tests/test_automation.py tests/test_github_intake.py
git commit -m "test: cover profile fallback protections"
```

### Task 4: Refresh docs and run full targeted verification

**Files:**
- Modify: `README.md`
- Modify: `docs/local-automation-usage.md`

- [ ] **Step 1: Update docs to explain automatic profile generation on missing profile**

```md
If `research-workspace/profile/interest-profile.md` is missing, `daily-pipeline` will try to generate it from `issue-intake/`.
```

- [ ] **Step 2: Run the full targeted verification suite**

Run: `PYTHONPATH=src pytest tests/test_profile.py tests/test_github_intake.py tests/test_automation.py tests/test_cli_smoke.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add README.md docs/local-automation-usage.md src/auto_research/github_intake.py src/auto_research/automation.py tests/test_profile.py tests/test_github_intake.py tests/test_automation.py tests/test_cli_smoke.py
git commit -m "docs: describe issue-intake profile fallback"
```
