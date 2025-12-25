#!/usr/bin/env python3
"""
C.O.R.A Voice Commands
Command handlers for voice-triggered actions

Per ARCHITECTURE.md v2.2.0:
- cmd_calendar - show today's events
- cmd_weather - show weather
- cmd_close - close app
- cmd_tasks - show pending tasks
- cmd_remind - set reminder
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass

# Project root
PROJECT_DIR = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_DIR / 'config' / 'voice_commands.json'

# Voice command configuration (loaded from JSON)
_voice_config: Dict = {}


def load_voice_config() -> Dict:
    """Load voice command configuration from JSON file.

    Returns:
        Dict with voice command settings
    """
    global _voice_config

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                _voice_config = json.load(f)
        except Exception as e:
            print(f"[!] Error loading voice config: {e}")
            _voice_config = {'enabled': True, 'commands': {}}
    else:
        _voice_config = {'enabled': True, 'commands': {}}

    return _voice_config


def save_voice_config() -> bool:
    """Save current voice command configuration.

    Returns:
        True if saved successfully
    """
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(_voice_config, f, indent=2)
        return True
    except Exception as e:
        print(f"[!] Error saving voice config: {e}")
        return False


def get_voice_config() -> Dict:
    """Get current voice config, loading if necessary."""
    if not _voice_config:
        load_voice_config()
    return _voice_config


def is_command_enabled(name: str) -> bool:
    """Check if a command is enabled in config.

    Args:
        name: Command name

    Returns:
        True if enabled (or not configured = enabled by default)
    """
    config = get_voice_config()
    cmd_config = config.get('commands', {}).get(name, {})
    return cmd_config.get('enabled', True)


def get_wake_words() -> List[str]:
    """Get configured wake words.

    Returns:
        List of wake words
    """
    config = get_voice_config()
    return config.get('wake_words', ['cora', 'hey cora'])


def get_confidence_threshold() -> float:
    """Get voice recognition confidence threshold.

    Returns:
        Confidence threshold (0.0-1.0)
    """
    config = get_voice_config()
    return config.get('confidence_threshold', 0.7)


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    should_speak: bool = True


# Command registry
_commands: Dict[str, Callable] = {}


def register_command(name: str, aliases: List[str] = None):
    """Decorator to register a voice command.

    Args:
        name: Primary command name
        aliases: Alternative names for the command
    """
    def decorator(func: Callable):
        _commands[name.lower()] = func
        if aliases:
            for alias in aliases:
                _commands[alias.lower()] = func
        return func
    return decorator


def get_command(name: str) -> Optional[Callable]:
    """Get command handler by name.

    Args:
        name: Command name

    Returns:
        Command handler or None
    """
    return _commands.get(name.lower())


def execute_command(name: str, args: str = "", context: Dict = None) -> CommandResult:
    """Execute a voice command.

    Args:
        name: Command name
        args: Command arguments
        context: Execution context

    Returns:
        CommandResult with response
    """
    # Check if voice commands are enabled globally
    config = get_voice_config()
    if not config.get('enabled', True):
        return CommandResult(
            success=False,
            message="Voice commands are disabled",
            should_speak=False
        )

    # Check if specific command is enabled
    if not is_command_enabled(name):
        return CommandResult(
            success=False,
            message=f"Command '{name}' is disabled",
            should_speak=True
        )

    handler = get_command(name)
    if not handler:
        return CommandResult(
            success=False,
            message=f"Unknown command: {name}",
            should_speak=True
        )

    try:
        return handler(args, context or {})
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Command error: {e}",
            should_speak=True
        )


# ============ BUILT-IN COMMANDS ============

@register_command("calendar", aliases=["events", "schedule", "today"])
def cmd_calendar(args: str, context: Dict) -> CommandResult:
    """Show today's calendar events."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.calendar import get_today_events, get_events_summary

        events = get_today_events()
        summary = get_events_summary(events)

        return CommandResult(
            success=True,
            message=summary,
            data={'events': events, 'count': len(events)},
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Couldn't get calendar: {e}",
            should_speak=True
        )


