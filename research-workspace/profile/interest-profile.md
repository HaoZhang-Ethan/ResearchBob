# Research Interest Profile

## Core Interests
- operator fusion
- graph compiler
- accelerator compiler
- tensor compiler
- instruction scheduling
- NPU
- neural processing unit

## Soft Boundaries
- compiler optimization for AI accelerators
- accelerator code generation
- hardware-aware compiler optimization
- memory layout, tiling, and pipelining for accelerators

## Exclusions
- model architecture papers with no compiler, runtime, or hardware execution angle
- GPU-only kernel fusion work that has no transferable NPU insight
- generic benchmark or survey papers without a concrete optimization mechanism

## Current-Phase Bias
- good problems where the existing solution or fusion policy looks incomplete
- hardware-grounded optimization opportunities that can lead to measurable speedup
- ideas where OoO-aware or pipeline-aware reasoning may change the optimal fusion choice

## Evaluation Heuristics
- reward papers that make explicit use of real NPU microarchitectural properties
- prefer cost models that are predictive, interpretable, and actionable
- prefer work that explains when fusion should not happen, not only when it should
- favor papers with clear evidence that compiler or runtime decisions match hardware behavior

## Open Questions
- when does out-of-order execution make aggressive instruction fusion counterproductive on NPUs
- which NPU pipeline or memory-system features most strongly change the optimal operator fusion boundary
- how should a fusion cost model account for dynamic shapes, runtime variability, and hardware queueing effects
- can operator fusion and instruction fusion be optimized jointly rather than as separate compiler passes
