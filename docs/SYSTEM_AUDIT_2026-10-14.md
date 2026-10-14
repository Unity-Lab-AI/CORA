# C.O.R.A — Full System Audit (2026-10-14)

> Task AUD-001. User's words: "okay now we need to do a full system check of the cora project and see what tech is out dated models and anything else that needs updating and replacing to fuylly make this project everything it should be and everything its missing" and "we will use our V2 voice model from the backrooms folder and voice lab".
>
> Read-only audit. Four parallel passes (dependencies/runtime, AI + voice stack, code health + security, vision-vs-implementation) plus a read of the V2 voice model. No code changed. Every claim below has a file:line or URL behind it in the per-pass notes; the headline numbers are reproduced here.

---

## 1. Verdict in one paragraph

C.O.R.A is a large library of mostly real building blocks (63 Python files, ~36k lines, plus a 5,300-line web app) wrapped around an assistant loop that is the weakest part of the project. The live path is `CORA.bat -> src/boot_sequence.py -> ui/boot_display.py`, and that path routes user text by regex, sends the LLM a single message with no history, never sets Ollama's context size (so the 27k-character persona prompt is silently clipped — the real cause of "the model ignores the system prompt"), never starts the reminder scheduler, and plays music through a shell-injectable command. Roughly 40% of the Python (the CLI, the GUI app, the 50-command voice registry, the code editor, four panels) is dead code nothing launches. The runtime is Python 3.10, which went end-of-life on 2026-10-01. The TTS stack has three divergent implementations and a requirements file that installs the wrong Kokoro package; all of it is replaced by the V2 voice sidecar. Fixing the loop (native tool calling, history, context, streaming), swapping the three models, moving to the V2 voice, and deleting the dead half of the tree is what turns this from a tool library into the assistant the ARCHITECTURE spec describes.

---

## 2. Runtime and dependencies

**Python:** 3.10.6 is the only interpreter on the machine and reached end-of-life 2026-10-01. `CORA.bat` uses bare `python`/`pip` from PATH with no version guard. With Kokoro gone (see §4) nothing caps the version; **target Python 3.12** (every remaining dependency supports it; numpy 2.5 needs ≥3.12) and revisit 3.13/3.14 after the first clean run. Only `vosk` (frozen wheel, works) and `pywin32` tags beyond cp311 were not verifiable.

**Dependency wiring is broken, not just stale:**

| Problem | Evidence |
|---|---|
| Listed TTS package is not the one imported | `requirements.txt` pins `kokoro-onnx~=0.4.0`; every call site does `from kokoro import KPipeline` (torch package, never listed). `src/cora.py:323-352` auto-installs `kokoro-onnx` on failure, so it can never satisfy the import. Moot after V2. |
| 11 imported packages missing from requirements | `pycaw`, `win10toast`, `GPUtil`, `keyboard`, `pynput`, `plyer`, `tkinterdnd2`, `playwright`, `pywin32`, `comtypes`, `yt-dlp` (shelled). 7 are not installed at all, so hotkeys, volume control, toasts and window tools silently degrade (all wrapped in try/except). |
| 4 listed packages not installed | `pygetwindow`, `pyautogui`, `portalocker`, `pytest-cov` — `CORA.bat` only runs pip when `data/.setup_complete` is absent (it has existed since 2025-12-24). |
| Test deps shipped despite NO TESTS policy | `pytest~=8.0.0`, `pytest-cov~=4.1.0`; no test files exist. |
| Two requirements files, neither authoritative | `config/requirements.txt` is a stale v0.5-era copy (`>=` pins, lists unused `ollama` and `colorama`). Nothing references it except a fallback in `stats_server.py:194`. |
| Pins contradict the installed env | `numpy~=1.26` pinned, 2.2.6 installed and working (no removed-alias uses in code). |

**Version bumps (all verified on PyPI, Oct 2026):** requests 2.31→2.34, aiohttp 3.9→3.14 (3.9 carries open CVEs), numpy 1.26→2.2 (2.5 after Py3.12), Pillow 10.2→12.3, psutil 5.9→7.2, opencv-python 4.9→4.12 (stay <5; 5.0 removed APIs, and `opencv-python-headless` 5.0 is installed alongside — uninstall it), SpeechRecognition 3.10→3.17, soundfile 0.12→0.14, sounddevice 0.4→0.5, python-dotenv 1.0→1.2, portalocker 2.8→4.4 (4.x drops pywin32 default; exclusive locks still work), customtkinter stay on 5.2.2 (6.0.0 has no published changelog). yt-dlp installed 2025.12.8 vs 2026.08.19; the bat only checks presence and never upgrades it.

