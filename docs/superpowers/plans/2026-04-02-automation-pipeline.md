# Automation Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a local daily automation pipeline that fetches arXiv papers, ranks them, generates Top K summaries, exports RIS, and optionally commits/pushes generated outputs.

**Architecture:** Add a small automation layer on top of the existing Phase 1 modules. The new code will orchestrate intake, model-assisted selection, summary generation, report composition, RIS export, and git automation through a single CLI command and wrapper script.

**Tech Stack:** Python 3.12, `httpx`, existing `auto_research` package, OpenAI Responses API over HTTP, pytest

---

### Planned Tasks

- Task 1: Add OpenAI client and selection primitives
- Task 2: Add RIS export and pipeline orchestration module
- Task 3: Add CLI + wrapper entrypoint
- Task 4: Add tests for ranking, RIS export, and automation flow
- Task 5: Validate pipeline outputs and document local scheduling usage
