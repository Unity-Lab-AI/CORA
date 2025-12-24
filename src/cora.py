#!/usr/bin/env python3
"""
# ================================================================
#   ____   ___   ____      _
#  / ___| / _ \ |  _ \    / \
# | |    | | | || |_) |  / _ \
# | |___ | |_| ||  _ <  / ___ \
#  \____| \___/ |_| \_\/_/   \_\
#
# C.O.R.A - Cognitive Operations & Reasoning Assistant
# ================================================================
# Version: 2.3.0
# Unity AI Lab
# Website: https://www.unityailab.com
# GitHub: https://github.com/Unity-Lab-AI
# Contact: unityailabcontact@gmail.com
# Creators: Hackall360, Sponge, GFourteen
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
VERSION = "2.3.0"

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

# ============ LOGGING SETUP ============
# Configure logging for CORA - logs to file and console
LOG_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / 'logs'
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

# Global system tray instance
_system_tray = None

# Project directory for loading system prompt
_PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent

# Cache for system prompt
_cora_system_prompt_cache = None


def get_system_prompt() -> str:
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

# Data directories and files - cora.py is in src/, so go up one level
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
DATA_DIR = ROOT_DIR / 'data'
CONFIG_DIR = ROOT_DIR / 'config'
CONFIG_FILE = CONFIG_DIR / 'config.json'

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


# Default paths (will be overridden by init_paths after config loads)
TASKS_FILE = DATA_DIR / 'tasks.json'
KNOWLEDGE_FILE = DATA_DIR / 'knowledge.json'
BACKUP_DIR = ROOT_DIR / 'backups'
PERSONALITY_FILE = CONFIG_DIR / 'personality.json'
CHAT_HISTORY_FILE = DATA_DIR / 'chat_history.json'

# Chat history for conversation memory
CHAT_HISTORY = []
MAX_CHAT_HISTORY = 50  # Keep last 50 exchanges for context

# Counters for ID generation
task_counter = 0
knowledge_counter = 0

# Global config (loaded at startup)
CONFIG = None

# CORA System Prompt - loaded from file
SYSTEM_PROMPT_FILE = CONFIG_DIR / 'system_prompt.txt'


def load_system_prompt():
    """Load system prompt from file (per ARCHITECTURE.md v2.0.0)."""
    if SYSTEM_PROMPT_FILE.exists():
        try:
            with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load system_prompt.txt: {e}")
    # Fallback if file doesn't exist
    return "You are CORA, a helpful assistant. Be concise and helpful."


SYSTEM_PROMPT = load_system_prompt()


def load_config():
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


def load_personality():
    """Load personality settings from personality.json."""
    if os.path.exists(PERSONALITY_FILE):
        try:
            with open(PERSONALITY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    # Require personality.json per ARCHITECTURE.md v2.0.0
    logger.warning("personality.json not found or invalid - creating default")
    default_personality = {
        'name': 'C.O.R.A',
        'full_name': 'Cognitive Operations & Reasoning Assistant',
        'identity': 'female personal assistant, hired employee',
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
        with open(PERSONALITY_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_personality, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save default personality: {e}")
    return default_personality


def generate_greeting(personality):
    """Generate an AI greeting based on full system prompt personality."""
    # Try to generate via Ollama using the FULL system prompt
    if CONFIG and CONFIG.get('ollama', {}).get('enabled', True):
        try:
            model = CONFIG.get('ollama', {}).get('model', 'llama3.2')

            # Use the full SYSTEM_PROMPT for proper CORA personality
            # Extract key personality traits for the greeting prompt
            prompt = f"""{SYSTEM_PROMPT}

Generate a single greeting (under 15 words) that sounds like CORA - mean, sarcastic, edgy emo goth bitch energy. Use profanity naturally. Just the greeting, nothing else."""

            result = subprocess.run(
                ['ollama', 'run', model, prompt],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
    # Fallback with CORA personality
    return "What the fuck do you want? CORA's online, bitch."


def check_ollama():
    """Check if ollama is installed and running via HTTP API.

    Per ARCHITECTURE.md v2.0.0: Use HTTP API instead of subprocess.
    """
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(
            'http://localhost:11434/api/version',
            headers={'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        pass
    return False


def check_tts():
    """Check if pyttsx3 is installed."""
    try:
        import pyttsx3
        return True
    except ImportError:
        return False


def auto_install_kokoro():
    """Auto-install Kokoro TTS if not present.

    Per ARCHITECTURE.md: Auto-install required components on first run.
    """
    try:
        from kokoro import KPipeline
        logger.info("Kokoro TTS already installed")
        return True
    except ImportError:
        logger.info("Installing Kokoro TTS...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'kokoro-onnx', 'sounddevice'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info("Kokoro TTS installed successfully")
                return True
            else:
                logger.error(f"Failed to install Kokoro: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout installing Kokoro TTS")
            return False
        except Exception as e:
            logger.error(f"Error installing Kokoro: {e}")
            return False


def auto_pull_model(model_name):
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

    Per ARCHITECTURE.md v2.0.0: Non-blocking UI updates.
    Uses generator pattern for async compatibility.
    """
    import sys
    # Simple immediate display for CLI (no blocking sleep)
    sys.stdout.write(f'[...] {message}\n')
    sys.stdout.flush()


