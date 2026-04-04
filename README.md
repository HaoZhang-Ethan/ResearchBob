# ResearchBob

[Jump to Chinese / 跳转中文](#中文说明)

ResearchBob is a local paper workflow for turning GitHub issue requests into daily arXiv summaries.

It is designed around one practical loop:

1. a user submits a request through GitHub issue,
2. the local pipeline pulls the request,
3. the system generates a daily paper summary,
4. the maintainer later finalizes GitHub-side actions in a network environment that can reach GitHub.

---

## To the User

If you are here to submit a request and read the output, this is the only part you need.

### What This Does

You can open a GitHub issue in this repository to describe a topic, direction, or constraint for the daily paper summary workflow.

This is not an on-demand paper analysis service.

It is a best-effort daily summary workflow that runs on my laptop.

That means:

- requests are collected through GitHub issues
- summaries are generated in batches, not instantly
- timing is not guaranteed

### How to Submit a Request

Open a GitHub issue with this minimal format:

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

Rules:

- the body must start with YAML frontmatter
- `direction` is required
- the issue title is free-form
- `Background` / `Requirements` / `Constraints` / `Notes` are recommended but not all mandatory

### What You Should Expect

After your issue is processed:

- the request may be folded into the next daily paper summary
- the system may comment on the issue when that request has been consumed
- the issue may then be closed as part of the GitHub finalize step

### Important Limits

- this workflow is only for daily paper summaries
- it does not promise immediate execution
- because it runs on a personal laptop, queue time and completion time are best-effort

### Prompt for Issue Drafting

If you want an AI assistant to turn rough notes into a valid issue, you can paste:

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

## To the Developer

This section is for the person operating the local workflow.

### Workflow

The intended operating flow is:

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace
```

Responsibilities:

- `sync-issues`
  pulls GitHub issues into `research-workspace/issue-intake/`
- `daily-pipeline`
  generates paper outputs and daily summary artifacts
- `finalize-github`
  runs `git push`, comments on consumed issues, and closes them

### Why `finalize-github` Exists

Some environments can reach arXiv and model gateways only under one proxy setup, while GitHub may require another.

So the workflow is intentionally split:

- `daily-pipeline` can run in the environment that works for arXiv and model calls
- `finalize-github` can run later in the environment that works for GitHub

### Workspace Layout

Important paths:

```text
research-workspace/
├── profile/
│   └── interest-profile.md
├── issue-intake/
│   └── <direction>/<github-username>/
│       ├── profile.json
│       ├── summary.md
│       └── requests/<issue-number>.md
├── papers/
├── reports/
│   ├── daily/
│   └── longterm/
├── exports/
│   └── zotero/
└── pipeline/
    ├── run-history.jsonl
    └── github-finalize.json
```

### Fallback Profile Behavior

If `research-workspace/profile/interest-profile.md` is missing:

- `daily-pipeline` will try to synthesize it from `research-workspace/issue-intake/`
- the synthesized profile is written to `profile/interest-profile.md`
- the run continues only if that generated profile passes validation

If the profile already exists:

- it is used as-is
- it is not overwritten

### GitHub Finalize Behavior

`finalize-github` uses `research-workspace/pipeline/github-finalize.json`.

Behavior:

- if the file is missing, there is no pending GitHub finalize work
- if the file is `pending`, the command runs `git push`, then issue comment, then issue close
- if the file is already `completed`, the command does not repeat work

### Network Notes

Common pattern:

- `sync-issues` and `finalize-github` need GitHub connectivity
- `daily-pipeline` needs arXiv and model connectivity

If proxy variables break one side of the workflow, run the commands under different environments.

Example without proxy variables:

```bash
env -u all_proxy -u ALL_PROXY -u http_proxy -u HTTP_PROXY -u https_proxy -u HTTPS_PROXY \
PYTHONPATH=src \
python -m auto_research.cli daily-pipeline --workspace research-workspace
```

### Setup

Initialize a workspace:

```bash
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
```

Set local config in `.env.local`:

```bash
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=http://your-gateway
AUTO_RESEARCH_MODEL=gpt-5.4
```

### CLI Commands

Available commands:

- `init-workspace`
- `validate-profile`
- `intake`
- `validate-extraction`
- `compose-report`
- `daily-pipeline`
- `sync-issues`
- `finalize-github`

### Prompt for Local Deployment

If you want an AI assistant to set up the local workflow, you can paste:

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

### Prompt for Codex Skill Installation

If you want an AI assistant to install the reusable Codex skills, you can paste:

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

### Included Codex Skills

This repository also ships reusable Codex skills:

- [research-interest-profile](skills/research-interest-profile/SKILL.md)
- [paper-intake-and-normalize](skills/paper-intake-and-normalize/SKILL.md)
- [paper-review-simulator](skills/paper-review-simulator/SKILL.md)
- [problem-solution-extractor](skills/problem-solution-extractor/SKILL.md)
- [report-composer](skills/report-composer/SKILL.md)

---

## 中文说明

## To the User

如果你只是来提需求、看日报，这一段就够了。

### 这套系统做什么

你可以通过当前仓库的 GitHub issue 提交一个研究方向、主题或约束，系统会把这些需求纳入“每天论文总结”流程。

它不是一个即时响应的论文分析服务。

它更像一个部署在我笔记本上的、本地运行的、best-effort 的每日总结系统。

这意味着：

- 需求入口是 GitHub issue
- 结果是批量生成的，不是即时返回
- 时间不保证

### 你怎么提需求

请按这个最小格式发 issue：

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

规则：

- 正文第一行就要开始 YAML frontmatter
- `direction` 必填
- issue 标题可以自由写
- `Background` / `Requirements` / `Constraints` / `Notes` 建议写，但不是每一项都强制

### 你可以期待什么

当你的 issue 被处理后：

- 它可能被纳入下一次每天论文总结
- 系统可能会先在 issue 下留言，说明这次需求已经被消费
- 然后 issue 可能被自动关闭

### 重要限制

- 这套流程只服务于每天论文总结
- 不承诺即时执行
- 因为它跑在个人笔记本上，所以排队时间和完成时间都是 best-effort

### 用 Prompt 帮你整理 Issue

如果你想让 AI 助手把零散想法整理成可提交的 issue，可以直接贴这段：

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

## To the Developer

这一段面向维护和运行本地流程的人。

### 标准工作流

推荐按这三步执行：

```bash
PYTHONPATH=src python -m auto_research.cli sync-issues --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli daily-pipeline --workspace research-workspace
PYTHONPATH=src python -m auto_research.cli finalize-github --workspace research-workspace
```

三步职责分别是：

- `sync-issues`
  从 GitHub 拉 issue，写入 `research-workspace/issue-intake/`
- `daily-pipeline`
  生成论文分析、日报和导出文件
- `finalize-github`
  执行 `git push`，然后对被消费的 issue 做 comment 和 close

### 为什么要拆出 `finalize-github`

现实环境里常见的问题是：

- 能访问 arXiv / 模型网关的网络环境，不一定能访问 GitHub
- 能访问 GitHub 的网络环境，不一定适合跑整套论文抓取和模型调用

所以现在设计成两段式：

- `daily-pipeline` 负责内容生成
- `finalize-github` 负责 GitHub 侧收尾

### 工作区结构

关键目录：

```text
research-workspace/
├── profile/
│   └── interest-profile.md
├── issue-intake/
│   └── <direction>/<github-username>/
│       ├── profile.json
│       ├── summary.md
│       └── requests/<issue-number>.md
├── papers/
├── reports/
│   ├── daily/
│   └── longterm/
├── exports/
│   └── zotero/
└── pipeline/
    ├── run-history.jsonl
    └── github-finalize.json
```

### Profile 缺失时的行为

如果 `research-workspace/profile/interest-profile.md` 不存在：

- `daily-pipeline` 会尝试从 `research-workspace/issue-intake/` 自动生成它
- 只有生成结果通过校验，流程才会继续

如果 profile 已经存在：

- 直接使用现有文件
- 不覆盖

### GitHub Finalize 的行为

`finalize-github` 读取：

```text
research-workspace/pipeline/github-finalize.json
```

规则：

- 文件不存在：说明没有待 finalize 的 GitHub 操作
- 文件是 `pending`：执行 `git push`，再 comment / close issue
- 文件是 `completed`：不重复执行

### 网络与代理

常见情况是：

- `sync-issues` 和 `finalize-github` 需要 GitHub 连通性
- `daily-pipeline` 需要 arXiv 和模型网关连通性

如果代理设置会让两边互相冲突，就在不同网络环境里分开执行。

例如去掉代理变量跑 `daily-pipeline`：

```bash
env -u all_proxy -u ALL_PROXY -u http_proxy -u HTTP_PROXY -u https_proxy -u HTTPS_PROXY \
PYTHONPATH=src \
python -m auto_research.cli daily-pipeline --workspace research-workspace
```

### 初始化

初始化工作区：

```bash
PYTHONPATH=src python -m auto_research.cli init-workspace --workspace research-workspace
```

在仓库根目录创建 `.env.local`：

```bash
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=http://your-gateway
AUTO_RESEARCH_MODEL=gpt-5.4
```

### 可用 CLI

可用命令：

- `init-workspace`
- `validate-profile`
- `intake`
- `validate-extraction`
- `compose-report`
- `daily-pipeline`
- `sync-issues`
- `finalize-github`

### 用 Prompt 帮你部署本地流程

如果你想让 AI 助手帮你搭建本地流程，可以直接贴这段：

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

### 用 Prompt 帮你安装 Codex Skill

如果你想让 AI 助手安装可复用的 Codex skills，可以直接贴这段：

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

### 仓库内置的 Codex Skills

这个仓库也包含几组可复用的 Codex skills：

- [research-interest-profile](skills/research-interest-profile/SKILL.md)
- [paper-intake-and-normalize](skills/paper-intake-and-normalize/SKILL.md)
- [paper-review-simulator](skills/paper-review-simulator/SKILL.md)
- [problem-solution-extractor](skills/problem-solution-extractor/SKILL.md)
- [report-composer](skills/report-composer/SKILL.md)
