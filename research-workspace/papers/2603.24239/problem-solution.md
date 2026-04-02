---
paper_id: "2603.24239v1"
title: "DVM: Real-Time Kernel Generation for Dynamic AI Models"
confidence: "medium"
relevance_band: "high-match"
opportunity_label: "read-now"
---

# One-Sentence Summary
This paper proposes a real-time compiler for dynamic AI models that combines runtime kernel generation with both static and dynamic operator fusion on NPUs.

# Problem
Dynamic tensor shapes and control flow make offline compilation either too expensive or too conservative, while naive runtime compilation adds too much overhead and hurts model efficiency.

# Proposed Solution
The paper introduces DVM, a runtime compiler that uses a bytecode virtual machine for fast operator compilation and adds an operator fuser that supports both symbol-deduction-based static fusion and runtime fusion on dynamic graphs.

# Claimed Contributions
- A real-time runtime compiler for dynamic AI operators
- A bytecode-VM execution model to reduce compilation overhead on NPUs
- Static-graph and dynamic-graph operator fusion support
- Large efficiency and compilation-time gains over existing baselines

# Evidence Basis
- Abstract

# Limitations
- The abstract emphasizes operator compilation and fusion availability more than a detailed fusion cost model
- It is not yet clear how the runtime decides when fusion is profitable versus harmful
- The NPU execution model is only summarized at a high level in the abstract
- The bytecode-VM approach may reduce compilation overhead while still leaving open whether the generated fused kernels are globally optimal for a specific NPU
- The paper may improve fusion opportunity coverage without fully characterizing the hardware-side penalties of over-fusion
- The abstract does not clarify whether the runtime fusion policy adapts to microarchitectural properties such as queueing, memory pressure, or execution overlap

# Relevance to Profile
This is highly relevant because it directly mentions operator fusion on NPUs and lives at the exact boundary of runtime compilation, dynamic execution, and fusion decision-making. It is especially useful if you care about how a cost model should behave under dynamic shapes or dynamic control flow.

# Analyst Notes
Among the current shortlist, this is probably the most directly useful paper for fusion policy reasoning. Even if it does not fully solve the cost-model problem, it likely exposes the decision surface: when runtime information makes fusion newly profitable, and what kinds of VM or execution constraints change the best fusion boundary.

What to look for while reading:
- how the paper represents dynamic information when deciding runtime fusion
- whether pattern-based and stacking-based fusion are backed by a common profitability model or by hand-tuned rules
- whether the virtual instruction layer exposes exactly the kind of features that a hardware-aware fusion cost model would need

Where it may still be improvable:
- if their runtime fuser is mostly rule-based, a natural extension is to learn or fit a true cost model over dynamic runtime state
- if they focus on operator-level runtime fusion, a next step for your direction is to connect fusion choice with instruction-level scheduling and NPU pipeline behavior
- the biggest likely gap is that “fast runtime compilation” and “correct fusion profitability” are related but not identical goals; there may still be room for better fusion decisions even if compilation is already cheap
