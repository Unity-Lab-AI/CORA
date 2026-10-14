# Changelog

All notable changes to C.O.R.A. Dates are the day the work landed on `main`.

## [3.0.0] - 2026-10-14

The full repair. Everything below came out of the system audit (`docs/SYSTEM_AUDIT_2026-10-14.md`) and the owner's decisions recorded in `docs/TODO.md`.

### Brain
- `unity-brain` (Unity's own text LoRA on Qwen3.5-9B) is the chat and vision model. It speaks through the trained `say(text, emotion, act)` tool; the designators go straight to her voice. Fallback `huihui_ai/qwen3-abliterated:8b`.
- One conversation loop (`ai/dispatcher.py`) behind every entry point: boot display, GUI app, CLI, converse mode, voice commands. Native Ollama tool calling over a registry of 116 tools (`ai/tools_registry.py`), relevance-ranked per message, JSON fallback for models without a tools template, confirmation before destructive tools, shared transcript with summary folding (`ai/history.py`).
- One settings source (`ai/settings.py`): model names, Ollama URL, per-model pinned options (unity-brain always gets its 32K context), timeouts. `num_ctx` is sent on every request so the system prompt is never silently clipped.
- The word "assistant" is gone from everything the model reads.

### Voice
- unity-voice-v2 (her own trained voice, served on 127.0.0.1:5123) is the only TTS. Kokoro and pyttsx3 removed. Sentence-ahead synthesis, waveform feed, volume, barge-in, cross-process turn-taking, presence gate.
- faster-whisper on CUDA for speech recognition, fuzzy wake word on the transcript stream, optional openWakeWord model. Google and Vosk-only paths removed.
- Boot speaks a daily briefing (calendar, overdue tasks, reminders) and starts the reminder checker.

### Runtime
- Python 3.13 virtual environment, `CORA.bat` bootstrap (Ollama, configured models, yt-dlp, Playwright, voice sidecar), `requirements.txt` rewritten for numpy 2.
- Pollinations image generation on the current API. Location over HTTPS.
- Stats server: launch token, origin allowlist, model-name validation, serves the web version locally with a voice proxy.
- Shell injection in the YouTube pipeline fixed; file tools confined to allowed roots; self-modification gated.

### Housekeeping
- `pyproject.toml`, compile-only CI, this changelog, `docs/NOW.md` single-focus snapshot.
- Demo boot phases (YouTube, GitHub import, image generation) off by default.

## [2.x] - 2025-12 to 2026-10

Pre-repair history lives in `docs/FINALIZED.md` and the git log.