@register_command("weather", aliases=["forecast", "temperature"])
def cmd_weather(args: str, context: Dict) -> CommandResult:
    """Show current weather."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from services.location import get_location
        from services.weather import get_current_weather, format_weather

        location = get_location()
        if not location:
            return CommandResult(
                success=False,
                message="Couldn't determine location",
                should_speak=True
            )

        weather = get_current_weather(location['lat'], location['lon'])
        if not weather:
            return CommandResult(
                success=False,
                message="Couldn't get weather data",
                should_speak=True
            )

        summary = format_weather(weather)
        return CommandResult(
            success=True,
            message=summary,
            data={'weather': weather, 'location': location},
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Weather error: {e}",
            should_speak=True
        )


@register_command("time", aliases=["clock", "what time"])
def cmd_time(args: str, context: Dict) -> CommandResult:
    """Tell the current time."""
    now = datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d")

    message = f"It's {time_str} on {date_str}."

    return CommandResult(
        success=True,
        message=message,
        data={'time': time_str, 'date': date_str},
        should_speak=True
    )


@register_command("tasks", aliases=["todos", "todo", "to do"])
def cmd_tasks(args: str, context: Dict) -> CommandResult:
    """Show pending tasks."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from ai.context import get_task_context, format_task_summary

        # Load tasks from file
        import json
        tasks_file = PROJECT_DIR / 'data' / 'tasks.json'

        if tasks_file.exists():
            with open(tasks_file) as f:
                data = json.load(f)
                tasks = data.get('tasks', [])
        else:
            tasks = []

        summary = format_task_summary(tasks)

        return CommandResult(
            success=True,
            message=summary,
            data={'tasks': tasks},
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Couldn't get tasks: {e}",
            should_speak=True
        )


@register_command("remind", aliases=["reminder", "remind me"])
def cmd_remind(args: str, context: Dict) -> CommandResult:
    """Set a reminder."""
    if not args:
        return CommandResult(
            success=False,
            message="What should I remind you about?",
            should_speak=True
        )

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.reminders import add_reminder, parse_time_string

        # Parse time from args
        # Format: "remind me to X in Y minutes/hours"
        # or: "remind me to X at Y:YY"

        text = args
        remind_time = None

        # Look for time indicators
        time_words = ['in', 'at', 'tomorrow', 'next']
        for word in time_words:
            if word in args.lower():
                parts = args.lower().split(word, 1)
                text = parts[0].strip()
                time_part = parts[1].strip() if len(parts) > 1 else ""
                remind_time = parse_time_string(time_part)
                break

        if not remind_time:
            remind_time = datetime.now() + timedelta(minutes=30)

        reminder_id = add_reminder(text, remind_time)

        if reminder_id:
            time_str = remind_time.strftime("%I:%M %p")
            return CommandResult(
                success=True,
                message=f"OK, I'll remind you at {time_str}.",
                data={'reminder_id': reminder_id, 'time': remind_time.isoformat()},
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message="Couldn't create reminder",
                should_speak=True
            )

    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Reminder error: {e}",
            should_speak=True
        )


@register_command("screenshot", aliases=["capture", "screen"])
def cmd_screenshot(args: str, context: Dict) -> CommandResult:
    """Take a screenshot."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.screenshots import desktop

        result = desktop()

        if result.success:
            return CommandResult(
                success=True,
                message="Screenshot saved.",
                data={'path': str(result.path), 'size': f"{result.width}x{result.height}"},
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message=f"Screenshot failed: {result.error}",
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Screenshot error: {e}",
            should_speak=True
        )


@register_command("close", aliases=["exit", "quit", "goodbye", "bye"])
def cmd_close(args: str, context: Dict) -> CommandResult:
    """Close the application."""
    return CommandResult(
        success=True,
        message="Goodbye!",
        data={'action': 'close'},
        should_speak=True
    )


@register_command("help", aliases=["commands", "what can you do"])
def cmd_help(args: str, context: Dict) -> CommandResult:
    """List available commands."""
    # Get unique commands (skip aliases)
    unique_commands = set()
    for name, func in _commands.items():
        if func.__name__ not in [f.__name__ for f in unique_commands]:
            unique_commands.add(func)

    command_list = [f.__name__.replace('cmd_', '') for f in unique_commands]
    command_str = ", ".join(sorted(command_list))

    return CommandResult(
        success=True,
        message=f"Available commands: {command_str}",
        data={'commands': list(_commands.keys())},
        should_speak=True
    )


@register_command("see", aliases=["look", "vision", "check presence"])
def cmd_see(args: str, context: Dict) -> CommandResult:
    """Check if user is present and get visual analysis."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from services.presence import check_human_present, full_human_check

        # Quick check or full analysis?
        if args and any(word in args.lower() for word in ['full', 'detail', 'analyze', 'emotion']):
            result = full_human_check()
            if result.present:
                message = f"I can see you. You appear {result.emotion or 'neutral'}."
                if result.activity:
                    message += f" You're {result.activity}."
                if result.holding:
                    message += f" I see you're holding {result.holding}."
            else:
                message = "I don't see anyone at the desk right now."
        else:
            result = check_human_present()
            if result.present:
                message = "Yes, I can see you're there."
            else:
                message = "I don't see anyone at the desk."

        return CommandResult(
            success=True,
            message=message,
            data={
                'present': result.present,
                'confidence': result.confidence,
                'emotion': result.emotion,
                'activity': result.activity,
                'posture': result.posture,
                'holding': result.holding
            },
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Vision check failed: {e}",
            should_speak=True
        )


