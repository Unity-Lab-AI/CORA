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

## Where things stand (2026-10-14, end of the repair day)

**Delivered:** the full repair, `docs/TODO.md` UPG-001 through UPG-045, all closed. Version 3.0.0 is tagged; main + develop are pushed to origin (Forgejo) and github after every phase. The two-minute cron that drove the day is stopped. The user's last instructions were "do both, go" (the web split and the oversized-file split, both done) and "wehn u are done, write the now.md file and kill the cron" (this file, and the cron is cancelled).

**What CORA is now, in one breath:** `unity-brain` (Unity's own LoRA) as brain and eyes, `unity-voice-v2` as her voice, faster-whisper as her ears, one conversation loop (`ai/dispatcher.py`) behind every entry point with 115 tools, a timeout-guarded camera layer, browser-backed web search and page fetch, config loader + daily log, models unloaded from the GPU on every exit, start/stop scripts for Windows and Linux, the web page served locally with her voice, docs that tell the truth, and no source file over 800 lines.

**Last verified runs (all on 2026-10-14):**
- Full boot with voice: runs 4 and 5, 13/13 systems.
- Silent boot (`--quick`) of the phased entry point after the splits: run 7, 12/12 systems (voice skipped by the flag), every phase to BOOT COMPLETE, GPU released after (9886 MiB -> 2375 MiB).
- Web page split (13 ordered scripts + css): headless load through the stats server, 0 page errors.
- Every split module verified against its original: names, signatures, command tables, singletons, paths.

**Tools that now live in `scripts/`:** `split_web.py`, `split_module.py`, `split_class.py`, `split_function.py`, `move_main.py`, `analyze_function.py`, `gpu_release.py`, `bootstrap.py`.

**Rules that bind every later session (learned today):**
- Checks never write to her real data: `CORA_HISTORY_FILE` scratch transcript, `handle(..., allowed_tools=...)` read-only set.
- Checks never make sound: `--quick` for the boot, `speak=False` for the dispatcher; never launch the GUI or CLI for a check.
- Unload the GPU after anything that touched her brain: `python scripts/gpu_release.py` (CORA does it herself on every normal exit).
- The user's words go into TODO / FINALIZED verbatim.

**Open, for whoever picks this up next:** `web/js/06-boot-sequence-exact-match-to.js` is one 1102-line function and was left whole (documented, UPG-021 b); the phase module names in `src/boot_phases/` carry the banner text (`phase_10_phase_4_1_...`), ugly but exact; the sidecar for her voice is shared with the stream rig and only killed by the stop scripts when CORA started it.

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
