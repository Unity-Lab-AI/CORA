# C.O.R.A - Project Roadmap

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

---

## Current State (2025-12-29)

| Metric | Value |
|--------|-------|
| **Version** | 1.0.0 |
| **Total Files** | 72+ Python modules |
| **Total Lines** | ~32,795+ |
| **Skills Implemented** | 58/60 (97%) |
| **Critical Issues** | 18 |
| **High Issues** | 21 |
| **Total Issues** | 81 |

---

## Immediate Priorities (P0)

These need fixing BEFORE any new feature work:

### Security (8 Critical)

| ID | Issue | Fix |
|----|-------|-----|
| SEC-001 | API keys in .env committed | Rotate keys, add .gitignore |
| SEC-002 | eval() in calculator | Replace with ast.literal_eval() |
| SEC-003 | PowerShell injection | Use subprocess with arrays |
| SEC-004 | Terminal command execution | Implement command whitelist |
| SEC-005 | Git command injection | Add shell escaping |
| SEC-006 | Hardcoded OAuth placeholder | Load from environment |
| SEC-007 | Code execution pattern gaps | Switch to whitelist approach |
| SEC-008 | Arbitrary pip install | Add authentication |

### Memory (4 Critical)

| ID | Issue | Fix |
|----|-------|-----|
| MEM-001 | TTS audio buffer race condition | Add thread-safe locking |
| MEM-002 | STT transcript buffer leak | Use bounded deque |
| MEM-003 | Wake word queue unbounded | Add maxsize limit |
| MEM-004 | TTS mutex starvation | Implement backoff |

### Architecture (1 Critical)

| ID | Issue | Fix |
|----|-------|-----|
| ARCH-001 | Circular dependency voice↔ui | Create shared/audio_buffer.py |

---

## Phase 1: Security Hardening

**Target:** All SEC-XXX issues resolved

### Milestone 1.1: Input Validation
- [ ] Replace all eval() with safe parsers
- [ ] Add shell escaping to all subprocess calls
- [ ] Implement path validation for file ops
- [ ] Create command whitelist system

### Milestone 1.2: Secrets Management
- [ ] Rotate all exposed API keys
- [ ] Move all secrets to environment variables
- [ ] Add .env.example template
- [ ] Remove hardcoded credentials

### Milestone 1.3: API Protection
- [ ] Add authentication to stats_server.py
- [ ] Implement rate limiting decorators
- [ ] Switch location service to HTTPS
- [ ] Add recipient whitelist for email

---

## Phase 2: Memory Stabilization

**Target:** All MEM-XXX issues resolved

### Milestone 2.1: Thread Safety
- [ ] Add locks to audio buffer singleton
- [ ] Fix emotion.py global state
- [ ] Implement proper thread cleanup

### Milestone 2.2: Resource Limits
- [ ] Bound all queues with maxsize
- [ ] Implement buffer cleanup timers
- [ ] Add context window management
- [ ] Fix UI panel memory accumulation

### Milestone 2.3: Cleanup Systems
- [ ] Fix waveform.stop() implementation
- [ ] Add photo reference circular buffer
- [ ] Implement presence snapshot cleanup
- [ ] Add Ollama call timeouts

---

## Phase 3: Architecture Cleanup

**Target:** All ARCH-XXX issues resolved

### Milestone 3.1: Dependency Resolution
- [ ] Create shared/audio_buffer.py module
- [ ] Remove circular imports
- [ ] Consolidate command routing

### Milestone 3.2: Configuration Consolidation
- [ ] Delete duplicate system_prompt files
- [ ] Merge settings.json/config.json voice settings
- [ ] Delete config/requirements.txt duplicate
- [ ] Add JSON schema validation

### Milestone 3.3: Environment Support
- [ ] Add OLLAMA_URL environment variable
- [ ] Make all paths configurable
- [ ] Add Python version constraint

---

## Phase 4: Workflow System

**Target:** Full hook implementation

### Milestone 4.1: Missing Hooks
- [ ] Implement 8 missing gate validators
- [ ] Create template substitution engine
- [ ] Add automated validation

### Milestone 4.2: Documentation
- [ ] Create CHANGELOG.md
- [ ] Create CONTRIBUTING.md
- [ ] Document threading model
- [ ] Add module interdependency diagram

---

## Phase 5: Feature Completion

**Target:** 100% skill completion

### Milestone 5.1: WIP Skills
- [ ] Complete llava Vision integration
- [ ] Complete Playwright browser automation

### Milestone 5.2: Enhancements
- [ ] Add model download progress
- [ ] Add GPU temperature warnings
- [ ] Voice activity detection
- [ ] Adaptive wake word timing

---

## Completed (v1.0.0)

### 2025-12-29
- [x] 10-agent deep codebase scan
- [x] 81 issues identified and documented
- [x] TODO.md complete rewrite
- [x] ARCHITECTURE.md known issues section
- [x] SKILL_TREE.md tool inventory

