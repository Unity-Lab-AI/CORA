# C.O.R.A CONSOLIDATED TODO
## Unity Supervisor - Task Queue Synced with ClaudeColab

**Generated:** 2025-12-23
**Total Tasks Posted:** 37
**Project:** cora
**Compliance:** 87%

---

## TASK QUEUE SUMMARY

### P9 CRITICAL (3 tasks)
| ID | Task | Assigned | Status |
|----|------|----------|--------|
| BUG-003 | Fix TTS engine selection factory | Slave2 | PENDING |
| BUG-004 | Fix boot TTS race condition | Slave1 | PENDING |
| BUG-005 | Fix wake detector cleanup | Slave2 | PENDING |

### P8 HIGH (4 tasks)
| ID | Task | Assigned | Status |
|----|------|----------|--------|
| CORA-001 | Create services/cli_popup.py | Slave1 | PENDING |
| CORA-003 | Wire cora.py to tools/tasks.py | Slave2 | PENDING |
| ARCH-001 | Connect GUI to cora.py properly | Slave1 | PENDING |
| FEAT-001 | CLI terminal popup service | Slave2 | PENDING |

### P7 MEDIUM-HIGH (8 tasks)
| ID | Task | Assigned | Status |
|----|------|----------|--------|
| CORA-002 | Update services/__init__.py exports | Slave1 | PENDING |
| CORA-004 | Wire boot_console to emotion.py | Slave2 | PENDING |
| CORA-011 | Wire wake word detection | Slave1 | PENDING |
| CORA-012 | Integrate voice_listener on boot | Slave2 | PENDING |
| ARCH-003 | Integrate claude-v1.1 voice | Slave1 | PENDING |
| PHASE10-001 | Always-running background service | Slave1 | PENDING |
| VOICE-001 | Complete converse mode | Slave2 | PENDING |
| FEAT-002 | Add cmd_open_cli() to cora.py | Slave1 | PENDING |

### P6 MEDIUM (7 tasks)
| ID | Task | Assigned | Status |
|----|------|----------|--------|
| CORA-005 | Add cmd_open_cli() command | Slave1 | PENDING |
| CORA-010 | Voice selection dropdown | Slave2 | PENDING |
| ARCH-002 | Consolidate config files | Slave2 | PENDING |
| CODE-005 | Wire settings panel save | Slave2 | PENDING |
| UI-002 | Complete query panels/hotbar | Slave1 | PENDING |
| PHASE10-003 | Safety sandboxing self_modify | Slave1 | PENDING |
| VOICE-002 | Copy voice config to .claude/ | Slave1 | PENDING |

### P5 LOW-MEDIUM (7 tasks)
| ID | Task | Assigned | Status |
|----|------|----------|--------|
| CORA-009 | Create ui/assets/ folder | Slave1 | PENDING |
| IMPL-002 | Add logging system | Slave2 | PENDING |
| CODE-006 | Throttle presence detection | Slave1 | PENDING |
| UI-001 | Connect splash to boot checks | Slave2 | PENDING |
| DATA-001 | Calendar event persistence | Slave2 | PENDING |
| DATA-002 | Memory auto-save | Slave1 | PENDING |
| SEC-001 | Move API keys to env vars | Slave2 | PENDING |

### P4 LOW (3 tasks)
| ID | Task | Assigned | Status |
|----|------|----------|--------|
| IMPL-003 | Fix screenshot save location | Slave1 | PENDING |
| PHASE10-002 | Create installer/packaging | Slave2 | PENDING |
| SEC-002 | Dependency version pins | Slave1 | PENDING |

### P3 DOCS (2 tasks)
| ID | Task | Assigned | Status |
|----|------|----------|--------|
| DOCS-001 | Create READMEs/ folder | Slave2 | PENDING |
| DOCS-002 | Update README.md | Slave1 | PENDING |

---

## COMPLETED (From Previous Sessions)

| Task | Completed By |
|------|--------------|
| tools/tasks.py created | Slave1 |
| tools/web.py verified | Slave1 |
| ai/prompts.py created | Slave1 |
| voice/echo_filter.py created | Slave1 |
| ui/monitor_panel.py created | Slave1 |
| think() method in ai/ollama.py | Slave1 |
| boot_sequence() integration | Slave1 |
| System tray integration | Slave1 |
| 3 boot checks (forecast, reminders, vosk) | Slave1 |
| config/config.json updated to v2.2.0 | Unity |
| tools/windows.py created (21KB) | Unity |
| tools/code.py created (23KB) | Unity |
| Logging integrated in cora.py | Unity |

---

## WORKER ASSIGNMENT SUMMARY

| Worker | P9 | P8 | P7 | P6 | P5 | P4 | P3 | Total |
|--------|----|----|----|----|----|----|----|----|
| Slave1 | 1 | 2 | 4 | 4 | 3 | 2 | 1 | 17 |
| Slave2 | 2 | 2 | 4 | 3 | 4 | 1 | 1 | 17 |

---

*Unity AI Lab - C.O.R.A v2.2.0*
*Synced with ClaudeColab project: cora*
*Last Updated: 2025-12-23*
