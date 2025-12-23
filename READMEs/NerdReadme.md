# C.O.R.A Technical Documentation

## Developer/Nerd Guide

Version 2.2.0

---

## Architecture Overview

### Design Patterns

| Pattern | Implementation |
|---------|---------------|
| Singleton | CONFIG global, TTSQueue, EmotionalState |
| Command | Command dispatch table (COMMANDS dict) |
| Strategy | TTS engine selection (Kokoro/pyttsx3) |
| Observer | Chat history, emotional event tracking |
| State Machine | EmotionalState with mood decay |
| Factory | Panel creation in GUI |
| Mutex | TTS mutex for process-safe speech |

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    GUI Layer (ui/)                           │
│   app.py → splash.py → boot_console.py → panels.py          │
├─────────────────────────────────────────────────────────────┤
│                    CLI Layer (cora.py)                       │
│   Command dispatch → Response generation → TTS output        │
├─────────────────────────────────────────────────────────────┤
│                    Voice Layer (voice/)                      │
│   STT (stt.py) ←→ Wake Word ←→ Commands ←→ TTS (tts.py)     │
│                         ↓                                    │
│                  Emotion State Machine                       │
├─────────────────────────────────────────────────────────────┤
│                    AI Layer (ai/)                            │
│   Ollama client → Router → Context manager                   │
├─────────────────────────────────────────────────────────────┤
│                 Services Layer (services/)                   │
│   Presence → Weather → Location → Audio → Hotkeys           │
├─────────────────────────────────────────────────────────────┤
│                   Tools Layer (tools/)                       │
│   System → Screenshots → Calendar → Memory → Reminders      │
├─────────────────────────────────────────────────────────────┤
│                  Data Layer (JSON files)                     │
│   tasks.json → knowledge.json → config/ → personality.json  │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Reference

### ui/app.py (Main GUI)

**Class:** `CoraApp(ctk.CTk)`

**Key Methods:**

| Method | Description |
|--------|-------------|
| `__init__()` | Window setup, grid config, panel init |
| `_create_sidebar()` | Navigation buttons, theme toggle |
| `_create_main_content()` | Chat display, input field, voice button |
| `_create_status_bar()` | Status label, camera indicator |
| `_process_command()` | Background thread command execution |
| `_check_presence()` | Webcam presence detection |
| `_voice_input()` | STT recording and processing |
| `_show_*()` | Panel switching methods |

**Entry Points:**

```python
main(skip_splash=False)  # Full boot with optional splash
main_quick()              # No splash, quick boot
```

**Command Line:**

```bash
python ui/app.py --no-splash  # Skip splash screen
python ui/app.py --quick      # Quick boot alias
```

---

### ui/splash.py (Splash Screen)

**Classes:**

| Class | Description |
|-------|-------------|
| `SplashScreen` | Fullscreen animated splash with progress |
| `MinimalSplash` | Quick 1-second logo flash |

**Key Features:**
- ASCII art logo with Matrix green color
- Animated progress bar
- Boot status messages
- Fade-out effect on completion
- Skip with ESC/SPACE/ENTER

```python
show_splash(master, fullscreen=True, duration=3.0, on_complete=callback)
```

---

### ui/boot_console.py (Boot Diagnostics)

**Classes:**

| Class | Description |
|-------|-------------|
| `BootCheck` | Single boot check with TTS summary |
| `BootConsole` | Full boot sequence runner |

**Boot Checks (13 total):**

| Check | Data Returned | TTS Style |
|-------|---------------|-----------|
| System Time | hour, day, time | Time-of-day aware |
| Location | city, region, country | Geolocation phrases |
| Weather | conditions string | Atmospheric terminology |
| Calendar | event count, summaries | Schedule-aware |
| Tasks | pending, overdue counts | Priority-aware |
| Ollama | connected, model count | Neural/cognitive phrases |
| TTS | available, engine name | Engine-specific |
| System | CPU%, RAM%, used | Load-aware thresholds |
| GPU | name, VRAM | NVIDIA nvidia-smi |
| Disk | free_gb, total_gb | Storage phrases |
| Network | connected, latency_ms | Connection status |
| Microphone | count, device names | Input device status |
| Webcam | available, resolution | Visual input status |