---

## 3. AI model stack

### LLM
- **Four sources disagree on the model:** `ai/ollama.py:24` hardcodes `dolphin-mistral:7b` (Oct-2023 lineage, last update Mar 2024); `config/config.json` and `settings.json` say `llama3.2`; `CORA.bat` pulls dolphin-mistral + llava + qwen2.5-coder; `models/model_config.json` says codellama. None is authoritative and `ai/router.py` (the model router) has no callers.
- **Context clipping bug:** `num_ctx` is never sent (zero hits in repo). Ollama defaults to 4096 tokens under 24 GiB VRAM and silently drops the beginning of the prompt. The persona prompt is ~5-7k tokens (plus ~1.8k for `tools_prompt.txt` in the boot path). This is the literal mechanism behind commits fa9a9a1/f38a87a ("dolphin-mistral ignoring 27k system prompt") and the web "personality kick" hack at `web/index.html:1328`. Fix: `options.num_ctx` ≥ 16384 per request at `ai/ollama.py:168`, and cut the prompt roughly in half.
- **No conversation memory over HTTP:** `src/cora.py:1664-1668` and `ui/boot_display.py:1174,1247` send `messages=[{'role':'user',...}]` only; the 50-exchange history is spliced only into the `ollama run` subprocess fallback.
- **No native tool calling, no streaming:** tools are regex-matched on the *user's* text (`ai/tool_executor.py:36-68`, dead path) or hardcoded regexes in `boot_display.py:860-1265` (live path). `chat_stream()`/`async_chat_stream()` exist with zero callers; TTS waits for the full completion.
- **Recommended chat model on the RTX 4070 Ti SUPER (16 GB):** `qwen3.5:9b` or `gemma4:12b` — both have native Ollama tool calling, vision, 32k+ context, and fit beside the V2 voice (0.5 GB). Backrooms already runs a Qwen3.5-9B LoRA (`unity-brain`) on this card with a 32k context. If an uncensored base is required, `dolphin3` (Llama-3.1-8B) is the current line, but its tool-calling reliability is unverified.
- **Vision:** `llava:7b` (3 files) → `qwen3-vl:4b` (3.3 GB, direct swap) or let `gemma4` do vision + tools in one model. Avoid `llama3.2-vision` (broken since Ollama 0.30).
- **Code model:** `qwen2.5-coder:7b` hardcoded in `cora_tools/code.py:79` → `qwen3-coder` family, or just reuse the chat model.
- **Timeouts** are 30/60/65/120 s across five files; a 9B model with a 7k-token prompt will blow the 60 s `cmd_chat` budget on first call. Set `keep_alive` and warm the model at boot.

### STT and wake word
- Vosk 0.3.45: last PyPI release Dec 2022, substring wake-word match on full transcripts (`wake_word.py:131`), unbounded audio queue (`:88`), model folder absent (no downloader). STT is disabled by default.
- `voice/converse.py:174` uses `recognize_google` (cloud) and the web page uses `webkitSpeechRecognition` (cloud) — both contradict local-first.
- **Replace with:** `faster-whisper` 1.2.1 on CUDA for command transcription (Backrooms already uses faster-whisper-base int8 for screening), **openWakeWord** with a trained "cora" model for the wake word (dedicated KWS is cheaper and far more accurate than continuous ASR). Moonshine or Parakeet TDT 0.6B are the streaming alternatives.

### Image generation
- `cora_tools/image_gen.py:29` uses `gen.pollinations.ai/image` with `model=flux` and `key=`; the web page uses the legacy `image.pollinations.ai` host with no key. Per current Pollinations APIDOCS a key is required (401 without), the default image model is now `tongyi-mai/z-image-turbo`, model IDs are fully qualified (`black-forest-labs/flux.1-schnell`), `nologo`/`enhance` are no longer documented, and `pk_` raw keys are rate-limited per IP. Whether the `flux` alias still resolves is unverified — query `/image/models`.

---

## 4. TTS → unity-voice-v2 (decided)

