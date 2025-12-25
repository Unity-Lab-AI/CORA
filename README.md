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
  Version: 2.4.0
  Unity AI Lab
  Website: https://www.unityailab.com
  GitHub: https://github.com/Unity-Lab-AI
  Contact: unityailabcontact@gmail.com
  Creators: Hackall360, Sponge, GFourteen
  ================================================================
```

**Version 2.4.0** | **75+ Python Files** | **Unity AI Lab 2025**

A Windows 11 AI-powered personal assistant with full autonomous capabilities: visual boot display, dynamic AI responses, task management, knowledge base, voice input/output, vision analysis, image generation, and live system monitoring.

---

## What's New in v2.4.0

- **Visual Boot Display** - Cyberpunk-themed boot screen with waveform visualization
- **Dynamic AI Responses** - CORA generates unique responses via Ollama (no hardcoded phrases)
- **Live System Stats** - Real-time CPU, RAM, GPU, VRAM, Disk monitoring during boot
- **Kokoro TTS** - High-quality neural voice synthesis with af_bella voice
- **Image Generation** - AI-generated art using Pollinations Flux model
- **Full Location Announcement** - City, State, Country announced at boot
- **Persistent Boot Display** - Window stays open with live stats after boot

---

## Quick Start

### Full Boot (Recommended)
```bash
python src/boot_sequence.py
```

### GUI Mode
```batch
python src/gui_launcher.py
```

### CLI Mode
```bash
python cora.py
```

### Quick Boot (No TTS)
```bash
python src/boot_sequence.py --quick
```

---

## Boot Sequence

When CORA boots, she runs a 10-phase diagnostic with TTS announcements:

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

**CORA generates her own unique responses for each phase using Ollama AI.**

---

## Features

### Visual Boot Display
- Two-column layout: Status panel + Scrolling log
- Audio waveform visualization during speech
- Color-coded status indicators (green/yellow/red)
- Live updating system stats panel
- Cyberpunk/goth dark theme

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
- Dynamic boot responses via AI
- Context-aware conversations
- Vision/image analysis via llava
- Image generation via Pollinations

### Voice Systems
- **TTS Output:** Kokoro neural TTS (af_bella voice)
- **Emotion-aware speech** with mood tracking
- **STT Input:** Speech recognition with wake word detection
- **Wake words:** "cora", "hey cora", "yo cora", "okay cora"
- **TTS Mutex:** Prevents overlapping speech across processes

### System Tools
- Screenshot capture (3840x2160 support)
- Webcam capture and vision analysis
- Hotkey support
- Image generation (Pollinations)
- Browser control
- Reminders and calendar integration
- Live system monitoring (CPU, RAM, GPU, VRAM, Network)

---

## Commands

### Task Management
| Command | Description |
|---------|-------------|
| `add <text>` | Create new task |
| `list` / `ls` | Show all tasks |
| `list pri` | Sort by priority |
| `done <id>` | Mark complete |
| `delete <id>` | Remove task |
| `pri <id> <1-10>` | Set priority |
| `due <id> <date>` | Set due date |
| `note <id> <text>` | Add note |
| `search <query>` | Find tasks |
| `today` | Show due/overdue |
| `undo` | Restore deleted |

### AI & Voice
| Command | Description |
|---------|-------------|
| `chat <msg>` | Talk to CORA |
| `speak <text>` | TTS output |
| `see [question]` | Camera vision |
| `imagine <desc>` | Generate image |

### System
| Command | Description |
|---------|-------------|
| `time` | Current time |
| `weather` | Weather info |
| `screenshot` | Capture screen |
| `backup` | Save data |

---

## Requirements

- **Python 3.10+**
- **Ollama** (for AI)
- **NVIDIA GPU** (recommended)
- **mpv** (optional, for YouTube playback)

### Install
```bash
pip install -r requirements.txt
```

### Ollama Setup
```bash
winget install Ollama.Ollama
ollama pull llama3.2
ollama pull llava
```

### mpv Setup (Optional - for YouTube)
mpv is optional - only needed for YouTube playback. CORA prompts you if missing.

**Download and Extract:**
1. Download: https://sourceforge.net/projects/mpv-player-windows/files/64bit/
2. Extract .7z/.zip to `./tools/` folder
3. CORA auto-detects mpv.exe (any subfolder works)

**Option 2: Package Manager**
```bash
winget install mpv
# or
choco install mpv
# or
scoop install mpv
```

---

## Project Structure

```
C.O.R.A/
├── src/
│   ├── boot_sequence.py     # Main boot with TTS
│   ├── cora.py              # CLI application
│   └── gui_launcher.py      # GUI launcher
├── ui/
│   ├── boot_display.py      # Visual boot display with waveform
│   ├── app.py               # Main GUI application
│   ├── camera_feed.py       # Live webcam window
│   └── panels.py            # Task/Settings/Knowledge panels
├── voice/
│   ├── tts.py               # Kokoro TTS engine (af_bella)
│   ├── stt.py               # Speech recognition
│   ├── commands.py          # Voice command processing
│   └── wake_word.py         # Wake word detection
├── ai/
│   ├── ollama.py            # Ollama API client
│   └── context.py           # Context management
├── cora_tools/              # CORA's Python tool modules
│   ├── image_gen.py         # Pollinations AI image gen
│   ├── screenshots.py       # Screen/window capture
│   ├── tasks.py             # Task management
│   ├── memory.py            # Working memory
│   ├── calendar.py          # Calendar & events
│   ├── media.py             # YouTube & media control
│   └── ...                  # 20+ tool modules
├── tools/                   # Downloaded binaries ONLY
│   └── mpv/                 # mpv player (extract here)
├── services/
│   ├── weather.py           # Weather API (wttr.in)
│   ├── location.py          # IP geolocation
│   └── presence.py          # Webcam presence detection
├── config/
│   └── settings.json        # Configuration
├── data/
│   ├── images/              # Generated images
│   └── camera/              # Camera captures
└── READMEs/
    ├── UserGuide.md         # User documentation
    └── NerdReadme.md        # Developer documentation
