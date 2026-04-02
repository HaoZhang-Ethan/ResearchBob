# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-02.md`

## Newly Selected Papers
- Orion: Characterizing and Programming Apple's Neural Engine for LLM Training and Inference
- DVM: Real-Time Kernel Generation for Dynamic AI Models
- AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization
- EAGLE-Pangu: Accelerator-Safe Tree Speculative Decoding on Ascend NPUs
- ANVIL: Accelerator-Native Video Interpolation via Codec Motion Vector Priors
- TENSURE: Fuzzing Sparse Tensor Compilers (Registered Report)
- Accelerating OpenPangu Inference on NPU via Speculative Decoding
- LLM Inference at the Edge: Mobile, NPU, and GPU Performance Efficiency Trade-offs Under Sustained Load
- TinyML Enhances CubeSat Mission Capabilities
- From ex(p) to poly: Gaussian Splatting with Polynomial Kernels

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- Over two billion Apple devices ship with a Neural Processing Unit (NPU) - the Apple Neural Engine (ANE) - yet this accelerator remains largely unused for large language model workloads. CoreML, Apple's public ML framework, imposes opaque abstractions that prevent direct ANE programming and do not support on-device training. We present Orion, to our knowledge the first open end-to-end system that combines direct ANE execution, a compiler pipeline, and stable multi-step training with checkpoint resume in a single native runtime, bypassing CoreML entirely via Apple's private _ANEClient and _ANECompiler APIs. Building on prior characterization work by maderix, we extend public knowledge of ANE constraints to a catalog of 20 restrictions on MIL IR programs, memory layout, compilation limits, and numerical behavior, including 14 previously undocumented constraints discovered during Orion development. Orion includes a compiler that lowers a graph IR through five optimization passes to ANE-native MIL and a runtime that manages IOSurface-backed zero-copy tensor I/O, program caching, and delta compilation for weight updates. Because the ANE bakes weights at compile time, naive training normally requires full recompilation per step (~4.2 s). We show that compiled programs can instead be updated by unloading, patching weight files, and reloading, bypassing ANECCompile() and reducing recompilation from 4,200 ms to 494 ms per step (8.5x), yielding a 3.8x training speedup. On an M4 Max, Orion achieves 170+ tokens/s for GPT-2 124M inference and demonstrates stable training of a 110M-parameter transformer on TinyStories for 1,000 steps in 22 minutes with zero NaN occurrences. We also present LoRA adapter-as-input, enabling hot-swap of adapters via IOSurface inputs without recompilation.
- Dynamism is common in AI computation, e.g., the dynamic tensor shapes and the dynamic control flows in models. Due to the long compilation time, existing runtime compilation damages the model efficiency, while the offline compilers either suffer from the long compilation time and device memory footprint to cover all the possible execution instances of a dynamic model, or sacrifice optimization opportunities for usability. In this paper, we rethink the feasibility of runtime compilation for dynamic models and identify that the key for it to work is to speed up the compilation or hide the compilation overhead. To do this, we propose a real-time compiler, DVM. In DVM, we design a runtime operator compiler based on a bytecode virtual machine to perform effective and efficient compilation for each dynamic operator instance given its input. Specifically, instead of compiling programs into machine code, we encode the operator program into bytecode on the CPU and decode the bytecode into virtual instructions for direct execution on the NPU. Based on the runtime operator compiler, we further propose an operator fuser, which performs symbol-deduction-based fusion on static graphs and runtime fusion on dynamic graphs. Both pattern- and stacking-based fusion are supported to increase fusion opportunities. Evaluation on operators, subgraphs, and models shows that, compared with TorchInductor, PyTorch-eager and MindSpore-graph-O0, we are up to 11.77$\times$ better in terms of the operator/model efficiency and up to 5 orders of magnitude faster in terms of the maximum compilation time.
- AscendC (Ascend C) operator optimization on Huawei Ascend neural processing units (NPUs) faces a two-fold knowledge bottleneck: unlike the CUDA ecosystem, there are few public reference implementations to learn from, and performance hinges on a coupled two-part artifact - a host-side tiling program that orchestrates data movement and a kernel program that schedules and pipelines instructions. We present AscendOptimizer, an episodic agent that bootstraps this missing expertise by turning execution into experience. On the host side, AscendOptimizer performs profiling-in-the-loop evolutionary search to discover valid and high-performing tiling and data-movement configurations directly from hardware feedback. On the kernel side, it mines transferable optimization motifs by rewinding optimized kernels - systematically de-optimizing them to synthesize instructive "bad-to-good" trajectories - and distills these motifs into a retrievable experience bank for guided rewriting. By alternating host tuning and kernel rewriting in a closed loop, AscendOptimizer steadily expands feasibility and pushes latency down. On a benchmark of 127 real AscendC operators, AscendOptimizer achieves a 1.19x geometric-mean speedup over the open-source baseline, with 49.61% of operators outperforming their references, outperforming strong agent and search baselines.
- Autoregressive decoding remains a primary bottleneck in large language model (LLM) serving, motivating speculative decoding methods that reduce expensive teacher-model invocations by verifying multiple candidate tokens per step. Tree-structured speculation further increases parallelism, but is often brittle when ported across heterogeneous backends and accelerator stacks, where attention masking, KV-cache layouts, and indexing semantics are not interchangeable. We present EAGLE-Pangu, a reproducible system that ports EAGLE-3-style tree speculative decoding to a Pangu teacher backend on Ascend NPUs. EAGLE-Pangu contributes (i) an explicit branch/commit cache manager built on the Cache API, (ii) accelerator-safe tree tensorization that removes undefined negative indices by construction and validates structural invariants, and (iii) a fused-kernel-compatible teacher verification path with a debuggable eager fallback. On 240 turns from MT-Bench and HumanEval-style prompts, EAGLE-Pangu improves end-to-end decoding throughput by 1.27x on average, up to 2.46x at p99, over teacher-only greedy decoding in the fused-kernel performance path. We also provide a fused-kernel-free reference path with structured traces and invariant checks to support reproducible debugging and ablation across execution modes and tree budgets.
- Real-time 30-to-60 fps video frame interpolation on mobile neural processing units (NPUs) requires each synthesized frame within 33.3 ms. We show that mainstream flow-based video frame interpolation faces three structural deployment barriers on mobile NPUs: spatial sampling operators exceed the frame budget or lack hardware support, iterative flow refinement collapses under 8-bit integer post-training quantization, and memory-bound operators dominate the inference graph. ANVIL addresses these barriers by reusing motion vectors from the H.264/AVC decoder to prealign input frames, removing learned optical flow, spatial sampling, and iterative accumulation from the accelerator graph. The remaining residual is refined by a convolution-dominated network composed almost entirely of compute-bound operators. On a Snapdragon 8 Gen 3 device, ANVIL achieves 12.8 ms 1080p inference at 8-bit integer precision; an open-source Android player sustains 28.4 ms median end-to-end latency over 30-minute continuous playback. Per-operator causal analysis identifies quantized accumulation on recurrent flow states as a key mechanism behind integer quantization failure in iterative methods. The current design targets H.264/AVC playback with decoder-exposed motion vectors.
- Sparse Tensor Compilers (STCs) have emerged as critical infrastructure for optimizing high-dimensional data analytics and machine learning workloads. The STCs must synthesize complex, irregular control flow for various compressed storage formats directly from high-level declarative specifications, thereby making them highly susceptible to subtle correctness defects. Existing testing frameworks, which rely on mutating computation graphs restricted to a standard vocabulary of operators, fail to exercise the arbitrary loop synthesis capabilities of these compilers. Furthermore, generic grammar-based fuzzers struggle to generate valid inputs due to the strict rules governing how indices are reused across multiple tensors. In this paper, we present TENSURE, the first extensible black-box fuzzing framework specifically designed for the testing of STCs. TENSURE leverages Einstein Summation (Einsum) notation as a general input abstraction, enabling the generation of complex, unconventional tensor contractions that expose corner cases in the code-generation phases of STCs. We propose a novel constraint-based generation algorithm that guarantees 100% semantic validity of synthesized kernels, significantly outperforming the ~3.3% validity rate of baseline grammar fuzzers. To enable metamorphic testing without a trusted reference, we introduce a set of semantic-preserving mutation operators that exploit algebraic commutativity and heterogeneity in storage formats. Our evaluation on two state-of-the-art systems, TACO and Finch, reveals widespread fragility, particularly in TACO, where TENSURE exposed crashes or silent miscompilations in a majority of generated test cases. These findings underscore the critical need for specialized testing tools in the sparse compilation ecosystem.
- To mitigate the Memory Wall bottleneck encountered by Large Language Models (LLMs) during inference on \textbf{NPU} hardware, and addressing the scarcity of native support for mainstream speculative decoding algorithms on domestic infrastructure, this study presents an end-to-end speculative inference acceleration scheme for OpenPangu-7B.
- Deploying large language models on-device for always-on personal agents demands sustained inference from hardware tightly constrained in power, thermal envelope, and memory. We benchmark Qwen 2.5 1.5B (4-bit quantised) across four platforms: a Raspberry Pi 5 with Hailo-10H NPU, a Samsung Galaxy S24 Ultra, an iPhone 16 Pro, and a laptop NVIDIA RTX 4050 GPU. Using a fixed 258-token prompt over 20 warm-condition iterations per device, we measure throughput, latency, power, and thermal behaviour. For mobile platforms, thermal management supersedes peak compute as the primary constraint: the iPhone 16 Pro loses nearly half its throughput within two iterations, and the S24 Ultra suffers a hard OS-enforced GPU frequency floor that terminates inference entirely. On dedicated hardware, distinct constraints dominate: the RTX 4050 is bounded by its battery power ceiling, while the Hailo-10H is limited by on-module memory bandwidth. The RTX 4050 sustains 131.7 tok/s at 34.1 W; the Hailo-10H sustains 6.9 tok/s at under 2 W with near-zero variance, matching the RTX 4050 in energy proportionality at 19x lower throughput. Results should be interpreted as platform-level deployment characterisations for a single model and prompt type, reflecting hardware and software combined, rather than general claims about hardware capability alone.
- Earth observation (EO) missions traditionally rely on transmitting raw or minimally processed imagery from satellites to ground stations for computationally intensive analysis. This paradigm is infeasible for CubeSat systems due to stringent constraints on the onboard embedded processors, energy availability, and communication bandwidth. To overcome these limitations, the paper presents a TinyML-based Convolutional Neural Networks (ConvNets) model optimization and deployment pipeline for onboard image classification, enabling accurate, energy-efficient, and hardware-aware inference under CubeSat-class constraints. Our pipeline integrates structured iterative pruning, post-training INT8 quantization, and hardware-aware operator mapping to compress models and align them with the heterogeneous compute architecture of the STM32N6 microcontroller from STMicroelectronics. This Microcontroller Unit (MCU) integrates a novel Arm Cortex-M55 core and a Neural-ART Neural Processing Unit (NPU), providing a realistic proxy for CubeSat onboard computers. The paper evaluates the proposed approach on three EO benchmark datasets (i.e., EuroSAT, RS_C11, MEDIC) and four models (i.e., SqueezeNet, MobileNetV3, EfficientNet, MCUNetV1). We demonstrate an average reduction in RAM usage of 89.55% and Flash memory of 70.09% for the optimized models, significantly decreasing downlink bandwidth requirements while maintaining task-acceptable accuracy (with a drop ranging from 0.4 to 8.6 percentage points compared to the Float32 baseline). The energy consumption per inference ranges from 0.68 mJ to 6.45 mJ, with latency spanning from 3.22 ms to 30.38 ms. These results fully satisfy the stringent energy budgets and real-time constraints required for efficient onboard EO processing.
- Recent advancements in Gaussian Splatting (3DGS) have introduced various modifications to the original kernel, resulting in significant performance improvements. However, many of these kernel changes are incompatible with existing datasets optimized for the original Gaussian kernel, presenting a challenge for widespread adoption. In this work, we address this challenge by proposing an alternative kernel that maintains compatibility with existing datasets while improving computational efficiency. Specifically, we replace the original exponential kernel with a polynomial approximation combined with a ReLU function. This modification allows for more aggressive culling of Gaussians, leading to enhanced performance across different 3DGS implementations. Our results show a notable performance improvement of 4 to 15% with negligible impact on image quality. We also provide a detailed mathematical analysis of the new kernel and discuss its potential benefits for 3DGS implementations on NPU hardware.

