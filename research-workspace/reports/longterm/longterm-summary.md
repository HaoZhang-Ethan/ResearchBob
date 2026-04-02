# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-02.md`

## Newly Selected Papers
- DVM: Real-Time Kernel Generation for Dynamic AI Models
- AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization
- Orion: Characterizing and Programming Apple's Neural Engine for LLM Training and Inference
- EAGLE-Pangu: Accelerator-Safe Tree Speculative Decoding on Ascend NPUs
- ANVIL: Accelerator-Native Video Interpolation via Codec Motion Vector Priors
- TENSURE: Fuzzing Sparse Tensor Compilers (Registered Report)
- LLM Inference at the Edge: Mobile, NPU, and GPU Performance Efficiency Trade-offs Under Sustained Load
- TinyML Enhances CubeSat Mission Capabilities
- From ex(p) to poly: Gaussian Splatting with Polynomial Kernels
- Accelerating OpenPangu Inference on NPU via Speculative Decoding

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- Dynamism is common in AI computation, e.g., the dynamic tensor shapes and the dynamic control flows in models. Due to the long compilation time, existing runtime compilation damages the model efficiency, while the offline compilers either suffer from the long compilation time and device memory footprint to cover all the possible execution instances of a dynamic model, or sacrifice optimization opportunities for usability. In this paper, we rethink the feasibility of runtime compilation for dynamic models and identify that the key for it to work is to speed up the compilation or hide the compilation overhead. To do this, we propose a real-time compiler, DVM. In DVM, we design a runtime operator compiler based on a bytecode virtual machine to perform effective and efficient compilation for each dynamic operator instance given its input. Specifically, instead of compiling programs into machine code, we encode the operator program into bytecode on the CPU and decode the bytecode into virtual instructions for direct execution on the NPU. Based on the runtime operator compiler, we further propose an operator fuser, which performs symbol-deduction-based fusion on static graphs and runtime fusion on dynamic graphs. Both pattern- and stacking-based fusion are supported to increase fusion opportunities. Evaluation on operators, subgraphs, and models shows that, compared with TorchInductor, PyTorch-eager and MindSpore-graph-O0, we are up to 11.77$\times$ better in terms of the operator/model efficiency and up to 5 orders of magnitude faster in terms of the maximum compilation time.
- AscendC (Ascend C) operator optimization on Huawei Ascend neural processing units (NPUs) faces a two-fold knowledge bottleneck: unlike the CUDA ecosystem, there are few public reference implementations to learn from, and performance hinges on a coupled two-part artifact - a host-side tiling program that orchestrates data movement and a kernel program that schedules and pipelines instructions. We present AscendOptimizer, an episodic agent that bootstraps this missing expertise by turning execution into experience. On the host side, AscendOptimizer performs profiling-in-the-loop evolutionary search to discover valid and high-performing tiling and data-movement configurations directly from hardware feedback. On the kernel side, it mines transferable optimization motifs by rewinding optimized kernels - systematically de-optimizing them to synthesize instructive "bad-to-good" trajectories - and distills these motifs into a retrievable experience bank for guided rewriting. By alternating host tuning and kernel rewriting in a closed loop, AscendOptimizer steadily expands feasibility and pushes latency down. On a benchmark of 127 real AscendC operators, AscendOptimizer achieves a 1.19x geometric-mean speedup over the open-source baseline, with 49.61% of operators outperforming their references, outperforming strong agent and search baselines.
- Over two billion Apple devices ship with a Neural Processing Unit (NPU) - the Apple Neural Engine (ANE) - yet this accelerator remains largely unused for large language model workloads. CoreML, Apple's public ML framework, imposes opaque abstractions that prevent direct ANE programming and do not support on-device training. We present Orion, to our knowledge the first open end-to-end system that combines direct ANE execution, a compiler pipeline, and stable multi-step training with checkpoint resume in a single native runtime, bypassing CoreML entirely via Apple's private _ANEClient and _ANECompiler APIs. Building on prior characterization work by maderix, we extend public knowledge of ANE constraints to a catalog of 20 restrictions on MIL IR programs, memory layout, compilation limits, and numerical behavior, including 14 previously undocumented constraints discovered during Orion development. Orion includes a compiler that lowers a graph IR through five optimization passes to ANE-native MIL and a runtime that manages IOSurface-backed zero-copy tensor I/O, program caching, and delta compilation for weight updates. Because the ANE bakes weights at compile time, naive training normally requires full recompilation per step (~4.2 s). We show that compiled programs can instead be updated by unloading, patching weight files, and reloading, bypassing ANECCompile() and reducing recompilation from 4,200 ms to 494 ms per step (8.5x), yielding a 3.8x training speedup. On an M4 Max, Orion achieves 170+ tokens/s for GPT-2 124M inference and demonstrates stable training of a 110M-parameter transformer on TinyStories for 1,000 steps in 22 minutes with zero NaN occurrences. We also present LoRA adapter-as-input, enabling hot-swap of adapters via IOSurface inputs without recompilation.
- Autoregressive decoding remains a primary bottleneck in large language model (LLM) serving, motivating speculative decoding methods that reduce expensive teacher-model invocations by verifying multiple candidate tokens per step. Tree-structured speculation further increases parallelism, but is often brittle when ported across heterogeneous backends and accelerator stacks, where attention masking, KV-cache layouts, and indexing semantics are not interchangeable. We present EAGLE-Pangu, a reproducible system that ports EAGLE-3-style tree speculative decoding to a Pangu teacher backend on Ascend NPUs. EAGLE-Pangu contributes (i) an explicit branch/commit cache manager built on the Cache API, (ii) accelerator-safe tree tensorization that removes undefined negative indices by construction and validates structural invariants, and (iii) a fused-kernel-compatible teacher verification path with a debuggable eager fallback. On 240 turns from MT-Bench and HumanEval-style prompts, EAGLE-Pangu improves end-to-end decoding throughput by 1.27x on average, up to 2.46x at p99, over teacher-only greedy decoding in the fused-kernel performance path. We also provide a fused-kernel-free reference path with structured traces and invariant checks to support reproducible debugging and ablation across execution modes and tree budgets.
- Real-time 30-to-60 fps video frame interpolation on mobile neural processing units (NPUs) requires each synthesized frame within 33.3 ms. We show that mainstream flow-based video frame interpolation faces three structural deployment barriers on mobile NPUs: spatial sampling operators exceed the frame budget or lack hardware support, iterative flow refinement collapses under 8-bit integer post-training quantization, and memory-bound operators dominate the inference graph. ANVIL addresses these barriers by reusing motion vectors from the H.264/AVC decoder to prealign input frames, removing learned optical flow, spatial sampling, and iterative accumulation from the accelerator graph. The remaining residual is refined by a convolution-dominated network composed almost entirely of compute-bound operators. On a Snapdragon 8 Gen 3 device, ANVIL achieves 12.8 ms 1080p inference at 8-bit integer precision; an open-source Android player sustains 28.4 ms median end-to-end latency over 30-minute continuous playback. Per-operator causal analysis identifies quantized accumulation on recurrent flow states as a key mechanism behind integer quantization failure in iterative methods. The current design targets H.264/AVC playback with decoder-exposed motion vectors.
- Sparse Tensor Compilers (STCs) have emerged as critical infrastructure for optimizing high-dimensional data analytics and machine learning workloads. The STCs must synthesize complex, irregular control flow for various compressed storage formats directly from high-level declarative specifications, thereby making them highly susceptible to subtle correctness defects. Existing testing frameworks, which rely on mutating computation graphs restricted to a standard vocabulary of operators, fail to exercise the arbitrary loop synthesis capabilities of these compilers. Furthermore, generic grammar-based fuzzers struggle to generate valid inputs due to the strict rules governing how indices are reused across multiple tensors. In this paper, we present TENSURE, the first extensible black-box fuzzing framework specifically designed for the testing of STCs. TENSURE leverages Einstein Summation (Einsum) notation as a general input abstraction, enabling the generation of complex, unconventional tensor contractions that expose corner cases in the code-generation phases of STCs. We propose a novel constraint-based generation algorithm that guarantees 100% semantic validity of synthesized kernels, significantly outperforming the ~3.3% validity rate of baseline grammar fuzzers. To enable metamorphic testing without a trusted reference, we introduce a set of semantic-preserving mutation operators that exploit algebraic commutativity and heterogeneity in storage formats. Our evaluation on two state-of-the-art systems, TACO and Finch, reveals widespread fragility, particularly in TACO, where TENSURE exposed crashes or silent miscompilations in a majority of generated test cases. These findings underscore the critical need for specialized testing tools in the sparse compilation ecosystem.
- Deploying large language models on-device for always-on personal agents demands sustained inference from hardware tightly constrained in power, thermal envelope, and memory. We benchmark Qwen 2.5 1.5B (4-bit quantised) across four platforms: a Raspberry Pi 5 with Hailo-10H NPU, a Samsung Galaxy S24 Ultra, an iPhone 16 Pro, and a laptop NVIDIA RTX 4050 GPU. Using a fixed 258-token prompt over 20 warm-condition iterations per device, we measure throughput, latency, power, and thermal behaviour. For mobile platforms, thermal management supersedes peak compute as the primary constraint: the iPhone 16 Pro loses nearly half its throughput within two iterations, and the S24 Ultra suffers a hard OS-enforced GPU frequency floor that terminates inference entirely. On dedicated hardware, distinct constraints dominate: the RTX 4050 is bounded by its battery power ceiling, while the Hailo-10H is limited by on-module memory bandwidth. The RTX 4050 sustains 131.7 tok/s at 34.1 W; the Hailo-10H sustains 6.9 tok/s at under 2 W with near-zero variance, matching the RTX 4050 in energy proportionality at 19x lower throughput. Results should be interpreted as platform-level deployment characterisations for a single model and prompt type, reflecting hardware and software combined, rather than general claims about hardware capability alone.
- Earth observation (EO) missions traditionally rely on transmitting raw or minimally processed imagery from satellites to ground stations for computationally intensive analysis. This paradigm is infeasible for CubeSat systems due to stringent constraints on the onboard embedded processors, energy availability, and communication bandwidth. To overcome these limitations, the paper presents a TinyML-based Convolutional Neural Networks (ConvNets) model optimization and deployment pipeline for onboard image classification, enabling accurate, energy-efficient, and hardware-aware inference under CubeSat-class constraints. Our pipeline integrates structured iterative pruning, post-training INT8 quantization, and hardware-aware operator mapping to compress models and align them with the heterogeneous compute architecture of the STM32N6 microcontroller from STMicroelectronics. This Microcontroller Unit (MCU) integrates a novel Arm Cortex-M55 core and a Neural-ART Neural Processing Unit (NPU), providing a realistic proxy for CubeSat onboard computers. The paper evaluates the proposed approach on three EO benchmark datasets (i.e., EuroSAT, RS_C11, MEDIC) and four models (i.e., SqueezeNet, MobileNetV3, EfficientNet, MCUNetV1). We demonstrate an average reduction in RAM usage of 89.55% and Flash memory of 70.09% for the optimized models, significantly decreasing downlink bandwidth requirements while maintaining task-acceptable accuracy (with a drop ranging from 0.4 to 8.6 percentage points compared to the Float32 baseline). The energy consumption per inference ranges from 0.68 mJ to 6.45 mJ, with latency spanning from 3.22 ms to 30.38 ms. These results fully satisfy the stringent energy budgets and real-time constraints required for efficient onboard EO processing.
- Recent advancements in Gaussian Splatting (3DGS) have introduced various modifications to the original kernel, resulting in significant performance improvements. However, many of these kernel changes are incompatible with existing datasets optimized for the original Gaussian kernel, presenting a challenge for widespread adoption. In this work, we address this challenge by proposing an alternative kernel that maintains compatibility with existing datasets while improving computational efficiency. Specifically, we replace the original exponential kernel with a polynomial approximation combined with a ReLU function. This modification allows for more aggressive culling of Gaussians, leading to enhanced performance across different 3DGS implementations. Our results show a notable performance improvement of 4 to 15% with negligible impact on image quality. We also provide a detailed mathematical analysis of the new kernel and discuss its potential benefits for 3DGS implementations on NPU hardware.
- To mitigate the Memory Wall bottleneck encountered by Large Language Models (LLMs) during inference on \textbf{NPU} hardware, and addressing the scarcity of native support for mainstream speculative decoding algorithms on domestic infrastructure, this study presents an end-to-end speculative inference acceleration scheme for OpenPangu-7B.

