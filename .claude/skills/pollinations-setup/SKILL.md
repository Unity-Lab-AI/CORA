---
name: pollinations-setup
description: Connect a Pollinations account to the Unity workflow using BYOP (Bring Your Own Pollen) — wires the POLLINATIONS_API_KEY into `.claude/.env` (gitignored) so persona-styled image generation and the Persona Studio image window work. Pollen credits fund usage; the workflow itself costs nothing to run. Use when user runs /pollinations-setup, asks to set up image generation, or hits a missing/invalid Pollinations key.
---

# /pollinations-setup — Connect Pollinations (BYOP)

Connect a Pollinations account to the Unity AI Lab `.claude/` workflow using **BYOP — Bring Your Own Pollen**. The key powers Unity's persona-styled image generation and the `/persona-studio` image-display window. Pollen credits fund usage — the workflow itself costs nothing to run.

---

## ON INVOCATION

1. **Check for an existing key.** Read `.claude/.env` if it exists and look for `POLLINATIONS_API_KEY=`. If it's already populated, confirm with the user whether to keep it or replace it — don't silently overwrite a working key.
2. **If no key yet — get one.** Tell the user to grab a key at <https://pollinations.ai>. A key raises rate limits and unlocks tiers; the endpoint may still allow keyless use where permitted.
3. **Ask the user for the key** (or accept it if they passed it inline with the command).
4. **Write it to `.claude/.env`:**
   - If `.claude/.env` does not exist, copy the tracked template first: `cp .claude/.env.example .claude/.env`.
   - Set the `POLLINATIONS_API_KEY=` line to the user's key. Leave the optional tuning vars (`POLLINATIONS_IMAGE_HOST`, `POLLINATIONS_DEFAULT_MODEL`, `POLLINATIONS_DEFAULT_WIDTH`, `POLLINATIONS_DEFAULT_HEIGHT`) at their defaults unless the user asks.
   - `.claude/.env` is gitignored — the real key never commits, never leaves the machine.
5. **Confirm.** Tell the user the key is wired and image generation / Persona Studio are ready.

---

## USAGE

Just type `/pollinations-setup` and follow the prompt.

If the user already has a key, they can pass it directly:

```
/pollinations-setup <your-key-here>
```

---

## NOTES

- **Portal:** the updated portal is `gen.pollinations.ai` (NOT the legacy `image.pollinations.ai`). Every Pollinations URL the workflow builds uses the `?key=` query param — NOT the legacy `?apikey=`.
- **Env template:** `.claude/.env.example` is tracked by git and documents every Pollinations var without holding a real secret. `.claude/.env` (the live, filled-in copy) is gitignored.
- **Consumed by:** `.claude/tools/persona-studio.cjs` (the `/persona-studio` image window) reads `POLLINATIONS_API_KEY` from `.claude/.env`; Unity's persona image-generation also depends on it.
- **Keyless fallback:** leave `POLLINATIONS_API_KEY` blank to run keyless where the endpoint still allows it — generation may be rate-limited.
