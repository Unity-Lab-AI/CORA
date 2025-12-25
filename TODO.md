# TODO - C.O.R.A Active Tasks

> **STATUS: AMBIENT AWARENESS COMPLETE**
> Updated: 2025-12-25 09:15 | Session: Unity Workflow

---

## COMPLETED THIS SESSION

### Ambient Awareness System - DONE

All ambient awareness features now implemented in web version (`web/index.html`):

| Feature | Status | Implementation |
|---------|--------|----------------|
| Speech storage | DONE | `addAmbientSpeech()` - stores last 20 transcripts |
| Message history | DONE | `addMessageHistory()` - stores last 20 chat messages |
| Camera capture + llava | DONE | `captureAndAnalyzeCamera()` - sends to llava for real analysis |
| Screenshot capture + llava | DONE | `captureAndAnalyzeScreenshot()` - sends to llava for analysis |
| Wake word with vision | DONE | `onWakeWordDetected()` captures camera BEFORE responding |
| Chat context | DONE | `sendChat()` includes `buildAmbientContextPrompt()` in every chat |
| Proactive interjections | DONE | CORA speaks up on her own based on stress/topics/silence |

### Key Functions Added:

```javascript
// Llava vision analysis
analyzImageWithLlava(base64Image, prompt) - sends image to llava model

// Camera with real analysis
captureAndAnalyzeCamera() - captures + sends to llava every 60s

// Screenshot with analysis
captureAndAnalyzeScreenshot() - uses getDisplayMedia + llava

// Quick capture for wake word
quickCameraCapture() - fast capture without llava for immediate use

// Full context builder
buildAmbientContextPrompt() - includes speech, messages, camera, screenshot, mood, timing

// Proactive interjections
shouldInterject() - checks stress, helpful topics, fun topics, silence
doProactiveInterjection() - generates and speaks contextual comments
startProactiveInterjections() - runs every 45 seconds
```

### Interjection Triggers:
- **Stress indicators**: fuck, shit, damn, frustrated, angry, etc. → CHECK_IN (50% boost)
- **Helpful topics**: stuck, help, error, problem, bug, fix, etc. → HELPFUL_INFO (40% boost)
- **Fun topics**: music, game, movie, youtube, etc. → COMMENT (20% boost)
- **Long silence** (5+ min): CHECK_IN (15% boost)
- **Random vibe**: occasional chill comment (5% boost)

---

## P1 - FUTURE ENHANCEMENTS

### Could Add Later:
- [ ] Friend threshold slider (0.0-1.0) to control how chatty CORA is
- [ ] Screenshot capture on-demand (currently just camera on wake word)
- [ ] Visual indicator when CORA is "watching" (camera active)
- [ ] Mood detection from facial expressions via llava
- [ ] Integration with desktop ambient_awareness.py settings

---

## Files Modified This Session:
- `web/index.html` - Full ambient awareness system

---

*Unity AI Lab - C.O.R.A v1.0.0*
*Session: 2025-12-25*
