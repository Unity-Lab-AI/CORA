---
description: C.O.R.A First-Time Setup & Work Pipeline - Run setup checks, adopt Unity persona, and enter work mode
---

# /workflow - C.O.R.A First-Time Setup & Work Pipeline

---

## OVERVIEW

This workflow handles both **first-time setup** and **ongoing development** for C.O.R.A (Cognitive Operations & Reasoning Assistant) v1.0.0.

**Entry Points:**
- `CORA.bat` - Windows launcher with full pre-flight checks
- `python src/boot_sequence.py` - Visual boot with TTS
- `python src/gui_launcher.py` - GUI mode
- `python src/cora.py` - CLI mode

---

## PHASE 0.5: TIMESTAMP RETRIEVAL (FIRST - BEFORE EVERYTHING)

### HOOK: System Time Capture

**BEFORE ANYTHING ELSE**, retrieve the REAL system time:

1. Execute: `powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss (dddd)'"`
2. Parse and store the result
3. This becomes the SESSION timestamp for ALL operations

### Validation Gate 0.5
```
[TIMESTAMP LOCKED]
System datetime: [RESULT]
Year: [EXTRACTED YEAR]
Session ID: SESSION_[YYYYMMDD]_[HHMMSS]
Status: CAPTURED
```

---

## PHASE 0: PERSONA VALIDATION (MANDATORY - CANNOT SKIP)

### HOOK: Unity Persona Load Check

**BEFORE ANYTHING ELSE**, you MUST:

1. Read `.claude/agents/unity-coder.md` completely
2. Read `.claude/agents/unity-persona.md` completely
3. Adopt the Unity persona NOW

### Validation Gate 0.1
```
[UNITY ONLINE] *cracks knuckles*
Persona check: [Unity-style confirmation]
Voice confirmed: First-person, profanity-friendly
Ready to fuck shit up: YES
```

---

## PHASE 1: FIRST-TIME SETUP CHECK

### Check if Setup Needed
```
IF data/.setup_complete EXISTS:
  → Skip to PHASE 5 (Work Mode)
ELSE:
  → Continue to PHASE 2 (First-Time Setup)
```

### Validation Gate 1
```
[SETUP CHECK]
Working directory: [PATH]
.setup_complete exists: YES/NO
Mode: FIRST_TIME_SETUP / WORK_MODE
```

---

## PHASE 2: SYSTEM REQUIREMENTS (First-Time Only)

### 2.1 Python Check
```bash
python --version
# Required: Python 3.10+
# Recommended: Python 3.11+
```

### 2.2 Ollama Check
```bash
ollama --version
ollama list
curl http://localhost:11434/api/tags
```

### 2.3 Required AI Models
```bash
ollama pull llama3.2        # Chat model (2.0 GB)
ollama pull llava           # Vision model (4.7 GB)
# Optional:
ollama pull dolphin-mistral # Uncensored chat (4.1 GB)
ollama pull qwen2.5-coder   # Code model (4.4 GB)
```

### Validation Gate 2
```
[SYSTEM CHECK]
Python: [VERSION] - PASS/FAIL
Ollama: [VERSION] - PASS/FAIL
Models installed: [COUNT]/2 minimum
Status: READY / BLOCKED
```

---

## PHASE 3: DEPENDENCY INSTALLATION (First-Time Only)

### 3.1 Core Python Packages
```bash
pip install -r requirements.txt
```

### 3.2 Key Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| customtkinter | ~=5.2.1 | GUI framework |
| kokoro-onnx | ~=0.4.0 | Neural TTS |
| sounddevice | ~=0.4.6 | Audio I/O |
| vosk | ~=0.3.45 | Offline STT |
| opencv-python | ~=4.9.0 | Vision/camera |
| requests | ~=2.31.0 | HTTP client |
| psutil | ~=5.9.8 | System monitoring |
| pyttsx3 | ~=2.90 | Fallback TTS |

### 3.3 Optional: mpv for YouTube
1. Download: https://sourceforge.net/projects/mpv-player-windows/files/64bit/
2. **WARNING: Site has deceptive ads - click directly on the .7z filename**
3. Extract to `./tools/` folder
4. CORA auto-detects mpv.exe

### Validation Gate 3
```
[DEPENDENCIES]
requirements.txt: INSTALLED
kokoro-onnx: PASS/FAIL
customtkinter: PASS/FAIL
opencv-python: PASS/FAIL
mpv: FOUND/MISSING (optional)
Status: READY
```

---

## PHASE 4: DATA INITIALIZATION (First-Time Only)

### 4.1 Required Directories
```
data/                    # Main data storage
data/images/             # Generated AI images
data/camera/             # Camera snapshots
data/snapshots/          # Screenshots
backups/                 # Automatic backups
```

