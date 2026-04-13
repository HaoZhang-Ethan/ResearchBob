[中文版](#chinese-version) | [English](#english-version)

<a id="chinese-version"></a>

## Chinese Version

### 标题
Tackling Intertwined Data and Device Heterogeneities in Federated Learning via Adaptive Dual Side Depth

### 元数据
- paper_id: `2309.13536v4`
- pdf_url: https://arxiv.org/pdf/2309.13536v4
- relevance_band: `high-match`

### 详细总结
根据（噪声很大/几乎全是非文本的）PDF 抽取结果以及所提供的元数据，这篇论文似乎聚焦于联邦学习（FL）中的*联合*（相互交织的）异质性： (i) **设备/系统异质性**（客户端的计算/内存/带宽预算不同）以及 (ii) **数据异质性**（客户端数据分布不同）。所提出的方法——题为 **Adaptive Dual Side Depth**——很可能通过在“两侧”（服务器/客户端，或网络的浅层/深层部分）改变*有效深度*来在客户端之间分配*自适应的模型容量*，从而让更多客户端参与，而不必强制所有人使用同一个固定的模型占用规模。然而，由于抽取出的文本主要是压缩的二进制流和图形对象，无法在此可靠恢复具体算法与理论细节；因此下面的分析会保持保守，只描述与标题/提及的图（例如 weighted aggregation、流程图、switching points、误差对比）一致的可能机制。

### 问题
**目标问题：** 真实部署中的 FL 同时存在*多重*异质性：
- **设备异质性：** 客户端在计算吞吐、内存、能耗与网络条件上不同，使得对弱设备而言，单一“全模型”的本地训练配置不可行。
- **数据异质性（non-IID）：** 客户端的标签/特征分布不同，导致客户端漂移（client drift）与有偏更新。

**交织性：** 两者并非相互独立——例如，弱设备可能也与特定用户群体/数据形态相关；并且部分参与/自适应计算会改变优化动态，可能加剧 non-IID 影响。

**为何现有基线可能失效：**
- 仅处理慢客户端（stragglers）的系统方法（丢弃/超时、客户端选择）可能会使参与集合产生偏差。
- 假设容量同质的个性化或 non-IID 方法可能会排除低端客户端或引入不公平。
- “slimmable/subnet” 方法虽可处理计算，但若设计不当，在 non-IID 下会造成聚合不匹配与不稳定收敛。

### 方案
**高层解法（由标题 + 图文件名推断）：** 引入*自适应深度*方案：每个客户端训练满足其设备约束的深度，同时保持与服务器聚合兼容。

**“Dual Side Depth”** 这一表述暗示深度自适应发生在划分的*两侧*，可能对应以下之一：
1) **客户端侧 vs 服务器侧的深度分配**（在某个层边界处切分），或
2) **浅层共享骨干 + 更深的专用模块**（两段式网络），或
3) **双向深度选择**：客户端可选择激活多少前层与多少后层（可能性较低）。

抽取 PDF 引用了多个以文件名标识的图（例如 `weighted_aggregation.pdf`, `flowchart.pdf`, `different_switching_points.pdf`, `error_over_training_*`, `error_comparison_*`），这与如下系统设计一致：
- 编排每个客户端使用的深度；
- 通过*加权聚合（weighted aggregation）*聚合部分重叠的参数集合；
- 设定*switching points* 的规则（何时改变深度或移动切分点）。

**系统导向角度：** 你提供的摘要明确将其描述为“system-oriented”的容量分配，因此方案很可能包含运行时 profiling（或预算上报）与每轮的深度选择调度/决策逻辑。

### 关键机制
鉴于可读文本有限，最稳妥的机制描述是：

1) **按客户端自适应深度训练**
- 每个客户端仅训练部分层（更“浅”或更“深”的子模型），以匹配其硬件预算。
- 可通过早退出（early-exit）式深度截断、layer dropping，或选择连续的模块块来实现。