**What V2 is:** your own FastSpeech2-style acoustic model + HiFi-GAN vocoder (159 MB), trained from scratch on the A2 "low warm alto" voice, emotional-range retrain live since 2026-10-13. Folder `C:\Users\gfour\Desktop\Backrooms\models\unity-voice-v2\`. Served by `serve.py` on `127.0.0.1:5123`: `POST /say {"text","emotion","intensity","speech_act"}` → 24 kHz PCM16 WAV, `GET /health`. ~0.5 GB VRAM, 4.4 s of audio in 0.3 s. 9 emotions (neutral, warm, happy, amused, excited, sad, concerned, frustrated, surprised), 7 speech acts (statement, yes_no_question, wh_question, exclamation, instruction, reassurance, aside), `[laughter]`/`[breath]` event tokens. Only the (emotion, act) pairs in `voice-meta.json` `delivery_support` are accepted; anything else is a 422. No fallback voice by design. Phoneme vocabulary holds only space `,` `.` `?` — any other mark makes the server refuse the whole line; the proven normalizer is `voice_text()` in `Backrooms/.claude/tools/unity-speak.py:20-58`. Runtime needs torch 2.7.1+cu118, misaki 0.9.4 exact, soundfile 0.13.1, numpy 2.2.6 — **it must run as a sidecar in its own venv**, which is how `Backrooms/stream/services.py` already runs it.

**What CORA has today (three divergent stacks, all to be deleted):**
1. `voice/tts.py` — `KokoroTTS` (torch kokoro, `sd.OutputStream` 24 kHz with the waveform hook at `:171-242`), `Pyttsx3TTS`, factory, `TTSQueue` with mutex + presence gate.
2. `cora_tools/tts_handler.py` — builds a new `KPipeline` per utterance, `sd.play`, no waveform.
3. `src/cora.py:314-352, 1236-1378` — its own kokoro/pyttsx3 functions + the broken auto-installer.
Plus `web/kokoro-worker.js` (kokoro-js 1.2.0) and a dead Kokoro-FastAPI probe at `web/index.html:1257`. Two referenced symbols do not exist: `voice.tts.stop_speaking` (`boot_display.py:1068`, so "stop/quiet" is a no-op) and `voice.tts.speak_async` (`services/cli_popup.py:359`, so popups never speak).

**Migration plan:**
1. New `voice/unity_voice.py` implementing the existing `TTSEngine` interface so `TTSQueue`, the mutex, callbacks and the Tk waveform stay untouched: `GET /health` with retry on `initialize()`; port `voice_text()` verbatim and apply it after the existing `*action*` stripping and URL stripping; split into sentences after normalization and POST each (a 422 loses one sentence, first audio starts sooner, synth N+1 while N plays); decode with `soundfile` and reuse the exact `sd.OutputStream` block so `_audio_buffer_singleton` keeps feeding the waveform; implement `stop_speaking()` (callback flag + `TTSQueue.clear()`) and `speak_async`.
2. Emotion/act selection from `voice/emotion.py`: excited→excited, concerned/urgent→concerned, satisfied→happy, warm/gentle→warm, annoyed→frustrated, playful→amused, else neutral; intensity 0.5 default, 0.8 for excited/frustrated, scaled by `config emotion.intensity`. Act per sentence: wh-word + `?` → wh_question, other `?` → yes_no_question, original `!` → exclamation, imperative verb → instruction, "it's okay"/"don't worry" → reassurance, `*aside*` → aside, else statement. Validate against `delivery_support` (read `voice-meta.json` when `UNITY_VOICE_MODEL_DIR` is set), fall back pairwise to neutral/statement.
3. Sidecar discovery, not a copy: `UNITY_VOICE_TTS_URL` (default `http://127.0.0.1:5123`, same env name unity-speak uses), `UNITY_VOICE_MODEL_DIR`, `UNITY_VOICE_PYTHON` (that venv). Boot: health check; if down and `autostart`, `Popen` the server detached and poll `/health` ≤30 s; leave it running (shared with Unity's other callers). Point `CLAUDE_MUTEX_DIR` at the same lock dir unity-speak uses so CORA and Unity never overlap on the one voice.
4. Config: replace `tts.engine/rate/kokoro{}` with `tts.{enabled, volume, engine:"unity-voice", unity_voice:{url, model_dir, autostart, default_intensity}}`; drop `auto_setup.auto_install_kokoro`; the `voice.tts_*` keys in `settings.json` are read by nothing and can go.
5. Delete: `KokoroTTS`, `Pyttsx3TTS`, `list_voices`, the `src/cora.py` TTS functions, `tts_handler.py` engine code, `web/kokoro-worker.js`, `kokoro-onnx` + `pyttsx3` from requirements, the SAPI voice combo + rate slider in `ui/panels.py`, every "Kokoro"/"af_bella" string in `boot_sequence.py`, `boot_console.py`, `index.html`, README, SETUP.
6. Move the presence check off the TTS thread (`voice/tts.py:636` opens the webcam and posts to llava with a 60 s timeout before every utterance).
7. Web version: a GitHub Pages (https) page cannot reach `127.0.0.1:5123` without Chrome's Local Network Access prompt plus CORS on `serve.py`, and it already has the same problem with Ollama on :11434. Recommended: serve `web/` locally from `stats_server.py` and proxy `/say` so everything is same-origin; otherwise keep Web Speech as the web-only voice. Playback side is a small change (`fetch('/say')` → `decodeAudioData` → the existing `BufferSource` + `AnalyserNode` code at `index.html:1562-1631`).

