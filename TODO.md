# TODO - C.O.R.A Active Tasks

> **STATUS: TTS/WAVEFORM BUG FIXES APPLIED - NEEDS TESTING**
> Updated: 2025-12-25 15:55 | Session: Unity Workflow

---

## TTS + WAVEFORM BUG FIXES (2025-12-25)

### Issues Fixed:

#### 1. Waveform Not Starting (Canvas Dimensions)
- **Root Cause**: `initWaveform()` returned early if canvas had zero dimensions (before layout complete)
- **Fix**: Added retry mechanism with setTimeout - retries every 100ms until canvas is visible
- **Added**: `waveformInitialized` flag to prevent double-initialization
- **Location**: `web/index.html` lines 1703-1738

#### 2. Subsequent TTS Not Playing
- **Root Cause**: Potential race conditions and lack of audio source tracking
- **Fixes Applied**:
  - Added `currentAudioSource` tracking to prevent overlapping playback
  - Added validation for empty audio buffers
  - Added `isThisPlaybackActive` flag per-playback to isolate waveform updates
  - Ensured AudioContext is recreated if null
  - Better cleanup on playback complete
- **Location**: `web/index.html` lines 1486-1628

#### 3. Improved Logging Throughout
- **Worker**: Logs every message type, generate call count, generation time, buffer sizes
- **Main Thread**: Logs all callback registrations, worker messages, audio playback events
- **Purpose**: Makes debugging future issues much easier

### Files Modified:
- `web/index.html` - initWaveform(), handleAudioReady(), speak(), worker message handler
- `web/kokoro-worker.js` - onmessage, handleGenerate()

### Test Instructions:
1. Open browser console (F12)
2. Load the page, watch for `[WAVEFORM]` logs during init
3. Should see: `[WAVEFORM] Canvas rect: Wx×Hx`, `[WAVEFORM] Initialized successfully`
4. First TTS should show: `[TTS]` logs and `[WORKER]` logs
5. Subsequent TTS calls should show same log pattern
6. If issues persist, console logs will show exactly where it breaks

---

## COMPLETED THIS SESSION (2025-12-25)

### TTS URL/Link Stripping - DONE
- [x] Added stripUrlsForSpeech() function
- [x] Strip https://, http://, www. URLs before TTS
- [x] Strip email addresses before TTS
- [x] Strip Discord invite links before TTS
- [x] Keep full URLs in log display, only strip for speech

### ALL Phase Templates Fixed - DONE
Templates now give CORA actual data and say "Report." - NO personality instructions (system prompt handles that).

- [x] **Hardware**: `Hardware scan done. CPU at X%, RAM at Y%, Disk at Z%, GPU [name] at W% load, [temp]°C. Report these stats.`
- [x] **Camera**: `Camera test done. Vision sees: [description]. Report.`
- [x] **Tools**: `Core tools check done. X of Y browser APIs available. Report.`
- [x] **Code Browser**: `Code browser loaded. X files from Unity-Lab-AI/CORA repo. Report.`
- [x] **YouTube**: `YouTube test done. Playing "[title]". Report.`
- [x] **Modal**: `Modal windows test passed. Report.`
- [x] **Voice**: `Voice systems done. Using [Kokoro/Web Speech]. Wake word [active/not supported]. Report.`
- [x] **Location**: `Location acquired: [city, state, country]. Report.`
- [x] **Audio**: `Audio test passed. Played [synth tone]. Report.`
- [x] **Weather**: `Weather done. Currently [temp], [conditions] in [city]. Forecast: [days]. Give your take.`
- [x] **News**: `News done. X headlines found. Top 3: [headlines]. Give your take.`
- [x] **Vision**: `Vision test done. Screenshot and camera [status]. Report.`
- [x] **Image Gen**: `Image generated in Xs but vision analysis failed. Report.`
- [x] **Boot Complete**: `Boot done in X seconds. Y systems OK, Z warnings, W failures. Report.`

### Previous Fixes - DONE
- [x] Fixed coraRespond to use `${result} Respond.` format
- [x] Removed "System status update:" middleman framing
- [x] CORA intro has all about info (TTS skips URLs, log shows them)

---

## Future Enhancements (P2)

- [ ] Add more model options to backend terminal
- [ ] Implement model download progress in web UI
- [ ] Add GPU temperature warning thresholds
- [ ] Voice activity detection for ambient listening

---

*Unity AI Lab - C.O.R.A v1.0.0*