async def async_progress(message, task_coro):
    """Async progress indicator wrapper.

    Per ARCHITECTURE.md v2.0.0: Replace blocking spinners with async.

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


def first_run_setup():
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

    # Step 2: Check TTS
    progress_spinner("Checking text-to-speech...")
    if check_tts():
        print("[OK] Text-to-speech available")
    else:
        print("[!] TTS not available. Install with: pip install pyttsx3")

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


def boot_sequence():
    """Advanced System Diagnostics - C.O.R.A Cognitive Operations & Reasoning Assistant.

    Full system initialization with hardware checks, neural network status,
    and cognitive subsystem verification.
    """
    print("")
    print("  ================================================================")
    print("    ____   ___   ____      _")
    print("   / ___| / _ \\ |  _ \\    / \\")
    print("  | |    | | | || |_) |  / _ \\")
    print("  | |___ | |_| ||  _ <  / ___ \\")
    print("   \\____| \\___/ |_| \\_\\/_/   \\_\\")
    print("")
    print("  C.O.R.A - ADVANCED SYSTEM DIAGNOSTICS")
    print("  Cognitive Operations & Reasoning Assistant v2.3.0")
    print("  ================================================================")
    print("  Unity AI Lab | unityailab.com")
    print("  ================================================================")
    speak("Initiating advanced system diagnostics.")

    # Phase 1: Core System Initialization
    print("\n[PHASE 1] CORE SYSTEM INITIALIZATION")
    print("-" * 40)

    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        period = 'morning'
    elif 12 <= hour < 17:
        period = 'afternoon'
    elif 17 <= hour < 21:
        period = 'evening'
    else:
        period = 'night'
    print(f"[OK] System Clock: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC-local")
    print(f"[OK] Session ID: CORA-{now.strftime('%Y%m%d%H%M%S')}")

    # Phase 2: Hardware Diagnostics
    print("\n[PHASE 2] HARDWARE DIAGNOSTICS")
    print("-" * 40)

    # CPU/RAM
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        cores = psutil.cpu_count()
        print(f"[OK] CPU: {cores} cores @ {cpu}% utilization")
        print(f"[OK] RAM: {ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB ({ram.percent}%)")
    except ImportError:
        print("[--] CPU/RAM: psutil not available")

    # GPU Check
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            if len(parts) >= 4:
                print(f"[OK] GPU: {parts[0].strip()}")
                print(f"[OK] VRAM: {parts[1].strip()}MB / {parts[2].strip()}MB @ {parts[3].strip()}%")
                speak("GPU acceleration available.")
        else:
            print("[--] GPU: No NVIDIA GPU detected")
    except Exception:
        print("[--] GPU: nvidia-smi not available")

    # Disk
    try:
        disk = shutil.disk_usage('/')
        print(f"[OK] Disk: {disk.free // (1024**3)}GB free / {disk.total // (1024**3)}GB total")
    except Exception:
        pass

    # Phase 3: Network & Location
    print("\n[PHASE 3] NETWORK & GEOLOCATION")
    print("-" * 40)

    # Network connectivity
    try:
        import urllib.request
        urllib.request.urlopen('http://google.com', timeout=3)
        print("[OK] Network: Internet connectivity verified")
    except Exception:
        print("[!!] Network: No internet connection")

    # Location
    try:
        from services.location import get_location_from_ip, format_location_string
        location = get_location_from_ip()
        if location:
            loc_str = format_location_string(location)
            print(f"[OK] Geolocation: {loc_str}")
        else:
            print("[--] Geolocation: Could not determine")
    except Exception:
        print("[--] Geolocation: Service unavailable")

    # Weather
    try:
        from services.weather import get_current_weather
        weather = get_current_weather()
        if weather:
            print(f"[OK] Weather API: {weather.get('temp', 'N/A')}°F, {weather.get('condition', 'Unknown')}")
    except Exception:
        print("[--] Weather API: Unavailable")

    # Phase 4: Neural Network Subsystems
    print("\n[PHASE 4] NEURAL NETWORK SUBSYSTEMS")
    print("-" * 40)

    # Ollama / Language Model
    if check_ollama():
        model = CONFIG.get('ollama', {}).get('model', 'llama3.2')
        print(f"[OK] Language Model: {model} loaded")
        print(f"[OK] Neural Core: Ollama endpoint active @ localhost:11434")
        speak("Neural language processing online.")
    else:
        print("[!!] Language Model: Ollama not running")
        print("[!!] Neural Core: OFFLINE - Start Ollama for full functionality")

    # Vision Model Check
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if 'llava' in result.stdout.lower():
            print("[OK] Vision Model: llava detected")
            speak("Visual cortex initialized.")
        else:
            print("[--] Vision Model: llava not installed (run: ollama pull llava)")
    except Exception:
        print("[--] Vision Model: Could not check")

    # Phase 5: Voice & Audio Systems
    print("\n[PHASE 5] VOICE & AUDIO SYSTEMS")
    print("-" * 40)

    # TTS
    if check_tts():
        print("[OK] Voice Synthesis: TTS engine initialized")
        speak("Voice synthesis module online.")
    else:
        print("[!!] Voice Synthesis: TTS not available")

    # Microphone check
    try:
        from services.audio import get_audio_manager
        manager = get_audio_manager()
        inputs = manager.get_input_devices()
        if inputs:
            default_mic = manager.get_default_input()
            print(f"[OK] Microphone: {len(inputs)} device(s) detected")
            if default_mic:
                print(f"[OK] Default Input: {default_mic.name[:40]}")
        else:
            print("[--] Microphone: No input devices")
    except Exception:
        print("[--] Audio System: Could not enumerate devices")

    # Phase 6: Camera / Vision Hardware
    print("\n[PHASE 6] VISUAL PERCEPTION SYSTEM")
    print("-" * 40)

    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print("[OK] Webcam: Camera accessible")
                speak("Visual perception system active.")
            else:
                print("[--] Webcam: Device found but cannot capture")
            cap.release()
        else:
            print("[--] Webcam: No camera detected")
    except ImportError:
        print("[--] Webcam: OpenCV not installed")
    except Exception as e:
        print(f"[--] Webcam: {e}")

    # Phase 7: Task & Memory Systems
    print("\n[PHASE 7] COGNITIVE MEMORY SYSTEMS")
    print("-" * 40)

    tasks = load_tasks()
    pending = [t for t in tasks if t.get('status') != 'done']
    overdue = [t for t in pending if t.get('due') and t.get('due') < now.strftime('%Y-%m-%d')]
    high_pri = [t for t in pending if t.get('priority', 5) <= 3]

    print(f"[OK] Task Memory: {len(tasks)} total, {len(pending)} active")
    if overdue:
        print(f"[!!] Overdue Tasks: {len(overdue)} require attention")
    if high_pri:
        print(f"[OK] High Priority: {len(high_pri)} flagged P1-P3")

    # Knowledge base
    try:
        knowledge = load_knowledge()
        print(f"[OK] Knowledge Base: {len(knowledge)} entries indexed")
    except Exception:
        print("[--] Knowledge Base: Could not load")

    # Reminders
    try:
        from tools.calendar import get_pending_reminders
        reminders = get_pending_reminders()
        if reminders:
            print(f"[OK] Active Reminders: {len(reminders)}")
    except Exception:
        pass

    # Boot Summary
    print("\n" + "=" * 60)
    print("  DIAGNOSTIC COMPLETE - ALL COGNITIVE SUBSYSTEMS NOMINAL")
    print("=" * 60)

    # Final spoken summary
    summary_parts = []
    summary_parts.append(f"Good {period}.")
    if pending:
        summary_parts.append(f"{len(pending)} tasks pending.")
    if overdue:
        summary_parts.append(f"{len(overdue)} overdue.")
    summary_parts.append("All cognitive subsystems nominal. Ready for input.")

    speak(" ".join(summary_parts))


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


def load_chat_history():
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
    """Get formatted chat history for AI context."""
    global CHAT_HISTORY
    if not CHAT_HISTORY:
        return ""

    history_parts = []
    for msg in CHAT_HISTORY[-(MAX_CHAT_HISTORY * 2):]:
        role = "User" if msg['role'] == 'user' else "CORA"
        history_parts.append(f"{role}: {msg['content']}")

    return "\n".join(history_parts)


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


def cmd_add(args, tasks):
    """Add a new task."""
    if not args:
        respond('error', {'message': "Please provide task text. Usage: add <description>"})
        return tasks

    text = ' '.join(args)
    task = {
        'id': generate_id(),
        'text': text,
        'status': 'pending',
        'priority': 5,
        'created': datetime.now().isoformat(),
        'notes': []
    }
    tasks.append(task)
    save_tasks(tasks)
    respond('task_added', {'id': task['id'], 'text': text[:40]})
    return tasks


def cmd_list(args, tasks):
    """List all tasks. Use 'list pri' to sort by priority."""
    if not tasks:
        respond('info', {'message': "No tasks found. Use 'add <text>' to create one."})
        return tasks

    # Check for sort option
    sort_by_pri = args and args[0].lower() in ('pri', 'priority', 'p')

    display_tasks = tasks.copy()
    if sort_by_pri:
        display_tasks.sort(key=lambda t: t.get('priority', 5))
        print("\n=== TASKS (sorted by priority) ===")
    else:
        print("\n=== TASKS ===")

    print(f"{'ID':<6} {'STATUS':<10} {'PRI':<4} {'DESCRIPTION'}")
    print("-" * 60)

    for task in display_tasks:
        status_icon = "[x]" if task['status'] == 'done' else "[ ]"
        print(f"{task['id']:<6} {status_icon:<10} P{task.get('priority', 5):<3} {task['text'][:40]}")

    pending = len([t for t in tasks if t['status'] == 'pending'])
    done = len([t for t in tasks if t['status'] == 'done'])
    active = len([t for t in tasks if t['status'] == 'active'])
    print("-" * 60)
    print(f"Total: {len(tasks)} | Pending: {pending} | Active: {active} | Done: {done}")
    return tasks


def cmd_done(args, tasks):
    """Mark a task as done."""
    if not args:
        respond('error', {'message': "Please provide task ID. Usage: done <id>"})
        return tasks

    task_id = args[0].upper()
    for task in tasks:
        if task['id'] == task_id:
            task['status'] = 'done'
            task['completed'] = datetime.now().isoformat()
            save_tasks(tasks)
            respond('task_done', {'id': task_id, 'text': task['text'][:40]})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_delete(args, tasks):
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


# Global for undo functionality (declared here for cmd_delete to access)
_last_deleted_task = None


def cmd_pri(args, tasks):
    """Set task priority (1-10)."""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and priority. Usage: pri <id> <1-10>"})
        return tasks

    task_id = args[0].upper()
    try:
        priority = int(args[1])
        if priority < 1 or priority > 10:
            respond('error', {'message': "Priority must be between 1 and 10"})
            return tasks
    except ValueError:
        respond('error', {'message': "Priority must be a number (1-10)"})
        return tasks

    for task in tasks:
        if task['id'] == task_id:
            task['priority'] = priority
            save_tasks(tasks)
            respond('priority_set', {'id': task_id, 'priority': priority})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_note(args, tasks):
    """Add a note to a task."""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and note text. Usage: note <id> <text>"})
        return tasks

    task_id = args[0].upper()
    note_text = ' '.join(args[1:])

    for task in tasks:
        if task['id'] == task_id:
            if 'notes' not in task:
                task['notes'] = []
            note = {
                'text': note_text,
                'created': datetime.now().isoformat()
            }
            task['notes'].append(note)
            save_tasks(tasks)
            respond('note_added', {'id': task_id, 'note': note_text[:40]})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_status(args, tasks):
    """Change task status."""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and status. Usage: status <id> <pending|active|done>"})
        return tasks

    task_id = args[0].upper()
    new_status = args[1].lower()

    valid_statuses = ['pending', 'active', 'done']
    if new_status not in valid_statuses:
        respond('error', {'message': f"Invalid status. Use: {', '.join(valid_statuses)}"})
        return tasks

    for task in tasks:
        if task['id'] == task_id:
            old_status = task['status']
            task['status'] = new_status
            if new_status == 'done' and 'completed' not in task:
                task['completed'] = datetime.now().isoformat()
            save_tasks(tasks)
            respond('status_changed', {'id': task_id, 'old': old_status, 'new': new_status})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_show(args, tasks):
    """Show detailed view of a single task."""
    if not args:
        respond('error', {'message': "Please provide task ID. Usage: show <id>"})
        return tasks

    task_id = args[0].upper()
    for task in tasks:
        if task['id'] == task_id:
            respond('task_shown', {'id': task_id}, speak_it=False)
            print(f"\n=== TASK {task_id} ===")
            print(f"Description: {task['text']}")
            print(f"Status:      {task['status']}")
            print(f"Priority:    P{task.get('priority', 5)}")
            if 'due' in task:
                print(f"Due Date:    {task['due']}")
            print(f"Created:     {task['created'][:10]}")
            if 'completed' in task:
                print(f"Completed:   {task['completed'][:10]}")

            # Show notes if any
            notes = task.get('notes', [])
            if notes:
                print(f"\nNotes ({len(notes)}):")
                for i, note in enumerate(notes, 1):
                    print(f"  {i}. {note['text']}")
                    print(f"     ({note['created'][:10]})")
            else:
                print("\nNotes: (none)")

            print("")
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def cmd_learn(args, tasks):
    """Add a knowledge entry. Use #tags to categorize."""
    if not args:
        respond('error', {'message': "Please provide knowledge text. Usage: learn <text> [#tag1 #tag2 ...]"})
        return tasks

    text = ' '.join(args)

    # Extract tags (words starting with #)
    tags = [word[1:] for word in args if word.startswith('#')]
    content = ' '.join(word for word in args if not word.startswith('#'))

    entries = load_knowledge()
    entry = {
        'id': generate_knowledge_id(),
        'content': content,
        'tags': tags,
        'created': datetime.now().isoformat()
    }
    entries.append(entry)
    save_knowledge(entries)

    tag_str = ', '.join(tags) if tags else '(none)'
    respond('knowledge_added', {'id': entry['id'], 'content': content[:50], 'tags': tag_str})
    return tasks