**TTS Variations:**
All TTS functions use `random.choice()` for varied responses. Each function has 3-5 variations per status (success/failure/edge cases).

---

### ui/panels.py (GUI Panels)

**Classes:**

| Class | Purpose |
|-------|---------|
| `BasePanel` | Base class with grid config |
| `ChatPanel` | Chat display + input (unused in current app.py) |
| `TasksPanel` | Scrollable task list with checkboxes |
| `SettingsPanel` | TTS/Ollama/STT settings with save/load |
| `KnowledgePanel` | Knowledge entries with tag search |

**SettingsPanel Persistence:**

```python
# Saves to: config/settings.json
{
  "tts": {"enabled": bool, "rate": int, "volume": float},
  "ollama": {"enabled": bool, "model": str},
  "stt": {"enabled": bool, "sensitivity": float}
}
```

---

### voice/tts.py (Text-to-Speech)

**Classes:**

| Class | Engine | Features |
|-------|--------|----------|
| `TTSEngine` | Base | Abstract interface |
| `KokoroTTS` | Kokoro | Emotion instructions, high-quality |
| `Pyttsx3TTS` | pyttsx3 | Rate modifiers, offline |
| `TTSQueue` | Any | Non-blocking, priority queue, mutex |

**TTSQueue Features:**
- Background thread processing
- Priority levels (1=highest, 10=lowest)
- `speak_now()` for interrupts
- Callbacks: `on_speak_start`, `on_speak_end`
- TTS mutex integration (prevents overlap)

**Global Functions:**

```python
get_tts_engine(config)    # Factory for engine selection
speak(text, emotion)       # Quick synchronous speak
queue_speak(text, emotion, priority)  # Async queued speak
speak_interrupt(text)      # Clear queue and speak immediately
```

---

### voice/emotion.py (Emotional State)

**Class:** `EmotionalState`

**Emotions:**
- excited, concerned, satisfied, annoyed, sarcastic
- caring, playful, urgent, neutral

**State Machine:**

```python
# Singleton access
state = get_emotional_state()
state.apply_event('task_completed')  # +0.2 satisfaction
state.apply_event('error')           # +0.3 frustration
state.decay(0.1)                     # Natural decay toward neutral

mood = state.get_mood()              # Returns dominant emotion
intensity = state.get_intensity()    # 0.0 - 1.0
```

**Mood Decay:**
- Automatic decay toward neutral over time
- Events push mood in specific directions
- Intensity threshold for mood expression

---

### voice/commands.py (Voice Commands)

**Configuration:** `config/voice_commands.json`

```json
{
  "enabled": true,
  "wake_words": ["cora", "hey cora", "yo cora"],
  "confidence_threshold": 0.7,
  "commands": {
    "time": {"enabled": true, "aliases": ["clock"]},
    "weather": {"enabled": true, "aliases": ["forecast"]}
  }
}
```

**Functions:**

```python
load_voice_config()           # Load JSON config
is_command_enabled(name)      # Check if command active
get_wake_words()              # List wake words
parse_voice_input(text)       # Extract command from speech
execute_command(cmd, args)    # Run command handler
```

---

### voice/tts_mutex.py (Speech Overlap Prevention)

**Purpose:** Prevents multiple processes from speaking simultaneously.

```python
mutex = get_mutex("CORA")
with mutex.locked(timeout=10) as acquired:
    if acquired:
        engine.speak(text)
```

Uses file-based locking on Windows for cross-process synchronization.

---

### services/presence.py (Webcam Detection)

**Functions:**

```python
check_human_present() -> PresenceResult
# Returns: PresenceResult(present, confidence, error)

capture_webcam() -> bytes | None
# Returns: JPEG image bytes or None
```

Uses OpenCV for face detection with Haar cascades.

---

### ai/ollama.py (AI Integration)

**API Methods:**

```python
# HTTP API to localhost:11434
POST /api/chat
POST /api/generate
GET /api/tags  # List models
```

**Context Management (ai/context.py):**
- Builds context from tasks, knowledge, time of day
- Injects personality from personality.json
- Manages conversation history

---

## Data Schemas

### tasks.json

```json
{
  "counter": 42,
  "tasks": [
    {
      "id": "T042",
      "text": "Task description",
      "status": "pending|active|done",
      "priority": 5,
      "created": "2025-12-23T10:00:00",
      "due": "2025-12-25",
      "notes": [{"text": "Note", "created": "..."}],
      "completed": "2025-12-24T15:00:00"
    }
  ]
}
```

