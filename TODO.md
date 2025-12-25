# TODO - C.O.R.A Web Version Critical Fixes

> **MASSIVE OVERHAUL NEEDED** - Web version is NOT matching desktop
> Generated: 2025-12-25 | Priority: CRITICAL

---

## Summary of Problems

| Category | Desktop Has | Web Has | Status |
|----------|-------------|---------|--------|
| YouTube Test | Actually searches & plays video | Just says "Available" | BROKEN |
| Code Import | Fetches real code from GitHub | Just says "API accessible" | BROKEN |
| Audio Test | Plays actual audio via yt-dlp/mpv | Just checks Web Audio API | BROKEN |
| Vision Test | Takes screenshot, AI analyzes | Just checks API available | BROKEN |
| Image Gen | Generates image via Pollinations | Just checks if online | BROKEN |
| Camera | Opens feed, captures frame, AI analyzes | Just requests permission | BROKEN |
| Modals | Shows popups for code, video, images | NO MODALS AT ALL | BROKEN |
| Weather | Current + 3-day forecast | Only current (if key set) | PARTIAL |
| News | Announces top 3-4 headlines | Just logs, doesn't announce | PARTIAL |
| AI Responses | cora_respond() with personality | Pre-written static text | MISSING |
| Tool Tests | Tests 10 actual modules | Lists generic web APIs | BROKEN |
| Location | IP-based, works automatically | Browser geolocation, flaky | PARTIAL |

---

## P0 - CRITICAL (Desktop Parity)

### Epic: Phase Tests Must Actually DO Something

#### 4.1 Code Import - BROKEN
- [ ] **Task:** Actually fetch code from GitHub API
  - Fetch from user's repos if token in settings
  - Fallback to public Python repos
  - Show code in a modal/popup window
  - CORA announces how many lines fetched
- [ ] **Task:** Add code modal popup
  - Syntax highlighted code display
  - Shows source repo name
  - Auto-closes after CORA speaks

#### 4.2 YouTube Test - BROKEN
- [ ] **Task:** Actually search YouTube
  - Use YouTube embed API or oEmbed
  - Search for random wild video like desktop does
  - Show video info in modal
- [ ] **Task:** Embed and play a sample video
  - Create YouTube embed iframe
  - Play 10-20 seconds as test
  - Show modal with video title/info
- [ ] **Task:** CORA announces what video was found

#### 4.3 Modal Windows - BROKEN
- [ ] **Task:** Create modal/popup system for web
  - Centered overlay modal
  - Dark theme matching boot display
  - Close button and auto-close timer
- [ ] **Task:** Show test modal with quote
  - Like desktop shows random inspirational quote
  - Display modal types available
- [ ] **Task:** Modal types needed:
  - Message/quote modal
  - Code viewer modal
  - Image viewer modal
  - Video player modal

#### 6.1 Audio Test - BROKEN
- [ ] **Task:** Actually play audio
  - Use Web Audio API to play a test sound
  - Or embed YouTube audio and play sample
  - Show what's playing in modal
- [ ] **Task:** CORA announces audio working with what played

#### 8.0 Vision Test - BROKEN
- [ ] **Task:** Actually capture screenshot/screen
  - Use Screen Capture API (getDisplayMedia)
  - Or use html2canvas to capture the page
  - Show captured image in modal
- [ ] **Task:** Send to Ollama vision for analysis
  - If Ollama has llava model, send screenshot
  - CORA describes what she sees
- [ ] **Task:** Actually test camera
  - Open camera stream in modal
  - Capture a frame
  - Send to Ollama vision for analysis

#### 9.0 Image Gen - BROKEN
- [ ] **Task:** Actually generate an image
  - Call Pollinations API with prompt
  - Show loading indicator
  - Display generated image in modal
- [ ] **Task:** Have CORA/Ollama create the prompt
  - Call Ollama to generate creative prompt
  - Like desktop's "fucked up image" request
- [ ] **Task:** Show image in fullscreen modal
  - Like desktop shows the generated image
  - Auto-close after CORA speaks

---

## P1 - High Priority

### Epic: AI-Powered Responses (cora_respond)

#### CORA Personality in Speech - MISSING
- [ ] **Task:** Create web equivalent of cora_respond()
  - Call Ollama to generate unique responses
  - Use CORA's system prompt for personality
  - Don't use static pre-written text
- [ ] **Task:** Load system_prompt.txt from somewhere
  - Embed it in the HTML or fetch from GitHub
  - Use for all AI calls
- [ ] **Task:** Each phase should use AI response
  - Hardware: AI describes the stats
  - Weather: AI announces naturally
  - News: AI summarizes headlines
  - Vision: AI describes what it sees

---

### Epic: Weather & News Parity

#### Weather - PARTIAL
- [ ] **Task:** Add 3-day forecast like desktop
  - Desktop uses get_forecast() for 3 days
  - Show today, tomorrow, day after
  - Include high/low temps and conditions
- [ ] **Task:** CORA announces full weather report
  - Current conditions
  - Today's forecast
  - Tomorrow and next day
- [ ] **Task:** Fix weather API to not require user key
  - Use free weather API that doesn't need key
  - Or use IP-based weather service

#### News - PARTIAL
- [ ] **Task:** CORA should READ the headlines aloud
  - Desktop announces top 3-4 headlines
  - Web just logs them silently
- [ ] **Task:** Use AI to summarize headlines naturally
  - Call cora_respond with headlines
  - Natural spoken summary

