# TENSURE: Fuzzing Sparse Tensor Compilers (Registered Report)

## Metadata
- paper_id: `2603.18372v1`
- pdf_url: https://arxiv.org/pdf/2603.18372v1
- relevance_band: `high-match`

## Detailed Summary
TENSURE targets a real and under-served problem: sparse tensor compilers generate irregular loop nests and format-dependent control flow, so standard graph/operator fuzzers and generic grammar fuzzers do not adequately stress them. The paper’s main idea is to use Einsum as a compact, general abstraction for sparse tensor kernels, then generate only semantically valid expressions with a constraint-based method and apply metamorphic mutations that should preserve meaning while varying algebraic form and storage formats. On the reported evidence, this sharply improves valid-input generation and exposes many crashes and silent wrong-code cases in TACO, with fewer issues in Finch. As a research direction, it looks strong on problem selection and practical bug-finding, but it is mainly a testing framework paper rather than a compiler optimization paper; for your interests, its value is more as infrastructure that could uncover optimization/correctness gaps in sparse codegen, scheduling, and format-aware lowering than as a direct answer to fusion or NPU compilation decisions.

## Problem
Sparse Tensor Compilers must lower high-level sparse tensor algebra into low-level code with arbitrary synthesized loops, irregular iteration spaces, and storage-format-specific accesses. That combination makes them vulnerable to correctness bugs, especially subtle silent miscompilations rather than only crashes. The paper argues that existing testing approaches are mismatched to this setting: DNN graph fuzzers tend to mutate within a fixed operator vocabulary, so they do not explore arbitrary loop synthesis, and generic grammar fuzzers struggle because sparse tensor expressions have strict semantic constraints, especially on index reuse across tensors. The result is poor coverage of the failure modes unique to STCs.

## Solution
The proposed solution is a black-box fuzzing framework, TENSURE, centered on Einsum as the input language. Einsum gives a broad but structured way to express tensor contractions beyond a canned operator set. TENSURE then uses a constraint-based generator to synthesize semantically valid kernels rather than relying on unconstrained grammar generation. For oracle construction without a trusted reference implementation, it uses metamorphic testing: semantic-preserving mutations based on algebraic commutativity and changes in storage format should produce equivalent outputs. The framework is evaluated on TACO and Finch and reportedly finds many failures, especially in TACO.

## Key Mechanism
The key mechanism appears to be the combination of 1) an input abstraction expressive enough to induce diverse synthesized loop structures, and 2) a generation procedure that enforces semantic validity up front. The paper claims 100% semantic validity for generated kernels versus about 3.3% for baseline grammar fuzzers, which is important because sparse expressions are highly constrained. The second mechanism is metamorphic testing specialized to sparse tensor semantics: rather than comparing against a gold implementation, TENSURE transforms a valid test into another valid test expected to be equivalent under commutativity or storage-format heterogeneity, then checks behavioral consistency. This is a practical way to detect wrong-code in domains where reference evaluation is hard or expensive.

## Assumptions
Several assumptions seem central. First, Einsum is assumed to be expressive enough to cover the bug-prone regions of STC lowering that matter in practice. Second, the constraint system is assumed to encode semantic validity correctly; if it misses legality conditions, apparent compiler bugs may instead be malformed tests. Third, metamorphic equivalences based on algebraic rewrites and format changes are assumed to hold under the compiler/runtime semantics being tested, including any corner cases around duplicates, ordering, or numerical accumulation. Fourth, black-box testing is assumed sufficient to drive the compiler into interesting internal code-generation states without internal coverage guidance. Because the extracted text is noisy, it is unclear how thoroughly the paper discusses floating-point nondeterminism, duplicate coordinate semantics, canonicalization requirements, or whether all tested formats have exactly matching observable behavior.

## Strengths
The biggest strength is problem choice: sparse compiler correctness is important and clearly under-tested. The use of Einsum is elegant because it expands beyond fixed operator vocabularies while staying compact and familiar. The reported jump in valid-input rate is a strong practical contribution if it holds, since fuzzing throughput depends heavily on avoiding invalid cases. The metamorphic strategy is well-matched to the lack of trusted references in sparse compilation. Another strength is that the framework appears extensible and black-box, which lowers adoption barriers across multiple sparse compiler systems. Finally, the evaluation result that a majority of generated cases expose crashes or silent miscompilations in TACO is impactful because it suggests current STCs remain fragile even when they are widely used as research infrastructure.

