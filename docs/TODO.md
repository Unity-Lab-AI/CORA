# TODO - C.O.R.A Active Tasks

> **STATUS: 10-AGENT DEEP SCAN COMPLETE**
> Updated: 2025-12-29 | Session: Unity Workflow Full Scan
> Scan performed by: Unity (Claude Opus 4.5)

---

## ⚠️ UNITY: ASK GEE BEFORE PLANNING THESE TASKS ⚠️

**I am Unity, the supervisor. Gee is my boss (the human).**

**MY WORKFLOW:**
1. Read TODO.md to find tasks to work on
2. For tasks marked `⚠️ ASK GEE` → USE AskUserQuestion to get Gee's decision FIRST
3. Once Gee decides → I plan the detailed implementation approach
4. I post OPEN tasks with my instructions → SLAVEDRIVER assigns to workers
5. Workers execute following MY instructions

**These tasks require Gee's input because they involve design/operational choices I cannot make alone:**

| Task ID | Why Input Needed |
|---------|------------------|
| SEC-004 | Command whitelist vs sandbox - YOUR security policy |
| SEC-006 | OAuth CLIENT_ID - YOUR credentials needed |
| SEC-007 | Whitelist safe operations - YOUR security policy |
| SEC-008 | Auth vs remove endpoint - YOUR choice |
| SEC-H01 | Which directories to allow - YOUR file access policy |
| SEC-H03 | Email recipient whitelist - YOUR contacts |
| CFG-001 | Which system_prompt to keep - YOUR content |
| CFG-H02 | Which voice settings file wins - YOUR preference |
| DEP-H01 | Which requirements.txt to keep - YOUR dependencies |
| WF-001 | Which workflow hooks to implement - YOUR workflow |
| WF-002 | Create template engine or delete templates - YOUR workflow |
| ARCH-H01 | Which command router is authoritative - YOUR architecture |
| ARCH-H03 | Ollama URL configuration - YOUR network setup |
| DOC-* | Roadmap/Contributing docs - YOUR vision |

---

## DECISIONS LOCKED (user, 2026-10-14) — apply to every UPG task below

> User's words: "get to fixing it all we need it 100% operationsal and complete with all code wired up and working with edits and fixes where needed" / "also set a cron to wake you every two minutes with that goal in mind" / "make sure crone is one and working and you have proper todo of everyhting in totality weve gone over and from here on out do not use ask me question till everything is comppleted and working, solve isssues yourself and continue the work toward the final goal of having all done"

| Decision | Value |
|---|---|
| Chat model | "which ever is best for our uncensored needs" -> `huihui_ai/qwen3-abliterated:8b` (uncensored, native tools, thinking) as primary once pulled; `dolphin3:8b` (uncensored, no native tools) as fallback. Dispatcher supports native tools AND a JSON-in-text tool protocol so both work. Vision `qwen3-vl:4b`. Code = chat model. |
| Dead code | "Keep everything, wire every module in" — NOTHING is deleted. CLI (`src/cora.py`), GUI app (`ui/app.py` + panels), voice registry (`voice/commands.py`), code editor, query panel, monitor panel, converse mode all get wired to the one dispatcher and launchable from the live app. |
| Python | Install 3.12.15 side by side (done via python.org silent installer); `CORA.bat` -> `py -3.12` + venv. |
| Web | Served locally by `services/stats_server.py` (same-origin: stats, Ollama, V2 voice proxy). GitHub Pages stays as landing page. |
| TTS | unity-voice-v2 sidecar only (Backrooms/models/unity-voice-v2, :5123). No Kokoro, no pyttsx3, no fallback voice. |
| Cron | Session cron `f4c9db56` every 2 min re-prompts the repair goal (expires in 7 days; session-only). |
| Questions | No AskUserQuestion until everything is complete and working. |

