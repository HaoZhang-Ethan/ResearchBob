---
paper_id: "2603.23640v1"
title: "LLM Inference at the Edge: Mobile, NPU, and GPU Performance Efficiency Trade-offs Under Sustained Load"
confidence: "medium"
relevance_band: "high-match"
opportunity_label: "follow-up"
---

# One-Sentence Summary
The paper argues that under sustained on-device LLM inference, real deployment limits are often thermal, power, and memory-bandwidth constraints rather than peak compute, with mobile phones degrading sharply while a small NPU delivers low but stable energy-efficient throughput.

# Problem
Edge deployment of always-on LLMs needs sustained inference within tight thermal, power, and memory budgets, but common evaluations overemphasize short-run peak performance and miss the platform-level bottlenecks that determine usable long-duration behavior.

# Proposed Solution
Benchmark a fixed quantized LLM workload under warm-condition repeated runs across heterogeneous edge platforms and characterize sustained throughput, latency, power, and thermal behavior to reveal the true limiting factors on each device class.

# Claimed Contributions
- Provides a sustained-load empirical comparison of Qwen 2.5 1.5B 4-bit inference across four edge-relevant platforms: Raspberry Pi 5 + Hailo-10H NPU, Samsung Galaxy S24 Ultra, iPhone 16 Pro, and NVIDIA RTX 4050 laptop GPU.
- Shows that on mobile devices, thermal management dominates sustained LLM inference behavior, including large throughput collapse on iPhone and OS-enforced GPU throttling/termination on the Samsung device.
- Shows that dedicated accelerators exhibit different dominant limits, with the RTX 4050 constrained by battery power ceiling and the Hailo-10H by on-module memory bandwidth.
- Reports that the RTX 4050 sustains 131.7 tok/s at 34.1 W while the Hailo-10H sustains 6.9 tok/s under 2 W with near-zero variance, suggesting strong energy proportionality for the NPU despite much lower absolute throughput.
- Frames the results as deployment-level characterizations of combined hardware-software stacks rather than broad hardware capability claims.

# Evidence Basis
- Abstract-level empirical measurements over 20 warm-condition iterations using a fixed 258-token prompt and a single model configuration.
- Reported platform-specific observations: iPhone throughput drops by nearly half within two iterations; Samsung GPU hits a hard OS frequency floor that ends inference; RTX 4050 is battery-power-limited; Hailo-10H is memory-bandwidth-limited.
- Quantitative sustained metrics stated in abstract for RTX 4050 and Hailo-10H throughput/power.

# Limitations
- Evidence appears limited to a single model (Qwen 2.5 1.5B), single quantization setting (4-bit), and single prompt length/type.
- Only title and abstract were available here, so methodology details, measurement controls, compiler/runtime stack, and statistical rigor cannot be verified.
- The work appears primarily characterization-focused rather than proposing a new compiler, fusion, or scheduling technique.
- The claimed Hailo memory-bandwidth bottleneck and other root-cause attributions may rely on internal platform knowledge not exposed in the abstract.
- Cross-platform comparisons may be confounded by different software stacks, kernels, runtimes, and vendor-specific execution paths.

# Relevance to Profile
Adjacent to high-match compiler/accelerator interests: it is highly relevant for hardware-grounded reasoning about NPU bottlenecks and when sustained behavior diverges from nominal peak performance, but it does not, from the abstract alone, offer explicit operator fusion, graph compiler, or instruction scheduling methods. It may still be useful as motivation or validation data for compiler policies that account for thermal, power, and memory-bandwidth limits under sustained load.

# Analyst Notes
Author claims are mostly system-level characterization claims, not compiler optimization claims. Analyst inference: the paper may expose opportunities for hardware-aware compilation policies that avoid bandwidth-heavy fusion or choose different schedules when thermal throttling or memory ceilings dominate, especially on mobile/NPU targets. Uncertainty: without the full PDF, it is unclear how deeply the authors connect observed bottlenecks to microarchitectural behavior, runtime scheduling, kernel selection, or compiler-generated code.
