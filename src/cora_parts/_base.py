#!/usr/bin/env python3
"""Shared base of the src.cora_parts package (split from src/cora.py on 2026-10-14): imports, module
state, the helpers and every function that rebinds a module global."""
from __future__ import annotations
#!/usr/bin/env python3
r"""
# ================================================================
#   ____   ___   ____      _
#  / ___| / _ \ |  _ \    / \
# | |    | | | || |_) |  / _ \
# | |___ | |_| ||  _ <  / ___ \
#  \____| \___/ |_| \_\/_/   \_\
#
# C.O.R.A - Cognitive Operations & Reasoning Assistant
# ================================================================
# Version: 1.0.0
# Unity AI Lab
# Website: https://www.unityailab.com
# GitHub: https://github.com/Unity-Lab-AI
# Contact: unityailabcontact@gmail.com
# Creators: Hackall360, Sponge, GFourteen, Alfreddo
# ================================================================
#
# A text-based cognitive assistant CLI application.

Usage:
    python cora.py                    - Start interactive mode
    python cora.py [command] [args]   - Run single command

Task Commands:
    add <text>           Create a new task with description
    list (ls)            Show all tasks with status and priority
    show <id>            Show detailed task view
    done <id>            Mark a task as complete
    delete <id>          Remove a task permanently (del/rm)
    pri <id> <1-10>      Set task priority (1=highest)
    due <id> <date>      Set due date (YYYY-MM-DD or +Nd)
    note <id> <text>     Add a note to a task
    status <id> <state>  Change status (pending|active|done)
    edit <id> <text>     Edit task description
    search <query>       Search tasks by text
    stats                Show task statistics

Knowledge Commands:
    learn <text> [#tags] Add knowledge entry with optional tags
    recall [#tag]        View knowledge entries (filter by tag)

AI Commands:
    chat <message>       Chat with AI (context-aware about your tasks)
    speak <text>         Speak text using TTS
    pull <model>         Pull an Ollama model

Other:
    backup               Create backup of all data
    help (?)             Show this help
    exit (quit, q)       Exit program

Task Format:
    - ID: Auto-generated (T001, T002, etc.)
    - Text: Task description
    - Status: pending, active, or done
    - Priority: 1-10 (default 5, 1=highest)
    - Due: Due date (YYYY-MM-DD format)
    - Created: ISO timestamp
    - Notes: List of notes

Data Storage:
    tasks.json     - Task storage
    knowledge.json - Knowledge base
    config.json    - Configuration

Examples:
    cora> add Buy groceries
    cora> pri T001 1                  Set highest priority
    cora> due T001 +3d                Due in 3 days
    cora> chat What should I focus on?   AI helps with tasks
    cora> learn Python is awesome #coding
"""

# Canonical version constant - import this everywhere
VERSION = "1.0.0"

import argparse
import asyncio
import json
import logging
import os
import sys
import shutil
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def get_system_prompt() -> str:
    from src.cora_parts.logging_setup import _PROJECT_DIR
    """Load CORA's full system prompt from config/system_prompt.txt."""
    global _cora_system_prompt_cache
    if _cora_system_prompt_cache is not None:
        return _cora_system_prompt_cache

    system_prompt_path = _PROJECT_DIR / 'config' / 'system_prompt.txt'
    if system_prompt_path.exists():
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            _cora_system_prompt_cache = f.read()
    else:
        _cora_system_prompt_cache = ""
    return _cora_system_prompt_cache

# Load paths from config if available, otherwise use defaults
def get_path(name, default):
    """Get path from config or use default."""
    global CONFIG
    if CONFIG and 'paths' in CONFIG:
        return DATA_DIR / CONFIG['paths'].get(name, default)
    return DATA_DIR / default


def init_paths():
    """Initialize file paths from config. Call after load_config()."""
    global TASKS_FILE, KNOWLEDGE_FILE, BACKUP_DIR, PERSONALITY_FILE
    TASKS_FILE = get_path('tasks_file', 'tasks.json')
    KNOWLEDGE_FILE = get_path('knowledge_file', 'knowledge.json')
    BACKUP_DIR = get_path('backup_dir', 'backups')
    PERSONALITY_FILE = get_path('personality_file', 'personality.json')