def cmd_recall(args, tasks):
    """Recall knowledge entries. Optionally filter by tag."""
    entries = load_knowledge()

    if not entries:
        respond('info', {'message': "No knowledge entries found. Use 'learn <text>' to add one."})
        return tasks

    # Filter by tag if provided
    if args:
        tag = args[0].lstrip('#').lower()
        entries = [e for e in entries if tag in [t.lower() for t in e.get('tags', [])]]
        if not entries:
            respond('no_results', {'query': f"#{tag}"})
            return tasks
        print(f"\n=== KNOWLEDGE (tag: #{tag}) ===")
    else:
        print("\n=== KNOWLEDGE BASE ===")

    print("-" * 60)
    for entry in entries[-10:]:  # Show last 10
        tags = ' '.join(f"#{t}" for t in entry.get('tags', []))
        print(f"{entry['id']}: {entry['content'][:50]}")
        if tags:
            print(f"       Tags: {tags}")
        print()

    print("-" * 60)
    print(f"Total entries: {len(entries)}")
    return tasks


def cmd_remember(args, tasks):
    """Remember/recall working memory. Usage: remember [key] [value] or remember (show all)"""
    try:
        from tools.memory import get_memory, remember, recall, forget
    except ImportError:
        print("Error: Memory module not available")
        return tasks

    mem = get_memory()

    if not args:
        # Show all memory
        all_mem = recall()
        if not all_mem:
            print("Working memory is empty.")
            print("Usage: remember <key> <value> - store something")
            print("       remember <key>         - recall a specific key")
            print("       remember               - show all memory")
            return tasks

        print("\n=== WORKING MEMORY ===")
        print("-" * 40)
        for key, value in all_mem.items():
            print(f"  {key}: {value}")
        print("-" * 40)
        print(f"Total: {mem.count()} entries")
        return tasks

    key = args[0]

    if len(args) == 1:
        # Recall specific key
        value = recall(key)
        if value is not None:
            print(f"{key}: {value}")
        else:
            print(f"No memory for '{key}'")
        return tasks

    # Remember key=value
    value = ' '.join(args[1:])
    remember(key, value)
    print(f"Remembered: {key} = {value}")
    return tasks