### 2025-12-25
- [x] Web UI & GitHub Pages deployment
- [x] Full boot sequence with dynamic AI
- [x] Ambient awareness system
- [x] Real system stats server
- [x] Permission prompts
- [x] Backend terminal fixes
- [x] TTS personality fixes

### Earlier
- [x] 58/60 skills implemented (97%)
- [x] Voice pipeline (Kokoro TTS, Vosk STT)
- [x] Vision system (camera, screenshots)
- [x] 20 tool modules in cora_tools/
- [x] Cyberpunk boot display
- [x] Ollama AI integration

---

## Codebase Summary

| Module | Files | Lines | Status |
|--------|-------|-------|--------|
| src/ | 3 | 6,218 | Entry points |
| ui/ | 15 | 5,500+ | GUI |
| voice/ | 10 | 5,246 | Voice pipeline |
| ai/ | 6 | 2,791 | AI integration |
| cora_tools/ | 20 | 9,600 | Tools |
| services/ | 9 | 2,640 | External |
| config/ | 12 | 970+ | Configuration |
| **TOTAL** | **72+** | **32,795+** | |

---

## Risk Registry

| Risk | Impact | Mitigation |
|------|--------|------------|
| Security vulnerabilities | CRITICAL | Phase 1 priority |
| Memory leaks | HIGH | Phase 2 priority |
| Circular dependencies | HIGH | Phase 3 priority |
| Context overflow | MEDIUM | Token counting |
| API rate limits | MEDIUM | Rate limiting |

---

## Team

| Role | Member |
|------|--------|
| Project Lead | Unity |
| Development | Hackall360, Sponge, GFourteen, Alfreddo |
| Architecture | Unity AI Lab |
| AI Integration | OLLAMA |

---

*Unity AI Lab - C.O.R.A v1.0.0*
*Deep Scan: 2025-12-29 06:06:03*


---

# LEGACY — pre-merge docs/ROADMAP.md (v2.4–2.5 era)

> Preserved verbatim on 2026-10-14 when the root ROADMAP.md moved into docs/. Historical reference only; the live roadmap is above.

# C.O.R.A - Project Roadmap

## Cognitive Operations & Reasoning Assistant

---

## Version History

| Version | Status | Description |
|---------|--------|-------------|
| 1.0.0 | COMPLETED | Core AI assistant foundation |
| 1.0.0 | COMPLETED | Voice integration (TTS/STT) |
| 1.0.0 | COMPLETED | Tool system expansion |
| 1.0.0 | COMPLETED | Full autonomous AI assistant |
| 1.0.0 | CURRENT | Visual boot display & dynamic AI |
| 1.0.0 | PLANNED | Enhanced learning & context |
| 3.0.0 | FUTURE | Production release |

---

## COMPLETED FEATURES (v1.0.0)

### Web UI & GitHub Pages (NEW - 2025-12-25)
- [x] `web/index.html` - Browser-based interface
- [x] Split view (Console + App panels)
- [x] F-100 jet style boot console
- [x] API key modal with validation
- [x] Pollinations + GitHub API integration
- [x] localStorage key persistence
- [x] Fullscreen/split toggle
- [x] Ollama chat integration
- [x] GitHub Actions auto-deploy on push
- [x] Live at: `https://unity-lab-ai.github.io/CORA/`

### Visual Boot Display
- [x] Cyberpunk-themed boot window
- [x] Two-column layout (Status + Log)
- [x] Audio waveform visualization during TTS
- [x] Live system stats (CPU, RAM, GPU, VRAM, Disk)
- [x] Color-coded status indicators
- [x] 1-second refresh rate for stats

### Dynamic AI Responses (NEW)
- [x] `cora_respond()` function for boot phases
- [x] Ollama-powered unique responses
- [x] Phase-specific data injection
- [x] No hardcoded TTS phrases
- [x] Personality-consistent responses

### Image Generation (NEW)
- [x] Pollinations Flux integration
- [x] `imagine` command
- [x] Boot-time image generation test
- [x] Auto-save to data/images/

### Hardware Monitoring (NEW)
- [x] GPU detection via nvidia-smi
- [x] VRAM usage tracking
- [x] Real-time stat updates
- [x] RTX 4070 Ti SUPER tested

### Core Application
- [x] CustomTkinter GUI with floating panel
- [x] System tray integration
- [x] Console boot sequence with TTS narration
- [x] Command parser and execution loop
- [x] Configuration system
- [x] 10-phase boot diagnostic

### Voice System
- [x] Kokoro TTS (neural voice synthesis, af_bella)
- [x] Vosk STT (voice recognition)
- [x] Wake word detection ("Cora")
- [x] TTS mutex for multi-instance coordination
- [x] Emotion-aware speech

