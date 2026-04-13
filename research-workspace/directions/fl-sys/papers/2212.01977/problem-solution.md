---
paper_id: "2212.01977v2"
title: "Distributed Pruning Towards Tiny Neural Networks in Federated Learning"
confidence: "low"
relevance_band: "adjacent"
opportunity_label: "manual-review"
---

[中文版](#chinese-version) | [English](#english-version)

<a id="chinese-version"></a>

## Chinese Version

### 一句话总结
该论文旨在通过一种分布式剪枝方法显著缩小联邦学习模型，在尽量保持精度的同时满足客户端计算/内存限制并降低通信开销。

### 问题
（作者声称；仅由标题/摘要推断）标准 FL 训练与通信的是完整尺寸的稠密模型，这对资源受限客户端可能过重且通信代价高；在 FL 中进行朴素剪枝可能因非 IID 数据、客户端异构性以及协同开销而变得困难。

### 方案
（作者声称；推断）将一种分布式剪枝方法集成到 FL 训练循环中，在客户端间逐步（或联合）剪除网络权重/结构，使全局模型变得“tiny”，从而可能同时降低端上开销与通信载荷。

### 核心贡献
- 一种用于在分布式（客户端-服务器）环境下剪枝神经网络的联邦学习框架/算法（推断）。
- 对在 FL 中剪枝时通信效率、设备效率（计算/内存）与模型精度之间权衡的研究（由总结推断）。
- 在 FL 约束下实现紧凑/微型网络的经验结果展示（可能，但未在未阅读 PDF 的情况下验证）。

### 证据依据
- 仅基于标题 + 已提供的总结（未检查 PDF 内容）。
- 从所给文本中无法获得具体数据集、基线、剪枝日程/策略、聚合细节或指标。

### 局限性
- 不清楚剪枝是非结构化还是结构化，以及稀疏性如何表示/通信（稠密掩码可能抵消通信收益）。
- 在非 IID 数据、部分参与和硬件异构性下的鲁棒性未知——这些是 FL 剪枝的常见失效模式。
- 不清楚通信节省是否以端到端（线缆字节数，bytes-on-wire）衡量，还是仅以参数数量衡量。
- 无法看到与相关基线的对比（例如 FedAvg + 事后剪枝、FedDST、彩票票据式 FL 等）。

### 与研究方向的相关性
与 FL 系统的相关性为中高：剪枝会直接影响通信轮数、载荷大小、客户端内存/计算以及在受限设备上的可部署性；相关性取决于该工作是否提供系统真实的核算（压缩格式、稀疏传输、客户端异构性）。

### 分析备注
建议人工审阅：（1）“distributed pruning”具体指什么（由谁决定掩码？逐客户端还是全局？），（2）稀疏性是否带来真实通信降低（例如坐标+数值编码、结构化剪枝），（3）在非 IID 与部分参与下的评估，以及（4）与 FedDST/其他稀疏 FL 基线的对比方式。若论文报告墙钟时间/线缆字节数与设备内存占用测量，则其与 FL-sys 的匹配度可能从“相邻”提升为“高度匹配”。

<a id="english-version"></a>

## English Version

# One-Sentence Summary
The paper targets making federated learning models much smaller via a distributed pruning approach that aims to balance accuracy with client compute/memory limits and reduced communication.

# Problem
(Author-claimed, inferred from title/abstract only) Standard FL trains/communicates full-size dense models, which can be too heavy for resource-constrained clients and expensive in communication; naïve pruning in FL may be hard due to non-IID data, heterogeneous clients, and coordination overhead.

# Proposed Solution
(Author-claimed, inferred) A distributed pruning method integrated into the FL training loop to progressively (or jointly) prune network weights/structures across clients so that the global model becomes “tiny,” potentially reducing both on-device cost and communication payload.

# Claimed Contributions
- A federated learning framework/algorithm for pruning neural networks in a distributed (client-server) setting (inferred).
- A study of tradeoffs between communication efficiency, device efficiency (compute/memory), and model accuracy when pruning in FL (inferred from summary).
- Empirical results demonstrating compact/tiny networks achievable under FL constraints (likely, but unverified without PDF).

# Evidence Basis
- Only title + provided summary (no PDF content inspected).
- No concrete datasets, baselines, pruning schedule, aggregation details, or metrics available from the provided text.

# Limitations
- Unclear whether pruning is unstructured vs structured, and how sparsity is represented/communicated (dense masks can erase comms gains).
- Unknown robustness under non-IID data, partial participation, and heterogeneous hardware—common failure modes for pruning in FL.
- Unclear whether communication savings are measured end-to-end (wire bytes) vs just parameter counts.
- No visibility into comparisons versus related baselines (e.g., FedAvg + post-hoc pruning, FedDST, lottery-ticket-style FL).

# Relevance to Profile
Adjacent-to-high for FL systems: pruning directly impacts communication rounds, payload size, client memory/compute, and deployability on constrained devices; relevance depends on whether the work provides system-realistic accounting (compression format, sparse transmission, client heterogeneity).

# Analyst Notes
Manual review recommended: check (1) what exactly is “distributed pruning” (who decides masks? per-client vs global?), (2) whether sparsity yields real communication reduction (e.g., coordinate + value encoding, structured pruning), (3) evaluation under non-IID and partial participation, and (4) how it compares to FedDST/other sparse-FL baselines. If the paper reports wall-clock/bytes-on-wire and device-memory measurements, it may move from adjacent to high-match for FL-sys.
