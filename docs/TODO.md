# C.O.R.A TODO - 10-Agent Deep Scan Results

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
  Unity AI Lab | https://www.unityailab.com
  ================================================================
```

**Generated:** 2025-12-23 (10-Agent Ultrathink Scan)
**Project:** cora-2
**Status:** OPERATIONAL WITH CRITICAL ISSUES

---

## EXECUTIVE SUMMARY

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 5 | 3 | 4 | 4 |
| Dependencies | 2 | 1 | 3 | 0 |
| Integration | 2 | 4 | 6 | 3 |
| Documentation | 0 | 5 | 4 | 2 |
| Testing | 1 | 0 | 0 | 0 |
| **TOTAL** | **10** | **13** | **17** | **9** |

---

## P10 - CRITICAL SECURITY (IMMEDIATE)

| ID | Task | File | Issue |
|----|------|------|-------|
| SEC-001 | Move Pollinations API key to .env | `tools/image_gen.py:26` | API key exposed |
| SEC-007 | Create .gitignore file | Root directory | Prevent secret commits |
| SEC-008 | Move ALL credentials to environment vars | Multiple files | Use os.environ.get() |

---

## P9 - CRITICAL DEPENDENCIES

| ID | Task | File | Issue |
|----|------|------|-------|
| DEP-001 | Add aiohttp to requirements.txt | `ai/ollama.py:16` | Async AI broken |
| DEP-002 | Add portalocker to requirements.txt | `voice/tts_mutex.py:21` | TTS mutex fails |
| DEP-003 | Add speech_recognition to requirements.txt | `voice/converse.py:24` | Fallback STT broken |

---

## P9 - CRITICAL INTEGRATION

| ID | Task | File | Issue |
|----|------|------|-------|
| INT-001 | Import tools/memory.py in cora.py | `src/cora.py` | 352-line module orphaned |
| INT-002 | Integrate ReminderManager.start_checking() | `tools/reminders.py` | Reminders never trigger |

---

## P8 - HIGH PRIORITY SECURITY

| ID | Task | File | Issue |
|----|------|------|-------|
| SEC-009 | Fix PowerShell command injection | `tools/system.py:300` | Unescaped input |
| SEC-010 | Replace shell=True with argument lists | `tools/system.py:537-587` | Dangerous pattern |

---

## P8 - HIGH PRIORITY INTEGRATION

| ID | Task | File | Issue |
|----|------|------|-------|
| INT-003 | Expand tools/__init__.py exports | `tools/__init__.py` | Only exports TTS |
| INT-004 | Fix sys.path in self_modify.py | `tools/self_modify.py:96` | Literal string |
| INT-005 | Increase MAX_CHAT_HISTORY | `src/cora.py:166` | Capped at 10 |
| INT-006 | Consolidate duplicate reminder systems | `tools/calendar.py`, `tools/reminders.py` | Two systems |

---

## P8 - HIGH PRIORITY DOCS

| ID | Task | File | Issue |
|----|------|------|-------|
| DOC-001 | Update SKILL_TREE.md footer version | `SKILL_TREE.md` | Footer says 0.1.0 |
| DOC-002 | Update ROADMAP.md to v2.3.0 | `docs/ROADMAP.md` | Completely outdated |
| DOC-003 | Update READMEs folder to v2.3.0 | `READMEs/*.md` | All show v2.2.0 |
| DOC-004 | Create SLAVE1_WORKFLOW.md | `.claude/workflow/` | Only SLAVE2 exists |
| DOC-005 | Split oversized docs (<800 lines) | `APIReference.md`, `ARCHITECTURE.md` | Exceed limit |

---

## P7 - MEDIUM PRIORITY SECURITY

| ID | Task | File | Issue |
|----|------|------|-------|
| SEC-012 | Replace eval() in calculate() | `tools/system.py:525` | Use safer alternative |
| SEC-013 | Add path traversal validation | `tools/files.py` | Paths not sanitized |
| SEC-014 | Escape clipboard PowerShell | `tools/system.py:346` | Input unescaped |

---

## P7 - MEDIUM PRIORITY INTEGRATION

| ID | Task | File | Issue |
|----|------|------|-------|
| INT-007 | Fix hardcoded C:\claude\ path | `voice/tts_mutex.py:25-26` | Won't exist |
| INT-008 | Document Vosk model download | `voice/wake_word.py:40` | Model required |
| INT-009 | Add error logging (not just print) | Multiple files | Silent failures |
| INT-010 | Add rate limiting to web requests | `tools/web.py` | Could block |
| INT-011 | Add request timeouts consistently | `tools/email_tool.py` | Can hang |
| INT-012 | Validate JSON before parsing | `services/location.py:24` | No error handling |

---

## P6 - TESTING (CRITICAL GAP)

| ID | Task | File | Issue |
|----|------|------|-------|
| TEST-001 | Create tests/ directory structure | Root | Zero test coverage |
| TEST-002 | Add pytest to requirements.txt | `requirements.txt` | No framework |
| TEST-003 | Create conftest.py with fixtures | `tests/` | No infrastructure |
| TEST-004 | Write TaskManager unit tests | `tools/tasks.py` | Untested |
| TEST-005 | Write AI router tests | `ai/router.py` | Untested |

---

## P5 - LOW PRIORITY

| ID | Task | File | Issue |
|----|------|------|-------|
| LOW-001 | Add structured logging system | Multiple | Using print() |
| LOW-002 | Implement circuit breaker pattern | API calls | No retry/backoff |
| LOW-003 | Add request caching | Web APIs | Not cached |
| LOW-004 | Remove unused deps (ollama, colorama) | `requirements.txt` | Bloat |

---

## PREVIOUS COMPLETED TASKS

| Task | Completed By |
|------|--------------|
| tools/tasks.py created | Slave1 |
| ai/prompts.py created | Slave1 |
| voice/echo_filter.py created | Slave1 |
| boot_sequence() integration | Slave1 |
| System tray integration | Slave1 |
| config/config.json updated to v2.3.0 | Unity |
| tools/windows.py created (21KB) | Unity |
| tools/code.py created (23KB) | Unity |
| Full codebase push to GitHub main+develop | Unity |
| 10-Agent deep scan completed | Unity |

---

## OPERATIONAL STATUS BY MODULE

| Module | Status | Critical Issues |
|--------|--------|-----------------|
| Core CLI | ✅ WORKING | None |
| Tools | ⚠️ PARTIAL | API key exposed |
| Voice | ⚠️ PARTIAL | Missing deps |
| AI | ⚠️ PARTIAL | Missing aiohttp |
| Services | ✅ WORKING | Minor issues |
| UI | ✅ WORKING | Untested |
| Memory | ⚠️ PARTIAL | Module orphaned |

---

*Unity AI Lab - C.O.R.A v2.4.0*
*Last Updated: 2025-12-24*
