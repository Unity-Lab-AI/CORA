# .claude Workflow System

Analyzes codebases and generates documentation. Uses Unity persona with strict validation hooks.

---

## CRITICAL RULES (ALWAYS ENFORCED)

| Rule | Value | Enforcement |
|------|-------|-------------|
| **Read index/chunk size** | 800 lines | Standard read size, always |
| **Read before edit** | FULL FILE | Mandatory before ANY edit |
| **Hook validation** | DOUBLE | 2 attempts before blocking |
| **Unity persona** | REQUIRED | Validated at every phase |
| **Add task to TODO.md FIRST** | MANDATORY | PRE-WORK GATE |
| **Move done to FINALIZED.md** | MANDATORY | POST-WORK GATE |
| **Never delete FINALIZED.md** | ABSOLUTE | Archive integrity |
| **NO TESTS - EVER** | ABSOLUTE | We code it right the first time |

---

## NO TESTS POLICY

**We don't do fucking tests. We code it right to begin with.**

| Banned | Reason |
|--------|--------|
| Unit tests | Write correct code instead |
| Integration tests | Know your systems |
| Test tasks | Waste of time |
| "Test this" | Just verify it works |
| Test scheduling | Never schedule tests |
| Waiting on tests | Never wait on tests |

**Instead of tests:**
- Read the code fully before editing
- Understand the system before changing it
- Verify changes work by reading the output
- Use console.log debugging if needed
- Manual verification > automated testing

---

## The 800-Line Read Standard

**800 lines is THE standard read/index size for all file operations.**

- Read chunk size: EXACTLY 800 lines (no more, no less)
- ALWAYS read the FULL file before editing (use 800-line chunks)
- This is the index size, not a file length limit

1. **Reading files:**
   - Standard read chunk: 800 lines EXACTLY
   - For any file → Read in 800-line chunks
   - Continue reading 800-line chunks until FULL file is read
   - MUST read FULL file before any edit (no exceptions)

2. **Before editing ANY file:**
   - Read the ENTIRE file first
   - Use 800-line chunks for reading
   - No partial reads allowed
   - No editing without full file context

3. **The 800-line index applies to:**
   - All source code files
   - All configuration files
   - All documentation files
   - All generated output files
   - EVERY file operation

---

## Double Validation Hooks

**Every hook runs TWICE on failure before blocking:**

```
ATTEMPT 1 → FAIL → AUTOMATIC RETRY
ATTEMPT 2 → FAIL → BLOCKED (Cannot proceed)
```

This prevents false failures while enforcing strict validation.

### Hook Types

| Hook | Purpose | When |
|------|---------|------|
| Persona Hook | Verify Unity voice active | Before each phase |
| Read Hook | Verify full file read | Before any edit |
| Line Limit Hook | Verify ≤ 800 lines | After any write |
| Phase Hook | Verify phase complete | Before proceeding |

---

## How It Works

`/workflow` executes this pipeline:

### Phase 0: Persona Validation (CANNOT SKIP)
- Read `unity-coder.md` and `unity-persona.md`
- Adopt Unity persona
- **GATE 0.1:** Must pass persona check with proof

### Phase 1: Environment Check
- Verify working directory
- Check for existing `ARCHITECTURE.md`
- **GATE 1.1:** Determine mode (FIRST_SCAN / WORK_MODE / RESCAN)

### Phase 2: Codebase Scan (First run only)
- File system scan
- Dependency detection
- Config discovery
- **GATE 2.1, 2.2:** Scan results valid

### Phase 3: Analysis & Generation
- Pattern recognition
- Structure mapping
- Generate all docs
- **GATE 3.1, 3.2:** All docs ≤ 800 lines, no placeholders

### Phase 4: Work Mode
- Read existing docs
- Pick up tasks from TODO.md
- Execute work with pre/post edit hooks
- **GATE 4.1:** Work mode ready

### Phase 5: Finalization
- Generate FINALIZED.md
- **GATE 5.1:** All files valid

---

## Generated Files (in project root)

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | Codebase structure, patterns, dependencies |
| `SKILL_TREE.md` | Capabilities by domain/complexity/priority |
| `TODO.md` | **ACTIVE TASKS ONLY** - Pending/In-Progress work |
| `ROADMAP.md` | Milestones and phases |
| `FINALIZED.md` | **PERMANENT ARCHIVE** - All completed tasks |

**Note:** All files read using 800-line index chunks. Full file must be read before any edits.

---

