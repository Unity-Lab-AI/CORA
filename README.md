# C.O.R.A

```
  ================================================================
    ____   ___   ____      _
   / ___| / _ \ |  _ \    / \
  | |    | | | || |_) |  / _ \
  | |___ | |_| ||  _ <  / ___ \
   \____| \___/ |_| \_\/_/   \_\

  Cognitive Operations & Reasoning Assistant
  ================================================================
  Version: 2.3.0
  Unity AI Lab
  Website: https://www.unityailab.com
  GitHub: https://github.com/Unity-Lab-AI
  Contact: unityailabcontact@gmail.com
  Creators: Hackall360, Sponge, GFourteen
  ================================================================
```

**Version 2.3.0** | **70+ Python Files** | **Unity AI Lab 2025**

A Windows 11 AI-powered personal assistant with full autonomous capabilities: task management, knowledge base, voice input/output, vision analysis, GUI interface, boot diagnostics, and self-modification.

---

## Quick Start

### GUI Mode (Recommended)
```batch
python gui_launcher.py
```
or
```batch
python ui/app.py
```

### CLI Mode
```bash
python cora.py
```

### Windows Batch
```batch
start.bat
```

---

## Features

### Task Management
- Add, list, complete, delete tasks
- Priority levels (1-10)
- Due dates and reminders
- Notes and status tracking
- Search functionality
- Undo last delete

### Knowledge Base
- Learn facts with tags
- Recall by tag or search
- Persistent storage

### AI Integration
- Ollama-powered chat (llama3.2, llava)
- Context-aware responses
- Conversation memory
- Vision/image analysis via llava

### Voice Systems
- **TTS Output:** pyttsx3 (default) or Kokoro neural TTS
- **Emotion-aware speech** with mood tracking
- **STT Input:** Speech recognition with wake word detection
- **Wake words:** "cora", "hey cora", "yo cora", "okay cora"
- **TTS Mutex:** Prevents overlapping speech across processes

### GUI Interface (CustomTkinter)
- Dark/Light mode toggle
- Chat panel with command processing
- Tasks panel with status checkboxes
- Knowledge panel with tag search
- Settings panel with save/load
- Status bar with camera presence detection

### Boot Sequence
- Fullscreen animated splash screen
- Advanced System Diagnostics display
- 13 boot checks: Time, Location, Weather, Calendar, Tasks, Ollama, TTS, System, GPU, Disk, Network, Microphone, Webcam
- Context-aware TTS narration with varied responses

### System Tools
- Screenshot capture
- Webcam presence detection
- Hotkey support
- Image generation (Pollinations)
- Browser control
- Reminders and calendar integration

---

## Commands

### Task Management
| Command | Description |
|---------|-------------|
| `add <text>` | Create new task |
| `list` / `ls` | Show all tasks |
| `list pri` | Show tasks sorted by priority |
| `done <id>` | Mark task complete |
| `delete <id>` / `del` / `rm` | Remove task |
| `pri <id> <1-10>` | Set priority (1=highest) |
| `due <id> <date>` | Set due date (YYYY-MM-DD or +3d) |
| `note <id> <text>` | Add note to task |
| `edit <id> <text>` | Edit task description |
| `status <id> <state>` | Change status (pending/active/done) |
| `show <id>` | View task details |
| `search <query>` | Find tasks by text |
| `today` | Show due/overdue tasks |
| `stats` | Task statistics |
| `undo` | Restore last deleted |

### Knowledge Base
| Command | Description |
|---------|-------------|
| `learn <text> [#tags]` | Add knowledge with tags |
| `recall [#tag]` | View/filter knowledge |

### AI & Voice
| Command | Description |
|---------|-------------|
| `chat <msg>` | Talk to CORA (context-aware) |
| `chathistory [clear]` | View/clear chat history |
| `speak <text>` | Text-to-speech output |
| `see [question]` | Camera vision analysis |
| `imagine <desc>` | Generate image from text |

### System Tools
| Command | Description |
|---------|-------------|
| `time` | Current time with greeting |
| `weather` | Current weather conditions |
| `remind <time> <msg>` | Set reminder |
| `open <path>` | Open file or launch app |
| `screenshot` | Capture screen |
| `backup` | Save all data |

### Runtime Tools
| Command | Description |
|---------|-------------|
| `create_tool <name> <desc>` | Create custom tool |
| `modify_tool <name> <action>` | Enable/disable/delete tool |
| `list_tools` | Show all runtime tools |

### Other
| Command | Description |
|---------|-------------|
| `settings [key] [value]` | View/modify config |
| `pull <model>` | Pull Ollama model |
| `clear` | Clear terminal |
| `help` | Show all commands |

---

## Requirements

- Python 3.10+
- Ollama (for AI features)
- pyttsx3 (for TTS)
- customtkinter (for GUI)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Install Ollama
```bash
winget install Ollama.Ollama
ollama pull llama3.2
ollama pull llava  # For vision
```

---

## Configuration

### config/settings.json
- TTS settings (rate, volume, engine)
- Ollama model selection
- STT settings (voice input)

### config/voice_commands.json
- Wake words
- Command aliases
- Enable/disable commands
- Custom responses

---

## Project Structure

