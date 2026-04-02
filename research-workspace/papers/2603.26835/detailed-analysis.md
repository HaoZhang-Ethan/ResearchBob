# ANVIL: Accelerator-Native Video Interpolation via Codec Motion Vector Priors

## Metadata
- paper_id: `2603.26835v3`
- pdf_url: https://arxiv.org/pdf/2603.26835v3
- relevance_band: `high-match`

## Detailed Summary
ANVIL is compelling because it reframes mobile video frame interpolation around what current NPUs are actually good at: dense convolutional inference, not arbitrary spatial warping, iterative flow refinement, or memory-heavy sampling pipelines. The paper’s central move is to reuse H.264 decoder motion vectors as a prior for prealignment, thereby removing learned optical flow and most hardware-unfriendly operators from the accelerator graph. The reported result—roughly 12.8 ms 1080p NPU inference and 28.4 ms median end-to-end playback on Snapdragon 8 Gen 3—is strong and unusually deployment-grounded. For a compiler/accelerator audience, the most interesting aspect is not just the model simplification, but the implicit graph shaping: ANVIL converts a difficult, mixed operator graph into a mostly convolution-dominated one that better matches mobile NPU execution. The main gap is that this hardware fit is argued at the operator-family level rather than through a detailed compiler or microarchitectural treatment of scheduling, memory traffic, layout choices, or when partial reintroduction of non-convolutional operators could become optimal.

## Problem
The paper targets real-time 30-to-60 fps video interpolation on mobile devices, where each synthesized frame must fit within about 33.3 ms end-to-end. It argues that mainstream flow-based VFI models are structurally mismatched to mobile NPUs for three reasons: spatial sampling/warping operators are either slow or unsupported, iterative flow refinement is fragile under 8-bit PTQ, and memory-bound operators dominate runtime. This is a strong problem framing for accelerator-native ML deployment: the obstacle is not just model size, but a graph/operator mix that current NPU stacks handle poorly. The paper further claims that these failures persist even when nominal throughput is high, because unsupported or inefficient ops spill to CPU/GPU or incur severe bandwidth and quantization penalties. From the profile’s perspective, this is a good 'fusion-policy looks incomplete' style problem: standard model design implicitly assumes a richer backend than mobile NPU compilers/hardware actually provide.

## Solution
ANVIL’s solution is to replace learned motion estimation and warping with codec-derived motion vector priors from the H.264/AVC decoder. These motion vectors are used to prealign input frames before the learned network, so the NPU model only needs to refine the residual mismatch and synthesize the interpolated frame. The resulting network is described as convolution-dominated and largely compute-bound, avoiding spatial sampling, iterative accumulation, and other memory-heavy components. This is less a small model tweak than a graph restructuring strategy: outsource coarse motion handling to the video codec path, then feed the NPU a graph consisting mostly of operators it accelerates well. The reported open-source Android player and device measurements make the proposal more credible as a full-stack systems result. Conservatively, because the PDF text is noisy, the exact network architecture details are hard to recover here; but the high-level design is clear and central.

## Key Mechanism
The paper’s key mechanism appears twofold. First, codec motion vectors provide a strong enough prior to eliminate learned optical flow and warping from the accelerator graph, which materially changes the operator distribution toward NPU-friendly convolutions. Second, the paper identifies quantized accumulation on recurrent/iterative flow states as a causal reason why integer quantization degrades iterative methods. That latter point is especially interesting: instead of saying 'PTQ hurts accuracy,' the paper isolates a mechanism tied to repeated state updates, implying that quantization error compounds through recurrence or iterative refinement. For hardware/compiler readers, this suggests a graph-level principle: operators may be individually quantizable, but their composition across iterative state paths can be unstable under INT8. This is the most actionable conceptual contribution because it may generalize beyond VFI to other iterative vision pipelines deployed on NPUs.

## Assumptions
ANVIL relies on several important assumptions. The biggest is availability of decoder-exposed motion vectors, and the current paper explicitly targets H.264/AVC playback. That means the approach depends on codec, platform software interfaces, and player integration, not just model architecture. It also assumes that decoder motion vectors are sufficiently informative for interpolation after residual refinement, at least for the target content distribution. Another assumption is that the prealignment stage can be implemented off the critical NPU path without creating a new bottleneck or synchronization penalty. The work also implicitly assumes that mobile NPU performance is dominated by operator support and bandwidth characteristics matching the paper’s framing, and that a convolution-heavy graph will remain the best choice across vendor stacks. These are reasonable, but likely less universal across newer NPUs or codecs with different MV semantics/exposure.