def load_config():
    from src.cora_parts.logging_setup import CONFIG_FILE, logger
    """Load configuration from config.json."""
    global CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                CONFIG = json.load(f)
                init_paths()  # Update paths from config
                return CONFIG
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config: {e}")
    # Return defaults if no config
    CONFIG = {
        'tts': {'enabled': True, 'rate': 150, 'volume': 0.9},
        'ollama': {'enabled': True, 'model': 'llama3.2'},
        'paths': {'tasks_file': 'tasks.json', 'knowledge_file': 'knowledge.json'}
    }
    init_paths()  # Initialize paths with defaults
    return CONFIG


def main():
    from src.cora_parts.logging_setup import COMMANDS, SYSTEM_TRAY_AVAILABLE, create_system_tray, load_personality, logger, parse_input
    from src.cora_parts.boot import boot_sequence
    from src.cora_parts.chat import generate_greeting, respond
    """Main entry point with command loop."""
    global _system_tray

    # Load config first
    load_config()

    # Run first-time setup if needed
    first_run_setup()

    # Run boot sequence (system diagnostics and startup checks)
    # This runs the full 18-check boot sequence per ARCHITECTURE.md
    try:
        boot_sequence()
    except Exception as e:
        logger.warning(f"Boot sequence warning: {e}")
        # Non-fatal - continue startup even if boot fails

    # Start system tray icon (runs in background thread)
    if SYSTEM_TRAY_AVAILABLE:
        def on_tray_quit():
            from src.cora_parts.logging_setup import logger
            """Handle quit from system tray."""
            logger.info("System tray quit requested")
            os._exit(0)

        def on_tray_settings():
            from src.cora_parts.logging_setup import logger
            """Handle settings from system tray."""
            logger.info("System tray settings requested")
            print("[*] Settings panel not implemented yet")

        _system_tray = create_system_tray(
            on_quit=on_tray_quit,
            on_settings=on_tray_settings
        )
        if _system_tray:
            _system_tray.start()
            logger.info("System tray icon started")

    # Load personality for greeting
    personality = load_personality()

    print("")
    print("  ==================================================")
    print("    ____   ___   ____      _")
    print("   / ___| / _ \\ |  _ \\    / \\")
    print("  | |    | | | || |_) |  / _ \\")
    print("  | |___ | |_| ||  _ <  / ___ \\")
    print("   \\____| \\___/ |_| \\_\\/_/   \\_\\")
    print("")
    print(f"  {personality.get('name', 'C.O.R.A')} v{VERSION}")
    print("  Cognitive Operations & Reasoning Assistant")
    print("  ==================================================")
    print("  Unity AI Lab | unityailab.com")
    print("  ==================================================")
    greeting = generate_greeting(personality)
    print(f"\n  {greeting}\n")
    speak(greeting)
    print("  Type 'help' for commands, 'exit' to quit\n")

    # Load existing tasks
    tasks = load_tasks()

    # Command dispatch table (shared with the GUI app)
    commands = COMMANDS

    # Main loop
    while True:
        try:
            user_input = input("cora> ").strip()

            if not user_input:
                continue

            cmd, args = parse_input(user_input)

            # Check for exit commands
            if cmd in ('exit', 'quit', 'q'):
                respond('shutdown', {})
                try:
                    from ai.ollama import unload_models
                    unload_models()          # her models leave the GPU on exit
                except Exception:
                    pass
                # Stop system tray before exit
                if _system_tray:
                    _system_tray.stop()
                break

            # Execute command; anything that is not a command is a chat message
            # for the assistant (tools + her voice via ai.dispatcher)
            if cmd in commands:
                tasks = commands[cmd](args, tasks)
            else:
                tasks = cmd_chat(user_input.split(), tasks)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            # Stop system tray
            if _system_tray:
                _system_tray.stop()
            break
        except EOFError:
            print("\nGoodbye!")
            # Stop system tray
            if _system_tray:
                _system_tray.stop()
            break


def load_chat_history():
    from src.cora_parts.logging_setup import CHAT_HISTORY_FILE, MAX_CHAT_HISTORY
    """Load chat history from JSON file."""
    global CHAT_HISTORY
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r') as f:
                CHAT_HISTORY = json.load(f)
                # Keep only the last MAX_CHAT_HISTORY exchanges
                if len(CHAT_HISTORY) > MAX_CHAT_HISTORY * 2:
                    CHAT_HISTORY = CHAT_HISTORY[-(MAX_CHAT_HISTORY * 2):]
                return CHAT_HISTORY
        except (json.JSONDecodeError, IOError):
            CHAT_HISTORY = []
    return CHAT_HISTORY


