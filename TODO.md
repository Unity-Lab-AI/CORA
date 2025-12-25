# TODO - C.O.R.A Web Version

> **STATUS: MAJOR OVERHAUL COMPLETE** - Most desktop parity achieved
> Updated: 2025-12-25 | Session: Unity Workflow

---

## COMPLETED THIS SESSION

| Feature | Status | Notes |
|---------|--------|-------|
| Modal System | ✅ DONE | createModal(), showCodeModal(), showImageModal(), showVideoModal() |
| Phase 4.1 Code Import | ✅ DONE | Actually fetches from GitHub, shows in code modal |
| Phase 4.2 YouTube | ✅ DONE | Searches and embeds YouTube videos in modal |
| Phase 4.3 Modals | ✅ DONE | Shows test modal with random quote |
| Phase 4.4 Browser | ✅ DONE | Full iframe browser with nav controls |
| Phase 6.1 Audio | ✅ DONE | Plays actual test tone using Web Audio API |
| Phase 8.0 Vision | ✅ DONE | Captures screenshot + camera, shows in modal |
| Phase 9.0 Image Gen | ✅ DONE | Actually generates images via Pollinations |
| Chat Commands | ✅ DONE | browse, search, generate image, screenshot, camera, play, weather, news |
| Popup Console | ✅ DONE | Opens console in separate window for side-by-side viewing |
| CORA's Browser | ✅ DONE | Full browser with URL bar, back/forward, search |

---

## REMAINING ITEMS

### P1 - Should Do

#### 3-Day Weather Forecast
- [ ] Add forecast data (today, tomorrow, day after)
- [ ] Display in boot sequence

#### News Reading Enhancement
- [ ] CORA reads headlines aloud with AI personality
- [ ] Summarize instead of just listing

---

### P2 - Nice to Have

#### Voice Commands
- [x] Wake word detection ("Hey CORA") - DONE
- [ ] Full voice command parsing
- [ ] Voice-to-text for chat

#### Ambient Awareness
- [ ] Periodic interjections
- [ ] React to what's on screen

---

### P3 - Future

- [ ] Task/reminder management
- [ ] Desktop notifications
- [ ] Persistent settings across sessions

---

## Summary of Web Version Capabilities

**CORA can now:**
- Browse the web (iframe-based browser)
- Search Google
- Fetch code from GitHub (shows in modal)
- Play YouTube videos (embedded)
- Generate images via Pollinations
- Take screenshots
- Access camera and capture frames
- Play audio test tones
- Get weather (with API key)
- Fetch news headlines
- Respond via Ollama chat with full personality

**Available Chat Commands:**
- `browse [url]` - Open URL in browser
- `search [query]` - Google search
- `generate image [prompt]` - Create image
- `take screenshot` - Capture display
- `open camera` - Show camera feed
- `play [song/video]` - YouTube embed
- `weather` - Get current weather
- `news` - Fetch headlines

---

*Unity AI Lab - C.O.R.A Web Version v2.4.0*
*Session: 2025-12-25*
