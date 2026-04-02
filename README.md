# AutoResearch

[中文说明 / Chinese](#中文说明)

AutoResearch is a local research-automation workflow for continuously discovering, filtering, analyzing, and summarizing arXiv papers around a persistent research profile.

It is designed for the following loop:

1. maintain a long-term research-interest profile
2. fetch fresh arXiv papers
3. rank and shortlist candidates
4. analyze selected papers in a structured way
5. generate daily and long-term summaries
6. export a Zotero-compatible RIS file
7. optionally commit and push generated artifacts back to GitHub

## Highlights

- Local-first workflow
- Profile-driven paper discovery
- Top-K candidate selection
- Structured short summaries and deeper per-paper analysis
- Daily summary and rolling long-term summary
- Zotero RIS export
- Optional fully automated `git commit + push`

## Project Structure

```text
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
```

## What the Pipeline Produces

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

## Requirements

- Python 3.12 target project layout
- Local shell access
- Network access for arXiv and model calls
- An OpenAI-compatible API endpoint for automated summarization/ranking

The code runs fine in local dev on Python 3.11 in this repo, but the declared project target remains `>=3.12`.

## Local Configuration

Create a local config file in the repository root:

```bash
.env.local
```

Recommended contents:

```bash
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=http://your-gateway
AUTO_RESEARCH_MODEL=gpt-5.4
```

This file is ignored by git.

## Quick Start

### 1. Initialize a workspace

```bash
cd /path/to/AutoResearch
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
```

### 2. Create or edit the research profile

Main profile file:

```text
research-workspace/profile/interest-profile.md
```

Validate it:

```bash
PYTHONPATH=src python -m auto_research.cli validate-profile research-workspace/profile/interest-profile.md
```

### 3. Run the daily pipeline

If local proxy variables interfere with direct arXiv or model-gateway access, unset them for the command:

```bash
cd /path/to/AutoResearch
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python scripts/daily_pipeline.py
```

Or use the CLI form:

```bash
cd /path/to/AutoResearch
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python -m auto_research.cli daily-pipeline --workspace research-workspace --push
```

## Daily Pipeline Behavior

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
11. exports Zotero RIS
12. optionally commits and pushes artifacts

## Scheduling

Example cron entry for running every day at 09:00:

```cron
0 9 * * * cd /path/to/AutoResearch && env -u all_proxy -u http_proxy -u https_proxy PYTHONPATH=src python scripts/daily_pipeline.py >> /tmp/auto-research-daily.log 2>&1
```

## Notes on Current Version

The automation is intentionally incremental:

- candidate ranking is automated
- PDF download is automated
- short and detailed summaries are automated
- daily and long-term summaries are automated

The system is meant to support idea discovery, not to replace careful paper reading.

## Known Limits

- PDF text extraction is currently best-effort and lightweight
- the workflow is local-only in this version
- the long-term summary is incrementally updated but still evolving
- model output quality depends on the configured provider/model

## 中文说明

AutoResearch 是一套本地运行的研究自动化流程，用来持续完成下面这件事：

1. 维护长期研究兴趣画像
2. 定期抓取 arXiv 新论文
3. 对候选论文做筛选
4. 对选中的论文做结构化分析
5. 生成日报和长线总结
6. 导出 Zotero 可导入的 RIS 文件
7. 可选自动提交并 push 到 GitHub

## 主要特点

- 本地优先
- 基于兴趣画像筛选论文
- 自动 Top-K 选择
- 逐篇短摘要和更详细分析
- 日报 + 长线总结
- Zotero RIS 导出
- 可选自动 `git commit + push`

## 主要输出

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

## 本地配置

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

## 快速开始

### 1. 初始化工作区

```bash
cd /path/to/AutoResearch
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
```

### 2. 编辑研究兴趣画像

主要输入文件：

```text
research-workspace/profile/interest-profile.md
```

校验：

```bash
PYTHONPATH=src python -m auto_research.cli validate-profile research-workspace/profile/interest-profile.md
```

### 3. 运行自动化流程

如果本地代理会影响 arXiv 或模型网关访问，建议在命令前去掉代理变量：

```bash
cd /path/to/AutoResearch
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python scripts/daily_pipeline.py
```

或者直接调用 CLI：

```bash
cd /path/to/AutoResearch
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python -m auto_research.cli daily-pipeline --workspace research-workspace --push
```

## 当前自动化流程会做什么

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

## 定时运行示例

每天早上 9 点：

```cron
0 9 * * * cd /path/to/AutoResearch && env -u all_proxy -u http_proxy -u https_proxy PYTHONPATH=src python scripts/daily_pipeline.py >> /tmp/auto-research-daily.log 2>&1
```

## 当前版本说明

这套自动化是逐步增强出来的，目标是帮助你：

- 发现值得继续想的论文
- 总结 problem / solution
- 形成日报和长期方向感

它不是为了代替精读论文，而是为了把“找方向、筛论文、积累 insight”这件事自动化。

## 当前限制

- PDF 文本提取目前是轻量、best-effort 版本
- 这一版仍然是本地运行，不是云端调度
- 长线总结已经可用，但后续还可以继续增强
- 最终输出质量仍然依赖模型和网关配置
