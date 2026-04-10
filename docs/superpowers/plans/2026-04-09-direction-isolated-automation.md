# Direction-Isolated Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the GitHub-issue-driven automation flow write each direction's profile, papers, reports, exports, and finalize state into the direction-local subtree rooted at `research-workspace/directions/<direction>/` instead of shared global directories.

**Architecture:** Keep `issue-intake/` as the shared inbound request area, add a direction execution-root helper in `workspace.py`, and route direction-aware automation through that root. Scope fallback profile generation to one direction at a time in `github_intake.py`, then thread the chosen direction through `automation.py` and the CLI so existing lower-level helpers like `run_intake()` and `compose_report()` can keep working unchanged against the direction-local workspace.

**Tech Stack:** Python 3.12, standard library `argparse`/`json`/`pathlib`, existing `auto_research` modules, pytest

---

## File Structure

- Modify: `src/auto_research/workspace.py`
  Add shared-vs-direction workspace directory helpers and keep symlink protections consistent.
- Modify: `src/auto_research/github_intake.py`
  Add direction discovery/resolution helpers and direction-scoped fallback profile generation.
- Modify: `src/auto_research/automation.py`
  Add direction-aware pipeline resolution, direction-local output paths, and direction-local finalize state handling.
- Modify: `src/auto_research/cli.py`
  Add `--direction` options to direction-sensitive commands and route them to the direction execution root.
- Modify: `tests/test_workspace.py`
  Cover `directions/` root creation and direction-local directory initialization.
- Modify: `tests/test_github_intake.py`
  Cover usable direction discovery and single-direction fallback profile generation.
- Modify: `tests/test_automation.py`
  Cover direction-local outputs, ambiguity failures, auto-selection for a single direction, and direction-local finalize state.
- Modify: `tests/test_cli_smoke.py`
  Cover parser/CLI wiring for `--direction`.
- Modify: `README.md`
  Document the new direction-local output layout and command usage.
- Modify: `docs/local-automation-usage.md`
  Update GitHub issue automation examples to show direction-local outputs.

### Task 1: Add direction workspace helpers

**Files:**
- Modify: `src/auto_research/workspace.py`
- Modify: `tests/test_workspace.py`

- [ ] **Step 1: Write a failing test for creating a direction execution root**

```python
def test_ensure_direction_workspace_creates_direction_local_directories(tmp_path) -> None:
    root = ensure_direction_workspace(tmp_path / "research-workspace", "llm-agents")

    assert root == tmp_path / "research-workspace" / "directions" / "llm-agents"
    assert (root / "profile").is_dir()
    assert (root / "papers").is_dir()
    assert (root / "reports" / "daily").is_dir()
    assert (root / "reports" / "manual").is_dir()
    assert (root / "reports" / "longterm").is_dir()
    assert (root / "exports" / "zotero").is_dir()
    assert (root / "pipeline").is_dir()
```

- [ ] **Step 2: Run the workspace test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_workspace.py::test_ensure_direction_workspace_creates_direction_local_directories -v`
Expected: FAIL because `ensure_direction_workspace` does not exist yet

- [ ] **Step 3: Write a failing test that the shared workspace now includes the `directions` root**

```python
def test_ensure_workspace_creates_shared_and_direction_roots(tmp_path) -> None:
    root = ensure_workspace(tmp_path / "research-workspace")

    assert (root / "issue-intake").is_dir()
    assert (root / "directions").is_dir()
```

- [ ] **Step 4: Run both workspace tests to verify the shared-root behavior is still incomplete**

Run: `PYTHONPATH=src pytest tests/test_workspace.py::test_ensure_workspace_creates_shared_and_direction_roots tests/test_workspace.py::test_ensure_direction_workspace_creates_direction_local_directories -v`
Expected: FAIL because the shared workspace helper does not create `directions/` and the direction helper is missing

- [ ] **Step 5: Implement the minimal direction workspace helper**

```python
PHASE1_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
    "issue-intake",
    "directions",
)

DIRECTION_WORKSPACE_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
    "reports/longterm",
    "exports/zotero",
    "pipeline",
)


def ensure_direction_workspace(root: Path, direction: str) -> Path:
    workspace = ensure_workspace(root)
    direction_root = workspace / "directions" / direction

    for relative_path in DIRECTION_WORKSPACE_DIRECTORIES:
        current = direction_root
        for part in Path(relative_path).parts:
            current = current / part
            if current.is_symlink():
                raise OSError(f"Refusing to use symlinked workspace directory: {current}")
            current.mkdir(parents=True, exist_ok=True)

    return direction_root
