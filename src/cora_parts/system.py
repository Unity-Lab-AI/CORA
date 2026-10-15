#!/usr/bin/env python3
"""src.cora_parts: system (split from src/cora.py on 2026-10-14)."""
from __future__ import annotations

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
from src.cora_parts import _base  # noqa: F401
from src.cora_parts._base import VERSION, datetime, os, shutil, speak, subprocess, sys  # noqa: F401




def check_ollama():
    """Check if Ollama is running (configured URL via ai.settings)."""
    try:
        from ai.ollama import check_ollama as _check
        return bool(_check().get('connected'))
    except Exception:
        return False


def auto_pull_model(model_name):
    from src.cora_parts.logging_setup import logger
    """Auto-pull an Ollama model if not present."""
    try:
        # Check if model exists
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if model_name in result.stdout:
            logger.info(f"Model '{model_name}' already available")
            return True

        logger.info(f"Pulling model '{model_name}' (this may take a while)...")
        pull_result = subprocess.run(['ollama', 'pull', model_name], timeout=600)
        if pull_result.returncode == 0:
            logger.info(f"Model '{model_name}' pulled successfully")
            return True
        else:
            logger.error(f"Failed to pull model '{model_name}'")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout pulling model '{model_name}'")
        return False
    except Exception as e:
        logger.error(f"Error pulling model: {e}")
        return False


def progress_spinner(message, duration=0.5):
    """Display a spinning progress indicator (non-blocking version).

    Per ARCHITECTURE.md v1.0.0: Non-blocking UI updates.
    Uses generator pattern for async compatibility.
    """
    import sys
    # Simple immediate display for CLI (no blocking sleep)
    sys.stdout.write(f'[...] {message}\n')
    sys.stdout.flush()