---

### Epic: Location Service

#### Location - PARTIAL
- [ ] **Task:** Don't timeout so quickly
  - Current 60 sec might not be enough
  - Show "waiting for permission" message
  - Let user click to retry
- [ ] **Task:** IP fallback should work better
  - ipapi.co sometimes fails
  - Add multiple IP geolocation fallbacks
- [ ] **Task:** Show location permission modal
  - Desktop shows clear instructions
  - Web should too

---

## P2 - Important

### Epic: Core Tools Testing

#### Tool Tests - BROKEN
- [ ] **Task:** Actually test web equivalents of tools
  - LocalStorage read/write test
  - Fetch API request test
  - WebSocket connection test
  - Canvas drawing test
  - Web Audio playback test
  - Geolocation test
  - Notification permission test
  - Clipboard access test
- [ ] **Task:** Show test results in log
  - Like desktop shows each tool status
  - Pass/fail with details

---

### Epic: CORA Can Call Functions Anytime

#### Tool/Action System - MISSING
- [ ] **Task:** Create function registry for web
  - Map commands to functions
  - "take screenshot" -> captureScreen()
  - "play video X" -> playYouTube(X)
  - "generate image X" -> generateImage(X)
- [ ] **Task:** CORA can execute these from chat
  - Parse user commands
  - Call appropriate function
  - Show result in modal
- [ ] **Task:** Functions needed:
  - captureScreen() - take screenshot
  - analyzeScreen() - screenshot + vision
  - openCamera() - show camera feed
  - analyzeCamera() - camera + vision
  - playYouTube(query) - search and play
  - generateImage(prompt) - Pollinations
  - getWeather() - current + forecast
  - getNews() - fetch headlines
  - searchGoogle(query) - web search
  - fetchCode(repo) - GitHub code import

---

## P3 - Nice to Have

### Epic: Full Desktop Feature Parity

- [ ] **Task:** Voice commands via speech recognition
  - Listen for wake word
  - Transcribe speech
  - Execute commands
- [ ] **Task:** Ambient awareness
  - Periodic interjections
  - React to what's on screen
- [ ] **Task:** Task/reminder management
  - Create tasks
  - Set reminders
  - Show in UI

---

## Files That Need Major Changes

| File | Changes Needed |
|------|----------------|
| `web/index.html` | ALL OF THE ABOVE |
| `web/kokoro-worker.js` | Verify working |
| NEW: `web/modals.js` | Modal system |
| NEW: `web/cora-tools.js` | Tool functions |

---

## Quick Reference: Desktop Functions Missing in Web

```javascript
// Desktop has these, web needs equivalents:

cora_respond(context, result, status, mode)  // AI-generated responses
create_popup(title, width, height, parent)   // Modal windows
create_code_window(title, width, height)     // Code viewer
create_image_window(title, width, height)    // Image viewer
get_weather(city)                            // Weather data
get_forecast(city, days)                     // Multi-day forecast
generate_image(prompt, width, height)        // Pollinations API
desktop() / quick_screenshot()               // Screen capture
generate_with_image(prompt, image_path)      // Vision AI
```

---

## Comparison: What Desktop Phase Does vs Web

### Phase 4.1 Code Import
**Desktop:**
```python
# Fetches actual code from GitHub API
# Shows code in modal window with syntax highlighting
# Announces "Pulled X lines from your GitHub"
```
**Web:**
```javascript
// Just logs "GitHub API accessible"
// No actual fetch
// No modal
```

### Phase 4.2 YouTube Test
**Desktop:**
```python
# Searches YouTube with yt-dlp
# Shows video info modal (title, URL)
# Plays video with mpv for 20 seconds
# Announces "Found: [title]. Playing sample."
```
**Web:**
```javascript
// Just logs "YouTube IFrame API - Available"
// No search
// No modal
// No playback
```

### Phase 6.1 Audio Test
**Desktop:**
```python
# Searches for random music (lofi, synthwave, etc)
# Plays audio via mpv for 20 seconds
# Announces "Audio working. Playing [genre]."
```
**Web:**
```javascript
// Just logs "Web Audio API - Available"
// No actual playback
```

### Phase 8.0 Vision Test
**Desktop:**
```python
# Takes actual screenshot of desktop
# Shows screenshot in modal for 5 seconds
# Sends to llava for AI vision analysis
# CORA describes what she sees on screen
```
**Web:**
```javascript
// Just checks "Screen Capture API - Available"
// No actual capture
// No modal
// No AI analysis
```

### Phase 9.0 Image Gen
**Desktop:**
```python
# Asks Ollama for creative prompt
# Generates image via Pollinations Flux
# Shows image in modal
# Sends to llava to describe what was generated
# CORA describes the image
```
**Web:**
```javascript
// Just checks if Pollinations is online
// No generation
// No modal
// No AI description
```

---

## Priority Order for Fixes

1. **Modal system** - Need this for everything else
2. **cora_respond()** - AI personality in responses
3. **Image generation** - Actually generate and show
4. **YouTube embed** - Actually search and play
5. **Screenshot/vision** - Capture and analyze
6. **Code import** - Fetch and display
7. **Audio playback** - Play test sound
8. **Weather forecast** - Add 3-day
9. **News reading** - CORA announces headlines
10. **Tool functions** - So CORA can call them from chat

---

*Unity AI Lab - C.O.R.A Web Version TODO*
*This is a MASSIVE overhaul - desktop does real tests, web just checks if APIs exist*