```

- [ ] **Step 6: Run the focused workspace tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_workspace.py::test_ensure_workspace_creates_shared_and_direction_roots tests/test_workspace.py::test_ensure_direction_workspace_creates_direction_local_directories -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/workspace.py tests/test_workspace.py
git commit -m "feat: add direction workspace helper"
```

### Task 2: Scope GitHub intake fallback to one direction

**Files:**
- Modify: `src/auto_research/github_intake.py`
- Modify: `tests/test_github_intake.py`

- [ ] **Step 1: Write a failing test for discovering usable issue directions**

```python
def test_discover_issue_directions_returns_only_usable_direction_roots(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    usable = workspace / "issue-intake" / "llm-agents" / "alice"
    ignored = workspace / "issue-intake" / "robotics" / "bob"
    (usable / "requests").mkdir(parents=True, exist_ok=True)
    (usable / "summary.md").write_text("# Issue Intake Summary: llm-agents / alice\n", encoding="utf-8")
    ignored.mkdir(parents=True, exist_ok=True)

    assert discover_issue_directions(workspace) == ["llm-agents"]
```

- [ ] **Step 2: Run the discovery test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_discover_issue_directions_returns_only_usable_direction_roots -v`
Expected: FAIL because `discover_issue_directions` does not exist yet

- [ ] **Step 3: Write a failing test for single-direction fallback profile generation**

```python
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
    (llm_dir / "12.md").write_text("issue_number: 12\n", encoding="utf-8")
    (robo_dir / "34.md").write_text("issue_number: 34\n", encoding="utf-8")

    result = build_fallback_profile_from_issue_intake(
        workspace,
        direction="llm-agents",
        repo="example/research",
    )

    assert "llm-agents / alice" in result.markdown
    assert "robotics / bob" not in result.markdown
    assert result.issue_numbers == [12]
    assert result.source_keys == ["llm-agents/alice"]
```

- [ ] **Step 4: Run the fallback test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_build_fallback_profile_from_issue_intake_uses_only_requested_direction -v`
Expected: FAIL because the current fallback helper aggregates all directions and does not accept a `direction` parameter

- [ ] **Step 5: Implement direction discovery and direction-scoped fallback helpers**

```python
@dataclass(slots=True)
class FallbackProfileResult:
    markdown: str
    repo: str | None
    issue_numbers: list[int]
    source_keys: list[str]
    direction: str


def discover_issue_directions(workspace: Path) -> list[str]:
    issue_root = workspace / "issue-intake"
    if not issue_root.exists():
        return []
    directions: list[str] = []
    for direction_dir in sorted(path for path in issue_root.iterdir() if path.is_dir()):
        if any((user_dir / "summary.md").exists() for user_dir in direction_dir.iterdir() if user_dir.is_dir()):
            directions.append(direction_dir.name)
    return directions


def build_fallback_profile_from_issue_intake(
    workspace: Path,
    direction: str,
    repo: str | None = None,
) -> FallbackProfileResult:
    sources = _collect_issue_intake_sources(workspace, direction)
    if not sources:
        raise ValueError(f"No usable issue intake data available for direction: {direction}")
    source_lines = [f"> - {source_direction} / {username}" for source_direction, username, _ in sources]
    source_keys = [f"{source_direction}/{username}" for source_direction, username, _ in sources]
    issue_numbers: list[int] = []
    for source_direction, username, _ in sources:
        issue_numbers.extend(
            _collect_issue_numbers_for_source(workspace / "issue-intake" / source_direction / username)
        )
    markdown = "\n".join(
        [
            "# Research Interest Profile",
            "",
            f"> Auto-generated from GitHub issue intake on {_utc_now_iso()}.",
            "> Sources:",
            *source_lines,
            "",
            "## Core Interests",
            f"- {direction}",
            "",
            "## Soft Boundaries",
            "- adjacent topics inferred from issue intake",
            "",
            "## Exclusions",
            "- no explicit exclusions were provided in issue intake",
            "",
            "## Current-Phase Bias",
            f"- focus on the active {direction} issue direction",
            "",
            "## Evaluation Heuristics",
            "- prefer papers aligned with the current issue-intake requests",
            "",
            "## Open Questions",
            "- which requested papers should be prioritized next",
            "",
        ]
    )
    return FallbackProfileResult(
        markdown=markdown,
        repo=repo,
        issue_numbers=sorted(set(issue_numbers)),
        source_keys=source_keys,
        direction=direction,
    )
```

