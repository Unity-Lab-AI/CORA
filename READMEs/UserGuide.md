# C.O.R.A User Guide

## Cognitive Operations & Reasoning Assistant

Version 2.4.0

---

## Getting Started

### Starting CORA

**Visual Boot (Recommended):**
```bash
python src/boot_sequence.py
```
Full cyberpunk visual boot display with dynamic AI responses.

**GUI Mode:**
```bash
python gui_launcher.py
```
or
```bash
python ui/app.py
```

**Quick Boot (No TTS):**
```bash
python src/boot_sequence.py --quick
```

**CLI Mode:**
```bash
python cora.py
```

**Single Command Mode:**
```bash
python cora.py <command> [args]
```

---

## Boot Sequence

When CORA starts with visual boot, you'll see:

1. **Visual Boot Display** - Cyberpunk-themed window with two panels
2. **10-Phase Diagnostic** - Each phase with dynamic AI responses:

| Phase | Check | What Happens |
|-------|-------|--------------|
| 1 | Voice Synthesis | Kokoro TTS initialization |
| 2 | AI Engine | Ollama connection check |
| 3 | Hardware Check | CPU, RAM, GPU, VRAM stats |
| 4 | Core Tools | Memory, Tasks, Files, Browser |
| 5 | Voice Systems | STT, Echo Filter, Wake Word |
| 6 | External Services | Weather, Location, Notifications |
| 7 | News Headlines | Top 3 headlines from Google News |
| 8 | Vision Test | Screenshot & webcam capture |
| 9 | Image Generation | AI art via Pollinations Flux |
| 10 | Final Check | Summary & readiness status |

3. **Live System Stats** - Real-time CPU, RAM, GPU, VRAM, Disk monitoring
4. **Waveform Visualization** - Audio waveform during TTS playback

**CORA generates unique responses for each phase using Ollama AI.**

---

## Visual Boot Display

```
┌────────────────────────────────────────────────────────────────┐
│  C.O.R.A v2.4.0 - Visual Boot Display                          │
├──────────────────────────┬─────────────────────────────────────┤
│  STATUS PANEL            │  BOOT LOG                           │
│                          │                                     │
│  CPU: 15%                │  [10:30:45] Voice synthesis ready   │
│  RAM: 45%                │  [10:30:46] AI engine connected     │
│  GPU: RTX 4070 Ti        │  [10:30:47] Hardware check passed   │
│  VRAM: 2.1/16 GB         │  [10:30:48] All systems online      │
│  Disk: 450/1000 GB       │                                     │
│                          │  ~~~ Waveform Visualization ~~~     │
│  Phase: 10/10            │                                     │
├──────────────────────────┴─────────────────────────────────────┤
│  CORA: "All systems operational. Ready to assist!"             │
└────────────────────────────────────────────────────────────────┘
```

Features:
- Two-column layout: Status panel + Scrolling log
- Audio waveform visualization during speech
- Color-coded status indicators (green/yellow/red)
- Live updating system stats panel
- Cyberpunk/goth dark theme

---

## GUI Interface

### Main Window

| Area | Function |
|------|----------|
| **Sidebar** | Navigation buttons (Chat, Tasks, Knowledge, Settings) |
| **Main Panel** | Active view content |
| **Status Bar** | Status messages, camera indicator |
| **Theme Toggle** | Switch Dark/Light mode |

### Navigation

- **Chat** - Main command interface
- **Tasks** - Visual task list with checkboxes
- **Knowledge** - Browse knowledge entries by tag
- **Settings** - Configure TTS, Ollama, voice input

### Input Methods

1. **Text** - Type in the input field, press Enter or click Send
2. **Voice** - Click Mic button, speak your command
3. **Wake Word** - Say "hey cora" to activate voice input

---

## Task Commands

### Creating Tasks

```
add <description>     Create a new task
```

Example:
```
cora> add Buy groceries
[CORA]: Task T001 added.
```

### Viewing Tasks

```
list                  Show all tasks
list pri              Sort by priority
show <id>             Detailed task view
stats                 Task statistics
today                 Due today + overdue
```

### Completing Tasks

```
done <id>             Mark task complete
status <id> <state>   Change status (pending|active|done)
```

### Modifying Tasks

```
pri <id> <1-10>       Set priority (1=highest)
due <id> <date>       Set due date (YYYY-MM-DD or +Nd)
note <id> <text>      Add a note
edit <id> <text>      Edit description
```

### Deleting Tasks

```
delete <id>           Remove task (aliases: del, rm)
undo                  Restore last deleted
```

### Searching

```
search <query>        Find tasks by text
```

---

## Knowledge Base

### Adding Knowledge

```
learn <text> [#tags]  Add knowledge entry
```

Example:
```
cora> learn Python is awesome #coding #languages
```

### Recalling Knowledge

```
recall                View all knowledge
recall #tag           Filter by tag
```

---

## AI Features

### Chatting with CORA