def save_chat_history():
    from src.cora_parts.logging_setup import CHAT_HISTORY_FILE, MAX_CHAT_HISTORY
    """Save chat history to JSON file."""
    global CHAT_HISTORY
    # Keep only the last MAX_CHAT_HISTORY exchanges (user + assistant = 2 per exchange)
    if len(CHAT_HISTORY) > MAX_CHAT_HISTORY * 2:
        CHAT_HISTORY = CHAT_HISTORY[-(MAX_CHAT_HISTORY * 2):]
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(CHAT_HISTORY, f, indent=2)


def add_to_chat_history(role, content):
    """Add a message to chat history."""
    global CHAT_HISTORY
    CHAT_HISTORY.append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    })
    save_chat_history()


def get_chat_history_context():
    from src.cora_parts.logging_setup import MAX_CHAT_HISTORY
    """Get formatted chat history for AI context."""
    global CHAT_HISTORY
    if not CHAT_HISTORY:
        return ""

    history_parts = []
    for msg in CHAT_HISTORY[-(MAX_CHAT_HISTORY * 2):]:
        role = "User" if msg['role'] == 'user' else "CORA"
        history_parts.append(f"{role}: {msg['content']}")

    return "\n".join(history_parts)


def cmd_chat(args, tasks):
    from src.cora_parts.chat import fallback_response, respond
    from src.cora_parts.logging_setup import logger
    """Chat with AI using Ollama with task context and conversation memory. Usage: chat <message>

    Per ARCHITECTURE.md v1.0.0: Uses ThreadPoolExecutor for non-blocking Ollama calls.
    This fixes the async/sync mismatch when GUI calls this function.
    """
    global CONFIG
    if CONFIG is None:
        load_config()

    if not args:
        respond('error', {'message': "Please provide a message. Usage: chat <your message>"})
        return tasks

    user_message = ' '.join(args)

    print(f"[You]: {user_message}")
    print("[CORA]: Thinking...")

    response = None
    try:
        # The shared assistant loop: tools, history and her voice all live there
        from ai.dispatcher import get_dispatcher
        d = get_dispatcher()
        d.confirm_callback = lambda q: input(f"[CORA] Allow {q}? (y/n) ").strip().lower().startswith('y')
        speak_it = bool(CONFIG.get('tts', {}).get('enabled', True))

        def on_event(kind, payload):
            if kind == 'tool_call':
                print(f"  -> {payload['tool']} {payload.get('arguments') or ''}")
            elif kind == 'tool_result':
                r = payload.get('result') or {}
                print(f"  <- {r.get('message') or r.get('error') or ''}"[:200])

        result = d.handle(user_message, speak=speak_it, on_event=on_event)
        if result.error:
            logger.warning(f"Chat offline mode: {result.error}")
            response = fallback_response(user_message, tasks)
            print(f"[CORA]: {response}")
            print(f"({result.error})")
        else:
            response = result.text or "(done)"
            print(f"[CORA]: {response}")
            # dispatcher already saved the exchange to the shared history
            load_chat_history()
            return load_tasks()
    except Exception as e:
        logger.warning(f"Chat offline mode: {e}")
        response = fallback_response(user_message, tasks)
        print(f"[CORA]: {response}")
        print(f"(Offline mode due to: {e})")

    # Save conversation to history (fallback path only)
    if response:
        add_to_chat_history('user', user_message)
        add_to_chat_history('assistant', response)

    return tasks


def cmd_chathistory(args, tasks):
    """View or clear chat history. Usage: chathistory [clear]"""
    global CHAT_HISTORY

    load_chat_history()

    if args and args[0].lower() == 'clear':
        CHAT_HISTORY = []
        save_chat_history()
        print("[CORA]: Chat history cleared.")
        return tasks

    if not CHAT_HISTORY:
        print("No chat history yet. Start a conversation with 'chat <message>'.")
        return tasks

    print("\n=== CHAT HISTORY ===")
    print("-" * 50)
    for msg in CHAT_HISTORY:
        role = "You" if msg['role'] == 'user' else "CORA"
        timestamp = msg.get('timestamp', '')[:16].replace('T', ' ')
        print(f"[{timestamp}] {role}: {msg['content'][:60]}...")
    print("-" * 50)
    print(f"Total messages: {len(CHAT_HISTORY)}")
    print("Use 'chathistory clear' to clear history.")
    return tasks