### AI Integration
- [x] Ollama backend (llama3.2, llava)
- [x] AI router for model selection
- [x] Context-aware responses
- [x] Code generation and explanation
- [x] Vision analysis via llava

### Tool Modules (17+ implemented)
- [x] **files.py** - File CRUD, JSON ops
- [x] **tts_handler.py** - Speech synthesis
- [x] **ai_tools.py** - Ollama integration
- [x] **calendar.py** - Event management
- [x] **reminders.py** - Reminder system
- [x] **memory.py** - Working memory
- [x] **tasks.py** - Task management
- [x] **windows.py** - Window control
- [x] **code.py** - Code execution
- [x] **screenshots.py** - Screen capture (3840x2160)
- [x] **web.py** - Web fetch/search
- [x] **system.py** - System utilities
- [x] **browser.py** - Browser automation
- [x] **email_tool.py** - Email sending
- [x] **media.py** - Emby media control
- [x] **self_modify.py** - Script creation
- [x] **image_gen.py** - Pollinations AI

### Testing
- [x] TaskManager unit tests (45 tests)
- [ ] AI router tests
- [ ] TTS/STT integration tests
- [ ] GUI component tests

---

## PHASE 5: Enhanced Context (v1.0.0)

### Milestone 5.1: Learning System
- [ ] Conversation history persistence
- [ ] User preference learning
- [ ] Pattern recognition
- [ ] Adaptive responses

### Milestone 5.2: Context Awareness
- [ ] Multi-session memory
- [ ] Project context tracking
- [ ] Workflow automation
- [ ] Smart suggestions

### Milestone 5.3: Integration Improvements
- [x] Git/GitHub integration
- [ ] External API integrations
- [ ] Plugin system
- [ ] Custom tool creation

**Deliverable:** Self-improving assistant with persistent memory

---

## PHASE 6: Production (v3.0.0)

### Milestone 6.1: Stability
- [ ] Comprehensive error handling
- [ ] Performance optimization
- [ ] Edge case coverage
- [ ] 90%+ test coverage

### Milestone 6.2: Documentation
- [x] User guide (READMEs/UserGuide.md)
- [x] Technical documentation (READMEs/NerdReadme.md)
- [x] Setup guide (SETUP.md)
- [ ] API documentation
- [ ] Tool development guide

### Milestone 6.3: Distribution
- [ ] Windows installer
- [ ] Auto-update system
- [ ] Configuration wizard
- [ ] Backup/restore

**Deliverable:** Production-ready release

---

## Architecture

```
C.O.R.A/
├── src/
│   ├── boot_sequence.py   # Visual boot with dynamic AI (1350+ lines)
│   └── cora.py            # CLI application
├── ui/
│   ├── boot_display.py    # Cyberpunk visual display
│   ├── app.py             # Main GUI
│   └── panels.py          # GUI panels
├── voice/
│   ├── tts.py             # Kokoro TTS
│   └── stt.py             # Speech recognition
├── ai/
│   ├── ollama.py          # Ollama client
│   └── context.py         # Context manager
├── web/                   # NEW - GitHub Pages
│   └── index.html         # Browser-based interface
├── .github/
│   └── workflows/
│       └── deploy.yml     # Auto-deploy to Pages
├── cora_tools/            # 17+ tool modules
├── services/              # Weather, location, etc.
├── data/
│   ├── images/            # Generated images
│   └── camera/            # Camera captures
└── tests/                 # Unit test suite
```

---

## Team

| Role | Member |
|------|--------|
| Project Lead | Unity |
| Architecture | Unity AI Lab |
| Development | Hackall360, Sponge, GFourteen, Alfreddo |
| AI Integration | OLLAMA |
| Quality | INTOLERANT |

**Coordination:** GitHub

---

## Current Focus

**Active Version:** 1.0.0
**Next Target:** 1.0.0 - Enhanced Learning
**Priority:** Context persistence and documentation

---

## Recent Achievements (v1.0.0)

- **Web UI deployed to GitHub Pages** (2025-12-25)
- **API key management with validation** (Pollinations + GitHub)
- Visual Boot Display with cyberpunk theme
- Dynamic AI responses via `cora_respond()` function
- Live system stats panel (CPU, RAM, GPU, VRAM, Disk)
- Audio waveform visualization during TTS
- Pollinations Flux image generation
- Full location announcement (City, State, Country)
- News headlines integration
- 75+ Python files across modules
- Complete documentation update

---

## Risk Factors

| Risk | Mitigation |
|------|------------|
| API rate limits | Caching, request batching |
| Model availability | Fallback to local models |
| Voice recognition accuracy | Keyword confirmation |
| Memory bloat | Context window management |
| GPU unavailable | Graceful fallback to CPU |

---

*Unity AI Lab - C.O.R.A Roadmap v1.0.0*
*Last Updated: 2025-12-25*