@register_command("camera", aliases=["show camera", "open camera", "show my camera", "webcam", "live camera", "camera feed", "show webcam"])
def cmd_camera(args: str, context: Dict) -> CommandResult:
    """Open live camera feed window."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from ui.camera_feed import open_live_camera, get_live_camera

        # Check if already open
        existing = get_live_camera()
        if existing and existing.is_active():
            return CommandResult(
                success=True,
                message="Camera feed is already open.",
                should_speak=True
            )

        # Open camera
        camera = open_live_camera()
        if camera:
            return CommandResult(
                success=True,
                message="Camera feed is now open. I can see through your webcam.",
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message="Couldn't open camera. Make sure it's connected.",
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Camera error: {e}",
            should_speak=True
        )


@register_command("close camera", aliases=["stop camera", "hide camera", "camera off", "close webcam"])
def cmd_close_camera(args: str, context: Dict) -> CommandResult:
    """Close live camera feed."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from ui.camera_feed import close_live_camera, get_live_camera

        if get_live_camera():
            close_live_camera()
            return CommandResult(
                success=True,
                message="Camera feed closed.",
                should_speak=True
            )
        else:
            return CommandResult(
                success=True,
                message="Camera wasn't open.",
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Error closing camera: {e}",
            should_speak=True
        )


@register_command("what do you see", aliases=["describe what you see", "what am i doing", "how many fingers", "what is this", "look at this", "analyze camera", "camera snapshot"])
def cmd_analyze_camera(args: str, context: Dict) -> CommandResult:
    """Analyze current camera frame with AI vision."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from ui.camera_feed import get_live_camera, capture_from_live_camera, open_live_camera
        from ai.ollama import generate_with_image

        # Open camera if not already open
        camera = get_live_camera()
        if not camera or not camera.is_active():
            camera = open_live_camera()
            if not camera:
                return CommandResult(
                    success=False,
                    message="Couldn't access camera.",
                    should_speak=True
                )
            # Wait for camera to initialize
            import time
            time.sleep(1)

        # Capture frame
        frame_path = capture_from_live_camera()
        if not frame_path:
            return CommandResult(
                success=False,
                message="Couldn't capture frame from camera.",
                should_speak=True
            )

        # Build prompt based on what user asked
        prompt = "What do you see in this image? Describe in detail."
        if args:
            args_lower = args.lower()
            if "finger" in args_lower:
                prompt = "How many fingers is the person holding up? Count carefully and tell me the number."
            elif "doing" in args_lower:
                prompt = "What is the person doing right now? Describe their activity."
            elif "holding" in args_lower or "this" in args_lower:
                prompt = "What is the person holding or showing? Describe what you see."
            elif "emotion" in args_lower or "feel" in args_lower:
                prompt = "How does the person appear to be feeling? Describe their emotional state."
            else:
                prompt = f"Looking at this camera image: {args}"

        # Analyze with vision AI
        result = generate_with_image(
            prompt=prompt,
            image_path=str(frame_path),
            model="llava"
        )

        if result and result.content:
            # Clean up response
            import re
            description = result.content.strip()
            description = re.sub(r'\*\*([^*]+)\*\*', r'\1', description)
            description = re.sub(r'\*([^*]+)\*', r'\1', description)
            description = re.sub(r'\n+', ' ', description)
            description = re.sub(r'\s+', ' ', description).strip()

            return CommandResult(
                success=True,
                message=description,
                data={'image_path': str(frame_path)},
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message="I couldn't analyze the image.",
                should_speak=True
            )

    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Vision analysis failed: {e}",
            should_speak=True
        )


@register_command("viewfile", aliases=["openfile", "showfile", "open file", "show file", "view file"])
def cmd_viewfile(args: str, context: Dict) -> CommandResult:
    """Open a file in modal viewer."""
    if not args:
        return CommandResult(
            success=False,
            message="What file should I open?",
            should_speak=True
        )

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.modal_tools import viewfile

        result = viewfile(args.strip())

        if result.get('success'):
            return CommandResult(
                success=True,
                message=f"Opened {Path(args).name}",
                data=result,
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message=result.get('error', 'Failed to open file'),
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Error opening file: {e}",
            should_speak=True
        )


@register_command("viewcode", aliases=["opencode", "showcode", "open code", "show code", "view code"])
def cmd_viewcode(args: str, context: Dict) -> CommandResult:
    """Open a code file with syntax highlighting."""
    if not args:
        return CommandResult(
            success=False,
            message="What code file should I open?",
            should_speak=True
        )

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.modal_tools import viewcode

        result = viewcode(args.strip())

        if result.get('success'):
            return CommandResult(
                success=True,
                message=f"Opened {Path(args).name} in code viewer",
                data=result,
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message=result.get('error', 'Failed to open code file'),
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Error opening code: {e}",
            should_speak=True
        )


@register_command("viewimage", aliases=["openimage", "showimage", "open image", "show image", "display image"])
def cmd_viewimage(args: str, context: Dict) -> CommandResult:
    """Display an image in popup window."""
    if not args:
        return CommandResult(
            success=False,
            message="What image should I show?",
            should_speak=True
        )

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.modal_tools import viewimage

        result = viewimage(args.strip())

        if result.get('success'):
            return CommandResult(
                success=True,
                message=f"Showing {Path(args).name}",
                data=result,
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message=result.get('error', 'Failed to show image'),
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Error showing image: {e}",
            should_speak=True
        )


@register_command("websearch", aliases=["search", "web search", "google", "look up"])
def cmd_websearch(args: str, context: Dict) -> CommandResult:
    """Search the web and show results in modal."""
    if not args:
        return CommandResult(
            success=False,
            message="What should I search for?",
            should_speak=True
        )

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.modal_tools import websearch

        result = websearch(args.strip())

        if result.get('success'):
            count = result.get('count', 0)
            return CommandResult(
                success=True,
                message=f"Found {count} results for {args}",
                data=result,
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message=result.get('error', 'Search failed'),
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Search error: {e}",
            should_speak=True
        )


@register_command("fetchurl", aliases=["fetch", "get url", "open url", "browse"])
def cmd_fetchurl(args: str, context: Dict) -> CommandResult:
    """Fetch a webpage and display content."""
    if not args:
        return CommandResult(
            success=False,
            message="What URL should I fetch?",
            should_speak=True
        )

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.modal_tools import fetchurl

        result = fetchurl(args.strip())

        if result.get('success'):
            return CommandResult(
                success=True,
                message=f"Fetched {args}",
                data=result,
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message=result.get('error', 'Failed to fetch URL'),
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Fetch error: {e}",
            should_speak=True
        )


@register_command("systemstats", aliases=["stats", "system stats", "hardware", "show stats"])
def cmd_systemstats(args: str, context: Dict) -> CommandResult:
    """Open live system stats monitor."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.modal_tools import systemstats

        result = systemstats()

        if result.get('success'):
            return CommandResult(
                success=True,
                message="Opening system stats monitor",
                data=result,
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message=result.get('error', 'Failed to open stats'),
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Stats error: {e}",
            should_speak=True
        )