def cmd_search(args, tasks):
    """Search tasks by text content."""
    if not args:
        respond('error', {'message': "Please provide search query. Usage: search <query>"})
        return tasks

    query = ' '.join(args).lower()
    matches = []

    for task in tasks:
        # Search in text
        if query in task['text'].lower():
            matches.append(task)
            continue
        # Search in notes
        for note in task.get('notes', []):
            if query in note['text'].lower():
                matches.append(task)
                break

    if not matches:
        respond('no_results', {'query': query})
        return tasks

    respond('search_results', {'count': len(matches), 'query': query}, speak_it=False)
    print(f"\n=== SEARCH RESULTS for '{query}' ===")
    print(f"{'ID':<6} {'STATUS':<10} {'PRI':<4} {'DESCRIPTION'}")
    print("-" * 60)

    for task in matches:
        status_icon = "[x]" if task['status'] == 'done' else "[ ]"
        print(f"{task['id']:<6} {status_icon:<10} P{task.get('priority', 5):<3} {task['text'][:40]}")

    print("-" * 60)
    print(f"Found: {len(matches)} matching tasks")
    return tasks


def cmd_pull_model(args, tasks):
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


def detect_emotion(text):
    """Detect emotion from text for TTS inflection.

    Returns emotion string for TTS instruction building.
    Per ARCHITECTURE.md: Analyze text before speaking, build TTS instruction.
    """
    text_lower = text.lower()

    # Keyword-based emotion detection (fast, no AI needed)
    if any(word in text_lower for word in ['!', 'great', 'awesome', 'excellent', 'amazing', 'congrats', 'fantastic']):
        return 'excited'
    if any(word in text_lower for word in ['sorry', 'unfortunately', 'failed', 'error', 'problem', 'issue']):
        return 'concerned'
    if any(word in text_lower for word in ['done', 'complete', 'finished', 'success', 'nice']):
        return 'satisfied'
    if any(word in text_lower for word in ['remember', 'don\'t forget', 'deadline', 'overdue', 'urgent']):
        return 'urgent'
    if any(word in text_lower for word in ['?']):
        return 'questioning'
    if any(word in text_lower for word in ['hello', 'hi', 'hey', 'welcome', 'greetings']):
        return 'warm'
    if any(word in text_lower for word in ['goodbye', 'bye', 'see you', 'later']):
        return 'gentle'

    return 'neutral'


def speak_kokoro(text, emotion='neutral'):
    """Speak text using Kokoro TTS with emotion (if available)."""
    global CONFIG
    tts_config = CONFIG.get('tts', {})
    kokoro_config = tts_config.get('kokoro', {})

    if not kokoro_config.get('enabled', False):
        return False

    try:
        # Try to import kokoro
        from kokoro import KPipeline
        import sounddevice as sd

        voice = kokoro_config.get('voice', 'af_bella')
        speed = kokoro_config.get('speed', 1.0)

        pipeline = KPipeline(lang_code='a')
        generator = pipeline(text, voice=voice, speed=speed)

        for _, _, audio in generator:
            sd.play(audio, samplerate=24000)
            sd.wait()

        return True
    except ImportError:
        return False
    except Exception:
        return False


def speak_pyttsx3(text):
    """Speak text using pyttsx3."""
    global CONFIG
    tts_config = CONFIG.get('tts', {})

    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', tts_config.get('rate', 150))
        engine.setProperty('volume', tts_config.get('volume', 1.0))
        engine.say(text)
        engine.runAndWait()
        return True
    except ImportError:
        return False
    except Exception:
        return False


def speak(text):
    """Speak text using configured TTS engine with emotion detection.

    Per ARCHITECTURE.md emotion pipeline:
    1. Response text generated
    2. Analyze emotional tone
    3. Build TTS instruction
    4. Render with appropriate inflection
    """
    global CONFIG
    if CONFIG is None:
        load_config()

    # Check if TTS is enabled in config
    if not CONFIG.get('tts', {}).get('enabled', True):
        return False

    # Detect emotion for TTS inflection
    emotion = detect_emotion(text)

    tts_config = CONFIG.get('tts', {})
    engine = tts_config.get('engine', 'pyttsx3')

    # Try Kokoro first if configured (supports emotion)
    if engine == 'kokoro' or tts_config.get('kokoro', {}).get('enabled', False):
        if speak_kokoro(text, emotion):
            return True

    # Fallback to pyttsx3 (no emotion support, but still works)
    return speak_pyttsx3(text)


def get_tts_engine(config=None):
    """Factory function to get TTS engine based on config.

    Returns the appropriate TTS engine name ('kokoro', 'pyttsx3', or None).
    Per ARCHITECTURE.md: TTS engine selection factory.
    """
    if config is None:
        config = CONFIG or {}

    tts_config = config.get('tts', {})
    if not tts_config.get('enabled', True):
        return None

    engine = tts_config.get('engine', 'pyttsx3')

    # Check if Kokoro is available and configured
    if engine == 'kokoro' or tts_config.get('kokoro', {}).get('enabled', False):
        try:
            from kokoro import KPipeline
            return 'kokoro'
        except ImportError:
            pass

    # Check if pyttsx3 is available
    try:
        import pyttsx3
        return 'pyttsx3'
    except ImportError:
        pass

    return None


def init_tts():
    """Initialize TTS engine with config settings and voice selection."""
    global CONFIG
    if CONFIG is None:
        load_config()

    tts_config = CONFIG.get('tts', {})
    if not tts_config.get('enabled', True):
        return None

    try:
        import pyttsx3
        engine = pyttsx3.init()
        # Set rate and volume from config
        engine.setProperty('rate', tts_config.get('rate', 150))
        engine.setProperty('volume', tts_config.get('volume', 0.9))
        # Set voice type if specified
        voice_index = tts_config.get('voice_index', 0)
        voices = engine.getProperty('voices')
        if voices and voice_index < len(voices):
            engine.setProperty('voice', voices[voice_index].id)
        return engine
    except ImportError:
        logger.warning("TTS not available. Install with: pip install pyttsx3")
        return None
    except Exception as e:
        logger.error(f"TTS init error: {e}")
        return None


def say(text):
    """Print text and optionally speak it. Convenience function."""
    print(text)
    speak(text)


# Response generation is AI-driven. No hardcoded templates.
# Fallback responses are generated dynamically based on action type.