## Current Rolling Summary
## Problem clusters

### 1) Runtime/dynamic compilation on NPUs
- **Key papers:** DVM, Orion
- **Recurring problem:** Static graph compilation breaks under dynamic shapes/control flow or under targets with expensive compile/update paths. The true objective is often **execution + compile/update latency**, not execution alone.
- **What current solutions do:**
  - DVM reduces runtime compilation cost via **bytecode/VM execution** and expands dynamic fusion opportunities.
  - Orion makes ANE usable by exposing real constraints and reducing **recompile cost via weight patching/reload**.
- **Common gap:** Better enablement than decision-making. Missing explicit models for **when fusion/partitioning should change because compile latency, reload cost, legality risk, or VM decode overhead dominate**.

### 2) Low-level NPU operator optimization: tiling, scheduling, pipelining
- **Key papers:** AscendOptimizer, TinyML CubeSat pipeline
- **Recurring problem:** Real NPU performance is jointly determined by **host tiling/data movement + kernel instruction scheduling/pipelining + fallback boundaries**.
- **What current solutions do:**
  - AscendOptimizer uses hardware-in-the-loop search and retrieval of optimization motifs.
  - TinyML deployment does pruning/quantization/operator mapping on MCU+NPU targets.
- **Common gap:** Strong practical optimization, weak **interpretable microarchitectural reasoning**. Little clarity on **stop policies**, failure cases, or break-even points for CPU vs NPU, more pipelining vs less, larger tiles vs smaller.

