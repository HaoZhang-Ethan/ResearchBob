---
paper_id: "2603.18372v1"
title: "TENSURE: Fuzzing Sparse Tensor Compilers (Registered Report)"
confidence: "medium"
relevance_band: "adjacent"
opportunity_label: "follow-up"
---

# One-Sentence Summary
The paper proposes a black-box fuzzing framework for sparse tensor compilers that uses valid Einsum-based kernel generation and metamorphic mutations to uncover crashes and silent miscompilations that generic fuzzers miss.

# Problem
Sparse tensor compilers generate irregular loop nests and control flow from declarative tensor expressions and storage formats, making them prone to subtle correctness bugs; existing graph-operator fuzzers and generic grammar fuzzers do not adequately cover arbitrary loop synthesis or produce enough semantically valid sparse tensor programs.

# Proposed Solution
TENSURE introduces an extensible black-box fuzzing approach for sparse tensor compilers using Einstein Summation as the input abstraction, a constraint-based generator to synthesize semantically valid sparse kernels, and semantic-preserving metamorphic mutations based on algebraic commutativity and storage-format variation to test compiler correctness without a trusted oracle.

# Claimed Contributions
- A first specialized black-box fuzzing framework for sparse tensor compilers.
- An Einsum-based input representation that can express complex and unconventional tensor contractions.
- A constraint-based generation algorithm claimed to achieve 100% semantic validity of generated kernels versus roughly 3.3% for baseline grammar fuzzers.
- Metamorphic testing operators that preserve semantics through commutativity and storage-format heterogeneity.
- An evaluation on TACO and Finch reporting many crashes and silent miscompilations, especially in TACO.

# Evidence Basis
- All details are drawn from the title and abstract only, not the full paper.
- The abstract reports comparative validity rates for generated test cases and bug findings on TACO and Finch.
- The abstract claims widespread fragility in tested systems, including majority-case failures for TACO on generated tests.

# Limitations
- This appears focused on compiler correctness testing, not directly on optimization quality, fusion policy, or hardware performance.
- Evidence is limited to abstract-level claims; implementation details, bug taxonomy, false-positive handling, and evaluation methodology are not visible here.
- Black-box fuzzing may reveal failures without explaining the underlying compiler phase or optimization interaction that caused them.
- Sparse tensor compilers are adjacent to, but not the same as, dense NPU/graph/tensor compiler pipelines emphasized in the profile.

# Relevance to Profile
Adjacent rather than core. It is compiler-focused and may be useful if you care about robustness of tensor compiler transformations or testing of code generation stacks, but it does not obviously address operator fusion, instruction scheduling, NPU microarchitecture, or hardware-aware cost modeling.

# Analyst Notes
Potential value as a follow-up read if you want ideas for testing compiler transformations or metamorphic validation of optimization passes. Lower priority for direct fusion/scheduling research unless you are exploring reliability tooling for accelerator compilers or sparse-NPU compiler stacks.