def cmd_pull_model(args, tasks):
    from src.cora_parts.logging_setup import logger
    """Pull an Ollama model. Usage: pull <model_name>"""
    if not args:
        print("Error: Please provide model name")
        print("Usage: pull <model_name>")
        print("Examples: pull llama3.2, pull mistral, pull codellama")
        return tasks

    model = args[0]
    print(f"Pulling model '{model}'...")
    print("This may take a while depending on model size.")

    try:
        result = subprocess.run(
            ['ollama', 'pull', model],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Model '{model}' pulled successfully!")
            print(result.stdout)
        else:
            logger.error(f"Error pulling model: {result.stderr}")
            print(f"Error pulling model: {result.stderr}")
    except FileNotFoundError:
        logger.error("Ollama not found")
        print("Error: Ollama not found. Please install Ollama first.")
        print("Visit: https://ollama.ai")
    except Exception as e:
        logger.error(f"Pull model error: {e}")
        print(f"Error: {e}")

    return tasks


def cmd_backup(args, tasks):
    from src.cora_parts.chat import respond
    """Create backup of all data files."""
    # Ensure backup directory exists
    if not os.path.exists(_base.BACKUP_DIR):
        os.makedirs(_base.BACKUP_DIR)

    # Generate timestamp for backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    backed_up = []

    # Backup tasks.json
    if os.path.exists(_base.TASKS_FILE):
        backup_name = f"tasks_{timestamp}.json"
        shutil.copy(_base.TASKS_FILE, _base.BACKUP_DIR / backup_name)
        backed_up.append(f"tasks.json -> {backup_name}")

    # Backup knowledge.json
    if os.path.exists(_base.KNOWLEDGE_FILE):
        backup_name = f"knowledge_{timestamp}.json"
        shutil.copy(_base.KNOWLEDGE_FILE, _base.BACKUP_DIR / backup_name)
        backed_up.append(f"knowledge.json -> {backup_name}")

    if backed_up:
        respond('backup_created', {'count': len(backed_up)})
        print(f"Location: {_base.BACKUP_DIR}")
        for b in backed_up:
            print(f"  {b}")
    else:
        respond('error', {'message': "No data files found to backup."})

    return tasks


def cmd_about(args, tasks):
    """Show about information for C.O.R.A."""
    print("")
    print("  ================================================================")
    print("    ____   ___   ____      _")
    print("   / ___| / _ \\ |  _ \\    / \\")
    print("  | |    | | | || |_) |  / _ \\")
    print("  | |___ | |_| ||  _ <  / ___ \\")
    print("   \\____| \\___/ |_| \\_\\/_/   \\_\\")
    print("")
    print("  C.O.R.A - Cognitive Operations & Reasoning Assistant")
    print("  ================================================================")
    print(f"  Version:  {VERSION}")
    print("  ================================================================")
    print("")
    print("  CREATED BY UNITY AI LAB")
    print("  ----------------------------------------------------------------")
    print("  Website:  https://www.unityailab.com")
    print("  GitHub:   https://github.com/Unity-Lab-AI")
    print("  Email:    unityailabcontact@gmail.com")
    print("")
    print("  Creators: Hackall360, Sponge, GFourteen, Alfreddo")
    print("  ================================================================")
    print("")
    return tasks


def cmd_help(args, tasks):
    """Show help message."""
    print(f"""
  ================================================================
  C.O.R.A - Cognitive Operations & Reasoning Assistant
  Version {VERSION} | Unity AI Lab
  ================================================================

TASK COMMANDS:
    add <text>           Create a new task
    list [pri]           List tasks (add 'pri' to sort by priority)
    show <id>            Show detailed task view
    done <id>            Mark task as complete
    delete <id>          Remove task (aliases: del, rm)
    pri <id> <1-10>      Set priority (1=highest)
    due <id> <date>      Set due date (YYYY-MM-DD or +Nd)
    note <id> <text>     Add note to task
    status <id> <state>  Change status (pending, active, done)
    search <query>       Search tasks by text

KNOWLEDGE COMMANDS:
    learn <text> [#tags] Add knowledge entry with optional tags
    recall [#tag]        View knowledge entries (filter by tag)

OTHER:
    help (?)             Show this help
    exit (quit, q)       Exit program

EXAMPLES:
    add Buy groceries                Create task
    list pri                         List sorted by priority
    learn Python is awesome #coding  Add knowledge with tag
    recall #coding                   View coding entries

DATA:
    tasks.json     - Task storage
    knowledge.json - Knowledge base
""")
    return tasks


def cmd_clear(args, tasks):
    """Clear the terminal screen."""
    import platform
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')
    return tasks


def cmd_remind(args, tasks):
    from src.cora_parts.chat import respond
    """Set a reminder. Usage: remind <time> <message>

    Time formats: 'in 5 minutes', 'at 3pm', 'tomorrow at 9am'
    """
    if len(args) < 2:
        respond('error', {'message': "Usage: remind <time> <message>\nExamples: remind 'in 30 minutes' Check email"})
        return tasks

    # Try to parse time from args
    time_words = []
    message_words = []
    found_message = False

    for word in args:
        if not found_message and word.lower() in ('in', 'at', 'tomorrow', 'minutes', 'hours', 'hour', 'minute', 'pm', 'am'):
            time_words.append(word)
        elif time_words and word[0].isdigit():
            time_words.append(word)
        else:
            found_message = True
            message_words.append(word)

    if not message_words:
        # Assume first arg is time expression, rest is message
        time_str = args[0]
        message = ' '.join(args[1:])
    else:
        time_str = ' '.join(time_words) if time_words else args[0]
        message = ' '.join(message_words)

    try:
        from cora_tools.reminders import parse_time_string, ReminderManager

        remind_time = parse_time_string(time_str)
        if remind_time is None:
            # Try with 'in' prefix
            remind_time = parse_time_string(f'in {time_str}')

        if remind_time is None:
            respond('error', {'message': f"Couldn't parse time: '{time_str}'. Try: 'in 5 minutes', 'at 3pm', 'tomorrow'"})
            return tasks

        manager = ReminderManager()
        reminder_id = manager.add(message, remind_time)

        time_display = remind_time.strftime('%I:%M %p')
        respond('info', {'message': f"Reminder set ({reminder_id}): '{message}' at {time_display}"})
        speak(f"Got it, I'll remind you at {time_display}")

    except ImportError:
        respond('error', {'message': "Reminder system not available"})
    except Exception as e:
        respond('error', {'message': f"Failed to set reminder: {e}"})

    return tasks


def cmd_open(args, tasks):
    from src.cora_parts.chat import respond
    """Open a file or application. Usage: open <path or app name>"""
    if not args:
        respond('error', {'message': "Usage: open <file path or app name>"})
        return tasks

    target = ' '.join(args)

    try:
        from cora_tools.system import open_file, launch_app
        import os

        # Check if it's a file path
        if os.path.exists(target):
            if open_file(target):
                respond('info', {'message': f"Opened: {target}"})
            else:
                respond('error', {'message': f"Failed to open: {target}"})
        else:
            # Try as application name
            if launch_app(target):
                respond('info', {'message': f"Launched: {target}"})
            else:
                respond('error', {'message': f"Could not open or launch: {target}"})

    except ImportError:
        respond('error', {'message': "System tools not available"})
    except Exception as e:
        respond('error', {'message': f"Failed to open: {e}"})

    return tasks


def cmd_open_cli(args, tasks):
    from src.cora_parts.chat import respond
    """Open CLI popup terminal for direct CORA communication.

    Usage: cli [message]

    Opens a dedicated terminal window where CORA can type/speak in real-time.
    If a message is provided, opens the popup and displays it immediately.
    """
    try:
        from services.cli_popup import (
            open_cli_popup,
            is_cli_open,
            send_to_cli,
            cli_say
        )

        # Open the CLI popup if not already open
        if not is_cli_open():
            if open_cli_popup("C.O.R.A Terminal"):
                respond('info', {'message': "CLI terminal opened"})
            else:
                respond('error', {'message': "Failed to open CLI terminal"})
                return tasks
        else:
            respond('info', {'message': "CLI terminal already open"})

        # If message provided, send it
        if args:
            message = ' '.join(args)
            cli_say(message, emotion='neutral')

    except ImportError:
        respond('error', {'message': "CLI popup service not available"})
    except Exception as e:
        respond('error', {'message': f"CLI error: {e}"})

    return tasks
