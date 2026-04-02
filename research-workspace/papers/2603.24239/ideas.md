# Idea Notes: DVM

## Why This Paper Matters

This paper is probably the closest one in the current set to your direct interest in:

- operator fusion,
- dynamic fusion,
- compiler/runtime boundary decisions,
- fusion profitability under real execution constraints.

Its core value is not just that it supports runtime fusion, but that it forces the right question:

**when dynamic information changes the best fusion boundary.**

## Where The Current Solution Looks Weak

### 1. Fusion Support Does Not Equal Fusion Understanding

The abstract says DVM supports:

- symbol-deduction-based static fusion,
- runtime fusion on dynamic graphs,
- pattern-based and stacking-based fusion.

That sounds strong, but a likely weakness is that “supports more fusion” is not the same as “knows when fusion is actually good.”

The central open question is:

- is the policy rule-based,
- heuristic,
- or cost-model-driven?

If it is mostly rule-based, there is a clear opening.

### 2. Compilation Overhead and Fusion Profitability Are Different Objectives

The paper is strongly motivated by reducing compilation latency. That is important, but it may blur two separate goals:

- making compilation fast,
- making fused execution optimal.

A system can compile very quickly and still choose a suboptimal fusion boundary.

### 3. Dynamic Graph Support May Still Ignore Hardware Microeffects

The abstract suggests better fusion coverage on dynamic graphs, but it does not say whether fusion profitability accounts for:

- memory-system behavior,
- buffer pressure,
- queueing,
- pipeline overlap,
- instruction scheduling quality,
- OoO-sensitive execution effects.

That is where your angle becomes stronger.

## Most Promising Follow-Up Ideas

### Idea A: Runtime Fusion Cost Model for NPUs

Take the setting DVM cares about, but replace or augment heuristic fusion decisions with a runtime cost model that uses:

- dynamic tensor shape,
- operator sequence type,
- estimated intermediate memory footprint,
- candidate fusion depth,
- backend-specific scheduling features,
- pipeline occupancy signals,
- hardware queue or overlap indicators.

Why this is promising:
the paper already creates the right runtime setting, but the most publishable gap may be the **decision model**, not the runtime compiler itself.

### Idea B: Fusion Boundary Selection with Instruction-Level Awareness

Current dynamic fusion systems often reason at graph/operator level. Your more novel angle is:

- the best operator fusion boundary may depend on downstream instruction scheduling,
- especially if fused code changes instruction mix, dependency chains, or on-chip resource pressure.

That suggests a joint formulation:

- graph-level candidate fusion generation,
- instruction-level cost estimation,
- backend-specific choice.

Why this is promising:
it connects operator fusion to instruction fusion, which is much closer to your actual taste.

### Idea C: Dynamic Fusion Under OoO-Sensitive Execution

If the NPU has any OoO-like capability, a simple “more fusion is better” policy can be wrong:

- fusion can remove overhead,
- but can also reduce exploitable overlap,
- serialize what used to run with implicit slack,
- or create a larger block with worse pipeline utilization.

A strong paper could study:

- when dynamic fusion increases work locality,
- versus when it suppresses useful execution flexibility.

Why this is promising:
that question is much less generic and much more hardware-specific, which is good.

## Best Low-Risk Research Cut

Build a **runtime fusion profitability study** for NPUs:

- choose a small set of operator patterns,
- vary shape/dynamic conditions,
- compare no fusion / static fusion / heuristic dynamic fusion / cost-model-guided dynamic fusion.

Minimal claim:

- existing runtime fusion support over-fuses or under-fuses under certain dynamic conditions,
- a hardware-aware cost model fixes that.

This is likely the cleanest “paper after DVM” direction.

## Higher-Risk, Higher-Upside Direction

Create a **joint operator-fusion + instruction-scheduling framework** for dynamic NPU execution.

Instead of:

- choosing fused operators first,
- and scheduling instructions later,

make the scheduler itself part of the fusion decision loop.

This is harder, but much more aligned with your real interests.

## What You Should Check In The Paper

- Are fusion decisions explained by a cost model or by ad hoc rules?
- How does DVM decide when runtime fusion is worth the overhead?
- Do they expose intermediate features or logs that could be reused for your own model?
- Are their best gains coming from faster compile, better fusion, or both?
- Do they show any failure cases where extra fusion hurts?

## Good “Can Be Better” Thesis

DVM likely demonstrates that dynamic operator fusion on NPUs is feasible and efficient, but feasibility is only the first step. The more interesting unsolved problem is **runtime fusion profitability under hardware-aware constraints**. In particular, fusion should be chosen not just from graph structure or symbolic shape information, but from its predicted effect on memory traffic, scheduling quality, and NPU execution behavior. That is where a stronger, more novel paper could sit.