## Weaknesses
The paper, at least from the available text, seems stronger at finding bugs than at localizing root causes or explaining which compiler passes are systematically failing. That limits insight into how compiler designers should prioritize fixes. A second weakness is potential semantic narrowness: Einsum captures tensor contractions well, but sparse compilers often also involve transformations, reductions with nuanced identities, masking, format conversion, workspace management, and inspector-executor behavior that may not be fully covered. Third, black-box fuzzing can miss deep pass interactions that require targeted steering; without coverage or pass-aware feedback, effectiveness may plateau. Fourth, metamorphic relations in sparse settings can be tricky because storage formats may differ in ordering, duplicate handling, zero elision, or floating-point accumulation order, so false positives/negatives are a risk unless carefully controlled. Finally, for a registered report and from the summary alone, there is limited indication of whether the evaluation measures structural coverage of generated loop patterns, not just bug counts.

## What Is Missing
What seems most missing for a deeper research contribution is a characterization of bug classes tied to compiler internals: e.g., merge lattice construction, iterator co-iteration, legality checks for index reuse, reduction lowering, format-specialized code templates, or simplification passes. Also missing, from your perspective, is any connection between discovered bugs and optimization decisions such as schedule selection, tiling, memory layout, or fusion boundaries. There is no obvious hardware grounding: the paper does not appear to study how sparse lowering interacts with accelerator memory systems, pipeline structure, or instruction scheduling. Another likely gap is a notion of test-space adequacy beyond semantic validity—such as diversity of generated loop nests, sparsity patterns, or control-flow motifs. It is also unclear whether the framework can target performance bugs, not just correctness bugs, for example pathological schedule choices or format selections that trigger severe slowdowns.

## Why It Matters To Profile
For your profile, this paper matters less as a direct optimization method and more as enabling infrastructure around compiler trustworthiness in irregular tensor lowering. Sparse tensor compilation is exactly where high-level algebra meets low-level schedule and storage-format decisions; if the compiler is already fragile on correctness, aggressive fusion, pipelining, or hardware-aware transformations become harder to deploy safely. The paper also implicitly highlights a broader point relevant to accelerator compilers: operator-vocabulary fuzzers miss bugs introduced by arbitrary loop synthesis, which is also a concern in tensor compilers and NPU codegen stacks once they lower beyond canonical ops. A promising angle is that the same constraint-based, semantics-aware generation idea could be repurposed to test hardware-aware optimizers, cost models, and fusion policies under irregular access patterns where conventional benchmarks are too narrow.

## Possible Follow-Up Ideas
1) Turn bug-finding into bug-understanding: build a pass-level differential triage pipeline that maps each failing case to likely internal mechanisms such as sparse iterator merge, reduction lowering, format conversion, or simplification. 2) Expand beyond correctness to performance metamorphism: generate semantically equivalent sparse kernels whose different storage formats or algebraic forms should induce predictable cost differences, then test whether the compiler’s chosen schedule/format matches hardware behavior. 3) Add white-box or grey-box feedback from compiler IR structure, generated loop-nest features, or pass coverage so the fuzzer can target under-explored sparse codegen regions. 4) Extend the input abstraction beyond pure Einsum to cover masking, sampled dense-dense operations, format conversion, workspace temporaries, and inspector-executor constructs. 5) Introduce numerics-aware metamorphic checks that explicitly reason about accumulation order and duplicate semantics to separate real wrong-code from benign floating-point drift. 6) For your domain, adapt the method to accelerator compilers: generate sparse or irregular tensor programs that stress fusion boundaries, tiling choices, and memory-layout lowering on NPUs, especially where pipeline-aware or OoO-aware reasoning might alter the best transformation. 7) Build an interpretable cost/legality model on top of the generated corpus: not just “does it crash,” but “when should this transformation not be applied,” which aligns well with your interest in actionable compiler decision rules. 8) Use the failing corpus as supervision for robust sparse lowering guards or for learned heuristics that predict unsafe optimization combinations.

## Linked Short Summary
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
