# Bilingual Summary Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Chinese-first bilingual daily summaries, long-term summaries, short paper summaries, and detailed analyses in the same files while preserving English canonical structures and downstream compatibility.

**Architecture:** Keep English as the canonical machine-readable layer, add a Chinese translation pass for human-facing reading blocks, and render both into the same Markdown file with anchor navigation. Add bilingual-aware readers so downstream summarization continues to ingest English-only canonical content. Extend long-term summaries with a dedicated technical trend analysis section.

**Tech Stack:** Python 3.12, existing `auto_research` modules, OpenAI Responses API client, pytest

---

### Task 1: Add failing tests for bilingual wrappers and canonical extraction

**Files:**
- Create: `tests/test_bilingual.py`
- Create: `src/auto_research/bilingual.py`

- [ ] **Step 1: Write failing tests for bilingual document rendering and English extraction**

```python
def test_render_bilingual_document_places_chinese_before_english() -> None:
    ...


def test_extract_english_markdown_returns_english_block_from_bilingual_text() -> None:
    ...
```

- [ ] **Step 2: Run the helper tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_bilingual.py -v`
Expected: FAIL because the bilingual helpers do not exist yet

- [ ] **Step 3: Implement minimal bilingual helper module**

```python
CHINESE_ANCHOR = '<a id="chinese-version"></a>'
ENGLISH_ANCHOR = '<a id="english-version"></a>'


def render_bilingual_document(...):
    ...


def extract_english_markdown(text: str) -> str:
    ...
```

- [ ] **Step 4: Run the helper tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_bilingual.py -v`
Expected: PASS

### Task 2: Add failing tests for bilingual short summaries and detailed analyses

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/automation.py`
- Modify: `src/auto_research/analysis.py`
- Modify: `src/auto_research/openai_client.py`

- [ ] **Step 1: Write a failing pipeline test asserting `problem-solution.md` and `detailed-analysis.md` are bilingual**

```python
def test_run_daily_pipeline_writes_bilingual_paper_artifacts(tmp_path, monkeypatch) -> None:
    ...
    assert "[中文版](#chinese-version)" in artifact_text
    assert "## Chinese Version" in artifact_text
    assert "## English Version" in artifact_text
    assert "### 一句话总结" in artifact_text
    assert "# One-Sentence Summary" in artifact_text
    assert "### 详细总结" in detailed_text
    assert "## Detailed Summary" in detailed_text
```

- [ ] **Step 2: Run the paper-artifact test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_writes_bilingual_paper_artifacts -v`
Expected: FAIL because artifact rendering is English-only

- [ ] **Step 3: Implement translation client helpers plus bilingual paper renderers**

```python
def translate_fields(...):
    ...


def _render_summary_markdown(...):
    ...


def render_detailed_analysis_markdown(...):
    ...
```

- [ ] **Step 4: Run the paper-artifact test to verify it passes**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_writes_bilingual_paper_artifacts -v`
Expected: PASS

### Task 3: Add failing tests for bilingual daily summary, long-term summary, and technical trend analysis

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/summary.py`
- Modify: `src/auto_research/longterm.py`
- Modify: `src/auto_research/openai_client.py`

- [ ] **Step 1: Write a failing pipeline test asserting bilingual daily and long-term summaries with technical trend analysis**

```python
def test_run_daily_pipeline_writes_bilingual_daily_and_longterm_summaries(tmp_path, monkeypatch) -> None:
    ...
    assert "## Chinese Version" in daily_text
    assert "## English Version" in daily_text
    assert "今日核心判断" in daily_text
    assert "Headline" in daily_text
    assert "技术趋势分析" in longterm_text
    assert "Technical Trend Analysis" in longterm_text
```

- [ ] **Step 2: Run the summary test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_writes_bilingual_daily_and_longterm_summaries -v`
Expected: FAIL because daily and long-term outputs are English-only and long-term has no technical trend section

- [ ] **Step 3: Implement bilingual daily/long-term rendering and extend long-term generation schema**

```python
def summarize_daily_findings(...):
    ...


def update_longterm_findings(...):
    ...


def render_daily_summary_markdown(...):
    ...


def update_longterm_summary(...):
    ...
```

- [ ] **Step 4: Run the summary test to verify it passes**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_run_daily_pipeline_writes_bilingual_daily_and_longterm_summaries -v`
Expected: PASS

### Task 4: Add failing tests for downstream English-only canonical reads

**Files:**
- Modify: `tests/test_automation.py`
- Modify: `src/auto_research/summary.py`
- Modify: `src/auto_research/automation.py`

- [ ] **Step 1: Write failing tests that downstream reads strip the Chinese wrapper**

```python
def test_load_detailed_analysis_texts_returns_english_block_from_bilingual_file(tmp_path) -> None:
    ...


def test_run_daily_pipeline_uses_english_previous_longterm_summary(tmp_path, monkeypatch) -> None:
    ...
```

- [ ] **Step 2: Run the downstream-read tests to verify they fail**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_load_detailed_analysis_texts_returns_english_block_from_bilingual_file tests/test_automation.py::test_run_daily_pipeline_uses_english_previous_longterm_summary -v`
Expected: FAIL because the current readers consume the entire file

- [ ] **Step 3: Implement bilingual-aware English-only readers**

```python
def load_detailed_analysis_texts(...):
    ...


previous_longterm = extract_english_markdown(...)
```

- [ ] **Step 4: Run the downstream-read tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_automation.py::test_load_detailed_analysis_texts_returns_english_block_from_bilingual_file tests/test_automation.py::test_run_daily_pipeline_uses_english_previous_longterm_summary -v`
Expected: PASS

### Task 5: Run targeted regression verification

**Files:**
- Modify: `tests/test_bilingual.py`
- Modify: `tests/test_automation.py`

- [ ] **Step 1: Run the bilingual-focused test set**

Run: `PYTHONPATH=src pytest tests/test_bilingual.py tests/test_automation.py -k "bilingual or summary or longterm or daily_pipeline_writes_outputs_under_direction_workspace" -v`
Expected: PASS

- [ ] **Step 2: Run a broader regression slice covering report parsing compatibility**

Run: `PYTHONPATH=src pytest tests/test_report.py tests/test_automation.py tests/test_cli_smoke.py -v`
Expected: PASS