2) **保持兼容性的聚合**
- 服务器可在不同深度客户端之间聚合更新而不破坏参数。
- 名为 `weighted_aggregation.pdf` 的图暗示该方法采用 **逐层/考虑参与度的加权**，例如：
  - 对被多数客户端训练的层：采用类似 FedAvg 的标准平均。
  - 对仅少数客户端训练的层（仅强设备参与）：更强正则、更小的服务器步长，或下调权重以避免对小子集过拟合。

3) **自适应的“dual side” 决策逻辑**
- `different_switching_points.pdf` 强烈暗示存在可调的 **switching point**（可能是层边界索引），并在实验中变化该点。
- “dual side” 可能表示模型在 switching point 处概念性切分：一侧始终/通常被训练（广泛参与），另一侧条件性训练（仅有能力的客户端），并通过自适应机制选择该点。

4) **误差 / 更新差异监控**
- `error_comparison_cosine_similarity.pdf` 与 `error_over_training_l1norm.pdf` 等文件名暗示他们度量类似如下的差异：
  - 全模型 vs 截断模型的更新；
  - 重建 vs 原始梯度/更新；
  - 或客户端 vs 全局更新方向。
- 余弦相似度与 L1 范数常用于量化 **更新对齐（update alignment）** 与 **幅度不匹配**，经常用来论证需要某种校正/加权策略。

总体效果：在保持广泛客户端覆盖（公平性/覆盖率）的同时，让高容量客户端贡献更多模型容量，并且在 non-IID 下不致使优化失稳。

### 假设
由于细节不可抽取，这些假设在该类方法中*很可能*成立：

- **模型架构可按深度分解**（如 ResNet blocks、堆叠层的 Transformer），使训练某个前缀/后缀/子集是有意义的。
- **客户端可上报或系统可估计设备能力**（内存/计算预算）以选择深度。
- **不同深度间共享层的参数形状一致**；未训练的层要么保持冻结，要么仅由部分客户端更新，要么通过蒸馏/正则化更新。
- **目标函数可容忍部分参数参与**（即某些层稀疏更新）而不发生灾难性漂移。
- **通信协议支持部分模型传输**（仅上传已训练层/块），或系统能高效掩码缺失更新。

### 优势
1) **直接针对真实部署中数据异质性与设备异质性的交叉问题**，而许多论文往往分开处理。

2) **可能提升参与度与覆盖面**：低端设备可通过更浅子模型贡献，而非作为 straggler 被丢弃。

3) **系统相关性强**：自适应深度是一个具象且立竿见影的系统调节旋钮（时延、内存、能耗、带宽）。

4) **聚合具备感知能力**（由 weighted aggregation 与差异图推断）：若显式处理不匹配，会比朴素“对收到的东西直接平均”更鲁棒。

5) **设计空间探索**（由 “different switching points” 推断）：表明他们研究了切分/深度边界的敏感性，而不是固定一个任意的切分点。

### 弱点
以下是需要从完整论文中核实的潜在弱点/缺口（无法从噪声抽取中确认）：

1) **深层稀疏更新问题**：若只有少数强客户端更新更深层，这些层可能对其 non-IID 数据过拟合，损害全局泛化。

2) **公平性担忧**：从不训练深层的客户端性能可能落后；方法可能隐式偏向强设备。

3) **稳定性与收敛保证**：深度变化的参与会改变有效目标/优化路径；许多类似方法在 non-IID + 部分参与下缺乏严格的收敛刻画。

4) **自适应开销**：profiling、深度选择、维护掩码/部分状态会增加编排复杂度；若频繁自适应，控制面开销可能不可忽视。

5) **架构依赖性**：依赖深度截断的方法在 ResNet 类堆叠结构上可能更有效，而在深度与归一化、注意力或 layer scaling 强耦合的架构上可能效果更差。

6) **交织异质性的建模难度**：“intertwined” 很难被令人信服地证明——论文可能展示了提升，但未能隔离因果机制（设备↔数据相关性、选择偏差等）。

### 仍然缺失的部分
结合你的关注点（FL systems）与“issue-intake directions”，最可操作、最值得在原 PDF 中核查的缺失信息包括：