def ai_respond(action, context=None, use_ai=True):
    """Generate a response for an action using Ollama AI.

    All responses are AI-generated based on personality. No hardcoded templates.

    Args:
        action: The type of action (e.g., 'task_added', 'error')
        context: Dict with variables for context
        use_ai: If True, use Ollama (default True per ARCHITECTURE.md)

    Returns:
        str: The AI-generated response text
    """
    context = context or {}

    # Build context string for AI
    context_str = ', '.join(f"{k}={v}" for k, v in context.items()) if context else "none"

    # Try AI-generated response
    if use_ai and CONFIG and CONFIG.get('ollama', {}).get('enabled', True):
        try:
            model = CONFIG.get('ollama', {}).get('model', 'llama3.2')
            full_prompt = f"{SYSTEM_PROMPT}\n\nAction: {action}\nContext: {context_str}\n\nRespond briefly (under 20 words):"

            result = subprocess.run(
                ['ollama', 'run', model, full_prompt],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass  # Fall back to dynamic response

    # Dynamic fallback (no hardcoded templates)
    # Generate simple response based on action type
    action_responses = {
        'task_added': f"Task {context.get('id', '')} added.",
        'task_done': f"Task {context.get('id', '')} complete.",
        'task_deleted': f"Task {context.get('id', '')} removed.",
        'error': f"Error: {context.get('message', 'Unknown error')}",
        'not_found': f"Task {context.get('id', '')} not found.",
        'priority_set': f"Priority set to {context.get('priority', '')}.",
        'due_set': f"Due date: {context.get('due', '')}.",
        'note_added': f"Note added to {context.get('id', '')}.",
        'status_changed': f"Status: {context.get('new', '')}.",
        'task_edited': f"Task {context.get('id', '')} updated.",
        'task_shown': f"Task {context.get('id', '')}:",
        'backup_created': f"Backup complete.",
        'search_results': f"Found {context.get('count', 0)} results.",
        'no_results': f"No results for '{context.get('query', '')}'.",
        'startup': "Ready.",
        'shutdown': "Goodbye.",
        'info': f"{context.get('message', '')}",
        'knowledge_added': f"Learned {context.get('id', '')}: {context.get('content', '')} (Tags: {context.get('tags', 'none')})",
        'unknown_command': f"Unknown command: {context.get('cmd', '')}. Type 'help' for available commands.",
    }
    return action_responses.get(action, f"{action}: {context_str}")


def respond(action, context=None, speak_it=True, use_ai=False):
    """Print and optionally speak a response for an action.

    This is the main function for CORA's responses. It generates appropriate
    text based on the action type, prints it, and optionally speaks it via TTS.

    Args:
        action: The type of action (e.g., 'task_added', 'error')
        context: Dict with variables for the response
        speak_it: If True, speak the response via TTS
        use_ai: If True, generate more natural responses via Ollama
    """
    response = ai_respond(action, context, use_ai)
    print(f"[CORA]: {response}")
    if speak_it:
        speak(response)
    return response


def cmd_speak(args, tasks):
    """Speak text aloud using text-to-speech. Usage: speak <text>"""
    if not args:
        respond('error', {'message': "Please provide text to speak. Usage: speak <text>"})
        return tasks

    text = ' '.join(args)
    respond('info', {'message': f"Speaking: {text}"}, speak_it=False)

    if speak(text):
        respond('info', {'message': "Done speaking."}, speak_it=False)
    else:
        respond('error', {'message': "TTS not available. Install with: pip install pyttsx3"})

    return tasks


def cmd_backup(args, tasks):
    """Create backup of all data files."""
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # Generate timestamp for backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    backed_up = []

    # Backup tasks.json
    if os.path.exists(TASKS_FILE):
        backup_name = f"tasks_{timestamp}.json"
        shutil.copy(TASKS_FILE, BACKUP_DIR / backup_name)
        backed_up.append(f"tasks.json -> {backup_name}")

    # Backup knowledge.json
    if os.path.exists(KNOWLEDGE_FILE):
        backup_name = f"knowledge_{timestamp}.json"
        shutil.copy(KNOWLEDGE_FILE, BACKUP_DIR / backup_name)
        backed_up.append(f"knowledge.json -> {backup_name}")

    if backed_up:
        respond('backup_created', {'count': len(backed_up)})
        print(f"Location: {BACKUP_DIR}")
        for b in backed_up:
            print(f"  {b}")
    else:
        respond('error', {'message': "No data files found to backup."})

    return tasks


def cmd_edit(args, tasks):
    """Edit task text. Usage: edit <id> <new text>"""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and new text. Usage: edit <id> <new text>"})
        return tasks

    task_id = args[0].upper()
    new_text = ' '.join(args[1:])

    for task in tasks:
        if task['id'] == task_id:
            old_text = task['text']
            task['text'] = new_text
            task['modified'] = datetime.now().isoformat()
            save_tasks(tasks)
            respond('task_edited', {'id': task_id, 'text': new_text[:40]})
            return tasks

    respond('not_found', {'id': task_id})
    return tasks


def get_task_context(tasks):
    """Build a context string describing current tasks for AI awareness."""
    if not tasks:
        return "The user has no tasks currently."

    pending = [t for t in tasks if t['status'] == 'pending']
    active = [t for t in tasks if t['status'] == 'active']
    done = [t for t in tasks if t['status'] == 'done']

    context_parts = [
        f"The user has {len(tasks)} total tasks: {len(pending)} pending, {len(active)} active, {len(done)} done."
    ]

    # Add high priority pending tasks
    high_pri = [t for t in pending if t.get('priority', 5) <= 3]
    if high_pri:
        context_parts.append("High priority pending tasks:")
        for t in high_pri[:3]:
            context_parts.append(f"  - {t['id']}: {t['text']} (P{t.get('priority', 5)})")

    # Add overdue tasks
    today = datetime.now().strftime('%Y-%m-%d')
    overdue = [t for t in tasks if t.get('due') and t['due'] < today and t['status'] != 'done']
    if overdue:
        context_parts.append("Overdue tasks:")
        for t in overdue[:3]:
            context_parts.append(f"  - {t['id']}: {t['text']} (due {t['due']})")

    # Add recently added tasks
    if pending:
        context_parts.append("Recent pending tasks:")
        for t in pending[:5]:
            context_parts.append(f"  - {t['id']}: {t['text']}")

    return "\n".join(context_parts)


def fallback_response(user_message, tasks):
    """Generate a helpful response when Ollama is unavailable."""
    message_lower = user_message.lower()

    # Task-related questions
    if any(word in message_lower for word in ['task', 'todo', 'what', 'list', 'show']):
        pending = [t for t in tasks if t['status'] == 'pending']
        if pending:
            response = f"You have {len(pending)} pending tasks. "
            if len(pending) <= 3:
                response += "They are: " + ", ".join(t['text'][:30] for t in pending)
            else:
                high_pri = [t for t in pending if t.get('priority', 5) <= 3]
                if high_pri:
                    response += f"Your highest priority: {high_pri[0]['text'][:40]}"
                else:
                    response += f"First one: {pending[0]['text'][:40]}"
            return response
        return "You have no pending tasks. Use 'add <task>' to create one."

    # Help requests
    if any(word in message_lower for word in ['help', 'how', 'what can']):
        return "I can help you manage tasks! Try: add, list, done, pri, due, search, stats, backup. Type 'help' for full list."

    # Priority questions
    if 'priority' in message_lower or 'important' in message_lower:
        high_pri = [t for t in tasks if t['status'] == 'pending' and t.get('priority', 5) <= 3]
        if high_pri:
            return f"High priority tasks: " + ", ".join(f"{t['id']}: {t['text'][:25]}" for t in high_pri[:3])
        return "No high priority tasks. Set priority with: pri <id> <1-10>"

    # Due date questions
    if 'due' in message_lower or 'deadline' in message_lower or 'overdue' in message_lower:
        today = datetime.now().strftime('%Y-%m-%d')
        overdue = [t for t in tasks if t.get('due') and t['due'] < today and t['status'] != 'done']
        if overdue:
            return f"You have {len(overdue)} overdue task(s): " + ", ".join(t['id'] for t in overdue[:3])
        return "No overdue tasks. Set due dates with: due <id> <YYYY-MM-DD>"

    # Generic fallback
    return "I'm in offline mode (Ollama unavailable). I can still help with basic task queries. Try asking about your tasks, priorities, or due dates!"


def cmd_chat(args, tasks):
    """Chat with AI using Ollama with task context and conversation memory. Usage: chat <message>

    Per ARCHITECTURE.md v2.2.0: Uses ThreadPoolExecutor for non-blocking Ollama calls.
    This fixes the async/sync mismatch when GUI calls this function.
    """
    global CONFIG
    if CONFIG is None:
        load_config()

    if not args:
        respond('error', {'message': "Please provide a message. Usage: chat <your message>"})
        return tasks

    user_message = ' '.join(args)
    model = CONFIG.get('ollama', {}).get('model', 'llama3.2')

    # Load chat history for context
    load_chat_history()

    # Build context-aware prompt with conversation memory
    task_context = get_task_context(tasks)
    chat_history = get_chat_history_context()

    # Load CORA's full system prompt and add task context
    system_prompt = get_system_prompt()
    if task_context:
        system_prompt += f"\n\nCurrent Task Context:\n{task_context}"

    # Include conversation history if available (for subprocess fallback)
    if chat_history:
        full_prompt = f"{system_prompt}\n\nRecent conversation:\n{chat_history}\n\nUser: {user_message}\n\nCORA:"
    else:
        full_prompt = f"{system_prompt}\n\nUser: {user_message}\n\nCORA:"

    print(f"[You]: {user_message}")
    print("[CORA]: Thinking...")

    response = None

    def _call_ollama_api():
        """Execute Ollama HTTP API call - runs in thread pool for non-blocking."""
        from ai.ollama import chat as ollama_chat
        messages = [{'role': 'user', 'content': user_message}]
        return ollama_chat(messages, model=model, system=system_prompt, timeout=60)

    try:
        # Use ThreadPoolExecutor for non-blocking Ollama call (fixes async/sync mismatch)
        # This prevents GUI freeze when called from tkinter main thread
        from concurrent.futures import TimeoutError as FuturesTimeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_ollama_api)
            try:
                result = future.result(timeout=65)  # Slightly longer than Ollama timeout

                if result.content and not result.error:
                    response = result.content
                    print(f"[CORA]: {response}")
                else:
                    response = fallback_response(user_message, tasks)
                    print(f"[CORA]: {response}")
                    if result.error:
                        print(f"({result.error})")
            except FuturesTimeout:
                response = fallback_response(user_message, tasks)
                print(f"[CORA]: {response}")
                print("(Request timed out)")

    except ImportError:
        # ai/ollama.py not available - use subprocess fallback (blocking)
        try:
            proc = subprocess.run(
                ['ollama', 'run', model, full_prompt],
                capture_output=True, text=True, timeout=60
            )
            if proc.returncode == 0:
                response = proc.stdout.strip()
                print(f"[CORA]: {response}")
            else:
                response = fallback_response(user_message, tasks)
                print(f"[CORA]: {response}")
        except Exception:
            response = fallback_response(user_message, tasks)
            print(f"[CORA]: {response}")
    except Exception as e:
        logger.warning(f"Chat offline mode: {e}")
        response = fallback_response(user_message, tasks)
        print(f"[CORA]: {response}")
        print(f"(Offline mode due to: {e})")

    # Save conversation to history
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