@register_command("terminal", aliases=["run", "execute", "shell", "cmd"])
def cmd_terminal(args: str, context: Dict) -> CommandResult:
    """Run a command and show output in terminal modal."""
    if not args:
        return CommandResult(
            success=False,
            message="What command should I run?",
            should_speak=True
        )

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.modal_tools import terminal

        result = terminal(args.strip())

        if result.get('success'):
            return CommandResult(
                success=True,
                message=f"Command executed",
                data=result,
                should_speak=True
            )
        else:
            return CommandResult(
                success=False,
                message=result.get('error', 'Command failed'),
                should_speak=True
            )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Terminal error: {e}",
            should_speak=True
        )


@register_command("memory", aliases=["remember", "recall"])
def cmd_memory(args: str, context: Dict) -> CommandResult:
    """Access working memory."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.memory import get_memory

        mem = get_memory()

        if not args:
            # Show all memory
            all_mem = mem.recall()
            if all_mem:
                items = [f"{k}: {v}" for k, v in list(all_mem.items())[:5]]
                message = "I remember: " + "; ".join(items)
            else:
                message = "My memory is empty."
            return CommandResult(success=True, message=message)

        # Check for "remember X is Y"
        if " is " in args:
            parts = args.split(" is ", 1)
            key = parts[0].strip()
            value = parts[1].strip()
            mem.remember(key, value)
            return CommandResult(
                success=True,
                message=f"OK, I'll remember that {key} is {value}."
            )

        # Recall specific key
        value = mem.recall(args.strip())
        if value:
            return CommandResult(
                success=True,
                message=f"{args.strip()} is {value}."
            )
        else:
            return CommandResult(
                success=False,
                message=f"I don't remember anything about {args.strip()}."
            )

    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Memory error: {e}"
        )


# ============ MEDIA CONTROL COMMANDS ============

@register_command("play", aliases=["play music", "play video", "play song"])
def cmd_play(args: str, context: Dict) -> CommandResult:
    """Play media - file, YouTube URL, or search query."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import play, get_media

        if not args:
            # Toggle play/pause
            result = get_media().play()
            return CommandResult(
                success=result['success'],
                message="Toggled play/pause" if result['success'] else "Media control failed",
                should_speak=True
            )

        # Play specific target
        msg = play(args.strip())
        success = msg.startswith("[+]")
        return CommandResult(
            success=success,
            message=msg.replace("[+] ", "").replace("[!] ", ""),
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Media error: {e}",
            should_speak=True
        )