def cmd_settings(args, tasks):
    from src.cora_parts.logging_setup import CONFIG_FILE
    """View or modify settings. Usage: settings [key] [value]"""
    global CONFIG

    if CONFIG is None:
        load_config()

    if not args:
        # Show all settings
        print("\n=== CORA SETTINGS ===")
        print("-" * 50)
        print(f"App Name:      {CONFIG.get('app_name', 'C.O.R.A')}")
        print(f"Version:       {CONFIG.get('version', '0.5.0')}")
        print("")
        print("TTS Settings:")
        tts = CONFIG.get('tts', {})
        print(f"  Enabled:     {tts.get('enabled', True)}")
        print(f"  Engine:      {tts.get('engine', 'pyttsx3')}")
        print(f"  Rate:        {tts.get('rate', 150)}")
        print(f"  Volume:      {tts.get('volume', 1.0)}")
        print("")
        print("Ollama Settings:")
        ollama = CONFIG.get('ollama', {})
        print(f"  Enabled:     {ollama.get('enabled', True)}")
        print(f"  Model:       {ollama.get('model', 'llama3.2')}")
        print("")
        print("Paths:")
        paths = CONFIG.get('paths', {})
        print(f"  Tasks:       {paths.get('tasks_file', 'tasks.json')}")
        print(f"  Knowledge:   {paths.get('knowledge_file', 'knowledge.json')}")
        print(f"  Backups:     {paths.get('backup_dir', 'backups')}")
        print("-" * 50)
        print("Usage: settings <key> <value> to modify")
        print("Example: settings tts.rate 180")
        return tasks

    if len(args) == 1:
        # Show specific setting
        key = args[0].lower()
        parts = key.split('.')

        if len(parts) == 1:
            value = CONFIG.get(parts[0])
        elif len(parts) == 2:
            section = CONFIG.get(parts[0], {})
            value = section.get(parts[1]) if isinstance(section, dict) else None
        else:
            value = None

        if value is not None:
            print(f"{key} = {value}")
        else:
            print(f"Unknown setting: {key}")
        return tasks

    # Set a value
    key = args[0].lower()
    value_str = ' '.join(args[1:])
    parts = key.split('.')

    # Convert value to appropriate type
    if value_str.lower() == 'true':
        value = True
    elif value_str.lower() == 'false':
        value = False
    elif value_str.isdigit():
        value = int(value_str)
    elif value_str.replace('.', '').isdigit():
        value = float(value_str)
    else:
        value = value_str

    # Update config
    if len(parts) == 1:
        CONFIG[parts[0]] = value
    elif len(parts) == 2:
        if parts[0] not in CONFIG:
            CONFIG[parts[0]] = {}
        CONFIG[parts[0]][parts[1]] = value
    else:
        print("Invalid key format. Use 'key' or 'section.key'")
        return tasks

    # Save to file
    with open(CONFIG_FILE, 'w') as f:
        json.dump(CONFIG, f, indent=2)

    print(f"Updated: {key} = {value}")
    return tasks


def speak(text):
    from src.cora_parts.chat import detect_emotion
    from src.cora_parts.logging_setup import logger
    """Speak text in CORA's own voice (unity-voice-v2) with emotion detection.

    Blocking: returns when the line has been spoken (or False if the voice
    sidecar is unavailable). There is no fallback voice by design.
    """
    global CONFIG
    if CONFIG is None:
        load_config()

    if not CONFIG.get('tts', {}).get('enabled', True):
        return False

    emotion = detect_emotion(text)
    try:
        from voice.tts import speak as _voice_speak
        return bool(_voice_speak(text, emotion))
    except Exception as e:
        logger.warning(f"voice unavailable: {e}")
        return False


def init_tts():
    from src.cora_parts.logging_setup import logger
    """Initialize the voice: returns the shared TTS queue (or None)."""
    global CONFIG
    if CONFIG is None:
        load_config()
    if not CONFIG.get('tts', {}).get('enabled', True):
        return None
    try:
        from voice.tts import get_tts_queue
        return get_tts_queue()
    except Exception as e:
        logger.error(f"TTS init error: {e}")
        return None


