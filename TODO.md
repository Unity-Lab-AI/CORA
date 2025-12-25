# TODO - C.O.R.A Active Tasks

> **STATUS: AMBIENT AWARENESS IMPLEMENTATION**
> Updated: 2025-12-25 08:45 | Session: Unity Workflow

---

## P0 - AMBIENT AWARENESS SYSTEM (IN PROGRESS)

**Goal:** Make CORA fully aware and contextual in web version - just like desktop `voice/ambient_awareness.py`

### What's Already Done:
- [x] `ambientContext` object created - stores speech, messages, camera, mood
- [x] `addAmbientSpeech()` - stores everything CORA hears (last 20 transcripts)
- [x] `addMessageHistory()` - stores chat history (last 20 messages)
- [x] `captureAndAnalyzeCamera()` - periodic camera snapshots (every 60s)
- [x] `buildAmbientContextPrompt()` - builds full context for AI
- [x] `onWakeWordDetected()` - now uses ambient context instead of hardcoded response
- [x] Wake word listener stores ALL speech, not just wake words

### What Still Needs Doing:

#### 1. Update `sendChat()` to store message history
```javascript
// In sendChat(), add:
addMessageHistory('USER', msg);
// After getting response:
addMessageHistory('CORA', reply);
```

#### 2. Send camera snapshots to llava for real analysis
```javascript
// In captureAndAnalyzeCamera(), convert canvas to base64 and send to:
// POST http://localhost:11434/api/generate
// model: 'llava'
// images: [base64Image]
// prompt: 'Describe what you see. Is the user there? What are they doing?'
```

#### 3. Add screenshot capture and analysis
```javascript
// Use getDisplayMedia() to capture screen periodically
// Send to llava for analysis
// Store in ambientContext.lastScreenshot
```

#### 4. Add chat context to regular chat (not just wake word)
```javascript
// In sendChat(), include recent context:
const context = buildAmbientContextPrompt();
prompt: `${context}\n\nUSER: ${msg}`
```

#### 5. Proactive interjections (like desktop)
- CORA can speak up when she notices something relevant
- Based on friend_threshold setting (0.0-1.0)
- Triggers: user seems stressed, interesting topic heard, long silence, etc.

---

## Desktop Reference: `voice/ambient_awareness.py`

### Key Features to Port:
1. **AmbientContext dataclass** - tracks speech, visual, screen, timing, state
2. **friend_threshold** - 0.0 (quiet) to 1.0 (chatty friend)
3. **Interjection reasons** - helpful_info, joke, check_in, comment, question, alert, vibe
4. **Topic detection** - helpful topics, fun topics, stress indicators
5. **Periodic monitoring** - screenshot every 60s, camera every 45s
6. **Probability-based interjection** - cooldowns, busy detection

### Desktop Interjection Logic:
```python
# If user mentions helpful topic -> 40% boost to interjection chance
# If user seems stressed -> 50% boost, reason = CHECK_IN
# If question detected -> 35% boost
# If user chilling + random vibe -> low chance comment
# If user busy -> reduce all probabilities by 70%
```

---

## P0 - CORA PERSONALITY FIXES (DONE)

- [x] Simplified `coraRespond()` prompt - just `[BOOT - ${context}] ${result}`
- [x] Let system_prompt.txt handle personality, no constraints
- [x] Temperature 0.9, num_predict 150

---

## Files Modified This Session:
- `web/index.html` - ambient awareness, wake word context, simplified prompts

---

## Quick Test Checklist:
- [ ] Say something near mic, then say "Hey CORA" - does she reference what she heard?
- [ ] Chat with CORA, then say "Hey CORA" - does she remember the conversation?
- [ ] Does camera capture happen every 60 seconds? (check console)
- [ ] Does CORA sound like herself (goth, sarcastic, profane)?

---

*Unity AI Lab - C.O.R.A v2.4.0*
*Session: 2025-12-25*
