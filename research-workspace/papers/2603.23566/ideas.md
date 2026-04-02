# Idea Notes: AscendOptimizer

## Why This Paper Matters

This paper is useful because it sits very close to the boundary between:

- host-side tiling and data movement
- kernel-side instruction scheduling and pipelining
- hardware feedback-driven optimization on a real NPU stack

That is already close to your target area. The main gap is that the paper appears to optimize **operators one by one**, while your likely opportunity is to reason about **fusion boundaries and instruction-level behavior jointly**.

## Where The Current Solution Looks Weak

### 1. Operator-Centric Rather Than Graph-Centric

The optimization loop seems centered on a single operator implementation. That is valuable, but it likely ignores interactions between:

- neighboring operators,
- intermediate tensor lifetimes,
- memory traffic across operator boundaries,
- whether fusion changes the best tiling/scheduling plan.

If true, this is a real weakness because a fast isolated operator can still be a bad choice once embedded in a fused subgraph.

### 2. Search Without Enough Structure

The paper likely gets strong results by combining search, profiling, and retrieved optimization motifs. But a likely weakness is that this gives:

- good optimization outcomes,
- weak explanatory power,
- limited transfer into an explicit cost model.

That creates a gap for a more interpretable method.

### 3. Scheduling Without Explicit Fusion Reasoning

The paper clearly cares about instruction scheduling and pipelining, but it is not obvious from the abstract that it answers:

- when two operators should be fused,
- when fusion hurts pipeline overlap,
- when fusion increases register or local-memory pressure enough to lose performance.

That is exactly the kind of question you care about.

## Most Promising Follow-Up Ideas

### Idea A: Fusion-Aware Operator Optimizer

Instead of optimizing an operator alone, optimize it together with a small neighborhood:

- operator alone
- fused with predecessor
- fused with successor
- fused with both neighbors when possible

Then compare:

- total latency,
- memory traffic,
- on-chip buffer pressure,
- pipeline occupancy,
- schedule shape.

Why this is promising:
it turns the paper's operator optimizer into a **fusion decision engine**, which is closer to a publishable systems/compiler contribution for your direction.

### Idea B: Interpretable Fusion Cost Model from Search Traces

Use the same kind of hardware feedback/search traces, but do not stop at finding a fast implementation. Instead, distill the traces into a cost model whose inputs include:

- tensor shapes,
- operator types,
- estimated memory movement,
- instruction count or instruction mix,
- tiling features,
- pipeline overlap or queueing signals,
- whether the NPU backend can exploit OoO execution.

Why this is promising:
it upgrades a black-box optimizer into a reusable decision model that could generalize across operators and fusion candidates.

### Idea C: Joint Host-Tiling and Instruction-Fusion Optimization

The paper separates host-side tiling and kernel-side scheduling in a loop. A stronger follow-up may be to explicitly model their interaction:

- host tiling changes data reuse
- data reuse changes profitable instruction grouping
- instruction grouping changes local memory/register pressure
- that changes whether a fused operator is still worthwhile

Why this is promising:
this is exactly the kind of cross-layer coupling many papers under-model.

## Best Low-Risk Research Cut

Build a **fusion profitability analyzer** on top of their operator-level optimization setup.

Minimal claim:

- not “we solve all NPU fusion”
- but “operator-level optimization is not enough; fusion changes the optimal tiling/schedule regime”

This is lower risk because you can start with:

- a few operator families,
- one NPU backend,
- pairwise fusion only.

## Higher-Risk, Higher-Upside Direction

Learn a **hardware-grounded cost model** that predicts not only latency, but also **when fusion breaks pipeline efficiency** due to:

- queueing imbalance,
- synchronization boundaries,
- local-memory overflow,
- reduced OoO opportunity,
- instruction-sequence inflation.

If you can make this interpretable and accurate enough, that is much stronger than a pure search paper.

## What You Should Check In The Paper

- Does it expose profiling signals that could serve as cost-model features?
- Does it ever evaluate fused operators or only isolated kernels?
- Does it show cases where the best schedule changes after tiling changes?
- Does it measure memory traffic explicitly, or only latency?
- Does it explain failures, or only report wins?

## Good “Can Be Better” Thesis

AscendOptimizer likely shows that operator optimization on NPUs is a coupled host/kernel problem, but it may still stop one layer too early. The stronger next step is to make the same coupling **fusion-aware** and **cost-model-driven**, so the system can reason about whether a fast local implementation remains fast once surrounding operators and NPU pipeline effects are taken into account.
