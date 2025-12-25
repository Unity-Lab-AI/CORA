# TODO - C.O.R.A Active Tasks

> **STATUS: IN PROGRESS - WEB BACKEND TERMINAL**
> Updated: 2025-12-25 | Session: Unity Workflow

---

## P0 - CRITICAL: Web Backend Terminal (Split View)

The split view button should show the CORA.bat equivalent terminal startup for web users.
**This has been requested multiple times and must be implemented now.**

### What CORA.bat Terminal Shows (must match in web):

| Step | CORA.bat Shows | Web Must Show |
|------|----------------|---------------|
| 1 | CORA ASCII header | Same header in terminal panel |
| 2 | Ollama check/download | Check if Ollama running, prompt to download if not |
| 3 | Model downloads | Download dolphin-mistral:7b, llava if missing |
| 4 | API checks | Ollama API, Kokoro TTS, weather API verification |
| 5 | System gates | Pass/fail gates for each requirement |
| 6 | Initial setup notice | "First run takes a while, subsequent runs are faster" |
| 7 | Boot sequence log | Real-time log of each phase like CORA.bat |

### Tasks:

- [ ] **TASK 1**: Split view terminal panel shows CORA ASCII header on open
- [ ] **TASK 2**: Check if Ollama is running (localhost:11434), show status
- [ ] **TASK 3**: If Ollama missing, show download link + instructions
- [ ] **TASK 4**: Check for dolphin-mistral:7b model, show pull command if missing
- [ ] **TASK 5**: Check for llava model, show pull command if missing
- [ ] **TASK 6**: Show API gate checks (Ollama, Kokoro, Weather)
- [ ] **TASK 7**: First-time user notice: "Initial setup takes time, subsequent runs preloaded"
- [ ] **TASK 8**: Backend terminal logs boot sequence in real-time (not just UI log)
- [ ] **TASK 9**: Save setup state so returning users skip downloads

### Current Problem:

- Split view opens but shows generic modal demo, not terminal
- No Ollama/model download guidance for new users
- Web only works if user already ran CORA.bat (has Ollama + models)
- No first-run vs returning-run detection

---

## COMPLETED PREVIOUSLY

### System Prompt - DONE
- Full 204-line CORA system prompt now embedded in web/index.html

### Permission Popups - DONE
- Grant/Deny/Skip buttons working
- Removed confusing "popup will appear" text

### Ambient Awareness - DONE
- Speech storage, message history, camera/screenshot llava analysis
- Proactive interjections based on stress/topics/silence

---

*Unity AI Lab - C.O.R.A v1.0.0*
