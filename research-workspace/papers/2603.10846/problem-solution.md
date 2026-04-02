---
paper_id: "2603.10846v1"
title: "Towards Cold-Start Drafting and Continual Refining: A Value-Driven Memory Approach with Application to NPU Kernel Synthesis"
confidence: "medium"
relevance_band: "high-match"
opportunity_label: "follow-up"
---

# One-Sentence Summary
This paper uses a value-driven memory and reinforcement-learning style agentic loop to improve NPU kernel synthesis in a data-scarce programming domain.

# Problem
General-purpose models perform poorly on NPU kernel synthesis because there is too little high-quality training data compared with mature ecosystems like CUDA, making cold-start generation and iterative improvement difficult.

# Proposed Solution
The paper proposes EvoKernel, an agentic framework that treats kernel synthesis as a memory-based reinforcement-learning task and uses value-driven retrieval of prior experiences to guide both initial draft generation and iterative refinement.

# Claimed Contributions
- A self-evolving agentic framework for NPU kernel synthesis
- A value-driven memory retrieval mechanism for selecting useful past experiences
- Cross-task memory sharing from simpler to more complex operators
- A new NPU-focused benchmark variant and reported gains in correctness and latency

# Evidence Basis
- Abstract

# Limitations
- The abstract is framed around kernel synthesis rather than operator fusion or instruction fusion directly
- It is not clear how much the value function reflects hardware-grounded cost versus LLM self-improvement heuristics
- The link from synthesized kernels to compiler-wide fusion policy is indirect

# Relevance to Profile
This paper matters because it is close to the “automatic optimization” angle of your interests. If you later want an agent or learned system to reason about fusion, instruction choices, or cost-model approximations on an NPU, this is a useful neighboring approach.

# Analyst Notes
This is probably less directly relevant than DVM or AscendOptimizer for your immediate fusion questions, but it is valuable if you want to think about automation. The key question while reading is whether its value-driven memory mechanism could be repurposed from kernel synthesis to fusion-boundary or instruction-level decision-making.