## Current Rolling Summary
## Problem clusters

### 1) Fusion/partitioning is missing real NPU objectives
- Repeated pattern: papers expose real accelerator constraints, but fusion/partitioning policy still optimizes a narrow proxy like kernel latency or compile availability.
- **Orion (Apple ANE)** is the clearest example: compile-time weight baking means optimal partitioning should include recompilation/reload/patchability cost, not just runtime speed.
- **DVM** shifts the objective again: when runtime compilation becomes cheap via VM bytecode, fusion decisions should be re-optimized around hardware behavior, not compile-latency fear.
- **Speculative decoding on NPUs** adds another hidden objective: verification/control/KV-cache overhead changes the best graph cuts and fused regions.
- Working hypothesis: on NPUs, the right fusion boundary often depends on nontraditional costs—recompile latency, legality risk, cache-update structure, dynamic-shape specialization overhead, and backend fallback probability.

### 2) Hardware-grounded legality is a major but underexploited signal
- Strong recent papers are valuable because they reveal **undocumented or backend-specific constraints**:
  - ANE MIL/legality restrictions, weight embedding, zero-copy/runtime artifact structure (**Orion**)
  - VM/runtime decode model and dynamic fusion mechanics (**DVM**)
  - Ascend host-tiling + kernel-pipeline coupling (**AscendOptimizer**)
  - Fused-kernel-safe indexing, KV-cache branch/commit semantics in speculative decoding (**EAGLE-Pangu**)
  - Operator families that are simply poor mobile-NPU fits, e.g. warping / iterative flow / memory-heavy vision ops (**ANVIL**)