1) **清晰的系统模型与约束**
- 是否建模了每轮 deadline、straggler 缓解、异构上行带宽、电量、内存限制？
- 是否给出了端到端成本模型（计算时间 + 通信 + 服务器聚合开销）？

2) **调度与选择的交互**
- 若客户端自行选择深度，这与客户端采样如何交互？系统是否会反复选择有能力的客户端来更新深层？

3) **端侧实现细节**
- 深度切换如何在常见 FL 栈（如 PyTorch/TensorFlow Mobile）中实现？
- 是否支持量化/混合精度，以及它与深度的交互方式？

4) **对动态条件的鲁棒性**
- 客户端是否能因热降频、后台负载或网络波动在不同轮次改变深度？
- 在这种随时间变化的深度分配下系统是否稳定？

5) **隐私/安全影响**
- 自适应深度与部分更新可能改变泄露面；此外，少量客户端产生的深层更新可能更具可识别性。

6) **超越深度的泛化**
- 许多系统采用 width/adapters/LoRA 类低秩更新；dual-side depth 是否优于或可与这些组合？若未讨论，这是一个缺口。

### 为什么与当前方向相关
就 **FL-sys** 的兴趣画像而言，这篇论文匹配度高，因为：

- **深度是第一类系统旋钮**：可直接映射到计算/内存/时延约束，并可按客户端、按轮次控制。
- **交织异质性是现实默认**：真实部署很少只有 non-IID 或只有设备差异。
- **可能带来新的 issue-intake 方向**：调度策略、部分聚合协议、公平性/覆盖率保证都是核心系统问题，而深度自适应 FL 既能赋能也会复杂化这些问题。

即便缺少全文，(i) weighted aggregation、(ii) switching point 敏感性、(iii) 更新差异度量 这三者的组合也暗示作者试图让深度自适应具备*优化感知（optimization-aware）*，这对系统设计尤为重要——否则系统改动容易 destabilize 训练。

### 可继续推进的想法
围绕 “adaptive dual side depth” 的具体、系统导向的后续方向：

1) **面向 deadline 的深度调度（服务器策略）**
- 构建每轮优化：在 round deadline 与带宽预算下，选择客户端集合 + 每客户端深度，以最大化期望精度增益。
- 使用 bandits/RL 或约束优化；与启发式 switching-point 规则对比。

2) **公平性与覆盖保证**
- 加入约束，避免深层更新被少数人口统计/设备类别主导。
- 探索显式抵消“少客户端深层更新”偏差的正则项或重加权。

3) **部分更新压缩协议**
- 将深度自适应与稀疏/部分传输协同设计：例如只发送变化的 blocks + sketching。
- 在规模化场景评估服务器 CPU/内存开销（维护 masked states）。

4) **非平稳资源下的动态深度**
- 客户端根据观测到的 step time 或热限制在线调整深度。
- 需要滞回/稳定机制（避免 switching points 振荡）。

5) **与安全聚合的兼容性**
- 安全聚合通常假设固定向量形状。为可变深度更新设计 **mask-compatible secure aggregation** 协议（例如 padding + masked sums；或逐层安全聚合分组）。

6) **相关性感知的异质性建模**
- 显式建模/测量设备类别与数据分布的相关性；评估 dual-side depth 是降低还是放大选择偏差。
- 构造 device/data 异质性可控耦合的基准。

7) **超越深度：adapters/低秩的双侧更新**
- 用参数高效模块（adapters/LoRA）替代“深侧”更新，仅由有能力客户端训练，同时所有客户端训练共享 trunk。
- 可能比稀疏更新深层更稳定。

8) **理论视角：逐层部分参与**
- 为“每层有独立参与率与 non-IID 漂移”的 FL 建立收敛界；识别何时加权聚合是必要/充分的。

如果你能提供更干净的文本抽取（或仅方法部分），我可以把机制描述收紧到更具体，并精确定位其相对既有 slimmable/split/personalized FL 方法的确切新颖点。

### 关联短摘要
### 一句话总结
提出一种面向系统的联邦学习（FL）方法，在客户端与服务器两侧自适应分配模型深度/容量，以更好应对数据异质性与设备（算力/内存）异质性的耦合影响。

