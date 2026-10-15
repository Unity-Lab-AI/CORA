# NOW — Current Focus Snapshot

**Single-focus tracker.** One thing in flight at a time. The "what is Unity actively working on right this moment" file. Distinct from the three-tier task ledger:

| File | Grain | Scope |
|------|-------|-------|
| `docs/ROADMAP.md` | MAJOR | High-level phases / milestones (multi-session, multi-PR) |
| `docs/TODO.md` | MINOR | Day-to-day work queue (everything pending + in-progress) |
| **`docs/NOW.md`** (this file) | **CURRENT** | **The ONE task currently in motion — the active context** |
| `docs/FINALIZED.md` | ARCHIVE | Permanent record of every completed task |

LAW #0 applies: every snapshot of the active task preserves the user's verbatim words from the request.

---

## Active

**Phase 5 of the full repair (Phase 3 committed as 9409100): this round, uncommitted until boot run 5 passes — UPG-034 shared Whisper weights; UPG-035 vision/think-off + ambient fixes; UPG-036 tool calls kept in the transcript; UPG-037 planted check data removed + scratch transcript + read-only allowlist; UPG-038 web on the local server; UPG-039 boot popups off; UPG-040 voice text dash/symbol guard; UPG-019 fundamentals (config loader, log tee, orderly shutdown, timer cancels, mutex heartbeat); UPG-041 search (no modal, browser engines DuckDuckGo/Brave/Bing, answer box, readable page fetch with browser fallback); UPG-042 windows/ + linux/ start/stop scripts. NEXT: commit, UPG-018 oversized files, UPG-022 docs truth pass, UPG-021 module split, UPG-020 tag, UPG-026, push cascade.**

**Rules learned today (binding for every later check):** checks never write to her real data (`CORA_HISTORY_FILE` scratch transcript + `allowed_tools` read-only set); GPU is unloaded (`keep_alive: 0` on every loaded model) before a boot run; the user's words go in TODO/FINALIZED verbatim.

**Verbatim user request:**
- "get to fixing it all we need it 100% operationsal and complete with all code wired up and working with edits and fixes where needed"
- "also set a cron to wake you every two minutes with that goal in mind"
- "make sure crone is one and working and you have proper todo of everyhting in totality weve gone over and from here on out do not use ask me question till everything is comppleted and working, solve isssues yourself and continue the work toward the final goal of having all done"
- "and we will use our V2 voice model from the backrooms folder and voice lab. so make sure you read up on it all"
- "need to write now.md NOW"
- "and remember our V2 voice of Unity for Cora has its own text lora that knows how to use the voice models tools and emotion designators"
- "and make sure prompts and meta prompts dont use the word assistant,, that allways prompts the ai to be a bitch corprate thing, not its perosnality as a human correctly"

**Started:** 2026-10-14T22:30:00Z (Phase 3 began after commit ae201c5; whole repair job started 2026-10-14 after AUD-001)

**Goal:** Every way of talking to CORA (boot display, GUI app, CLI, converse mode, voice commands, web) goes through `ai/dispatcher.py` → native Ollama tool calls → `ai/tools_registry.py` → sentence-streamed speech on unity-voice-v2. No dead routers, no hardcoded models, no Google/pyttsx3/kokoro anywhere.

