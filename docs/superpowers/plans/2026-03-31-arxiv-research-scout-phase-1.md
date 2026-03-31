# ArXiv Research Scout Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Phase 1 of the ArXiv Research Scout suite: a single-user workflow with a persistent interest profile, deterministic arXiv intake and deduplication, structured problem-solution artifacts, and daily/manual report composition.

**Architecture:** Implement four Codex skills backed by a small Python support package. Deterministic code will manage workspace state, profile parsing, arXiv intake, registry deduplication, artifact validation, and report rendering. The skills will handle the high-judgment steps while validators enforce output contracts and keep the workflow auditable.

**Tech Stack:** Python 3.12, `argparse`, `httpx`, `pytest`, `ruff`, Markdown artifacts, JSONL registry files

---

## Planned File Structure

- `pyproject.toml`
  Project metadata, dependencies, pytest configuration, and `auto-research` console entrypoint.
- `.gitignore`
  Ignore Python caches, virtualenvs, local workspace data, and generated reports.
- `src/auto_research/__init__.py`
  Package marker and version string.
- `src/auto_research/cli.py`
  CLI entrypoint for `init-workspace`, `validate-profile`, `intake`, `validate-extraction`, and `compose-report`.
- `src/auto_research/models.py`
  Shared dataclasses and literal types for registry entries, interest profiles, and extraction metadata.
- `src/auto_research/workspace.py`
  Workspace layout helpers and directory creation logic.
- `src/auto_research/registry.py`
  JSONL load/write helpers and deduplication logic keyed by stable arXiv id.
- `src/auto_research/profile.py`
  Markdown parser and validator for `interest-profile.md`.
- `src/auto_research/arxiv.py`
  arXiv Atom feed client and XML parser.
- `src/auto_research/intake.py`
  Query construction, metadata writing, and registry updates.
- `src/auto_research/extraction.py`
  Problem-solution artifact template rendering, frontmatter parsing, and validation.
- `src/auto_research/report.py`
  Report grouping and Markdown rendering for daily/manual reports.
- `skills/research-interest-profile/...`
  Skill metadata, instructions, template, and validator wrapper for maintaining the user profile.
- `skills/paper-intake-and-normalize/...`
  Skill metadata, instructions, reference rules, and wrapper for deterministic intake.
- `skills/problem-solution-extractor/...`
  Skill metadata, extraction contract, artifact template, and validator wrapper.
- `skills/report-composer/...`
  Skill metadata, report section contract, template, and report wrapper.
- `tests/fixtures/interest_profile.md`
  Representative profile input for parser tests.
- `tests/fixtures/arxiv_feed.xml`
  Atom feed fixture for arXiv parsing tests.
- `tests/fixtures/problem_solution.md`
  Valid extraction artifact fixture for validator tests.
- `tests/test_cli_smoke.py`
  CLI availability smoke test.
- `tests/test_workspace.py`
  Workspace layout and registry deduplication tests.
- `tests/test_profile.py`
  Profile parsing and validation tests.
- `tests/test_arxiv.py`
  arXiv parsing and intake tests.
- `tests/test_extraction.py`
  Extraction artifact validation tests.
- `tests/test_report.py`
  Report composition tests for daily/manual modes.

### Task 1: Bootstrap the Python Package and CLI Skeleton

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `src/auto_research/__init__.py`
- Create: `src/auto_research/cli.py`
- Create: `tests/test_cli_smoke.py`

- [ ] **Step 1: Write the failing smoke test for the CLI**

```python
# tests/test_cli_smoke.py
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
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run: `pytest tests/test_cli_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'auto_research'`

- [ ] **Step 3: Write the minimal package and CLI implementation**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "auto-research"
version = "0.1.0"
description = "Phase 1 tooling for the ArXiv Research Scout skill suite"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "httpx>=0.27,<0.28",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.1,<9.0",
  "ruff>=0.11,<0.12",
]

[project.scripts]
auto-research = "auto_research.cli:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```gitignore
# .gitignore
.pytest_cache/
.ruff_cache/
.venv/
__pycache__/
*.pyc
research-workspace/
```

```python
# src/auto_research/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```python
# src/auto_research/cli.py
from __future__ import annotations

import argparse
from typing import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-workspace")
    subparsers.add_parser("validate-profile")
    subparsers.add_parser("intake")
    subparsers.add_parser("validate-extraction")
    subparsers.add_parser("compose-report")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `pytest tests/test_cli_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit the bootstrap**

```bash
git add .gitignore pyproject.toml src/auto_research/__init__.py src/auto_research/cli.py tests/test_cli_smoke.py
git commit -m "chore: bootstrap auto research package"
```

### Task 2: Implement Workspace Layout, Shared Models, and Registry Deduplication

**Files:**
- Create: `src/auto_research/models.py`
- Create: `src/auto_research/workspace.py`
- Create: `src/auto_research/registry.py`
- Modify: `src/auto_research/cli.py`
- Create: `tests/test_workspace.py`

- [ ] **Step 1: Write the failing workspace and registry tests**

```python
# tests/test_workspace.py
from auto_research.models import RegistryEntry
from auto_research.registry import merge_registry_entries
from auto_research.workspace import ensure_workspace


def test_ensure_workspace_creates_phase1_directories(tmp_path) -> None:
    root = ensure_workspace(tmp_path / "research-workspace")

    assert (root / "profile").is_dir()
    assert (root / "papers").is_dir()
    assert (root / "reports" / "daily").is_dir()
    assert (root / "reports" / "manual").is_dir()


