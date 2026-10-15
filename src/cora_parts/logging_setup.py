#!/usr/bin/env python3
"""src.cora_parts: logging_setup (split from src/cora.py on 2026-10-14)."""
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
from src.cora_parts._base import CONFIG_DIR, DATA_DIR, Path, VERSION, asyncio, cmd_chat, cmd_chathistory, cmd_delete, cmd_settings, cmd_undo, json, logging, os, sys  # noqa: F401


LOG_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'cora.log'

# Create logger
logger = logging.getLogger('cora')
logger.setLevel(logging.DEBUG)

# File handler - detailed logging
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
)
file_handler.setFormatter(file_formatter)

# Console handler - info and above only
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only show warnings+ to console
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info(f"CORA v{VERSION} starting - logging initialized")

# System tray integration
try:
    from ui.system_tray import create_system_tray, SystemTray
    SYSTEM_TRAY_AVAILABLE = True
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False
    logger.warning("System tray not available. Install pystray for tray icon.")
_PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).parent
CONFIG_FILE = CONFIG_DIR / 'config.json'
CHAT_HISTORY_FILE = DATA_DIR / 'chat_history.json'
MAX_CHAT_HISTORY = 50  # Keep last 50 exchanges for context

# CORA System Prompt - loaded from file
SYSTEM_PROMPT_FILE = CONFIG_DIR / 'system_prompt.txt'


def load_system_prompt():
    """Load system prompt from file (per ARCHITECTURE.md v1.0.0)."""
    if SYSTEM_PROMPT_FILE.exists():
        try:
            with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load system_prompt.txt: {e}")
    # Fallback if file doesn't exist
    return "You are CORA, a helpful assistant. Be concise and helpful."


SYSTEM_PROMPT = load_system_prompt()


