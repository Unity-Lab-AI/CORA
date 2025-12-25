# TODO - C.O.R.A Web Version (GitHub Pages)

> **STATUS: DESKTOP PARITY ACHIEVED!**
> Updated: 2025-12-25 | Session: Unity Workflow

---

## IMPORTANT: Local Desktop App Works Fine!

**The LOCAL desktop application (CORA.bat / boot_sequence.py) is WORKING CORRECTLY.**

This TODO was specifically for the **WEB VERSION** (web/index.html) which is deployed to GitHub Pages.

---

## COMPLETED - Desktop Parity Achieved!

### Modal System
- [x] `createDynamicModal()` - Generic modal creator
- [x] `showCodeModal()` - Code display with syntax highlighting
- [x] `showImageModal()` - Image viewer
- [x] `showVideoModal()` - YouTube embed
- [x] `showQuoteModal()` - Quote display

### Phase 4.1 - Code Import
- [x] Fetches real Python code from GitHub (TheAlgorithms, geekcomputers)
- [x] Displays in code modal popup
- [x] CORA speaks about the import
- [x] Auto-closes after viewing

### Phase 4.2 - YouTube Test
- [x] Embeds actual YouTube videos
- [x] Plays in modal popup
- [x] Random selection of classic videos
- [x] Auto-closes after 5 seconds

### Phase 4.3 - Modal Windows
- [x] Shows actual test modal
- [x] Displays random inspirational quote
- [x] Auto-closes after speaking

### Phase 6.1 - Audio Test
- [x] Plays 440Hz test tone via Web Audio API
- [x] 2-second sine wave with fade out
- [x] CORA speaks about the beep

### Phase 8.0 - Vision Test
- [x] Opens camera via getUserMedia
- [x] Shows live video feed in modal
- [x] Captures frame like desktop
- [x] CORA speaks about what she sees

### Phase 9.0 - Image Generation
- [x] Generates images via Pollinations API
- [x] Creative prompts (cyberpunk, gothic, synthwave)
- [x] Displays in image modal
- [x] Auto-closes after viewing

### Settings & Data
- [x] Settings button (top right) - access API keys anytime
- [x] Clear All Data button with TRIPLE warning
- [x] Clears localStorage, sessionStorage, cookies

### Real System Stats (Phase 3.0)
- [x] stats_server.py on localhost:11435 (like Ollama on 11434)
- [x] Real GPU stats via nvidia-smi
- [x] Real CPU/RAM/Disk stats via psutil
- [x] Web version fetches from stats server
- [x] 1-second polling for live updates
- [x] CORA.bat auto-starts stats server

---

## P1 - Nice to Have (Future)

### 3-Day Weather Forecast
- [ ] Add forecast data (today, tomorrow, day after)
- [ ] Display in boot sequence like desktop

### News Reading Enhancement
- [ ] CORA reads headlines aloud with AI personality
- [ ] Summarize instead of just listing

### Voice Commands
- [x] Wake word detection ("Hey CORA") - DONE
- [ ] Full voice command parsing
- [ ] Voice-to-text for chat

### Ambient Awareness
- [ ] Periodic interjections
- [ ] React to what's on screen

---

## P2 - Future

- [ ] Task/reminder management
- [ ] Desktop notifications
- [ ] Persistent settings across sessions

---

## What Web Version Now Does (Summary)

**All phases now ACTUALLY perform actions instead of just logging "Available":**

| Phase | Action |
|-------|--------|
| 3.0 | Real GPU/CPU/RAM stats from localhost:11435 |
| 4.1 | Fetches real code from GitHub, shows in modal |
| 4.2 | Embeds YouTube video in modal, plays it |
| 4.3 | Shows quote modal popup |
| 6.1 | Plays 440Hz audio test tone |
| 8.0 | Opens camera, shows live feed in modal |
| 9.0 | Generates image via Pollinations, shows in modal |

**Stats update every 1 second with real GPU/CPU/RAM data from stats_server.py**
**Settings accessible anytime via Settings button (top right)**
**Clear All Data available with triple confirmation safety**

---

*Unity AI Lab - C.O.R.A Web Version v2.4.0*
*Session: 2025-12-25*
*Status: COMPLETE - Desktop parity achieved!*
