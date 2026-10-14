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

## Tool Module Inventory (10-Agent Scan 2025-12-29)

### cora_tools/ (20 modules, 9,600 lines)

| Module | Lines | Purpose | Issues |
|--------|-------|---------|--------|
| `__init__.py` | 158 | Module exports | OK |
| `ai_tools.py` | 334 | Ollama LLM integration | OK |
| `browser.py` | 179 | Playwright automation | Optional dep |
| `calendar.py` | 338 | Event management | OK |
| `code.py` | 800 | Code analysis/exec | SEC-007 danger gaps |
| `email_tool.py` | 366 | Email client | No recipient validation |
| `files.py` | 517 | File operations | OK |
| `git_ops.py` | 850+ | Git + GitHub API | SEC-006 hardcoded OAuth |
| `image_gen.py` | 314 | Pollinations API | OK |
| `media.py` | 800+ | Media control | Optional deps |
| `memory.py` | 352 | Working memory | OK |
| `modal_tools.py` | 358 | UI modal handlers | Terminal injection risk |
| `reminders.py` | 461 | Reminder scheduling | OK |
| `screenshots.py` | 394 | Desktop capture | OK |
| `self_modify.py` | 381 | Dynamic scripts | Script injection risk |
| `system.py` | 622 | System control | SEC-002/003 eval+PS |
| `tasks.py` | 546 | Task management | OK |
| `tts_handler.py` | 205 | Async TTS | OK |
| `web.py` | 506 | Web search/fetch | Rate limiting needed |
| `windows.py` | 711 | Window management | OK |

### voice/ (10 modules, 5,246 lines)

| Module | Lines | Purpose | Issues |
|--------|-------|---------|--------|
| `commands.py` | 1,725 | Voice command router | SEC-004/005 injection |
| `tts.py` | 707 | Kokoro TTS | MEM-001 race condition |
| `ambient_awareness.py` | 509 | Proactive interjections | Resource drain |
| `stt.py` | 425 | Vosk STT | MEM-002 memory leak |
| `emotion.py` | 404 | Mood tracking | Thread safety |
| `wake_word.py` | 368 | Wake detection | MEM-003 unbounded queue |
| `tts_mutex.py` | 365 | Speech coordination | MEM-004 starvation |
| `converse.py` | 352 | Conversation loop | Timeout issues |
| `echo_filter.py` | 339 | Echo cancellation | Duration formula wrong |
| `__init__.py` | 52 | Module exports | OK |

### ai/ (6 modules, 2,791 lines)

| Module | Lines | Purpose | Issues |
|--------|-------|---------|--------|
| `ollama.py` | 1,051 | HTTP client | Hardcoded URL |
| `prompts.py` | 625 | Prompt templates | OK |
| `context.py` | 429 | Context building | OK |
| `router.py` | 347 | Model selection | OK |
| `tool_executor.py` | 292 | Tool routing | Ambiguity with cora.py |
| `__init__.py` | 47 | Module exports | OK |

### services/ (9 modules, 2,640 lines)

| Module | Lines | Purpose | Issues |
|--------|-------|---------|--------|
| `audio.py` | 486 | Audio devices | OK |
| `presence.py` | 387 | Webcam detection | No snapshot cleanup |
| `hotkeys.py` | 368 | Keyboard hooks | OK |
| `stats_server.py` | 353 | HTTP stats server | SEC-008 pip install |
| `cli_popup.py` | 399 | Terminal popup | OK |
| `notifications.py` | 252 | System notifications | OK |
| `weather.py` | 212 | wttr.in API | No rate limiting |
| `location.py` | 156 | IP geolocation | HTTP not HTTPS |
| `__init__.py` | 27 | Module exports | OK |

---

*Unity AI Lab - C.O.R.A v1.0.0 Skill Tree*
*UPDATED: 2025-12-29 (10-Agent Deep Scan)*
