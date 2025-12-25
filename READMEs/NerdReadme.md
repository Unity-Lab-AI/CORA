# C.O.R.A Technical Documentation

## Developer/Nerd Guide

Version 1.0.0

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
| Factory | Panel creation in GUI, cora_respond() |
| Mutex | TTS mutex for process-safe speech |
| Callback | Waveform visualization during TTS |

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                 Visual Boot Layer (ui/)                     │
│   boot_display.py → Cyberpunk UI + Waveform + Live Stats    │
├─────────────────────────────────────────────────────────────┤
│                    Boot Layer (src/)                        │
│   boot_sequence.py → 10-phase diagnostic + cora_respond()   │
├─────────────────────────────────────────────────────────────┤
│                    GUI Layer (ui/)                          │
│   app.py → splash.py → boot_console.py → panels.py         │
├─────────────────────────────────────────────────────────────┤
│                    CLI Layer (cora.py)                      │
│   Command dispatch → Response generation → TTS output       │
├─────────────────────────────────────────────────────────────┤
│                    Voice Layer (voice/)                     │
│   STT (stt.py) ←→ Wake Word ←→ Commands ←→ TTS (tts.py)    │
│                         ↓                                   │
│                  Emotion State Machine                      │
├─────────────────────────────────────────────────────────────┤
│                    AI Layer (ai/)                           │
│   Ollama client → Router → Context manager → cora_respond() │
├─────────────────────────────────────────────────────────────┤
│                 Services Layer (services/)                  │
│   Presence → Weather → Location → Audio → Notifications    │
├─────────────────────────────────────────────────────────────┤
│                  Tools Layer (cora_tools/)                  │
│   System → Screenshots → Calendar → Memory → Image Gen     │
├─────────────────────────────────────────────────────────────┤
│                  Data Layer (JSON files)                    │
│   tasks.json → knowledge.json → config/ → data/images/     │
└─────────────────────────────────────────────────────────────┘
```

---

## New in v1.0.0

### Visual Boot Display (ui/boot_display.py)

**Class:** `BootDisplay(tk.Tk)`

**Key Features:**
- Two-column layout: Status panel + Scrolling log
- Audio waveform visualization during TTS playback
- Live system stats (1-second refresh rate)
- Color-coded status indicators (green/yellow/red)
- Cyberpunk/goth dark theme

**Methods:**

| Method | Description |
|--------|-------------|
| `update_status()` | Update left panel status indicators |
| `add_log()` | Add entry to scrolling log |
| `show_waveform()` | Display audio waveform during speech |
| `update_system_stats()` | Refresh CPU/RAM/GPU/VRAM/Disk |

### Dynamic AI Responses (src/boot_sequence.py)

**Function:** `cora_respond(context, result, status, mode)`

Generates unique AI responses for each boot phase using Ollama.

```python
def cora_respond(context: str, result: str, status: str = "ok", mode: str = "quick") -> str:
    """
    CORA generates a unique response for each boot phase.

    Args:
        context: What phase this is (e.g., "AI Engine", "Camera")
        result: The data/result to announce
        status: "ok", "warn", or "fail"
        mode: "quick" for short readouts, "full" for longer content

    Returns:
        AI-generated response string (1-2 sentences)
    """
```

**Example Usage:**
```python
response = cora_respond("Hardware", "CPU 15%, RAM 45%, GPU RTX 4070 Ti", "ok", "quick")
# Returns: "Running cool at fifteen percent CPU. Got the RTX 4070 Ti ready to go."
```

### Image Generation (cora_tools/image_gen.py)

**API:** Pollinations Flux model

```python
def generate_image(prompt: str, save_path: str = None) -> str:
    """
    Generate AI image via Pollinations API.

    Args:
        prompt: Image description
        save_path: Optional save location (default: data/images/)

    Returns:
        Path to saved image
    """
