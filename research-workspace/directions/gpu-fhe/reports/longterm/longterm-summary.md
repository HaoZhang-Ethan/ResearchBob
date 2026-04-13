# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-13.md`

## Newly Selected Papers
- CAT: A GPU-Accelerated FHE Framework with Its Application to High-Precision Private Dataset Query
- GME: GPU-based Microarchitectural Extensions to Accelerate Homomorphic Encryption
- AEGIS: Scaling Long-Sequence Homomorphic Encrypted Transformer Inference via Hybrid Parallelism on Multi-GPU Systems
- Towards the AlexNet Moment for Homomorphic Encryption: HCNN, theFirst Homomorphic CNN on Encrypted Data with GPUs

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- Direct hit on GPU-accelerated FHE framework. Appears highly aligned with system design: explicitly describes a three-layer architecture, core math layer, combined operations, and API-accessible FHE operators; also says open-source.
- Architecture/system-focused rather than pure software library. Relevant for mapping HE/FHE primitives to GPU microarchitecture and understanding accelerator-aware bottlenecks.
- Application-system paper for encrypted ML on multi-GPU systems. Included because it appears to have substantial systems contribution: hybrid parallelism, memory capacity scaling, and multi-GPU orchestration.
- Deep Learning as a Service (DLaaS) stands as a promising solution for cloud-based inference applications. In this setting, the cloud has a pre-learned model whereas the user has samples on which she wants to run the model. The biggest concern with DLaaS is user privacy if the input samples are sensitive data. We provide here an efficient privacy-preserving system by employing high-end technologies such as Fully Homomorphic Encryption (FHE), Convolutional Neural Networks (CNNs) and Graphics Processing Units (GPUs). FHE, with its widely-known feature of computing on encrypted data, empowers a wide range of privacy-concerned applications. This comes at high cost as it requires enormous computing power. In this paper, we show how to accelerate the performance of running CNNs on encrypted data with GPUs. We evaluated two CNNs to classify homomorphically the MNIST and CIFAR-10 datasets. Our solution achieved a sufficient security level (> 80 bit) and reasonable classification accuracy (99%) and (77.55%) for MNIST and CIFAR-10, respectively. In terms of latency, we could classify an image in 5.16 seconds and 304.43 seconds for MNIST and CIFAR-10, respectively. Our system can also classify a batch of images (> 8,000) without extra overhead.

## Current Rolling Summary
# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-10.md`

## Newly Integrated Papers
- CAT: A GPU-Accelerated FHE Framework with Its Application to High-Precision Private Dataset Query
- GME: GPU-based Microarchitectural Extensions to Accelerate Homomorphic Encryption
- AEGIS: Scaling Long-Sequence Homomorphic Encrypted Transformer Inference via Hybrid Parallelism on Multi-GPU Systems
- Towards the AlexNet Moment for Homomorphic Encryption: HCNN, theFirst Homomorphic CNN on Encrypted Data with GPUs

## Current Problem Clusters
- GPU-FHE as a full-stack systems problem
- Layout / packing / memory-management bottlenecks
- Hardware-software co-design for HE on GPU
- Multi-GPU scaling for encrypted workloads

## New Insights
- The center of gravity is shifting from “accelerate HE primitives on one GPU” toward **frameworks, runtime abstractions, communication-aware scheduling, and memory orchestration**.
- A recurring pattern across HCNN, CAT, GME, and AEGIS: **raw arithmetic speedups are necessary but insufficient**; end-to-end wins depend on ciphertext layout, key-switch/rotation costs, memory allocation/traffic, and execution planning.
- There is now a clearer split between three complementary directions:
  1. **Framework/infrastructure** (CAT)
  2. **Microarchitectural bottleneck analysis** (GME)
  3. **Distributed scaling/runtime orchestration** (AEGIS)
- This sharpens the open issue in `gpu-fhe`: the key gap is not just faster NTT/modmul, but the lack of strong intermediate abstractions between HE kernels and application workloads.

## Current Rolling Summary

## Problem clusters

### 1) GPU-FHE as an end-to-end systems stack
- **HCNN** remains a useful historical baseline for showing feasibility of GPU-accelerated encrypted inference.
- **CAT** strengthens the case that the next valuable contribution is not another isolated kernel, but a **layered GPU-FHE framework** connecting low-level arithmetic, composed operators, and application APIs.
- Emerging lesson: practical progress needs reusable system layers for memory planning, operator composition, and scheme-aware execution, not just hand-optimized kernels.

### 2) Packing/layout and memory traffic are persistent first-order bottlenecks
- Across the papers, bottlenecks repeatedly trace back to **ciphertext layout, slot utilization, rotations/automorphisms, key switching, and memory movement**.
- CAT hints that **memory pooling / allocation strategy** may matter as much as arithmetic throughput in a reusable GPU-FHE stack.
- HCNN already suggested that batching gains depend heavily on favorable packing assumptions; this remains true in more modern settings.
- This cluster increasingly looks like a **compiler/runtime optimization problem** rather than a pure crypto-kernel problem.