- These papers often stop at “here are the constraints,” but the real opportunity is to convert them into **predictive compiler features** for partitioning, fusion stopping, scheduling, and legality-aware search.

### 3) Pipeline/overlap and host-device coordination remain under-modeled
- A recurring missing layer is reasoning about **DMA/compute overlap, host-managed control, cache updates, and pipeline bubbles**.
- **AscendOptimizer** is especially relevant because it explicitly couples host tiling/data movement with kernel-side pipelining.
- **Orion** suggests compile/reload/update should be treated as part of the execution pipeline for training and adapter serving.
- **Speculative decoding papers** imply the same for draft/verify/commit/cache stages, but do not yet turn this into a scheduling model.
- Likely high-value direction: treat graph partitioning + schedule shape as a **pipeline-capacity allocation problem**, not just an op-combine problem.

### 4) Dynamic workloads change the optimal compiler policy
- **DVM** makes this especially clear: if runtime specialization is cheap enough, static fusion heuristics are no longer obviously right.
- Dynamic shapes/control flow likely need **runtime fusion policies** with hardware-informed anti-fusion logic, hot-shape adaptation, and promotion paths (VM first, native later).
- This looks like a strong research cluster: dynamic models expose a richer decision surface where compile cost, decode overhead, memory planning, and scheduling freedom all interact.