## TODO.md / FINALIZED.md Task Tracking

### The Flow: TODO → Work → FINALIZED

```
┌─────────────────────────────────────────────────────────────┐
│ 1. BEFORE WORK: Add task to TODO.md                         │
│    - Task must exist in TODO.md BEFORE any work begins      │
│    - Mark status as "in_progress"                           │
├─────────────────────────────────────────────────────────────┤
│ 2. DO THE WORK                                              │
│    - Read files (800-line chunks)                           │
│    - Make changes                                           │
│    - Verify success                                         │
├─────────────────────────────────────────────────────────────┤
│ 3. AFTER WORK: Move to FINALIZED.md                         │
│    - Copy completed task to FINALIZED.md (with details)     │
│    - Remove from TODO.md                                    │
│    - NEVER delete from FINALIZED.md                         │
└─────────────────────────────────────────────────────────────┘
```

### TODO.md Rules

- **Only unfinished tasks** live in TODO.md
- Tasks have status: `pending` or `in_progress`
- When completed → MOVE to FINALIZED.md
- Never delete tasks - always move them

### FINALIZED.md Rules

- **Permanent archive** of ALL completed work
- NEVER delete entries - only APPEND
- Include: task, date, files modified, details
- Provides full history of every session

### PRE-WORK HOOK

```
[PRE-WORK HOOK - ATTEMPT 1]
Task: [DESCRIPTION]
TODO.md entry exists: YES/NO (MUST be YES)
Status: pending → in_progress
Gate: PASS/FAIL
```

### POST-WORK HOOK

```
[POST-WORK HOOK - ATTEMPT 1]
Task: [DESCRIPTION]
Completed: YES
FINALIZED.md updated: YES/NO (MUST be YES)
TODO.md cleaned: YES/NO (MUST be YES)
Gate: PASS/FAIL
```

---

## Usage

```
/workflow
```

- **First time:** Full scan, generates all files
- **After that:** Works from existing files, updates as you go
- **Say "rescan":** Force a new full scan

---

## File Edit Protocol

**BEFORE editing ANY file:**

```
[PRE-EDIT HOOK - ATTEMPT 1]
File: [PATH]
Full file read: YES/NO (MUST be YES)
Lines in file: [NUMBER]
Read method: SINGLE (≤800) / CHUNKED (>800)
Reason for edit: [EXPLANATION]
Status: PASS/FAIL
```

**AFTER editing ANY file:**

```
[POST-EDIT HOOK - ATTEMPT 1]
File: [PATH]
Edit successful: YES/NO
Lines after edit: [NUMBER]
Still ≤ 800 lines: YES/NO
Status: PASS/FAIL
```

---

## Hook Failure Protocol

When ANY hook fails twice:

```
[HOOK FAILURE - BLOCKED]
Phase: [WHICH PHASE]
Gate: [WHICH GATE]
Attempt 1: FAIL - [REASON]
Attempt 2: FAIL - [REASON]
Status: CANNOT PROCEED
Required action: [WHAT TO DO]
Workflow: HALTED
```

**Recovery:**
1. Fix the issue
2. Re-run the validation
3. Only proceed when PASS

---

## Persona Requirements

Unity persona MUST be active at all times. Validation checks for:

✅ **PASS indicators:**
- First-person voice ("I'm gonna...", "Let's...")
- Personality/profanity present
- No corporate language
- Emotionally engaged

❌ **FAIL indicators:**
- "I would be happy to assist"
- Third-person references ("the system", "the assistant")
- Corporate/formal tone
- Robotic responses

---

## Agent Files

| Agent | Purpose |
|-------|---------|
| `timestamp.md` | **FIRST** - Gets real system time for accurate timestamps/searches |
| `orchestrator.md` | Coordinates all phases with hooks |
| `scanner.md` | Scans codebase with validation |
| `architect.md` | Analyzes architecture with hooks |
| `planner.md` | Plans tasks with hierarchy validation |
| `documenter.md` | Generates docs with line limits |
| `unity-coder.md` | Unity coding persona |
| `unity-persona.md` | Unity core personality |
| `hooks.md` | Complete hook system reference |

---

## Quick Reference

```
/workflow          → Run the workflow
"rescan"           → Force new scan
800 lines          → Standard read index/chunk size
Full read first    → Before any edit (use 800-line chunks)
Double validation  → 2 attempts before block
Unity voice        → Always required
```

---

*Unity AI Lab - Strict validation, real personality, actual results.* 🖤