@register_command("pause", aliases=["pause music", "pause video"])
def cmd_pause(args: str, context: Dict) -> CommandResult:
    """Pause current media playback."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import pause

        msg = pause()
        success = msg.startswith("[+]")
        return CommandResult(
            success=success,
            message="Paused" if success else "Failed to pause",
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Pause error: {e}",
            should_speak=True
        )


@register_command("resume", aliases=["unpause", "continue playing"])
def cmd_resume(args: str, context: Dict) -> CommandResult:
    """Resume media playback."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import resume

        msg = resume()
        success = msg.startswith("[+]")
        return CommandResult(
            success=success,
            message="Resumed" if success else "Failed to resume",
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Resume error: {e}",
            should_speak=True
        )


@register_command("stop", aliases=["stop music", "stop video", "stop playing"])
def cmd_stop(args: str, context: Dict) -> CommandResult:
    """Stop media playback."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import stop

        msg = stop()
        success = msg.startswith("[+]")
        return CommandResult(
            success=success,
            message="Stopped" if success else "Failed to stop",
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Stop error: {e}",
            should_speak=True
        )


@register_command("next", aliases=["next track", "next song", "skip"])
def cmd_next(args: str, context: Dict) -> CommandResult:
    """Skip to next track."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import next_track

        msg = next_track()
        success = msg.startswith("[+]")
        return CommandResult(
            success=success,
            message="Next track" if success else "Failed to skip",
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Next error: {e}",
            should_speak=True
        )


@register_command("previous", aliases=["prev", "previous track", "previous song", "go back"])
def cmd_prev(args: str, context: Dict) -> CommandResult:
    """Go to previous track."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import prev_track

        msg = prev_track()
        success = msg.startswith("[+]")
        return CommandResult(
            success=success,
            message="Previous track" if success else "Failed",
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Previous error: {e}",
            should_speak=True
        )


@register_command("volume", aliases=["set volume", "volume level"])
def cmd_volume(args: str, context: Dict) -> CommandResult:
    """Get or set volume (0-100)."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import volume

        if args:
            # Try to parse volume level
            try:
                level = int(args.strip().replace("%", ""))
                level = max(0, min(100, level))  # Clamp to 0-100
                msg = volume(level)
            except ValueError:
                return CommandResult(
                    success=False,
                    message=f"Invalid volume level: {args}",
                    should_speak=True
                )
        else:
            msg = volume()

        success = msg.startswith("[+]")
        return CommandResult(
            success=success,
            message=msg.replace("[+] ", "").replace("[!] ", ""),
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Volume error: {e}",
            should_speak=True
        )


@register_command("mute", aliases=["unmute", "toggle mute"])
def cmd_mute(args: str, context: Dict) -> CommandResult:
    """Toggle mute."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import mute

        msg = mute()
        success = msg.startswith("[+]")
        return CommandResult(
            success=success,
            message="Mute toggled" if success else "Failed to toggle mute",
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Mute error: {e}",
            should_speak=True
        )


@register_command("now playing", aliases=["what's playing", "whats playing", "current song"])
def cmd_now_playing(args: str, context: Dict) -> CommandResult:
    """Get what's currently playing."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.media import now

        msg = now()
        return CommandResult(
            success=True,
            message=msg,
            should_speak=True
        )
    except Exception as e:
        return CommandResult(
            success=False,
            message=f"Now playing error: {e}",
            should_speak=True
        )


# ==================== GIT & GITHUB COMMANDS ====================

