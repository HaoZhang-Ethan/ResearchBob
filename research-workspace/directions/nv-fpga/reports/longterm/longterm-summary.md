# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-10.md`

## Newly Selected Papers
- Digitally Mutating NV-FPGAs into Physically Clone-Resistant Units

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- The concept of Secret Unknown Ciphers (SUCs) was introduced a decade ago as a new visionary concept without devising practical real-world examples. The major contribution of this work is to show the feasibility of "self-mutating" unknown cipher-modules for physical security applications in a non-volatile FPGA environment. The mutated devices may then serve as clone-resistant physical units. The mutated unpredictable physical-digital modules represent consistent and low-cost physical identity alternatives to the traditional analog Physically Unclonable Functions (PUFs). PUFs were introduced two decades ago as unclonable analog physical identities which are relatively complex and suffer from operational inconsistencies. We present a novel and practical SUC-creation technique based on pre-compiled cipher-layout-templates in FPGAs. A devised bitstream-manipulator serves as "mutation generator" to randomly-manipulate the bitstream without violating the FPGA design rules. Two large cipher classes (class-size larger than $2^{1000}$) are proposed with optimally designed structure for a non-volatile FPGA fabric structure. The cipher-mutation process is just a simple random unknown-cipher-selection by consulting the FPGA's internal True Random Number Generator (TRNG). The security levels and qualities of the proposed ciphers are evaluated. The attained security levels are scalable and even adaptable to the post-quantum cryptography. The hardware and software complexities of the created SUCs are experimentally prototyped in a real field FPGA technology to show very promising results.

## Current Rolling Summary
# Rolling long-term summary

## Core cluster: NV-FPGA-native hardware identity and clone resistance
- **Emerging direction:** Use **non-volatile FPGA configuration itself** as the source of per-device uniqueness, rather than relying on noisy analog PUF behavior.
- **Key example:** `1908.03898v1` proposes **TRNG-driven mutation of pre-compiled, fabric-legal cipher templates** to instantiate device-specific **Secret Unknown Ciphers (SUCs)** inside NV-FPGAs.
- **Why this matters:** Strong fit to `nv-fpga` focus because it reframes programmability and non-volatility as **security primitives**, not only attack surfaces.

## Recurring problem clusters
### 1) Stable hardware identity without analog PUF fragility
- Desired property: per-chip uniqueness with better repeatability across power cycles, voltage/temperature variation, and aging.
- Current promising angle: **persistent digital structural uniqueness** stored in NV-FPGA configuration.

### 2) Secure self-personalization / provisioning
- Interest is shifting toward **on-chip, post-manufacture personalization** using trusted entropy sources.
- The attractive pattern is **TRNG-seeded first-boot mutation or instantiation** of a hidden hardware structure.

### 3) Bitstream-level security as both mechanism and threat boundary
- Bitstream manipulation appears increasingly relevant as a design method for creating uniqueness.
- At the same time, **bitstream access, extraction, reverse engineering, and legality constraints** are the obvious attack and portability boundaries.

### 4) Hardware-bound roots of trust beyond conventional keys
- A recurring adjacent opportunity: combine **structural uniqueness** with standard cryptographic flows for authentication, secure boot, and device-bound secrets.
- Best viewed as **root-identity infrastructure**, not just as a standalone “new cipher” idea.

## Common weaknesses / recurring gaps
### A) Threat models are weaker than the claims
- Large nominal design spaces (e.g. `>2^1000`) do **not** by themselves establish clone resistance.
- Repeated missing pieces:
  - bitstream readout assumptions
  - invasive extraction assumptions
  - side-channel/fault resilience
  - structural recovery difficulty under realistic attackers

### B) Security is often argued from hidden structure, but lifecycle is underdefined
- Frequent under-specification:
  - enrollment
  - verifier interaction
  - revocation/replacement
  - failure recovery
  - reprovisioning/renewability
- For SUC-like approaches, this protocol layer is as important as the hardware mechanism.

### C) Effective entropy is not the same as combinatorial diversity
- Need to distinguish:
  - nominal count of realizable variants
  - actually distinguishable instances
  - attack-relevant entropy after leakage and structural correlations

### D) Vendor/family specificity may limit real usefulness
- Pre-compiled templates and safe bitstream mutation are likely **fabric-specific**.
- Portability and dependence on undocumented bitstream knowledge remain recurring concerns.

### E) Comparisons against FPGA PUF baselines are often incomplete
- The key benchmark questions remain:
  - reliability over environment and aging
  - area/power/latency
  - helper-data complexity
  - modeling resistance
  - extraction/clone cost

## Most promising directions
### 1) Formalizing effective clone resistance for NV-FPGA personalization schemes
- High-priority research need: models that separate **design-space size** from **true resistance to cloning/reconstruction** under bitstream, invasive, and side-channel adversaries.

### 2) Attested first-boot personalization
- Promising issue-intake direction: **first-boot or in-field mutation** with auditable evidence that personalization occurred, without revealing the resulting structure.
- Potentially important for supply-chain trust and secure provisioning.

### 3) Hybrid roots of trust
- Strong practical direction: use **SUC-style structural uniqueness as a hardware-bound anchor**, then layer:
  - conventional keys
  - secure boot
  - authentication protocols
  - possibly PQ-compatible schemes

### 4) Direct empirical comparison with FPGA PUFs
- Especially valuable studies would compare NV-FPGA structural-identity approaches vs PUF baselines on:
  - stability/reliability
  - entropy quality
  - implementation overhead
  - side-channel and extraction resilience
  - lifecycle manageability

### 5) Portability and tooling studies
- Important adjacent question: how much of this class of technique can be generalized across **NV-FPGA families** without fragile dependence on proprietary bitstream internals.

## Current working view
- The strongest active thread is **NV-FPGA security through self-generated, persistent structural identity**.
- `1908.03898v1` is currently best treated as a **high-interest direction signal** rather than a fully validated solution, because the mechanism is compelling but the evidence seen so far leaves major protocol and attack-model questions open.
- Near-term priority should go to papers that clarify:
  1. realistic attacker model,
  2. enrollment/authentication flow,
  3. effective entropy measurement,
  4. resistance to bitstream extraction and structural recovery,
  5. deployment practicality across NV-FPGA platforms.