---

## 5. Security

**New, in the live path (HIGH):** `ui/boot_display.py:977-978` builds `yt-dlp -o - "ytsearch1:{query}" | mpv ...` with `shell=True` from user/STT text matched at `:952`. `play foo" & calc & "` executes. The only `shell=True` reachable today and not in the 2025 list. Fix: two list-args `Popen` calls piped together, or reuse the safe pattern in `cora_tools/media.py:470`.

**New, in currently dead paths but exported (HIGH):** `cora_tools/files.py:15-66` `_validate_path(base_dir=None)` is a no-op by default and no caller passes `base_dir`, so all 17 file ops accept any absolute path including recursive delete. `cora_tools/self_modify.py:56-167` writes arbitrary LLM-supplied Python and runs it with no check. `cora_tools/system.py:620-689` `run_shell` claims "no shell=True" but runs `['cmd','/c', command]` behind a substring blocklist.

**Still open from Dec 2025:** SEC-004 (terminal `shell=True`, dead path), SEC-006 (OAuth placeholder `Ov23liYourClientIdHere`), SEC-007 (10-regex blacklist in `code.py`), SEC-008 (`stats_server.py` unauthenticated `POST /setup/install-requirements` + `/setup/pull-model/<name>` behind `Access-Control-Allow-Origin: *` — CSRF from any website while it runs; mitigated only by the 127.0.0.1 bind), SEC-H01 (viewfile arbitrary path), API-H01 (`http://ip-api.com`).

**Fixed since Dec 2025:** SEC-002 (AST calculator), SEC-003 (PowerShell escaping), SEC-005 (git list args + ref validation), MEM-001, MEM-002. `docs/TODO.md` still lists SEC-002/003 as pending.

**Privacy:** `.env` is not tracked (good; contains only `POLLINATIONS_API_KEY` and `GITHUB_TOKEN`). But `data/*.json` (chat history, knowledge, working memory, calendar, tasks), `config/settings.json`, `config/personality.json` and `backups/*` are tracked in a repo that is now public on GitHub. Boot phase 4.1 (`boot_sequence.py:1161-1260`) uses `GITHUB_TOKEN` to enumerate the user's private repos and display a random file.

---

## 6. The assistant loop (vision vs implementation)

