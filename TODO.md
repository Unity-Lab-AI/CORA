# TODO - C.O.R.A Active Tasks

> **STATUS: READY FOR NEW TASKS**
> Updated: 2025-12-25 | Session: Unity Workflow

---

## Current: No Blocking Tasks

All P0 critical tasks have been completed. System is operational.

---

## Future Enhancements (P2)

- [ ] Add more model options to backend terminal
- [ ] Implement model download progress in web UI
- [ ] Add GPU temperature warning thresholds
- [ ] Voice activity detection for ambient listening

---

## COMPLETED THIS SESSION (2025-12-25)

### Web Backend Terminal - DONE
- [x] **TASK 1**: Split view terminal panel shows CORA ASCII header on open
- [x] **TASK 2**: Check if Ollama is running (localhost:11434), show status
- [x] **TASK 3**: If Ollama missing, show download link + instructions
- [x] **TASK 4**: Check for dolphin-mistral:7b model, show pull command if missing
- [x] **TASK 5**: Check for llava model, show pull command if missing
- [x] **TASK 6**: Show API gate checks (Ollama, Kokoro, Weather)
- [x] **TASK 7**: First-time user notice: "Initial setup takes time, subsequent runs preloaded"
- [x] **TASK 8**: Backend terminal logs boot sequence in real-time
- [x] **TASK 9**: Save setup state so returning users skip downloads
- [x] **TASK 10**: Fixed terminal visibility (moved outside mainContainer)
- [x] **TASK 11**: Added fixed BACK/SPLIT VIEW buttons in terminal panel

### CORA Personality Fix - DONE
- [x] Fixed AI prompts to explicitly demand profanity and attitude
- [x] Increased char limit from 200 to 350 for personality responses
- [x] Changed from 2 to 3 sentences allowed
- [x] Trims long responses instead of falling back to boring data

### TTS Sync Fix - DONE
- [x] CORA text now appears in log ONLY when audio starts playing
- [x] Fixed for both Kokoro TTS and Web Speech API fallback

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