### 3) Hardware-software co-design is becoming unavoidable
- **GME** is important because it frames some HE-on-GPU limits as potentially **microarchitectural**, not just software shortcomings.
- Likely enduring insight: FHE workloads stress GPUs differently from standard ML workloads, especially in **modular arithmetic width, structured communication, and memory-system behavior**.
- This suggests a productive split in future work:
  - software techniques that emulate/approximate missing support on current GPUs
  - architectural proposals identifying what truly requires new hardware

### 4) Multi-GPU scaling is emerging as the next serious frontier
- **AEGIS** pushes beyond single-GPU acceleration toward **memory-capacity scaling and communication-aware execution** for long-sequence encrypted transformers.
- This is a meaningful shift: for larger encrypted models, the limiting factor may be **HBM capacity and inter-GPU communication**, not only per-device kernel speed.
- Multi-GPU FHE likely needs hybrid strategies rather than plain data/model parallelism because ciphertext-heavy workloads have unusual compute/memory/communication ratios.

### 5) Feasibility demos still outpace convincing scalable deployments
- HCNN shows the historical pattern: strong feasibility signal, but with HE-constrained models, dated security targets, and high latency for anything beyond small tasks.
- Newer systems appear more ambitious, but the same risk persists: **framework quality, distributed orchestration, or hardware insight may improve parts of the stack without yet making modern encrypted ML broadly practical**.

## Common weaknesses in existing solutions
- **Arithmetic-centric evaluation:** many works still risk overemphasizing NTT/modular arithmetic while under-analyzing rotations, key switching, basis conversion, and memory orchestration.
- **Weak decomposition of gains:** often unclear what fraction of speedup comes from kernel optimization vs layout choice vs runtime scheduling vs model simplification.
- **Limited end-to-end generality:** some papers target one workload class (CNN inference, dataset query, transformer inference) without proving portability across HE applications.
- **Systems abstraction gap:** there is still no clear standard IR/runtime boundary for GPU-FHE operator fusion, memory planning, and distributed placement.
- **Platform sensitivity:** multi-GPU and architecture-heavy ideas may depend strongly on fast interconnects, specific GPU generations, or simulator assumptions.
- **Benchmark fragility:** batching and throughput claims are often sensitive to packing efficiency, idealized workloads, or narrow parameter choices.
- **Historical operating points:** older papers in particular use weaker security targets or outdated scheme/model assumptions, limiting direct comparability.

## Most promising directions

### A) GPU-FHE intermediate abstractions: IR, operator fusion, and memory planning
- The strongest cross-paper opportunity is a **middle layer** between HE kernels and applications.
- Desired capabilities:
  - operator fusion boundaries
  - ciphertext lifetime analysis
  - memory pool / allocation planning
  - packing/layout search
  - scheduling across streams/devices
- CAT makes this feel especially timely and practical.

### B) Layout/packing co-design with runtime and compiler support
- Treat layout as a first-class optimization target jointly affecting:
  - slot utilization
  - rotation/key-switch count
  - memory locality
  - communication volume
  - fusion opportunities
- This direction now connects single-GPU and multi-GPU work: layout decisions shape both kernel efficiency and distributed traffic.

### C) Software-vs-hardware bottleneck separation for GPU-FHE
- Use papers like GME to distinguish:
  - what can be fixed with better CUDA/Triton kernels, shared-memory tiling, scheduling, and runtime design
  - what likely needs architectural support in arithmetic units, NoC/interconnect, or memory hierarchy
- This is especially promising for issue intake because it clarifies where practical near-term work is still available.

### D) Multi-GPU HE runtimes with communication-aware scheduling
- AEGIS suggests strong potential in:
  - hybrid parallelism
  - topology-aware placement
  - overlap of communication and HE kernels
  - memory-capacity scaling for long-sequence encrypted models
- Important open question: how much of distributed HE performance is controlled by scheduler/runtime quality versus base HE kernel quality.

### E) Standardized gpu-fhe benchmarking and profiling
- Strong need for reproducible benchmarks with fixed:
  - scheme/parameter sets
  - security levels
  - packing assumptions
  - latency/throughput modes
  - profiler breakdowns for arithmetic, rotations, key switching, memory traffic, and communication
- This would make CAT/GME/AEGIS-style contributions much easier to compare on end-to-end value.

### F) Modern replication of early GPU-FHE baselines
- Revisit HCNN-style encrypted inference with modern libraries and security targets.
- Key value is decomposition: identify what improved over time in
  - NTT/modmul
  - key switching / base conversion
  - memory movement
  - packing efficiency
  - scheduling/runtime support
- Useful as a grounded baseline for evaluating whether newer work really solves the historical bottlenecks.

## Cumulative bottom line
- The durable conclusion is now stronger: **GPU-FHE should be viewed as a cross-layer systems problem, not a primitive-acceleration problem.**
- The most promising work is converging on three open fronts:
  1. **framework/runtime abstractions**,
  2. **hardware-software co-design**, and
  3. **multi-GPU scaling under memory/communication pressure**.
- The biggest recurring gap remains the absence of a robust shared layer that can jointly optimize **ciphertext layout, operator composition, memory management, and device scheduling**.
- **HCNN** remains the historical feasibility marker; **CAT** looks like the practical framework direction; **GME** sharpens the architectural bottleneck map; **AEGIS** points to the next frontier of distributed encrypted inference.
