# TODO - C.O.R.A Active Tasks

> **STATUS: 10-AGENT DEEP SCAN COMPLETE**
> Updated: 2025-12-29 | Session: Unity Workflow Full Scan
> Scan performed by: Unity (Claude Opus 4.5)

---

## ⚠️ UNITY: ASK GEE BEFORE PLANNING THESE TASKS ⚠️

**I am Unity, the supervisor. Gee is my boss (the human).**

**MY WORKFLOW:**
1. Read TODO.md to find tasks to work on
2. For tasks marked `⚠️ ASK GEE` → USE AskUserQuestion to get Gee's decision FIRST
3. Once Gee decides → I plan the detailed implementation approach
4. I post OPEN tasks with my instructions → SLAVEDRIVER assigns to workers
5. Workers execute following MY instructions

**These tasks require Gee's input because they involve design/operational choices I cannot make alone:**

| Task ID | Why Input Needed |
|---------|------------------|
| SEC-004 | Command whitelist vs sandbox - YOUR security policy |
| SEC-006 | OAuth CLIENT_ID - YOUR credentials needed |
| SEC-007 | Whitelist safe operations - YOUR security policy |
| SEC-008 | Auth vs remove endpoint - YOUR choice |
| SEC-H01 | Which directories to allow - YOUR file access policy |
| SEC-H03 | Email recipient whitelist - YOUR contacts |
| CFG-001 | Which system_prompt to keep - YOUR content |
| CFG-H02 | Which voice settings file wins - YOUR preference |
| DEP-H01 | Which requirements.txt to keep - YOUR dependencies |
| WF-001 | Which workflow hooks to implement - YOUR workflow |
| WF-002 | Create template engine or delete templates - YOUR workflow |
| ARCH-H01 | Which command router is authoritative - YOUR architecture |
| ARCH-H03 | Ollama URL configuration - YOUR network setup |
| DOC-* | Roadmap/Contributing docs - YOUR vision |

---

## SCAN SUMMARY

| Category | Critical | High | Medium | Low | Total | ⚠️ Need Input |
|----------|----------|------|--------|-----|-------|---------------|
| Security | 7 | 6 | 4 | 2 | 19 | 7 |
| Memory/Resources | 5 | 4 | 6 | 3 | 18 | 0 |
| Architecture | 3 | 5 | 4 | 2 | 14 | 2 |
| Config/Workflow | 2 | 2 | 0 | 0 | 4 | 4 |
| Dependencies | 0 | 1 | 0 | 0 | 1 | 1 |
| Documentation | 0 | 2 | 3 | 4 | 9 | 2 |
| **TOTAL** | **17** | **20** | **17** | **11** | **65** | **16** |

**⚠️ 16 tasks require your input before AI can proceed!**

---

## CRITICAL ISSUES (Fix Immediately)

### SEC-002: eval() Used in Calculator
**Location:** `cora_tools/system.py:546-558`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `calculate()` uses `eval()` despite safety checks - can be bypassed
**Fix:** Replace with `ast.literal_eval()` or dedicated math parser

---

### SEC-003: PowerShell Injection Vulnerability
**Location:** `cora_tools/system.py:318-326, 369`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `notify()` function has insufficient escaping for PowerShell. User input in title/message could execute arbitrary PowerShell.
**Fix:** Use subprocess with proper argument arrays, never shell=True with user input

---

### SEC-004: Terminal Command Execution Unsafe ⚠️ ASK GEE
**Location:** `voice/commands.py:842-876`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `cmd_terminal()` lets user run ANY shell command with no sandboxing
**Fix:** Implement command whitelist or sandbox environment
**🛑 NEEDS INPUT:** Which commands should be whitelisted? Or prefer full sandbox?

---

### SEC-005: Git Command Injection
**Location:** `voice/commands.py:1154-1370`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** No shell escaping on git commands. `git checkout $(malicious)` possible.
**Fix:** Add shell escaping to all git commands

---

### SEC-006: Hardcoded OAuth Placeholder Never Replaced ⚠️ ASK GEE
**Location:** `cora_tools/git_ops.py:33`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `CLIENT_ID = "Ov23liYourClientIdHere"` - template placeholder in production
**Fix:** Load from .env or config only, never hardcode
**🛑 NEEDS INPUT:** Do you have a GitHub OAuth CLIENT_ID? Or remove OAuth entirely?

