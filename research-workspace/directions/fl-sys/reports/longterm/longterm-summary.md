[中文版](#chinese-version) | [English](#english-version)

<a id="chinese-version"></a>

## Chinese Version

# 长期总结

## 最近更新来源
- 日报: `2026-04-13.md`

## 新纳入论文
- FedP3: Heterogeneous Federated Learning with Personalized Neural Network Pruning
- Tackling Intertwined Data and Device Heterogeneities in Federated Learning via Adaptive Dual Side Depth
- Distributed Pruning Towards Tiny Neural Networks in Federated Learning
- Towards Scalable and Non-IID Robust Hierarchical Federated Learning via Label-Driven Knowledge Aggregator

## 当前问题簇
- 算子融合 / 融合边界
- 指令调度 / 内核执行
- 面向硬件的编译决策

## 新发现
- FedP3 在资源受限场景下研究异构联邦学习，采用个性化模型剪枝，使具有不同计算与带宽预算的客户端能更高效地训练与通信，同时保持模型质量。
- 本文聚焦数据异质性与设备异质性相互交织的联邦学习，提出系统导向的方法：分配自适应模型容量，使具备不同硬件限制与数据特征的客户端都能有效参与。
- Distributed Pruning 研究如何在联邦设置中训练紧凑神经网络，强调当客户端资源有限时，通信效率与设备端效率之间的权衡。
- 该工作研究分层联邦学习以提升可扩展性与非 IID 鲁棒性，使用标签驱动的知识聚合设计，在多层级之间协调学习，而非单一扁平的服务器-客户端拓扑。

## 技术趋势分析
## 新兴技术趋势（FL-sys）
- **将模型可塑性作为系统控制旋钮** 正在收敛为两类方法：
  1) **基于剪枝/稀疏性的按客户端子网络**（FedP3；Distributed Pruning）。
  2) **按客户端的可变执行深度 / 分层参与**（Adaptive Dual Side Depth）。
- **部分/异构聚合正变得“层/掩码感知”**：聚合规则越来越多地考虑 **参数参与率**（例如加权聚合；缺层/缺参数更新）。
- **通过拓扑实现可扩展性**：**分层联邦学习（HFL）** 被视为大规模部署的路径，聚合从权重平均逐步转向 **知识/标签条件化聚合**（Label-Driven Knowledge Aggregator）。
- **非 IID 鲁棒性正在被重述为条件化/路由问题**：
  - HFL 中的标签条件化知识迁移；
  - 子网络方法中的重叠/兼容性约束（隐式）；
  - 明确关注 **设备+数据异质性相互交织**，而非将二者割裂对待。

## 需要跟踪的跨论文技术张力
- **容量偏置**：额外容量（未剪枝权重 / 更深层）往往只由少量、且通常不具代表性的子集更新 → 公平性 + 泛化风险。
- **控制平面成为瓶颈**：决定掩码/深度、随时间更新它们、以及维护服务器端状态的成本，可能超过所宣称的数据平面节省。
- **协议现实性缺口**：许多方法依赖部分更新，但对 **线上字节数（bytes-on-wire）**、元数据/掩码编码、安全聚合兼容性、以及在 churn/慢客户端（stragglers）下的端到端运行时描述不足。


## 当前滚动总结
# 长期滚动总结（FL-sys）

## 范围 / 当前状态
- 聚焦：**联邦学习系统（FL-sys）**，偏向 **主动 issue-intake 方向**。
- 证据基底目前包含 4 篇异质性/可扩展性论文（2 篇高匹配：Adaptive Dual Side Depth；Label-Driven HFL Aggregator；2 篇相邻：FedP3；Distributed Pruning）。

## 问题簇（以已审论文集为依据）
1) **系统 + 统计异质性（相互交织）**
   - 设备约束（计算/内存/带宽）与非 IID 漂移的联合（Adaptive Dual Side Depth）。
2) **通过容量自适应提升通信/计算效率**
   - 个性化剪枝 / 分布式剪枝，生成更小的客户端工作负载与载荷（FedP3；Distributed Pruning）。
3) **通过分层拓扑实现可扩展性**
   - 边缘/云多层聚合；降低扇入与协调负担（Label-Driven Knowledge Aggregator）。
4) **参数/层级别的部分参与**
   - 某些层/权重仅由部分客户端更新（深度截断、剪枝掩码）→ 新的聚合与公平性问题。

