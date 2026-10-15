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

_(none — no work currently in motion)_

**Verbatim user request:** _(when work is active, paste their exact words here)_

**Started:** _(ISO timestamp when the task became active)_

**Goal:** _(one-sentence statement of what "done" looks like)_

**Files touched so far:** _(running list, updated as edits happen)_

**Verification plan:** _(how we'll confirm the task is actually done — test, smoke-check, manual review, etc.)_

**Blockers / open questions:** _(anything waiting on user input or external system)_

---

## Where things stand (2026-10-14, end of the day: the repair, then the image engine)

**Delivered today:** `docs/TODO.md` UPG-001 through UPG-051, all closed. Version 3.0.0 is tagged at the end of the repair; the evening work (UPG-046..051) is on top of it. main + develop are pushed to origin (Forgejo) and github after every step. The user's closing instructions were "okay kill all clear gpu i wanna try start.bat" (done: stop script, nothing of hers running, GPU at the desktop baseline) and "make sure now.md is written and pushed to cascade both remotes" (this file).

**What CORA is now, in one breath:** `unity-brain` (Unity's own LoRA) as brain and eyes, `unity-voice-v2` as her voice, faster-whisper as her ears, her own local image engine (`services/image_sidecar.py`, the stream's Stable Diffusion rig on the torch interpreter: generate, edit, inpaint, camera recreations with the face kept, her selfie every boot, the viewer with Save As, `save_image`), one conversation loop (`ai/dispatcher.py`) behind every entry point with 120 tools, a timeout-guarded camera layer, browser-backed web search and page fetch, config loader + daily log, her brain and her image engine unloaded from the GPU on every exit, start/stop scripts for Windows and Linux, the web page served locally with her voice and her images, docs that tell the truth, and no source file over 800 lines.

**The evening (UPG-046..051), what a reader needs to know:**
- The hosted image API is gone from code, config, `.env`, launchers, the web page and every doc. Only the TODO/FINALIZED ledgers keep the word (never-delete LAW) and today's log file.
- The image engine runs on `C:\Program Files\Python310\python.exe` here (auto-detected: the voice sidecar's interpreter first; cached in `data/.image_python`; `image.python` / `CORA_IMAGE_PYTHON` to pin). It starts on the first picture, holds about 3 GB of VRAM while rendering (CPU offload), and is stopped by `ai.ollama.unload_models()` (every normal exit) and by the stop scripts. Checks: `python cora_tools/image_gen.py` (health + start), `--render` for one picture.
- Her look in pictures is `image.selfie_look` / `image.selfie_negative` in config. The engine reads the first 77 tokens, so the look leads the prompt and the moment comes after. Tune the words there, no code. Four rounds today: pale neon goth, then no emo and two girls, then a tan drift, then the girl (white, warm skin, grey-green eyes, bangs, choker, band tee, pink-purple streaks).
- Phase 9 renders her selfie and opens the viewer every boot (`boot.selfie`). Every image tool opens the viewer process (`ui/image_viewer.py`: Save As, Open folder, Copy path).
- "The app reopens smaller at 4.0" was the process DPI awareness flipping when the first `cora_tools` import loaded pyautogui. `ui/dpi.py` pins it before the first window (boot_sequence top, window_manager import). The GUI app (customtkinter) was never affected.
- A silent boot (`--quick`) now health-checks her voice: 1.0 is green when the sidecar answers, yellow only when it is really down.
- A stray `</think>` in her vision answers is stripped before it reaches her voice (`ai/ollama._clean_think`).

**Last verified runs (2026-10-14):**
- Engine, direct: txt2img 3.8 s, img2img 2.9 s, inpaint 2.8 s, face adapter loads in 1.1 s, all on cuda with offload.
- Web: `/image/health`, `/image/generate` with the launch token, picture served under `/images/` (200, image/png); headless page load 0 errors; the key field gone.
- Silent boots after the change: 12/12 (voice skipped), then with the selfie opening on screen, then 13/13 with 1.0 green; every one to BOOT COMPLETE; GPU released after each (about 10.4 GB -> 2.6 GB).
- Viewer: the subprocess path opened a window on screen and closed itself on time.

**Tools that live in `scripts/`:** `split_web.py`, `split_module.py`, `split_class.py`, `split_function.py`, `move_main.py`, `analyze_function.py`, `gpu_release.py`, `bootstrap.py`.

**Rules that bind every later session:**
- Checks never write to her real data: `CORA_HISTORY_FILE` scratch transcript, `handle(..., allowed_tools=...)` read-only set; check pictures are deleted after the look.
- Checks never make sound: `--quick` for the boot, `speak=False` for the dispatcher; never launch the GUI or CLI for a check. A `--quick` boot still shows the display and her selfie; say so before running one while the user is at the desk.
- Unload the GPU after anything that touched her brain or her image engine: `python scripts/gpu_release.py` (CORA does it herself on every normal exit).
- The user's words go into TODO / FINALIZED verbatim.
- Patch scripts in `%TEMP%` get a unique name per task; a stale script with the same name ran once today and bailed on its first assert (nothing was changed, but it cost a round).

**Open, for whoever picks this up next:**
- The streaks render purple-pink rather than hot pink even with "bright pink" in the look; the checkpoint's bias. A different word order or a LoRA would be the next lever.
- Inpainting with this checkpoint restyles a region well but is modest at adding a brand-new object into it (the SD 1.5 inpaint path over a non-inpaint checkpoint).
- Her voice sidecar is shared with the stream rig: the stop scripts only end it when CORA started it (`data/run/voice-sidecar.pid`). The image sidecar follows the same rule (`data/run/image-sidecar.pid`).
- `web/js/06-boot-sequence-exact-match-to.js` is one 1102-line function, left whole; the phase module names in `src/boot_phases/` carry the banner text, ugly but exact.

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