### 3) Speculative decoding / irregular stateful inference on NPUs
- **Key papers:** EAGLE-Pangu, OpenPangu speculative decoding, edge sustained-load study
- **Recurring problem:** Speculative decoding and long-context inference are dominated by **KV-cache traffic, verification overhead, backend legality, and runtime state management**, not just arithmetic.
- **What current solutions do:**
  - EAGLE-Pangu makes tree speculation **backend-safe** on Ascend.
  - OpenPangu brings speculative decoding to domestic NPU infrastructure.
  - Sustained-load study shows deployment-optimal behavior differs from cold-run peak behavior.
- **Common gap:** Policies are mostly fixed or empirical. Missing **predictive models for when to speculate, how much to speculate, when to disable it, and how to organize verify/commit/cache stages for the NPU pipeline**.

### 4) Hardware-shaped graph redesign rather than better lowering of a fixed graph
- **Key papers:** ANVIL, Orion, DVM, polynomial-kernel Gaussian splatting
- **Recurring problem:** Some graphs are simply poor matches to NPUs. The real win may come from **changing the operator set / graph structure** rather than lowering the original graph better.
- **What current solutions do:**
  - ANVIL removes NPU-hostile flow/warping ops using codec motion-vector priors.
  - Orion changes deployment economics through patchable compiled artifacts.
  - DVM changes the codegen/execution interface via VM bytecode.