- [ ] **Step 6: Run the focused GitHub intake tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_github_intake.py::test_discover_issue_directions_returns_only_usable_direction_roots tests/test_github_intake.py::test_build_fallback_profile_from_issue_intake_uses_only_requested_direction -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/github_intake.py tests/test_github_intake.py
git commit -m "feat: scope issue fallback by direction"
```

### Task 3: Make the daily pipeline direction-aware

**Files:**
- Modify: `src/auto_research/automation.py`
- Modify: `tests/test_automation.py`

- [ ] **Step 1: Write a failing test for direction-local daily pipeline outputs**

```python
def test_run_daily_pipeline_writes_outputs_under_direction_workspace(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    direction_root = workspace / "directions" / "llm-agents"
    profile_path = direction_root / "profile" / "interest-profile.md"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """# Research Interest Profile

## Core Interests
- llm agents

## Soft Boundaries
- orchestration

## Exclusions
- pure benchmark papers

## Current-Phase Bias
- strong system design

## Evaluation Heuristics
- prefer recent papers

## Open Questions
- how should agent memory be structured?
""",
        encoding="utf-8",
    )
    entry = RegistryEntry(
        arxiv_id="2603.23566v1",
        title="AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization",
        summary="Operator optimization on Ascend NPUs.",
        pdf_url="https://arxiv.org/pdf/2603.23566v1",
        published_at="2026-03-24T08:54:53Z",
        updated_at="2026-03-24T08:54:53Z",
        relevance_band="high-match",
        source="arxiv",
    )

    monkeypatch.setattr("auto_research.automation.run_intake", lambda **kwargs: [entry])
    monkeypatch.setattr("auto_research.automation.download_pdf", lambda **kwargs: kwargs["destination"].write_bytes(b"%PDF-1.4\nExample text\n"))
    monkeypatch.setattr(
        "auto_research.automation.build_detailed_analysis",
        lambda **kwargs: (
            "Example extracted PDF text",
            {
                "one_paragraph_summary": "Detailed summary.",
                "problem": "Detailed problem.",
                "solution": "Detailed solution.",
                "key_mechanism": "Detailed mechanism.",
                "assumptions": "Detailed assumptions.",
                "strengths": "Detailed strengths.",
                "weaknesses": "Detailed weaknesses.",
                "what_is_missing": "Detailed missing.",
                "why_it_matters": "Detailed relevance.",
                "follow_up_ideas": "Detailed follow-up.",
            },
        ),
    )

    result = run_daily_pipeline(
        PipelineConfig(
            workspace=workspace,
            direction="llm-agents",
            top_k=1,
            prefilter_limit=5,
            max_results=5,
            label="2026-04-09",
        ),
        llm_client=FakeLLMClient(),
    )

    assert result.report_path == direction_root / "reports" / "daily" / "2026-04-09.md"
    assert result.ris_path == direction_root / "exports" / "zotero" / "2026-04-09.ris"
    assert result.history_path == direction_root / "pipeline" / "run-history.jsonl"
```

- [ ] **Step 2: Run the direction-local output test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_writes_outputs_under_direction_workspace -v`
Expected: FAIL because `PipelineConfig` has no `direction` field and the pipeline still writes into the shared root

- [ ] **Step 3: Write a failing test for ambiguous direction resolution**

```python
def test_run_daily_pipeline_requires_direction_when_multiple_issue_directions_exist(tmp_path) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    (workspace / "issue-intake" / "llm-agents" / "alice").mkdir(parents=True, exist_ok=True)
    (workspace / "issue-intake" / "llm-agents" / "alice" / "summary.md").write_text("# Issue Intake Summary\n", encoding="utf-8")
    (workspace / "issue-intake" / "robotics" / "bob").mkdir(parents=True, exist_ok=True)
    (workspace / "issue-intake" / "robotics" / "bob" / "summary.md").write_text("# Issue Intake Summary\n", encoding="utf-8")

    with pytest.raises(ValueError, match="--direction"):
        run_daily_pipeline(PipelineConfig(workspace=workspace, label="2026-04-09"), llm_client=FakeLLMClient())
```