| Promise (ARCHITECTURE/README/SKILL_TREE) | Reality |
|---|---|
| LLM can call tasks, calendar, knowledge, files, system, windows, web, code, email, media | No native tool calling anywhere. Tools reachable only by typed CLI words (dead) or ~15 hardcoded regexes in `boot_display.py`. Git, email, media, terminal, viewfile are unreachable in the shipped path. |
| One command router | **Four**: `boot_display._default_process_input` (live), `voice/commands.py` registry (50 cmds, dead), `src/cora.py` CLI dispatch (dead), `ai/tool_executor.py` regex table (dead). |
| Boot narrates today's calendar, overdue tasks, upcoming reminders | Calendar never called; tasks/reminders are counted, nothing spoken. Instead boot runs YouTube, GitHub private-repo import, audio test, modal test, and an AI-prompted "disturbing image" generation — 60-120 s with internet, vs the ~10 s spec. |
| Reminders fire | `ReminderManager.start_checking()` (`reminders.py:260`) has no caller. Two reminder stores (`data/reminders.json` vs `data/calendar.json`). |
| Self-modification (`create_tool`) | Three divergent stubs; `src/cora.py:2160-2230` writes `# TODO: Implement tool logic`; `data/temp_scripts.json` has no reader. |
| Multi-model routing (primary/code/image) | Config slots null; router dead. |
| Email send/read | `mailto:` URL and launching Outlook. |
| Media (Emby) | Reads `config/media_config.json` which does not exist. |
| Tasks panel, Knowledge panel, Settings panel | `_add_task: pass`; knowledge entries never loaded and `cmd_learn` gets a `str` instead of a list; settings panel writes a schema nothing reads. `ui/app.py:375` references `cora.COMMANDS` which does not exist. |
| Code editor / IDE, query panels + hotbar, converse mode | Modules exist (1,309 / 553 / ~300 lines) with no caller. |
| Wake word always listening | Needs `models/vosk-model-small-en-us-0.15` which is absent and never downloaded; STT disabled by default. |
| Presence detection before speaking at boot | Module exists; not wired into boot. |
| Installer / auto-updater | Absent. |

**Modern-assistant capabilities absent:** streaming, native tools, conversation memory, context management (`settings.ai.context_window` has no reader), RAG over `knowledge.json` (tag filter only; `/api/embed` unused), MCP client, plugin/skill system, scheduling, barge-in/VAD, multi-language (`lang_code='a'`, en-us everywhere), GPU provider selection, offline caching (boot hits ip-api, wttr.in, Google News, GitHub, YouTube, Pollinations uncached), auto-update.

---

## 7. Code health

**Dead code (never imported, not the entry point):** `src/cora.py` (2,767 lines), `src/gui_launcher.py`, `ui/app.py`, `ui/panels.py`, `ai/tool_executor.py`, `ai/prompts.py`, `ai/router.py`, `ui/code_editor.py`, `ui/fullscreen_image.py`, `ui/image_panel.py`, `ui/monitor_panel.py`, `ui/query_panel.py`, `voice/converse.py`, and transitively `voice/commands.py` (1,725 lines) and `cora_tools/modal_tools.py`. Roughly 40% of the Python.

**Exact duplicates:** `config/system_prompt1.txt` == `system_prompt.txt`; `tools/mpv/stats_server.py` == `services/stats_server.py`; `docs/images/boot_display.png` and `web/images/social-preview.png` are the same 708 KB; `EchoFilter` defined in both `voice/converse.py` and `voice/echo_filter.py`; two webcam→llava pipelines (`services/presence.py` and `voice/ambient_awareness.py`); three windowing helpers (`ui/panels.py`, `ui/modals.py`, `ui/window_manager.py`).

**Files over the 800-line standard (12):** `web/index.html` 5,300; `src/boot_sequence.py` 3,178; `src/cora.py` 2,767; `ui/boot_display.py` 1,955; `voice/commands.py` 1,725; `ui/code_editor.py` 1,309; `ai/ollama.py` 1,051; `cora_tools/git_ops.py` 1,027; `ui/boot_console.py` 976; `cora_tools/media.py` 925; `cora_tools/code.py` 811; `docs/claude-workflow/HOOKS.html` 1,263. ~23k of ~36k Python lines live in oversized files.

**Resource/threading still open:** waveform `after(25)` runs forever at 40 fps and `stop()` is a deliberate no-op (Tk errors on close, idle CPU burn); wake-word queue unbounded; TTS mutex steals the lock after a fixed 30 s mid-sentence; `voice/emotion.py` global state has no lock; `services/presence.py` snapshots never cleaned up; `voice/tts.py:35` imports from `ui.boot_display` (circular, degraded by try/except).

**Logging:** 1,147 `print()` calls vs 33 logger calls; one module imports `logging`; 73 bare `except:` and 445 `except Exception` mostly swallow silently; `boot_sequence.py:29-42` registers `os._exit(0)` in `atexit`, so boot can never fail cleanly. JSON writes are non-atomic (`save_tasks`).