- **Common gap:** Good intuition, weak formalization. Missing compiler frameworks that decide **when to externalize, approximate, rewrite, or preserve operator subgraphs based on hardware capabilities and non-execution costs**.

### 5) Correctness/robustness infrastructure for nonstandard tensor compilation
- **Key papers:** TENSURE
- **Recurring problem:** Irregular tensor lowering remains fragile; testing tools lag the complexity of sparse/tensor compilers.
- **What current solutions do:** Constraint-based valid generation + metamorphic testing.
- **Common gap:** Useful for trustworthiness, but not yet tied to **optimization decision quality**, hardware behavior, or no-transform conditions.

## Recurring weaknesses in existing solutions

### A. Opportunity expansion without profitability explanation
Many papers find more places to optimize/fuse/speculate, but do not explain **when the optimization should stop**.
- Recurrent missing piece: **anti-fusion / anti-speculation / anti-mapping policy**.
- Strongest repeated gap across DVM, AscendOptimizer, speculative decoding papers, TinyML deployment.

### B. Hardware-aware in motivation, not in decision model
A lot of work is clearly shaped by real NPU constraints, but decision logic remains:
- rule-based,
- search-heavy,
- retrieval-based, or
- post hoc empirical.

Missing: **predictive, interpretable cost models** tied to concrete resources like SRAM pressure, DMA startup, pipeline overlap, decode overhead, issue limits, cache traffic, fallback cost, and compile/reload latency.

### C. Weak treatment of non-execution costs
A major cross-paper lesson: optimal compiler decisions often depend on costs beyond kernel runtime:
- compile latency,
- recompilation/update latency,
- cache/state management overhead,
- legality/fragility risk,
- sustained thermal/power behavior.

Most current systems acknowledge these costs but do not **optimize them jointly** with execution.