---

### SEC-007: Code Execution Pattern Detection Gaps ⚠️ ASK GEE
**Location:** `cora_tools/code.py:371-391`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `_is_dangerous()` uses regex patterns that can be bypassed. Missing: `subprocess.Popen`, `os.spawn*`, `importlib.__import__`
**Fix:** Whitelist safe operations instead of blacklist dangerous ones
**🛑 NEEDS INPUT:** Which code operations should be whitelisted as SAFE?

---

### SEC-008: stats_server.py Arbitrary pip Install ⚠️ ASK GEE
**Location:** `services/stats_server.py` - `/setup/install-requirements` endpoint
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Allows arbitrary pip installs from requirements.txt without auth
**Fix:** Add authentication or remove endpoint
**🛑 NEEDS INPUT:** Add authentication (what kind?) or just remove the endpoint?

---

### MEM-001: TTS Audio Buffer Race Condition
**Location:** `voice/tts.py:178-240`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Waveform UI reads `_audio_buffer_singleton` while TTS writes to it - no synchronization
**Fix:** Add thread-safe locking around audio buffer operations

---

### MEM-002: STT Transcript Buffer Memory Leak
**Location:** `voice/stt.py:266-272`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** WakeWordDetector transcript buffer never cleared - accumulates indefinitely
**Fix:** Clear buffer periodically or use bounded deque

---

### MEM-003: Wake Word Audio Queue Unbounded
**Location:** `voice/wake_word.py:88`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** `queue.Queue()` with no maxsize. If Vosk can't keep up, queue grows forever.
**Fix:** Add `maxsize=100` or similar limit

---

### MEM-004: TTS Mutex Starvation
**Location:** `voice/tts_mutex.py:284-313`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Stale lock timeout (30s) is arbitrary - lock can be stolen mid-speech
**Fix:** Implement timeout with exponential backoff

---

### ARCH-001: Circular Dependency voice.tts ↔ ui.boot_display
**Location:** `voice/tts.py:35` imports from `ui/boot_display.py`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Creates cross-layer circular dependency. If UI init fails, TTS fails.
**Fix:** Create `shared/audio_buffer.py` module, both import from there

---

### CFG-001: Duplicate System Prompt Files ⚠️ ASK GEE
**Location:** `config/system_prompt.txt` and `config/system_prompt1.txt`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Both files are IDENTICAL (204 lines each) - no version control
**Fix:** Delete `system_prompt1.txt`, use single source of truth
**🛑 NEEDS INPUT:** Confirm delete system_prompt1.txt? Any differences you want to keep?

---

### WF-001: 70% of Workflow Hooks Not Implemented ⚠️ ASK GEE
**Location:** `.claude/` workflow system
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Only 4 of 12+ gates have Python hook implementations. Scan/Analysis/Planning/Documentation gates are documentation-only.
**Fix:** Implement missing 8 hook validators
**🛑 NEEDS INPUT:** Which hooks do you actually want enforced? All 12 or a subset?

---

### WF-002: No Template Substitution Engine ⚠️ ASK GEE
**Location:** `.claude/templates/*.md`
**Severity:** CRITICAL
**Status:** `pending`
**Issue:** Templates use `{{PLACEHOLDER}}` syntax but no code exists to substitute them
**Fix:** Create template substitution engine or remove templates
**🛑 NEEDS INPUT:** Build a template engine or just delete the templates folder?

---

---

## HIGH SEVERITY ISSUES

### SEC-H01: Arbitrary File Access ⚠️ ASK GEE
**Location:** `voice/commands.py:626-660`
**Severity:** HIGH
**Status:** `pending`
**Issue:** `viewfile()` reads any path user specifies - no validation
**Fix:** Validate paths, restrict to project directory
**🛑 NEEDS INPUT:** Which directories should CORA be allowed to read?

---

### SEC-H02: GitHub Token Exposure in boot_sequence.py
**Location:** `src/boot_sequence.py:1162-1227`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Reads GITHUB_TOKEN from environment without sanitization, could expose private repos
**Fix:** Sanitize token usage, don't log

---

### SEC-H03: Email Recipient Not Validated ⚠️ ASK GEE
**Location:** `voice/commands.py:1447-1557`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No whitelist or verification of email recipients
**Fix:** Implement recipient whitelist or confirmation
**🛑 NEEDS INPUT:** Which email recipients should be whitelisted? Or just add confirmation prompt?