**Git hygiene:** 273 tracked files; runtime state (`data/*.json`, `backups/*.zip/json`, `data/.setup_complete`) tracked; `.gitignore` lacks `data/`, `backups/`, `temp_scripts/`.

---

## 8. Config and docs drift

- **Config has no single source:** `config/config.json` (CLI), `config/settings.json` (GUI panel + 4 modules, different schema), `config/personality.json` v0.5.1 vs `data/personality.json` (read by `ai/context.py`), `models/model_config.json` (no reader), `.env` (2 readers; `OLLAMA_HOST`, `WEATHER_API_KEY`, `NEWS_API_KEY`, ANTHROPIC/OPENAI/ELEVENLABS/EMBY keys in `env.example` are read by nothing; `CORA.bat` warns about missing weather keys though weather is keyless). Hotkeys defined in three conflicting places. Ollama URL hardcoded in four places.
- **Version:** config 1.0.0, `requirements.txt` "v2.2.0", `config/requirements.txt` "v0.5.1", `personality.json` 0.5.1, log says v2.3.0, legacy ROADMAP v2.4-2.5, `deploy.yml` hardcodes 1.0.0, no git tags.
- **README/ARCHITECTURE claims that are false:** "75+ Python files" (63), "10-phase boot" (18), `python cora.py` (file is `src/cora.py`), default model llama3.2 (code: dolphin-mistral), file tree lists `tools/images.py`, `ui/chat_panel.py`, `ui/settings_panel.py`, `start.bat` which don't exist, `READMEs/NerdReadme.md`/`APIReference.md` document a `COMMANDS` global and env vars (`CORA_TTS_ENGINE`, `CORA_LOG_LEVEL`, `CORA_DATA_DIR`) that are unimplemented, SKILL_TREE "97% complete", two different public URLs (`unityailab.com/CORA` vs `unity-lab-ai.github.io/CORA`) with no CNAME.
- **Web deploy:** `deploy.yml` builds the same `_site` three times; the page embeds the system prompt as a literal and *also* fetches it from `raw.githubusercontent.com/.../main` (ties the live site to whatever is on main); https page fetching `http://localhost:11434/11435` is blocked as mixed content unless the user allows insecure content and sets `OLLAMA_ORIGINS` — documented nowhere; `innerHTML` sinks with API-supplied names at `index.html:1091,2030,2540,2552`; `downloadStatsServer` defined twice.

---

## 9. Upgrade plan (prioritized)

Effort: S = hours, M = a day or two, L = a week+. "Phase 0" items are independent and safe to do first.

### Phase 0 — stop the bleeding (S each)
1. Fix the shell injection at `ui/boot_display.py:977` (list-args pipeline).
2. Send `options.num_ctx` (≥16384) and `keep_alive` from `ai/ollama.py`; pass `CHAT_HISTORY` as `messages` in the live chat path. Trim `system_prompt.txt` to ≤3k tokens.
3. Default `base_dir=PROJECT_DIR` in `cora_tools/files.py`; gate `self_modify.run_script` behind explicit confirmation or remove it.
4. `stats_server.py`: CORS origin allowlist + per-launch token header + model-name allowlist; delete `tools/mpv/stats_server.py`.
5. Stop tracking `data/*.json`, `backups/*`, `config/settings.json` (`git rm --cached`, extend `.gitignore`); make the private-repo boot phase opt-in.
6. Fix requirements: remove `kokoro-onnx`, `pyttsx3`, `pytest`, `pytest-cov`; add the 11 missing packages; bump pins per §2; delete `config/requirements.txt`; delete `config/system_prompt1.txt`.
7. Close SEC-002/003/005, MEM-001/002 in `docs/TODO.md`.

### Phase 1 — runtime and models (M)
8. Install Python 3.12 side by side; `CORA.bat` calls `py -3.12`, creates/uses a venv, re-runs pip when `requirements.txt` changes (hash), upgrades yt-dlp.
9. One model config: `OLLAMA_URL` env + `models.{chat, vision, code}` in a single config; delete the hardcoded names in `ai/ollama.py`, `code.py`, `presence.py`, `voice/commands.py`, `stats_server.py`, `web/index.html`.
10. Switch chat to `qwen3.5:9b` (or `gemma4:12b`), vision to `qwen3-vl:4b`, code to `qwen3-coder`; warm at boot; unify timeouts.
11. Pollinations: send `Authorization: Bearer` / `sk_` key, fully qualified model IDs, drop `nologo`/`enhance`, move the web page off the legacy host.