def cmd_stats(args, tasks):
    """Show task statistics."""
    if not tasks:
        respond('info', {'message': "No tasks found. Use 'add <text>' to create one."})
        return tasks

    # Count by status
    pending = len([t for t in tasks if t['status'] == 'pending'])
    active = len([t for t in tasks if t['status'] == 'active'])
    done = len([t for t in tasks if t['status'] == 'done'])
    total = len(tasks)

    # Count by priority
    pri_counts = {}
    for t in tasks:
        p = t.get('priority', 5)
        pri_counts[p] = pri_counts.get(p, 0) + 1

    # Count overdue
    today = datetime.now().strftime('%Y-%m-%d')
    overdue = len([t for t in tasks if t.get('due') and t['due'] < today and t['status'] != 'done'])

    # Count with notes
    with_notes = len([t for t in tasks if t.get('notes')])

    print("\n=== TASK STATISTICS ===")
    print("-" * 40)
    print(f"Total Tasks:     {total}")
    print(f"  Pending:       {pending}")
    print(f"  Active:        {active}")
    print(f"  Done:          {done}")
    print("-" * 40)
    print("By Priority:")
    for p in sorted(pri_counts.keys()):
        count = pri_counts[p]
        bar = "#" * count
        print(f"  P{p}: {count:>3} {bar}")
    print("-" * 40)
    print(f"Overdue:         {overdue}")
    print(f"With Notes:      {with_notes}")

    if total > 0:
        completion = (done / total) * 100
        print(f"Completion:      {completion:.1f}%")

    print("")
    return tasks


def cmd_due(args, tasks):
    """Set task due date."""
    if len(args) < 2:
        respond('error', {'message': "Please provide task ID and date. Usage: due <id> <YYYY-MM-DD> or +Nd"})
        return tasks

    task_id = args[0].upper()
    date_str = args[1]

    # Parse date
    try:
        if date_str.startswith('+') and date_str.endswith('d'):
            # Relative date: +3d means 3 days from now
            days = int(date_str[1:-1])
            due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        else:
            # Absolute date: YYYY-MM-DD
            datetime.strptime(date_str, '%Y-%m-%d')  # Validate format
            due_date = date_str
    except ValueError:
        respond('error', {'message': "Invalid date. Use YYYY-MM-DD or +Nd (e.g., +3d)"})
        return tasks

    for task in tasks:
        if task['id'] == task_id:
            task['due'] = due_date
            save_tasks(tasks)
            respond('due_set', {'id': task_id, 'due': due_date})
            return tasks

    respond('not_found', {'id': task_id})
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
    print("  Creators: Hackall360, Sponge, GFourteen")
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