def test_merge_registry_entries_keeps_latest_version() -> None:
    old = RegistryEntry(
        arxiv_id="2501.00001v1",
        title="Older version",
        summary="old",
        pdf_url="https://arxiv.org/pdf/2501.00001v1",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        relevance_band="adjacent",
        source="arxiv",
    )
    new = RegistryEntry(
        arxiv_id="2501.00001v2",
        title="Newer version",
        summary="new",
        pdf_url="https://arxiv.org/pdf/2501.00001v2",
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-03T00:00:00Z",
        relevance_band="high-match",
        source="arxiv",
    )

    merged = merge_registry_entries([old], [new])

    assert len(merged) == 1
    assert merged[0].arxiv_id == "2501.00001v2"
    assert merged[0].relevance_band == "high-match"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_workspace.py -v`
Expected: FAIL with `ImportError` for `auto_research.models`, `auto_research.registry`, or `auto_research.workspace`

- [ ] **Step 3: Implement the workspace and registry modules**

```python
# src/auto_research/models.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

RelevanceBand = Literal["high-match", "adjacent", "low-priority"]
Confidence = Literal["high", "medium", "low"]
OpportunityLabel = Literal["read-now", "follow-up", "skip", "manual-review"]


@dataclass(slots=True)
class InterestProfile:
    core_interests: list[str] = field(default_factory=list)
    soft_boundaries: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    current_phase_bias: list[str] = field(default_factory=list)
    evaluation_heuristics: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RegistryEntry:
    arxiv_id: str
    title: str
    summary: str
    pdf_url: str
    published_at: str
    updated_at: str
    relevance_band: RelevanceBand
    source: str

    @property
    def stable_id(self) -> str:
        base, _, _ = self.arxiv_id.partition("v")
        return base

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
```

```python
# src/auto_research/workspace.py
from __future__ import annotations

from pathlib import Path


PHASE1_DIRECTORIES = (
    "profile",
    "papers",
    "reports/daily",
    "reports/manual",
)


def ensure_workspace(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)

    for relative_path in PHASE1_DIRECTORIES:
        (root / relative_path).mkdir(parents=True, exist_ok=True)

    return root
```

```python
# src/auto_research/registry.py
from __future__ import annotations

import json
from pathlib import Path

from auto_research.models import RegistryEntry