```

**Note:** `cora_tools/` = Python source code. `tools/` = downloaded binaries only (mpv, ffmpeg).

---

## Hardware Detection

| Component | Method |
|-----------|--------|
| CPU | psutil.cpu_percent() |
| RAM | psutil.virtual_memory() |
| Disk | psutil.disk_usage() |
| GPU | nvidia-smi subprocess |
| VRAM | nvidia-smi memory query |
| Network | psutil.net_if_stats() |
| Camera | OpenCV VideoCapture |

---

## Recent Updates (v2.4.0)

- Visual Boot Display with cyberpunk theme
- Dynamic AI responses via Ollama for all boot phases
- Live system stats panel with 1-second refresh
- Kokoro TTS with af_bella neural voice
- Image generation test creates AI art during boot
- Full location announcement (City, State, Country)
- Waveform visualization during TTS playback
- GPU detection via nvidia-smi (RTX 4070 Ti SUPER tested)
- 75+ Python files across all modules

---

## Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | Overview & quick start |
| [SETUP.md](SETUP.md) | Installation guide |
| [HOW_TO_USE.md](HOW_TO_USE.md) | Simple user guide |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture |
| [READMEs/UserGuide.md](READMEs/UserGuide.md) | Full user docs |
| [READMEs/NerdReadme.md](READMEs/NerdReadme.md) | Developer docs |

---

## Roadmap

- [x] Phase 1: CLI Task Manager
- [x] Phase 2: Kokoro TTS + Emotion
- [x] Phase 3: CustomTkinter GUI
- [x] Phase 4: Voice Input (STT)
- [x] Phase 5: Boot Diagnostics
- [x] Phase 6: Vision/Camera
- [x] Phase 7: Visual Boot Display + Dynamic AI
- [ ] Phase 8: Auto-updater + Installer

---

## License

Unity AI Lab - 2025

---

*C.O.R.A v2.4.0 - Cognitive Operations & Reasoning Assistant*
*Last Updated: 2025-12-25*
*Built by Unity AI Lab*