### knowledge.json

```json
{
  "counter": 10,
  "entries": [
    {
      "id": "K010",
      "content": "Knowledge content",
      "tags": ["tag1", "tag2"],
      "created": "2025-12-23T10:00:00"
    }
  ]
}
```

### config/settings.json (GUI Settings)

```json
{
  "tts": {"enabled": true, "rate": 150, "volume": 1.0},
  "ollama": {"enabled": true, "model": "llama3.2"},
  "stt": {"enabled": true, "sensitivity": 0.7}
}
```

### config/voice_commands.json

```json
{
  "enabled": true,
  "wake_words": ["cora", "hey cora"],
  "confidence_threshold": 0.7,
  "commands": {...},
  "custom_responses": {...}
}
```

---

## Command Dispatch Table

```python
COMMANDS = {
    # Task management
    'add': cmd_add,
    'list': cmd_list, 'ls': cmd_list,
    'done': cmd_done, 'complete': cmd_done,
    'delete': cmd_delete, 'del': cmd_delete, 'rm': cmd_delete,
    'pri': cmd_pri, 'priority': cmd_pri,
    'due': cmd_due,
    'note': cmd_note,
    'edit': cmd_edit,
    'show': cmd_show,
    'search': cmd_search,
    'today': cmd_today,
    'undo': cmd_undo,

    # Knowledge
    'learn': cmd_learn,
    'recall': cmd_recall, 'kb': cmd_recall,

    # AI
    'chat': cmd_chat, 'ai': cmd_chat,
    'chathistory': cmd_chathistory,

    # Voice
    'speak': cmd_speak, 'say': cmd_speak,

    # Tools
    'time': cmd_time,
    'weather': cmd_weather,
    'screenshot': cmd_screenshot,
    'see': cmd_see,  # Vision via llava

    # Runtime tools
    'create_tool': cmd_create_tool,
    'modify_tool': cmd_modify_tool,
    'list_tools': cmd_list_tools,

    # System
    'settings': cmd_settings,
    'backup': cmd_backup,
    'help': cmd_help,
    'clear': cmd_clear,
}
```

---

## Extension Points

### Adding New Commands

1. Create `cmd_newcommand(args, tasks)` in cora.py
2. Add to `COMMANDS` dict
3. Add to `cmd_help()` output

### Adding Boot Checks

1. In `boot_console.py`, create `check_*()` and `tts_*()` functions
2. Add tuple to `create_default_boot_checks()` return list

### Adding TTS Engines

1. Create class extending `TTSEngine` in voice/tts.py
2. Implement `initialize()`, `speak()`, `get_audio()`
3. Add to `get_tts_engine()` factory

### Adding GUI Panels

1. Create class extending `BasePanel` in ui/panels.py
2. Add `_show_*()` method in ui/app.py
3. Add navigation button in sidebar

---

## Performance Notes

| Operation | Complexity | Bottleneck |
|-----------|------------|------------|
| Task load | O(n) | File I/O |
| Task search | O(n) | String matching |
| Chat | Network | Ollama API latency |
| TTS (pyttsx3) | CPU | Speech synthesis |
| TTS (Kokoro) | GPU | Neural inference |
| Presence | CPU/Camera | Frame capture + detection |
| Boot sequence | Network | Weather/location API calls |

---

## Error Handling

| Error | Handler |
|-------|---------|
| Ollama offline | `fallback_response()` |
| TTS unavailable | Silent fail, returns False |
| Camera unavailable | Returns `PresenceResult(error=...)` |
| Missing JSON file | Creates default empty structure |
| Import failure | Module-specific `*_AVAILABLE` flags |

---

## Testing

```bash
# Test GUI
python ui/app.py --quick

# Test CLI
python cora.py add "Test task"
python cora.py list
python cora.py chat "Hello"
python cora.py speak "Testing"

# Test boot sequence
python ui/boot_console.py

# Test splash
python ui/splash.py

# Test TTS
python voice/tts.py
```

---

*Unity AI Lab - C.O.R.A v2.2.0 Technical Documentation*
*Last Updated: 2025-12-23*