def load_registry(path: Path) -> list[RegistryEntry]:
    if not path.exists():
        return []

    entries: list[RegistryEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(RegistryEntry(**json.loads(line)))
    return entries


def write_registry(path: Path, entries: list[RegistryEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(entry.to_dict(), sort_keys=True) for entry in entries)
    path.write_text(f"{payload}\n" if payload else "", encoding="utf-8")


def merge_registry_entries(
    existing: list[RegistryEntry], incoming: list[RegistryEntry]
) -> list[RegistryEntry]:
    merged: dict[str, RegistryEntry] = {entry.stable_id: entry for entry in existing}

    for entry in incoming:
        current = merged.get(entry.stable_id)
        if current is None or current.updated_at <= entry.updated_at:
            merged[entry.stable_id] = entry

    return sorted(merged.values(), key=lambda item: item.updated_at, reverse=True)
```

```python
# src/auto_research/cli.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from auto_research.workspace import ensure_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    subparsers.add_parser("validate-profile")
    subparsers.add_parser("intake")
    subparsers.add_parser("validate-extraction")
    subparsers.add_parser("compose-report")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-workspace":
        ensure_workspace(Path(args.workspace))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_workspace.py -v`
Expected: PASS

- [ ] **Step 5: Commit the shared workspace layer**

```bash
git add src/auto_research/models.py src/auto_research/workspace.py src/auto_research/registry.py src/auto_research/cli.py tests/test_workspace.py
git commit -m "feat: add workspace and registry primitives"
```

### Task 3: Implement the Research Interest Profile Skill and Validator

**Files:**
- Create: `src/auto_research/profile.py`
- Modify: `src/auto_research/cli.py`
- Create: `skills/research-interest-profile/SKILL.md`
- Create: `skills/research-interest-profile/agents/openai.yaml`
- Create: `skills/research-interest-profile/assets/interest-profile-template.md`
- Create: `skills/research-interest-profile/references/profile-format.md`
- Create: `skills/research-interest-profile/scripts/validate_profile.py`
- Create: `tests/fixtures/interest_profile.md`
- Create: `tests/test_profile.py`

- [ ] **Step 1: Write the failing profile parsing tests**

```python
# tests/test_profile.py
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
```

```markdown
<!-- tests/fixtures/interest_profile.md -->
# Research Interest Profile

## Core Interests
- distributed systems for ML serving
- operating systems for resource isolation and scheduling

## Soft Boundaries
- systems papers adjacent to inference efficiency
- empirical infrastructure work with strong operational lessons

## Exclusions
- pure cryptography
- benchmark-only model scaling papers without systems content

## Current-Phase Bias
- strong problems with incomplete current solutions
- ideas that could plausibly become conference submissions

## Evaluation Heuristics
- reward important bottlenecks more than stylistic novelty
- prefer simple mechanisms over ornamental complexity

## Open Questions
- where current LLM serving stacks are still wasteful under tail latency constraints
- which scheduler assumptions break under heterogeneous accelerators
```

- [ ] **Step 2: Run the profile tests to verify they fail**

Run: `pytest tests/test_profile.py -v`
Expected: FAIL with `ImportError: cannot import name 'load_interest_profile'`

- [ ] **Step 3: Implement the profile parser, CLI validation, and skill files**

```python
# src/auto_research/profile.py
from __future__ import annotations

import re
from pathlib import Path

from auto_research.models import InterestProfile


SECTION_NAMES = (
    "Core Interests",
    "Soft Boundaries",
    "Exclusions",
    "Current-Phase Bias",
    "Evaluation Heuristics",
    "Open Questions",
)


def _section_pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        rf"^## {re.escape(name)}\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )


def _extract_bullets(body: str) -> list[str]:
    return [line[2:].strip() for line in body.splitlines() if line.startswith("- ")]


def validate_interest_profile_text(text: str) -> list[str]:
    errors: list[str] = []

    for section in SECTION_NAMES:
        match = _section_pattern(section).search(text)
        if match is None:
            errors.append(f"Missing section: {section}")
            continue
        if not _extract_bullets(match.group("body")):
            errors.append(f"Section has no bullet items: {section}")

    return errors


def parse_interest_profile_text(text: str) -> InterestProfile:
    errors = validate_interest_profile_text(text)
    if errors:
        raise ValueError("\n".join(errors))

    sections = {
        section: _extract_bullets(_section_pattern(section).search(text).group("body"))
        for section in SECTION_NAMES
    }

    return InterestProfile(
        core_interests=sections["Core Interests"],
        soft_boundaries=sections["Soft Boundaries"],
        exclusions=sections["Exclusions"],
        current_phase_bias=sections["Current-Phase Bias"],
        evaluation_heuristics=sections["Evaluation Heuristics"],
        open_questions=sections["Open Questions"],
    )


def load_interest_profile(path: Path) -> InterestProfile:
    return parse_interest_profile_text(path.read_text(encoding="utf-8"))
```

```python
# src/auto_research/cli.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from auto_research.profile import validate_interest_profile_text
from auto_research.workspace import ensure_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("path")

    subparsers.add_parser("intake")
    subparsers.add_parser("validate-extraction")
    subparsers.add_parser("compose-report")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-workspace":
        ensure_workspace(Path(args.workspace))
        return 0

    if args.command == "validate-profile":
        text = Path(args.path).read_text(encoding="utf-8")
        errors = validate_interest_profile_text(text)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("interest profile is valid")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```md
<!-- skills/research-interest-profile/SKILL.md -->
---
name: research-interest-profile
description: Maintain and revise a persistent single-user research interest profile for arXiv scouting. Use when Codex should interview the user about what topics to watch, what adjacent areas to keep in view, what to exclude, or how current research priorities have shifted.
---

# Workflow

1. Read `research-workspace/profile/interest-profile.md` if it exists.
2. Ask one question at a time to refine core interests, soft boundaries, exclusions, current-phase bias, evaluation heuristics, and open questions.
3. Keep the profile selective but not brittle. Preserve adjacent directions when the user wants breadth.
4. Update `research-workspace/profile/interest-profile.md` using the template in `assets/interest-profile-template.md`.
5. Run `python skills/research-interest-profile/scripts/validate_profile.py research-workspace/profile/interest-profile.md`.
6. Summarize what changed in 3 to 5 bullets.
```

```yaml
# skills/research-interest-profile/agents/openai.yaml
interface:
  display_name: "Research Interest Profile"
  short_description: "Maintain a persistent scouting profile"
  default_prompt: "Use $research-interest-profile to revise my long-term arXiv scouting profile."
```

```md
<!-- skills/research-interest-profile/assets/interest-profile-template.md -->
# Research Interest Profile

## Core Interests
- 

## Soft Boundaries
- 

## Exclusions
- 

## Current-Phase Bias
- 

## Evaluation Heuristics
- 

## Open Questions
- 
```

```md
<!-- skills/research-interest-profile/references/profile-format.md -->
# Profile Rules

- Keep each section as bullet points.
- Prefer short, concrete phrases over paragraphs.
- Revise stale bullets instead of only appending new ones.
- Use `Soft Boundaries` for adjacent directions the user does not want to miss.
- Use `Exclusions` to suppress recurring noise in later intake steps.
```

```python
# skills/research-interest-profile/scripts/validate_profile.py
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from auto_research.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["validate-profile", *sys.argv[1:]]))
```

- [ ] **Step 4: Run the tests and CLI validation**

Run: `pytest tests/test_profile.py -v`
Expected: PASS

Run: `PYTHONPATH=src python -m auto_research.cli validate-profile tests/fixtures/interest_profile.md`
Expected: `interest profile is valid`

- [ ] **Step 5: Commit the profile skill**

```bash
git add src/auto_research/profile.py src/auto_research/cli.py skills/research-interest-profile tests/fixtures/interest_profile.md tests/test_profile.py
git commit -m "feat: add research interest profile skill"
```

### Task 4: Implement arXiv Intake, Metadata Normalization, and the Intake Skill

**Files:**
- Create: `src/auto_research/arxiv.py`
- Create: `src/auto_research/intake.py`
- Modify: `src/auto_research/cli.py`
- Create: `skills/paper-intake-and-normalize/SKILL.md`
- Create: `skills/paper-intake-and-normalize/agents/openai.yaml`
- Create: `skills/paper-intake-and-normalize/references/intake-rules.md`
- Create: `skills/paper-intake-and-normalize/scripts/run_intake.py`
- Create: `tests/fixtures/arxiv_feed.xml`
- Create: `tests/test_arxiv.py`

- [ ] **Step 1: Write the failing arXiv parsing and intake tests**

```python
# tests/test_arxiv.py
from pathlib import Path

import httpx

from auto_research.arxiv import ArxivClient
from auto_research.intake import build_query_from_profile
from auto_research.profile import load_interest_profile


FIXTURE_XML = Path("tests/fixtures/arxiv_feed.xml").read_text(encoding="utf-8")


def test_build_query_from_profile_uses_core_and_soft_topics() -> None:
    profile = load_interest_profile(Path("tests/fixtures/interest_profile.md"))

    query = build_query_from_profile(profile)

    assert "distributed systems for ML serving" in query
    assert "systems papers adjacent to inference efficiency" in query


def test_arxiv_client_parses_atom_feed() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=FIXTURE_XML)
    )
    client = ArxivClient(httpx.Client(transport=transport), "https://example.test/api/query")

    entries = client.fetch_recent("distributed systems", max_results=2)

    assert [entry.arxiv_id for entry in entries] == ["2501.00001v1", "2501.00002v1"]
    assert entries[0].relevance_band == "adjacent"
```

```xml
<!-- tests/fixtures/arxiv_feed.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2501.00001v1</id>
    <updated>2026-01-03T00:00:00Z</updated>
    <published>2026-01-01T00:00:00Z</published>
    <title>Efficient Tail Latency Control for Serving Clusters</title>
    <summary>We study tail latency in serving clusters and propose a queue-aware scheduler.</summary>
    <link title="pdf" href="http://arxiv.org/pdf/2501.00001v1"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2501.00002v1</id>
    <updated>2026-01-02T00:00:00Z</updated>
    <published>2026-01-02T00:00:00Z</published>
    <title>Inference Scheduling Under Heterogeneous Accelerators</title>
    <summary>We examine scheduling policies for mixed GPU and accelerator fleets.</summary>
    <link title="pdf" href="http://arxiv.org/pdf/2501.00002v1"/>
  </entry>
</feed>
```

- [ ] **Step 2: Run the intake tests to verify they fail**

Run: `pytest tests/test_arxiv.py -v`
Expected: FAIL with missing `auto_research.arxiv` or `auto_research.intake`

- [ ] **Step 3: Implement the arXiv client, intake logic, CLI command, and intake skill**

```python
# src/auto_research/arxiv.py
from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

from auto_research.models import RegistryEntry


ATOM_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivClient:
    def __init__(self, client: httpx.Client | None = None, endpoint: str | None = None) -> None:
        self._client = client or httpx.Client(timeout=30.0)
        self._endpoint = endpoint or "http://export.arxiv.org/api/query"

    def fetch_recent(self, query: str, max_results: int = 25) -> list[RegistryEntry]:
        response = self._client.get(
            self._endpoint,
            params={"search_query": query, "start": 0, "max_results": max_results},
        )
        response.raise_for_status()
        return self._parse_feed(response.text)

    def _parse_feed(self, xml_text: str) -> list[RegistryEntry]:
        root = ET.fromstring(xml_text)
        entries: list[RegistryEntry] = []

        for entry in root.findall("atom:entry", ATOM_NAMESPACE):
            raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NAMESPACE).rsplit("/", 1)[-1]
            title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM_NAMESPACE).split())
            summary = " ".join(entry.findtext("atom:summary", default="", namespaces=ATOM_NAMESPACE).split())
            published_at = entry.findtext("atom:published", default="", namespaces=ATOM_NAMESPACE)
            updated_at = entry.findtext("atom:updated", default="", namespaces=ATOM_NAMESPACE)
            pdf_url = ""

            for link in entry.findall("atom:link", ATOM_NAMESPACE):
                if link.attrib.get("title") == "pdf":
                    pdf_url = link.attrib.get("href", "")
                    break

            entries.append(
                RegistryEntry(
                    arxiv_id=raw_id,
                    title=title,
                    summary=summary,
                    pdf_url=pdf_url,
                    published_at=published_at,
                    updated_at=updated_at,
                    relevance_band="adjacent",
                    source="arxiv",
                )
            )

        return entries
```

```python
# src/auto_research/intake.py
from __future__ import annotations

import json
from pathlib import Path

from auto_research.arxiv import ArxivClient
from auto_research.models import InterestProfile, RegistryEntry
from auto_research.profile import load_interest_profile
from auto_research.registry import load_registry, merge_registry_entries, write_registry
from auto_research.workspace import ensure_workspace


def build_query_from_profile(profile: InterestProfile) -> str:
    query_terms = profile.core_interests + profile.soft_boundaries[:2]
    return " OR ".join(f'all:"{term}"' for term in query_terms)


def _paper_directory_name(entry: RegistryEntry) -> str:
    return entry.arxiv_id.replace("/", "_")


def run_intake(workspace: Path, profile_path: Path, max_results: int = 25) -> list[RegistryEntry]:
    ensure_workspace(workspace)
    profile = load_interest_profile(profile_path)
    query = build_query_from_profile(profile)
    incoming = ArxivClient().fetch_recent(query, max_results=max_results)

    normalized: list[RegistryEntry] = []
    for entry in incoming:
        relevance_band = "high-match"
        if any(term.lower() in entry.summary.lower() for term in profile.soft_boundaries):
            relevance_band = "adjacent"
        if any(term.lower() in entry.summary.lower() for term in profile.exclusions):
            relevance_band = "low-priority"

        normalized.append(
            RegistryEntry(
                arxiv_id=entry.arxiv_id,
                title=entry.title,
                summary=entry.summary,
                pdf_url=entry.pdf_url,
                published_at=entry.published_at,
                updated_at=entry.updated_at,
                relevance_band=relevance_band,
                source=entry.source,
            )
        )

    registry_path = workspace / "papers" / "registry.jsonl"
    merged = merge_registry_entries(load_registry(registry_path), normalized)
    write_registry(registry_path, merged)

    for entry in normalized:
        paper_dir = workspace / "papers" / _paper_directory_name(entry)
        paper_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = paper_dir / "metadata.json"
        metadata_path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")

    return normalized
```

```python
# src/auto_research/cli.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from auto_research.intake import run_intake
from auto_research.profile import validate_interest_profile_text
from auto_research.workspace import ensure_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("path")

    intake = subparsers.add_parser("intake")
    intake.add_argument("--workspace", default="research-workspace")
    intake.add_argument("--profile", default="research-workspace/profile/interest-profile.md")
    intake.add_argument("--max-results", type=int, default=25)

    subparsers.add_parser("validate-extraction")
    subparsers.add_parser("compose-report")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-workspace":
        ensure_workspace(Path(args.workspace))
        return 0

    if args.command == "validate-profile":
        text = Path(args.path).read_text(encoding="utf-8")
        errors = validate_interest_profile_text(text)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("interest profile is valid")
        return 0

    if args.command == "intake":
        entries = run_intake(
            workspace=Path(args.workspace),
            profile_path=Path(args.profile),
            max_results=args.max_results,
        )
        print(f"ingested {len(entries)} papers")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```md
<!-- skills/paper-intake-and-normalize/SKILL.md -->
---
name: paper-intake-and-normalize
description: Fetch, normalize, and deduplicate arXiv candidates for the current research profile. Use when Codex needs to collect recent papers, rerun a retrieval window, update metadata, or prepare a candidate pool for later problem-solution analysis.
---

# Workflow

1. Read `research-workspace/profile/interest-profile.md` and validate it first.
2. Run `python skills/paper-intake-and-normalize/scripts/run_intake.py --workspace research-workspace --profile research-workspace/profile/interest-profile.md`.
3. Inspect `research-workspace/papers/registry.jsonl` and the new per-paper `metadata.json` files.
4. Keep low-priority papers in the registry for auditability, but do not promote them to later report sections unless requested.
5. Summarize how many papers were high-match, adjacent, and low-priority.
```

```yaml
# skills/paper-intake-and-normalize/agents/openai.yaml
interface:
  display_name: "Paper Intake and Normalize"
  short_description: "Fetch and normalize arXiv candidates"
  default_prompt: "Use $paper-intake-and-normalize to fetch the latest arXiv papers for my active profile."
```

```md
<!-- skills/paper-intake-and-normalize/references/intake-rules.md -->
# Intake Rules

- Use the active profile as the default source of retrieval intent.
- Preserve `low-priority` entries in the registry instead of silently discarding them.
- Treat versioned arXiv ids with the same base id as one logical paper and keep the newest update.
- Write one `metadata.json` file per paper directory so later skills can work paper-by-paper.
```

```python
# skills/paper-intake-and-normalize/scripts/run_intake.py
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from auto_research.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["intake", *sys.argv[1:]]))
```

- [ ] **Step 4: Run the tests and exercise the intake command**

Run: `pytest tests/test_arxiv.py -v`
Expected: PASS

Run: `PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace`
Expected: exit code `0`

- [ ] **Step 5: Commit the intake layer**

```bash
git add src/auto_research/arxiv.py src/auto_research/intake.py src/auto_research/cli.py skills/paper-intake-and-normalize tests/fixtures/arxiv_feed.xml tests/test_arxiv.py
git commit -m "feat: add arxiv intake and normalization skill"
```

### Task 5: Implement the Problem-Solution Artifact Contract and Extraction Skill

**Files:**
- Create: `src/auto_research/extraction.py`
- Modify: `src/auto_research/cli.py`
- Create: `skills/problem-solution-extractor/SKILL.md`
- Create: `skills/problem-solution-extractor/agents/openai.yaml`
- Create: `skills/problem-solution-extractor/assets/problem-solution-template.md`
- Create: `skills/problem-solution-extractor/references/extraction-contract.md`
- Create: `skills/problem-solution-extractor/scripts/validate_problem_solution.py`
- Create: `tests/fixtures/problem_solution.md`
- Create: `tests/test_extraction.py`

- [ ] **Step 1: Write the failing extraction validator tests**

```python
# tests/test_extraction.py
from pathlib import Path