### 问题
标准FL方法在以下情况下表现不佳：(a) 客户端数据为非IID；(b) 客户端设备资源约束差异很大；且这两类异质性会相互作用——导致“一刀切”模型对部分客户端低效或不可行，并可能损害收敛性/准确率。

### 方案
一种自适应方法（“adaptive dual side depth”）：在不同客户端之间（并可能在服务器端的聚合路径上）分配不同的有效模型深度/容量，使资源受限的客户端可训练更小的子模型，而资源更充足的客户端可训练更深的模型；并配套一种协调/聚合机制，旨在在异质参与条件下保持全局学习质量。

### 核心贡献
- 形式化/聚焦数据异质性与设备异质性共同影响FL性能的*交织*设定（作者主张，基于标题/摘要层面的描述）。
- 提出一种跨客户端与服务器两侧的自适应深度/容量分配机制（作者主张）。
- 面向系统的设计，旨在在非IID数据下，在不牺牲（或提升）准确率的同时，使受硬件限制的广泛客户端仍可参与训练（作者主张）。

### 证据依据
- 仅有标题 + 所提供的摘要式描述可用；未审阅PDF内容（方法、公式、实验）。
- 提供文本中未给出数据集/指标/基线对比，因此无法在此核验其实证支持。

### 局限性
- （基于所给文本）不清楚如何在可变深度模型之间进行聚合（例如参数对齐、蒸馏、分层聚合），以及是否存在理论保证。
- 开销未知：调度、个性化与全局一致性的权衡、通信成本，以及在真实设备上的实现复杂度。
- 其对部分参与、拖慢者（stragglers）与动态资源可用性（FL系统常见问题）的鲁棒性尚未验证。

### 与研究方向的相关性
与FL-sys高度匹配：直接处理系统约束（设备异质性）与统计异质性交织的问题，并通过自适应容量分配保持多样化客户端持续参与——符合面向实际异构FL的问题收集方向。

### 分析备注
推断：这类似于异构模型FL / 拆分容量（split-capacity）或可伸缩网络（slimmable-network）思路在FL中的改造，但在缺少PDF的情况下，具体机制及“dual side”作用位置仍不确定。建议阅读重点：(1) 深度分配如何决定（在线？按轮次？资源感知与数据感知？），(2) 不同深度的模型更新如何聚合，(3) 是否有超越准确率的真实设备/系统评估（时延、能耗、掉线）。

<a id="english-version"></a>

## English Version

# Tackling Intertwined Data and Device Heterogeneities in Federated Learning via Adaptive Dual Side Depth

## Metadata
- paper_id: `2309.13536v4`
- pdf_url: https://arxiv.org/pdf/2309.13536v4
- relevance_band: `high-match`

## Detailed Summary
From the (very noisy/mostly-non-text) PDF extraction plus the provided metadata, this paper appears to address *joint* (intertwined) heterogeneity in Federated Learning (FL): (i) **device/systems heterogeneity** (clients have different compute/memory/bandwidth budgets) and (ii) **data heterogeneity** (clients have different distributions). The proposed approach—titled **Adaptive Dual Side Depth**—likely allocates *adaptive model capacity* across clients by varying *effective depth* on both “sides” (server/client, or shallow/deep parts of the network), enabling more clients to participate without forcing a single fixed model footprint. However, because the extracted text is largely compressed binary streams and figure objects, the detailed algorithmic and theoretical specifics cannot be reliably recovered here; the analysis below is therefore conservative and focuses on plausible mechanisms consistent with the title/figures mentioned (e.g., weighted aggregation, flowchart, switching points, error comparisons).

## Problem
**Targeted problem:** FL in real deployments suffers from *simultaneous* heterogeneities:
- **Device heterogeneity:** clients differ in compute throughput, memory, energy, and network conditions, making a single “full model” local training configuration infeasible for weak devices.
- **Data heterogeneity (non-IID):** clients’ label/feature distributions differ, leading to client drift and biased updates.

**Intertwined aspect:** these are not independent—e.g., weaker devices may also correlate with specific user populations/data regimes; and partial participation/adaptive computation changes the optimization dynamics, potentially worsening non-IID effects.

