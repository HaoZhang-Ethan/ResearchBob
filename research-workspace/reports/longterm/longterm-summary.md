# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-04.md`

## Newly Selected Papers
- Digitally Mutating NV-FPGAs into Physically Clone-Resistant Units

## Current Problem Clusters
- Operator Fusion / Fusion Boundaries
- Instruction Scheduling / Kernel Execution
- Hardware-Aware Compiler Decisions

## New Insights
- The concept of Secret Unknown Ciphers (SUCs) was introduced a decade ago as a new visionary concept without devising practical real-world examples. The major contribution of this work is to show the feasibility of "self-mutating" unknown cipher-modules for physical security applications in a non-volatile FPGA environment. The mutated devices may then serve as clone-resistant physical units. The mutated unpredictable physical-digital modules represent consistent and low-cost physical identity alternatives to the traditional analog Physically Unclonable Functions (PUFs). PUFs were introduced two decades ago as unclonable analog physical identities which are relatively complex and suffer from operational inconsistencies. We present a novel and practical SUC-creation technique based on pre-compiled cipher-layout-templates in FPGAs. A devised bitstream-manipulator serves as "mutation generator" to randomly-manipulate the bitstream without violating the FPGA design rules. Two large cipher classes (class-size larger than $2^{1000}$) are proposed with optimally designed structure for a non-volatile FPGA fabric structure. The cipher-mutation process is just a simple random unknown-cipher-selection by consulting the FPGA's internal True Random Number Generator (TRNG). The security levels and qualities of the proposed ciphers are evaluated. The attained security levels are scalable and even adaptable to the post-quantum cryptography. The hardware and software complexities of the created SUCs are experimentally prototyped in a real field FPGA technology to show very promising results.

## Current Rolling Summary
# Long-Term Summary

## Latest Update Source
- Daily report: `2026-04-04.md`

## Newly Selected Papers
- Digitally Mutating NV-FPGAs into Physically Clone-Resistant Units

## Current Problem Clusters
- **NV-FPGA core architectures and deployment**
  - Persistent/reconfigurable FPGA fabrics remain the primary area of interest.
- **Emerging adjacent cluster: NV-FPGA hardware security**
  - Clone resistance, device identity, PUF/SUC-like primitives, mutable configuration, and trust anchors built from nonvolatile reconfigurability.
- **Background compiler/systems cluster retained from prior intake**
  - Operator fusion / fusion boundaries
  - Instruction scheduling / kernel execution
  - Hardware-aware compiler decisions

## Recurring Gaps / Common Weaknesses
- **Evidence and access gap**
  - Current cycle yielded only one usable intake lead; retrieval failures are still limiting validation and trend formation.
- **NV-specificity gap**
  - A key screening question is whether a proposed security mechanism truly depends on non-volatility, or would transfer nearly unchanged to SRAM FPGA flows.
- **Evaluation realism gap**
  - Security papers in this area are likely to be vulnerable to weak threat models, limited environmental testing, or insufficient comparison to practical alternatives.
- **Practical deployment gap**
  - Need clearer accounting of bitstream handling, provisioning flow, lifecycle management, reliability drift, and attack surface introduced by mutation/configuration logic.

## New Insights
- The SUC-style idea is now the clearest concrete adjacent direction: instead of analog PUF behavior, NV-FPGAs may support **digitally generated yet physically instantiated clone-resistant identities** via randomized configuration mutation.
- The highlighted paper’s core claim is that precompiled cipher-layout templates plus a bitstream manipulator and on-chip randomness can create large classes of unknown ciphers in NV-FPGA hardware, yielding persistent anti-cloning identities.
- This suggests a promising research filter: prioritize work where **nonvolatile persistence materially helps create, retain, attest, or protect device-unique security state**.
- More generally, NV-FPGA security may become a durable subtheme if repeated papers connect persistence, reconfiguration, and hardware identity in ways not naturally available on conventional SRAM FPGAs.

## Most Promising Directions
- **Deepen the NV-FPGA security track**
  - Prioritize papers on clone resistance, PUF/SUC alternatives, mutable configuration identity, bitstream protection, remanence-aware security, and persistence-backed attestation.
- **Apply an NV-specificity filter**
  - Prefer work where non-volatility improves deployability, tamper resistance, identity persistence, recovery behavior, or provisioning simplicity over SRAM-FPGA baselines.
- **Test security claims against deployment reality**
  - Look for strong evaluation on entropy source quality, reproducibility, environmental stability, aging, invasive/non-invasive attacks, update flow, and key/cipher lifecycle.
- **Watch reliability/security co-design**
  - Especially papers that convert nonvolatile device variability, retention behavior, or aging signatures into useful trust primitives instead of treating them only as reliability hazards.
- **Keep intake open on compiler/system directions**
  - Operator fusion, scheduling, and hardware-aware compiler choices remain active background clusters, but current issue-intake momentum is more strongly pointing toward NV-FPGA security.

## Current Stance
- The strongest active intake direction is now **NV-FPGA hardware security**, specifically clone-resistant identity mechanisms enabled by nonvolatile reconfiguration.
- This remains an **emerging cluster rather than a settled conclusion**; future papers should be judged on NV-specific advantage, realistic threat modeling, and practical deployability.