from auto_research.extraction import parse_extraction_document, validate_extraction_document


FIXTURE_PATH = Path("tests/fixtures/problem_solution.md")


def test_parse_extraction_document_reads_frontmatter() -> None:
    parsed = parse_extraction_document(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert parsed["paper_id"] == "2501.00001v1"
    assert parsed["confidence"] == "high"
    assert parsed["opportunity_label"] == "follow-up"


def test_validate_extraction_document_rejects_missing_sections() -> None:
    errors = validate_extraction_document(
        "---\n"
        'paper_id: "2501.00001v1"\n'
        'title: "Paper"\n'
        'confidence: "high"\n'
        'relevance_band: "high-match"\n'
        'opportunity_label: "read-now"\n'
        "---\n\n"
        "# One-Sentence Summary\ntext\n"
    )

    assert "Missing heading: Problem" in errors
    assert "Missing heading: Proposed Solution" in errors
```

```md
<!-- tests/fixtures/problem_solution.md -->
---
paper_id: "2501.00001v1"
title: "Efficient Tail Latency Control for Serving Clusters"
confidence: "high"
relevance_band: "high-match"
opportunity_label: "follow-up"
---

# One-Sentence Summary
This paper studies tail latency in serving clusters and proposes a queue-aware scheduler.

# Problem
Tail latency remains unstable under bursty serving loads in shared clusters.

# Proposed Solution
The authors introduce a queue-aware scheduling policy with admission control.

# Claimed Contributions
- A serving scheduler designed for bursty request traces
- A policy evaluation across several load regimes

# Evidence Basis
- Abstract
- Introduction
- Experiments

# Limitations
- The scheduler is only evaluated on a narrow workload family.

# Relevance to Profile
This is directly relevant to systems for ML serving.

# Analyst Notes
The problem looks stronger than the breadth of the presented evaluation.
```

- [ ] **Step 2: Run the extraction tests to verify they fail**

Run: `pytest tests/test_extraction.py -v`
Expected: FAIL with missing `auto_research.extraction`

- [ ] **Step 3: Implement extraction parsing, validation, CLI support, and the skill files**

```python
# src/auto_research/extraction.py
from __future__ import annotations

import re


REQUIRED_FRONTMATTER_KEYS = (
    "paper_id",
    "title",
    "confidence",
    "relevance_band",
    "opportunity_label",
)

REQUIRED_HEADINGS = (
    "One-Sentence Summary",
    "Problem",
    "Proposed Solution",
    "Claimed Contributions",
    "Evidence Basis",
    "Limitations",
    "Relevance to Profile",
    "Analyst Notes",
)

ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_RELEVANCE = {"high-match", "adjacent", "low-priority"}
ALLOWED_OPPORTUNITY = {"read-now", "follow-up", "skip", "manual-review"}


def parse_extraction_document(text: str) -> dict[str, str]:
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if frontmatter_match is None:
        raise ValueError("Missing YAML frontmatter")

    data: dict[str, str] = {}
    for line in frontmatter_match.group(1).splitlines():
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip().strip('"')
    return data


def validate_extraction_document(text: str) -> list[str]:
    errors: list[str] = []

    try:
        frontmatter = parse_extraction_document(text)
    except ValueError as exc:
        return [str(exc)]

    for key in REQUIRED_FRONTMATTER_KEYS:
        if not frontmatter.get(key):
            errors.append(f"Missing frontmatter key: {key}")

    if frontmatter.get("confidence") not in ALLOWED_CONFIDENCE:
        errors.append("Invalid confidence value")
    if frontmatter.get("relevance_band") not in ALLOWED_RELEVANCE:
        errors.append("Invalid relevance_band value")
    if frontmatter.get("opportunity_label") not in ALLOWED_OPPORTUNITY:
        errors.append("Invalid opportunity_label value")

    for heading in REQUIRED_HEADINGS:
        if f"# {heading}\n" not in text:
            errors.append(f"Missing heading: {heading}")

    return errors
```

```python
# src/auto_research/cli.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from auto_research.extraction import validate_extraction_document
from auto_research.intake import run_intake
from auto_research.profile import validate_interest_profile_text
from auto_research.workspace import ensure_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("path")

    intake = subparsers.add_parser("intake")
    intake.add_argument("--workspace", default="research-workspace")
    intake.add_argument("--profile", default="research-workspace/profile/interest-profile.md")
    intake.add_argument("--max-results", type=int, default=25)

    validate_extraction = subparsers.add_parser("validate-extraction")
    validate_extraction.add_argument("path")

    subparsers.add_parser("compose-report")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-workspace":
        ensure_workspace(Path(args.workspace))
        return 0

    if args.command == "validate-profile":
        text = Path(args.path).read_text(encoding="utf-8")
        errors = validate_interest_profile_text(text)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("interest profile is valid")
        return 0

    if args.command == "intake":
        entries = run_intake(
            workspace=Path(args.workspace),
            profile_path=Path(args.profile),
            max_results=args.max_results,
        )
        print(f"ingested {len(entries)} papers")
        return 0

    if args.command == "validate-extraction":
        text = Path(args.path).read_text(encoding="utf-8")
        errors = validate_extraction_document(text)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("problem-solution artifact is valid")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```md
<!-- skills/problem-solution-extractor/SKILL.md -->
---
name: problem-solution-extractor
description: Produce a structured problem-solution artifact for a specific paper. Use when Codex needs to summarize a paper's core problem, proposed solution, contributions, limitations, evidence basis, confidence, and relevance to the active research profile.
---

# Workflow

1. Read the target paper's `metadata.json`.
2. If a PDF or richer text is available, use it. If not, say so and lower confidence if necessary.
3. Write `problem-solution.md` using `assets/problem-solution-template.md`.
4. Separate author claims, analyst inference, and uncertainty.
5. Use `manual-review` when the paper is too ambiguous to summarize cleanly.
6. Run `python skills/problem-solution-extractor/scripts/validate_problem_solution.py <path-to-problem-solution.md>`.
```

```yaml
# skills/problem-solution-extractor/agents/openai.yaml
interface:
  display_name: "Problem Solution Extractor"
  short_description: "Write structured paper analysis artifacts"
  default_prompt: "Use $problem-solution-extractor to analyze this paper's problem and solution."
```

```md
<!-- skills/problem-solution-extractor/assets/problem-solution-template.md -->
---
paper_id: ""
title: ""
confidence: "medium"
relevance_band: "adjacent"
opportunity_label: "manual-review"
---

# One-Sentence Summary

# Problem

# Proposed Solution

# Claimed Contributions
- 

# Evidence Basis
- 

# Limitations
- 

# Relevance to Profile

# Analyst Notes
```

```md
<!-- skills/problem-solution-extractor/references/extraction-contract.md -->
# Extraction Contract

- `confidence` must be one of `high`, `medium`, or `low`.
- `relevance_band` must be one of `high-match`, `adjacent`, or `low-priority`.
- `opportunity_label` must be one of `read-now`, `follow-up`, `skip`, or `manual-review`.
- `Evidence Basis` should list the sections that actually support the summary.
- Use `Analyst Notes` for critique, unresolved ambiguity, or opportunity signals.
```

```python
# skills/problem-solution-extractor/scripts/validate_problem_solution.py
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from auto_research.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["validate-extraction", *sys.argv[1:]]))
```

- [ ] **Step 4: Run the validator tests and CLI command**

Run: `pytest tests/test_extraction.py -v`
Expected: PASS

Run: `PYTHONPATH=src python -m auto_research.cli validate-extraction tests/fixtures/problem_solution.md`
Expected: `problem-solution artifact is valid`

- [ ] **Step 5: Commit the extraction skill**

```bash
git add src/auto_research/extraction.py src/auto_research/cli.py skills/problem-solution-extractor tests/fixtures/problem_solution.md tests/test_extraction.py
git commit -m "feat: add problem solution extraction skill"
```

### Task 6: Implement Report Composition, Daily/Manual Modes, and Phase 1 Validation

**Files:**
- Create: `src/auto_research/report.py`
- Modify: `src/auto_research/cli.py`
- Create: `skills/report-composer/SKILL.md`
- Create: `skills/report-composer/agents/openai.yaml`
- Create: `skills/report-composer/assets/daily-report-template.md`
- Create: `skills/report-composer/references/report-sections.md`
- Create: `skills/report-composer/scripts/compose_report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: Write the failing report composition tests**

```python
# tests/test_report.py
import json
from pathlib import Path

from auto_research.models import RegistryEntry
from auto_research.registry import write_registry
from auto_research.report import compose_report
from auto_research.workspace import ensure_workspace


def test_compose_daily_report_groups_entries_by_opportunity(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    registry_path = workspace / "papers" / "registry.jsonl"
    write_registry(
        registry_path,
        [
            RegistryEntry(
                arxiv_id="2501.00001v1",
                title="Efficient Tail Latency Control for Serving Clusters",
                summary="Tail latency scheduler.",
                pdf_url="https://arxiv.org/pdf/2501.00001v1",
                published_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-03T00:00:00Z",
                relevance_band="high-match",
                source="arxiv",
            )
        ],
    )

    paper_dir = workspace / "papers" / "2501.00001v1"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "problem-solution.md").write_text(
        "---\n"
        'paper_id: "2501.00001v1"\n'
        'title: "Efficient Tail Latency Control for Serving Clusters"\n'
        'confidence: "high"\n'
        'relevance_band: "high-match"\n'
        'opportunity_label: "follow-up"\n'
        "---\n\n"
        "# One-Sentence Summary\nA serving scheduler for tail latency.\n\n"
        "# Problem\nTail latency instability.\n\n"
        "# Proposed Solution\nQueue-aware scheduling.\n\n"
        "# Claimed Contributions\n- New scheduler\n\n"
        "# Evidence Basis\n- Abstract\n\n"
        "# Limitations\n- Narrow evaluation\n\n"
        "# Relevance to Profile\nDirectly relevant.\n\n"
        "# Analyst Notes\nPromising problem, incomplete validation.\n",
        encoding="utf-8",
    )

    report_path = compose_report(workspace, mode="daily", label="2026-03-31")
    report_text = report_path.read_text(encoding="utf-8")

    assert report_path == workspace / "reports" / "daily" / "2026-03-31.md"
    assert "Top Papers to Read Now" in report_text
    assert "Promising Problems, Weak Solutions" in report_text
    assert "Efficient Tail Latency Control for Serving Clusters" in report_text


def test_compose_manual_report_writes_to_manual_directory(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    report_path = compose_report(workspace, mode="manual", label="ml-serving-scan")
    assert report_path == workspace / "reports" / "manual" / "ml-serving-scan.md"
```

- [ ] **Step 2: Run the report tests to verify they fail**

Run: `pytest tests/test_report.py -v`
Expected: FAIL with missing `auto_research.report`

- [ ] **Step 3: Implement report composition, CLI support, and the report skill**

```python
# src/auto_research/report.py
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from auto_research.extraction import parse_extraction_document
from auto_research.workspace import ensure_workspace


SECTION_TITLES = {
    "read-now": "Top Papers to Read Now",
    "follow-up": "Promising Problems, Weak Solutions",
    "skip": "Papers Likely Safe to Skip",
    "manual-review": "Papers Requiring Manual Verification",
}


def _paper_directories(workspace: Path) -> list[Path]:
    papers_root = workspace / "papers"
    return [path for path in papers_root.iterdir() if path.is_dir()]


def compose_report(workspace: Path, mode: str, label: str) -> Path:
    ensure_workspace(workspace)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for paper_dir in _paper_directories(workspace):
        artifact_path = paper_dir / "problem-solution.md"
        if not artifact_path.exists():
            continue
        text = artifact_path.read_text(encoding="utf-8")
        frontmatter = parse_extraction_document(text)
        grouped[frontmatter["opportunity_label"]].append(frontmatter)

    lines = [f"# Research Scout Report: {label}", ""]
    for label_key in ("read-now", "follow-up", "skip", "manual-review"):
        lines.append(f"## {SECTION_TITLES[label_key]}")
        entries = grouped.get(label_key, [])
        if not entries:
            lines.append("- None")
        else:
            for entry in entries:
                lines.append(
                    f'- **{entry["title"]}** (`{entry["paper_id"]}`, confidence: {entry["confidence"]}, relevance: {entry["relevance_band"]})'
                )
        lines.append("")

    report_dir = workspace / "reports" / mode
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{label}.md"
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path
```

```python
# src/auto_research/cli.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from auto_research.extraction import validate_extraction_document
from auto_research.intake import run_intake
from auto_research.profile import validate_interest_profile_text
from auto_research.report import compose_report
from auto_research.workspace import ensure_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("path")

    intake = subparsers.add_parser("intake")
    intake.add_argument("--workspace", default="research-workspace")
    intake.add_argument("--profile", default="research-workspace/profile/interest-profile.md")
    intake.add_argument("--max-results", type=int, default=25)

    validate_extraction = subparsers.add_parser("validate-extraction")
    validate_extraction.add_argument("path")

    compose = subparsers.add_parser("compose-report")
    compose.add_argument("--workspace", default="research-workspace")
    compose.add_argument("--mode", choices=("daily", "manual"), default="daily")
    compose.add_argument("--label", required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-workspace":
        ensure_workspace(Path(args.workspace))
        return 0

    if args.command == "validate-profile":
        text = Path(args.path).read_text(encoding="utf-8")
        errors = validate_interest_profile_text(text)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("interest profile is valid")
        return 0

    if args.command == "intake":
        entries = run_intake(
            workspace=Path(args.workspace),
            profile_path=Path(args.profile),
            max_results=args.max_results,
        )
        print(f"ingested {len(entries)} papers")
        return 0

    if args.command == "validate-extraction":
        text = Path(args.path).read_text(encoding="utf-8")
        errors = validate_extraction_document(text)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("problem-solution artifact is valid")
        return 0

    if args.command == "compose-report":
        report_path = compose_report(
            workspace=Path(args.workspace),
            mode=args.mode,
            label=args.label,
        )
        print(report_path)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```md
<!-- skills/report-composer/SKILL.md -->
---
name: report-composer
description: Compose concise daily or manual research scout reports from existing paper artifacts. Use when Codex should turn validated problem-solution files into a browsing-oriented shortlist with read-now, follow-up, skip, and manual-review sections.
---

# Workflow

1. Read all available `problem-solution.md` artifacts for the requested window.
2. Trust `opportunity_label` only if the artifact passes validation.
3. Run `python skills/report-composer/scripts/compose_report.py --workspace research-workspace --mode daily --label 2026-03-31` or use `manual` mode with a custom label.
4. Inspect the generated report and add 2 to 5 lines of commentary only if the user asked for a narrative layer.
5. Keep the report short enough that a researcher can review it in a few minutes.
```

```yaml
# skills/report-composer/agents/openai.yaml
interface:
  display_name: "Report Composer"
  short_description: "Compose daily or manual scout reports"
  default_prompt: "Use $report-composer to generate today's research scout report."
```

```md
<!-- skills/report-composer/assets/daily-report-template.md -->
# Research Scout Report: report-label

## Top Papers to Read Now
- 

## Promising Problems, Weak Solutions
- 

## Papers Likely Safe to Skip
- 

## Papers Requiring Manual Verification
- 
```

```md
<!-- skills/report-composer/references/report-sections.md -->
# Report Section Rules

- `Top Papers to Read Now`: High-confidence entries with `read-now`.
- `Promising Problems, Weak Solutions`: Entries marked `follow-up`.
- `Papers Likely Safe to Skip`: Entries marked `skip`.
- `Papers Requiring Manual Verification`: Low-confidence or ambiguous entries marked `manual-review`.
- Keep the report as a selection surface, not a literature review essay.
```

```python
# skills/report-composer/scripts/compose_report.py
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from auto_research.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["compose-report", *sys.argv[1:]]))
```

- [ ] **Step 4: Run the tests and validate all four skills**

Run: `pytest tests/test_report.py -v`
Expected: PASS

Run: `pytest -v`
Expected: PASS for the full Phase 1 suite

Run: `python3 /Users/zhanghao/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/research-interest-profile`
Expected: `Skill is valid!`

Run: `python3 /Users/zhanghao/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/paper-intake-and-normalize`
Expected: `Skill is valid!`

Run: `python3 /Users/zhanghao/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/problem-solution-extractor`
Expected: `Skill is valid!`

Run: `python3 /Users/zhanghao/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/report-composer`
Expected: `Skill is valid!`

- [ ] **Step 5: Commit the report layer and validation pass**

```bash
git add src/auto_research/report.py src/auto_research/cli.py skills/report-composer tests/test_report.py
git commit -m "feat: add report composer skill and phase1 validation"
```