**Why existing baselines can fail:**
- Systems methods that only address stragglers (drop/timeout, client selection) can bias the participating set.
- Personalization or non-IID methods that assume homogeneous capacity may exclude low-end clients or induce unfairness.
- “Slimmable/subnet” methods may handle compute but can create aggregation mismatch and unstable convergence under non-IID if not carefully designed.

## Solution
**High-level solution (inferred from title + figure filenames):** Introduce an *adaptive depth* scheme where each client trains a model with depth that fits its device constraints while remaining compatible for aggregation.

The phrase **“Dual Side Depth”** suggests depth adaptation may occur on *two sides* of a partition, likely one of:
1) **Client-side vs server-side depth allocation** (a split at some layer boundary), or
2) **Shallow shared backbone + deeper specialized blocks** (two-part network), or
3) **Bidirectional depth choice**: clients can choose how many early layers and how many late layers to activate (less likely).

The extracted PDF references multiple figures by filename (e.g., `weighted_aggregation.pdf`, `flowchart.pdf`, `different_switching_points.pdf`, `error_over_training_*`, `error_comparison_*`), which is consistent with a system that:
- orchestrates which depth each client uses,
- aggregates partially-overlapping parameter sets via *weighted aggregation*,
- has a rule for *switching points* (when to change depth or when to move a cut).

**System-oriented angle:** The summary you provided explicitly frames it as “system-oriented” capacity allocation, so the solution likely includes runtime profiling (or budget reporting) and scheduling/decision logic for depth selection per round.

## Key Mechanism
Given the limited readable text, the most defensible mechanism description is:

1) **Depth-adaptive training per client**
- Each client trains only a subset of layers (a “shallower” or “deeper” submodel) according to its hardware budget.
- This can be implemented via early-exit style depth truncation, layer dropping, or selecting contiguous blocks.

2) **Compatibility-preserving aggregation**
- Server aggregates updates from clients of different depths without corrupting parameters.
- The presence of a figure named `weighted_aggregation.pdf` suggests the method uses **layer-wise / participation-aware weighting**, e.g.:
  - For layers trained by many clients: standard FedAvg-like averaging.
  - For layers trained by few (only strong devices): heavier regularization, smaller server step, or down-weighting to avoid overfitting to a small subset.

3) **Adaptive “dual side” decision logic**
- A figure `different_switching_points.pdf` strongly hints at a tunable **switching point** (likely a boundary index of layers) and experiments varying it.
- “Dual side” could mean the model is conceptually split at a switching point: one side is always/mostly trained (broad participation), the other side is conditionally trained (only capable clients), with an adaptive mechanism to pick that point.

4) **Error / update discrepancy monitoring**
- Filenames like `error_comparison_cosine_similarity.pdf` and `error_over_training_l1norm.pdf` suggest they measure discrepancy between something like:
  - full-model vs truncated-model updates,
  - reconstructed vs original gradients/updates,
  - or client vs global update directions.
- Cosine similarity and L1 norm are typical to quantify **update alignment** and **magnitude mismatch**, often used to motivate a correction/weighting strategy.

Net effect: keep broad client coverage (fairness/coverage) while allowing high-capacity clients to contribute more model capacity, without destabilizing optimization under non-IID.

## Assumptions
Because the details are not extractable, these assumptions are *likely* given the approach class:

- **Model architecture is depth-decomposable** (e.g., ResNet blocks, Transformers with stacked layers) such that training a prefix/suffix/subset is meaningful.
- **Clients can report or the system can estimate device capability** (memory/compute budget) to select depth.
- **Parameter shapes are consistent across depths** for shared layers; untrained layers either remain frozen, are updated only by some clients, or are updated via distillation/regularization.
- **The objective tolerates partial parameter participation** (i.e., some layers updated sparsely) without catastrophic drift.
- **Communication protocol supports partial model transmission** (upload only trained layers/blocks), or the system can efficiently mask absent updates.

## Strengths
1) **Directly targets the real deployment intersection** of data heterogeneity and device heterogeneity, which many papers treat separately.

