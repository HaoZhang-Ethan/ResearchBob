# Bilingual Summary Artifacts Design

Status: Draft for implementation
Date: 2026-04-13

## Summary

Extend generated research summary artifacts so each file contains a Chinese reading version followed by the existing English version in the same Markdown file.

The first version must preserve all current English machine-readable structures while adding:

- top-of-file anchor navigation between Chinese and English sections
- Chinese-first presentation for human reading
- bilingual coverage for daily summaries, long-term summaries, short paper summaries, and detailed paper analyses
- a new `Technical Trend Analysis` section inside long-term summaries

## Goals

- Keep English output fully usable by the current parsers and downstream report generation
- Add a Chinese reading layer in the same file instead of creating separate `*.zh.md` files
- Place Chinese content before English content for readability
- Add anchor links at the top so readers can jump directly to Chinese or English sections
- Cover these artifact types:
  - `reports/daily/*-summary.md`
  - `reports/longterm/longterm-summary.md`
  - `papers/*/problem-solution.md`
  - `papers/*/detailed-analysis.md`
- Add a dedicated long-term `Technical Trend Analysis` section

## Non-Goals

- Translating the standard daily shortlist report produced by `compose_report`
- Translating arbitrary legacy Markdown files already on disk
- Replacing English as the canonical structure used by validation or reporting
- Reworking the existing extraction validator to support Chinese headings as a primary format

## Key Constraint

`problem-solution.md` is currently parsed by `src/auto_research/extraction.py` and grouped by `src/auto_research/report.py`.

Those components depend on the existing English YAML frontmatter and English top-level `#` headings such as:

- `# One-Sentence Summary`
- `# Problem`
- `# Proposed Solution`

Because of that, the English extraction structure must remain intact. The Chinese layer must not break validation or section parsing.

## File Layout

### Shared Navigation

All four artifact types should begin with a short navigation block:

- `[中文版](#chinese-version)`
- `[English](#english-version)`

Section anchors should be stable and explicit. Use HTML anchors so the bilingual wrapper does not create extra English top-level Markdown sections that might confuse existing parsers:

- `<a id="chinese-version"></a>`
- `<a id="english-version"></a>`

The navigation should appear at the top of the human-readable content. For files with YAML frontmatter, the frontmatter remains first.

### `problem-solution.md`

Required order:

1. existing YAML frontmatter
2. navigation block
3. `<a id="chinese-version"></a>` followed by a Chinese section headed by `## Chinese Version`
4. `<a id="english-version"></a>` followed by an English section headed by `## English Version`
5. within the English block, preserve the current top-level English extraction headings exactly as they exist today

Chinese subsection headings should use `###` headings and Chinese labels such as:

- `### 一句话总结`
- `### 问题`
- `### 方案`
- `### 核心贡献`
- `### 证据依据`
- `### 局限性`
- `### 与研究方向的相关性`
- `### 分析备注`

This avoids colliding with the parser that looks for English `# Heading` sections.

### `detailed-analysis.md`

Use the same pattern:

1. navigation block
2. Chinese anchor plus Chinese section
3. English anchor plus English section

The English section may keep the current top-level headings. The Chinese section should mirror the same content using Chinese subsection labels.

### Daily Summary

Daily summary files should use:

1. navigation block
2. Chinese anchor plus Chinese section
3. English anchor plus English section

Chinese headings should mirror the English structure:

- `今日核心判断`
- `关键结论`
- `好问题，弱方案`
- `值得继续想`
- `重复出现的主题`
- `需要手动补 PDF`
- `失败 / 需要重试`

### Long-Term Summary

Long-term summary files should use:

1. navigation block
2. Chinese anchor plus Chinese section
3. English anchor plus English section

Both language blocks should include:

- latest update source
- newly selected papers
- current problem clusters
- new insights
- technical trend analysis
- current rolling summary

The new `Technical Trend Analysis` section is part of the canonical long-term summary structure for both languages.

## Generation Strategy

Recommended implementation strategy:

1. keep current English generation behavior as the canonical source
2. add translation-oriented LLM helpers that transform the generated English payload/sections into Chinese
3. render bilingual Markdown from the pair of English + Chinese structures

This is safer than replacing the existing English schemas with bilingual schemas because:

- current tests and fake clients already assume English-only payload structures
- report parsing depends on the English artifact form
- it isolates the bilingual change to rendering and translation helpers

## Translation Scope

### `problem-solution.md`

Translate these fields:

- one-sentence summary
- problem
- proposed solution
- claimed contributions
- evidence basis
- limitations
- relevance to profile
- analyst notes

The YAML frontmatter remains English-only and unchanged.

### `detailed-analysis.md`

Translate these sections:

- detailed summary
- problem
- solution
- key mechanism
- assumptions
- strengths
- weaknesses
- what is missing
- why it matters to profile
- possible follow-up ideas

The metadata block can remain structurally the same, with Chinese labels in the Chinese section and the current labels in the English section.

### Daily Summary

Translate the existing payload fields:

- `headline`
- `top_takeaways`
- `good_problem_weak_solution`
- `worth_further_thought`
- `recurring_themes`
- `failed_or_retry`
- `needs_manual_pdf`

### Long-Term Summary

Translate the generated English long-term summary into Chinese after the English content is computed.

Also extend the long-term generation prompt/schema so English canonical output includes a dedicated `Technical Trend Analysis` section rather than burying trend observations inside free-form prose.

## Internal Read Compatibility

The bilingual layout introduces a new risk: later pipeline steps currently read whole files and pass the content forward.

If the code reads the entire bilingual file, future runs may:

- send duplicate Chinese + English content to the LLM
- waste tokens
- skew summaries with repeated content

Implementation should therefore add helper logic that extracts or reconstructs the English canonical block when reading:

- `papers/*/detailed-analysis.md` for downstream daily summarization
- `reports/longterm/longterm-summary.md` when preparing the next long-term update

Rule:

- downstream model inputs should continue to use English-only canonical content

## Rendering Rules

- Keep output deterministic and Markdown-only
- Keep anchor names stable across all files
- Keep Chinese before English in every bilingual artifact
- Keep list structure aligned between languages when source content is a list
- Preserve current English wording where it is already generated by the system unless the structure itself changes
- Do not duplicate YAML frontmatter into the Chinese block

## Testing Strategy

Tests should cover:

- bilingual `problem-solution.md` still passes `validate_extraction_document`
- report generation still groups bilingual `problem-solution.md` correctly
- bilingual daily summary contains top navigation and both language anchors
- bilingual long-term summary contains `Technical Trend Analysis` in both language blocks
- bilingual detailed analysis renders Chinese before English
- helpers that reload detailed analysis for later summarization return only the English canonical content
- helpers that reload previous long-term summary for updates return only the English canonical content

## Architecture

Recommended module split:

- `src/auto_research/openai_client.py`
  - add translation helpers
  - extend long-term generation structure to include technical trend analysis
- `src/auto_research/automation.py`
  - render bilingual `problem-solution.md`
  - feed bilingual-aware readers into downstream steps
- `src/auto_research/analysis.py`
  - render bilingual `detailed-analysis.md`
- `src/auto_research/summary.py`
  - render bilingual daily summaries
- `src/auto_research/longterm.py`
  - render bilingual long-term summaries and preserve English canonical extraction for later reuse
- tests in `tests/test_automation.py` and targeted rendering/parser tests

## Open Questions

- whether Chinese translation failures should fail the whole run or fall back to English-only output
- whether the long-term `Technical Trend Analysis` section should remain prose or evolve into bullets in a later version

## Recommendation

For the first implementation:

- make bilingual generation required when summary generation succeeds
- keep English canonical structure untouched
- generate Chinese as a second pass from English content
- add explicit bilingual readers so later pipeline stages only ingest English canonical text
- implement `Technical Trend Analysis` as a dedicated prose section in long-term summaries