## 反复出现的缺口 / 需测试的共性弱点（已与证据关联）
- **端到端核算缺失或薄弱**：
  - 真实 **线上字节数（bytes-on-wire）**，包括掩码/索引/元数据；
  - **服务器 CPU/内存/状态** 随按客户端掩码/深度策略的扩展性；
  - 在慢客户端（stragglers）/churn 与异构上行链路下的 **墙钟时间 makespan**；
  - **能耗 / 端侧运行时**（尤其是结构化 vs 非结构化稀疏）。
- **安全聚合不兼容风险**：
  - 变形状更新（深度/掩码）常与固定向量安全聚合冲突；许多论文未解决。
- **部分层参与下的容量偏置 + 公平性**：
  - 深层 / 未剪枝容量由少数客户端更新 → 长尾客户端可能退化；全局模型可能偏向高端设备。
- **控制平面/编排描述不足**：
  - 谁来选择深度/掩码、多久改变一次、如何对时变预算（温控/电量/网络）做出响应。
- **“条件化”信号引入的隐私泄露向量**：
  - 标签驱动聚合可能泄露标签分布；掩码/深度选择可能成为侧信道。

## 最有前景方向（面向 FL-sys issue-intake 的优先级）
1) **面向部分更新的协议 + 系统协同设计**
   - 为可变深度 / 掩码更新标准化可落地协议：掩码编码、用于安全聚合的填充/遮蔽，以及可测量的线上字节数。
2) **结合容量自适应的截止期感知调度**
   - 联合选择（客户端集合、按客户端的深度/稀疏度）以满足轮次截止期与带宽上限；显式建模慢客户端与动态预算。
3) **分层参与建模 + 偏置控制**
   - 将每层/参数组视为拥有各自参与率；加入重加权/正则，使很少更新的容量不会对狭窄子集过拟合。
4) **带隐私保护标签信号的 HFL 知识聚合**
   - 将标签驱动聚合与 DP/安全统计结合；测试其对被操纵的标签信号与不稳定层级结构的鲁棒性。
5) **结构化（可部署）的效率机制**
   - 优先结构化剪枝 / 块或通道丢弃 / adapters，而非非结构化稀疏；用真实设备内核与能耗进行验证。

## 论文级锚点（用于后续综合）
- **Adaptive Dual Side Depth (2309.13536v4)**：与“交织异质性”最一致；可作为调度 + 分层参与理论的良好起点。
- **Label-Driven HFL Aggregator (2209.14520v2)**：可扩展性框架强；关键未解问题是隐私 + 协议复杂度。
- **FedP3 (2404.09816v1)** & **Distributed Pruning (2212.01977v2)**：是实现异构设备参与的有前景杠杆，但若不完整说明/测量掩码开销、结构化加速，以及在 churn 下的稳定性，很可能无法通过 FL-sys 的审视。


<a id="english-version"></a>

## English Version

# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-13.md`

## Newly Selected Papers
- FedP3: Heterogeneous Federated Learning with Personalized Neural Network Pruning
- Tackling Intertwined Data and Device Heterogeneities in Federated Learning via Adaptive Dual Side Depth
- Distributed Pruning Towards Tiny Neural Networks in Federated Learning
- Towards Scalable and Non-IID Robust Hierarchical Federated Learning via Label-Driven Knowledge Aggregator

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- FedP3 studies heterogeneous federated learning under resource constraints, using personalized model pruning so clients with different compute and bandwidth budgets can train and communicate more efficiently while retaining model quality.
- This paper targets federated learning under intertwined data and device heterogeneity, proposing a system-oriented approach that allocates adaptive model capacity so clients with different hardware limits and data characteristics can participate effectively.
- Distributed Pruning looks at how to train compact neural networks in federated settings, emphasizing communication and device-efficiency tradeoffs that matter when clients have limited resources.
- This work studies hierarchical federated learning for scalability and non-IID robustness, using a label-driven knowledge aggregation design to coordinate learning across multiple levels rather than a single flat server-client topology.

## Technical Trend Analysis
## Emerging technical trends (FL-sys)
- **Model plasticity as a systems control knob** is consolidating into two families:
  1) **Per-client subnetworks via pruning/sparsity** (FedP3; Distributed Pruning).
  2) **Per-client variable execution depth / layer participation** (Adaptive Dual Side Depth).
- **Partial/heterogeneous aggregation is becoming layer-/mask-aware**: aggregation rules increasingly account for **parameter participation rates** (e.g., weighted aggregation; missing-layer/missing-parameter updates).
- **Scalability via topology**: **Hierarchical FL (HFL)** is framed as the path to large deployments, with aggregation moving from weight averaging toward **knowledge/label-conditioned aggregation** (Label-Driven Knowledge Aggregator).
- **Non-IID robustness is being reframed as conditioning/routing**:
  - label-conditioned knowledge transfer in HFL;
  - overlap/compatibility constraints (implicit) in subnetwork methods;
  - explicit focus on **intertwined device+data heterogeneity** rather than treating them separately.

