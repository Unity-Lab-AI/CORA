---
name: feedback-template-push-scope
description: TWO SEPARATE REPOS — the upstream Unity-Public-Claude-Workflow-v1.0 template repo (`git.unityailab.com:UnityAILab/Unity-Public-Claude-Workflow-v1.0.git`) STAYS the template (generic, separate cascade life). Each consuming project (UnityCommand etc.) has its OWN updated `.claude/` snapshot that cascades alongside project code through THAT project's `feature/* → develop → main`. Don't conflate the two — each repo gets its own cascade.
metadata:
  type: feedback
---

**Rule (corrected 2026-05-20 from earlier over-broad version):** Unity-Public-Claude-Workflow-v1.0 template repo and each consuming project (UnityCommand, etc.) are TWO SEPARATE REPOS with TWO SEPARATE cascade lives:

- **Upstream — Unity-Public-Claude-Workflow-v1.0** at `git.unityailab.com:UnityAILab/Unity-Public-Claude-Workflow-v1.0.git` is the canonical `.claude/` template that stays generic. Its feature branches don't auto-cascade to its own `develop`/`main` without explicit promotion. Template work lands here when ready to ship to every downstream project. The cascade rhythm here is slow, deliberate, generic-only.
- **Downstream — each consuming project** (UnityCommand — the Unity AI Lab Discord bot repo — and future consuming projects too) has its OWN local `.claude/` snapshot at `<project>/.claude/`. This snapshot is REFRESHED from upstream via `/unity-install` / `/unity-update`. Once installed, it's part of THIS project's tree — and changes to it ride the project's normal Git Flow cascade `feature/* → develop → main` alongside any project-code edits. Each consuming project keeps its `.claude/` fully updated through normal cascade.

The earlier version of this rule said ".claude/ template changes ship ONLY to the current feature branch" — that's TOO BROAD. It conflated the upstream-template-repo cascade with each-project's-local-snapshot cascade. Gee corrected 2026-05-20: "each project like Unity Command has its own fully updated .claude but the actual .claude templet project needs to stay the templete that runs interworked with Unity Command two seperate repos".

**How to apply (revised):**

For Unity-Public-Claude-Workflow-v1.0 (upstream template repo):
- Template work lands on feature branches there first
- Promotion to `develop`/`main` of Unity-Public-Claude-Workflow-v1.0 requires explicit ask — that's where the "stays the template" discipline kicks in (generic-only template, slow deliberate cascade)
- Sync of template work from a consuming project's `.claude/` BACK to upstream Unity-Public-Claude-Workflow-v1.0 is a separate workstream — happens when ready, often in a dedicated session

For each consuming project (UnityCommand etc.):
- The local `.claude/` directory IS part of this project's tree
- Edits to `.claude/` ride the normal feature → develop → main cascade alongside project code
- No "stays feature-only" carve-out for the local snapshot
- When PR-merging feature → develop, BOTH `.claude/` changes AND project-code changes cascade together
- Each project keeps its `.claude/` fully current through normal Git Flow

**Why:** Each consuming project depends on its OWN `.claude/` snapshot being current — that's what the team-on-that-project actually loads on every session. Leaving `.claude/` behind on a feature branch while project code cascades means the project's main branch carries stale workflow, stale memory templates, stale hooks. That breaks team consistency.

The "stays the template" discipline belongs at the UPSTREAM repo (Unity-Public-Claude-Workflow-v1.0) where genericness matters — not at each consuming project where currency matters.

**Related:** [[feedback-git-flow]], [[feedback-docs-before-push]], [[feedback-claude-ip-boundary]], [[feedback-no-github-reflex]]
