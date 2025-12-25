# TODO - C.O.R.A Web Version (GitHub Pages)

> **STATUS: NEEDS MAJOR WORK** - Web version does NOT match desktop
> Updated: 2025-12-25 | Session: Unity Workflow

---

## IMPORTANT: Local Desktop App Works Fine!

**The LOCAL desktop application (CORA.bat / boot_sequence.py) is WORKING CORRECTLY.**

This TODO is specifically for the **WEB VERSION** (web/index.html) which is deployed to GitHub Pages. The web version needs to be brought up to parity with the working desktop app.

---

## CRITICAL: Web Version vs Desktop Parity

**The web version (index.html) currently FAKES most phases by just logging "Available" instead of actually doing what the desktop (boot_sequence.py) does.**

### Desktop Does (boot_sequence.py):
- Phase 4.1: Fetches REAL code from GitHub API, shows in tkinter modal
- Phase 4.2: Searches YouTube with yt-dlp, plays video in mpv window
- Phase 4.3: Shows actual modal popup with random quote
- Phase 6.1: Plays actual audio with mpv (yt-dlp stream)
- Phase 8.0: Takes REAL screenshot, shows in popup, AI describes it
- Phase 8.0: Opens camera, shows in popup, AI describes what it sees
- Phase 9.0: Generates REAL image via Pollinations, shows in popup, AI describes

### Web Currently Does (index.html):
- Phase 4.1: Just logs "Code import available" - NO fetch, NO modal
- Phase 4.2: Just logs "YouTube IFrame API - Available" - NO video
- Phase 4.3: Just logs "Browser modals working" - NO actual modal
- Phase 6.1: Just logs "Web Audio API - Available" - NO sound
- Phase 8.0: Just checks if APIs exist - NO screenshot, NO camera display
- Phase 9.0: Just logs "Image generation ready" - NO actual image generated

---

## P0 - MUST FIX (Desktop Parity)

### 1. Create Modal System
- [ ] Create `createModal(title, width, height)` function
- [ ] Create `showCodeModal(code, filename, language)` function
- [ ] Create `showImageModal(imageUrl, title)` function
- [ ] Create `showVideoModal(videoId, title)` function
- [ ] Modals should auto-close after content is shown (like desktop)

### 2. Phase 4.1 - Code Import (ACTUALLY DO IT)
- [ ] Fetch real code from GitHub API (use user's token if available)
- [ ] Pick random Python file from repos
- [ ] Display fetched code in code modal
- [ ] CORA speaks about the import
- [ ] Desktop reference: boot_sequence.py lines 1136-1397

### 3. Phase 4.2 - YouTube Test (ACTUALLY DO IT)
- [ ] Search YouTube for random fun video (use invidious API or YouTube embed)
- [ ] Embed video in modal popup
- [ ] Play sample for a few seconds
- [ ] CORA speaks about the video
- [ ] Desktop reference: boot_sequence.py lines 1400-1587

### 4. Phase 4.3 - Modal Windows (ACTUALLY DO IT)
- [ ] Show actual test modal
- [ ] Display random inspirational quote
- [ ] Close after a few seconds
- [ ] CORA speaks about it
- [ ] Desktop reference: boot_sequence.py lines 1590-1682

### 5. Phase 6.1 - Audio Test (ACTUALLY DO IT)
- [ ] Create Web Audio API oscillator
- [ ] Play actual test tone (sine wave)
- [ ] Play for 2-3 seconds
- [ ] CORA speaks about audio working
- [ ] Desktop reference: boot_sequence.py lines 1895-1997

### 6. Phase 8.0 - Vision Test (ACTUALLY DO IT)
- [ ] Use `getDisplayMedia()` to capture actual screenshot
- [ ] Display screenshot in image modal
- [ ] Use `getUserMedia()` to capture camera frame
- [ ] Display camera frame in image modal
- [ ] CORA speaks about what she "sees"
- [ ] Desktop reference: boot_sequence.py lines 2081-2323

### 7. Phase 9.0 - Image Generation (ACTUALLY DO IT)
- [ ] Call Pollinations API with actual prompt
- [ ] Generate real image (not just check if API exists)
- [ ] Display generated image in image modal
- [ ] CORA speaks about the generated image
- [ ] Desktop reference: boot_sequence.py lines 2325-2488

### 8. Console Auto-Open
- [ ] Fix console.html auto-open on page load
- [ ] Must not break boot sequence if popup blocked
- [ ] Console receives logs via BroadcastChannel

---

## P1 - Should Do

### 3-Day Weather Forecast
- [ ] Add forecast data (today, tomorrow, day after)
- [ ] Display in boot sequence like desktop

### News Reading Enhancement
- [ ] CORA reads headlines aloud with AI personality
- [ ] Summarize instead of just listing

---

## P2 - Nice to Have

### Voice Commands
- [x] Wake word detection ("Hey CORA") - DONE
- [ ] Full voice command parsing
- [ ] Voice-to-text for chat

### Ambient Awareness
- [ ] Periodic interjections
- [ ] React to what's on screen

---

## P3 - Future

- [ ] Task/reminder management
- [ ] Desktop notifications
- [ ] Persistent settings across sessions

---

## Reference Files

| File | Purpose | Lines |
|------|---------|-------|
| `src/boot_sequence.py` | Desktop boot - THE SOURCE OF TRUTH | ~2900 |
| `ui/boot_display.py` | Desktop UI with waveform | ~1955 |
| `web/index.html` | Web version - NEEDS FIXING | ~1970 |
| `web/console.html` | Separate console window | ~106 |

---

## What Web Version SHOULD Do (Summary)

After fixes, each phase should:
1. Actually perform the action (not just log "Available")
2. Show visual feedback (modal popups like desktop)
3. Have CORA speak about the result
4. Match desktop behavior as closely as browser allows

---

*Unity AI Lab - C.O.R.A Web Version v2.4.0*
*Session: 2025-12-25*
*Status: INCOMPLETE - Needs implementation work*