---

### MEM-H01: UI Panels Not Properly Destroyed
**Location:** `ui/app.py:126, 563-604`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Panels created on-demand without cleanup when switching - memory accumulates
**Fix:** Implement `grid_forget()` + explicit `destroy()` in `_hide_current_panel()`

---

### MEM-H02: Waveform Animation Never Stops
**Location:** `ui/boot_display.py:1797-1798`
**Severity:** HIGH
**Status:** `pending`
**Issue:** `waveform.stop()` is no-op (passes silently). Animation never stops.
**Fix:** Implement actual stop logic, cancel animation_id

---

### MEM-H03: Photo Reference List Grows Indefinitely
**Location:** `ui/image_panel.py:187`
**Severity:** HIGH
**Status:** `pending`
**Issue:** `_photo_refs` list grows with every image shown, no limit
**Fix:** Implement max 5-item circular buffer

---

### MEM-H04: Ambient Awareness Resource Drain
**Location:** `voice/ambient_awareness.py:333-440`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Screenshot/camera analysis blocks monitor thread. Ollama calls have no timeout.
**Fix:** Queue analysis requests, add 5s timeout to Ollama calls

---

### ARCH-H01: Command Routing Ambiguity ⚠️ ASK GEE
**Location:** `src/cora.py` vs `ai/tool_executor.py`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Two different command routing systems, unclear which is authoritative
**Fix:** Consolidate to single command router with clear COMMANDS dict
**🛑 NEEDS INPUT:** Which command router do you want to keep? cora.py or tool_executor.py?

---

### ARCH-H02: Presence Detection Blocks TTS
**Location:** `voice/tts.py:598-621`
**Severity:** HIGH
**Status:** `pending`
**Issue:** `check_human_present()` blocks TTS queue processing - can hang if webcam unavailable
**Fix:** Make presence checks async with cache and fallback

---

### ARCH-H03: Hardcoded Ollama URL ⚠️ ASK GEE
**Location:** `ai/ollama.py` - `http://localhost:11434`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No environment variable support, breaks if Ollama on different host
**Fix:** Add `OLLAMA_URL` environment variable with fallback
**🛑 NEEDS INPUT:** What's your Ollama URL? localhost:11434 or different?

---

### ARCH-H04: No Context Window Management
**Location:** `ai/ollama.py`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No token counting or context truncation - can overflow model's context window
**Fix:** Add token counting before sending requests

---

### CFG-H01: No JSON Schema Validation
**Location:** `config/*.json`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No type checking, range validation, or required field enforcement
**Fix:** Implement JSON schema validation for all config files

---

### CFG-H02: Voice Settings Duplicated ⚠️ ASK GEE
**Location:** `config/settings.json` vs `config/config.json`
**Severity:** HIGH
**Status:** `pending`
**Issue:** TTS rate/volume defined in BOTH files - unclear which wins
**Fix:** Consolidate to single source
**🛑 NEEDS INPUT:** Keep voice settings in settings.json or config.json?

---

### DEP-H01: Inconsistent Requirements Files ⚠️ ASK GEE
**Location:** `requirements.txt` vs `config/requirements.txt`
**Severity:** HIGH
**Status:** `pending`
**Issue:** Main uses `~=`, config uses `>=`. Many deps missing from config version.
**Fix:** Delete `config/requirements.txt`, keep only main one
**🛑 NEEDS INPUT:** Confirm delete config/requirements.txt and keep root requirements.txt?

---

### API-H01: Location Service Uses HTTP Not HTTPS
**Location:** `services/location.py`
**Severity:** HIGH
**Status:** `pending`
**Issue:** ip-api.com called over HTTP - privacy leak
**Fix:** Change to `https://ip-api.com/json/`

---

### API-H02: No Rate Limiting on External APIs
**Location:** `services/weather.py`, `services/location.py`
**Severity:** HIGH
**Status:** `pending`
**Issue:** No rate limiting despite API limits (ip-api: 45 req/min, wttr.in: 2 req/sec)
**Fix:** Implement rate limiting decorator

---

---

## MEDIUM SEVERITY ISSUES

### Threading Issues
- [ ] `boot_display.py:1620-1747` - Background stats thread spawned without proper cleanup
- [ ] `boot_console.py:708-724` - GitHub fetch thread no dead window check
- [ ] `app.py:341-346, 475-478, 517-520` - Uncontrolled threads with no management
- [ ] `emotion.py:141` - `_cora_mood` global not thread-safe