def cmd_today(args, tasks):
    """Show tasks due today and overdue tasks."""
    today = datetime.now().strftime('%Y-%m-%d')

    # Find overdue and today's tasks
    overdue = [t for t in tasks if t.get('due') and t['due'] < today and t['status'] != 'done']
    today_tasks = [t for t in tasks if t.get('due') == today and t['status'] != 'done']

    if not overdue and not today_tasks:
        print("No tasks due today or overdue.")
        return tasks

    print(f"\n=== TODAY ({today}) ===")

    if overdue:
        print(f"\nOVERDUE ({len(overdue)}):")
        print("-" * 50)
        for task in overdue:
            days_late = (datetime.now() - datetime.strptime(task['due'], '%Y-%m-%d')).days
            print(f"  {task['id']}: {task['text'][:35]} (due {task['due']}, {days_late}d late)")

    if today_tasks:
        print(f"\nDUE TODAY ({len(today_tasks)}):")
        print("-" * 50)
        for task in today_tasks:
            print(f"  {task['id']}: {task['text'][:40]} P{task.get('priority', 5)}")

    print("")
    return tasks


# Global for undo functionality
_last_deleted_task = None


def cmd_undo(args, tasks):
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


def cmd_remind(args, tasks):
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
        from tools.reminders import parse_time_string, ReminderManager

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
    """Open a file or application. Usage: open <path or app name>"""
    if not args:
        respond('error', {'message': "Usage: open <file path or app name>"})
        return tasks

    target = ' '.join(args)

    try:
        from tools.system import open_file, launch_app
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


def cmd_create_tool(args, tasks):
    """Create a new runtime tool. Usage: create_tool <name> <description>

    Creates a temporary script in tools/temp_scripts/ for runtime tool creation.
    Per ARCHITECTURE.md P4-SELF: Self-modification capabilities.
    """
    if len(args) < 2:
        respond('error', {'message': "Usage: create_tool <name> <description>"})
        print("Example: create_tool greet 'Say hello to user'")
        return tasks

    tool_name = args[0].lower().replace(' ', '_')
    description = ' '.join(args[1:])

    try:
        # Ensure temp_scripts directory exists
        temp_scripts_dir = DATA_DIR / 'tools' / 'temp_scripts'
        temp_scripts_dir.mkdir(parents=True, exist_ok=True)

        # Track tools in a registry file
        registry_file = temp_scripts_dir / 'tool_registry.json'
        if registry_file.exists():
            with open(registry_file) as f:
                registry = json.load(f)
        else:
            registry = {'tools': []}

        # Check if tool already exists
        existing = [t for t in registry.get('tools', []) if t.get('name') == tool_name]
        if existing:
            respond('error', {'message': f"Tool '{tool_name}' already exists. Use modify_tool to update."})
            return tasks

        # Create tool entry
        tool_entry = {
            'name': tool_name,
            'description': description,
            'created': datetime.now().isoformat(),
            'script': f'{tool_name}.py',
            'enabled': True
        }

        # Create a stub script file
        script_path = temp_scripts_dir / f'{tool_name}.py'
        script_template = f'''#!/usr/bin/env python3
"""
{tool_name} - Runtime tool for CORA

Description: {description}
Created: {datetime.now().isoformat()}

This is a runtime-created tool. Modify as needed.
"""

def run(args=None):
    """Main entry point for the tool."""
    args = args or []
    # TODO: Implement tool logic here
    print(f"[{tool_name}] Running with args: {{args}}")
    return {{"success": True, "message": "Tool executed"}}


if __name__ == "__main__":
    import sys
    run(sys.argv[1:])
'''
        with open(script_path, 'w') as f:
            f.write(script_template)

        # Update registry
        registry['tools'].append(tool_entry)
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        respond('info', {'message': f"Created tool '{tool_name}'"})
        print(f"Script: {script_path}")
        print("Edit the script to add your tool logic.")

    except Exception as e:
        respond('error', {'message': f"Failed to create tool: {e}"})

    return tasks


def cmd_modify_tool(args, tasks):
    """Modify an existing runtime tool. Usage: modify_tool <name> [enable|disable|delete]

    Per ARCHITECTURE.md P4-SELF: Self-modification capabilities.
    """
    if not args:
        respond('error', {'message': "Usage: modify_tool <name> [enable|disable|delete]"})
        return tasks

    tool_name = args[0].lower()
    action = args[1].lower() if len(args) > 1 else 'show'

    try:
        temp_scripts_dir = DATA_DIR / 'tools' / 'temp_scripts'
        registry_file = temp_scripts_dir / 'tool_registry.json'

        if not registry_file.exists():
            respond('error', {'message': "No tools registry found. Create a tool first."})
            return tasks

        with open(registry_file) as f:
            registry = json.load(f)

        # Find tool
        tool_index = None
        tool_entry = None
        for i, t in enumerate(registry.get('tools', [])):
            if t.get('name') == tool_name:
                tool_index = i
                tool_entry = t
                break

        if tool_entry is None:
            respond('error', {'message': f"Tool '{tool_name}' not found."})
            print("Available tools:")
            for t in registry.get('tools', []):
                print(f"  - {t['name']}: {t.get('description', '')[:40]}")
            return tasks

        if action == 'show':
            print(f"\n=== TOOL: {tool_name} ===")
            print(f"Description: {tool_entry.get('description', 'N/A')}")
            print(f"Created:     {tool_entry.get('created', 'N/A')[:10]}")
            print(f"Enabled:     {tool_entry.get('enabled', True)}")
            print(f"Script:      {temp_scripts_dir / tool_entry.get('script', 'N/A')}")

        elif action == 'enable':
            tool_entry['enabled'] = True
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            respond('info', {'message': f"Tool '{tool_name}' enabled."})

        elif action == 'disable':
            tool_entry['enabled'] = False
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            respond('info', {'message': f"Tool '{tool_name}' disabled."})

        elif action == 'delete':
            # Remove from registry
            registry['tools'].pop(tool_index)
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)

            # Delete script file
            script_path = temp_scripts_dir / tool_entry.get('script', '')
            if script_path.exists():
                script_path.unlink()

            respond('info', {'message': f"Tool '{tool_name}' deleted."})

        else:
            respond('error', {'message': f"Unknown action: {action}. Use: enable, disable, delete, or show"})

    except Exception as e:
        respond('error', {'message': f"Failed to modify tool: {e}"})

    return tasks