```
chat <message>        Context-aware conversation
chathistory           View chat history
chathistory clear     Clear history
```

CORA knows about your tasks and can help prioritize!

Example:
```
cora> chat What should I focus on today?
```

### Voice Output

```
speak <text>          Speak text aloud (Kokoro TTS)
```

### Vision / Camera

```
see                   Capture webcam and describe what CORA sees
see <prompt>          Analyze camera image with specific question
```

Uses Ollama's llava model for vision analysis.

### Image Generation

```
imagine <description>  Generate AI image via Pollinations Flux
```

Example:
```
cora> imagine a cyberpunk city at night with neon lights
```

Images saved to `data/images/` folder.

### AI Model Management

```
pull <model>          Download Ollama model
```

---

## System Tools

### Time & Weather

```
time                  Show current time with greeting
weather               Show current weather conditions
```

### Screenshots

```
screenshot            Capture and save screenshot (supports 3840x2160)
```

### Camera

```
see                   Vision analysis via webcam
```

The status bar shows camera status:
- **Check** button - Manual presence detection
- **Check mark** - User detected
- **X** - No user
- **--** - Not checked

---

## Voice Commands

### Wake Words

Say any of these to activate:
- "cora"
- "hey cora"
- "yo cora"
- "okay cora"

### Voice Command Examples

- "Hey CORA, what time is it?"
- "CORA, add task buy milk"
- "Hey CORA, what's on my schedule?"
- "CORA, weather"

---

## Settings

### GUI Settings Panel

Access via **Settings** button in sidebar:

| Setting | Range | Description |
|---------|-------|-------------|
| TTS Enabled | On/Off | Enable voice output |
| Speech Rate | 50-300 | Words per minute |
| Volume | 0-100% | Voice volume |
| Ollama Enabled | On/Off | Enable AI chat |
| Model | text | Ollama model name |
| Voice Input | On/Off | Enable STT |
| Sensitivity | 0-100% | Voice detection threshold |

Click **Save Settings** to persist changes.

### CLI Settings

```
settings              View all settings
settings <key>        View specific setting
settings <key> <val>  Update setting
```

Example:
```
cora> settings tts.rate 180
```

---

## Runtime Tools

Create your own tools at runtime:

```
create_tool <name> <description>    Create new tool
modify_tool <name> enable/disable   Toggle tool
list_tools                          Show all custom tools
```

---

## Backup

```
backup                Save all data to backups/
```

---

## Date Formats

| Format | Example | Meaning |
|--------|---------|---------|
| YYYY-MM-DD | 2024-12-25 | Specific date |
| +Nd | +3d | Days from now |

---

## Task Priority

| Level | Meaning |
|-------|---------|
| P1 | Highest priority |
| P2-P4 | High priority |
| P5 | Normal (default) |
| P6-P9 | Low priority |
| P10 | Lowest priority |

---

## Data Files

| File | Purpose |
|------|---------|
| tasks.json | Task storage |
| knowledge.json | Knowledge base |
| chat_history.json | Conversation memory |
| config/settings.json | GUI settings |
| config/voice_commands.json | Voice config |
| personality.json | AI personality |
| data/images/ | Generated images |
| data/camera/ | Camera captures |
| backups/ | Backup directory |

---

## Keyboard Shortcuts

### CLI Mode

| Key | Action |
|-----|--------|
| Ctrl+C | Exit |
| Up/Down | Command history |

### GUI Mode

| Key | Action |
|-----|--------|
| Enter | Send message |
| Ctrl+C | Exit |

### Boot Display

| Key | Action |
|-----|--------|
| ESC | Close display |
| Any key | Skip boot (during phases) |

---

## Tips

1. **High Priority Tasks:** Use `pri <id> 1` for urgent items
2. **Relative Due Dates:** Use `+3d` for "3 days from now"
3. **Quick Lists:** `list pri` shows by priority
4. **Task Context:** Chat knows your tasks - ask for help!
5. **Tags:** Use #tags in knowledge entries for easy filtering
6. **Quick Boot:** Use `--quick` flag to skip TTS announcements
7. **Voice Activation:** Say "hey cora" hands-free
8. **Camera Check:** Use the Check button to verify presence
9. **Dark Mode:** Toggle in sidebar for eye comfort
10. **Image Generation:** Use `imagine` to create AI art
11. **System Stats:** Boot display shows live CPU/RAM/GPU stats
12. **Dynamic AI:** CORA generates unique responses every boot

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No voice | Check TTS settings, ensure Kokoro installed |
| No AI | Start Ollama service (`ollama serve`), check model |
| No camera | Install opencv-python, check webcam connection |
| Slow boot | Use `--quick` flag |
| Voice not heard | Check microphone in settings |
| No GPU stats | Install NVIDIA drivers, check nvidia-smi |
| No images | Check internet connection (Pollinations needs internet) |

---

*Unity AI Lab - C.O.R.A v2.4.0*
*Last Updated: 2025-12-23*
