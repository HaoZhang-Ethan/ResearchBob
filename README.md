# AutoResearch

## 中文说明

AutoResearch 是一个本地运行的自动化研究流程，用来帮助你：

- 维护长期研究兴趣画像
- 定期抓取 arXiv 论文
- 自动筛选 Top K 候选论文
- 生成短摘要与更详细的逐篇分析
- 生成日报与长线总结
- 导出 Zotero 可识别的 RIS 文件
- 自动提交并 push 结果到 GitHub

### 主要命令

当前 CLI 提供：

```bash
PYTHONPATH=src python -m auto_research.cli --help
```

可用命令：

- `init-workspace`
- `validate-profile`
- `intake`
- `validate-extraction`
- `compose-report`
- `daily-pipeline`

### 本地配置

推荐在仓库根目录创建一个本地文件：

```bash
.env.local
```

内容示例：

```bash
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=http://your-gateway
AUTO_RESEARCH_MODEL=gpt-5.4
```

这个文件已经被 `.gitignore` 忽略，不会被正常提交。

### 初始化工作区

```bash
cd /path/to/AutoResearch
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
```

主要输入文件：

- `research-workspace/profile/interest-profile.md`

### 手动运行自动化流程

如果你的环境里设置了代理，而这些代理会影响直连 arXiv 或 API 网关，建议在命令前去掉本地代理变量：

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

### 自动化流程会做什么

当前版本的流程会：

1. 读取研究兴趣画像
2. 抓取 arXiv 候选论文
3. 做轻量筛选
4. 选择 Top K 论文
5. 下载 PDF
6. 生成 `problem-solution.md`
7. 生成 `detailed-analysis.md`
8. 生成日报和长线总结
9. 导出 RIS
10. 可选自动 `git commit + push`

### 主要输出目录

- `research-workspace/papers/<paper-id>/metadata.json`
- `research-workspace/papers/<paper-id>/source.pdf`
- `research-workspace/papers/<paper-id>/problem-solution.md`
- `research-workspace/papers/<paper-id>/detailed-analysis.md`
- `research-workspace/papers/<paper-id>/state.json`
- `research-workspace/reports/daily/<date>.md`
- `research-workspace/reports/daily/<date>-summary.md`
- `research-workspace/reports/daily/<date>-bundle.json`
- `research-workspace/reports/longterm/longterm-summary.md`
- `research-workspace/exports/zotero/<date>.ris`
- `research-workspace/pipeline/run-history.jsonl`

### 定时运行示例

每天早上 9 点运行：

```cron
0 9 * * * cd /path/to/AutoResearch && env -u all_proxy -u http_proxy -u https_proxy PYTHONPATH=src python scripts/daily_pipeline.py >> /tmp/auto-research-daily.log 2>&1
```

## English

AutoResearch is a local automation workflow for:

- maintaining a persistent research-interest profile
- fetching arXiv papers on a schedule
- ranking and selecting Top K candidates
- generating short and detailed per-paper analyses
- producing a daily summary and a long-term rolling summary
- exporting Zotero-compatible RIS files
- optionally committing and pushing generated outputs back to GitHub

### Available CLI Commands

```bash
PYTHONPATH=src python -m auto_research.cli --help
```

Commands:

- `init-workspace`
- `validate-profile`
- `intake`
- `validate-extraction`
- `compose-report`
- `daily-pipeline`

### Local Configuration

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

### Initialize a Workspace

```bash
cd /path/to/AutoResearch
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
```

Main input file:

- `research-workspace/profile/interest-profile.md`

### Run the Daily Pipeline

If local proxy environment variables interfere with direct arXiv or gateway access, unset them for the command:

```bash
cd /path/to/AutoResearch
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python scripts/daily_pipeline.py
```

Or via CLI:

```bash
cd /path/to/AutoResearch
env -u all_proxy -u http_proxy -u https_proxy \
PYTHONPATH=src \
python -m auto_research.cli daily-pipeline --workspace research-workspace --push
```

### What the Pipeline Does

The current workflow:

1. reads the research-interest profile
2. fetches arXiv candidates
3. runs lightweight ranking
4. selects Top K papers
5. downloads PDFs
6. generates `problem-solution.md`
7. generates `detailed-analysis.md`
8. generates daily and long-term summaries
9. exports RIS
10. optionally runs `git commit + push`

### Main Output Paths

- `research-workspace/papers/<paper-id>/metadata.json`
- `research-workspace/papers/<paper-id>/source.pdf`
- `research-workspace/papers/<paper-id>/problem-solution.md`
- `research-workspace/papers/<paper-id>/detailed-analysis.md`
- `research-workspace/papers/<paper-id>/state.json`
- `research-workspace/reports/daily/<date>.md`
- `research-workspace/reports/daily/<date>-summary.md`
- `research-workspace/reports/daily/<date>-bundle.json`
- `research-workspace/reports/longterm/longterm-summary.md`
- `research-workspace/exports/zotero/<date>.ris`
- `research-workspace/pipeline/run-history.jsonl`

### Cron Example

Run every day at 09:00:

```cron
0 9 * * * cd /path/to/AutoResearch && env -u all_proxy -u http_proxy -u https_proxy PYTHONPATH=src python scripts/daily_pipeline.py >> /tmp/auto-research-daily.log 2>&1
```
