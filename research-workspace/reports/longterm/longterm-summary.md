# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-04.md`

## Newly Selected Papers
- CORAL: Towards Autonomous Multi-Agent Evolution for Open-Ended Discovery
- No Attacker Needed: Unintentional Cross-User Contamination in Shared-State LLM Agents
- EvolveTool-Bench: Evaluating the Quality of LLM-Generated Tool Libraries as Software Artifacts
- $\texttt{YC-Bench}$: Benchmarking AI Agents for Long-Term Planning and Consistent Execution
- When Users Change Their Mind: Evaluating Interruptible Agents in Long-Horizon Web Navigation
- Asymmetric Actor-Critic for Multi-turn LLM Agents
- PHMForge: A Scenario-Driven Agentic Benchmark for Industrial Asset Lifecycle Maintenance
- SKILL0: In-Context Agentic Reinforcement Learning for Skill Internalization
- Detecting Multi-Agent Collusion Through Multi-Agent Interpretability
- LangMARL: Natural Language Multi-Agent Reinforcement Learning

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- Large language model (LLM)-based evolution is a promising approach for open-ended discovery, where progress requires sustained search and knowledge accumulation. Existing methods still rely heavily on fixed heuristics and hard-coded exploration rules, which limit the autonomy of LLM agents. We present CORAL, the first framework for autonomous multi-agent evolution on open-ended problems. CORAL replaces rigid control with long-running agents that explore, reflect, and collaborate through shared persistent memory, asynchronous multi-agent execution, and heartbeat-based interventions. It also provides practical safeguards, including isolated workspaces, evaluator separation, resource management, and agent session and health management. Evaluated on diverse mathematical, algorithmic, and systems optimization tasks, CORAL sets new state-of-the-art results on 10 tasks, achieving 3-10 times higher improvement rates with far fewer evaluations than fixed evolutionary search baselines across tasks. On Anthropic's kernel engineering task, four co-evolving agents improve the best known score from 1363 to 1103 cycles. Mechanistic analyses further show how these gains arise from knowledge reuse and multi-agent exploration and communication. Together, these results suggest that greater agent autonomy and multi-agent evolution can substantially improve open-ended discovery. Code is available at https://github.com/Human-Agent-Society/CORAL.
- LLM-based agents increasingly operate across repeated sessions, maintaining task states to ensure continuity. In many deployments, a single agent serves multiple users within a team or organization, reusing a shared knowledge layer across user identities. This shared persistence expands the failure surface: information that is locally valid for one user can silently degrade another user's outcome when the agent reapplies it without regard for scope. We refer to this failure mode as unintentional cross-user contamination (UCC). Unlike adversarial memory poisoning, UCC requires no attacker; it arises from benign interactions whose scope-bound artifacts persist and are later misapplied. We formalize UCC through a controlled evaluation protocol, introduce a taxonomy of three contamination types, and evaluate the problem in two shared-state mechanisms. Under raw shared state, benign interactions alone produce contamination rates of 57--71%. A write-time sanitization is effective when shared state is conversational, but leaves substantial residual risk when shared state includes executable artifacts, with contamination often manifesting as silent wrong answers. These results indicate that shared-state agents need artifact-level defenses beyond text-level sanitization to prevent silent cross-user failures.
- Modern LLM agents increasingly create their own tools at runtime -- from Python functions to API clients -- yet existing benchmarks evaluate them almost exclusively by downstream task completion. This is analogous to judging a software engineer only by whether their code runs, ignoring redundancy, regression, and safety. We introduce EvolveTool-Bench, a diagnostic benchmark for LLM-generated tool libraries in software engineering workflows. Across three domains requiring actual tool execution (proprietary data formats, API orchestration, and numerical computation), we define library-level software quality metrics -- reuse, redundancy, composition success, regression stability, and safety -- alongside a per-tool Tool Quality Score measuring correctness, robustness, generality, and code quality. In the first head-to-head comparison of code-level and strategy-level tool evolution (ARISE vs. EvoSkill vs. one-shot baselines, 99 tasks, two models), we show that systems with similar task completion (63-68%) differ by up to 18% in library health, revealing software quality risks invisible to task-only evaluation. Our results highlight that evaluation and governance of LLM-generated tools require treating the evolving tool library as a first-class software artifact, not a black box.
- As LLM agents tackle increasingly complex tasks, a critical question is whether they can maintain strategic coherence over long horizons: planning under uncertainty, learning from delayed feedback, and adapting when early mistakes compound. We introduce $\texttt{YC-Bench}$, a benchmark that evaluates these capabilities by tasking an agent with running a simulated startup over a one-year horizon spanning hundreds of turns. The agent must manage employees, select task contracts, and maintain profitability in a partially observable environment where adversarial clients and growing payroll create compounding consequences for poor decisions. We evaluate 12 models, both proprietary and open source, across 3 seeds each. Only three models consistently surpass the starting capital of \$200K, with Claude Opus 4.6 achieving the highest average final funds at \$1.27 M, followed by GLM-5 at \$1.21 M at 11$\times$ lower inference cost. Scratchpad usage, the sole mechanism for persisting information across context truncation, is the strongest predictor of success, and adversarial client detection is the primary failure mode, accounting for $47\%$ of bankruptcies. Our analysis reveals that frontier models still fail through distinct failure modes such as over-parallelization, demonstrating the capability gaps for long-horizon performance. $\texttt{YC-Bench}$ is open-source, reproducible, and configurable.
- As LLM agents transition from short, static problem solving to executing complex, long-horizon tasks in dynamic environments, the ability to handle user interruptions, such as adding requirement or revising goals, during mid-task execution is becoming a core requirement for realistic deployment. However, existing benchmarks largely assume uninterrupted agent behavior or study interruptions only in short, unconstrained language tasks. In this paper, we present the first systematic study of interruptible agents in long-horizon, environmentally grounded web navigation tasks, where actions induce persistent state changes. We formalize three realistic interruption types, including addition, revision, and retraction, and introduce InterruptBench, a benchmark derived from WebArena-Lite that synthesizes high-quality interruption scenarios under strict semantic constraints. Using a unified interruption simulation framework, we evaluate six strong LLM backbones across single- and multi-turn interruption settings, analyzing both their effectiveness in adapting to updated intents and their efficiency in recovering from mid-task changes. Our results show that handling user interruptions effectively and efficiently during long-horizon agentic tasks remains challenging for powerful large-scale LLMs. Code and dataset are available at https://github.com/HenryPengZou/InterruptBench.
- Large language models (LLMs) exhibit strong reasoning and conversational abilities, but ensuring reliable behavior in multi-turn interactions remains challenging. In many real-world applications, agents must succeed in one-shot settings where retries are impossible. Existing approaches either rely on reflection or post-hoc evaluation, which require additional attempts, or assume fully trainable models that cannot leverage proprietary LLMs. We propose an asymmetric actor-critic framework for reliable conversational agents. A powerful proprietary LLM acts as the actor, while a smaller open-source critic provides runtime supervision, monitoring the actor's actions and intervening within the same interaction trajectory. Unlike training-based actor-critic methods, our framework supervises a fixed actor operating in open-ended conversational environments. The design leverages a generation-verification asymmetry: while high-quality generation requires large models, effective oversight can often be achieved by smaller ones. We further introduce a data generation pipeline that produces supervision signals for critic fine-tuning without modifying the actor. Experiments on $τ$-bench and UserBench show that our approach significantly improves reliability and task success over strong single-agent baselines. Moreover, lightweight open-source critics rival or surpass larger proprietary models in the critic role, and critic fine-tuning yields additional gains over several state-of-the-art methods.
- Large language model (LLM) agents are increasingly deployed for complex tool-orchestration tasks, yet existing benchmarks fail to capture the rigorous demands of industrial domains where incorrect decisions carry significant safety and financial consequences. To address this critical gap, we introduce PHMForge, the first comprehensive benchmark specifically designed to evaluate LLM agents on Prognostics and Health Management (PHM) tasks through realistic interactions with domain-specific MCP servers. Our benchmark encompasses 75 expert-curated scenarios spanning 7 industrial asset classes (turbofan engines, bearings, electric motors, gearboxes, aero-engines) across 5 core task categories: Remaining Useful Life (RUL) Prediction, Fault Classification, Engine Health Analysis, Cost-Benefit Analysis, and Safety/Policy Evaluation. To enable rigorous evaluation, we construct 65 specialized tools across two MCP servers and implement execution-based evaluators with task-commensurate metrics: MAE/RMSE for regression, F1-score for classification, and categorical matching for health assessments. Through extensive evaluation of leading frameworks (ReAct, Cursor Agent, Claude Code) paired with frontier LLMs (Claude Sonnet 4.0, GPT-4o, Granite-3.0-8B), we find that even top-performing configurations achieve only 68\% task completion, with systematic failures in tool orchestration (23\% incorrect sequencing), multi-asset reasoning (14.9 percentage point degradation), and cross-equipment generalization (42.7\% on held-out datasets). We open-source our complete benchmark, including scenario specifications, ground truth templates, tool implementations, and evaluation scripts, to catalyze research in agentic industrial AI.
- Agent skills, structured packages of procedural knowledge and executable resources that agents dynamically load at inference time, have become a reliable mechanism for augmenting LLM agents. Yet inference-time skill augmentation is fundamentally limited: retrieval noise introduces irrelevant guidance, injected skill content imposes substantial token overhead, and the model never truly acquires the knowledge it merely follows. We ask whether skills can instead be internalized into model parameters, enabling zero-shot autonomous behavior without any runtime skill retrieval. We introduce SKILL0, an in-context reinforcement learning framework designed for skill internalization. SKILL0 introduces a training-time curriculum that begins with full skill context and progressively withdraws it. Skills are grouped offline by category and rendered with interaction history into a compact visual context, teaching he model tool invocation and multi-turn task completion. A Dynamic Curriculum then evaluates each skill file's on-policy helpfulness, retaining only those from which the current policy still benefits within a linearly decaying budget, until the agent operates in a fully zero-shot setting. Extensive agentic experiments demonstrate that SKILL0 achieves substantial improvements over the standard RL baseline (+9.7\% for ALFWorld and +6.6\% for Search-QA), while maintaining a highly efficient context of fewer than 0.5k tokens per step. Our code is available at https://github.com/ZJU-REAL/SkillZero.
- As LLM agents are increasingly deployed in multi-agent systems, they introduce risks of covert coordination that may evade standard forms of human oversight. While linear probes on model activations have shown promise for detecting deception in single-agent settings, collusion is inherently a multi-agent phenomenon, and the use of internal representations for detecting collusion between agents remains unexplored. We introduce NARCBench, a benchmark for evaluating collusion detection under environment distribution shift, and propose five probing techniques that aggregate per-agent deception scores to classify scenarios at the group level. Our probes achieve 1.00 AUROC in-distribution and 0.60--0.86 AUROC when transferred zero-shot to structurally different multi-agent scenarios and a steganographic blackjack card-counting task. We find that no single probing technique dominates across all collusion types, suggesting that different forms of collusion manifest differently in activation space. We also find preliminary evidence that this signal is localised at the token level, with the colluding agent's activations spiking specifically when processing the encoded parts of their partner's message. This work takes a step toward multi-agent interpretability: extending white-box inspection from single models to multi-agent contexts, where detection requires aggregating signals across agents. These results suggest that model internals provide a complementary signal to text-level monitoring for detecting multi-agent collusion, particularly for organisations with access to model activations. Code and data are available at https://github.com/aaronrose227/narcbench.
- Large language model (LLM) agents struggle to autonomously evolve coordination strategies in dynamic environments, largely because coarse global outcomes obscure the causal signals needed for local policy refinement. We identify this bottleneck as a multi-agent credit assignment problem, which has long been studied in classical multi-agent reinforcement learning (MARL) but remains underaddressed in LLM-based systems. Building on this observation, we propose LangMARL, a framework that brings credit assignment and policy gradient evolution from cooperative MARL into the language space. LangMARL introduces agent-level language credit assignment, pioneers gradient evolution in language space for policy improvement, and summarizes task-relevant causal relations from replayed trajectories to provide dense feedback and improve convergence under sparse rewards. Extensive experiments across diverse cooperative multi-agent tasks demonstrate improved sample efficiency, interpretability, and strong generalization.