### 5) In some cases the graph itself should change, not just the codegen
- **ANVIL** is the clearest example: instead of optimizing flow/warping better, remove them from the NPU graph using codec priors.
- **Orion** suggests parameter placement itself is part of graph design: baked weights vs patchable weights vs input-fed adapters.
- **Speculative decoding** papers suggest speculative state and KV-cache semantics should perhaps be first-class IR concepts rather than ad hoc runtime logic.
- Emerging theme: a capability-aware compiler may need to decide when to **externalize, approximate, defuse, or replace** hardware-hostile subgraphs.

### 6) Sustained-load and deployment-state effects are underexplored compiler objectives
- The edge LLM characterization paper reinforces that peak-optimal execution may be wrong under **thermal, power, and memory-bandwidth** limits.
- This suggests a longer-horizon problem: fusion/scheduling decisions should potentially optimize **sustained tokens/s over time**, not just cold-run throughput.
- Promising angle: selective defusion or thermally smoother stage boundaries may beat peak-optimal fused kernels on edge devices.

## Recurring gaps in existing solutions

### A. Missing “when not to fuse / when not to optimize” logic
- This is the most consistent gap across papers.
- Most systems explain how to enable more fusion/specialization, but not when larger fused regions hurt due to:
  - compile fragility or recompilation cost
  - local-memory/register pressure
  - pipeline disruption / reduced overlap
  - verification/control overhead
  - unsupported fused patterns or fallback risk
  - thermal/power bursts under sustained load
- This anti-fusion/anti-specialization policy is a strong fit to the current phase bias.

### B. Cost models are often empirical but not interpretable or actionable
- Many papers use hardware feedback or system measurement, but stop short of deriving a model a compiler could actually use.
- Preference reinforced: reward work that converts hardware behavior into **simple predictive features** such as legality risk, DMA pressure, patchability, cache-update cost, pipeline occupancy, decode overhead, or fallback probability.

### C. Microarchitectural grounding is present as motivation, absent as decision logic
- Good papers increasingly mention real NPU constraints, but often do not connect them all the way to compiler choices.
- Missing bridge: show that chosen fusion/scheduling/partitioning decisions actually match counters, traces, queueing behavior, or measured overlap limits.

### D. Single-op optimization is ahead of graph-level reasoning
- **AscendOptimizer** is useful because it reveals host/kernel coupling at operator level, but the bigger opportunity is to lift that logic to **cross-op boundary decisions**.
- Current gap: graph compilers often choose boundaries without enough knowledge of how those boundaries alter tiling feasibility and pipeline behavior downstream.

