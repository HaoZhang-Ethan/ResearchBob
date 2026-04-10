# ResearchBob

[Jump to Chinese / 跳转中文](#中文说明)

ResearchBob is a local research workflow for collecting ideas, discovering papers, and producing periodic paper summaries from GitHub issue requests.

---

## 1. Project Overview

### What It Is

ResearchBob is a local workflow for:

- collecting research directions from GitHub issues
- fetching and filtering arXiv papers
- generating daily paper summaries and supporting artifacts
- providing reusable research-oriented Codex skills

### Motivation

For research work, the bottleneck is usually not access to papers, but attention:

- too many papers are published
- interesting ideas are easy to miss
- user requirements are often scattered in notes or chat
- it is hard to consistently turn broad directions into a small set of worth-reading papers

ResearchBob is built to reduce that friction.

### How It Works

At a high level:

1. a user submits a direction or requirement, usually through a GitHub issue
2. the local workflow syncs those requests into the workspace
3. the pipeline uses an interest profile to fetch and rank papers
4. the system writes reports, summaries, and export artifacts
5. GitHub-side actions can be finalized later in a separate network environment

### Strengths and Limits

**Strengths**

- simple issue-driven request flow
- local-first and easy to inspect
- works well for periodic paper discovery and summarization
- supports split-network execution through `finalize-github`
- also includes reusable Codex research skills

**Limits**

- not an on-demand paper analysis service
- timing is best-effort because it runs on a personal laptop
- current pipeline is single-workspace, not multi-tenant
- network and proxy setup may need different handling for arXiv/model access and GitHub access

---

## 2. Main Features

| Feature | What It Does | Best For | Strengths | Limits |
|---|---|---|---|---|
| Automatic idea collection and discovery | Turns requests into periodic paper discovery and daily summaries | People who want recurring research monitoring | Structured input, repeatable workflow, local artifacts | Not instant, depends on scheduled/local execution |
| Research skill toolkit | Provides reusable Codex skills for research-related tasks | People who want interactive assistance | Reusable, modular, skill-oriented | Separate from the automated periodic pipeline |

---

## 3. Feature 1: Automatic Idea Collection and Discovery

### What It Is

This feature turns a research direction into a recurring paper summary workflow.

Typical outputs include:

- daily report markdown
- daily summary markdown
- selected paper artifacts
- RIS export
- GitHub-side follow-up state for consumed requests

### Usage Mode 1: Local Deployment

#### What It Is

This is the operator view.

You run the workflow locally and let it:

- sync issue requests
- build or reuse the profile
- discover and summarize papers
- optionally finalize GitHub-side actions later

#### How to Use It

Typical flow:

```bash
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace --direction llm-agents
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace --direction llm-agents
```

Important commands:

- `sync-issues`
  pulls GitHub issues into `research-workspace/issue-intake/`
- `daily-pipeline`
  generates the daily summary outputs
- `finalize-github`
  runs `git push`, comments on consumed issues, and closes them

#### Deploy It With AI

If you want an AI assistant to help deploy the local workflow, paste:

```text
Please help me set up this repository as a local daily paper summary workflow on my machine.

Repository path: /path/to/ResearchBob
Workspace path: /path/to/ResearchBob/research-workspace

Tasks:
1. Initialize the workspace if needed.
2. Tell me which environment variables or `.env.local` values I still need to provide.
3. Verify the CLI commands for `sync-issues`, `daily-pipeline`, and `finalize-github`.
4. Show me the exact commands to run the workflow end to end.
5. Call out any proxy or network split I may need between paper generation and GitHub finalize.
```

### Usage Mode 2: GitHub Issue

#### What It Is

This is the request-submission view.

Users submit directions, requirements, and constraints through GitHub issues in this repository, and the system periodically folds those requests into the paper summary workflow.

#### How to Use It

Users only need to submit issues in the required format.

Operators later run:

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace --direction llm-agents
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace --direction llm-agents
```

#### User Side

If you are only submitting requests, this is the part that matters.

In this repository, you can directly open an issue and the project will periodically produce:

- a daily report
- a daily summary
- selected paper artifacts
- supporting exports

Important output directories:

```text
research-workspace/directions/<direction>/reports/daily/
research-workspace/directions/<direction>/papers/
research-workspace/directions/<direction>/exports/zotero/
```

Issue format:

```md
---
direction: llm-agents
---

## Background
I want to focus on papers about multi-agent collaboration, planning, and tool use.

## Requirements
- Prefer papers with clear system design
- In the daily summary, highlight the problem, method, and limitations

## Constraints
- Avoid papers that are mostly benchmark chasing
- Prefer recent work when possible

## Notes
If there is an open-source implementation, it is helpful to mention it.
```

Details:

- the body must start with YAML frontmatter
- `direction` is required
- the title is free-form
- `Background` / `Requirements` / `Constraints` / `Notes` are recommended
- this workflow is periodic, not instant
- timing is best-effort because the system runs locally on a laptop

#### Developer Side

If you do not deploy the project, you do not need to care about this section.

This side is responsible for:

- syncing issues into `research-workspace/issue-intake/`
- running the daily summary pipeline
- optionally splitting content generation and GitHub finalization across two network environments

Key details:

- `daily-pipeline` may auto-generate `directions/<direction>/profile/interest-profile.md` (and the paired `directions/<direction>/profile/search-profile.json`) if the interest profile is missing
- if `interest-profile.md` exists but `search-profile.json` is missing, the workflow only generates `search-profile.json` and preserves the existing interest profile contents
- `finalize-github --direction <direction>` reads `research-workspace/directions/<direction>/pipeline/github-finalize.json`
- `finalize-github` exists so GitHub actions can run separately from arXiv/model calls

##### Issue-to-Profile Hybrid Retrieval

When `daily-pipeline` consumes the issue intake, it synthesizes the missing direction-local profiles under `directions/<direction>/profile/` so that retrieval is guided by an aligned `search-profile.json`. If `interest-profile.md` is missing it is generated along with the paired `search-profile.json`. If only `search-profile.json` is missing, the workflow generates `search-profile.json` and preserves the existing interest profile contents. The pipeline issues both arXiv API queries and agent-assisted web retrieval guided by the search profile, merges those candidates, and ranks them together before generating the rest of the report.

Relevant papers that are missing PDFs are kept rather than discarded; they are written under `directions/<direction>/papers/<stable_arxiv_id>/` with a `state.json` in a retry/manual-PDF-needed state (typically `status: needs_retry` with `failure_kind: manual_required` or `missing_pdf`). Operators can satisfy that by downloading the PDF and placing it at `research-workspace/directions/<direction>/papers/<stable_arxiv_id>/source.pdf`. The next daily run detects the new file and resumes analysis for papers that were previously queued (those that already have a `state.json`).

#### Draft the Issue With AI

If you want an AI assistant to turn rough notes into a valid issue, paste:

```text
Please turn my request into a GitHub issue for the daily paper summary workflow in this repository.

Requirements:
1. Use YAML frontmatter and include a non-empty `direction`.
2. Keep the issue body concise and structured.
3. Organize the body with these sections when relevant:
   - Background
   - Requirements
   - Constraints
   - Notes
4. Preserve my intent, but rewrite it into a clean issue that is easy for the intake workflow to parse.

Here is my raw request:
<paste my rough request here>
```

---

## 4. Feature 2: Research Skill Toolkit

### What It Is

This repository also includes reusable Codex skills for research-related work outside the periodic automation loop.

You can use them for:

- interest profile editing
- paper intake and normalization
- paper review simulation
- problem-solution extraction
- report composition

### Skill Table

| Skill | What It Does | Typical Use |
|---|---|---|
| `research-interest-profile` | Helps define or revise research interests | Maintaining the input profile |
| `paper-intake-and-normalize` | Helps fetch and normalize paper candidates | Interactive paper intake |
| `paper-review-simulator` | Simulates reviewer-style criticism | Draft review before submission |
| `problem-solution-extractor` | Extracts problem/solution structure from papers | Structured reading |
| `report-composer` | Helps compose paper reports | Interactive report generation |

### How to Use It

You can install the skill folders into your Codex skills directory and use them interactively.

Example prompts:

```text
Use $research-interest-profile to revise my research profile.
Use $paper-intake-and-normalize to fetch today's arXiv papers.
Use $paper-review-simulator to critique my paper draft before submission.
Use $problem-solution-extractor to analyze this paper.
Use $report-composer to generate today's report.
```

Skill directories:

- [research-interest-profile](skills/research-interest-profile/SKILL.md)
- [paper-intake-and-normalize](skills/paper-intake-and-normalize/SKILL.md)
- [paper-review-simulator](skills/paper-review-simulator/SKILL.md)
- [problem-solution-extractor](skills/problem-solution-extractor/SKILL.md)
- [report-composer](skills/report-composer/SKILL.md)

### Install It With AI

If you want an AI assistant to install the reusable Codex skills, paste:

```text
Please install the Codex skills from this repository into my local Codex skills directory.

Repository path: /path/to/ResearchBob
Target skills directory: ~/.codex/skills

Use symlinks for these skill folders:
- research-interest-profile
- paper-intake-and-normalize
- paper-review-simulator
- problem-solution-extractor
- report-composer

After installation, verify the links exist and show me the exact paths that were created.
```

---

## 中文说明

## 1. 项目概述

### 简介

ResearchBob 是一套本地研究工作流，用来把 GitHub issue 里的研究需求转成周期性的 arXiv 论文发现与总结。

### 动机

科研里真正困难的通常不是“能不能拿到论文”，而是：

- 论文太多
- 方向容易发散
- 用户需求常常分散在聊天、笔记或 issue 里
- 很难稳定地把方向变成一组值得读的论文和总结

这个项目就是为了降低这部分摩擦。

### 原理

整体流程是：

1. 用户通过 GitHub issue 提需求
2. 本地流程把需求同步到工作区
3. 系统用研究画像抓取、筛选并总结论文
4. 系统写日报、论文集合和导出文件
5. GitHub 侧的 push / issue comment / issue close 可以稍后在另一个网络环境里执行

### 优势与局限

**优势**

- issue 驱动，输入清晰
- 本地优先，产物可检查
- 适合周期性论文发现和总结
- 通过 `finalize-github` 支持网络环境拆分
- 同时提供可复用的 Codex research skills

**局限**

- 不是即时响应的论文分析服务
- 时间不保证，因为它运行在个人笔记本上
- 当前还是单工作区，不是多租户系统
- arXiv / 模型网关和 GitHub 可能需要不同代理环境

---

## 2. 主要功能

| 功能 | 作用 | 适合谁 | 优势 | 局限 |
|---|---|---|---|---|
| 自动 idea 收集与发现 | 把需求转成周期性论文发现和日报 | 想持续跟踪方向的人 | 输入结构化、流程稳定、本地产物清晰 | 不是即时执行，依赖本地周期运行 |
| 科研 Skill 工具集 | 提供可复用的 Codex skills | 想交互式做科研辅助的人 | 可复用、模块化、适合互动场景 | 与自动化周期流程是两条路径 |

---

## 3. 功能 1：自动 idea 收集与发现

### 介绍是什么

这个功能会把研究方向、主题和限制条件，转换成周期性的论文发现与日报流程。

常见输出包括：

- 每日 markdown 报告
- 每日 summary
- 选中文章的本地 artifacts
- RIS 导出
- GitHub finalize 需要的状态文件

### 使用方式 1：自动 idea 收集与发现（本地部署）

#### 介绍是什么

这是运维/部署者视角。

你本地运行工作流，让系统自动：

- 同步 issue 需求
- 构建或复用研究画像
- 发现和总结论文
- 在后续环境中做 GitHub 收尾

#### 具体使用方式

典型流程：

```bash
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace --direction llm-agents
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace --direction llm-agents
```

几个关键命令：

- `sync-issues`
  把 GitHub issue 拉到 `research-workspace/issue-intake/`
- `daily-pipeline`
  生成论文分析和日报
- `finalize-github`
  执行 `git push`，然后对被消费的 issue 做 comment 和 close

#### 利用 AI 部署

如果你想让 AI 助手帮你部署本地流程，可以直接贴：

```text
请帮我把这个仓库部署成本地的每天论文总结流程。

仓库路径：/path/to/ResearchBob
工作区路径：/path/to/ResearchBob/research-workspace

请完成这些事情：
1. 如果需要，初始化 workspace。
2. 告诉我还缺哪些环境变量或 `.env.local` 配置。
3. 校验 `sync-issues`、`daily-pipeline`、`finalize-github` 这三个 CLI 命令的用法。
4. 给我一套端到端运行命令。
5. 说明如果 GitHub 和 arXiv 需要不同网络环境，我应该怎么拆开执行。
```

### 使用方式 2：使用 Issue

#### 介绍是什么

这是用户提交需求的方式。

用户直接在本仓库提 GitHub issue，系统会在周期性运行时把这些需求纳入论文总结流程。

#### 具体使用方式

用户提交 issue。

部署端后续执行：

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace --direction llm-agents
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace --direction llm-agents
```

#### 用户侧

如果你只是提需求，这一部分才是你要关心的。

在本仓库里，你可以直接提 issue。项目会周期性地产出：

- 每日报告
- 每日 summary
- 选中文章的本地 artifacts
- 导出文件

关键输出目录：

```text
research-workspace/directions/<direction>/reports/daily/
research-workspace/directions/<direction>/papers/
research-workspace/directions/<direction>/exports/zotero/
```

Issue 格式：

```md
---
direction: llm-agents
---

## Background
我最近想重点关注多智能体协作、规划和 tool use 相关论文。

## Requirements
- 优先看有明确系统设计的工作
- 希望每天总结里突出 problem、method、limitations

## Constraints
- 尽量避免纯 benchmark 堆分数的论文

## Notes
如果有开源实现，也可以顺手记一下。
```

细节：

- 正文第一行就必须开始 YAML frontmatter
- `direction` 必填
- 标题随意
- `Background` / `Requirements` / `Constraints` / `Notes` 推荐写
- 这是周期性流程，不是即时响应
- 时间是 best-effort，因为系统跑在本地笔记本上

#### 开发者侧

如果你不部署这个项目，不需要关注这部分。

部署端需要负责：

- 把 issue 同步到 `research-workspace/issue-intake/`
- 运行每天论文总结流程
- 必要时在另一个网络环境里执行 GitHub finalize

关键细节：

- 如果 `directions/<direction>/profile/interest-profile.md` 缺失，`daily-pipeline` 可能自动生成它
- `finalize-github --direction <direction>` 读取 `research-workspace/directions/<direction>/pipeline/github-finalize.json`
- `finalize-github` 的存在，就是为了把 GitHub 操作从论文总结本身解耦

#### 利用 AI 凝练 Issue

如果你想让 AI 助手把零散需求整理成合法 issue，可以直接贴：

```text
请帮我把下面这段需求整理成适合这个仓库使用的 GitHub issue。

要求：
1. 使用 YAML frontmatter，并且包含非空的 `direction`。
2. issue 正文尽量简洁、结构化。
3. 按需要组织这些章节：
   - Background
   - Requirements
   - Constraints
   - Notes
4. 保留我的原始意图，但把它改写成便于 intake 流程解析的格式。

这是我的原始需求：
<把你的需求贴在这里>
```

---

## 4. 功能 2：科研相关的 Skill 工具集

### 介绍是什么

这个仓库还附带了一组可复用的 Codex skills，用来支持研究相关的交互式工作，而不是周期性自动化流程。

你可以用它们来做：

- 研究画像编辑
- 论文 intake 与整理
- reviewer 视角模拟
- 问题/方案提取
- 报告生成

### Skill 表

| Skill | 作用 | 适用场景 |
|---|---|---|
| `research-interest-profile` | 编辑或修订研究兴趣画像 | 维护输入 profile |
| `paper-intake-and-normalize` | 拉取并整理论文候选 | 交互式 intake |
| `paper-review-simulator` | 模拟 reviewer 式质疑 | 投稿前自查 |
| `problem-solution-extractor` | 提取论文的问题/方案结构 | 结构化阅读 |
| `report-composer` | 辅助生成报告 | 交互式报告产出 |

### 使用方式

你可以把这些 skill 安装到 Codex 的 skills 目录里，然后交互式使用。

示例 prompt：

```text
Use $research-interest-profile to revise my research profile.
Use $paper-intake-and-normalize to fetch today's arXiv papers.
Use $paper-review-simulator to critique my paper draft before submission.
Use $problem-solution-extractor to analyze this paper.
Use $report-composer to generate today's report.
```

Skill 目录：

- [research-interest-profile](skills/research-interest-profile/SKILL.md)
- [paper-intake-and-normalize](skills/paper-intake-and-normalize/SKILL.md)
- [paper-review-simulator](skills/paper-review-simulator/SKILL.md)
- [problem-solution-extractor](skills/problem-solution-extractor/SKILL.md)
- [report-composer](skills/report-composer/SKILL.md)

### 利用 AI 部署

如果你想让 AI 助手帮你安装这些 Codex skills，可以直接贴：

```text
请帮我把这个仓库里的 Codex skills 安装到本机的 Codex skills 目录。

仓库路径：/path/to/ResearchBob
目标目录：~/.codex/skills

请用软链接安装以下目录：
- research-interest-profile
- paper-intake-and-normalize
- paper-review-simulator
- problem-solution-extractor
- report-composer

安装完成后，请校验这些链接是否存在，并把实际创建的路径列给我。
```