## Current Rolling Summary
# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-04.md`

## Current Problem Clusters
- **LLM agents: reliability and control in realistic deployment**
  - Long-horizon planning, consistent execution, and adaptation under delayed consequences
  - Interruptibility and mid-trajectory goal revision
  - Shared-state memory, cross-user contamination, and scope-aware persistence
  - Runtime oversight via critics, behavioral gating, and anti-sycophancy controls
  - Skill acquisition/internalization vs inference-time retrieval
  - Tool creation and maintenance as evolving software artifacts
- **LLM agents: multi-agent autonomy and oversight**
  - Open-ended multi-agent search/evolution with persistent shared memory
  - Multi-agent collusion, interpretability, and oversight under distribution shift
  - Benchmarks for realistic multi-agent and industrial agent settings
- **NV-FPGA security and identity**
  - Clone resistance, persistent device identity, mutation/configuration-derived trust anchors
  - Lifecycle security: enrollment, updates, recovery, revocation, and long-term stability
- **Background systems/compiler cluster**
  - Operator fusion / fusion boundaries
  - Instruction scheduling / kernel execution
  - Hardware-aware compiler decisions

## Recurring Gaps / Common Weaknesses
- **Benchmark-to-deployment gap**
  - Many agent papers diagnose failure modes well but stop at benchmark exposure rather than deployable fixes.
