---
paper_id: "2603.23566v1"
title: "AscendOptimizer: Episodic Agent for Ascend NPU Operator Optimization"
confidence: "medium"
relevance_band: "high-match"
opportunity_label: "read-now"
---

# One-Sentence Summary
This paper uses an episodic agent to jointly optimize host-side tiling and kernel-side instruction scheduling for Ascend NPU operators.

# Problem
Operator optimization on Huawei Ascend NPUs is hard because public references are scarce and performance depends on a tightly coupled combination of host-side tiling and data movement plus kernel-side instruction scheduling and pipelining.

# Proposed Solution
The paper introduces AscendOptimizer, an agentic optimization loop that uses profiling-guided search to tune host-side tiling and mines reusable kernel optimization motifs from optimized kernels to guide kernel rewriting, alternating both steps until latency improves.

# Claimed Contributions
- An episodic agent framework for Ascend NPU operator optimization
- Profiling-in-the-loop search for tiling and data-movement configurations
- A kernel rewriting strategy based on retrieving optimization motifs from prior trajectories
- Benchmark evidence on 127 AscendC operators against open-source and agent/search baselines

# Evidence Basis
- Abstract

# Limitations
- The abstract frames the method at the operator level rather than directly addressing cross-operator fusion
- The system is specialized to the AscendC / Huawei Ascend ecosystem
- It is unclear from the abstract how much of the gain comes from search versus reusable learned heuristics
- The optimization target appears to be per-operator latency rather than whole-graph or pipeline-level global optimality
- There is no explicit indication in the abstract that the method reasons about when two optimized local kernels should or should not be fused
- The agent may discover good schedules empirically without yielding a reusable analytical cost model

# Relevance to Profile
This is one of the closest papers to your interests because it directly touches NPU operator optimization, instruction scheduling, pipelining, and host/kernel co-optimization. Even if it is not explicitly a fusion paper, it is very relevant to how fusion decisions might interact with scheduling and tiling on an NPU.

# Analyst Notes
The problem is highly relevant and concrete. The main reason to read it is not only the reported speedup, but also the optimization decomposition: host-side tiling plus kernel-side instruction scheduling is very close to the compiler/runtime boundary you care about. If the paper does not already model fusion, it may still expose where a fusion cost model should interface with tiling and pipeline decisions.

What to look for while reading:
- whether the host-side tiling search exposes features that could be reused as inputs to a fusion cost model
- whether the kernel-side rewriting step is implicitly exploiting pipeline overlap or OoO-style execution effects without naming them explicitly
- whether their benchmark includes operators whose best implementation changes once neighboring operators are fused

Where it may still be improvable:
- the paper may optimize each operator in isolation, while your target problem is likely a joint decision over operator fusion, instruction fusion, and schedule shape
- a stronger follow-up direction would be to turn their empirical search signals into an interpretable fusion-and-scheduling cost model
- another likely weakness is that an agentic loop can find fast code but still fail to explain transferability across operators or architectures
