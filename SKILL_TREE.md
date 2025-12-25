# C.O.R.A - Skill Tree

```
  ================================================================
    ____   ___   ____      _
   / ___| / _ \ |  _ \    / \
  | |    | | | || |_) |  / _ \
  | |___ | |_| ||  _ <  / ___ \
   \____| \___/ |_| \_\/_/   \_\

  Cognitive Operations & Reasoning Assistant
  ================================================================
  Version: 1.0.0
  Unity AI Lab | https://www.unityailab.com
  ================================================================
```

## Cognitive Operations & Reasoning Assistant Capabilities

> **Status Key:** DONE = Implemented | WIP = In Progress | TODO = Planned

---

## Domain: Voice & Speech

### Text-to-Speech (TTS)
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Kokoro TTS | Core | DONE | Neural voice synthesis (af_bella) |
| Emotion-aware Speech | Advanced | DONE | Context-based tone adjustment |
| TTS Mutex | Core | DONE | Prevents overlapping speech |
| pyttsx3 Fallback | Basic | DONE | Backup TTS engine |

### Speech-to-Text (STT)
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Vosk STT | Core | DONE | Offline speech recognition |
| Wake Word Detection | Core | DONE | "Cora" activation |
| Echo Filtering | Advanced | DONE | Ignore own speech |
| Conversation Mode | Advanced | DONE | Continuous listening |

---

## Domain: Vision & Camera

### Camera Operations
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Webcam Capture | Basic | DONE | Multi-index camera detection |
| Presence Detection | Intermediate | DONE | User at desk detection |
| llava Vision | Advanced | WIP | AI image analysis |
| Screenshot Capture | Basic | DONE | Desktop/window screenshots |

---

## Domain: AI & Reasoning

### Local AI (Ollama)
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Chat Generation | Core | DONE | dolphin-mistral responses |
| Code Generation | Intermediate | DONE | qwen2.5-coder integration |
| Vision Analysis | Advanced | DONE | llava model |
| Dynamic Responses | Advanced | DONE | cora_respond() boot phases |
| Context Tracking | Intermediate | DONE | Conversation memory |

### External AI
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Pollinations API | Intermediate | DONE | Image generation |
| GitHub API | Intermediate | DONE | Repository access |

---

## Domain: Task Management

### Core Tasks
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Create Task | Basic | DONE | Add with priority/due date |
| List Tasks | Basic | DONE | Filter by status |
| Complete Task | Basic | DONE | Mark as done |
| Delete Task | Basic | DONE | Remove tasks |
| Priority Sorting | Intermediate | DONE | Auto-sort by priority |
| Due Date Tracking | Intermediate | DONE | Deadline alerts |

### Calendar & Reminders
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Calendar Events | Intermediate | DONE | Event management |
| Reminders | Intermediate | DONE | Time-based alerts |
| Knowledge Base | Intermediate | DONE | Store/recall information |

---

## Domain: System Control

### Windows Operations
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Launch App | Basic | DONE | Start applications |
| Close App | Basic | DONE | Terminate processes |
| Window Management | Intermediate | DONE | Focus/minimize/maximize |
| System Stats | Basic | DONE | CPU/RAM/GPU monitoring |
| Volume Control | Basic | DONE | Audio adjustment |

### File Operations
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| File CRUD | Basic | DONE | Create/read/update/delete |
| File Search | Intermediate | DONE | Find by name/content |
| JSON Handling | Basic | DONE | Parse/generate JSON |

---

## Domain: Web & External

### Web Operations
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Web Search | Intermediate | DONE | DuckDuckGo search |
| URL Fetch | Intermediate | DONE | Get webpage content |
| Weather API | Intermediate | DONE | wttr.in integration |
| Location API | Intermediate | DONE | IP geolocation |
| News Headlines | Intermediate | DONE | Current news fetch |

### Browser Automation
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Playwright | Advanced | WIP | Web automation |
| Media Control | Intermediate | DONE | mpv YouTube playback |

---

## Domain: Code & Development

### Code Tools
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Code Execution | Intermediate | DONE | Safe Python/JS runner |
| Code Explanation | Intermediate | DONE | AI-powered analysis |
| Code Generation | Advanced | DONE | Write code from description |
| Syntax Display | Basic | DONE | Formatted code output |

### Self-Modification
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Create Tool | Advanced | DONE | Runtime tool creation |
| Modify Tool | Advanced | DONE | Enable/disable tools |
| Tool Registry | Advanced | DONE | List all capabilities |

---

## Domain: User Interface

### Desktop GUI
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| CustomTkinter GUI | Core | DONE | Floating panel UI |
| Boot Display | Core | DONE | Cyberpunk boot console |
| Waveform Visual | Intermediate | DONE | Audio visualization |
| System Tray | Basic | DONE | Background operation |
| Query Panels | Intermediate | DONE | Popup interactions |

### Web UI (NEW)
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| Split View | Core | DONE | Console + App layout |
| Boot Console | Core | DONE | F-100 style boot sequence |
| API Key Modal | Intermediate | DONE | Key input with validation |
| localStorage | Basic | DONE | Persistent key storage |
| Fullscreen Toggle | Basic | DONE | View mode switching |
| Ollama Chat | Core | DONE | Browser AI chat |

### Deployment
| Skill | Level | Status | Description |
|-------|-------|--------|-------------|
| GitHub Actions | Intermediate | DONE | Auto-deploy workflow |
| GitHub Pages | Intermediate | DONE | Static site hosting |

---

## Skill Completion Summary

| Domain | Done | WIP | TODO | Total |
|--------|------|-----|------|-------|
| Voice & Speech | 8 | 0 | 0 | 8 |
| Vision & Camera | 3 | 1 | 0 | 4 |
| AI & Reasoning | 7 | 0 | 0 | 7 |
| Task Management | 8 | 0 | 0 | 8 |
| System Control | 8 | 0 | 0 | 8 |
| Web & External | 6 | 1 | 0 | 7 |
| Code & Development | 6 | 0 | 0 | 6 |
| User Interface | 12 | 0 | 0 | 12 |
| **TOTAL** | **58** | **2** | **0** | **60** |

**Completion: 97%** (58/60 skills implemented)

---

## Implementation Files

| Domain | Primary Files |
|--------|---------------|
| Voice | `voice/tts.py`, `voice/stt.py`, `voice/wake_word.py` |
| Vision | `services/presence.py`, `ui/camera_feed.py` |
| AI | `ai/ollama.py`, `ai/context.py` |
| Tasks | `cora_tools/tasks.py`, `cora_tools/calendar.py` |
| System | `cora_tools/system.py`, `cora_tools/windows.py` |
| Web | `cora_tools/web.py`, `services/weather.py` |
| Code | `cora_tools/code.py`, `cora_tools/self_modify.py` |
| UI | `ui/app.py`, `ui/boot_display.py`, `web/index.html` |

---

*Unity AI Lab - C.O.R.A v1.0.0 Skill Tree*
*UPDATED: 2025-12-25*
