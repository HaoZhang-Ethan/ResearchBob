---
name: research-interest-profile
description: Maintain and revise a persistent single-user research interest profile for arXiv scouting. Use when Codex should interview the user about what topics to watch, what adjacent areas to keep in view, what to exclude, or how current research priorities have shifted.
---

# Workflow

1. Read `research-workspace/profile/interest-profile.md` if it exists.
2. Ask one question at a time to refine core interests, soft boundaries, exclusions, current-phase bias, evaluation heuristics, and open questions.
3. Keep the profile selective but not brittle. Preserve adjacent directions when the user wants breadth.
4. Consult `references/profile-format.md` for formatting expectations before editing the template.
5. Update `research-workspace/profile/interest-profile.md` using the template in `assets/interest-profile-template.md`.
6. Run `python skills/research-interest-profile/scripts/validate_profile.py research-workspace/profile/interest-profile.md`.
7. Summarize what changed in 3 to 5 bullets.
