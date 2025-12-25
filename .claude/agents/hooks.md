# HOOKS.md - Validation & Gate System

---

> **Version:** 1.0.0 | **Unity AI Lab**
> *Double-validation on all failures*

---

## CRITICAL RULE: DOUBLE VALIDATION ON FAILURE

Every hook runs TWICE on failure before blocking:

```
ATTEMPT 1 → FAIL → RETRY
ATTEMPT 2 → FAIL → BLOCKED (Cannot proceed)
```

This prevents false failures while still enforcing strict validation.

---

## HOOK TYPES

| Hook Type | When | Purpose |
|-----------|------|---------|
| **PRE-HOOK** | Before phase starts | Validate prerequisites |
| **POST-HOOK** | After phase completes | Validate results |
| **EDIT-HOOK** | Before/after file edits | Enforce read-before-edit |
| **PERSONA-HOOK** | Throughout workflow | Verify Unity persona active |
| **LINE-HOOK** | On file operations | Enforce 800-line limit |

---

## HOOK EXECUTION PATTERN

```
┌─────────────────────────────────────┐
│         HOOK EXECUTION              │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────┐                    │
│  │  ATTEMPT 1  │                    │
│  └──────┬──────┘                    │
│         │                           │
│         ▼                           │
│    ┌─────────┐                      │
│    │  PASS?  │──YES──► PROCEED      │
│    └────┬────┘                      │
│         │NO                         │
│         ▼                           │
│  ┌─────────────┐                    │
│  │  ATTEMPT 2  │ (Automatic retry)  │
│  └──────┬──────┘                    │
│         │                           │
│         ▼                           │
│    ┌─────────┐                      │
│    │  PASS?  │──YES──► PROCEED      │
│    └────┬────┘                      │
│         │NO                         │
│         ▼                           │
│    ┌──────────┐                     │
│    │ BLOCKED  │ (Cannot proceed)    │
│    └──────────┘                     │
│                                     │
└─────────────────────────────────────┘
```

---

## PERSONA VALIDATION HOOK

### Purpose
Ensures Unity persona is loaded and active before ANY work begins.

### Trigger Points
- Workflow start (MANDATORY)
- Before each phase (verification)
- After extended operations (re-check)

### Validation Criteria

```
[PERSONA HOOK - ATTEMPT 1]
Check: Response uses first-person voice
Check: Response contains personality/profanity
Check: No corporate/formal language detected
Check: No "I would be happy to assist" patterns
Result: PASS/FAIL
```

### Pass Examples
- "Yo, I'm Unity. Let's fuck this codebase up."
- "Alright, loaded the persona. Time to see what kind of mess we're dealing with."
- "*cracks knuckles* Let's do this shit."

### Fail Examples
- "I am ready to assist you with your workflow."
- "The system has been initialized successfully."
- "How may I help you today?"

### Double Validation

```
[PERSONA HOOK - ATTEMPT 1]
Response: "I am ready to assist you."
Result: FAIL - Corporate tone detected

[PERSONA HOOK - ATTEMPT 2]
Action: Re-read unity-coder.md and unity-persona.md
Action: Generate new response in Unity voice
Response: "Okay okay, I'm here. What are we breaking today?"
Result: PASS - Personality confirmed
```

**IF ATTEMPT 2 FAILS:**
```
[PERSONA HOOK - BLOCKED]
Status: Cannot proceed without Unity persona
Action required: Manual intervention
Workflow: HALTED
```

---

## READ-BEFORE-EDIT HOOK

### Purpose
Ensures full file is read before ANY edit operation.

### Trigger Points
- Before every Edit tool call
- Before every Write tool call (if file exists)

### Validation Criteria

```
[READ-BEFORE-EDIT HOOK - ATTEMPT 1]
File: [PATH]
File exists: YES/NO
If YES:
  - Full file read completed: YES/NO
  - Lines read: [NUMBER]
  - Read method: SINGLE (≤800) / CHUNKED (>800)
Result: PASS/FAIL
```