## Strengths
The strongest part of the paper is hardware-grounded problem selection. It does not merely compress an existing VFI model; it removes the exact operator classes that mobile NPUs struggle with. This is much more aligned with real deployment than benchmark-only efficiency work. The end-to-end device measurements on Snapdragon 8 Gen 3 and long-duration playback evaluation are also strong evidence that the claimed speedups survive outside isolated inference tests. Another strength is the causal analysis of quantization failure in iterative flow methods; that kind of explanation is more useful than black-box ablations. From a compiler perspective, the work is attractive because it effectively performs architecture-aware graph simplification: by exploiting codec-side priors, it reshapes the IR into something far easier for current NPU compilers to lower efficiently. Finally, the paper seems honest about scope, explicitly noting current H.264 targeting rather than overselling universality.

## Weaknesses
The main weakness, relative to your interests, is that the paper is accelerator-native but not deeply compiler-native. It motivates operator support and memory/computation balance, yet does not appear to expose detailed backend behavior such as kernel fusion boundaries, layout transforms, DMA costs, tiling choices, or instruction scheduling consequences. So while the model is well matched to hardware, the paper stops short of explaining how compiler decisions interact with that match. Another weakness is codec dependence: if motion vectors are unavailable, low quality, delayed, or semantically different across codecs/platform APIs, the method may lose its advantage. There is also a risk that moving prealignment outside the learned graph hides costs rather than eliminating them, unless those costs are carefully accounted for in all deployment settings. Finally, because the solution removes warping rather than optimizing it, it may leave accuracy on the table for scenes where decoder MVs are systematically poor, such as occlusion-heavy or non-translational motion cases.

## What Is Missing
Several things appear missing or underdeveloped. First, there is no clear hardware cost model connecting operator mix to actual NPU behavior in an interpretable way. The paper says the remaining graph is compute-bound, but for your profile the next question is: under what layouts, tile sizes, SRAM capacities, and bandwidth assumptions? Second, it does not seem to discuss negative cases in enough detail: when do codec MVs fail badly enough that a limited learned correction or selective warping becomes worthwhile? Third, the work does not appear to quantify compiler/runtime overheads such as graph partitioning, host-device synchronization, buffer materialization, or layout conversion between decoder surfaces and NPU tensors. Fourth, there is an unexploited scheduling question: once the graph is simplified, can decode, MV extraction, prealignment, and NPU inference be overlapped as a pipeline rather than treated mostly sequentially? Finally, there is no broader design-space exploration across codecs, vendors, or mixed-precision choices to show when the current all-in 'remove flow/warping' policy is optimal versus overly conservative.

## Why It Matters To Profile
This paper matters to your profile because it is an unusually concrete example of hardware-aware model redesign that changes the fusion/search space before the compiler even begins. It demonstrates that the right answer for an NPU is sometimes not better codegen for a bad graph, but a graph whose operator set aligns with supported, compute-dense kernels. That directly connects to operator fusion and accelerator compiler concerns: if spatial sampling and iterative state updates are fundamentally hostile to current mobile NPU backends, fusion policies that treat them as just another op sequence may be missing the real bottleneck. The paper also raises a useful compiler question: can backend- or microarchitecture-aware reasoning tell us when to keep, approximate, externalize, or remove certain operators altogether? Its quantization findings are similarly relevant because they point to graph structures where standard INT8 lowering is predictably fragile. In short, the work is valuable less as a final compiler solution and more as evidence that hardware behavior should change the model/operator decomposition itself.

## Possible Follow-Up Ideas
1) Build an explicit NPU-oriented cost model for VFI graphs that predicts when warping/iterative refinement should be removed, approximated, or retained. Include operator support, memory traffic, buffer liveness, layout conversions, and host/NPU partition costs. 2) Explore selective or regional refinement: use codec MVs globally, but trigger small learned motion correction only in blocks with low MV confidence, occlusion cues, or high residual error. This would directly address 'when fusion/extra ops should not happen' rather than adopting a global policy. 3) Treat decode + MV extraction + prealignment + residual CNN as a pipelined heterogeneous schedule problem. There may be measurable latency reductions from overlapping codec and NPU stages, especially with ring buffers and multi-frame lookahead. 4) Investigate compiler support for fused prealignment-friendly frontends, e.g., folding residual preprocessing, color conversion, and initial feature extraction into fewer kernels to reduce memory traffic from decoder output surfaces. 5) Study mixed precision specifically on recurrent/iterative state paths: perhaps limited higher precision for accumulations would recover iterative methods without fully abandoning them. 6) Extend beyond H.264 to HEVC/VVC if MV access is possible, and analyze whether richer codec motion information changes the optimal network/graph structure. 7) Compare 'external prior + conv residual net' against hardware-optimized approximate warping operators; if future NPUs gain better gather/scatter support, the current architecture choice may no longer be optimal. 8) A compiler paper follow-up could formalize ANVIL’s insight as graph rewriting rules driven by backend capability models: replace unsupported/memory-bound motion subgraphs with side-channel priors when available, and generate alternative lowered graphs depending on hardware and codec interface constraints.

## Linked Short Summary
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