### E. Runtime state and mutability are not first-class enough in compiler models
- Weight updates, LoRA swapping, speculative branch state, KV-cache commit/rollback, dynamic-shape hot paths: these are increasingly first-order costs.
- Existing IR/cost models often treat them as runtime details rather than optimization objectives.

## Most promising directions

### 1) Recompilation-aware and mutability-aware fusion/partitioning
- Strongest direction seeded by **Orion**.
- Optimize graph cuts using a cost model that includes:
  - execution latency
  - compile/recompile latency
  - patch/reload cost
  - legality risk
  - parameter mutability (static vs patchable vs dynamic input)
  - cacheability of compiled artifacts
- Especially promising for on-device training, adapter serving, and targets with opaque compiler stacks.

### 2) Hardware-grounded anti-fusion models
- Build explicit predictors for **when fusion should stop**.
- Candidate features across papers:
  - on-chip memory footprint / spill risk
  - DMA startup + overlap potential
  - decode/dispatch overhead (for VM-like runtimes)
  - fallback probability for unsupported fused patterns
  - verification/control overhead in speculative execution
  - sustained power/thermal density
- This direction is central and repeatedly justified by the current paper set.

### 3) Joint boundary + schedule optimization via pipeline reasoning
- Go beyond “fuse then schedule.”
- Treat graph partitioning, tiling, data movement, and instruction scheduling as a joint problem constrained by pipeline overlap and queueing.
- **AscendOptimizer** is the most relevant substrate here; likely next step is extending host/kernel co-optimization to adjacent-op or fused-region decisions.

### 4) Dynamic-shape/runtime-aware fusion with tiered execution paths
- Strong direction from **DVM**.
- Likely promising architecture:
  - immediate low-latency VM/bytecode execution for cold dynamic instances
  - online profiling of hot recurring shapes
  - promotion of selected subgraphs to native or more aggressively scheduled kernels
  - runtime anti-fusion rules based on measured hardware bottlenecks
- Important because cheap runtime specialization changes the search space.

### 5) Compiler-driven handling of speculative stateful decoding
- Treat speculative decoding as a compiler problem, not just a serving trick.
- Optimize jointly over:
  - tree width/depth
  - verification graph shape
  - fusion boundaries in verify/commit/cache-update paths
  - KV-cache branch/commit scheduling
  - disable/speculate policy under low acceptance or high cache pressure
- The current papers suggest this area is real but under-modeled.

### 6) Capability-driven graph rewriting / operator externalization
- Generalize the **ANVIL** insight into a compiler framework:
  - identify hardware-hostile operator families
  - replace, externalize, approximate, or split them based on backend capability models
  - decide when side-channel priors or alternate formulations are better than optimizing the original graph
- This looks especially promising for mobile NPUs and other restricted accelerators.

### 7) Sustained-load-aware optimization for edge accelerators
- New but promising direction from the edge inference characterization paper.
- Study whether fusion/tiling/layout choices that win on cold runs lose under thermal or bandwidth limits.
- Potentially publishable framing: optimize for **stable long-horizon throughput** rather than burst latency.

## Papers currently most aligned with the core agenda
- **Orion**: best substrate for legality-aware, recompilation-aware partitioning on a real opaque NPU target.
- **DVM**: strongest direct opening for runtime fusion policy under dynamic shapes/control flow.
- **AscendOptimizer**: strongest operator-level evidence that host tiling and kernel pipelining must be optimized together.

## Secondary but useful idea sources
- **EAGLE-Pangu / OpenPangu speculative decoding**: useful for backend-safe speculative-state handling and fused-kernel legality constraints, but current optimization story seems incomplete.
- **ANVIL**: valuable as a graph-redesign exemplar for NPU-native operator sets.
- **Edge sustained-load characterization**: useful motivation for thermal/power-aware compiler policy.
- **TENSURE / TinyML / polynomial splatting**: more adjacent, but potentially useful for robustness tooling, tiny-NPU partitioning, and accelerator-friendly primitive substitution.

## Working research thesis
Real NPU optimization is increasingly limited not by missing fusion mechanisms, but by missing **boundary-selection logic** that accounts for legality, mutability, compile/update overhead, overlap potential, and hardware-hostile operator structure. The best opportunities are in building interpretable cost models that explain both **when to fuse** and **when not to**, using real accelerator constraints rather than generic compiler heuristics.
