---
name: paper-intake-and-normalize
description: Fetch, normalize, and deduplicate arXiv candidates for the current research profile. Use when Codex needs to collect recent papers, rerun a retrieval window, update metadata, or prepare a candidate pool for later problem-solution analysis.
---

# Workflow

1. Read `research-workspace/profile/interest-profile.md` and validate it first.
2. Run `python skills/paper-intake-and-normalize/scripts/run_intake.py --workspace research-workspace --profile research-workspace/profile/interest-profile.md`.
3. Inspect `research-workspace/papers/registry.jsonl` and the new per-paper `metadata.json` files.
4. Keep low-priority papers in the registry for auditability, but do not promote them to later report sections unless requested.
5. Summarize how many papers were high-match, adjacent, and low-priority.