2) **Potentially improves participation and coverage**: low-end devices can still contribute via a shallower submodel instead of being dropped as stragglers.

3) **System relevance**: adaptive depth is a tangible knob with immediate systems payoff (latency, memory, energy, bandwidth).

4) **Aggregation awareness** (suggested by weighted aggregation and discrepancy plots): if they explicitly handle mismatch, it can be more robust than naïve “average whatever arrives.”

5) **Design space exploration** (suggested by “different switching points”): indicates they studied sensitivity to the cut/depth boundary rather than fixing an arbitrary split.

## Weaknesses
These are plausible weaknesses/gaps to verify from the full paper (cannot be confirmed from the noisy extraction):

1) **Sparse update problem for deep layers**: if only a small subset of powerful clients update deeper layers, those layers may overfit to their non-IID data, harming global generalization.

2) **Fairness concerns**: performance on clients that never train deep layers may lag; the method might implicitly prioritize strong devices.

3) **Stability and convergence guarantees**: depth-varying participation changes the effective objective/optimization path; many such methods lack rigorous convergence characterization under non-IID + partial participation.

4) **Overhead of adaptivity**: profiling, selecting depths, and maintaining masks/partial state can add orchestration complexity; if adaptation is frequent, control-plane overhead may be nontrivial.

5) **Architecture dependence**: methods that rely on depth truncation may work best on ResNet-like stacks and less well on architectures where depth interacts strongly with normalization, attention, or layer scaling.

6) **Intertwined heterogeneity modeling**: “intertwined” is hard to demonstrate convincingly—paper may show improvements but not isolate causal mechanisms (device↔data correlation, selection bias, etc.).

## What Is Missing
Given your profile focus (FL systems) and “issue-intake directions,” the most actionable missing pieces (to check in the actual PDF) are:

1) **Clear systems model and constraints**
- Do they model per-round deadlines, straggler mitigation, heterogeneous uplink bandwidth, battery, memory limits?
- Do they provide an end-to-end cost model (compute time + communication + server aggregation overhead)?

2) **Scheduling + selection interaction**
- If clients choose depth, how does this interact with client sampling? Is there a risk that the system repeatedly selects capable clients to update deep layers?

3) **On-device implementation details**
- How is depth switching implemented in common FL stacks (e.g., PyTorch/TensorFlow Mobile)?
- Do they support quantization/mixed precision, and how does that interact with depth?

4) **Robustness to dynamic conditions**
- Can a client change depth across rounds due to thermal throttling, background load, network fluctuation?
- Does the system remain stable under such time-varying depth assignments?

5) **Privacy/security implications**
- Adaptive depth and partial updates can change leakage surfaces; also, deep-layer updates coming from few clients may be more identifying.

6) **Generalization beyond depth**
- Many systems use width/adapters/LoRA-like low-rank updates; does dual-side depth outperform/compose with these? If not discussed, that’s a gap.

## Why It Matters To Profile
For an **FL-sys** interest profile, this paper is a high-match because:

- **Depth is a first-class systems knob**: it maps directly to compute/memory/latency constraints and can be controlled per-client per-round.
- **Intertwined heterogeneity is the practical default**: real deployments rarely have only non-IID or only device variability.
- **Potential for new issue-intake directions**: scheduling policies, partial aggregation protocols, and fairness/coverage guarantees are core systems concerns that depth-adaptive FL can enable but also complicate.

Even without full text, the combination of (i) weighted aggregation, (ii) switching point sensitivity, and (iii) update discrepancy metrics suggests the authors are trying to make depth adaptivity *optimization-aware*, which is especially relevant for systems designs that otherwise risk destabilizing training.

## Possible Follow-Up Ideas
Concrete, systems-oriented follow-ups that build on “adaptive dual side depth”:

1) **Deadline-aware depth scheduling (server policy)**
- Formulate a per-round optimization: choose client set + per-client depth to maximize expected accuracy gain under a round deadline and bandwidth budget.
- Use bandits/RL or constrained optimization; compare to heuristic switching-point rules.