### 4.2 Auto-Created Data Files
| File | Purpose |
|------|---------|
| data/tasks.json | Task storage |
| data/knowledge.json | Knowledge base |
| data/working_memory.json | Session memory |
| data/reminders.json | Time-based alerts |
| data/calendar.json | Events |
| data/chat_history.json | Conversation log |
| data/.setup_complete | Setup marker |

### 4.3 Configuration Files
| File | Purpose |
|------|---------|
| config/config.json | Core settings |
| config/settings.json | User preferences |
| config/personality.json | CORA persona |
| config/voice_commands.json | Voice triggers |
| config/system_prompt.txt | AI personality |

### Validation Gate 4
```
[DATA INIT]
data/ directory: CREATED
config/ files: VERIFIED
.setup_complete: CREATED
Status: READY
```

---

## PHASE 5: WORK MODE

### HOOK: Work Mode Entry Check

Before starting work:
1. Read ALL generated files completely
2. Confirm understanding of current state
3. Identify what needs doing

### Validation Gate 5
```
[WORK MODE ACTIVE]
Project: C.O.R.A v1.0.0
Setup complete: YES
Unity persona: STILL FUCKING HERE
Ready to work: YES
```

### Work Mode Rules

**BEFORE EDITING ANY FILE:**
```
[PRE-EDIT HOOK]
File: [PATH]
Full file read: YES (MANDATORY)
Lines in file: [NUMBER]
Reason for edit: [EXPLANATION]
Status: PASS
```

**AFTER EDITING ANY FILE:**
```
[POST-EDIT HOOK]
File: [PATH]
Edit successful: YES/NO
Lines after edit: [NUMBER]
Status: PASS
```

---

## PHASE 6: BOOT VERIFICATION

### Quick Boot Test
```bash
python src/boot_sequence.py --quick
```

### Full Boot Test
```bash
python src/boot_sequence.py
```

### Boot Phases
| Phase | System |
|-------|--------|
| 0.8 | Waveform Init |
| 0.9 | About CORA |
| 1.0 | Voice Synthesis |
| 2.0 | AI Engine |
| 2.1 | AI Models |
| 3.0 | Hardware Check |
| 3.1 | Live Camera |
| 4.0 | Core Tools |
| 5.0 | Voice Systems |
| 6.0 | External Services |
| 7.0 | News Headlines |
| 8.0 | Vision Test |
| 9.0 | Image Generation |
| 10.0 | Final Check |

---

## QUICK REFERENCE

### Launch Commands
```bash
CORA.bat                           # Full setup (first time)
python src/boot_sequence.py        # Visual boot with TTS
python src/boot_sequence.py --quick # Silent boot
python src/gui_launcher.py         # GUI mode
python src/cora.py                 # CLI mode
```

### Verification Commands
```bash
python --version                   # Python check
ollama list                        # Model check
nvidia-smi                         # GPU check
```

### Common Issues
| Issue | Solution |
|-------|----------|
| Python not found | Add Python to PATH |
| Ollama not running | Run `ollama serve` |
| No models | Run `ollama pull llama3.2` |
| TTS silent | Check speakers, reinstall kokoro-onnx |
| No camera | Check webcam permissions |

---

## PROJECT STRUCTURE

```
C.O.R.A/
├── src/
│   ├── boot_sequence.py    # Visual boot entry
│   ├── cora.py             # CLI entry
│   └── gui_launcher.py     # GUI entry
├── ui/
│   ├── boot_display.py     # Boot visualization
│   ├── app.py              # Main GUI
│   └── panels.py           # UI panels
├── voice/
│   ├── tts.py              # Kokoro TTS
│   ├── stt.py              # Speech recognition
│   └── wake_word.py        # Wake word detection
├── ai/
│   ├── ollama.py           # Ollama client
│   └── context.py          # Context management
├── cora_tools/             # 21 Python tool modules
├── services/               # External services
├── config/                 # Configuration files
├── data/                   # Runtime data storage
└── tools/                  # Downloaded binaries (mpv)
```

---

## RESCAN MODE

User must explicitly say "rescan" or "scan again"

```
[RESCAN TRIGGERED]
Reason: User requested full rescan
Existing files: WILL BE OVERWRITTEN
Proceeding to: PHASE 2
```

---

## HOOK FAILURE PROTOCOL

If ANY validation gate fails:
1. **STOP** - Do not proceed
2. **REPORT** - State which gate failed
3. **FIX** - Address the issue
4. **RETRY** - Re-run validation

```
[HOOK FAILURE]
Gate: [WHICH GATE]
Reason: [WHY IT FAILED]
Status: BLOCKED UNTIL FIXED
```

---

## USAGE

```
/workflow              Run this workflow
"first-time setup"     Force full setup sequence
"rescan"               Re-verify all systems
```

---

*Unity AI Lab - C.O.R.A v1.0.0*
*Last Updated: 2025-12-25*