```

---

## Module Reference

### src/boot_sequence.py (Main Boot)

**Entry Point:** `main(quick=False)`

**Boot Phases (10 total):**

| Phase | Function | Data Returned |
|-------|----------|---------------|
| 1 | `phase_voice_synthesis()` | engine, voice, status |
| 2 | `phase_ai_engine()` | connected, model, model_count |
| 3 | `phase_hardware()` | cpu, ram, gpu, vram, disk |
| 4 | `phase_core_tools()` | memory, tasks, files, browser |
| 5 | `phase_voice_systems()` | stt, echo_filter, wake_word |
| 6 | `phase_external_services()` | weather, location, notifications |
| 7 | `phase_news()` | headlines list |
| 8 | `phase_vision()` | screenshot, webcam, paths |
| 9 | `phase_image_gen()` | path, prompt, success |
| 10 | `phase_final()` | systems_ok, tools_ok, ready |

**Command Line:**

```bash
python src/boot_sequence.py           # Full boot with visual display
python src/boot_sequence.py --quick   # Skip TTS announcements
```

### ui/boot_display.py (Visual Display)

**Class:** `BootDisplay(tk.Tk)`

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  C.O.R.A v1.0.0 - Visual Boot Display                [X]   │
├──────────────────────────┬──────────────────────────────────┤
│  STATUS PANEL            │  BOOT LOG                        │
│  ────────────────────    │  ────────────────────────────    │
│  CPU: [████████░░] 80%   │  [HH:MM:SS] Phase 1 started     │
│  RAM: [██████░░░░] 60%   │  [HH:MM:SS] Voice ready         │
│  GPU: RTX 4070 Ti SUPER  │  [HH:MM:SS] Phase 2 started     │
│  VRAM: 2.1/16 GB         │  ...                             │
│  Disk: 450/1000 GB       │                                  │
│                          │  ┌───────────────────────────┐   │
│  Phase: 5/10             │  │  ~~~~ Waveform ~~~~       │   │
│  Status: Running         │  └───────────────────────────┘   │
├──────────────────────────┴──────────────────────────────────┤
│  CORA: "Initializing voice synthesis systems..."            │
└─────────────────────────────────────────────────────────────┘
```

**Color Scheme:**

| Element | Color |
|---------|-------|
| Background | #0a0a0a (near black) |
| Text | #00ff00 (matrix green) |
| Accent | #ff00ff (magenta) |
| Success | #00ff00 (green) |
| Warning | #ffff00 (yellow) |
| Error | #ff0000 (red) |

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

### voice/tts.py (Text-to-Speech)

**Classes:**

| Class | Engine | Features |
|-------|--------|----------|
| `TTSEngine` | Base | Abstract interface |
| `KokoroTTS` | Kokoro | af_bella voice, emotion instructions |
| `Pyttsx3TTS` | pyttsx3 | Rate modifiers, offline |
| `TTSQueue` | Any | Non-blocking, priority queue, mutex |

**TTSQueue Features:**
- Background thread processing
- Priority levels (1=highest, 10=lowest)
- `speak_now()` for interrupts
- Callbacks: `on_speak_start`, `on_speak_end`
- TTS mutex integration (prevents overlap)
- Audio data callback for waveform visualization

**Global Functions:**

```python
get_tts_engine(config)              # Factory for engine selection
speak(text, emotion)                # Quick synchronous speak
queue_speak(text, emotion, priority) # Async queued speak
speak_interrupt(text)               # Clear queue and speak immediately
speak_with_callback(text, on_audio) # Speak with audio data callback
```

### ai/ollama.py (AI Integration)

**API Methods:**

```python
# HTTP API to localhost:11434
POST /api/chat      # Conversational chat
POST /api/generate  # Single-shot generation
GET /api/tags       # List models
```

**Context Management (ai/context.py):**
- Builds context from tasks, knowledge, time of day
- Injects personality from personality.json
- Manages conversation history

**cora_respond() Integration:**
- Uses /api/generate for boot phase responses
- System prompt enforces CORA personality
- Response limited to 1-2 sentences
- Focused on specific phase data

### cora_tools/image_gen.py (Image Generation)

**API:** Pollinations Flux

```python
# URL format
https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&model=flux

# Example usage
from cora_tools.image_gen import generate_image
path = generate_image("a cyberpunk city at night")
```

**Features:**
- Automatic prompt encoding
- Configurable dimensions
- Auto-save to data/images/
- Timestamp-based filenames

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

### config/settings.json