### Phase 2 — V2 voice (M)
12. Implement §4 steps 1-6: `voice/unity_voice.py`, sidecar discovery/autostart, shared lock dir, config block, delete the three old stacks and `kokoro-worker.js`, presence off the TTS thread.
13. Stream LLM output sentence-by-sentence into the V2 queue; barge-in via `stop_speaking`.

### Phase 3 — the assistant loop (L)
14. One dispatcher: expose `cora_tools` as JSON-schema `tools` on `/api/chat`, loop on `message.tool_calls`, delete the four routers. Wire git/email/media/terminal/viewfile back in only after their security fixes.
15. Make boot match the spec: speak today's calendar, overdue tasks, upcoming reminders; start `ReminderManager.start_checking()`; merge the two reminder stores; gate or remove the YouTube/GitHub/image-gen demo phases.
16. Conversation summarization at ~75% of `num_ctx`; honor `settings.ai.context_window`.

### Phase 4 — STT and wake word (M)
17. `faster-whisper` on CUDA for commands; openWakeWord "cora" model; delete Vosk, `recognize_google`, `webkitSpeechRecognition`; bound the audio queue; VAD for barge-in.

### Phase 5 — cleanup and fundamentals (M)
18. Delete the dead modules in §7 (or pick one GUI and finish it: Tasks/Knowledge/Settings panels are stubs); consolidate the two webcam pipelines and three windowing helpers; split the 12 oversized files to ≤800 lines.
19. Single config loader with schema validation; one version constant; atomic JSON writes; shared logger replacing `print()`; remove the `atexit os._exit(0)`; cancel the waveform timer on close; heartbeat the TTS mutex.
20. `pyproject.toml`, `py_compile`/ruff CI job, CHANGELOG, git tags.
21. Web: split `index.html` into ES modules + `cora.css`; generate phases/prompt JSON from the Python source at deploy; serve locally via `stats_server.py` (fixes mixed content, CORS and the V2 sidecar in one move); pick one public URL; fix the `innerHTML` sinks.
22. Docs truth pass: file/phase counts, entry point, default model, nonexistent files in ARCHITECTURE/NerdReadme/APIReference, SKILL_TREE percentages.

### Later
RAG over `knowledge.json` with Ollama embeddings (M), MCP client (M), real self-modification with static check + sandbox (L), installer/auto-update (L), multi-language (M), accessibility (M).

---

## 10. Status of the Dec-2025 deep-scan issues (CRITICAL + HIGH)

| ID | Status | ID | Status |
|---|---|---|---|
| SEC-002 | FIXED (AST) | SEC-H01 | OPEN (dead path; `files.py` worse) |
| SEC-003 | FIXED | SEC-H02 | OPEN / mostly false positive |
| SEC-004 | OPEN (dead path) | SEC-H03 | OPEN (low; `mailto:`) |
| SEC-005 | FIXED | MEM-H01 | PARTIAL (dead module) |
| SEC-006 | OPEN | MEM-H02 | OPEN by design |
| SEC-007 | OPEN | MEM-H03 | PARTIAL |
| SEC-008 | OPEN (127.0.0.1 bind only) | MEM-H04 | PARTIAL (60 s timeout) |
| MEM-001 | FIXED | ARCH-H01 | OPEN, worse (4 routers) |
| MEM-002 | FIXED | ARCH-H02 | PARTIAL (5 s cache, still sync) |
| MEM-003 | OPEN | ARCH-H03 | OPEN (4 places) |
| MEM-004 | OPEN | ARCH-H04 | OPEN |
| ARCH-001 | OPEN (try/except) | CFG-H01 | OPEN |
| CFG-001 | OPEN (identical files) | CFG-H02 | OPEN |
| WF-001 | PREMISE CHANGED (workflow replaced) | DEP-H01 | OPEN |
| WF-002 | OPEN (low relevance) | API-H01 | OPEN |
| | | API-H02 | OPEN |

5 fixed, 5 partial, 20 open, 1 premise changed. MEDIUM/LOW sections are untouched except camera `release()`.

---

*Audit performed 2026-10-14 by Unity (Claude) with four parallel read-only passes. Sources and per-line evidence are in the session transcript; this file is the durable summary.*