def first_run_setup():
    from src.cora_parts.system import auto_pull_model, check_ollama, progress_spinner
    from src.cora_parts.voice import check_tts
    """Check and setup required components on first run."""
    global CONFIG
    if CONFIG is None:
        load_config()

    setup_file = DATA_DIR / '.setup_complete'
    if setup_file.exists():
        return True

    print("\n=== FIRST RUN SETUP ===")
    print("Checking required components...\n")

    # Step 1: Check Ollama
    progress_spinner("Checking Ollama installation...")
    if check_ollama():
        print("[OK] Ollama is installed")
        if CONFIG.get('auto_setup', {}).get('auto_pull_model', False):
            model = CONFIG.get('ollama', {}).get('model', 'llama3.2')
            progress_spinner(f"Pulling model '{model}'...")
            auto_pull_model(model)
    else:
        print("[!] Ollama not found.")
        print("    Download from: https://ollama.ai")

    # Step 2: Check TTS (her own voice sidecar)
    progress_spinner("Checking text-to-speech...")
    if check_tts():
        print("[OK] Voice (unity-voice-v2) available")
    else:
        print("[!] Voice server not reachable (see data/voice-sidecar.log)")

    # Step 3: Create backup directory
    progress_spinner("Setting up backup directory...")
    BACKUP_DIR.mkdir(exist_ok=True)
    print("[OK] Backup directory ready")

    # Step 4: Initialize data files
    progress_spinner("Initializing data files...")
    if not os.path.exists(TASKS_FILE):
        save_tasks([])
        print("[OK] Tasks file created")
    if not os.path.exists(KNOWLEDGE_FILE):
        save_knowledge([])
        print("[OK] Knowledge file created")

    # Mark setup complete
    with open(setup_file, 'w') as f:
        f.write(datetime.now().isoformat())

    print("\n=== SETUP COMPLETE ===\n")
    return True


def load_knowledge():
    """Load knowledge entries from JSON file."""
    global knowledge_counter
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE, 'r') as f:
                data = json.load(f)
                knowledge_counter = data.get('counter', 0)
                return data.get('entries', [])
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_knowledge(entries):
    """Save knowledge entries to JSON file."""
    global knowledge_counter
    data = {
        'counter': knowledge_counter,
        'entries': entries
    }
    with open(KNOWLEDGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def generate_knowledge_id():
    """Generate unique knowledge ID."""
    global knowledge_counter
    knowledge_counter += 1
    return f"K{knowledge_counter:03d}"


def load_tasks():
    """Load tasks from JSON file."""
    global task_counter
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                data = json.load(f)
                task_counter = data.get('counter', 0)
                return data.get('tasks', [])
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_tasks(tasks):
    """Save tasks to JSON file."""
    global task_counter
    data = {
        'counter': task_counter,
        'tasks': tasks
    }
    with open(TASKS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def generate_id():
    """Generate unique task ID."""
    global task_counter
    task_counter += 1
    return f"T{task_counter:03d}"


def cmd_delete(args, tasks):
    from src.cora_parts.chat import respond
    """Delete a task. Use 'undo' to restore."""
    global _last_deleted_task
    if not args:
        respond('error', {'message': "Please provide task ID. Usage: delete <id>"})
        return tasks

    task_id = args[0].upper()
    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            removed = tasks.pop(i)
            _last_deleted_task = removed.copy()  # Save for undo
            save_tasks(tasks)
            respond('task_deleted', {'id': task_id, 'text': removed['text'][:40]})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_undo(args, tasks):
    from src.cora_parts.chat import respond
    """Restore the last deleted task."""
    global _last_deleted_task

    if _last_deleted_task is None:
        respond('error', {'message': "Nothing to undo. No recently deleted task."})
        return tasks

    # Restore the task
    tasks.append(_last_deleted_task)
    save_tasks(tasks)
    restored_id = _last_deleted_task['id']
    restored_text = _last_deleted_task['text'][:40]
    _last_deleted_task = None

    print(f"[CORA]: Restored task {restored_id}: {restored_text}")
    speak(f"Restored task {restored_id}")
    return tasks

# Global system tray instance
_system_tray = None

# Cache for system prompt
_cora_system_prompt_cache = None


# Default paths (will be overridden by init_paths after config loads)
TASKS_FILE = DATA_DIR / 'tasks.json'
KNOWLEDGE_FILE = DATA_DIR / 'knowledge.json'
BACKUP_DIR = ROOT_DIR / 'backups'
PERSONALITY_FILE = CONFIG_DIR / 'personality.json'

# Chat history for conversation memory
CHAT_HISTORY = []

# Counters for ID generation
task_counter = 0
knowledge_counter = 0

# Global config (loaded at startup)
CONFIG = None


# Global for undo functionality (declared here for cmd_delete to access)
_last_deleted_task = None


# Global for undo functionality
_last_deleted_task = None
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).parent
DATA_DIR = ROOT_DIR / 'data'
CONFIG_DIR = ROOT_DIR / 'config'