2) **Fairness and coverage guarantees**
- Add constraints so that deep layers are not dominated by a small demographic/device class.
- Explore regularizers or reweighting that explicitly counteracts the “few-client deep update” bias.

3) **Partial-update compression protocol**
- Co-design depth adaptivity with sparse/partial transmission: e.g., send only changed blocks + sketching.
- Evaluate server CPU/memory overhead for maintaining masked states at scale.

4) **Dynamic depth under nonstationary resources**
- Clients adapt depth on-the-fly based on observed step time or thermal limits.
- Need hysteresis/stability mechanisms (avoid oscillations in switching points).

5) **Secure aggregation compatibility**
- Secure aggregation typically assumes fixed vector shapes. Design a protocol for **mask-compatible secure aggregation** with variable depth updates (e.g., padded + masked sums; or per-layer secure aggregation groups).

6) **Correlation-aware heterogeneity modeling**
- Explicitly model/measure correlation between device class and data distribution; evaluate whether dual-side depth reduces or amplifies selection bias.
- Create benchmarks where device/data heterogeneity are controllably coupled.

7) **Beyond depth: adapters/low-rank dual-side updates**
- Replace “deep side” updates with parameter-efficient modules (adapters/LoRA) trained only by capable clients, while all clients train the shared trunk.
- Could yield better stability than sparsely-updated deep layers.

8) **Theoretical lens: layer-wise partial participation**
- Develop convergence bounds for FL where each layer has its own participation rate and non-IID drift; identify conditions when weighted aggregation is necessary/sufficient.

If you can provide a cleaner text extraction (or just the method section), I can tighten this into a much more specific mechanism description and pinpoint the exact novelty vs prior slimmable/split/personalized FL methods.

## Linked Short Summary
# One-Sentence Summary
Proposes a system-oriented FL method that adaptively allocates model depth/capacity on both client and server sides to better handle the coupled effects of data heterogeneity and device (compute/memory) heterogeneity.

# Problem
Standard FL methods struggle when (a) client data are non-IID and (b) client devices have varying resource constraints, and these two heterogeneities interact—making one-size-fits-all models inefficient or infeasible for some clients and potentially harming convergence/accuracy.

# Proposed Solution
An adaptive approach (“adaptive dual side depth”) that assigns different effective model depths/capacities across clients (and potentially server aggregation paths) so resource-limited clients can train smaller submodels while richer clients train deeper ones, with a coordination/aggregation mechanism intended to preserve global learning quality under heterogeneous participation.

# Claimed Contributions
- Formulates/targets the *intertwined* setting where data and device heterogeneity jointly impact FL performance (author claim, based on title/abstract-level description).
- Introduces an adaptive depth/capacity allocation mechanism across both client and server sides (author claim).
- System-oriented design intended to enable broad client participation despite hardware limits while maintaining/improving accuracy under non-IID data (author claim).

# Evidence Basis
- Only title + provided summary/abstract-like description were available; no PDF content (methods, equations, experiments) was reviewed.
- No reported datasets/metrics/baselines are available from the provided text, so empirical support cannot be verified here.

# Limitations
- Unclear (from provided text) how aggregation is performed across variable-depth models (e.g., parameter alignment, distillation, hierarchical aggregation) and what theoretical guarantees exist.
- Unknown overheads: scheduling, personalization vs. global consistency, communication cost, and implementation complexity on real devices.
- Unverified robustness to partial participation, stragglers, and dynamic resource availability—common in FL systems.

# Relevance to Profile
High match for FL-sys: directly addresses system constraints (device heterogeneity) intertwined with statistical heterogeneity, and focuses on adaptive capacity allocation to keep diverse clients active—aligned with issue-intake directions around practical heterogeneous FL.

# Analyst Notes
Inference: this resembles heterogeneous-model FL / split-capacity or slimmable-network ideas adapted to FL, but the exact mechanism and where “dual side” applies is uncertain without the PDF. Recommend reading for: (1) how depth assignment is decided (online? per-round? resource- and data-aware?), (2) how model updates from different depths are aggregated, and (3) any real-device or systems evaluation beyond accuracy (latency, energy, dropout).
