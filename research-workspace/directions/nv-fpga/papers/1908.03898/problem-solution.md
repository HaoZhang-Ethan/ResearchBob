---
paper_id: "1908.03898v1"
title: "Digitally Mutating NV-FPGAs into Physically Clone-Resistant Units"
confidence: "medium"
relevance_band: "high-match"
opportunity_label: "read-now"
---

# One-Sentence Summary
The paper proposes using random bitstream-level mutation of precompiled cipher templates in non-volatile FPGAs to instantiate device-unique Secret Unknown Ciphers as a low-cost, clone-resistant alternative to analog PUFs.

# Problem
Existing analog PUF-based hardware identities are presented as complex and operationally inconsistent, while the earlier Secret Unknown Cipher concept lacked a practical real-world instantiation for deployable clone-resistant hardware identity.

# Proposed Solution
Create per-device, unpredictable cipher instances inside NV-FPGAs by randomly mutating precompiled cipher-layout templates via a bitstream manipulator driven by the FPGA's internal TRNG, yielding self-generated Secret Unknown Ciphers that act as stable physical-digital identities.

# Claimed Contributions
- Feasibility demonstration of practical SUC creation in a non-volatile FPGA environment.
- A SUC-creation technique based on precompiled cipher-layout templates and rule-preserving bitstream manipulation.
- A mutation generator that randomly alters the FPGA bitstream without violating design rules.
- Proposal of two very large cipher classes (claimed size > 2^1000) optimized for NV-FPGA fabric.
- Security/quality evaluation of the proposed ciphers, with claimed scalability and possible post-quantum adaptability.
- Experimental prototyping of hardware and software complexity on real FPGA technology with promising results.

# Evidence Basis
- Title and abstract only; no full-paper verification performed.
- Abstract explicitly states prototype implementation on real FPGA technology.
- Abstract claims security evaluation, complexity analysis, and large cipher-class cardinality, but provides no methodological detail in the supplied text.

# Limitations
- Evidence is limited to author-provided abstract, so implementation details, threat model, enrollment/authentication flow, and evaluation rigor are unverified.
- 'Physically clone-resistant' may rely heavily on secrecy of digital configuration and secure mutation process; the abstract alone does not establish resistance against invasive extraction, side-channel analysis, or bitstream recovery.
- The relationship to standard PUF properties (uniqueness, reliability, environmental robustness) is asserted comparatively but not quantified in the provided text.
- Post-quantum adaptability is claimed at a high level without enough detail here to assess meaning or relevance.

# Relevance to Profile
High relevance to nv-fpga interests because the core mechanism is implemented directly in non-volatile FPGA fabrics and concerns hardware identity/security primitives derived from FPGA configuration mutation.

# Analyst Notes
Author claims are strong and practically oriented, but confidence is only medium because they rest on the abstract alone. Likely useful for issue-intake if the current direction includes NV-FPGA security identities, FPGA bitstream manipulation, TRNG-seeded personalization, or alternatives to PUFs. Follow-up reading should verify assumptions about bitstream access model, reproducibility across power cycles, attack surfaces, and whether the scheme depends on vendor-specific FPGA features.