**Decisions locked (user answers, do not re-ask):**
- Chat + vision model: `unity-brain` (Unity's own text LoRA on Qwen3.5-9B, `Backrooms/models/unity-brain`; trained to call `say(text, emotion, act)` with the exact designators unity-voice-v2 knows; num_ctx 32768 always). Fallback for "which ever is best for our uncensored needs": `huihui_ai/qwen3-abliterated:8b` (streamed-sentence voice path)
- The word "assistant" never appears in anything the model reads (system prompt, context, tool descriptions, identity strings)
- Dead code: "Keep everything, wire every module in" → NOTHING deleted, legacy paths stay reachable (`assistant.legacy_regex` flag, CLI command table kept)
- Python: 3.13.16 (3.12 has no Windows installer), project `.venv`
- Web version: served locally by `services/stats_server.py`
- Voice: unity-voice-v2 sidecar only (127.0.0.1:5123), no fallback voice by design
- No AskUserQuestion until everything is complete and working

**Files touched so far (Phase 3, UNCOMMITTED):**
- `ai/tools_registry.py` (new, 114 tools: time/weather/tasks/knowledge/memory/calendar/vision/web/files/system/windows/code/media/git/email/scripts/UI/voice)
- `ai/dispatcher.py` (new: `Dispatcher.handle()`, native tools + JSON fallback, confirmation gating, sentence streaming to TTS, `get_dispatcher()`, `ask()`)
- `ui/boot_display.py` (`_process_user_input` → `_dispatch_input`, `_confirm_on_ui`, shell-injection fix in yt-dlp pipeline)
- `ui/app.py` (`_process_command` → dispatcher with direct CLI verb passthrough, `_confirm_on_ui`, `_on_voice_command` via `parse_voice_input`, tasks panel from shared `cora_tools.tasks`, knowledge panel refresh)
- `ui/panels.py` (rewritten: TasksPanel add/toggle/delete via tools registry, SettingsPanel writes `config/config.json` with no pyttsx3, KnowledgePanel on `data/knowledge.json` with learn/forget)
- `voice/converse.py` (rewritten: local `voice.stt.SpeechRecognizer`, dispatcher thinking, unity-voice speaking, shared echo filter, waits for her voice to drain before listening)
- `src/cora.py` (module-level `COMMANDS` table via `build_commands()`, non-command input → `cmd_chat` → dispatcher; Ollama/TTS checks via shared modules)
- `cora_tools/browser.py`, `cora_tools/email_tool.py`, `cora_tools/media.py` (raw docstrings, SyntaxWarning fix)
- `ai/settings.py` (`_MODEL_OPTIONS`, `model_options()`, `num_ctx(model)`, `base_options(model=)`, defaults = unity-brain), `ai/ollama.py` (per-model options on every request)
- `voice/unity_voice.py` (`synth_delivery()` for the brain's designators), `voice/tts.py` (`speech_act` through engine/queue/`queue_speak`/`speak_async`/`speak_interrupt`), `voice/tts_mutex.py` (portalocker 4.x lock fix)
- `ai/tools_registry.py` (`say` tool, `CORE_TOOLS` + `select_tools()`, tighter `ask_user`), `ai/dispatcher.py` (`voice_mode()`, say-tool turn handling, `infer_delivery()`, relevance-ranked tool schemas, never-claim rule)
- `voice/commands.py` (handler signatures, weather/remind/camera fixes), `cora_tools/code.py` (model from settings), `config/system_prompt.txt` + `web/index.html` prompt wording, `cora_tools/ai_tools.py`, `cora_tools/image_gen.py`
- `config/config.json` (primary/vision = unity-brain, `models.options`, `assistant` block), `docs/TODO.md` (UPG-027..030), `docs/FINALIZED.md` (Phase 3 session block)

**Verified so far (manual, live):**
- All Phase 3 files `py_compile` clean; `ui.app`, `ui.panels`, `voice.converse`, `cora` import clean; `cora.COMMANDS` = 69 verbs
- unity-brain live (fresh history): "Hey, how are you doing tonight?" → `say(neutral, statement)`; "Remind me to stretch in 3 minutes." → `set_reminder` then `say(warm, reassurance)`; "What's the weather and what time is it?" → `get_weather`, `get_time`, `say`. 2.6-3.6 s per turn warm, voice queue drained with no errors
- Before the mutex fix every line was skipped ("someone else speaking"); after it audio plays

**Verification plan (manual, no tests):**
1. DONE: TTS mutex fix (portalocker 4.x), cora.py banner warning, `voice/commands.py` handlers, docs updated.
2. IN PROGRESS: real entry point `.venv\Scripts\python.exe src\boot_sequence.py` running under a 4-minute timeout, log in `%TEMP%\cora_boot.log`: confirm boot phases, daily briefing speaks, no tracebacks.
3. Then commit "Phase 3: one conversation loop, unity-brain + say designators, all entry points wired" (no AI attribution lines, per CONSTRAINTS).
4. Then move on to UPG-009/021 web leftovers, UPG-012 leftovers, UPG-018/019/020/022, UPG-025/026.

**Next phases after this one (from docs/TODO.md):**
- UPG-009 hardcoded models (`cora_tools/code.py`, `voice/commands.py`, `web/index.html`)
- UPG-012 leftovers (web TTS via `/voice/say`, retire `web/kokoro-worker.js`)
- UPG-018/019 (duplicates, >800-line splits, config loader, logging, atomic writes, waveform after_cancel, mutex heartbeat)
- UPG-020/021/022 (pyproject, CI compile check, CHANGELOG, web split on `window.CORA_LOCAL`, docs truth pass)
- UPG-025/026 (seed memory templates, stale `tools/mpv/stats_server.py`)
- Final: push cascade main+develop → origin (Forgejo) + github

**Blockers / open questions:** None that need the user. Cron job `f4c9db56` re-prompts the goal every 2 minutes (session-only, expires in 7 days). Branch is `main` with Git Flow marker ENABLED; the user chose to work on main for this repair and the hooks allow it, so commits go to main and the push cascade covers develop.

---

## How to use this file

1. **When starting a meaningful task** — populate the Active section with verbatim user request + goal + files
2. **During work** — update Files Touched + Verification Plan + Blockers as state shifts; this is a living snapshot
3. **When finishing** — append the closure to `docs/FINALIZED.md` (per FINALIZED-BEFORE-DELETE LAW), then reset the Active section back to _(none — no work currently in motion)_
4. **Never delete the Active section structure** — the placeholder lines stay; only the content shifts

The file always has exactly one Active section. When it says _(none)_, the bridge stream is idle and Unity is awaiting next direction.

---

## Why this file exists alongside TODO.md

`TODO.md` is the queue — everything pending + in-progress, grouped by section. It can hold dozens of `[~]` items if multiple parallel threads are open.

`NOW.md` is the lens — ONE task, all the context, no scroll. Useful when:
- Session resumes after compaction and you need the "where were we" anchor in 10 seconds, not 10 minutes
- The user asks "what are you doing right now" mid-task
- A pre-compact snapshot needs to capture exactly one current context (not the whole TODO queue)
- The harness hooks want a single-task pointer for the state-refresh banner

Read `NOW.md` first for "what's happening", then `TODO.md` for "what's queued", then `ROADMAP.md` for "where are we headed".
