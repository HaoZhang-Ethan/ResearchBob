# Full Analysis Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the local automation pipeline so it downloads PDFs for Top 10 papers, generates detailed per-paper analysis, tracks per-paper state, and maintains both daily and long-term summaries.

**Architecture:** Build incrementally on the existing daily pipeline. Add PDF download/text extraction, state tracking, and long-term summary generation while preserving the current Top-K ranking, report composition, RIS export, and git automation.

**Tech Stack:** Python 3.12, `httpx`, `pytest`, existing `auto_research` package, OpenAI Responses API, local files under `research-workspace`

---

### Planned Tasks

- Task 1: Add state management and PDF download/extraction helpers
- Task 2: Extend automation pipeline for Top 10 PDF-aware analysis
- Task 3: Add detailed-analysis and long-term summary generation
- Task 4: Add tests for state transitions, PDF backfill, and long-term summaries
- Task 5: Validate the end-to-end workflow and local docs