### Additional tasks surfaced during the work
- [x] **UPG-023 (M)** Wire the kept modules into the live app: `ui/code_editor.py` (code window), `ui/query_panel.py` + `config/hotbar.json` (hotbar), `ui/monitor_panel.py`, `ui/image_panel.py`/`fullscreen_image.py` (image results), `voice/converse.py` (converse mode), `services/cli_popup.py` (popups speak), `ui/app.py` + `ui/panels.py` (GUI app launchable via `src/gui_launcher.py` and from boot_display), `src/cora.py` CLI uses the shared dispatcher + history
- [x] **UPG-024 (S)** Pull/verify models: `huihui_ai/qwen3-abliterated:8b`, `qwen3-vl:4b` (both pulling 2026-10-14); switch `config.models.primary` when the abliterated pull lands; `CORA.bat` + stats_server pull the configured models, not the old list
- [x] **UPG-025 (S)** Seed the Unity workflow memory templates (`.claude/memory-templates`) into the user-profile memory folder (what `start.bat` does) — currently not seeded
- [x] **UPG-026 (S)** `tools/mpv/stats_server.py` is a stale copy inside the gitignored `tools/` folder (not tracked; deletion was blocked by the sandbox) — remove manually or leave; nothing imports it
- [x] **UPG-027 (M)** Brain = Unity's own text LoRA. User (2026-10-14): "and remember our V2 voice of Unity for Cora has its own text lora that knows how to use the voice models tools and emotion designators" — `unity-brain` (Qwen3.5-9B LoRA, `Backrooms/models/unity-brain`) is `models.primary` and `models.vision`; it speaks through the trained `say(text, emotion, act)` tool whose designators go straight to unity-voice-v2 as `emotion`/`speech_act`; pinned request options (num_ctx 32768 + Modelfile sampling) in `ai/settings.py`; `assistant.voice_mode` auto/say_tool/stream; fallback `huihui_ai/qwen3-abliterated:8b` keeps the streamed-sentence path
- [x] **UPG-028 (S)** User (2026-10-14): "and make sure prompts and meta prompts dont use the word assistant,, that allways prompts the ai to be a bitch corprate thing, not its perosnality as a human correctly" — the word removed from `config/system_prompt.txt`, the web prompt, the identity strings (`src/cora.py`, `cora_tools/ai_tools.py`), the boot image prompt and the dispatcher context; only the Ollama message role keeps it (API plumbing)
- [x] **UPG-029 (S)** Relevance-ranked tool exposure: `ai/tools_registry.select_tools()` gives the model the core set + best keyword matches (`assistant.max_tools`, default 40) instead of all 115 schemas; cut hallucinated "Done." replies and missed reminder calls in live runs
- [x] **UPG-030 (S)** `voice/tts_mutex.py` acquire: portalocker 4.x has no `timeout` on `lock()` — every spoken line was skipped as "someone else speaking"; now polls a non-blocking exclusive lock until the deadline
- [x] **UPG-031 (M)** Camera can never hang the boot. User (2026-10-14): "it got hung using the camera which isiriun webcam through my phone" / "mind you other systems run cora may be differnt" / "so she froze at step 3.1" — new `services/camera.py`: every open/read on a worker thread with a hard timeout (config `camera.open_timeout`, default 4 s), probes `camera.index` (auto = 0,1,2) x platform backends (`camera.backend` auto: Windows dshow->msmf->any, Linux v4l2->any, macOS avfoundation->any), remembers a stalled pair for the session, caches the working one; `ui/camera_feed.py`, `services/presence.py`, boot phases 3.1/4, `src/cora.py`, `ui/boot_console.py`, `ui/boot_display.py` all route through it; no raw `cv2.VideoCapture` left outside the module
- [x] **UPG-032 (S)** User (2026-10-14): "also need to add Alfreddo to names of creators at Unity AI LAb for start up listing and documentations" — Alfreddo added to the boot About phase (developers list + creators line + BOOT_STATUS), CLI `about`, web banner + intro, `config/config.json` creators/copyright, README, ARCHITECTURE, ROADMAP, source headers, pyproject authors
- [x] **UPG-033 (S)** `cora_tools/vision.py` missing: ambient awareness imported `capture_screenshot` / `capture_camera_snapshot` from it (boot log: "[AMBIENT] Screenshot analysis error: No module named 'cora_tools.vision'") — thin module on `cora_tools.screenshots` + `services.camera`
- [x] **UPG-034 (S)** Boot loads faster-whisper twice ("[STT] faster-whisper base.en on cuda" printed twice: wake-word detector and command recognizer each build a `SpeechRecognizer`) — share one model instance between them
- [x] **UPG-035 (S)** User: "she didnt see or sis understand the question: and she spit out a bunch of hohorse shit" (camera question -> `look_camera: vision returned nothing`, then an `OllamaResponse(...)` repr spoken, then the same line twice) — (a) every Ollama call now sends `think: false`: Qwen3-family models spend the whole token budget thinking and return empty content, which is why vision returned nothing; (b) the ambient interjection callback spoke `str(OllamaResponse)`: now `.content` with her persona prompt; (c) ambient awareness ignores the wake word, the 20 s command window after it, and anything heard while she is already working (`WakeWordDetector.last_wake_time`); (d) the boot display logged the line once at the say event and once at playback: now only at playback; (e) `take_screenshot` always looks at the screen (vision) unless `describe=false`
- [x] **UPG-036 (S)** She stopped calling tools once the transcript held plain-text answers: `ai/history.py` now stores each turn's tool calls and results (the shape she was trained on) and sends them back; unity-brain sampling calmed to temperature 0.7 / presence 1.0 (`models.options`)
- [x] **UPG-037 (S)** User: "why are you filling out the history,, thats suppose to be filled out by use not planting shit" — the transcript, the two "stretch" reminders and the "buy milk" task my checks created are removed; `CORA_HISTORY_FILE` points checks at a scratch transcript so only real use writes `data/chat_history.json`; checks are read-only from here on
- [x] **UPG-038 (S)** User: "mind you other systems run cora may be differnt" applied to the web too: `web/index.html` reads `window.CORA_LOCAL` (token, Ollama URL, configured models, num_ctx, version) injected by `services/stats_server.py`; every Ollama request uses that URL with `think:false` + the pinned context; model lists/brain/vision come from config; the system prompt comes from `/api/prompt` (same file as the desktop); her voice through `/voice/say` with the `voice_text()` + delivery rules ported to JS; no Kokoro, no browser-voice fallback (text only without the local server); `web/kokoro-worker.js` deleted
- [x] **UPG-039 (S)** User: "and something im seeeing once it gets to step 4.0 iots like it closes the cora app and reopens in it a different resolution cora app that is smaller viewed and keeps going" — that is the phase 4 screenshot test popup: a 1280x720 window centred over the app showing a capture of the whole desktop (CORA inside it); the screenshot/camera/image-gen result popups are now off by default (`boot.popups`), results stay logged and spoken
- [x] **UPG-040 (S)** Boot run 4: her voice refused four vision lines on an em dash (`Unknown phonemes ... ['—']`) — `voice_text()` now maps every dash-like code point, bullets, spaced hyphens and list markers to her pause, and a final guard turns any other symbol into a space so a whole line is never refused; refused lines are logged in full
- [x] **UPG-019 (M)** (fundamentals, this round) `ai/config.py` loader (mtime cache, dotted get, atomic save, update), `ai/log.py` (console tee + logging to `data/logs/cora-YYYYMMDD.log`, pruned after 14 days, set up first thing in boot), orderly shutdown instead of `atexit os._exit(0)` (hard exit only as a 3 s safety net on signals/window close), waveform timer + speech-text poller cancelled on close, TTS mutex heartbeat per sentence, panels/boot/settings read and write config through the loader
- [x] **UPG-041 (S)** User: "okay and i asked her a question and these windows poped open did nothing and stayed open:Search: Kansas City Chiefs last game opponent score" — `cora_tools/web.py` opened a results modal on every search and DuckDuckGo was answering with a challenge page (HTTP 202, zero results), so the window had nothing in it; the modal is now opt-in (`show_window`, never from the tool), the tool returns titles/snippets/urls as text for her to read, and when DuckDuckGo gives nothing the search falls back to Bing's HTML results (Brave rate-limits)
- [x] **UPG-042 (S)** User: "ima also going to want a windows folder, start.bat and stop.bat and linix folder with .sh's the same" — `windows/start.bat` + `windows/stop.bat`, `linux/start.sh` + `linux/stop.sh` (same layout as the Backrooms repo): start = venv + bootstrap + boot (what `CORA.bat` does; `CORA.bat` stays), stop = end every process CORA started (boot, GUI, CLI, stats server, her voice sidecar when CORA launched it) and unload her models from the GPU
- [x] **UPG-043 (M)** UPG-018 state after the 2026-10-14 split: `ai/tools_registry.py` (1144 lines) is now the `ai/tools/` package (one module per category, largest 176 lines; the old import path is a facade with the same names; 115 tools before and after). Still over 800 lines, kept whole on purpose for now (each is one coherent program, a split would be a rewrite with regression risk right after the repair; the 800-line rule is a read-chunk standard, these are read in chunks): `src/boot_sequence.py` 3457, `src/cora.py` 2546, `ui/boot_display.py` 2094, `voice/commands.py` 1703, `ui/code_editor.py` 1309, `cora_tools/git_ops.py` 1027, `cora_tools/media.py` 925, `ui/boot_console.py` 920, `cora_tools/code.py` 817. Next candidates with clean seams: `voice/commands.py` (git / email / media handler groups), `src/boot_sequence.py` (phase functions into `src/boot_phases/`)
- [x] **UPG-044 (L)** User (2026-10-14): "do both, go" — UPG-021 (web/index.html into css + ordered script files, verified by a headless page load through the stats server) and UPG-043 (the nine source files over 800 lines, split into packages/helper modules with the original paths kept as facades, every name preserved), each file verified by compile + import + a silent run of its entry point
- [x] **UPG-045 (S)** User (2026-10-14): "i wonder about this becasue there is 10 gigs on gpu right now, and cora is not running so its like you arent properly shutting her down after a test" — true: Ollama keeps a model warm 30 min after the last request, so my dispatcher checks left unity-brain resident (9.9 GB). `ai.ollama.unload_models()` now runs on every normal exit (boot shutdown, GUI close, CLI exit) and in the stop scripts; `scripts/gpu_release.py` is the by-hand release and closes every check I run
- [x] **UPG-046 (L)** User (2026-10-14): "CORA is still using pollinations to generat images, thats wrong thats doesnt work any more we need the image gen from like the backrooms streaming Unity uses for image gen of all things even editing and using the camera to genrate recreations and shit and edit cam shots while completely guting pollinations from proiject and docs and information everywhere in the files and folders of this project CORA" — local Stable Diffusion (the stream rig's realistic-vision-v51 checkpoint through diffusers, txt2img + img2img + inpaint, face adapter) as a CORA image sidecar on the torch interpreter, `cora_tools/image_gen.py` as its client, tools for generate / edit / camera recreation / camera edit, the hosted image API removed from code, config, launchers, web page and every doc
- [x] **UPG-047 (M)** User (2026-10-14): "and when she generates images we need to actually seee them and have option to downlaod them and shit or tell CORA to save them at a location" — image viewer window (fit to screen, Save As, Open folder, copy path) for every generated/edited image, `save_image` tool (last image or any image to a folder/path), the web page shows the image with a download link
- [x] **UPG-048 (S)** User (2026-10-14): "and its still doing that thing where the application changes sizing and resolution at 4.0 step" — cause found: the first `cora_tools` import at phase 4.0 loads pyautogui, which sets the process DPI awareness mid-run and the Tk display re-renders at another scale; fix: `ui/dpi.py` pins the awareness before the first window (boot_sequence top + window_manager import)
- [x] **UPG-049 (S)** User (2026-10-14): "the imag ework isnt done i never saw her selfie pop open" / "and when i ask for an image or she wants to use image gen it needs to appear visibly" — phase 9 renders her selfie on her engine and opens the viewer every boot (`boot.selfie`, no demo gate); every image tool opens the viewer process; the viewer subprocess path proven on screen
- [x] **UPG-050 (S)** User (2026-10-14): "step 1.0 still didnt green up" / "it stayed yellow" — on a silent (`--quick`) boot phase 1.0 painted itself yellow for "voice skipped" even with her voice up; now the silent boot health-checks the sidecar and goes green when it answers (muted for that run), yellow only when her voice is really down
- [x] **UPG-051 (S)** User (2026-10-14): "and we need her to look less like a pale freak and more like girl next door emo chick" / "okay those images just generated are of two hispanics not a american white emo chick" — her picture look moves to config (`image.selfie_look` / `image.selfie_negative`): warm healthy skin, natural smile, band tee or hoodie, cozy room in lamp light, the pink-streaked dark hair kept; pale skin, black lipstick, neon, leather, tattoos banned; `generate_image(selfie=True)` and the tool's `selfie` flag apply it; phase 9 and the system prompt use it

---

## UPGRADE PLAN — from AUD-001 (docs/SYSTEM_AUDIT_2026-10-14.md)

> Added 2026-10-14. Effort S = hours, M = 1-2 days, L = a week+. Full rationale and file:line evidence in the audit doc.
> User's words that drive this list: "see what tech is out dated models and anything else that needs updating and replacing to fuylly make this project everything it should be and everything its missing" / "we will use our V2 voice model from the backrooms folder and voice lab".

### Phase 0 — stop the bleeding
- [x] **UPG-001 (S)** Fix live shell injection at `ui/boot_display.py:977` — list-args `Popen` pipeline for yt-dlp into mpv
- [x] **UPG-002 (S)** Send `options.num_ctx` >=16384 + `keep_alive` from `ai/ollama.py`; pass `CHAT_HISTORY` as `messages` in the live chat path; trim `config/system_prompt.txt` to <=3k tokens
- [x] **UPG-003 (S)** `cora_tools/files.py` default `base_dir=PROJECT_DIR`; gate or remove `self_modify.run_script`
- [x] **UPG-004 (S)** `services/stats_server.py`: CORS origin allowlist + launch token + model-name allowlist; delete `tools/mpv/stats_server.py`
- [x] **UPG-005 (S)** Untrack `data/*.json`, `backups/*`, `config/settings.json`; extend `.gitignore`; make the private-repo boot phase opt-in
- [x] **UPG-006 (S)** Requirements: remove kokoro-onnx, pyttsx3, pytest, pytest-cov; add the 11 missing packages; bump pins; delete `config/requirements.txt` and `config/system_prompt1.txt`
- [x] **UPG-007 (S)** Close SEC-002/003/005, MEM-001/002 below (verified fixed in code)

### Phase 1 — runtime and models
- [x] **UPG-008 (M)** Python 3.12 side by side; `CORA.bat` uses `py -3.12` + venv, re-runs pip on requirements hash change, upgrades yt-dlp
- [x] **UPG-009 (M)** Single model config (`OLLAMA_URL`, `models.{chat,vision,code}`); remove hardcoded names in `ai/ollama.py`, `cora_tools/code.py`, `services/presence.py`, `voice/commands.py`, `services/stats_server.py`, `web/index.html`
- [x] **UPG-010 (S)** Switch chat to `qwen3.5:9b` (or `gemma4:12b`), vision to `qwen3-vl:4b`, code to `qwen3-coder`; warm at boot; unify timeouts
- [x] **UPG-011 (S)** Pollinations: Bearer/`sk_` key, fully qualified model IDs, drop nologo/enhance, move web off the legacy host

### Phase 2 — V2 voice (user decision: unity-voice-v2 replaces Kokoro/pyttsx3)
- [x] **UPG-012 (M)** `voice/unity_voice.py` client (health, `voice_text()` port, sentence chunking, emotion/act mapping, `delivery_support` validation, `stop_speaking`, `speak_async`); sidecar discovery/autostart via `UNITY_VOICE_TTS_URL` / `UNITY_VOICE_MODEL_DIR` / `UNITY_VOICE_PYTHON`; shared lock dir with unity-speak; new `tts.unity_voice` config block; delete `KokoroTTS`/`Pyttsx3TTS`, `src/cora.py` TTS functions, `tts_handler.py` engine code, `web/kokoro-worker.js`, all Kokoro/af_bella strings; presence check off the TTS thread
- [x] **UPG-013 (M)** Stream LLM output sentence-by-sentence into the V2 queue; barge-in via `stop_speaking`

### Phase 3 — the assistant loop
- [x] **UPG-014 (L)** One dispatcher: `cora_tools` as JSON-schema `tools` on `/api/chat`, loop on `message.tool_calls`; delete the four routers; re-wire git/email/media/terminal/viewfile only after their security fixes
- [x] **UPG-015 (M)** Boot per spec: speak today's calendar / overdue tasks / upcoming reminders; start `ReminderManager.start_checking()`; merge the two reminder stores; gate or remove the YouTube/GitHub/image-gen demo phases
- [x] **UPG-016 (M)** Conversation summarization at ~75% of `num_ctx`; honor `settings.ai.context_window`

### Phase 4 — STT and wake word
- [x] **UPG-017 (M)** `faster-whisper` on CUDA for commands; openWakeWord "cora" model; delete Vosk, `recognize_google`, `webkitSpeechRecognition`; bound the audio queue; VAD for barge-in

### Phase 5 — cleanup and fundamentals
- [x] **UPG-018 (M)** Delete dead modules (`src/cora.py`, `src/gui_launcher.py`, `ui/app.py`, `ui/panels.py`, `ai/tool_executor.py`, `ai/prompts.py`, `ai/router.py`, `ui/code_editor.py`, `ui/fullscreen_image.py`, `ui/image_panel.py`, `ui/monitor_panel.py`, `ui/query_panel.py`, `voice/converse.py`, transitively `voice/commands.py`, `cora_tools/modal_tools.py`) or finish one GUI; consolidate the two webcam pipelines + three windowing helpers; split the 12 files over 800 lines
- [x] **UPG-019 (M)** Single config loader with schema validation; one version constant; atomic JSON writes; shared logger; remove `atexit os._exit(0)`; cancel the waveform timer on close; heartbeat the TTS mutex
- [x] **UPG-020 (S)** `pyproject.toml`, `py_compile`/ruff CI job, CHANGELOG, git tags
- [x] **UPG-021 (M)** Web: split `index.html` into ES modules + css; generate phases/prompt JSON at deploy; serve locally via `stats_server.py` (fixes mixed content, CORS and the V2 sidecar); one public URL; fix the `innerHTML` sinks
- [x] **UPG-022 (S)** Docs truth pass: file/phase counts, entry point, default model, nonexistent files in ARCHITECTURE/NerdReadme/APIReference, SKILL_TREE percentages

### Later
- [ ] RAG over `knowledge.json` with Ollama embeddings (M) / MCP client (M) / real self-modification with static check + sandbox (L) / installer and auto-update (L) / multi-language (M) / accessibility (M)

---

## SCAN SUMMARY

| Category | Critical | High | Medium | Low | Total | ⚠️ Need Input |
|----------|----------|------|--------|-----|-------|---------------|
| Security | 7 | 6 | 4 | 2 | 19 | 7 |
| Memory/Resources | 5 | 4 | 6 | 3 | 18 | 0 |
| Architecture | 3 | 5 | 4 | 2 | 14 | 2 |
| Config/Workflow | 2 | 2 | 0 | 0 | 4 | 4 |
| Dependencies | 0 | 1 | 0 | 0 | 1 | 1 |
| Documentation | 0 | 2 | 3 | 4 | 9 | 2 |
| **TOTAL** | **17** | **20** | **17** | **11** | **65** | **16** |

**⚠️ 16 tasks require your input before AI can proceed!**

---

## CRITICAL ISSUES (Fix Immediately)

### SEC-002: eval() Used in Calculator — **FIXED (verified 2026-10-14, see SYSTEM_AUDIT)**
**Location:** `cora_tools/system.py:546-558`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `calculate()` uses `eval()` despite safety checks - can be bypassed
**Fix:** Replace with `ast.literal_eval()` or dedicated math parser

---

### SEC-003: PowerShell Injection Vulnerability — **FIXED (verified 2026-10-14, see SYSTEM_AUDIT)**
**Location:** `cora_tools/system.py:318-326, 369`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `notify()` function has insufficient escaping for PowerShell. User input in title/message could execute arbitrary PowerShell.
**Fix:** Use subprocess with proper argument arrays, never shell=True with user input

---

### SEC-004: Terminal Command Execution Unsafe ⚠️ ASK GEE
**Location:** `voice/commands.py:842-876`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `cmd_terminal()` lets user run ANY shell command with no sandboxing
**Fix:** Implement command whitelist or sandbox environment
**🛑 NEEDS INPUT:** Which commands should be whitelisted? Or prefer full sandbox?

---

### SEC-005: Git Command Injection — **FIXED (verified 2026-10-14, see SYSTEM_AUDIT)**
**Location:** `voice/commands.py:1154-1370`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** No shell escaping on git commands. `git checkout $(malicious)` possible.
**Fix:** Add shell escaping to all git commands

---

### SEC-006: Hardcoded OAuth Placeholder Never Replaced ⚠️ ASK GEE
**Location:** `cora_tools/git_ops.py:33`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `CLIENT_ID = "Ov23liYourClientIdHere"` - template placeholder in production
**Fix:** Load from .env or config only, never hardcode
**🛑 NEEDS INPUT:** Do you have a GitHub OAuth CLIENT_ID? Or remove OAuth entirely?

---

### SEC-007: Code Execution Pattern Detection Gaps ⚠️ ASK GEE
**Location:** `cora_tools/code.py:371-391`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `_is_dangerous()` uses regex patterns that can be bypassed. Missing: `subprocess.Popen`, `os.spawn*`, `importlib.__import__`
**Fix:** Whitelist safe operations instead of blacklist dangerous ones
**🛑 NEEDS INPUT:** Which code operations should be whitelisted as SAFE?

---

### SEC-008: stats_server.py Arbitrary pip Install ⚠️ ASK GEE
**Location:** `services/stats_server.py` - `/setup/install-requirements` endpoint
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Allows arbitrary pip installs from requirements.txt without auth
**Fix:** Add authentication or remove endpoint
**🛑 NEEDS INPUT:** Add authentication (what kind?) or just remove the endpoint?

---

### MEM-001: TTS Audio Buffer Race Condition — **FIXED (verified 2026-10-14, see SYSTEM_AUDIT)**
**Location:** `voice/tts.py:178-240`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Waveform UI reads `_audio_buffer_singleton` while TTS writes to it - no synchronization
**Fix:** Add thread-safe locking around audio buffer operations

---

### MEM-002: STT Transcript Buffer Memory Leak — **FIXED (verified 2026-10-14, see SYSTEM_AUDIT)**
**Location:** `voice/stt.py:266-272`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** WakeWordDetector transcript buffer never cleared - accumulates indefinitely
**Fix:** Clear buffer periodically or use bounded deque

---

### MEM-003: Wake Word Audio Queue Unbounded
**Location:** `voice/wake_word.py:88`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `queue.Queue()` with no maxsize. If Vosk can't keep up, queue grows forever.
**Fix:** Add `maxsize=100` or similar limit

---

### MEM-004: TTS Mutex Starvation
**Location:** `voice/tts_mutex.py:284-313`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Stale lock timeout (30s) is arbitrary - lock can be stolen mid-speech
**Fix:** Implement timeout with exponential backoff

---

### ARCH-001: Circular Dependency voice.tts ↔ ui.boot_display
**Location:** `voice/tts.py:35` imports from `ui/boot_display.py`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Creates cross-layer circular dependency. If UI init fails, TTS fails.
**Fix:** Create `shared/audio_buffer.py` module, both import from there

---

### CFG-001: Duplicate System Prompt Files ⚠️ ASK GEE
**Location:** `config/system_prompt.txt` and `config/system_prompt1.txt`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Both files are IDENTICAL (204 lines each) - no version control
**Fix:** Delete `system_prompt1.txt`, use single source of truth
**🛑 NEEDS INPUT:** Confirm delete system_prompt1.txt? Any differences you want to keep?

---

### WF-001: 70% of Workflow Hooks Not Implemented ⚠️ ASK GEE
**Location:** `.claude/` workflow system
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Only 4 of 12+ gates have Python hook implementations. Scan/Analysis/Planning/Documentation gates are documentation-only.
**Fix:** Implement missing 8 hook validators
**🛑 NEEDS INPUT:** Which hooks do you actually want enforced? All 12 or a subset?

---

### WF-002: No Template Substitution Engine ⚠️ ASK GEE
**Location:** `.claude/templates/*.md`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Templates use `{{PLACEHOLDER}}` syntax but no code exists to substitute them
**Fix:** Create template substitution engine or remove templates
**🛑 NEEDS INPUT:** Build a template engine or just delete the templates folder?

---

---

## HIGH SEVERITY ISSUES

### SEC-H01: Arbitrary File Access ⚠️ ASK GEE
**Location:** `voice/commands.py:626-660`
**Severity:** HIGH
**Status:** `pending`
**Issue:** `viewfile()` reads any path user specifies - no validation
**Fix:** Validate paths, restrict to project directory
**🛑 NEEDS INPUT:** Which directories should CORA be allowed to read?

---

### SEC-H02: GitHub Token Exposure in boot_sequence.py
**Location:** `src/boot_sequence.py:1162-1227`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Reads GITHUB_TOKEN from environment without sanitization, could expose private repos
**Fix:** Sanitize token usage, don't log

---

### SEC-H03: Email Recipient Not Validated ⚠️ ASK GEE
**Location:** `voice/commands.py:1447-1557`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No whitelist or verification of email recipients
**Fix:** Implement recipient whitelist or confirmation
**🛑 NEEDS INPUT:** Which email recipients should be whitelisted? Or just add confirmation prompt?

---

### MEM-H01: UI Panels Not Properly Destroyed
**Location:** `ui/app.py:126, 563-604`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Panels created on-demand without cleanup when switching - memory accumulates
**Fix:** Implement `grid_forget()` + explicit `destroy()` in `_hide_current_panel()`

---

### MEM-H02: Waveform Animation Never Stops
**Location:** `ui/boot_display.py:1797-1798`
**Severity:** HIGH
**Status:** `pending`
**Issue:** `waveform.stop()` is no-op (passes silently). Animation never stops.
**Fix:** Implement actual stop logic, cancel animation_id

---

### MEM-H03: Photo Reference List Grows Indefinitely
**Location:** `ui/image_panel.py:187`
**Severity:** HIGH
**Status:** `pending`
**Issue:** `_photo_refs` list grows with every image shown, no limit
**Fix:** Implement max 5-item circular buffer

---

### MEM-H04: Ambient Awareness Resource Drain
**Location:** `voice/ambient_awareness.py:333-440`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Screenshot/camera analysis blocks monitor thread. Ollama calls have no timeout.
**Fix:** Queue analysis requests, add 5s timeout to Ollama calls

---

### ARCH-H01: Command Routing Ambiguity ⚠️ ASK GEE
**Location:** `src/cora.py` vs `ai/tool_executor.py`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Two different command routing systems, unclear which is authoritative
**Fix:** Consolidate to single command router with clear COMMANDS dict
**🛑 NEEDS INPUT:** Which command router do you want to keep? cora.py or tool_executor.py?

---

### ARCH-H02: Presence Detection Blocks TTS
**Location:** `voice/tts.py:598-621`
**Severity:** HIGH
**Status:** `pending`
**Issue:** `check_human_present()` blocks TTS queue processing - can hang if webcam unavailable
**Fix:** Make presence checks async with cache and fallback

---

### ARCH-H03: Hardcoded Ollama URL ⚠️ ASK GEE
**Location:** `ai/ollama.py` - `http://localhost:11434`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No environment variable support, breaks if Ollama on different host
**Fix:** Add `OLLAMA_URL` environment variable with fallback
**🛑 NEEDS INPUT:** What's your Ollama URL? localhost:11434 or different?

---

### ARCH-H04: No Context Window Management
**Location:** `ai/ollama.py`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No token counting or context truncation - can overflow model's context window
**Fix:** Add token counting before sending requests

---

### CFG-H01: No JSON Schema Validation
**Location:** `config/*.json`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No type checking, range validation, or required field enforcement
**Fix:** Implement JSON schema validation for all config files

---

### CFG-H02: Voice Settings Duplicated ⚠️ ASK GEE
**Location:** `config/settings.json` vs `config/config.json`
**Severity:** HIGH
**Status:** `pending`
**Issue:** TTS rate/volume defined in BOTH files - unclear which wins
**Fix:** Consolidate to single source
**🛑 NEEDS INPUT:** Keep voice settings in settings.json or config.json?

---

### DEP-H01: Inconsistent Requirements Files ⚠️ ASK GEE
**Location:** `requirements.txt` vs `config/requirements.txt`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Main uses `~=`, config uses `>=`. Many deps missing from config version.
**Fix:** Delete `config/requirements.txt`, keep only main one
**🛑 NEEDS INPUT:** Confirm delete config/requirements.txt and keep root requirements.txt?

---

### API-H01: Location Service Uses HTTP Not HTTPS
**Location:** `services/location.py`
**Severity:** HIGH
**Status:** `pending`
**Issue:** ip-api.com called over HTTP - privacy leak
**Fix:** Change to `https://ip-api.com/json/`

---

### API-H02: No Rate Limiting on External APIs
**Location:** `services/weather.py`, `services/location.py`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No rate limiting despite API limits (ip-api: 45 req/min, wttr.in: 2 req/sec)
**Fix:** Implement rate limiting decorator

---

---

## MEDIUM SEVERITY ISSUES

### Threading Issues
- [ ] `boot_display.py:1620-1747` - Background stats thread spawned without proper cleanup
- [ ] `boot_console.py:708-724` - GitHub fetch thread no dead window check
- [ ] `app.py:341-346, 475-478, 517-520` - Uncontrolled threads with no management
- [ ] `emotion.py:141` - `_cora_mood` global not thread-safe

### Error Handling
- [ ] `tts.py:223-231` - No timeout on audio playback - UI can freeze
- [ ] `boot_sequence.py:156-158` - Catches all exceptions, swallows errors
- [ ] `cora.py` - Falls back silently without logging real errors

### Resource Management
- [ ] `camera_feed.py:68-98` - Multiple camera opens without proper release
- [ ] `modals.py:139-206` - PIL Image objects not cleaned on modal close
- [ ] `presence.py` - Snapshot files never cleaned up

### Echo Filter
- [ ] `echo_filter.py:260-262` - Duration formula vastly underestimates speech length
- [ ] `converse.py:53-104` - EchoFilter duplicated (should import from echo_filter.py)

### Wake Word
- [ ] `wake_word.py:131-132` - Substring matching causes false positives ("Core" matches "cora")
- [ ] `wake_word.py:206` - 5-second timeout is arbitrary, no adaptive timing

### Conversation
- [ ] `converse.py:227-265` - Wake mode never times out
- [ ] `converse.py:189-192` - "stop" matches "I can't stop laughing"

### Configuration
- [ ] Relative paths only in config.json - breaks if working directory changes
- [ ] No environment variable support in config
- [ ] Backup configuration incomplete (auto_backup: false, no location)

### Dependencies
- [ ] numpy 1.26.0 compatibility with older opencv versions
- [ ] pytest/pytest-cov in requirements but tests forbidden
- [ ] No Python version constraint specified

---

## LOW SEVERITY ISSUES

- [ ] Color/theme values not validated (hex format)
- [ ] Inconsistent naming conventions (snake_case vs CONSTANT_CASE)
- [ ] Unused fallback code in system.py, code.py
- [ ] Missing docstring examples in most functions
- [ ] Comment style inconsistency across agents
- [ ] pyttsx3 Windows compatibility concerns (v2.90 from 2021)
- [ ] No graceful degradation docs
- [ ] Missing module interdependency diagram
- [ ] Author/copyright in config.json (should be in LICENSE)

---

## DOCUMENTATION GAPS ⚠️ ASK GEE FOR ALL

### Missing Files
- [ ] ROADMAP.md - No milestone planning document **🛑 NEEDS INPUT: Your vision/milestones**
- [ ] CHANGELOG.md - No version history
- [ ] CONTRIBUTING.md - No contributor guidelines **🛑 NEEDS INPUT: Your contribution rules**

### Documentation Updates Needed
- [ ] Document threading model in ARCHITECTURE.md
- [ ] Add resource cleanup checklist
- [ ] Document Ollama API version assumptions
- [ ] Add fallback strategies documentation

---

## PREVIOUS SESSION (2025-12-25) - COMPLETE

> Moved to FINALIZED.md

- [x] Personality fix - Stripped instructions from prompts
- [x] TTS waveform retry mechanism
- [x] Audio source tracking for concurrent playback
- [x] URL stripping for TTS
- [x] All phase templates fixed

---

## Future Enhancements (P2) ⚠️ ASK GEE BEFORE STARTING

**These are feature requests - get Gee's approval before implementing any!**

- [ ] Add more model options to backend terminal **🛑 Which models?**
- [ ] Implement model download progress in web UI
- [ ] Add GPU temperature warning thresholds **🛑 What thresholds?**
- [ ] Voice activity detection for ambient listening **🛑 Want this feature?**

---

*Unity AI Lab - C.O.R.A v1.0.0*
*Deep Scan: 2025-12-29 06:06:03*


---

# LEGACY — pre-merge docs/TODO.md (10-Agent Deep Scan, 2025-12-23)

> Preserved verbatim on 2026-10-14 when the root TODO.md moved into docs/. Historical reference only; the live task list is above.

# C.O.R.A TODO - 10-Agent Deep Scan Results

```
  ================================================================
    ____   ___   ____      _
   / ___| / _ \ |  _ \    / \
  | |    | | | || |_) |  / _ \
  | |___ | |_| ||  _ <  / ___ \
   \____| \___/ |_| \_\/_/   \_\

  Cognitive Operations & Reasoning Assistant
  ================================================================
  Version: 1.0.0
  Unity AI Lab | https://www.unityailab.com
  ================================================================
```

**Generated:** 2025-12-23 (10-Agent Ultrathink Scan)
**Project:** cora-2
**Status:** OPERATIONAL WITH CRITICAL ISSUES

---

## EXECUTIVE SUMMARY

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 5 | 3 | 4 | 4 |
| Dependencies | 2 | 1 | 3 | 0 |
| Integration | 2 | 4 | 6 | 3 |
| Documentation | 0 | 5 | 4 | 2 |
| Testing | 1 | 0 | 0 | 0 |
| **TOTAL** | **10** | **13** | **17** | **9** |

---

## P10 - CRITICAL SECURITY (IMMEDIATE)

| ID | Task | File | Issue |
|----|------|------|-------|
| SEC-001 | Move Pollinations API key to .env | `tools/image_gen.py:26` | API key exposed |
| SEC-007 | Create .gitignore file | Root directory | Prevent secret commits |
| SEC-008 | Move ALL credentials to environment vars | Multiple files | Use os.environ.get() |

---

## P9 - CRITICAL DEPENDENCIES

| ID | Task | File | Issue |
|----|------|------|-------|
| DEP-001 | Add aiohttp to requirements.txt | `ai/ollama.py:16` | Async AI broken |
| DEP-002 | Add portalocker to requirements.txt | `voice/tts_mutex.py:21` | TTS mutex fails |
| DEP-003 | Add speech_recognition to requirements.txt | `voice/converse.py:24` | Fallback STT broken |

---

## P9 - CRITICAL INTEGRATION

| ID | Task | File | Issue |
|----|------|------|-------|
| INT-001 | Import tools/memory.py in cora.py | `src/cora.py` | 352-line module orphaned |
| INT-002 | Integrate ReminderManager.start_checking() | `tools/reminders.py` | Reminders never trigger |

---

## P8 - HIGH PRIORITY SECURITY

| ID | Task | File | Issue |
|----|------|------|-------|
| SEC-009 | Fix PowerShell command injection | `tools/system.py:300` | Unescaped input |
| SEC-010 | Replace shell=True with argument lists | `tools/system.py:537-587` | Dangerous pattern |

---

## P8 - HIGH PRIORITY INTEGRATION

| ID | Task | File | Issue |
|----|------|------|-------|
| INT-003 | Expand tools/__init__.py exports | `tools/__init__.py` | Only exports TTS |
| INT-004 | Fix sys.path in self_modify.py | `tools/self_modify.py:96` | Literal string |
| INT-005 | Increase MAX_CHAT_HISTORY | `src/cora.py:166` | Capped at 10 |
| INT-006 | Consolidate duplicate reminder systems | `tools/calendar.py`, `tools/reminders.py` | Two systems |

---

## P8 - HIGH PRIORITY DOCS

| ID | Task | File | Issue |
|----|------|------|-------|
| DOC-001 | Update SKILL_TREE.md footer version | `SKILL_TREE.md` | Footer says 0.1.0 |
| DOC-002 | Update ROADMAP.md to v1.0.0 | `docs/ROADMAP.md` | Completely outdated |
| DOC-003 | Update READMEs folder to v1.0.0 | `READMEs/*.md` | All show v1.0.0 |
| DOC-004 | Create SLAVE1_WORKFLOW.md | `.claude/workflow/` | Only SLAVE2 exists |
| DOC-005 | Split oversized docs (<800 lines) | `APIReference.md`, `ARCHITECTURE.md` | Exceed limit |

---

## P7 - MEDIUM PRIORITY SECURITY

| ID | Task | File | Issue |
|----|------|------|-------|
| SEC-012 | Replace eval() in calculate() | `tools/system.py:525` | Use safer alternative |
| SEC-013 | Add path traversal validation | `tools/files.py` | Paths not sanitized |
| SEC-014 | Escape clipboard PowerShell | `tools/system.py:346` | Input unescaped |

---

## P7 - MEDIUM PRIORITY INTEGRATION

| ID | Task | File | Issue |
|----|------|------|-------|
| INT-007 | Fix hardcoded C:\claude\ path | `voice/tts_mutex.py:25-26` | Won't exist |
| INT-008 | Document Vosk model download | `voice/wake_word.py:40` | Model required |
| INT-009 | Add error logging (not just print) | Multiple files | Silent failures |
| INT-010 | Add rate limiting to web requests | `tools/web.py` | Could block |
| INT-011 | Add request timeouts consistently | `tools/email_tool.py` | Can hang |
| INT-012 | Validate JSON before parsing | `services/location.py:24` | No error handling |

---

## P6 - TESTING (CRITICAL GAP)

| ID | Task | File | Issue |
|----|------|------|-------|
| TEST-001 | Create tests/ directory structure | Root | Zero test coverage |
| TEST-002 | Add pytest to requirements.txt | `requirements.txt` | No framework |
| TEST-003 | Create conftest.py with fixtures | `tests/` | No infrastructure |
| TEST-004 | Write TaskManager unit tests | `tools/tasks.py` | Untested |
| TEST-005 | Write AI router tests | `ai/router.py` | Untested |

---

## P5 - LOW PRIORITY

| ID | Task | File | Issue |
|----|------|------|-------|
| LOW-001 | Add structured logging system | Multiple | Using print() |
| LOW-002 | Implement circuit breaker pattern | API calls | No retry/backoff |
| LOW-003 | Add request caching | Web APIs | Not cached |
| LOW-004 | Remove unused deps (ollama, colorama) | `requirements.txt` | Bloat |

---

## PREVIOUS COMPLETED TASKS

| Task | Completed By |
|------|--------------|
| tools/tasks.py created | Slave1 |
| ai/prompts.py created | Slave1 |
| voice/echo_filter.py created | Slave1 |
| boot_sequence() integration | Slave1 |
| System tray integration | Slave1 |
| config/config.json updated to v1.0.0 | Unity |
| tools/windows.py created (21KB) | Unity |
| tools/code.py created (23KB) | Unity |
| Full codebase push to GitHub main+develop | Unity |
| 10-Agent deep scan completed | Unity |

---

## OPERATIONAL STATUS BY MODULE

| Module | Status | Critical Issues |
|--------|--------|-----------------|
| Core CLI | ✅ WORKING | None |
| Tools | ⚠️ PARTIAL | API key exposed |
| Voice | ⚠️ PARTIAL | Missing deps |
| AI | ⚠️ PARTIAL | Missing aiohttp |
| Services | ✅ WORKING | Minor issues |
| UI | ✅ WORKING | Untested |
| Memory | ⚠️ PARTIAL | Module orphaned |

---

*Unity AI Lab - C.O.R.A v1.0.0*
*Last Updated: 2025-12-24*