- **State semantics gap**
  - Memory and persistence remain weakly specified: what is shared, who owns it, when it is valid, and how it is revised are often unclear.
- **Isolation and authority gap**
  - Shared-state agents still lack principled user isolation, artifact scoping, and authority boundaries; text sanitization alone is insufficient when executable artifacts persist.
- **Control/corrigibility gap**
  - Interruptibility, anti-sycophancy, and critic-style oversight help, but many methods look like runtime patching rather than solutions to objective misspecification or uncertainty-aware action selection.
- **Mechanism gap in multi-agent safety**
  - Work on collusion/coordination often emphasizes detection after the fact rather than incentive design, enforceable constraints, or protocol-level prevention.
- **Long-horizon competence gap**
  - Strong models still fail on persistent planning due to weak scratchpad use, adversarial-state handling, compounding mistakes, and over-parallelization.
- **Artifact quality gap for agent tooling**
  - Task success can hide poor tool-library health: redundancy, regressions, brittle composition, and unsafe code evolution.
- **Skill-transfer gap**
  - Retrieval-based skills add token overhead and noise; internalization is promising but evidence is still task-bounded.
- **NV-specificity gap**
  - For NV-FPGA, the key filter remains whether persistence materially changes security, provisioning, or deployment advantage over SRAM FPGA baselines.