- [ ] **Step 4: Run the ambiguity test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_requires_direction_when_multiple_issue_directions_exist -v`
Expected: FAIL because the pipeline has no direction-resolution guard yet

- [ ] **Step 5: Implement direction resolution and route all output paths through the direction execution root**

```python
@dataclass(slots=True)
class PipelineConfig:
    workspace: Path
    direction: str | None = None
    profile_path: Path | None = None
    max_results: int = 20
    prefilter_limit: int = 15
    top_k: int = 10
    label: str | None = None
    model: str | None = None
    overwrite_summaries: bool = False
    push: bool = False


def _resolve_run_direction(workspace: Path, requested_direction: str | None) -> str:
    if requested_direction:
        return requested_direction
    directions = discover_issue_directions(workspace)
    if len(directions) == 1:
        return directions[0]
    if not directions:
        raise ValueError("No usable issue directions found; pass --direction")
    raise ValueError("Multiple issue directions found; pass --direction")


def run_daily_pipeline(
    config: PipelineConfig,
    *,
    llm_client: OpenAIResponsesClient | None = None,
) -> PipelineResult:
    shared_workspace = ensure_workspace(config.workspace)
    direction = _resolve_run_direction(shared_workspace, config.direction)
    execution_workspace = ensure_direction_workspace(shared_workspace, direction)
    profile_path = config.profile_path or execution_workspace / "profile" / "interest-profile.md"
    profile_path, fallback = _ensure_profile_exists_with_metadata(
        shared_workspace,
        execution_workspace,
        direction,
        profile_path,
    )
    profile = load_interest_profile(profile_path)
    intake_entries = run_intake(
        workspace=execution_workspace,
        profile_path=profile_path,
        max_results=config.max_results,
    )
    report_path = compose_report(workspace=execution_workspace, mode="daily", label=label)
    ris_path = export_ris(selected_entries, execution_workspace / "exports" / "zotero" / f"{label}.ris")
```

- [ ] **Step 6: Run the focused pipeline resolution tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_writes_outputs_under_direction_workspace tests/test_automation.py::test_run_daily_pipeline_requires_direction_when_multiple_issue_directions_exist -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py tests/test_automation.py
git commit -m "feat: route pipeline outputs by direction"
```

### Task 4: Scope fallback profile generation and GitHub finalize state to the chosen direction

**Files:**
- Modify: `src/auto_research/automation.py`
- Modify: `tests/test_automation.py`

- [ ] **Step 1: Write a failing test for fallback profile generation into the direction workspace**

```python
def test_run_daily_pipeline_generates_profile_from_requested_direction_issue_intake(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_workspace(workspace)
    request_dir = workspace / "issue-intake" / "llm-agents" / "alice" / "requests"
    request_dir.mkdir(parents=True, exist_ok=True)
    (request_dir.parent / "summary.md").write_text(
        """# Issue Intake Summary: llm-agents / alice

- Direction: `llm-agents`
- GitHub Username: `alice`
- Request Count: 1

## Active Issues
- #12: Track multi-agent papers (OPEN)

## Requirements
- prefer strong system design
""",
        encoding="utf-8",
    )
    (workspace / "issue-intake" / "robotics" / "bob" / "requests").mkdir(parents=True, exist_ok=True)
    ((workspace / "issue-intake" / "robotics" / "bob") / "summary.md").write_text(
        """# Issue Intake Summary: robotics / bob

- Direction: `robotics`
- GitHub Username: `bob`
- Request Count: 1

## Active Issues
- #34: Track robot grasping papers (OPEN)
""",
        encoding="utf-8",
    )
    entry = RegistryEntry(
        arxiv_id="2603.23566v1",
        title="AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization",
        summary="Operator optimization on Ascend NPUs.",
        pdf_url="https://arxiv.org/pdf/2603.23566v1",
        published_at="2026-03-24T08:54:53Z",
        updated_at="2026-03-24T08:54:53Z",
        relevance_band="high-match",
        source="arxiv",
    )

    monkeypatch.setattr("auto_research.automation.run_intake", lambda **kwargs: [entry])
    monkeypatch.setattr("auto_research.automation.download_pdf", lambda **kwargs: kwargs["destination"].write_bytes(b"%PDF-1.4\nExample text\n"))
    monkeypatch.setattr(
        "auto_research.automation.build_detailed_analysis",
        lambda **kwargs: (
            "Example extracted PDF text",
            {
                "one_paragraph_summary": "Detailed summary.",
                "problem": "Detailed problem.",
                "solution": "Detailed solution.",
                "key_mechanism": "Detailed mechanism.",
                "assumptions": "Detailed assumptions.",
                "strengths": "Detailed strengths.",
                "weaknesses": "Detailed weaknesses.",
                "what_is_missing": "Detailed missing.",
                "why_it_matters": "Detailed relevance.",
                "follow_up_ideas": "Detailed follow-up.",
            },
        ),
    )

    run_daily_pipeline(
        PipelineConfig(workspace=workspace, direction="llm-agents", top_k=1, prefilter_limit=5, max_results=5, label="2026-04-09"),
        llm_client=FakeLLMClient(),
    )

    profile_path = workspace / "directions" / "llm-agents" / "profile" / "interest-profile.md"
    assert profile_path.exists()
    assert "llm-agents / alice" in profile_path.read_text(encoding="utf-8")
    assert "robotics / bob" not in profile_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the fallback profile test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_generates_profile_from_requested_direction_issue_intake -v`