### D. Pipeline-aware reasoning is implicit, rarely explicit
Many papers involve staged behavior—host tiling vs kernel scheduling, branch/commit caches, verify/commit loops, decode/reload/update paths—but rarely formalize:
- overlap opportunities,
- queueing/resource contention,
- when fusion reduces overlap,
- when splitting enables better steady-state throughput.

### E. Insufficient failure taxonomy
Especially valuable future work would explain why methods fail by cluster:
- memory-bound vs compute-bound,
- decode-overhead-bound,
- legality-bound,
- local-memory-limited,
- sustained-power-limited,
- acceptance-rate-limited,
- fallback/partition-overhead-limited.

## Most promising directions

### 1) Explicit “when not to fuse / speculate / map” models
This is the clearest recurring opportunity.
- Build models that predict when optimization harms:
  - on-chip memory pressure,
  - pipeline overlap,
  - cache traffic,
  - thermal stability,
  - recompilation/update cost,
  - fallback frequency.
- High-value because most current papers optimize only in the positive direction.

### 2) Joint cost models that include execution + compile/update/runtime-state costs
Most promising unifying direction across DVM, Orion, speculative decoding, and edge deployment.
- Objective should combine:
  - execution latency,
  - compile latency,
  - update/reload latency,
  - memory traffic,
  - sustained power/thermal state,
  - legality risk / fallback cost.
- This seems especially fertile for NPUs where static compilation assumptions often distort the real optimum.

### 3) Pipeline-aware fusion and partitioning on real NPUs
Strong fit to current interests.
- Treat fusion as a **pipeline-capacity allocation** problem, not just launch reduction or memory-locality maximization.
- Key questions:
  - when does a larger fused region block overlap of copy/compute/store?
  - when does defusion improve queueing or hide DMA?
  - when does VM execution or speculative verification limit instruction/schedule freedom?

### 4) Runtime-adaptive / hot-instance specialization
Especially promising for DVM-like settings and speculative decoding.
- Cold path: low-latency generic/VM execution.
- Hot path: promote recurrent shapes/graphs to more aggressively optimized kernels.
- Add online adaptation using hardware counters or recent acceptance/shape history.

### 5) Resource-pattern-based optimization rather than syntax-pattern-based optimization
Suggested by AscendOptimizer’s limits.
- Retrieve/prioritize cases by **buffer footprint, overlap structure, bandwidth pressure, occupancy class**, not only operator syntax.
- Better chance of generalizing across operators and architectures.

### 6) Graph rewriting around hardware capability models
Promising lesson from ANVIL and Orion.
- Compiler should sometimes decide to:
  - remove hostile operators,
  - externalize computation to side channels/priors,
  - rewrite to approximations better matched to the accelerator,
  - preserve boundaries for update/reload flexibility.
- This is broader than classic fusion and may be a better fit for NPU-native optimization.

### 7) Counter-validated compiler decisions
Across many papers, a strong evaluation gap remains.
- Best future work will show chosen fusion/partition/schedule decisions match:
  - measured hardware counters,
  - observed bottlenecks,
  - sustained-state behavior,
  - failure regimes.
- This aligns well with the preference for interpretable, actionable cost models.

## Current strongest seeds

### Read-now level seeds
- **DVM:** runtime/dynamic NPU compilation is a strong substrate for research on **fusion under compile-latency constraints** and **VM-vs-native promotion policies**.
- **AscendOptimizer:** strongest seed for **joint tiling + scheduling + pipeline-aware operator optimization** on a real NPU; especially valuable because its incomplete success rate exposes room for a better explanatory model.
- **Orion:** best substrate for **recompilation-aware partitioning/fusion** and optimization under target-specific legality constraints.

### High-upside follow-up seeds
- **Speculative decoding on NPUs (EAGLE-Pangu / OpenPangu):** promising if reformulated as **graph partitioning + cache-layout + pipeline scheduling**, not just decoding policy.
- **ANVIL:** useful as evidence that compiler work may need to **rewrite graphs around hardware capability mismatches**, not just optimize within a fixed graph.
- **Edge sustained-load study:** strong motivation for **thermal-/power-/bandwidth-aware compiler policies** where peak-optimal and sustained-optimal schedules differ.

## Working research hypothesis
The most promising long-term direction is a **hardware-grounded, interpretable optimizer for NPUs that jointly chooses fusion boundaries, tiling/scheduling, and runtime partitioning under execution, memory, compile/update, and pipeline-overlap constraints—while explicitly modeling when not to optimize further**.
