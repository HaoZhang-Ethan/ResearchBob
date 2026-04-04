# ResearchBob

[Jump to Chinese / 跳转中文](#中文说明)

ResearchBob is a local research workflow for discovering, filtering, analyzing, and summarizing arXiv papers around a persistent research profile.

It is built for one practical goal:

> Turn a large stream of new papers into a small set of ideas worth thinking about.

---

## Three Ways to Use This Project

### Usage Mode 1: Local Automation Workflow

Use ResearchBob as a local automation project that:

- fetches arXiv papers,
- ranks and selects candidates,
- downloads PDFs,
- generates short and detailed analyses,
- writes daily and long-term summaries,
- exports RIS,
- and optionally commits/pushes generated outputs.

This is the right mode if you want the system to run every day by itself.

Prompt for this mode:

```text
Please help me set up this repository as a local daily paper summary workflow on my machine.

Repository path: /path/to/ResearchBob
Workspace path: /path/to/ResearchBob/research-workspace

Tasks:
1. Initialize the workspace if needed.
2. Tell me which environment variables or `.env.local` values I still need to provide.
3. Verify the CLI commands for `daily-pipeline` and `sync-issues`.
4. Show me the exact command to run the daily paper summary locally.
5. Show me an optional cron example.

Important constraints:
- This deployment is only for the daily paper summary workflow.
- GitHub issue intake is best-effort because the automation runs on a laptop, not always-on infrastructure.
```

### Usage Mode 2: Codex Skill Set

Use the repository as a set of reusable Codex skills for interactive paper work:

- revise a research profile,
- fetch papers on demand,
- analyze a specific paper,
- compose a report interactively,
- simulate reviewer-style feedback on your own paper draft before submission.

This is the right mode if you want to work with Codex paper by paper instead of only relying on scheduled automation.

Prompt for this mode:

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

### Usage Mode 3: GitHub Issue Intake

Use GitHub issues in this repository as a lightweight request channel for the daily paper summary workflow.

This is the right mode if:

- you want users to submit directions and constraints through a fixed issue format,
- you want the local workflow to pull those requests during sync,
- and you accept that timing is best-effort because the automation runs on a laptop.

Prompt for this mode:

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

## Quick Start

### 1. Initialize a workspace

```bash
cd /path/to/ResearchBob
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
```

### 2. Create a local config

Create a local file in the repository root:

```bash
.env.local
```

Example:

```bash
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=http://your-gateway
AUTO_RESEARCH_MODEL=gpt-5.4
```

This file is ignored by git.

### 3. Create or edit the research profile

Main input file:

```text
research-workspace/profile/interest-profile.md
```

Validate it:

```bash
PYTHONPATH=src python -m auto_research.cli validate-profile research-workspace/profile/interest-profile.md
```

### 4. Run the daily pipeline

If local proxy variables interfere with direct arXiv or gateway access, unset them for the command:

```bash
cd /path/to/ResearchBob
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python scripts/daily_pipeline.py
```

Or via CLI:

```bash
cd /path/to/ResearchBob
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python -m auto_research.cli daily-pipeline --workspace research-workspace --push
```

If `research-workspace/profile/interest-profile.md` is missing, `daily-pipeline` will now try to generate it automatically from `research-workspace/issue-intake/` before continuing.

If that fallback profile generation is used and the run finishes successfully, the pipeline can also comment on and close the consumed GitHub issues on a best-effort basis.

For split-network environments, prefer this two-step pattern:

```bash
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace
```

This lets content generation happen in one network environment and GitHub push/comment/close happen later in another.

---

## What You Get

Per paper:

- `metadata.json`
- `source.pdf`
- `problem-solution.md`
- `detailed-analysis.md`
- `state.json`

Per run:

- `reports/daily/<date>.md`
- `reports/daily/<date>-summary.md`
- `reports/daily/<date>-bundle.json`
- `reports/longterm/longterm-summary.md`
- `exports/zotero/<date>.ris`
- `pipeline/run-history.jsonl`

---

## CLI Commands

```bash
PYTHONPATH=src python -m auto_research.cli --help
```

Available commands:

- `init-workspace`
- `validate-profile`
- `intake`
- `validate-extraction`
- `compose-report`
- `daily-pipeline`
- `sync-issues`

---

## Using It as Codex Skills

This repository is not only an automation pipeline. It also includes reusable Codex skills under `skills/`.

Available skills:

- [research-interest-profile](skills/research-interest-profile/SKILL.md)
- [paper-intake-and-normalize](skills/paper-intake-and-normalize/SKILL.md)
- [paper-review-simulator](skills/paper-review-simulator/SKILL.md)
- [problem-solution-extractor](skills/problem-solution-extractor/SKILL.md)
- [report-composer](skills/report-composer/SKILL.md)

Example prompts:

```text
Use $research-interest-profile to revise my research profile.
Use $paper-intake-and-normalize to fetch today's arXiv papers.
Use $paper-review-simulator to critique my paper draft before submission.
Use $problem-solution-extractor to analyze this paper.
Use $report-composer to generate today's report.
```

In practice:

- `skills/` is for interactive use with Codex
- `daily-pipeline` is for scheduled local automation
- `sync-issues` is for pulling structured issue requests into the local workspace

### GitHub Issue Intake

You can let users submit demand through GitHub issues in this repository, then pull those requests into the local workspace.

Current scope and reliability:

- this path is only for the daily paper summary workflow
- it is not an on-demand paper analysis service
- timing is best-effort only, because the automation runs on my laptop instead of always-on infrastructure

User-side view:

- if you are only submitting requests, you only need to open an issue in the required format
- you do not need to care how the deployment side sets up the intake workflow
- after submitting, wait for the next local sync and daily summary cycle

Deployment-side view:

- the operator needs to run `sync-issues` locally to pull issue requests into the workspace
- if `--push` is enabled, the operator can also commit and push generated intake artifacts
- because this runs on a laptop, timing is best-effort rather than guaranteed

Minimal issue format:

```md
---
direction: llm-agents
---

## Background
...

## Requirements
...

## Constraints
...

## Notes
...
```

Run the sync locally:

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
```

With auto push:

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace --push
```

Generated files are written under:

```text
research-workspace/issue-intake/<direction>/<github-username>/
```

Repository rename note:

- by default the command derives `owner/repo` from the current git remote
- if the repository is renamed, update your local remote and the sync command will keep working
- you can also override discovery with `--repo owner/repo`

### How to Install the Skills into Codex

If you want these skills available globally in Codex across repositories, install them into your Codex skills directory:

```bash
~/.codex/skills/
```

Example using symlinks:

```bash
mkdir -p ~/.codex/skills
ln -s /path/to/AutoResearch/skills/research-interest-profile ~/.codex/skills/research-interest-profile
ln -s /path/to/AutoResearch/skills/paper-intake-and-normalize ~/.codex/skills/paper-intake-and-normalize
ln -s /path/to/AutoResearch/skills/paper-review-simulator ~/.codex/skills/paper-review-simulator
ln -s /path/to/AutoResearch/skills/problem-solution-extractor ~/.codex/skills/problem-solution-extractor
ln -s /path/to/AutoResearch/skills/report-composer ~/.codex/skills/report-composer
```

If you prefer, you can copy the directories instead of symlinking them.

After installation, restart Codex if your setup requires a restart before newly added skills are discovered.

### Which Mode Should You Choose?

- Choose **Usage Mode 1** if you want unattended daily automation.
- Choose **Usage Mode 2** if you want interactive, paper-by-paper work with Codex.
- Choose **Usage Mode 3** if you want users to submit daily-summary requests through GitHub issues.

---

## Directory Structure

```text
docs/
├── local-automation-usage.md
└── superpowers/
    ├── plans/
    └── specs/
research-workspace/
├── profile/
│   └── interest-profile.md
├── papers/
│   └── <paper-id>/
│       ├── metadata.json
│       ├── source.pdf
│       ├── problem-solution.md
│       ├── detailed-analysis.md
│       └── state.json
├── reports/
│   ├── daily/
│   └── longterm/
├── exports/
│   └── zotero/
└── pipeline/
    └── run-history.jsonl
scripts/
├── daily_pipeline.py
skills/
├── research-interest-profile/
├── paper-intake-and-normalize/
├── paper-review-simulator/
├── problem-solution-extractor/
└── report-composer/
src/auto_research/
tests/
```

---

## Project Motivation

The motivation is straightforward:

- too many papers are published to track manually,
- but the real value is not just “what was published,”
- the real value is:
  - what problem the paper is actually solving,
  - whether the solution is strong or still weak,
  - whether the paper exposes a gap that could become your next idea.

So ResearchBob is not just a paper fetcher and not just a summarizer.

It is meant to support:

- idea discovery,
- idea summarization,
- idea comparison,
- and long-term direction tracking.

---

## How the Current Pipeline Works

The current automation pipeline:

1. reads `interest-profile.md`
2. runs arXiv intake
3. prefilters and ranks candidates
4. selects Top K papers
5. downloads PDFs
6. generates `problem-solution.md`
7. generates `detailed-analysis.md`
8. generates a daily report
9. generates a daily idea summary
10. updates a long-term summary
11. exports RIS
12. optionally commits and pushes artifacts

---

## Scheduling Example

Run every day at 09:00:

```cron
0 9 * * * cd /path/to/AutoResearch && env -u all_proxy -u http_proxy -u https_proxy PYTHONPATH=src python scripts/daily_pipeline.py >> /tmp/auto-research-daily.log 2>&1
```

---

## Requirements

- Local shell access
- Network access for arXiv and model calls
- An OpenAI-compatible API endpoint for automated ranking and summarization

Declared project target:

- Python `>=3.12`

The current repo is also tested locally on Python 3.11 during development.

---

## Current Limitations

- PDF text extraction is lightweight and best-effort
- the workflow is local-only in this version
- the long-term summary is incrementally updated but still evolving
- output quality still depends on the configured model and gateway

---

## 中文说明

ResearchBob 是一套本地运行的研究自动化流程，用来持续完成这件事：

> 把大量新论文收敛成少量真正值得继续想的 idea。

---

## 三种使用方法

### 使用方法一：作为本地自动化流程

把 AutoResearch 当成一个本地自动化项目来用：

- 定期抓论文
- 自动筛选 Top K
- 下载 PDF
- 生成短摘要和详细分析
- 生成日报和长线总结
- 导出 RIS
- 可选自动提交和 push

这种方式适合你想让它每天自动运行。

这个方式可直接配合下面这段 prompt 交给 AI 助手：

```text
请帮我把这个仓库部署成本地的每天论文总结流程。

仓库路径：/path/to/ResearchBob
工作区路径：/path/to/ResearchBob/research-workspace

请完成这些事情：
1. 如果需要，初始化 workspace。
2. 告诉我还缺哪些环境变量或 `.env.local` 配置。
3. 校验 `daily-pipeline` 和 `sync-issues` 这两个 CLI 命令的用法。
4. 给我一条本地运行每天论文总结的准确命令。
5. 给我一个可选的 cron 示例。

注意：
- 这个部署只服务于每天论文总结。
- GitHub issue intake 因为跑在笔记本上，所以同步和产出时间都不是强保证。
```

### 使用方法二：作为 Codex Skill 使用

把仓库里的 `skills/` 当成一组可复用的 Codex skills 来用。

这种方式适合你想和 Codex 交互式地做这些事：

- 修改研究画像
- 临时抓一批论文
- 单独分析一篇论文
- 生成某天的报告
- 在投稿前模拟 reviewer 对自己 paper 的质疑

这个方式可直接配合下面这段 prompt 交给 AI 助手：

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

### 使用方法三：GitHub Issue 方式

把当前仓库的 GitHub issue 当成“每天论文总结需求入口”来用。

这种方式适合你：

- 想让用户按固定格式提交方向、约束和补充说明
- 想让本地流程在同步时自动拉取这些需求
- 能接受因为服务跑在笔记本上，所以时间是 best-effort 而不是严格保证

这个方式可直接配合下面这段 prompt 交给 AI 助手：

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

### 如何安装成 Codex Skill

如果你想让这些 skills 在别的项目里也能直接用，推荐安装到：

```bash
~/.codex/skills/
```

例如用软链接安装：

```bash
mkdir -p ~/.codex/skills
ln -s /path/to/AutoResearch/skills/research-interest-profile ~/.codex/skills/research-interest-profile
ln -s /path/to/AutoResearch/skills/paper-intake-and-normalize ~/.codex/skills/paper-intake-and-normalize
ln -s /path/to/AutoResearch/skills/paper-review-simulator ~/.codex/skills/paper-review-simulator
ln -s /path/to/AutoResearch/skills/problem-solution-extractor ~/.codex/skills/problem-solution-extractor
ln -s /path/to/AutoResearch/skills/report-composer ~/.codex/skills/report-composer
```

如果不想用软链接，也可以直接复制这些目录。

安装后，如果你的 Codex 环境不会自动刷新 skills，需要重启一次 Codex。

也可以用 prompt 让 AI 助手代你完成安装，例如：

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

### 该选哪一种方式

- 如果你要每天自动跑，用 **使用方法一**
- 如果你要和 Codex 交互式逐篇分析，用 **使用方法二**
- 如果你要让用户通过 GitHub issue 提交每天论文总结需求，用 **使用方法三**

---

## 快速开始

### 1. 初始化工作区

```bash
cd /path/to/ResearchBob
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
```

### 2. 创建本地配置

在仓库根目录创建：

```bash
.env.local
```

建议内容：

```bash
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=http://your-gateway
AUTO_RESEARCH_MODEL=gpt-5.4
```

这个文件已被 git 忽略。

### 3. 编辑研究兴趣画像

主要输入文件：

```text
research-workspace/profile/interest-profile.md
```

校验：

```bash
PYTHONPATH=src python -m auto_research.cli validate-profile research-workspace/profile/interest-profile.md
```

### 4. 运行自动化流程

如果本地代理会影响 arXiv 或模型网关访问，建议在命令前去掉代理变量：

```bash
cd /path/to/ResearchBob
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python scripts/daily_pipeline.py
```

或者直接调用 CLI：

```bash
cd /path/to/ResearchBob
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python -m auto_research.cli daily-pipeline --workspace research-workspace --push
```

---

## 你会得到什么

每篇论文：

- `metadata.json`
- `source.pdf`
- `problem-solution.md`
- `detailed-analysis.md`
- `state.json`

每次运行：

- `reports/daily/<date>.md`
- `reports/daily/<date>-summary.md`
- `reports/daily/<date>-bundle.json`
- `reports/longterm/longterm-summary.md`
- `exports/zotero/<date>.ris`
- `pipeline/run-history.jsonl`

---

## 作为 Codex Skill 使用

这个仓库不只是自动化脚本，也包含可直接作为 Codex skill 使用的内容：

- [research-interest-profile](skills/research-interest-profile/SKILL.md)
- [paper-intake-and-normalize](skills/paper-intake-and-normalize/SKILL.md)
- [paper-review-simulator](skills/paper-review-simulator/SKILL.md)
- [problem-solution-extractor](skills/problem-solution-extractor/SKILL.md)
- [report-composer](skills/report-composer/SKILL.md)

使用方式例如：

```text
Use $research-interest-profile to revise my research profile.
Use $paper-intake-and-normalize to fetch today's arXiv papers.
Use $paper-review-simulator to critique my paper draft before submission.
Use $problem-solution-extractor to analyze this paper.
Use $report-composer to generate today's report.
```

也就是说：

- `skills/` 更适合交互式使用
- `daily-pipeline` 更适合本地自动定时跑

## GitHub Issue 使用方式

你也可以通过当前仓库的 GitHub issue 提需求，再由本地 `sync-issues` 流程把需求拉到工作区。

当前范围和限制：

- 这个入口只服务于每天论文总结这条流程
- 它不是一个随时触发、随时返回结果的论文分析服务
- 因为自动化实际部署在我的笔记本上，不是常驻在线基础设施，所以同步时间和摘要产出时间都无法保证

用户视角：

- 如果你只是提需求，只需要按要求格式写 issue 即可
- 你不需要关注部署端是怎么部署自动抓取服务的
- 提交之后，等待下一次本地同步和每天论文总结流程即可

部署端视角：

- 部署端需要在本地运行 `sync-issues`，把 issue 需求拉到工作区
- 如果使用 `--push`，部署端还可以把 intake 产物自动提交并推送
- 因为服务跑在笔记本上，所以时间特性只能是 best-effort，而不是强保证

最小 issue 格式：

```md
---
direction: llm-agents
---

## Background
...

## Requirements
...

## Constraints
...

## Notes
...
```

本地同步命令：

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
```

如果需要自动提交并 push intake 产物：

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace --push
```

生成目录：

```text
research-workspace/issue-intake/<direction>/<github-username>/
```

补充说明：

- 默认会从当前 git remote 推断 `owner/repo`
- 仓库改名后，只要本地 remote 已更新，这个流程仍然能继续用
- 也可以用 `--repo owner/repo` 手动指定仓库

---

## 目录结构

```text
docs/
├── local-automation-usage.md
└── superpowers/
    ├── plans/
    └── specs/
research-workspace/
├── profile/
│   └── interest-profile.md
├── papers/
│   └── <paper-id>/
│       ├── metadata.json
│       ├── source.pdf
│       ├── problem-solution.md
│       ├── detailed-analysis.md
│       └── state.json
├── reports/
│   ├── daily/
│   └── longterm/
├── exports/
│   └── zotero/
└── pipeline/
    └── run-history.jsonl
scripts/
├── daily_pipeline.py
skills/
├── research-interest-profile/
├── paper-intake-and-normalize/
├── paper-review-simulator/
├── problem-solution-extractor/
└── report-composer/
src/auto_research/
tests/
```

---

## 项目动机

这个项目的动机很直接：

- 论文太多，人工追踪成本太高
- 真正重要的不只是“今天发了什么”
- 更重要的是：
  - 它在解决什么问题
  - 现有 solution 有没有明显缺口
  - 它能不能启发你自己的下一步 idea

所以它不只是一个论文抓取器，也不只是一个自动摘要器。  
它更像一套本地运行的研究助手，帮助你做：

- idea 发现
- idea 总结
- idea 比较
- 长线方向积累

---

## 当前流程会做什么

当前版本会：

1. 读取兴趣画像
2. 抓取 arXiv 候选论文
3. 做预筛选和排序
4. 选出 Top K
5. 下载 PDF
6. 生成 `problem-solution.md`
7. 生成 `detailed-analysis.md`
8. 生成日报
9. 生成每日 idea summary
10. 更新长线总结
11. 导出 RIS
12. 可选自动 `git commit + push`

---

## 定时运行示例

每天早上 9 点：

```cron
0 9 * * * cd /path/to/ResearchBob && env -u all_proxy -u http_proxy -u https_proxy PYTHONPATH=src python scripts/daily_pipeline.py >> /tmp/auto-research-daily.log 2>&1
```

---

## 当前限制

- PDF 文本提取目前仍然是轻量、best-effort 版本
- 这一版仍然是本地运行，不是云端调度
- 长线总结已经可用，但后续还可以继续增强
- 最终输出质量依然取决于模型和网关配置