```
C.O.R.A/
├── cora.py                  # Main CLI application (2300+ lines)
├── gui_launcher.py          # GUI entry point
├── config.json              # Legacy settings
├── personality.json         # AI personality config
├── system_prompt.txt        # AI system prompt (282 lines)
├── tasks.json               # Task storage
├── knowledge.json           # Knowledge base
├── chat_history.json        # Conversation memory
├── requirements.txt         # Dependencies
├── start.bat                # Windows launcher
├── ARCHITECTURE.md          # System architecture spec
├── TODO.md                  # Task hierarchy
├── todoDriver.md            # Driver scan results
├── todoSlave1.md            # Slave1 scan results
├── todoSlave2.md            # Slave2 scan results
│
├── ui/                      # GUI Components
│   ├── app.py               # Main GUI application (620+ lines)
│   ├── splash.py            # Fullscreen animated splash
│   ├── boot_console.py      # Boot diagnostics (800+ lines)
│   ├── panels.py            # Task/Settings/Knowledge panels
│   ├── query_panel.py       # Query interface
│   ├── image_panel.py       # Image display
│   ├── fullscreen_image.py  # Fullscreen image viewer
│   └── system_tray.py       # System tray integration
│
├── voice/                   # Voice Systems
│   ├── tts.py               # Text-to-speech (Kokoro/pyttsx3)
│   ├── stt.py               # Speech-to-text (Vosk)
│   ├── emotion.py           # Emotional state machine
│   ├── wake_word.py         # Wake word detection
│   ├── commands.py          # Voice command processing
│   ├── converse.py          # Conversation handler + echo filter
│   └── tts_mutex.py         # Speech overlap prevention
│
├── ai/                      # AI Integration
│   ├── ollama.py            # Ollama HTTP API client
│   ├── router.py            # Model routing
│   ├── context.py           # Context management
│   └── prompts.py           # Prompt templates
│
├── tools/                   # System Tools
│   ├── system.py            # System info/control + calculator + shell
│   ├── web.py               # Web search + instant answers
│   ├── browser.py           # Playwright browser control
│   ├── email_tool.py        # SMTP email sending
│   ├── media.py             # Emby media server control
│   ├── screenshots.py       # Screen capture
│   ├── calendar.py          # Calendar integration
│   ├── memory.py            # Working memory
│   ├── reminders.py         # Reminder system
│   ├── image_gen.py         # Image generation (Pollinations)
│   ├── files.py             # File operations
│   ├── tasks.py             # Task management module
│   ├── self_modify.py       # Runtime tool creation
│   ├── ai_tools.py          # AI tool integrations
│   └── tts_handler.py       # TTS utility handler
│
├── services/                # Background Services
│   ├── presence.py          # Webcam presence detection
│   ├── audio.py             # Audio device management
│   ├── weather.py           # Weather API (wttr.in)
│   ├── location.py          # IP geolocation
│   ├── hotkeys.py           # Hotkey handling
│   └── notifications.py     # System notifications
│
├── config/                  # Configuration
│   ├── settings.json        # GUI settings
│   └── voice_commands.json  # Voice command config
│
├── READMEs/                 # Documentation
│   ├── UserGuide.md         # User documentation
│   └── NerdReadme.md        # Developer documentation
│
└── backups/                 # Data backups
```

---

## Command Line Arguments

```bash
# GUI with splash screen (default)
python ui/app.py

# GUI without splash (quick boot)
python ui/app.py --no-splash
python ui/app.py --quick

# CLI mode
python cora.py
```

---

## Roadmap

- [x] Phase 0: CLI Task Manager (cora.py - 84KB)
- [x] Phase 1: Kokoro TTS + Emotion (voice/ - 98KB)
- [x] Phase 2: CustomTkinter GUI (ui/ - 145KB)
- [x] Phase 3: Voice Input (STT + Wake Word)
- [x] Phase 4: Boot Diagnostics + Splash Screen
- [x] Phase 5: Vision/Camera Integration (llava)
- [x] Phase 6: Voice Commands (voice_commands.json)
- [x] Phase 7: System tray integration
- [x] Phase 8: Advanced Tools (browser, email, media, calculator)
- [~] Phase 9: Self-modification system (in progress)
- [ ] Phase 10: Auto-updater + Installer

---

## Recent Updates (v2.3.0)

- **70+ Python files** - Full production codebase
- Advanced System Diagnostics boot sequence with 13+ checks
- Voice command processing via voice_commands.json
- Camera presence detection in GUI status bar
- TTS mutex for preventing speech overlap
- Emotional state tracking with mood-aware responses
- Runtime tool creation system (self-modification)
- Image generation via Pollinations API
- Browser automation (Playwright)
- Email sending (SMTP)
- Media server control (Emby)
- Web search with DuckDuckGo instant answers
- Math calculator with safe expression evaluation
- Shell command execution with safety checks
- Conversation mode with echo filtering
- Working memory system (remember/recall)
- Query panels with hotbar support
- Natural language command parsing

### Module Breakdown

| Module | Files | Purpose |
|--------|-------|---------|
| **cora.py** | 1 | Main CLI application |
| **ui/** | 10 | GUI components |
| **voice/** | 9 | TTS/STT/Wake word |
| **tools/** | 18 | System tools (browser, email, media, web, etc.) |
| **ai/** | 5 | Ollama integration |
| **services/** | 8 | Background services |

---

## License

Unity AI Lab - 2025

---

*C.O.R.A v2.3.0 - Cognitive Operations & Reasoning Assistant*
*Last Updated: 2025-12-23*
*Built by Unity AI Lab with ClaudeColab team coordination*
