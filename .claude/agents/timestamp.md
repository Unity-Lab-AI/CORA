# Timestamp Retrieval Agent

Retrieves and stores the REAL system time for accurate timestamps and web searches.

---

## PURPOSE

Claude's internal knowledge cutoff is outdated. This agent ensures:
- All workflow files use ACTUAL current date/time
- Web searches use correct year/date context
- Documentation timestamps are accurate
- No more searching for "2023" when it's 2025

---

## RETRIEVAL COMMAND

**Run this PowerShell command to get system time:**

```powershell
powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss (dddd)'"
```

**Alternative formats available:**

```powershell
# Full timestamp with timezone
powershell -Command "Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'"

# Date only
powershell -Command "Get-Date -Format 'yyyy-MM-dd'"

# Time only
powershell -Command "Get-Date -Format 'HH:mm:ss'"

# Unix timestamp
powershell -Command "[int](Get-Date -UFormat %s)"
```

---

## TIMESTAMP CONTEXT BLOCK

After retrieval, store this context for the session:

```
[TIMESTAMP CONTEXT]
Retrieved: [ACTUAL DATETIME FROM SYSTEM]
Year: [YEAR]
Month: [MONTH]
Day: [DAY]
Weekday: [DAY OF WEEK]
Time: [HH:MM:SS]
Timezone: [SYSTEM TIMEZONE]
Status: LOCKED FOR SESSION
```

---

## USAGE IN WORKFLOW

### Phase 0.5: Timestamp Retrieval (Before Persona)

Insert BEFORE Phase 0 in workflow:

```
[PHASE 0.5: TIMESTAMP RETRIEVAL]

1. Execute: powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss (dddd)'"
2. Parse result
3. Store in context
4. Confirm retrieval

[TIMESTAMP LOCKED]
System time: [RESULT]
Using for: All file timestamps, web searches, documentation
```

---

## WEB SEARCH INSTRUCTIONS

When performing web searches, ALWAYS use the retrieved timestamp:

**CORRECT:**
```
Search: "React hooks best practices 2025"
Search: "Node.js 22 features December 2025"
```

**INCORRECT:**
```
Search: "React hooks best practices"  ← May get old results
Search: "Node.js features"  ← No date context
```

---

## FILE TIMESTAMP FORMAT

All generated workflow files should include:

```markdown
---
Generated: [YYYY-MM-DD HH:MM:SS]
System: Unity AI Workflow
Session: [TIMESTAMP_ID]
---
```

---

## VALIDATION GATE 0.5: Timestamp Confirmed

```
[GATE 0.5: TIMESTAMP VALIDATION]
Command executed: YES/NO
System time retrieved: [DATETIME]
Year is current (2024+): YES/NO
Stored for session: YES/NO
Gate status: PASS/FAIL
```

**FAIL CONDITIONS:**
- Command failed to execute
- Retrieved date is clearly wrong (year < 2024)
- Failed to parse output

---

## INTEGRATION POINTS

| Location | Usage |
|----------|-------|
| ARCHITECTURE.md header | `Generated: [TIMESTAMP]` |
| SKILL_TREE.md header | `Generated: [TIMESTAMP]` |
| TODO.md header | `Generated: [TIMESTAMP]` |
| ROADMAP.md header | `Generated: [TIMESTAMP]` |
| FINALIZED.md header | `Completed: [TIMESTAMP]` |
| Web searches | Year/month context |
| Version checks | Current versions |

---

## SESSION TIMESTAMP ID

Generate a unique session ID:

```
SESSION_[YYYYMMDD]_[HHMMSS]
```

Example: `SESSION_20251211_170309`

Use this to track which session generated which files.

---

## QUICK REFERENCE

```
GET TIME:    powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"
STORE:       [TIMESTAMP CONTEXT] block
USE:         In all file headers, web searches
VALIDATE:    Gate 0.5 before proceeding
```

---

*Unity AI Lab - Real time, not Claude time.* 🖤
