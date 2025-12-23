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
        from tools.calendar import get_today_events, get_events_summary

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
        from tools.reminders import add_reminder, parse_time_string

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
        from tools.screenshots import desktop

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


@register_command("memory", aliases=["remember", "recall"])
def cmd_memory(args: str, context: Dict) -> CommandResult:
    """Access working memory."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from tools.memory import get_memory

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