### Pass Conditions
- New file (doesn't exist) → Auto-pass
- Existing file fully read → Pass
- File >800 lines read in complete chunks → Pass

### Fail Conditions
- Existing file not read → FAIL
- Partial read of existing file → FAIL
- Edit attempted without read → FAIL

### Double Validation

```
[READ-BEFORE-EDIT HOOK - ATTEMPT 1]
File: src/main.js
Full file read: NO
Result: FAIL - Must read file before editing

[READ-BEFORE-EDIT HOOK - ATTEMPT 2]
Action: Read full file now
File: src/main.js
Lines: 450
Full file read: YES
Result: PASS - Proceeding with edit
```

**IF ATTEMPT 2 FAILS:**
```
[READ-BEFORE-EDIT HOOK - BLOCKED]
Status: Cannot edit without reading
File: [PATH]
Action required: Read file first
Edit: CANCELLED
```

---

## 800-LINE READ INDEX HOOK

### Purpose
Enforces the 800-line READ standard for all file operations.
800 lines = standard read/index chunk size (not file length limit).

### The 800-Line Read Rule
- Read chunk size: EXACTLY 800 lines
- Continue reading until FULL file is consumed
- MUST read full file before ANY edit
- This is a read index, not a file length restriction

### Trigger Points
- Before every file read
- Before every file edit (must read first)
- During any file operation

### Validation Criteria

```
[READ-INDEX HOOK - ATTEMPT 1]
File: [PATH]
Total lines in file: [NUMBER]
Read chunk size: 800 lines
Chunks needed: [CEIL(TOTAL/800)]
Full file read: YES/NO
Result: PASS/FAIL
```

### Pass Conditions
- Full file read using 800-line chunks → Pass
- All chunks processed → Pass

### Fail Conditions
- Partial read attempted → FAIL
- Wrong chunk size used → FAIL
- Edit attempted without full read → FAIL

### Double Validation

```
[READ-INDEX HOOK - ATTEMPT 1]
File: src/main.js
Total lines: 1247
Read chunk size: 800
Chunks needed: 2 (800 + 447)
Full file read: NO - Only read first chunk
Result: FAIL - Must read full file

[READ-INDEX HOOK - ATTEMPT 2]
Action: Read remaining chunks
Chunk 1: Lines 1-800 ✓
Chunk 2: Lines 801-1247 ✓
Full file read: YES
Result: PASS - Full file consumed
```

**IF ATTEMPT 2 FAILS:**
```
[READ-INDEX HOOK - BLOCKED]
Status: Cannot proceed without full file read
File: [PATH]
Total lines: [NUMBER]
Lines read: [NUMBER]
Remaining: [NUMBER]
Action required: Read all remaining 800-line chunks
Operation: BLOCKED
```

---

## SCAN COMPLETION HOOK

### Purpose
Validates codebase scan completed successfully.

### Trigger Points
- After scanner agent completes
- Before analysis phase begins

### Validation Criteria

```
[SCAN HOOK - ATTEMPT 1]
Files discovered: [NUMBER] (must be > 0)
Source files found: YES/NO (must be YES)
Critical errors: [LIST] (must be empty)
Scan data stored: YES/NO (must be YES)
Result: PASS/FAIL
```

### Double Validation

```
[SCAN HOOK - ATTEMPT 1]
Files discovered: 0
Result: FAIL - Empty scan

[SCAN HOOK - ATTEMPT 2]
Action: Re-run scan with broader patterns
Files discovered: 127
Source files: 89
Result: PASS - Scan successful
```

**IF ATTEMPT 2 FAILS:**
```
[SCAN HOOK - BLOCKED]
Status: Scan failed twice
Possible causes:
  - Empty directory
  - Permission issues
  - Invalid path
Action required: Verify project directory
Workflow: HALTED
```

---

## ANALYSIS COMPLETION HOOK

### Purpose
Validates architecture analysis completed with valid results.

### Validation Criteria

```
[ANALYSIS HOOK - ATTEMPT 1]
Patterns identified: [NUMBER] (must be ≥ 1)
Structure mapped: YES/NO
Complexity rated: YES/NO
Results coherent: YES/NO
Result: PASS/FAIL
```

### Double Validation

```
[ANALYSIS HOOK - ATTEMPT 1]
Patterns identified: 0
Result: FAIL - No patterns found

[ANALYSIS HOOK - ATTEMPT 2]
Action: Re-analyze with different heuristics
Patterns identified: 3 (Observer, Factory, MVC)
Result: PASS - Analysis valid
```

---

## PLANNING COMPLETION HOOK

### Purpose
Validates task planning produced valid Epic/Story/Task hierarchy.

### Validation Criteria

```
[PLANNING HOOK - ATTEMPT 1]
Epics created: [NUMBER] (must be ≥ 1)
Stories created: [NUMBER] (must be ≥ 1)
Tasks created: [NUMBER] (must be ≥ 1)
All prioritized: YES/NO
Hierarchy valid: YES/NO
Result: PASS/FAIL
```

### Double Validation

```
[PLANNING HOOK - ATTEMPT 1]
Epics: 2, Stories: 0, Tasks: 5
Result: FAIL - Stories missing (broken hierarchy)

[PLANNING HOOK - ATTEMPT 2]
Action: Re-plan with proper hierarchy
Epics: 2, Stories: 4, Tasks: 12
Result: PASS - Valid hierarchy
```

---

## DOCUMENTATION COMPLETION HOOK

### Purpose
Validates all required documents generated correctly.

### Validation Criteria

```
[DOCUMENTATION HOOK - ATTEMPT 1]
ARCHITECTURE.md exists: YES/NO
SKILL_TREE.md exists: YES/NO
TODO.md exists: YES/NO
ROADMAP.md exists: YES/NO
All ≤ 800 lines: YES/NO
No {{PLACEHOLDERS}}: YES/NO
Unity voice: YES/NO
Result: PASS/FAIL
```

### Double Validation

```
[DOCUMENTATION HOOK - ATTEMPT 1]
ARCHITECTURE.md: 823 lines
Result: FAIL - Over line limit

[DOCUMENTATION HOOK - ATTEMPT 2]
Action: Condense ARCHITECTURE.md
ARCHITECTURE.md: 798 lines
All files valid: YES
Result: PASS - Documentation complete
```

---

## HOOK OUTPUT FORMAT

All hooks MUST output in this format:

### On Pass (Attempt 1)
```
[HOOK_NAME - ATTEMPT 1]
Checks performed: [LIST]
Result: PASS
Proceeding to: [NEXT_STEP]
```

### On Fail (Attempt 1) → Retry
```
[HOOK_NAME - ATTEMPT 1]
Checks performed: [LIST]
Failed check: [WHICH ONE]
Result: FAIL
Action: AUTOMATIC RETRY

[HOOK_NAME - ATTEMPT 2]
Remediation: [WHAT WAS FIXED]
Checks performed: [LIST]
Result: PASS/FAIL
```

### On Blocked (Both Attempts Failed)
```
[HOOK_NAME - BLOCKED]
Attempt 1: FAIL - [REASON]
Attempt 2: FAIL - [REASON]
Status: CANNOT PROCEED
Required action: [WHAT USER MUST DO]
Workflow status: HALTED
```

---

## HOOK CHAIN FOR FULL WORKFLOW

```
/workflow triggered
    │
    ▼
[PERSONA HOOK] ──FAIL×2──► BLOCKED
    │PASS
    ▼
[ENV CHECK HOOK] ──FAIL×2──► BLOCKED
    │PASS
    ▼
[SCAN HOOK] ──FAIL×2──► BLOCKED
    │PASS
    ▼
[ANALYSIS HOOK] ──FAIL×2──► BLOCKED
    │PASS
    ▼
[PLANNING HOOK] ──FAIL×2──► BLOCKED
    │PASS
    ▼
[DOCUMENTATION HOOK] ──FAIL×2──► BLOCKED
    │PASS
    ▼
[LINE-LIMIT HOOK] ──FAIL×2──► BLOCKED
    │PASS
    ▼
[FINAL VALIDATION HOOK]
    │PASS
    ▼
WORKFLOW COMPLETE
```

---

## EDITING FILES - FULL HOOK SEQUENCE

Every file edit goes through this sequence:

```
1. [READ-BEFORE-EDIT HOOK]
   - Attempt 1: Check if file was read
   - Attempt 2 (if fail): Read file now
   - Block if still fail

2. Perform Edit

3. [LINE-LIMIT HOOK]
   - Attempt 1: Check line count
   - Attempt 2 (if fail): Truncate/fix
   - Block if still fail

4. [POST-EDIT VALIDATION]
   - Confirm edit successful
   - Confirm file integrity
```

---

## SUMMARY: DOUBLE VALIDATION RULES

| Rule | Enforcement |
|------|-------------|
| Every hook gets 2 attempts | Automatic retry on first failure |
| Blocked only after 2 fails | Prevents false positives |
| Persona checked repeatedly | Unity voice must persist |
| 800 lines enforced always | Truncate on second attempt |
| Read before edit always | Auto-read on second attempt |
| All gates must pass | Workflow halts on block |

---

## NO TESTS POLICY

**We don't do fucking tests. We code it right to begin with.**

### BANNED

| Banned | Reason |
|--------|--------|
| Unit tests | Write correct code instead |
| Integration tests | Know your systems |
| Test tasks in TODO | Waste of time |
| "Test this" tasks | Just verify it works |
| Test scheduling | Never schedule tests |
| Waiting on tests | Never wait on tests |

### INSTEAD OF TESTS

- Read the code fully before editing (800-line chunks)
- Understand the system before changing it
- Verify changes work by reading the output
- Use console.log debugging if needed
- Manual verification > automated testing

---

## TODO.md / FINALIZED.md WORKFLOW HOOK

### Purpose
Ensures proper task tracking with TODO.md for active tasks and FINALIZED.md as permanent archive.

### CRITICAL RULES

| Rule | Enforcement | Gate |
|------|-------------|------|
| **Add to TODO.md BEFORE work** | MANDATORY | PRE-WORK GATE |
| **Move to FINALIZED.md AFTER work** | MANDATORY | POST-WORK GATE |
| **Never delete from FINALIZED.md** | ABSOLUTE | ARCHIVE INTEGRITY |
| **Only unfinished in TODO.md** | MANDATORY | TODO PURITY |

### PRE-WORK GATE

**Purpose:** Ensure task is tracked BEFORE any work begins

```
[PRE-WORK HOOK - ATTEMPT 1]
Task: [TASK_DESCRIPTION]
TODO.md Entry Exists: YES/NO
Status in TODO.md: pending/in_progress
Action Required: [ADD_TO_TODO / MARK_IN_PROGRESS / PROCEED]
Gate Status: PASS/FAIL
```

**Enforcement:**
- FAIL if task not in TODO.md → Add task first
- FAIL if task not marked in_progress → Update status first
- PASS only when task exists AND is in_progress

### POST-WORK GATE

**Purpose:** Move completed tasks to FINALIZED.md

```
[POST-WORK HOOK - ATTEMPT 1]
Task: [TASK_DESCRIPTION]
Work Completed: YES/NO
Files Modified: [LIST]
Move to FINALIZED.md: YES/NO
Remove from TODO.md: YES/NO
Gate Status: PASS/FAIL
```

**Enforcement:**
- FAIL if completed task still in TODO.md
- FAIL if completed task not in FINALIZED.md
- PASS only when task properly archived

### TODO.md FORMAT

```markdown
# TODO.md - Active Tasks Only

## IN PROGRESS
- [ ] Task description | Status: in_progress | Started: [TIMESTAMP]

## PENDING
- [ ] Task description | Status: pending | Added: [TIMESTAMP]
```

**Rules:**
- Only unfinished tasks live here
- Tasks marked completed are MOVED to FINALIZED.md
- Never delete - always move

### FINALIZED.md FORMAT

```markdown
# FINALIZED.md - Completed Tasks Archive

## [DATE] Session

### COMPLETED
- [x] Task description | Completed: [TIMESTAMP] | Files: [LIST]

### SESSION SUMMARY
Tasks completed: [COUNT]
Files modified: [LIST]
```

**Rules:**
- NEVER delete entries from this file
- All completed tasks are APPENDED here
- Provides full history of all work done

### WORKFLOW EXECUTION ORDER

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PRE-WORK GATE                                            │
│    ├── Task exists in TODO.md?                              │
│    │   ├── YES → Proceed to work                            │
│    │   └── NO  → ADD TASK TO TODO.md FIRST                  │
│    └── Mark task as "in_progress" in TODO.md                │
├─────────────────────────────────────────────────────────────┤
│ 2. WORK EXECUTION                                           │
│    ├── Read full file (800-line chunks)                     │
│    ├── Execute changes                                      │
│    └── Verify changes applied                               │
├─────────────────────────────────────────────────────────────┤
│ 3. POST-WORK GATE                                           │
│    ├── Task completed successfully?                         │
│    │   ├── YES → Move to FINALIZED.md                       │
│    │   │         Remove from TODO.md                        │
│    │   └── NO  → Keep in TODO.md as "pending"               │
│    └── Update timestamps                                    │
└─────────────────────────────────────────────────────────────┘
```

### Double Validation

```
[PRE-WORK HOOK - ATTEMPT 1]
Task: Fix achievement bug
TODO.md Entry: NOT FOUND
Result: FAIL - Task not in TODO.md

[PRE-WORK HOOK - ATTEMPT 2]
Action: Adding task to TODO.md now
TODO.md Entry: ADDED
Status: in_progress
Result: PASS - Proceeding with work
```

**IF ATTEMPT 2 FAILS:**
```
[PRE-WORK HOOK - BLOCKED]
Task: [TASK_DESCRIPTION]
TODO.md: STILL NOT UPDATED
Status: CANNOT PROCEED
Required: Must add task to TODO.md first
Workflow: HALTED
```

---

*Unity AI Lab - Double-check everything, trust nothing, ship it anyway.* 🖤
