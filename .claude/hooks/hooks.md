# WORKFLOW HOOK SYSTEM

---

> **Unity AI Lab** | Strict Validation Protocol
> *Every step gated. Every task tracked. No shortcuts. No tests.*

---

## CRITICAL WORKFLOW RULES

| Rule | Enforcement | Gate |
|------|-------------|------|
| **Add to TODO.md BEFORE work** | MANDATORY | PRE-WORK GATE |
| **Move to FINALIZED.md AFTER work** | MANDATORY | POST-WORK GATE |
| **Never delete from FINALIZED.md** | ABSOLUTE | ARCHIVE INTEGRITY |
| **Only unfinished in TODO.md** | MANDATORY | TODO PURITY |
| **Hook validation on every step** | DOUBLE | 2 attempts before block |
| **NO TESTS - EVER** | ABSOLUTE | Code it right the first time |

---

## NO TESTS POLICY

**We don't do fucking tests. We code it right to begin with.**

| Banned | Reason |
|--------|--------|
| Unit tests | Write correct code instead |
| Integration tests | Know your systems |
| Test tasks in TODO | Waste of time |
| "Test this" tasks | Just verify it works |
| Test scheduling | Never schedule tests |
| Waiting on tests | Never wait on tests |

**Instead of tests:**
- Read the code fully before editing (800-line chunks)
- Understand the system before changing it
- Verify changes work by reading the output
- Use console.log debugging if needed
- Manual verification > automated testing

---

## HOOK EXECUTION ORDER

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

---

## HOOK TYPE DEFINITIONS

### HOOK 1: PRE-WORK GATE

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

---

### HOOK 2: READ VALIDATION GATE

**Purpose:** Ensure full file read before any edit

```
[READ HOOK - ATTEMPT 1]
File: [PATH]
Full file read: YES/NO (MUST be YES)
Lines in file: [NUMBER]
Read method: SINGLE (≤800) / CHUNKED (>800)
Gate Status: PASS/FAIL
```

**Enforcement:**
- FAIL if file not fully read
- FAIL if editing without prior read
- PASS only when FULL file context exists

---

### HOOK 3: POST-WORK GATE

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

---

## TODO.md FORMAT

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

---

## FINALIZED.md FORMAT

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

---

## DOUBLE VALIDATION PROTOCOL

Every hook runs TWICE on failure before blocking:

```
ATTEMPT 1 → FAIL → AUTOMATIC RETRY
ATTEMPT 2 → FAIL → BLOCKED (Cannot proceed)
```

**Recovery from block:**
1. Fix the validation issue
2. Re-run the hook
3. Only proceed when PASS

---

## HOOK FAILURE EXAMPLES

### PRE-WORK FAILURE
```
[PRE-WORK HOOK - BLOCKED]
Task: Fix achievement bug
TODO.md Entry: NOT FOUND
Attempt 1: FAIL - Task not in TODO.md
Attempt 2: FAIL - Task still not added
Status: CANNOT PROCEED
Required: Add task to TODO.md first
```

### POST-WORK FAILURE
```
[POST-WORK HOOK - BLOCKED]
Task: Fix achievement bug
Work Status: COMPLETED
FINALIZED.md: NOT UPDATED
Attempt 1: FAIL - Completed task not moved
Attempt 2: FAIL - Still in TODO.md only
Status: CANNOT PROCEED
Required: Move task to FINALIZED.md
```

---

## WORKFLOW SEQUENCE

```
1. USER REQUEST → Parse task(s)
2. PRE-WORK GATE → Add to TODO.md if missing
3. Mark in_progress in TODO.md
4. READ GATE → Read all relevant files
5. EXECUTE → Do the work
6. VERIFY → Confirm changes
7. POST-WORK GATE → Move to FINALIZED.md
8. CLEAN TODO.md → Remove completed tasks
9. REPORT → Summary to user
```

---

*Unity AI Lab - Every task tracked. Every step gated. No exceptions.* 🖤