## Cross-paper technical tensions to track
- **Capacity bias**: extra capacity (unpruned weights / deeper layers) tends to be updated by a small, often non-representative subset → fairness + generalization risks.
- **Control-plane becomes the bottleneck**: deciding masks/depth, updating them over time, and maintaining server state can dominate vs the purported data-plane savings.
- **Protocol realism gap**: many approaches rely on partial updates but under-specify **bytes-on-wire**, metadata/mask encoding, secure aggregation compatibility, and end-to-end runtime under churn/stragglers.


## Current Rolling Summary
# Long-Term Rolling Summary (FL-sys)

## Scope / current status
- Focus: **federated learning systems (FL-sys)** with bias toward **active issue-intake directions**.
- Evidence base now includes 4 heterogeneity/scalability papers (2 high-match: Adaptive Dual Side Depth; Label-Driven HFL Aggregator; 2 adjacent: FedP3; Distributed Pruning).

## Problem clusters (grounded in the reviewed set)
1) **System + statistical heterogeneity (intertwined)**
   - Joint device constraints (compute/memory/bandwidth) + non-IID drift (Adaptive Dual Side Depth).
2) **Communication-/compute-efficiency via capacity adaptation**
   - Personalized pruning / distributed pruning to produce smaller client workloads and payloads (FedP3; Distributed Pruning).
3) **Scalability via hierarchical topology**
   - Edge/cloud multi-level aggregation; reduce fan-in and coordination load (Label-Driven Knowledge Aggregator).
4) **Partial participation at the parameter/layer level**
   - Some layers/weights updated by only a subset of clients (depth truncation, pruning masks) → new aggregation and fairness problems.

## Recurring gaps / common weaknesses to test for (now evidence-linked)
- **End-to-end accounting missing or weak**:
  - true **bytes-on-wire** incl. masks/indices/metadata;
  - **server CPU/memory/state scaling** for per-client masks/depth policies;
  - **wall-clock makespan** under stragglers/churn and heterogeneous uplinks;
  - **energy / on-device runtime** (esp. structured vs unstructured sparsity).
- **Secure aggregation incompatibility risk**:
  - variable-shape updates (depth/masks) often clash with fixed-vector secure aggregation; many papers don’t resolve this.
- **Capacity bias + fairness under partial layer participation**:
  - deep layers / unpruned capacity updated by few clients → tail clients can degrade; global model may skew toward high-end devices.
- **Control-plane/orchestration under-specified**:
  - who chooses depth/mask, how often it changes, how it reacts to time-varying budgets (thermal/battery/network).
- **Privacy leakage vectors introduced by “conditioning” signals**:
  - label-driven aggregation can leak label distribution; masks/depth choices can become side channels.

## Most promising directions (prioritized for FL-sys issue-intake)
1) **Protocol + systems co-design for partial updates**
   - Standardize a practical protocol for variable-depth / masked updates with: mask encoding, padding/masking for secure agg, and measured bytes-on-wire.
2) **Deadline-aware scheduling with capacity adaptation**
   - Jointly choose (client set, per-client depth/sparsity) to meet round deadlines and bandwidth caps; explicitly model stragglers and dynamic budgets.
3) **Layer-wise participation modeling + bias control**
   - Treat each layer/parameter group as having its own participation rate; add reweighting/regularization so rarely-updated capacity doesn’t overfit to a narrow subset.
4) **HFL knowledge aggregation with privacy-preserving label signals**
   - Combine label-driven aggregation with DP/secure stats; test robustness to manipulated label signals and unstable hierarchies.
5) **Structured (deployable) efficiency mechanisms**
   - Prefer structured pruning / block/channel dropping / adapters over unstructured sparsity; validate with real device kernels and energy.

## Paper-specific anchors (for future synthesis)
- **Adaptive Dual Side Depth (2309.13536v4)**: strongest alignment to intertwined heterogeneity; good seed for scheduling + layer-wise participation theory.
- **Label-Driven HFL Aggregator (2209.14520v2)**: strong scalability framing; key open issues are privacy + protocol complexity.
- **FedP3 (2404.09816v1)** & **Distributed Pruning (2212.01977v2)**: promising hetero-device participation lever, but most likely to fail FL-sys scrutiny unless they fully specify/measure mask overhead, structured speedups, and stability under churn.
