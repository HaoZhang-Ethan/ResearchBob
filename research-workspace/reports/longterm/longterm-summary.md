# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-09.md`

## Newly Selected Papers
- Digitally Mutating NV-FPGAs into Physically Clone-Resistant Units

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- The concept of Secret Unknown Ciphers (SUCs) was introduced a decade ago as a new visionary concept without devising practical real-world examples. The major contribution of this work is to show the feasibility of "self-mutating" unknown cipher-modules for physical security applications in a non-volatile FPGA environment. The mutated devices may then serve as clone-resistant physical units. The mutated unpredictable physical-digital modules represent consistent and low-cost physical identity alternatives to the traditional analog Physically Unclonable Functions (PUFs). PUFs were introduced two decades ago as unclonable analog physical identities which are relatively complex and suffer from operational inconsistencies. We present a novel and practical SUC-creation technique based on pre-compiled cipher-layout-templates in FPGAs. A devised bitstream-manipulator serves as "mutation generator" to randomly-manipulate the bitstream without violating the FPGA design rules. Two large cipher classes (class-size larger than $2^{1000}$) are proposed with optimally designed structure for a non-volatile FPGA fabric structure. The cipher-mutation process is just a simple random unknown-cipher-selection by consulting the FPGA's internal True Random Number Generator (TRNG). The security levels and qualities of the proposed ciphers are evaluated. The attained security levels are scalable and even adaptable to the post-quantum cryptography. The hardware and software complexities of the created SUCs are experimentally prototyped in a real field FPGA technology to show very promising results.

## Current Rolling Summary
# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-09.md`

## Current Problem Clusters
- **LLM agents: reliability and control in realistic deployment**
  - Long-horizon planning, execution consistency, and adaptation under delayed consequences
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
  - Clone resistance, persistent device identity, and configuration-derived trust anchors
  - Digital alternatives to analog PUFs using configuration-native mechanisms
  - Mutation/self-randomization flows for per-device identity generation
  - Lifecycle security: enrollment, updates, recovery, revocation, and long-term stability
  - Configuration-level mechanisms that exploit non-volatility rather than treating it as incidental
- **Background systems/compiler cluster**
  - Operator fusion / fusion boundaries
  - Instruction scheduling / kernel execution
  - Hardware-aware compiler decisions

## Recurring Gaps / Common Weaknesses
- **Benchmark-to-deployment gap**
  - Many agent papers expose failures well but stop short of deployable fixes.
- **State semantics gap**
  - Memory and persistence remain weakly specified: what is shared, who owns it, when it is valid, and how it is revised are often unclear.
- **Isolation and authority gap**
  - Shared-state agents still lack principled user isolation, artifact scoping, and authority boundaries; text sanitization alone is insufficient when executable artifacts persist.
- **Control/corrigibility gap**
  - Interruptibility, anti-sycophancy, and critic-style oversight often act as runtime patches rather than addressing objective misspecification or uncertainty-aware action selection.
- **Mechanism gap in multi-agent safety**
  - Work on collusion/coordination still emphasizes detection after the fact more than incentive design, enforceable constraints, or protocol-level prevention.
- **Long-horizon competence gap**
  - Strong models still fail on persistent planning because of weak scratchpad use, adversarial-state handling, compounding mistakes, and over-parallelization.
- **Artifact quality gap for agent tooling**
  - Task success can hide poor tool-library health: redundancy, regressions, brittle composition, and unsafe code evolution.
- **Skill-transfer gap**
  - Retrieval-based skills add token overhead and noise; internalization is promising but evidence remains task-bounded.
- **NV-specificity gap**
  - For NV-FPGA, the key filter remains whether persistence materially changes security, provisioning, or deployment advantage over SRAM FPGA baselines.
- **Lifecycle evaluation gap in NV-FPGA security**
  - Security claims still need stronger evidence on aging, temperature, repeatability, attack resistance, field update behavior, and operational lifecycle handling.
- **Threat-model gap in NV-FPGA identity work**
  - Large configuration spaces and secret structures are often presented as security evidence, but practical resistance to readback, extraction, side channels, emulation, and provisioning compromise is rarely established clearly.
- **Security-vs-search-space gap in mutation-based identity schemes**
  - Huge claimed cipher/configuration families do not by themselves establish clone resistance; the real question is whether attackers can recover, emulate, or learn the instantiated structure under realistic access.
- **Protocol gap in configuration-derived identity**
  - Enrollment, authentication, challenge exposure limits, verifier trust assumptions, and revocation/update handling are often underspecified even when the primitive itself is novel.