Expected: FAIL because the automation fallback still targets the shared profile path and does not pass `direction` into the fallback builder

- [ ] **Step 3: Write a failing test for direction-local GitHub finalize state**

```python
def test_finalize_github_reads_direction_local_state(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    ensure_direction_workspace(workspace, "llm-agents")
    state_path = workspace / "directions" / "llm-agents" / "pipeline" / "github-finalize.json"
    state_path.write_text(
        """{
  "direction": "llm-agents",
  "label": "2026-04-09",
  "repo": "example/research",
  "report_path": "/tmp/report.md",
  "daily_summary_path": "/tmp/summary.md",
  "used_fallback_profile": true,
  "consumed_issue_numbers": [12],
  "source_keys": ["llm-agents/alice"],
  "status": "pending",
  "created_at": "2026-04-09T00:00:00Z",
  "finalized_at": ""
}
""",
        encoding="utf-8",
    )
    calls = []

    monkeypatch.setattr("auto_research.automation.subprocess.run", lambda cmd, cwd, check: calls.append(("push", cmd)) or None)
    monkeypatch.setattr("auto_research.automation.comment_on_issue", lambda *, repo, issue_number, body: calls.append(("comment", repo, issue_number)))
    monkeypatch.setattr("auto_research.automation.close_issue", lambda *, repo, issue_number: calls.append(("close", repo, issue_number)))

    result = finalize_github(workspace, direction="llm-agents")

    assert result["status"] == "completed"
    assert calls[0] == ("push", ["git", "push"])
    assert calls[1] == ("comment", "example/research", 12)
    assert calls[2] == ("close", "example/research", 12)
```

- [ ] **Step 4: Run the finalize-state test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_finalize_github_reads_direction_local_state -v`
Expected: FAIL because `finalize_github()` still reads the shared `pipeline/github-finalize.json` path and does not accept `direction`

- [ ] **Step 5: Implement direction-scoped fallback writes and finalize-state reads**

```python
def _ensure_profile_exists_with_metadata(
    workspace: Path,
    execution_workspace: Path,
    direction: str,
    profile_path: Path,
) -> tuple[Path, object | None]:
    if profile_path.exists():
        return profile_path, None
    repo = discover_github_repo()
    fallback = build_fallback_profile_from_issue_intake(workspace, direction=direction, repo=repo)
    errors = validate_interest_profile_text(fallback.markdown)
    if errors:
        raise ValueError("Generated invalid fallback interest profile: " + "; ".join(errors))
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(fallback.markdown, encoding="utf-8")
    return profile_path, fallback


def _github_finalize_state_path(execution_workspace: Path) -> Path:
    return execution_workspace / "pipeline" / "github-finalize.json"


