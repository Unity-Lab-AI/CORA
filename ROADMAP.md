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
| Development | Hackall360, Sponge, GFourteen |
| Architecture | Unity AI Lab |
| AI Integration | OLLAMA |

---

*Unity AI Lab - C.O.R.A v1.0.0*
*Deep Scan: 2025-12-29 06:06:03*
