# TODO - C.O.R.A Active Tasks

> **STATUS: ALL CRITICAL FIXES COMPLETE**
> Updated: 2025-12-25 12:31 | Session: Unity Workflow

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
