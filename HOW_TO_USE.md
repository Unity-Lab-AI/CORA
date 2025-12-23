# C.O.R.A - How To Use (Simple Guide)

## What is CORA?

CORA is your computer friend who can:
- **Talk to you** (she speaks out loud!)
- **Listen to you** (say "Hey Cora" and she wakes up)
- **Remember things** for you (tasks, notes, facts)
- **See you** through your webcam
- **Help you** with questions (she's smart like ChatGPT)

---

## Starting CORA

### Double-click to start:
```
start_gui.bat
```

### Or type in terminal:
```
python gui_launcher.py
```

### Quick start (skip the intro):
```
python gui_launcher.py --quick
```

---

## What Happens When You Start

1. **Splash Screen** - Pretty loading screen appears
2. **Boot Checks** - CORA checks everything:
   - What time is it?
   - Where are you?
   - What's the weather?
   - Do you have tasks due?
   - Is the AI brain ready?
3. **CORA Speaks** - She tells you a summary out loud
4. **Main Window** - The app opens and you can chat!

---

## The Main Window

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
| **🎤 (Microphone)** | Click to talk instead of type |
| **⚙️ (Settings)** | Change how CORA looks/sounds |
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

## If Something Goes Wrong

### CORA won't start?
1. Make sure Ollama is running (the AI brain)
2. Open a terminal and type: `ollama serve`

### CORA can't hear you?
1. Check your microphone is plugged in
2. Make sure it's not muted

### CORA won't talk?
1. Check your speakers are on
2. Check volume isn't zero

---

## Quick Reference Card

```
TASKS:
  add <thing>     = Add a task
  list            = See all tasks
  done <number>   = Finish a task
  delete <number> = Remove a task

CHAT:
  chat <message>  = Talk to CORA

VOICE:
  "Hey Cora"      = Wake her up
  speak <text>    = Make her talk

INFO:
  time            = Get the time
  weather         = Get the weather
  help            = See all commands

MEMORY:
  learn <fact>    = Teach CORA something
  recall          = Ask CORA to remember
```

---

## That's It!

CORA is your helper. Just talk to her like a friend.

- Type what you need
- Or say "Hey Cora" and speak
- She'll help you!

**Have fun!** 🎉

---

*C.O.R.A v2.3.0 - Your Computer Friend*
*Made by Unity AI Lab*