## New Insights
- The strongest active intake remains **LLM-agent issue scouting**, especially papers exposing realistic reliability failures rather than pure capability gains.
- A major emerging systems problem is **shared-state contamination**: benign multi-user reuse of memory/artifacts can silently degrade later outcomes, especially when executable artifacts are shared.
- **Interruptibility and changing user intent** now look like first-class deployment requirements, not edge cases.
- Long-horizon benchmarks are most valuable when they expose concrete failure mechanisms, especially **memory persistence strategy, adversarial detection, and compounding execution errors**.
- Runtime oversight appears to be bifurcating into two promising styles: **critic/supervisor architectures** for action monitoring and **behavioral gating** for targeted control failures like sycophancy.
- Multi-agent work is splitting into two important tracks: **productive autonomy** and **safety oversight**.
- Tool-generation research is improving when it treats the tool library as a **software artifact** rather than evaluating only downstream task completion.
- In NV-FPGA, the clearest hardware direction remains **persistent, configuration-derived identity and clone resistance**, including digital self-mutation ideas that use non-volatile configuration itself as the trust substrate.
- The NV-FPGA security subtrack is now more sharply defined: the interesting question is not just uniqueness, but whether **persistent secret structure in configuration** can serve as a credible trust anchor under realistic extraction and lifecycle assumptions.
- The SUC-style NV-FPGA paper strengthens a specific subdirection: **controlled, design-rule-safe bitstream mutation** may be a practical way to generate per-device digital identities in NV-FPGAs, potentially offering a more stable alternative to analog PUFs.
- The key caveat is now clearer: **configuration secrecy is not automatically physical unclonability**; decisive filters are readback assumptions, invasive/side-channel resistance, query leakage, provisioning trust, and protocol design.
- A useful framing shift is emerging for NV-FPGA work: move from **manufacturing randomness as identity** toward **controlled configuration diversity as identity**, but require attack-grounded validation before treating it as true clone resistance.

## Most Promising Directions
- **Prioritize agent papers aligned with realistic deployment failures**
  - Especially shared-state contamination, interruptibility, long-horizon consistency, controllability, and runtime oversight.
- **Favor principled state/memory architectures**
  - Prefer work that defines scoping, ownership, revision, isolation, and artifact validity semantics over prompt-level mitigations.
- **Track benchmarks that expose actionable failure taxonomies**
  - Best targets: long-horizon execution, changing goals, persistent state, multi-user settings, tool maintenance, and industrial orchestration.
- **Follow runtime supervision architectures**
  - Critic-based monitoring and asymmetric oversight look promising when they improve reliability without retraining the main actor.
- **Watch skill internalization closely**
  - Internalizing skills may reduce retrieval noise and context cost if it generalizes beyond narrow benchmarks.
- **Track multi-agent oversight beyond text-level monitoring**
  - Interpretability-based collusion detection is promising, but should be paired with mechanism design and constraints.
- **Keep tool-library quality as a first-class evaluation target**
  - Reuse, regressions, composition, robustness, and safety matter for agent systems that generate or evolve code.
- **Keep NV-FPGA security as the main hardware subtrack**
  - Focus on clone resistance, persistent identity, bitstream/configuration-derived trust, and lifecycle-aware security evaluation.
- **Prioritize configuration-native NV-FPGA security mechanisms**
  - Especially approaches where non-volatility enables first-boot identity generation, persistent secret structure, attestation roots, anti-counterfeit binding, or recovery/provisioning advantages.
- **Track digital mutation / SUC-style identity mechanisms**
  - Most interesting when legal bitstream mutation, on-device entropy, and persistent configuration combine into per-device trust anchors that are stable enough for deployment.
- **Apply a strict NV-advantage filter**
  - Prefer work where non-volatility clearly improves identity retention, tamper resistance, provisioning, recovery, or deployability.
- **Demand stronger attack-grounded validation in NV-FPGA identity papers**
  - Most promising work will pair configuration-derived identity claims with explicit enrollment/authentication protocols and evidence against readback, black-box learning, side-channel, invasive extraction, and provisioning compromise.
- **Prefer protocol-complete NV-FPGA identity work**
  - The strongest future papers will connect the primitive to verifier enrollment, challenge budgeting, field update behavior, and recovery/revocation paths.

## Current Stance
- **Primary active direction:** LLM-agent robustness under realistic deployment constraints, especially memory/state isolation, interruptibility, long-horizon execution, runtime oversight, and multi-agent safety.
- **Most salient subproblems:** cross-user contamination in shared memory, adaptation to changed user intent, persistent planning failures, and tool/library quality under autonomous code generation.
- **Primary hardware direction:** NV-FPGA security centered on persistent clone-resistant identity and configuration/mutation-based trust primitives.
- **Near-term NV-FPGA emphasis:** configuration-level identity mechanisms are promising, especially digital self-mutation/SUC-style approaches, but should be treated as architectural leads until backed by clear threat models, protocol details, and lifecycle/attack evidence.
- **Overall filter:** prioritize papers that surface real operational failure modes or provide mechanisms and evaluations likely to transfer beyond narrow benchmarks.
