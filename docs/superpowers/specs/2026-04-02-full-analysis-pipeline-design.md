# Full Analysis Pipeline Increment Design

Status: Draft for implementation
Date: 2026-04-02

## Summary

Extend the local automation pipeline from abstract-only Top K processing to a fuller daily analyst workflow:

1. intake fresh arXiv candidates
2. rank and select Top 10 papers
3. download PDFs for the selected set
4. generate detailed per-paper analysis from full text when possible
5. keep a daily summary report
6. maintain a long-term rolling summary organized by problem clusters
7. export a Zotero RIS file
8. commit and push generated artifacts

The first version should support graceful failure and backfill:

- if a PDF download fails, record the failure and continue
- if a PDF is manually added later, the next run should detect it and complete the missing analysis automatically

## Goals

- Analyze at most 10 papers per run
- Support PDF download and PDF-ready backfill
- Add explicit per-paper state files
- Produce both short and detailed analyses
- Produce a daily summary and a long-term summary
- Keep the existing automation entrypoint and extend it incrementally

## Non-Goals

- Full-text parsing with layout-perfect fidelity
- OCR for scanned PDFs in the first version
- Multi-user coordination
- Cloud scheduling

## New Outputs

Per paper:

- `metadata.json`
- `source.pdf`
- `problem-solution.md`
- `detailed-analysis.md`
- `state.json`

Per run:

- `reports/daily/<date>.md`
- `reports/longterm/longterm-summary.md`
- `exports/zotero/<date>.ris`

Global:

- `pipeline/run-history.jsonl`

## State Model

Each paper should have a `state.json` with at least:

- `status`
- `last_attempt_at`
- `last_error`
- `analysis_version`
- `source_updated_at`

Expected statuses:

- `discovered`
- `pdf_downloaded`
- `pdf_failed`
- `analysis_done`
- `analysis_failed`
- `needs_retry`

## Pipeline Logic

### 1. Intake

Keep the existing intake behavior.

### 2. Rank + Select Top 10

Reuse the existing ranking structure but increase the summary generation cap to Top 10.

### 3. PDF Download

For each selected paper:

- if `source.pdf` already exists, keep it
- otherwise download the paper PDF
- on success, set `pdf_downloaded`
- on failure, set `pdf_failed` and record the error

### 4. Backfill Detection

Before skipping a paper, check:

- if `source.pdf` exists
- but `detailed-analysis.md` does not

In that case, advance to analysis even if the previous download failed.

### 5. Detailed Analysis

For each paper with a usable PDF and no valid analysis yet:

- extract text from the PDF
- ask the model for a more detailed analysis artifact
- emit both:
  - `problem-solution.md`
  - `detailed-analysis.md`
- validate the short artifact before saving
- if analysis fails, set `analysis_failed`

### 6. Daily Summary

Generate a daily report that includes:

- Top 10 papers
- good problem / weak solution candidates
- worth-further-thought candidates
- failed / needs retry

### 7. Long-Term Summary

Maintain a rolling `longterm-summary.md` organized by problem cluster, recurring gaps, and most promising directions.

The first implementation may regenerate the file from the currently selected papers plus the previous file contents, but it should remain stable and appendive in spirit.

## New Modules

- `src/auto_research/pdf.py`
  Download PDFs and extract text
- `src/auto_research/state.py`
  Read/write per-paper state files
- `src/auto_research/longterm.py`
  Maintain the rolling long-term summary

## Reliability Rules

- Never fail the entire run because one PDF fails
- Never reanalyze an already analyzed paper unless explicitly requested or the artifact is missing
- Always preserve failure reasons in `state.json`
- Treat manual PDF drops as valid backfill input

## Main Risk

PDF text extraction quality will be noisy across papers, so the first version should keep the detailed analysis concise and uncertainty-aware rather than pretending full fidelity.
