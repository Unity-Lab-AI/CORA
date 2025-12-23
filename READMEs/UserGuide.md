# C.O.R.A User Guide

## Cognitive Operations & Reasoning Assistant

Version 2.2.0

---

## Getting Started

### Starting CORA

**GUI Mode (Recommended):**
```bash
python ui/app.py
```

**GUI Quick Boot (No Splash):**
```bash
python ui/app.py --quick
```

**CLI Mode:**
```bash
python cora.py
```

**Single Command Mode:**
```bash
python cora.py <command> [args]
```

**Windows Launcher:**
```batch
start.bat
```

---

## Boot Sequence

When CORA starts in GUI mode, you'll see:

1. **Splash Screen** - Animated logo with progress bar (press ESC/SPACE to skip)
2. **Boot Diagnostics** - System checks with status indicators:
   - Time, Location, Weather
   - Calendar, Tasks
   - AI (Ollama), Voice (TTS)
   - System resources (CPU, RAM, GPU, Disk)
   - Network, Microphone, Webcam

CORA will speak a summary of each check as it boots.

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
speak <text>          Speak text aloud
```

### Vision / Camera

```
see                   Capture webcam and describe what CORA sees
see <prompt>          Analyze camera image with specific question
```

Uses Ollama's llava model for vision.

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
screenshot            Capture and save screenshot
```

### Camera

```
see                   Vision analysis via webcam
```

The status bar shows camera status:
- **Check** button - Manual presence detection
- **📷 ✓** - User detected
- **📷 ✗** - No user
- **📷 --** - Not checked

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
| config.json | Legacy settings |
| config/settings.json | GUI settings |
| config/voice_commands.json | Voice config |
| personality.json | AI personality |
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

### Splash Screen

| Key | Action |
|-----|--------|
| ESC | Skip splash |
| SPACE | Skip splash |
| Enter | Skip splash |

---

## Tips

1. **High Priority Tasks:** Use `pri <id> 1` for urgent items
2. **Relative Due Dates:** Use `+3d` for "3 days from now"
3. **Quick Lists:** `list pri` shows by priority
4. **Task Context:** Chat knows your tasks - ask for help!
5. **Tags:** Use #tags in knowledge entries for easy filtering
6. **Quick Boot:** Use `--quick` flag to skip splash screen
7. **Voice Activation:** Say "hey cora" hands-free
8. **Camera Check:** Use the Check button to verify presence
9. **Dark Mode:** Toggle in sidebar for eye comfort
10. **Settings Persist:** GUI settings save to config/settings.json

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No voice | Check TTS settings, install pyttsx3 |
| No AI | Start Ollama service, check model |
| No camera | Install opencv-python, check webcam |
| Slow boot | Use `--quick` flag |
| Voice not heard | Check microphone in settings |

---

*Unity AI Lab - C.O.R.A v2.2.0*
*Last Updated: 2025-12-23*