- **Lifecycle evaluation gap in NV-FPGA security**
  - Security claims still need stronger evidence on aging, temperature, repeatability, attack resistance, field update behavior, and operational lifecycle handling.

## New Insights
- The strongest active intake remains **LLM-agent issue scouting**, especially papers exposing realistic reliability failures rather than pure capability gains.
- A major emerging systems problem is **shared-state contamination**: benign multi-user reuse of memory/artifacts can silently degrade later outcomes, especially when executable artifacts are shared.
- **Interruptibility and changing user intent** now look like first-class requirements for deployed agents, not edge cases.
- Long-horizon benchmarks are increasingly useful when they expose concrete mechanisms of failure, especially **memory persistence strategy, adversarial detection, and compounding execution errors**.
- Runtime oversight appears to be bifurcating into two promising styles: **critic/supervisor architectures** for action monitoring and **behavioral gating** for targeted control failures like sycophancy.
- Multi-agent work is splitting into two important tracks: **productive autonomy** (e.g., open-ended evolution) and **safety oversight** (e.g., collusion detection via internals).
- Tool-generation research is improving by treating the tool library as a **software artifact** rather than evaluating only downstream task completion.
- In NV-FPGA, the clearest validated hardware direction remains **persistent, mutation/configuration-based device identity and clone resistance**, with lifecycle realism still underexplored.

## Most Promising Directions
- **Prioritize agent papers aligned with realistic deployment failures**
  - Especially shared-state contamination, interruptibility, long-horizon consistency, controllability, and runtime oversight.
- **Favor principled state/memory architectures**
  - Prefer work that defines scoping, ownership, revision, isolation, and artifact validity semantics over prompt-level mitigations.
- **Track benchmarks that expose actionable failure taxonomies**
  - Best targets: long-horizon execution, changing goals, persistent state, multi-user settings, tool maintenance, and industrial orchestration.
- **Follow runtime supervision architectures**
  - Critic-based monitoring and asymmetric oversight look promising when they improve reliability without requiring retraining the main actor.
- **Watch skill internalization closely**
  - Internalizing skills may reduce retrieval noise and context cost if it generalizes beyond narrow benchmarks.
- **Track multi-agent oversight beyond text-level monitoring**
  - Interpretability-based collusion detection is promising, but should be paired with mechanism design and constraints.
- **Keep tool-library quality as a first-class evaluation target**
  - Reuse, regressions, composition, robustness, and safety matter for agent systems that generate or evolve code.
- **Keep NV-FPGA security as the main hardware subtrack**
  - Focus on clone resistance, persistent identity, bitstream/configuration-derived trust, and lifecycle-aware security evaluation.
- **Apply a strict NV-advantage filter**
  - Prefer work where non-volatility clearly improves identity retention, tamper resistance, provisioning, recovery, or deployability.

## Current Stance
- **Primary active direction:** LLM-agent robustness under realistic deployment constraints, especially memory/state isolation, interruptibility, long-horizon execution, runtime oversight, and multi-agent safety.
- **Most salient subproblems:** cross-user contamination in shared memory, adaptation to changed user intent, persistent planning failures, and tool/library quality under autonomous code generation.
- **Primary hardware direction:** NV-FPGA security centered on persistent clone-resistant identity and configuration/mutation-based trust primitives.
- **Overall filter:** prioritize papers that surface real operational failure modes and provide mechanisms or evaluation setups that could transfer beyond narrow benchmarks.
