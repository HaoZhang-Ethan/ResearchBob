---
paper_id: "2603.26835v3"
title: "ANVIL: Accelerator-Native Video Interpolation via Codec Motion Vector Priors"
confidence: "medium"
relevance_band: "high-match"
opportunity_label: "follow-up"
---

# One-Sentence Summary
This paper redesigns video interpolation for mobile NPUs by removing hardware-unfriendly operators and replacing them with codec-informed prealignment plus a compute-dominated residual network.

# Problem
Mainstream flow-based video interpolation performs poorly on mobile NPUs because key operators are too slow or unsupported, iterative refinement is fragile under 8-bit quantization, and memory-bound operators dominate the computation graph.

# Proposed Solution
The paper proposes ANVIL, which reuses motion vectors from the H.264/AVC decoder to prealign frames and removes learned optical flow, spatial sampling, and iterative accumulation from the NPU graph, leaving a more NPU-friendly convolution-heavy residual model.

# Claimed Contributions
- A mobile-NPU-oriented redesign of video interpolation
- Explicit removal of hardware-unfriendly operators from the accelerator graph
- Empirical latency results on Snapdragon 8 Gen 3
- A causal explanation for why iterative methods fail under integer quantization

# Evidence Basis
- Abstract

# Limitations
- The design is task-specific to video interpolation and H.264/AVC playback
- It is more about eliminating bad operators than learning a general fusion strategy
- The abstract does not describe a general-purpose compiler or cost model

# Relevance to Profile
This paper is relevant because it gives concrete evidence about which operator patterns are bad fits for NPUs. That is useful input for fusion reasoning: a good fusion policy often depends on recognizing hardware-hostile operators and avoiding graphs that amplify their cost.

# Analyst Notes
This is less about generic fusion algorithms and more about “NPU-native redesign.” It is still worth reading because it may reveal a negative heuristic set: which operators, dataflow patterns, or quantized iterative structures should never be fused together on an NPU-like target.
