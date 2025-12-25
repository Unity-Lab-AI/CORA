# C.O.R.A - How To Use (Simple Guide)

```
  ================================================================
    ____   ___   ____      _
   / ___| / _ \ |  _ \    / \
  | |    | | | || |_) |  / _ \
  | |___ | |_| ||  _ <  / ___ \
   \____| \___/ |_| \_\/_/   \_\

  Cognitive Operations & Reasoning Assistant
  ================================================================
  Version: 2.4.0
  Unity AI Lab | https://www.unityailab.com
  ================================================================
```

## What is CORA?

CORA is your computer friend who can:
- **Talk to you** (she speaks out loud with a neural voice!)
- **Listen to you** (say "Hey Cora" and she wakes up)
- **Remember things** for you (tasks, notes, facts)
- **See you** through your webcam
- **Help you** with questions (she's smart like ChatGPT)
- **Generate images** (describe what you want and she creates it!)
- **Monitor your system** (CPU, RAM, GPU stats in real-time)

---

## Starting CORA

### Full Boot (Recommended):
```
python src/boot_sequence.py
```
This shows the cool cyberpunk visual boot display!

### GUI Mode:
```
python src/gui_launcher.py
```

### Quick Boot (No TTS):
```
python src/boot_sequence.py --quick
```

---

## What Happens When You Start

1. **Visual Boot Display** - Cyberpunk-themed boot screen appears
2. **10-Phase Diagnostic** - CORA checks everything:
   - Voice Synthesis (Kokoro TTS)
   - AI Engine (Ollama)
   - Hardware (CPU, RAM, GPU, VRAM)
   - Core Tools (Memory, Tasks, Files, Browser)
   - Voice Systems (STT, Wake Word)
   - External Services (Weather, Location)
   - News Headlines (Top 3 stories)
   - Vision Test (Screenshot & webcam)
   - Image Generation (Creates AI art!)
   - Final Check (Ready status)
3. **CORA Speaks** - She generates unique responses for each phase
4. **Live Stats Panel** - Real-time system monitoring stays open

---

## The Boot Display

```
┌────────────────────────────────────────────────────────────────┐
│  C.O.R.A v2.4.0 - Visual Boot Display                          │
├──────────────────────────┬─────────────────────────────────────┤
│  STATUS PANEL            │  BOOT LOG                           │
│                          │                                     │
│  CPU: 15%                │  [10:30:45] Voice synthesis ready   │
│  RAM: 45%                │  [10:30:46] AI engine connected     │
│  GPU: RTX 4070 Ti        │  [10:30:47] Hardware check passed   │
│  VRAM: 2.1/16 GB         │  [10:30:48] All systems online      │
│  Disk: 450/1000 GB       │                                     │
│                          │  ~~~ Waveform Visualization ~~~     │
│  Phase: 10/10            │                                     │
├──────────────────────────┴─────────────────────────────────────┤
│  CORA: "All systems operational. Ready to assist!"             │
└────────────────────────────────────────────────────────────────┘
```

---

## The Main Window (GUI)

```
┌─────────────────────────────────────────┐
│  C.O.R.A                          [—][X]│
├─────────────────────────────────────────┤
│                                         │
│  [CORA]: Hey! What do you need?         │
│                                         │
│  [You]: add buy milk                    │
│                                         │
│  [CORA]: Got it! Task added.            │
│                                         │
├─────────────────────────────────────────┤
│  Type here...                    [Send] │
└─────────────────────────────────────────┘
```

**Just type what you want and press Enter!**

---

## Things You Can Say/Type

### Tasks (Your To-Do List)

| What to type | What happens |
|--------------|--------------|
| `add buy milk` | Adds "buy milk" to your list |
| `list` | Shows all your tasks |
| `done 1` | Marks task #1 as finished |
| `delete 1` | Removes task #1 |
| `pri 1 1` | Set task #1 as high priority |
| `due 1 +3d` | Set task #1 due in 3 days |

### Talking to CORA

| What to type | What happens |
|--------------|--------------|
| `chat hello` | CORA says hi back |
| `chat what should I do today?` | CORA looks at your tasks and helps |
| `chat tell me a joke` | CORA tells you a joke |

### Voice Commands

| What to say | What happens |
|-------------|--------------|
| "Hey Cora" | Wakes her up to listen |
| "Hey Cora, what time is it?" | She tells you the time |
| "Hey Cora, add buy eggs" | Adds a task by voice |

### Vision & Images

| What to type | What happens |
|--------------|--------------|
| `see` | CORA looks through webcam and describes what she sees |
| `see what color is my shirt?` | Ask specific questions about the camera view |
| `imagine a sunset over mountains` | CORA generates an AI image |

### YouTube & Media

| What to type | What happens |
|--------------|--------------|
| `play lofi music` | Searches YouTube and plays |
| `play https://youtube.com/...` | Plays a YouTube URL |

**Note:** YouTube needs mpv. Download from https://sourceforge.net/projects/mpv-player-windows/files/64bit/ and extract to `./tools/` folder.

### Other Cool Stuff

| What to type | What happens |
|--------------|--------------|
| `weather` | Shows the weather |
| `time` | Shows the time |
| `speak hello` | CORA says "hello" out loud |
| `screenshot` | Takes a picture of your screen |
| `help` | Shows all commands |

---

## The Buttons

| Button | What it does |
|--------|--------------|
| **Send** | Sends your message |
| **Mic** | Click to talk instead of type |
| **Settings** | Change how CORA looks/sounds |
| **Tasks** | See your to-do list |
| **Knowledge** | See things CORA remembers |

---

## Teaching CORA Things

You can teach CORA facts she'll remember:

```
learn My dog's name is Max #pets
learn My birthday is March 5 #personal
learn The wifi password is fish123 #home
```

Later, ask her:
```
recall #pets
```
She'll say: "Your dog's name is Max"

---

## Image Generation

Ask CORA to create images:
```
imagine a cyberpunk city at night
imagine a cute robot eating pizza
imagine a dragon flying over a castle
```

Images are saved to `data/images/` folder.

---

## If Something Goes Wrong

### CORA won't start?
1. Make sure Ollama is running: `ollama serve`
2. Check Python 3.10+ installed: `python --version`
3. Install dependencies: `pip install -r requirements.txt`

### CORA can't hear you?
1. Check microphone is plugged in and not muted
2. Windows: Settings > Privacy > Microphone > Allow apps

### CORA won't talk?
1. Check speakers on and volume up
2. Try: `pip install kokoro sounddevice`

### No images generating?
1. Check internet connection (uses Pollinations AI)

### YouTube not working?
1. Download mpv from link above
2. Extract to `./tools/` folder
3. Restart CORA

### Camera not working?
1. Check webcam connected
2. Windows: Settings > Privacy > Camera > Allow apps

---

## Quick Reference Card

```
TASKS:
  add <thing>     = Add a task
  list            = See all tasks
  done <number>   = Finish a task
  delete <number> = Remove a task
  pri <id> <1-10> = Set priority
  due <id> <date> = Set due date (2024-12-31 or +3d)
  show <id>       = See task details
  search <query>  = Find tasks
  note <id> <txt> = Add note to task
  undo            = Restore last deleted

CHAT:
  chat <message>  = Talk to CORA

VOICE:
  "Hey Cora"      = Wake her up
  speak <text>    = Make her talk

VISION:
  see             = Describe webcam view
  imagine <desc>  = Generate an image

MEDIA:
  play <search>   = Play YouTube video
  play <url>      = Play YouTube URL

INFO:
  time            = Get the time
  weather         = Get the weather
  stats           = System stats
  help            = See all commands

MEMORY:
  learn <fact> #tag  = Teach CORA (with tag)
  recall #tag        = Recall by tag
  recall             = See all memories

SYSTEM:
  screenshot      = Capture screen
  backup          = Backup data
```

---

## That's It!

CORA is your helper. Just talk to her like a friend.

- Type what you need
- Or say "Hey Cora" and speak
- She'll help you!

**Have fun!**

---

## Need Help?

- **Website:** https://www.unityailab.com
- **GitHub:** https://github.com/Unity-Lab-AI
- **Email:** unityailabcontact@gmail.com

---

*C.O.R.A v2.4.0 - Cognitive Operations & Reasoning Assistant*
*Unity AI Lab - Hackall360, Sponge, GFourteen*