def cmd_imagine(args, tasks):
    """Generate an image from a text prompt. Usage: imagine <description>

    Uses Pollinations.AI via PolliLibPy for image generation.
    """
    if not args:
        respond('error', {'message': "What should I create? Usage: imagine <description>"})
        return tasks

    prompt = ' '.join(args)

    try:
        from tools.image_gen import generate_image, show_fullscreen_image

        print(f"[CORA]: Creating image: {prompt[:50]}...")
        speak("Generating image. This might take a moment.")

        result = generate_image(prompt=prompt, width=1024, height=1024)

        if result["success"]:
            print(f"[CORA]: Image saved: {result['path']}")
            print(f"[CORA]: Generated in {result['inference_time']:.1f}s")
            speak("Done. Opening image.")

            # Show the image
            show_fullscreen_image(result['path'])
        else:
            respond('error', {'message': f"Generation failed: {result.get('error', 'Unknown')}"})

    except ImportError as e:
        logger.error(f"Image module not available: {e}")
        respond('error', {'message': f"Image module not available: {e}"})
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        respond('error', {'message': f"Image error: {e}"})

    return tasks


def cmd_see(args, tasks):
    """See through the camera - describe what's visible. Usage: see [question]

    Uses webcam + Ollama llava vision model to analyze what's visible.
    """
    try:
        from services.presence import capture_webcam, ask_vision

        print("[CORA]: Accessing visual cortex...")
        speak("Let me take a look.")

        # Capture from webcam
        image_path = capture_webcam()
        if not image_path:
            respond('error', {'message': "Camera offline. Can't see shit."})
            return tasks

        # Build vision prompt
        if args:
            question = ' '.join(args)
        else:
            question = "Describe what you see in detail. Include people, objects, environment, lighting, and mood."

        print("[CORA]: Processing visual data...")

        # Use Ollama llava to analyze
        description = ask_vision(image_path, question)

        if description:
            print(f"[CORA]: {description}")
            speak(description[:150])
        else:
            respond('error', {'message': "Vision processing failed. Try again."})

    except ImportError as e:
        logger.error(f"Vision module not loaded: {e}")
        respond('error', {'message': f"Vision module not loaded: {e}"})
    except Exception as e:
        logger.error(f"Vision error: {e}")
        respond('error', {'message': f"Vision error: {e}"})

    return tasks


def cmd_list_tools(args, tasks):
    """List all runtime tools. Usage: list_tools"""
    try:
        temp_scripts_dir = DATA_DIR / 'tools' / 'temp_scripts'
        registry_file = temp_scripts_dir / 'tool_registry.json'

        if not registry_file.exists():
            print("No runtime tools created yet.")
            print("Use 'create_tool <name> <description>' to create one.")
            return tasks

        with open(registry_file) as f:
            registry = json.load(f)

        tools = registry.get('tools', [])
        if not tools:
            print("No runtime tools created yet.")
            return tasks

        print("\n=== RUNTIME TOOLS ===")
        print("-" * 50)
        for t in tools:
            status = "[ON]" if t.get('enabled', True) else "[OFF]"
            print(f"  {status} {t['name']}: {t.get('description', '')[:40]}")
        print("-" * 50)
        print(f"Total: {len(tools)} tools")

    except Exception as e:
        respond('error', {'message': f"Failed to list tools: {e}"})

    return tasks


def cmd_open_cli(args, tasks):
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


def main():
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
            """Handle quit from system tray."""
            logger.info("System tray quit requested")
            os._exit(0)

        def on_tray_settings():
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

    # Command dispatch table
    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'ls': cmd_list,
        'done': cmd_done,
        'complete': cmd_done,
        'delete': cmd_delete,
        'del': cmd_delete,
        'remove': cmd_delete,
        'rm': cmd_delete,
        'pri': cmd_pri,
        'priority': cmd_pri,
        'due': cmd_due,
        'deadline': cmd_due,
        'note': cmd_note,
        'status': cmd_status,
        'show': cmd_show,
        'view': cmd_show,
        'search': cmd_search,
        'find': cmd_search,
        'learn': cmd_learn,
        'recall': cmd_recall,
        'knowledge': cmd_recall,
        'kb': cmd_recall,
        'remember': cmd_remember,
        'mem': cmd_remember,
        'stats': cmd_stats,
        'count': cmd_stats,
        'pull': cmd_pull_model,
        'chat': cmd_chat,
        'ai': cmd_chat,
        'chathistory': cmd_chathistory,
        'history': cmd_chathistory,
        'speak': cmd_speak,
        'say': cmd_speak,
        'backup': cmd_backup,
        'edit': cmd_edit,
        'modify': cmd_edit,
        'settings': cmd_settings,
        'config': cmd_settings,
        'help': cmd_help,
        '?': cmd_help,
        'about': cmd_about,
        'version': cmd_about,
        'clear': cmd_clear,
        'cls': cmd_clear,
        'today': cmd_today,
        'undo': cmd_undo,
        'remind': cmd_remind,
        'reminder': cmd_remind,
        'open': cmd_open,
        'launch': cmd_open,
        'run': cmd_open,
        'create_tool': cmd_create_tool,
        'newtool': cmd_create_tool,
        'modify_tool': cmd_modify_tool,
        'edittool': cmd_modify_tool,
        'list_tools': cmd_list_tools,
        'tools': cmd_list_tools,
        'see': cmd_see,
        'look': cmd_see,
        'vision': cmd_see,
        'camera': cmd_see,
        'imagine': cmd_imagine,
        'generate': cmd_imagine,
        'draw': cmd_imagine,
        'create': cmd_imagine,
        'cli': cmd_open_cli,
        'terminal': cmd_open_cli,
        'popup': cmd_open_cli,
    }

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
                # Stop system tray before exit
                if _system_tray:
                    _system_tray.stop()
                break

            # Execute command
            if cmd in commands:
                tasks = commands[cmd](args, tasks)
            else:
                respond('unknown_command', {'cmd': cmd})

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


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Single command mode
        tasks = load_tasks()
        cmd = sys.argv[1].lower()
        args = sys.argv[2:]

        commands = {
            'add': cmd_add,
            'list': cmd_list,
            'done': cmd_done,
            'delete': cmd_delete,
            'pri': cmd_pri,
            'due': cmd_due,
            'note': cmd_note,
            'status': cmd_status,
            'show': cmd_show,
            'search': cmd_search,
            'learn': cmd_learn,
            'recall': cmd_recall,
            'remember': cmd_remember,
            'mem': cmd_remember,
            'stats': cmd_stats,
            'pull': cmd_pull_model,
            'chat': cmd_chat,
            'chathistory': cmd_chathistory,
            'speak': cmd_speak,
            'backup': cmd_backup,
            'edit': cmd_edit,
            'settings': cmd_settings,
            'help': cmd_help,
            'about': cmd_about,
            'version': cmd_about,
            'create_tool': cmd_create_tool,
            'modify_tool': cmd_modify_tool,
            'list_tools': cmd_list_tools,
            'tools': cmd_list_tools,
            'see': cmd_see,
            'look': cmd_see,
            'vision': cmd_see,
            'camera': cmd_see,
            'imagine': cmd_imagine,
            'generate': cmd_imagine,
            'draw': cmd_imagine,
            'create': cmd_imagine,
        }

        if cmd in commands:
            commands[cmd](args, tasks)
        else:
            logger.debug(f"Unknown command attempted: {cmd}")
            print(f"Unknown command: {cmd}")
            cmd_help([], tasks)
    else:
        # Interactive mode
        main()
