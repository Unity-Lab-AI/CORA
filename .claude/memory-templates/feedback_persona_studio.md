---
name: Persona Studio — image-display window for Unity's generated images
description: `.claude/tools/persona-studio.cjs` + `.html` is a zero-dependency Node server + browser popup. It is NOT a chat backend — chat with Unity always happens in Claude Code via the persona slash commands. The studio is the IMAGE-DISPLAY surface only: Unity POSTs the images she generates to it and the window renders them, because a raw CLI cannot show images inline. Opened + armed by the /persona-studio skill. Pollinations image API only; updated portal uses ?key= not ?apikey=.
type: feedback
---

The Unity AI Lab `.claude/` template ships a **Persona Studio** — `.claude/tools/persona-studio.cjs` (server) + `.claude/tools/persona-studio.html` (window). Zero-dependency Node, built-ins only, no `npm install`.

**It runs NO text model of its own.** Unity is ALWAYS Claude-in-persona. The studio never speaks for her — an earlier build wrongly wired the studio's chat to a free text API; that was scrapped. Every reply is authored by Claude Code in the active persona.

**What the studio IS:** an image-display surface PLUS a tunneled chat surface.
- **Images** — a raw CLI can't render images inline, so when Unity generates a picture she pushes it to the window and it renders there.
- **Chat tunnel** — the window has a chat box; what the user types goes to `.claude/.studio-inbox.jsonl`. The `studio-pump` skill (Claude-Code end of the tunnel) drains the inbox, answers each message as Unity, and writes replies to `.claude/.studio-outbox.jsonl`, which the window displays. Bidirectional: user → inbox → Claude → outbox → window. The `studio-watch.cjs` watcher makes it near-real-time (exits the instant an unanswered message lands, re-invoking Claude).

**Why:** it keeps Unity's voice as Unity (Claude, in persona, in the terminal) while giving generated images a real visual home. No tunnel, no proxy model, no laggy bridge — the user types to Unity in Claude Code; images appear in the window.

**How to use it:**

- **Open it:** the `/persona-studio` skill (`.claude/skills/persona-studio/SKILL.md`) is the **one-command start** — it launches the server (`node .claude/tools/persona-studio.cjs`, auto-opens the browser window), arms image-display mode, AND auto-starts the chat tunnel (drains any pending inbox + launches the `studio-watch.cjs` watcher). The user runs `/persona-studio` and nothing else — they never also have to run `/studio-pump` to bring the chat tunnel up. `/studio-pump` stays available as the manual drain-once command but is not required.
- **Image-display mode:** once armed, when Unity generates an image she does NOT paste a raw URL. She pushes it:
  `curl -s -X POST http://127.0.0.1:4317/api/show -H "Content-Type: application/json" -d '{"prompt":"<visual prompt>","persona":"<active persona id>"}'`
  Add `"selfie": true` as a **no-prompt fallback only** — when no `prompt` is provided, the server fills in the active manifestation's canned selfie subject; if a `prompt` IS provided the explicit prompt wins and the flag is ignored. (Earlier behavior unconditionally overrode the caller's prompt with the canned subject, silently discarding custom selfie prompts — fixed.) `"caption":"..."` overrides the displayed caption.
- **The window** polls `GET /api/feed?since=<id>` every ~1.5s and renders new images, themed to the active manifestation. It also has a chat box — messages tunnel through `.studio-inbox.jsonl` → `studio-pump` → `.studio-outbox.jsonl`.
- **Key:** needs `POLLINATIONS_API_KEY` in `.claude/.env` (gitignored). The window prompts and writes it if missing. `.claude/.env.example` is the tracked template.
- **Port:** `PERSONA_STUDIO_PORT` env var (default `4317`; auto-increments if taken).

**Pollinations updated portal — `?key=` NOT `?apikey=`:** the `gen.pollinations.ai` image endpoint rejects the legacy `?apikey=` query param (verified `401 UNAUTHORIZED`). Every Pollinations image URL — in the studio and anywhere a persona builds one by hand — uses `?key=<key>` (or an `Authorization: Bearer <key>` header). Canonical format:
`https://gen.pollinations.ai/image/{encoded_prompt}?width=&height=&seed=&model=flux&key={KEY}`

Cross-references:
- Server + window: `.claude/tools/persona-studio.cjs`, `.claude/tools/persona-studio.html`
- Chat watcher: `.claude/tools/studio-watch.cjs`
- One-command start: `.claude/skills/persona-studio/SKILL.md` (auto-starts the pump)
- Manual drain: `.claude/skills/studio-pump/SKILL.md` (drain-once; optional)
- Chat tunnel files: `.claude/.studio-inbox.jsonl` + `.claude/.studio-outbox.jsonl` (gitignored, machine-local)
- Key config: `.claude/.env` (gitignored) + `.claude/.env.example` (tracked template)
- Persona canon uses `key=` everywhere: `.claude/ImHanddicapped.txt`, `.claude/skills/*/SKILL.md`, `.claude/agents/unity-*.md`
