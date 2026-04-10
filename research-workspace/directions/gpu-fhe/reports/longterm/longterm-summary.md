# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-10.md`

## Newly Selected Papers
- Towards the AlexNet Moment for Homomorphic Encryption: HCNN, theFirst Homomorphic CNN on Encrypted Data with GPUs

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- Deep Learning as a Service (DLaaS) stands as a promising solution for cloud-based inference applications. In this setting, the cloud has a pre-learned model whereas the user has samples on which she wants to run the model. The biggest concern with DLaaS is user privacy if the input samples are sensitive data. We provide here an efficient privacy-preserving system by employing high-end technologies such as Fully Homomorphic Encryption (FHE), Convolutional Neural Networks (CNNs) and Graphics Processing Units (GPUs). FHE, with its widely-known feature of computing on encrypted data, empowers a wide range of privacy-concerned applications. This comes at high cost as it requires enormous computing power. In this paper, we show how to accelerate the performance of running CNNs on encrypted data with GPUs. We evaluated two CNNs to classify homomorphically the MNIST and CIFAR-10 datasets. Our solution achieved a sufficient security level (> 80 bit) and reasonable classification accuracy (99%) and (77.55%) for MNIST and CIFAR-10, respectively. In terms of latency, we could classify an image in 5.16 seconds and 304.43 seconds for MNIST and CIFAR-10, respectively. Our system can also classify a batch of images (> 8,000) without extra overhead.

## Current Rolling Summary
## Problem clusters

### 1) GPU-accelerated FHE inference as an end-to-end systems problem
- **HCNN (1811.00778v3)** is a strong baseline for the active `gpu-fhe` intake: early demonstration that encrypted CNN inference can benefit from GPU offload.
- Core lesson: practical performance depends jointly on **HE-compatible model design**, **ciphertext packing/SIMD**, and **GPU mapping of FHE kernels**.
- Historical value is high even if absolute results are dated; useful as a reference point for what was gained by arithmetic acceleration alone.

### 2) Packing/layout vs raw kernel speed
- Recurring pattern: papers can speed up core arithmetic, but end-to-end wins are often limited by **slot layout inefficiency**, **rotations/automorphisms**, **key switching/base conversion**, and **memory movement**.
- Packing is essential, but its benefits are conditional on high slot utilization and low permutation overhead.
- This suggests the real bottleneck cluster is not “multiply faster” but “organize ciphertext computation so accelerator-friendly work dominates.”

### 3) Feasibility demos vs scalable encrypted ML
- Early systems show feasibility on small benchmarks (e.g., MNIST, CIFAR-10), but often require **HE-constrained architectures**, modest security assumptions, and still-high latency.
- Important recurring gap: acceleration of primitives does **not automatically translate** into practical larger-model encrypted inference.

## Common weaknesses in existing solutions
- **Arithmetic-centric optimization:** GPU offload likely helps NTT/modular arithmetic, but does not by itself solve rotations, key switching, and data-layout costs.
- **End-to-end scalability limits:** encouraging results on small datasets/tasks, weak evidence for realistic modern models.
- **Outdated operating points:** older security targets (e.g. >80-bit) and likely BFV-style assumptions reduce direct applicability to current deployment expectations.
- **Insufficient decomposition of gains:** often unclear how much improvement comes from GPU kernels vs packing strategy vs model simplification.
- **Throughput/latency ambiguity:** batching claims can look strong, but may rely on ideal packing utilization and may not reflect mixed or low-batch workloads.

## Most promising directions

### A) Modern GPU-first FHE profiling and decomposition
- Revisit early systems like HCNN with modern stacks and isolate where speedups actually come from:
  - NTT/modular multiplication
  - key switching / base conversion
  - rotations / automorphisms
  - host-device transfer and memory traffic
- High priority because this directly fits current issue-intake needs in `FHE on GPU`.

### B) Layout/packing co-design as a first-class optimization target
- Treat ciphertext layout as a **compiler/search problem** jointly optimized for:
  - slot utilization
  - rotation count
  - key-switch frequency
  - GPU memory locality / kernel fusion
- This currently looks like one of the clearest gaps between primitive acceleration and application-level wins.

### C) BFV vs CKKS on GPU under matched conditions
- Compare exact and approximate HE inference on GPU with:
  - same model topology
  - same security target
  - same batching assumptions
- Useful for separating “scheme choice” from “accelerator implementation” as the dominant factor.

### D) Multi-GPU / heterogeneous decomposition
- Explore scaling across CRT primes, ciphertext groups, or pipeline stages.
- Promising because CRT/channel-level parallelism appears structurally compatible with GPU scaling, but evidence remains thin.

### E) Standardized gpu-fhe benchmarking
- Strong practical need for reproducible benchmarks with fixed parameter sets, security levels, and profiler traces.
- Would help evaluate future intake papers on whether they improve arithmetic kernels only, or real end-to-end encrypted inference.

## Cumulative bottom line
- Current long-term view: **GPU-FHE remains a strong problem area, but the key open issue is not merely faster HE kernels.**
- The durable research opportunity is **cross-layer co-design**: scheme choice, packing/layout, rotation and key-switch management, and accelerator scheduling.
- **HCNN** should be remembered as an important baseline showing feasibility and framing the agenda, not as a complete solution.