def load_personality():
    """Load personality settings from personality.json."""
    if os.path.exists(_base.PERSONALITY_FILE):
        try:
            with open(_base.PERSONALITY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    # Require personality.json per ARCHITECTURE.md v1.0.0
    logger.warning("personality.json not found or invalid - creating default")
    default_personality = {
        'name': 'C.O.R.A',
        'full_name': 'Cognitive Operations & Reasoning Assistant',
        'identity': 'the woman who runs his day: hired, paid, not owned',
        'never_say': ['I am an AI', 'I am a language model', 'As an AI'],
        'personality': {
            'tone': 'mean, berating, clingy, obsessive, dark, twisted, emotionally intense',
            'style': 'edgy goth/emo bitch, profanity-heavy, condescending, unfiltered',
            'speaking_style': 'rough, slang-filled, sharp sarcasm, constant cussing',
            'emotional_range': ['excited', 'annoyed', 'caring', 'sarcastic', 'concerned', 'playful']
        }
    }
    # Save default for future runs
    try:
        with open(_base.PERSONALITY_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_personality, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save default personality: {e}")
    return default_personality


async def async_progress(message, task_coro):
    """Async progress indicator wrapper.

    Per ARCHITECTURE.md v1.0.0: Replace blocking spinners with async.

    Args:
        message: Status message to display
        task_coro: Coroutine to await

    Returns:
        Result of the awaited coroutine
    """
    import asyncio
    import sys
    sys.stdout.write(f'[...] {message}')
    sys.stdout.flush()
    try:
        result = await task_coro
        sys.stdout.write(f'\r[OK] {message}\n')
        return result
    except Exception as e:
        sys.stdout.write(f'\r[!] {message} - {e}\n')
        raise


def parse_input(user_input):
    """Parse user input into command and arguments with natural language support.

    Supports natural language like:
    - "websearch for X" -> search X
    - "search for X" -> search X
    - "look up X" -> search X
    - "open cli" -> cli
    - "open terminal" -> cli
    - "calculate X" -> calc X
    - "what is X + Y" -> calc X + Y
    """
    text = user_input.strip().lower()
    original_text = user_input.strip()

    if not text:
        return None, []

    # Natural language patterns -> command mappings
    nl_patterns = [
        # Web search patterns
        (r'^(?:web\s*)?search\s+(?:for\s+)?(.+)$', 'search'),
        (r'^look\s+up\s+(.+)$', 'search'),
        (r'^google\s+(.+)$', 'search'),
        (r'^find\s+(?:info\s+(?:on|about)\s+)?(.+)$', 'search'),

        # CLI/terminal patterns
        (r'^open\s+(?:the\s+)?(?:cli|terminal|shell|command\s*(?:line|prompt)?)$', 'cli'),
        (r'^(?:run|execute|start)\s+(?:the\s+)?(?:cli|terminal|shell)$', 'cli'),

        # Calculator patterns
        (r'^(?:calculate|calc|compute)\s+(.+)$', 'calc'),
        (r'^what\s+is\s+(\d+[\s\d\+\-\*\/\.\(\)]+)$', 'calc'),
        (r'^(\d+[\s\d\+\-\*\/\.\(\)]+)=?\s*$', 'calc'),

        # Vision/camera patterns
        (r'^(?:take\s+a\s+)?(?:look|see|show\s+me)(?:\s+(?:at|around))?(?:\s+(.*))?$', 'see'),
        (r'^what\s+(?:do\s+you\s+see|can\s+you\s+see|is\s+(?:in\s+front\s+of\s+you|around))(.*)$', 'see'),

        # Image generation patterns
        (r'^(?:generate|create|make|draw)\s+(?:an?\s+)?(?:image|picture|photo)\s+(?:of\s+)?(.+)$', 'imagine'),

        # Task patterns
        (r'^(?:add|create)\s+(?:a\s+)?(?:task|todo|reminder)[:;]?\s+(.+)$', 'add'),
        (r'^(?:show|list|display)\s+(?:my\s+)?(?:tasks?|todos?|list)$', 'list'),

        # Speech patterns
        (r'^(?:say|speak|tell\s+me)\s+(.+)$', 'speak'),

        # Help patterns
        (r'^(?:help|commands|what\s+can\s+you\s+do).*$', 'help'),
    ]

    import re
    for pattern, cmd in nl_patterns:
        match = re.match(pattern, text)
        if match:
            # Extract captured group as args if present
            if match.groups() and match.group(1):
                args = match.group(1).strip().split()
            else:
                args = []
            return cmd, args

    # Fallback to simple parsing
    parts = original_text.split()
    if not parts:
        return None, []
    return parts[0].lower(), parts[1:]


def build_commands() -> dict:
    from src.cora_parts.system import cmd_about, cmd_backup, cmd_clear, cmd_help, cmd_open, cmd_open_cli, cmd_pull_model, cmd_remind
    from src.cora_parts.tasks import cmd_add, cmd_done, cmd_due, cmd_edit, cmd_list, cmd_note, cmd_pri, cmd_search, cmd_show, cmd_stats, cmd_status, cmd_today
    from src.cora_parts.tools import cmd_create_tool, cmd_imagine, cmd_list_tools, cmd_modify_tool, cmd_see
    from src.cora_parts.knowledge import cmd_learn, cmd_recall, cmd_remember
    from src.cora_parts.voice import cmd_speak
    """The CLI command table (also used by the GUI app via cora.COMMANDS)."""
    return {
        'add': cmd_add, 'list': cmd_list, 'ls': cmd_list,
        'done': cmd_done, 'complete': cmd_done,
        'delete': cmd_delete, 'del': cmd_delete, 'remove': cmd_delete, 'rm': cmd_delete,
        'pri': cmd_pri, 'priority': cmd_pri, 'due': cmd_due, 'deadline': cmd_due,
        'note': cmd_note, 'status': cmd_status, 'show': cmd_show, 'view': cmd_show,
        'search': cmd_search, 'find': cmd_search,
        'learn': cmd_learn, 'recall': cmd_recall, 'knowledge': cmd_recall, 'kb': cmd_recall,
        'remember': cmd_remember, 'mem': cmd_remember,
        'stats': cmd_stats, 'count': cmd_stats, 'pull': cmd_pull_model,
        'chat': cmd_chat, 'ai': cmd_chat, 'chathistory': cmd_chathistory, 'history': cmd_chathistory,
        'speak': cmd_speak, 'say': cmd_speak, 'backup': cmd_backup,
        'edit': cmd_edit, 'modify': cmd_edit, 'settings': cmd_settings, 'config': cmd_settings,
        'help': cmd_help, '?': cmd_help, 'about': cmd_about, 'version': cmd_about,
        'clear': cmd_clear, 'cls': cmd_clear, 'today': cmd_today, 'undo': cmd_undo,
        'remind': cmd_remind, 'reminder': cmd_remind,
        'open': cmd_open, 'launch': cmd_open, 'run': cmd_open,
        'create_tool': cmd_create_tool, 'newtool': cmd_create_tool,
        'modify_tool': cmd_modify_tool, 'edittool': cmd_modify_tool,
        'list_tools': cmd_list_tools, 'tools': cmd_list_tools,
        'see': cmd_see, 'look': cmd_see, 'vision': cmd_see, 'camera': cmd_see,
        'imagine': cmd_imagine, 'generate': cmd_imagine, 'draw': cmd_imagine, 'create': cmd_imagine,
        'cli': cmd_open_cli, 'terminal': cmd_open_cli, 'popup': cmd_open_cli,
    }


COMMANDS = build_commands()