def finalize_github(workspace: Path, direction: str | None = None) -> dict[str, object]:
    shared_workspace = ensure_workspace(workspace)
    resolved_direction = _resolve_run_direction(shared_workspace, direction)
    execution_workspace = ensure_direction_workspace(shared_workspace, resolved_direction)
    state_path = _github_finalize_state_path(execution_workspace)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") == "completed":
        return state
    repo_root = shared_workspace.parent if shared_workspace.name == "research-workspace" else Path.cwd()
    subprocess.run(["git", "push"], cwd=repo_root, check=True)
    for issue_number in state.get("consumed_issue_numbers", []):
        comment_on_issue(repo=str(state["repo"]), issue_number=int(issue_number), body="direction-local finalize")
        close_issue(repo=str(state["repo"]), issue_number=int(issue_number))
    state["status"] = "completed"
    state["finalized_at"] = utc_now_iso()
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state
```

- [ ] **Step 6: Run the focused fallback/finalize tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_generates_profile_from_requested_direction_issue_intake tests/test_automation.py::test_finalize_github_reads_direction_local_state -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/auto_research/automation.py tests/test_automation.py
git commit -m "feat: isolate fallback and finalize by direction"
```

### Task 5: Add CLI flags, update docs, and run targeted verification

**Files:**
- Modify: `src/auto_research/cli.py`
- Modify: `tests/test_cli_smoke.py`
- Modify: `README.md`
- Modify: `docs/local-automation-usage.md`

- [ ] **Step 1: Write a failing CLI test for forwarding `--direction` to `daily-pipeline`**

```python
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
```

- [ ] **Step 2: Run the CLI forwarding test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_cli_smoke.py::test_daily_pipeline_cli_passes_direction -v`
Expected: FAIL because the parser does not accept `--direction` and `PipelineConfig` is not populated from the CLI

- [ ] **Step 3: Write a failing CLI test for forwarding `--direction` to `finalize-github`**

```python
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
```

- [ ] **Step 4: Run both CLI tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_cli_smoke.py::test_daily_pipeline_cli_passes_direction tests/test_cli_smoke.py::test_finalize_github_cli_passes_direction -v`
Expected: FAIL because the parser and command wiring do not yet support `--direction`

- [ ] **Step 5: Implement CLI flags and wiring**

```python
compose.add_argument("--direction")
pipeline.add_argument("--direction")
finalize_parser.add_argument("--direction")

if args.command == "daily-pipeline":
    result = run_daily_pipeline(
        PipelineConfig(
            workspace=Path(args.workspace),
            direction=args.direction,
            profile_path=(Path(args.profile) if _profile_path_was_overridden(raw_argv) else None),
            max_results=args.max_results,
            prefilter_limit=args.prefilter_limit,
            top_k=args.top_k,
            label=args.label,
            model=args.model,
            overwrite_summaries=args.overwrite_summaries,
            push=args.push,
        )
    )
    print(result.report_path)
    print(result.ris_path)
    return 0

if args.command == "finalize-github":
    result = finalize_github(Path(args.workspace), direction=args.direction)
    print(
        " ".join(
            [
                f"status={result.get('status', '')}",
                f"label={result.get('label', '')}",
                f"consumed_issues={len(result.get('consumed_issue_numbers', []))}",
            ]
        )
    )
    return 0
```

- [ ] **Step 6: Update the docs to show direction-local paths and commands**

```md
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace --direction llm-agents

Generated artifacts now land under:

- `research-workspace/directions/llm-agents/profile/`
- `research-workspace/directions/llm-agents/papers/`
- `research-workspace/directions/llm-agents/reports/`
- `research-workspace/directions/llm-agents/exports/zotero/`
```

- [ ] **Step 7: Run the targeted verification suite**

Run: `PYTHONPATH=src pytest tests/test_workspace.py tests/test_github_intake.py tests/test_automation.py tests/test_cli_smoke.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/auto_research/cli.py tests/test_cli_smoke.py README.md docs/local-automation-usage.md src/auto_research/workspace.py src/auto_research/github_intake.py src/auto_research/automation.py tests/test_workspace.py tests/test_github_intake.py tests/test_automation.py
git commit -m "docs: describe direction-isolated automation"
```

## Self-Review

- **Spec coverage:** Task 1 covers the new directory model, Task 2 covers single-direction fallback generation, Task 3 covers direction-local outputs and ambiguity handling, Task 4 covers direction-local finalize state and fallback writes, and Task 5 covers CLI/documentation updates.
- **Placeholder scan:** No `TODO`, `TBD`, or "implement later" placeholders remain; every code-changing step includes concrete code or test snippets and exact commands.
- **Type consistency:** The plan consistently uses `direction: str | None` on `PipelineConfig` and `finalize_github()`, and `direction: str` on `build_fallback_profile_from_issue_intake()` after resolution.