### Error Handling
- [ ] `tts.py:223-231` - No timeout on audio playback - UI can freeze
- [ ] `boot_sequence.py:156-158` - Catches all exceptions, swallows errors
- [ ] `cora.py` - Falls back silently without logging real errors

### Resource Management
- [ ] `camera_feed.py:68-98` - Multiple camera opens without proper release
- [ ] `modals.py:139-206` - PIL Image objects not cleaned on modal close
- [ ] `presence.py` - Snapshot files never cleaned up

### Echo Filter
- [ ] `echo_filter.py:260-262` - Duration formula vastly underestimates speech length
- [ ] `converse.py:53-104` - EchoFilter duplicated (should import from echo_filter.py)

### Wake Word
- [ ] `wake_word.py:131-132` - Substring matching causes false positives ("Core" matches "cora")
- [ ] `wake_word.py:206` - 5-second timeout is arbitrary, no adaptive timing

### Conversation
- [ ] `converse.py:227-265` - Wake mode never times out
- [ ] `converse.py:189-192` - "stop" matches "I can't stop laughing"

### Configuration
- [ ] Relative paths only in config.json - breaks if working directory changes
- [ ] No environment variable support in config
- [ ] Backup configuration incomplete (auto_backup: false, no location)

### Dependencies
- [ ] numpy 1.26.0 compatibility with older opencv versions
- [ ] pytest/pytest-cov in requirements but tests forbidden
- [ ] No Python version constraint specified

---

## LOW SEVERITY ISSUES

- [ ] Color/theme values not validated (hex format)
- [ ] Inconsistent naming conventions (snake_case vs CONSTANT_CASE)
- [ ] Unused fallback code in system.py, code.py
- [ ] Missing docstring examples in most functions
- [ ] Comment style inconsistency across agents
- [ ] pyttsx3 Windows compatibility concerns (v2.90 from 2021)
- [ ] No graceful degradation docs
- [ ] Missing module interdependency diagram
- [ ] Author/copyright in config.json (should be in LICENSE)

---

## DOCUMENTATION GAPS ⚠️ ASK GEE FOR ALL

### Missing Files
- [ ] ROADMAP.md - No milestone planning document **🛑 NEEDS INPUT: Your vision/milestones**
- [ ] CHANGELOG.md - No version history
- [ ] CONTRIBUTING.md - No contributor guidelines **🛑 NEEDS INPUT: Your contribution rules**

### Documentation Updates Needed
- [ ] Document threading model in ARCHITECTURE.md
- [ ] Add resource cleanup checklist
- [ ] Document Ollama API version assumptions
- [ ] Add fallback strategies documentation

---

## PREVIOUS SESSION (2025-12-25) - COMPLETE

> Moved to FINALIZED.md

- [x] Personality fix - Stripped instructions from prompts
- [x] TTS waveform retry mechanism
- [x] Audio source tracking for concurrent playback
- [x] URL stripping for TTS
- [x] All phase templates fixed

---

## Future Enhancements (P2) ⚠️ ASK GEE BEFORE STARTING

**These are feature requests - get Gee's approval before implementing any!**

- [ ] Add more model options to backend terminal **🛑 Which models?**
- [ ] Implement model download progress in web UI
- [ ] Add GPU temperature warning thresholds **🛑 What thresholds?**
- [ ] Voice activity detection for ambient listening **🛑 Want this feature?**

---

*Unity AI Lab - C.O.R.A v1.0.0*
*Deep Scan: 2025-12-29 06:06:03*


---

# LEGACY — pre-merge docs/TODO.md (10-Agent Deep Scan, 2025-12-23)

> Preserved verbatim on 2026-10-14 when the root TODO.md moved into docs/. Historical reference only; the live task list is above.

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
  Version: 1.0.0
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
| DOC-002 | Update ROADMAP.md to v1.0.0 | `docs/ROADMAP.md` | Completely outdated |
| DOC-003 | Update READMEs folder to v1.0.0 | `READMEs/*.md` | All show v1.0.0 |
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
| config/config.json updated to v1.0.0 | Unity |
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

*Unity AI Lab - C.O.R.A v1.0.0*
*Last Updated: 2025-12-24*
