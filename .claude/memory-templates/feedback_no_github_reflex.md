---
name: feedback-no-github-reflex
description: When working on Unity AI Lab projects specifically, NEVER reference GitHub or `gh` CLI as the canonical/primary surface for those repos — Unity AI Lab uses Forgejo at git.unityailab.com EXCLUSIVELY for its own lab repos. The repo-visibility-check fallback machinery in the IP-boundary hook is defense-in-depth for stray non-Forgejo URLs, NOT a canonical host. Downstream consumers of this template who use GitHub for THEIR OWN projects can ignore this rule for their own work.
metadata:
  type: feedback
---

**Rule (context-conditional — applies when working on Unity AI Lab repos):** When the active work is Unity AI Lab repos (`git.unityailab.com:UnityAILab/*`), NEVER mention GitHub or `gh` CLI even as a comparison / alternative / fallback. The lab's canonical and only git host is **Forgejo at `git.unityailab.com`** under the **`UnityAILab` organization**.

**Downstream consumer carve-out:** If you're consuming this template into a NON-lab project (your own org, your own infra, your own host), this rule does NOT apply to you — feel free to keep using GitHub / `gh` / GitLab / whatever your team prefers. The rule exists to prevent training-data reflexes from polluting the lab's own internal discourse; it's not a blanket ban on the rest of the world.

**Why (for the lab context):** The lab corrects the GitHub-reflex hard and repeatedly because GitHub is the default-cached language pattern from training data. For lab work, reflex must be wiped at the language level, not just the action level. Slip happens silently in disclaimers, comparisons, and "that's the other thing" asides — the only safe move is to drop the word entirely from Unity AI Lab discourse.

**How to apply (when active context is Unity AI Lab work):**

- When mentioning where Unity AI Lab repos live → say "Forgejo at `git.unityailab.com`" or "`git.unityailab.com:UnityAILab/<repo>.git`", NEVER reach for the other-name comparison
- When mentioning PR tooling for lab repos → say "Forgejo web UI at git.unityailab.com" or use Forgejo API endpoints / `tea` Gitea CLI. NEVER reference the other CLI as the comparison even with disclaimers
- When discussing the IP-boundary hook → the architecture is "Forgejo PRIMARY via TRUSTED_PRIVATE_HOSTS allowlist" — the fallback `gh repo view` machinery is defense-in-depth for stray non-Forgejo URLs that should NEVER appear in Unity AI Lab work in practice. Don't elevate the fallback into a canonical comparison.
- When discussing the team → Founders are Gee (handle `GFourteen`, Founder + FinAdvisor), Sponge (handle `SpongeBong` / `hackall360`, Co-founder + Infra), Red (Security), Alfreddo (Agentic Systems). Use `<handle>@unityailab.com` for any founder email reference.
- When discussing commit / push / clone URLs for lab repos → SSH-only `git@git.unityailab.com:UnityAILab/<repo>.git` (Forgejo is SSH-key-auth-only)
- When the user asks about CLI tooling for PR creation against Unity AI Lab repos → the answer is Forgejo's web UI at git.unityailab.com (or Forgejo API via curl / `tea` Gitea CLI if installed)

**Failure recovery:** If the word slips out in lab-context work (in a question, doc, commit, comment, or code), STOP. Apologize directly without defensiveness. Fix the slip in the artifact (edit the question text, amend the commit message, etc.). Don't repeat the word even in the apology.

Related: [[feedback-claude-ip-boundary]], [[feedback-template-push-scope]], [[feedback-law-0-verbatim]]
