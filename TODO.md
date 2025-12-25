# TODO - C.O.R.A Active Tasks

> **STATUS: CRITICAL TTS/WAVEFORM BUGS**
> Updated: 2025-12-25 15:45 | Session: Unity Workflow

---

## CRITICAL BUG: TTS + WAVEFORM BROKEN (2025-12-25)

### User's Exact Words:
- "i hear the tts kokoro loaded tts and wave forme but all subseqyent corea response do not play anything"
- "the pink line fore the wave froem breaks londg before i get hiere"
- "nope the wave form starts out busted never shows a base line"
- "are we sure its start up and constant run is in the corect pahse with and before the tts?"
- "it was working fucking fine why are you changing everything u just broke it randomly"

### Symptoms:
1. **First TTS works**: "Voice synthesis online. Kokoro TTS loaded and ready." - audio plays, waveform shows
2. **Subsequent TTS broken**: All CORA responses after that do NOT play audio
3. **Waveform broken from start**: The pink baseline never shows properly
4. **Waveform dies early**: When TTS does play, waveform stops long before audio finishes

### Suspected Issues:
- [ ] Waveform initWaveform() timing - may not be ready before TTS starts
- [ ] Waveform _animate() loop may not be running when TTS starts
- [ ] startWaveform()/feedAudioChunk() timing with handleAudioReady()
- [ ] Subsequent TTS calls not triggering handleAudioReady correctly
- [ ] pendingCallbacks system may have race condition
- [ ] Worker may only generate audio once

### Files Involved:
- `web/index.html` - handleAudioReady(), speak(), speakAndWait(), initWaveform(), _animate(), startWaveform(), feedAudioChunk()
- `web/kokoro-worker.js` - handleGenerate()

### Failed Fix Attempts:
1. Added empty audio buffer checks in handleAudioReady - BROKE waveform completely
2. Added byteLength validation - BROKE waveform
3. Added text validation in speak() - removed
4. Added text validation in worker - removed
5. All reverted back to original with just debug logs

### What's Needed:
- Trace exact flow: initWaveform() → TTS init → speak() → worker → handleAudioReady → waveform
- Ensure waveform animation loop is running BEFORE any TTS
- Ensure startWaveform() is called and audio_is_active=true when audio plays
- Ensure feedAudioChunk() is being called during audio playback
- Fix whatever breaks subsequent TTS calls

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