```json
{
  "tts": {"enabled": true, "rate": 150, "volume": 1.0},
  "ollama": {"enabled": true, "model": "llama3.2"},
  "stt": {"enabled": true, "sensitivity": 0.7}
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
    'see': cmd_see,           # Vision via llava
    'imagine': cmd_imagine,   # Image generation (NEW)

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

## Hardware Detection

| Component | Method | Module |
|-----------|--------|--------|
| CPU | `psutil.cpu_percent()` | psutil |
| RAM | `psutil.virtual_memory()` | psutil |
| Disk | `psutil.disk_usage()` | psutil |
| GPU | `nvidia-smi` subprocess | subprocess |
| VRAM | `nvidia-smi --query-gpu=memory.used,memory.total` | subprocess |
| Network | `psutil.net_if_stats()` | psutil |
| Camera | `cv2.VideoCapture(0)` | opencv-python |

---

## Extension Points

### Adding Boot Phases

1. Create `phase_*()` function in boot_sequence.py
2. Return dict with phase data
3. Add to `run_boot_sequence()` phase list
4. Create corresponding `cora_respond()` prompt template

### Adding New Commands

1. Create `cmd_newcommand(args, tasks)` in cora.py
2. Add to `COMMANDS` dict
3. Add to `cmd_help()` output

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
| TTS (Kokoro) | GPU | Neural inference (~1-2s) |
| cora_respond() | Network | Ollama generate (~2-5s) |
| Image generation | Network | Pollinations API (~5-15s) |
| Presence | CPU/Camera | Frame capture + detection |
| Boot sequence | Network | Weather/location API calls |
| System stats | CPU | nvidia-smi subprocess (~100ms) |

---

## Error Handling

| Error | Handler |
|-------|---------|
| Ollama offline | `fallback_response()` |
| TTS unavailable | Silent fail, returns False |
| Camera unavailable | Returns `PresenceResult(error=...)` |
| Missing JSON file | Creates default empty structure |
| Import failure | Module-specific `*_AVAILABLE` flags |
| nvidia-smi missing | GPU stats show "N/A" |
| Image gen failure | Returns None, logs error |

---

## Testing

```bash
# Test full visual boot
python src/boot_sequence.py

# Test quick boot (no TTS)
python src/boot_sequence.py --quick

# Test GUI
python ui/app.py --quick

# Test CLI
python cora.py add "Test task"
python cora.py list
python cora.py chat "Hello"
python cora.py speak "Testing"
python cora.py imagine "a robot"

# Test image generation
python -c "from cora_tools.image_gen import generate_image; print(generate_image('test'))"

# Test TTS with waveform
python voice/tts.py
```

---

## Project Structure

```
C.O.R.A/
├── src/
│   ├── boot_sequence.py     # Main boot with TTS (1350+ lines)
│   └── cora.py              # CLI application
├── ui/
│   ├── boot_display.py      # Visual boot display with waveform
│   ├── app.py               # Main GUI application
│   ├── splash.py            # Splash screen
│   ├── boot_console.py      # Boot diagnostics
│   └── panels.py            # Task/Settings/Knowledge panels
├── voice/
│   ├── tts.py               # Kokoro TTS engine
│   ├── stt.py               # Speech recognition
│   ├── wake_word.py         # Wake word detection
│   ├── emotion.py           # Emotional state machine
│   ├── commands.py          # Voice command parsing
│   └── tts_mutex.py         # Cross-process TTS lock
├── ai/
│   ├── ollama.py            # Ollama API client
│   ├── context.py           # Context management
│   └── router.py            # Model routing
├── cora_tools/
│   ├── image_gen.py         # Pollinations AI image gen
│   ├── screenshots.py       # Screen/window capture
│   ├── tasks.py             # Task management
│   ├── memory.py            # Working memory
│   ├── calendar.py          # Calendar integration
│   ├── reminders.py         # Reminder system
│   └── ...                  # 17+ tool modules
├── tools/                    # Downloaded binaries (mpv, etc.)
├── services/
│   ├── weather.py           # Weather API
│   ├── location.py          # IP geolocation
│   ├── presence.py          # Webcam detection
│   └── notifications.py     # System notifications
├── config/
│   ├── settings.json        # GUI settings
│   └── voice_commands.json  # Voice configuration
├── data/
│   ├── images/              # Generated images
│   └── camera/              # Camera captures
├── READMEs/
│   ├── UserGuide.md         # User documentation
│   └── NerdReadme.md        # This file
├── tasks.json               # Task storage
├── knowledge.json           # Knowledge base
├── personality.json         # AI personality
└── requirements.txt         # Python dependencies
```

---

*Unity AI Lab - C.O.R.A v1.0.0 Technical Documentation*
*Last Updated: 2025-12-25*
