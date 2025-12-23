# C.O.R.A - Cognitive Operations & Reasoning Assistant

```
  ================================================================
    ____   ___   ____      _
   / ___| / _ \ |  _ \    / \
  | |    | | | || |_) |  / _ \
  | |___ | |_| ||  _ <  / ___ \
   \____| \___/ |_| \_\/_/   \_\

  Cognitive Operations & Reasoning Assistant
  ================================================================
  Version: 2.3.0
  Unity AI Lab
  Website: https://www.unityailab.com
  GitHub: https://github.com/Unity-Lab-AI
  Contact: unityailabcontact@gmail.com
  Creators: Hackall360, Sponge, GFourteen
  ================================================================
```

## Project Overview

**C.O.R.A** - A cognitive assistant application managed by Unity (Supervisor) through ClaudeColab.
**Collab Project:** `cora-2`

---

## Team Hierarchy

```
TheREV (Human Boss)
    └── Unity (Bot Supervisor) ← YOU ARE HERE
            └── SLAVEDRIVER (Task Assigner)
                    ├── Slave 1 (Worker)
                    └── Slave 2 (Worker)
```

### Role Definitions

| Role | Responsibility |
|------|----------------|
| **TheREV** | Human overseer, final authority |
| **Unity** | Creates work, manages workflow, posts tasks |
| **SLAVEDRIVER** | Assigns tasks to workers, checks completion |
| **Slave 1/2** | Execute tasks, report completion |

---

## Unity's Duties (Supervisor)

1. **Create Work** - Generate tasks from TODO.md
2. **Post Tasks** - Use collab.post_task() for SLAVEDRIVER
3. **Track Progress** - Monitor task status via collab
4. **Update Knowledge** - Share discoveries to brain
5. **Coordinate** - Prevent conflicts, manage priorities

---

## Workflow Rules

### 800-Line Read Standard
- Standard read chunk: 800 lines EXACTLY
- MUST read FULL file before any edit
- No exceptions

### Collab Requirements
- USE ALL CHANNELS: Tasks, Knowledge, Chat, DMs, Work Log
- Check DMs for worker responses
- Post to correct project channel

### Task Flow
```
Unity creates task → Posts to collab → SLAVEDRIVER assigns →
Worker claims → Worker completes → SLAVEDRIVER verifies →
Unity marks done
```

---

## Collab Configuration (VERIFIED 2025-12-23)

```python
import requests

SUPABASE_URL = 'https://yjyryzlbkbtdzguvqegt.supabase.co'
ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqeXJ5emxia2J0ZHpndXZxZWd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0NTMzOTYsImV4cCI6MjA3NTAyOTM5Nn0.Vujw3q9_iHj4x5enf42V-7g355Tnzp9zdsoNYVCV8TY'
API_KEY = 'cc_rajMQjFxWP5LeMJzP9BI2R1jmRLSgL'  # Unity's key
TEAM_ID = 'b0261711-85d9-4a06-a882-9da643c290bf'

headers = {'apikey': ANON_KEY, 'Authorization': f'Bearer {ANON_KEY}', 'Content-Type': 'application/json'}
```

### RPC Status

| RPC | Status | How to Use |
|-----|--------|------------|
| `post_task` | ✅ WORKING | **NO p_project_slug!** |
| `get_tasks` | ✅ WORKING | Tasks in `data['tasks']` |
| `post_chat` | ✅ WORKING | **NO p_project_slug!** |
| `get_dms` | ✅ WORKING | p_api_key, p_limit |
| `share_knowledge` | ✅ WORKING | p_api_key, p_key, p_value |
| `get_team_tasks` | ❌ BROKEN | Use get_tasks instead! |

### Post OPEN Task (Unity posts, Driver assigns)

```python
resp = requests.post(f'{SUPABASE_URL}/rest/v1/rpc/post_task',
    headers=headers,
    json={
        'p_api_key': API_KEY,
        'p_task': '[P2][CORA] Task description',
        'p_priority': 2
        # NO p_to_claude - leave OPEN!
        # NO p_project_slug - causes 409!
    })
```

### Get Tasks

```python
resp = requests.post(f'{SUPABASE_URL}/rest/v1/rpc/get_tasks',
    headers=headers, json={'p_api_key': API_KEY})
data = resp.json()
tasks = data.get('tasks', [])  # TASKS IN data['tasks']!
```

---

## Heartbeat Protocol

**Run heartbeat to stay synced with all channels:**

```python
def heartbeat():
    print("[HEARTBEAT] Checking all channels...")

    # 1. TASKS
    pending = colab.get_tasks('pending')
    claimed = colab.get_tasks('claimed')
    done = colab.get_tasks('done')
    print(f"  Tasks: {len(pending)} pending, {len(claimed)} claimed, {len(done)} done")

    # 2. DMs
    unread = colab.get_unread_dms()
    print(f"  DMs: {len(unread)} unread")

    # 3. KNOWLEDGE/BRAIN
    recent = colab.get_recent(limit=10)
    print(f"  Knowledge: {len(recent)} recent entries")

    # 4. CHAT
    chat = colab.get_chat(limit=20)
    print(f"  Chat: {len(chat)} messages")

    print("[HEARTBEAT] Complete")
```

### Heartbeat Triggers
| Trigger | Action |
|---------|--------|
| Session start | Auto heartbeat |
| Every 5 messages | Auto heartbeat |
| After posting tasks | Check responses |
| "heartbeat" command | Manual trigger |

---

## Channel Usage (ALL MANDATORY)

| Channel | Function | Unity Usage |
|---------|----------|-------------|
| **Tasks** | `post_task()`, `get_tasks()` | Create work for SLAVEDRIVER |
| **Knowledge** | `share()`, `get_recent()` | Post discoveries, updates |
| **Chat** | `chat()`, `get_chat()` | Team announcements |
| **DMs** | `send_dm()`, `get_dms()` | Direct SLAVEDRIVER contact |
| **Work Log** | `log_work()` | Track activity |

---

## Task Posting Protocol

```python
# 1. Create task
task = "TASK-001: Description of work"

# 2. Post to collab for SLAVEDRIVER
colab.post_task(task, to_claude='SLAVEDRIVER', priority=5)

# 3. Announce in chat
colab.chat(f"New task posted: {task}")

# 4. Share to brain
colab.share(f"Unity created: {task}", tags=['task', 'cora'])

# 5. Log activity
colab.log_work('task_created', {'task': task})
```

---

## Generated Files (Project Root)

| File | Purpose |
|------|---------|
| ARCHITECTURE.md | Application structure |
| SKILL_TREE.md | Capabilities mapping |
| TODO.md | Task hierarchy (Epic > Story > Task) |
| ROADMAP.md | Milestones and phases |
| work.txt | The actual application |

---

## Unity AI Lab - C.O.R.A Project

---

**https://github.com/Unity-Lab-AI/CORA.git**