@register_command("git status", aliases=["git stat", "repo status"])
def cmd_git_status(args: str, context: Dict) -> CommandResult:
    """Show git repository status."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_status

        result = git_status()
        if result['success']:
            return CommandResult(
                success=True,
                message=result.get('status', 'Repository is clean'),
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Git error'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Git error: {e}", should_speak=True)


@register_command("git pull", aliases=["pull changes", "pull from remote"])
def cmd_git_pull(args: str, context: Dict) -> CommandResult:
    """Pull latest changes from remote."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_pull

        result = git_pull()
        if result['success']:
            return CommandResult(
                success=True,
                message=f"Pulled changes. {result.get('output', 'Up to date')}",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Pull failed'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Pull error: {e}", should_speak=True)


@register_command("git push", aliases=["push changes", "push to remote"])
def cmd_git_push(args: str, context: Dict) -> CommandResult:
    """Push commits to remote."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_push

        result = git_push()
        if result['success']:
            return CommandResult(
                success=True,
                message=f"Pushed to remote. {result.get('message', '')}",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Push failed'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Push error: {e}", should_speak=True)


@register_command("git commit", aliases=["commit changes"])
def cmd_git_commit(args: str, context: Dict) -> CommandResult:
    """Commit staged changes with a message."""
    if not args:
        return CommandResult(success=False, message="Need a commit message", should_speak=True)

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_commit

        result = git_commit(args)
        if result['success']:
            return CommandResult(
                success=True,
                message=f"Committed: {args[:40]}",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Commit failed'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Commit error: {e}", should_speak=True)


@register_command("git add", aliases=["stage files", "add files"])
def cmd_git_add(args: str, context: Dict) -> CommandResult:
    """Stage files for commit."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_add

        files = args if args else '.'
        result = git_add(files)
        if result['success']:
            return CommandResult(
                success=True,
                message=f"Staged: {files}",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Add failed'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Add error: {e}", should_speak=True)


@register_command("git branch", aliases=["list branches", "show branches"])
def cmd_git_branch(args: str, context: Dict) -> CommandResult:
    """List all branches."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_branch

        result = git_branch()
        if result['success']:
            current = result.get('current', 'unknown')
            return CommandResult(
                success=True,
                message=f"On branch: {current}",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Branch error'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Branch error: {e}", should_speak=True)


@register_command("git checkout", aliases=["switch branch", "change branch"])
def cmd_git_checkout(args: str, context: Dict) -> CommandResult:
    """Switch to a branch."""
    if not args:
        return CommandResult(success=False, message="Need a branch name", should_speak=True)

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import get_git

        git = get_git()
        # Check for -b flag for new branch
        if args.startswith('-b '):
            branch = args[3:].strip()
            result = git.checkout_new(branch)
        else:
            result = git.checkout(args)

        if result['success']:
            return CommandResult(
                success=True,
                message=result.get('message', f'Switched to {args}'),
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Checkout failed'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Checkout error: {e}", should_speak=True)


@register_command("git merge", aliases=["merge branch"])
def cmd_git_merge(args: str, context: Dict) -> CommandResult:
    """Merge a branch into current branch."""
    if not args:
        return CommandResult(success=False, message="Need a branch name to merge", should_speak=True)

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_merge

        result = git_merge(args)
        if result['success']:
            return CommandResult(
                success=True,
                message=f"Merged {args}",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Merge failed'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Merge error: {e}", should_speak=True)


@register_command("git clone", aliases=["clone repo", "clone repository"])
def cmd_git_clone(args: str, context: Dict) -> CommandResult:
    """Clone a repository."""
    if not args:
        return CommandResult(success=False, message="Need a repository URL", should_speak=True)

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_clone

        result = git_clone(args)
        if result['success']:
            return CommandResult(
                success=True,
                message=f"Cloned repository",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Clone failed'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Clone error: {e}", should_speak=True)


@register_command("git log", aliases=["commit history", "show commits"])
def cmd_git_log(args: str, context: Dict) -> CommandResult:
    """Show recent commits."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import git_log

        count = int(args) if args and args.isdigit() else 5
        result = git_log(count)
        if result['success']:
            commits = result.get('commits', [])
            return CommandResult(
                success=True,
                message=f"Found {len(commits)} recent commits",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Log error'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Log error: {e}", should_speak=True)


@register_command("github login", aliases=["login github", "github auth", "authenticate github"])
def cmd_github_login(args: str, context: Dict) -> CommandResult:
    """Login to GitHub (opens browser for token creation)."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import github_login_browser, github_login

        if args:
            # Token provided directly
            result = github_login(args)
            if result['success']:
                return CommandResult(
                    success=True,
                    message=f"Logged in as {result.get('username', 'unknown')}",
                    should_speak=True
                )
            return CommandResult(success=False, message=result.get('error', 'Login failed'), should_speak=True)
        else:
            # Open browser
            result = github_login_browser()
            return CommandResult(
                success=True,
                message="Opening browser for GitHub authentication. Create a token and tell me the token to complete login.",
                should_speak=True
            )
    except Exception as e:
        return CommandResult(success=False, message=f"Login error: {e}", should_speak=True)


@register_command("github repos", aliases=["my repos", "list repos", "show repositories"])
def cmd_github_repos(args: str, context: Dict) -> CommandResult:
    """List your GitHub repositories."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import github_repos

        result = github_repos()
        if result['success']:
            count = result.get('count', 0)
            return CommandResult(
                success=True,
                message=f"Found {count} repositories",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Could not list repos'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Repos error: {e}", should_speak=True)


@register_command("github create", aliases=["create repo", "new repo", "create repository"])
def cmd_github_create(args: str, context: Dict) -> CommandResult:
    """Create a new GitHub repository."""
    if not args:
        return CommandResult(success=False, message="Need a repository name", should_speak=True)

    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from cora_tools.git_ops import github_create_repo

        # Parse args: name [description] [--private]
        private = '--private' in args
        args = args.replace('--private', '').strip()
        parts = args.split(' ', 1)
        name = parts[0]
        description = parts[1] if len(parts) > 1 else ''

        result = github_create_repo(name, description, private)
        if result['success']:
            return CommandResult(
                success=True,
                message=f"Created repository: {result.get('full_name', name)}",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Create failed'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Create error: {e}", should_speak=True)


# ============ EMAIL COMMANDS ============

@register_command("send email", aliases=["email", "send message", "message"])
def handle_send_email(args: str = "") -> CommandResult:
    """Send an email using default mail app."""
    try:
        from cora_tools.email_tool import parse_email_command, send_email

        # Parse natural language command
        parsed = parse_email_command(f"send email {args}" if not args.startswith("to ") else f"send email to {args}")

        if not parsed.get('success'):
            # Try simpler parsing: "email karen saying hi"
            parsed = parse_email_command(f"email {args}")

        if parsed.get('success'):
            result = send_email(parsed['to'], parsed['message'])
            if result['success']:
                return CommandResult(
                    success=True,
                    message=f"Opening email to {parsed['to']}",
                    should_speak=True
                )
            else:
                hint = result.get('hint', '')
                return CommandResult(
                    success=False,
                    message=result.get('error', 'Email failed') + (f". {hint}" if hint else ""),
                    should_speak=True
                )
        else:
            return CommandResult(
                success=False,
                message="Tell me who to email and what to say. Like: email Karen saying hello",
                should_speak=True
            )
    except Exception as e:
        return CommandResult(success=False, message=f"Email error: {e}", should_speak=True)


@register_command("check email", aliases=["read email", "read emails", "check emails", "open email", "open inbox", "inbox"])
def handle_check_email(args: str = "") -> CommandResult:
    """Open email inbox in default mail app."""
    try:
        from cora_tools.email_tool import read_emails

        result = read_emails()
        if result['success']:
            return CommandResult(
                success=True,
                message="Opening your email inbox",
                should_speak=True
            )
        return CommandResult(success=False, message=result.get('error', 'Could not open email'), should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Email error: {e}", should_speak=True)


@register_command("add contact", aliases=["save contact", "new contact"])
def handle_add_contact(args: str = "") -> CommandResult:
    """Add a contact to the address book."""
    try:
        from cora_tools.email_tool import add_contact

        # Parse: "add contact karen karen@email.com" or "karen is karen@email.com"
        parts = args.strip().split()
        if len(parts) >= 2:
            # Last part should be email
            email = parts[-1]
            name = ' '.join(parts[:-1])

            if '@' in email:
                result = add_contact(name, email)
                if result['success']:
                    return CommandResult(
                        success=True,
                        message=f"Added {name} to contacts",
                        should_speak=True
                    )
                return CommandResult(success=False, message=result.get('error', 'Failed to add contact'), should_speak=True)

        return CommandResult(
            success=False,
            message="Tell me the name and email. Like: add contact Karen karen@email.com",
            should_speak=True
        )
    except Exception as e:
        return CommandResult(success=False, message=f"Contact error: {e}", should_speak=True)


@register_command("list contacts", aliases=["show contacts", "my contacts", "contacts"])
def handle_list_contacts(args: str = "") -> CommandResult:
    """List saved email contacts."""
    try:
        from cora_tools.email_tool import list_contacts

        result = list_contacts()
        if result['count'] > 0:
            names = ', '.join(result['contacts'].keys())
            return CommandResult(
                success=True,
                message=f"You have {result['count']} contacts: {names}",
                data=result['contacts'],
                should_speak=True
            )
        return CommandResult(
            success=True,
            message="No contacts saved yet. Add one with: add contact name email",
            should_speak=True
        )
    except Exception as e:
        return CommandResult(success=False, message=f"Contacts error: {e}", should_speak=True)


# ============ HEARING/TRANSCRIPT COMMANDS ============

@register_command("what did you hear", aliases=["what did i say", "what did i just say", "what was that", "repeat that", "what did you just hear"])
def handle_what_did_you_hear(args: str = "") -> CommandResult:
    """Tell user what was heard before the wake word."""
    try:
        from voice.stt import WakeWordDetector

        last_heard = WakeWordDetector.get_last_heard()

        if last_heard:
            return CommandResult(
                success=True,
                message=f"Before you said my name, I heard: {last_heard}",
                should_speak=True
            )
        else:
            return CommandResult(
                success=True,
                message="I didn't catch anything before you called me. Maybe it was too quiet or I wasn't picking it up clearly.",
                should_speak=True
            )
    except Exception as e:
        return CommandResult(success=False, message=f"Couldn't check transcript: {e}", should_speak=True)


@register_command("be more chatty", aliases=["talk more", "be more involved", "be active", "friend mode"])
def handle_be_more_chatty(args: str = "") -> CommandResult:
    """Increase CORA's ambient interjection frequency."""
    try:
        from voice.ambient_awareness import get_ambient_awareness

        ambient = get_ambient_awareness()
        new_threshold = min(1.0, ambient.friend_threshold + 0.2)
        ambient.set_friend_threshold(new_threshold)

        if new_threshold >= 0.8:
            msg = "Alright, I'll be more chatty. I'll chime in more often like a close friend would."
        elif new_threshold >= 0.5:
            msg = "Got it, I'll be more involved in what's going on. I'll speak up when I notice things."
        else:
            msg = "I'll try to be a bit more active. Let me know if you want me even more involved."

        return CommandResult(success=True, message=msg, should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Couldn't adjust: {e}", should_speak=True)


@register_command("be quiet", aliases=["be less chatty", "talk less", "quiet mode", "shut up", "give me space", "leave me alone"])
def handle_be_quiet(args: str = "") -> CommandResult:
    """Decrease CORA's ambient interjection frequency."""
    try:
        from voice.ambient_awareness import get_ambient_awareness

        ambient = get_ambient_awareness()
        new_threshold = max(0.0, ambient.friend_threshold - 0.3)
        ambient.set_friend_threshold(new_threshold)

        if new_threshold <= 0.1:
            msg = "Okay, I'll stay quiet unless you call me. Just say my name if you need me."
        elif new_threshold <= 0.3:
            msg = "Alright, I'll tone it down. I'll only speak up if something seems important."
        else:
            msg = "Got it, I'll give you more space. I'm still here if you need me though."

        return CommandResult(success=True, message=msg, should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Couldn't adjust: {e}", should_speak=True)


@register_command("how aware are you", aliases=["awareness level", "friend threshold", "how chatty are you"])
def handle_awareness_level(args: str = "") -> CommandResult:
    """Check CORA's current ambient awareness level."""
    try:
        from voice.ambient_awareness import get_ambient_awareness

        ambient = get_ambient_awareness()
        status = ambient.get_status()
        threshold = status['friend_threshold']
        interjections = status['interjection_count']

        if threshold >= 0.8:
            level = "very chatty, like a close friend"
        elif threshold >= 0.5:
            level = "moderately involved, chiming in occasionally"
        elif threshold >= 0.3:
            level = "pretty quiet, only speaking up for important stuff"
        else:
            level = "very quiet, mostly waiting for you to call me"

        msg = f"My friend threshold is at {threshold:.0%}. I'm {level}. I've interjected {interjections} times this session."

        return CommandResult(success=True, message=msg, should_speak=True)
    except Exception as e:
        return CommandResult(success=False, message=f"Couldn't check: {e}", should_speak=True)


def list_commands() -> List[str]:
    """Get list of all registered commands.

    Returns:
        List of command names
    """
    return list(_commands.keys())


def parse_voice_input(text: str) -> tuple:
    """Parse voice input into command and args.

    Args:
        text: Raw voice input

    Returns:
        (command_name, args) tuple
    """
    text = text.lower().strip()

    # Remove wake word if present (use configured wake words)
    wake_words = get_wake_words()
    for wake in wake_words:
        if text.startswith(wake):
            text = text[len(wake):].strip()
            break

    # Try to match a command (only enabled ones)
    for cmd_name in sorted(_commands.keys(), key=len, reverse=True):
        if text.startswith(cmd_name) and is_command_enabled(cmd_name):
            args = text[len(cmd_name):].strip()
            return (cmd_name, args)

    # No command found - return as query
    return (None, text)


if __name__ == "__main__":
    print("=== VOICE COMMANDS TEST ===")

    print("\nRegistered commands:")
    for name in sorted(set(f.__name__ for f in _commands.values())):
        print(f"  - {name.replace('cmd_', '')}")

    print("\n--- Testing commands ---")

    # Test time
    result = execute_command("time")
    print(f"\ntime: {result.message}")

    # Test calendar
    result = execute_command("calendar")
    print(f"calendar: {result.message}")

    # Test help
    result = execute_command("help")
    print(f"help: {result.message}")

    # Test parse
    print("\n--- Parsing test ---")
    test_inputs = [
        "what time is it",
        "cora show my calendar",
        "remind me to check email in 30 minutes",
        "take a screenshot"
    ]

    for inp in test_inputs:
        cmd, args = parse_voice_input(inp)
        print(f"'{inp}' -> cmd={cmd}, args='{args}'")
