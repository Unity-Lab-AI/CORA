#!/usr/bin/env python3
"""
C.O.R.A Tool Executor
Parses user input, detects tool/command requests, and executes them.

This bridges user requests to the actual tool functions.
"""

import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Project root
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


def get_system_prompt() -> str:
    """Load system prompt."""
    path = PROJECT_DIR / 'config' / 'system_prompt.txt'
    if path.exists():
        return path.read_text(encoding='utf-8')
    return ""


def get_tools_prompt() -> str:
    """Load tools prompt."""
    path = PROJECT_DIR / 'config' / 'tools_prompt.txt'
    if path.exists():
        return path.read_text(encoding='utf-8')
    return ""


# Tool patterns - regex to detect tool requests
TOOL_PATTERNS = {
    # File viewing
    r'(?:open|show|view|display)\s+(?:file|code|image)?\s*["\']?([^"\']+)["\']?\s*(?:in\s+(?:code\s*viewer|viewer))?': 'viewfile',
    r'(?:view|open|show)\s*code\s+["\']?([^"\']+)["\']?': 'viewcode',
    r'(?:view|open|show|display)\s*image\s+["\']?([^"\']+)["\']?': 'viewimage',

    # Web
    r'(?:search|google|look\s*up|web\s*search)\s+(?:for\s+)?(.+)': 'websearch',
    r'(?:fetch|get|browse|open)\s+(?:url\s+)?(?:https?://\S+)': 'fetchurl',

    # System
    r'(?:show|open|display)?\s*(?:system\s*)?stats': 'systemstats',
    r'(?:show|open|display)?\s*hardware': 'systemstats',

    # Terminal
    r'(?:run|execute|terminal|shell|cmd)\s+(.+)': 'terminal',

    # Vision
    r'(?:take\s+)?(?:a\s+)?screenshot': 'screenshot',
    r'(?:see|look|what\s*do\s*you\s*see)': 'see',

    # Image generation
    r'(?:imagine|draw|generate|create)\s+(?:an?\s+)?(?:image\s+)?(?:of\s+)?(.+)': 'imagine',

    # Tasks
    r'(?:add|create)\s+(?:task|todo)\s+(.+)': 'add_task',
    r'(?:list|show)\s+(?:my\s+)?tasks?': 'list_tasks',

    # Time/weather
    r'(?:what\s*)?time\s*(?:is\s*it)?': 'time',
    r'(?:what\'?s?\s+the\s+)?weather': 'weather',
    r'forecast': 'weather',
}


def detect_tool(user_input: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect if user input is a tool/command request.

    Args:
        user_input: User's text input

    Returns:
        (tool_name, argument) or (None, None) if no tool detected
    """
    user_input = user_input.strip().lower()

    for pattern, tool_name in TOOL_PATTERNS.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            # Extract argument if captured
            arg = match.group(1) if match.lastindex else ""
            return (tool_name, arg.strip())

    return (None, None)


def execute_tool(tool_name: str, arg: str = "") -> Dict[str, Any]:
    """
    Execute a tool by name.

    Args:
        tool_name: Name of tool to execute
        arg: Argument to pass to tool

    Returns:
        Result dict with 'success', 'message', and optional 'data'
    """
    try:
        # Modal tools
        if tool_name in ['viewfile', 'viewcode', 'viewimage', 'websearch', 'fetchurl', 'systemstats', 'terminal', 'message']:
            from tools.modal_tools import MODAL_TOOLS
            if tool_name in MODAL_TOOLS:
                if tool_name == 'systemstats':
                    return MODAL_TOOLS[tool_name]()
                else:
                    return MODAL_TOOLS[tool_name](arg)

        # Screenshot
        if tool_name == 'screenshot':
            from tools.screenshots import desktop
            result = desktop()
            return {
                'success': result.success,
                'message': f"Screenshot saved to {result.path}" if result.success else result.error,
                'data': {'path': str(result.path)} if result.success else None
            }

        # Vision
        if tool_name == 'see':
            from voice.commands import execute_command
            result = execute_command('see', arg, {})
            return {
                'success': result.success,
                'message': result.message,
                'data': result.data
            }

        # Image generation
        if tool_name == 'imagine':
            from tools.image_gen import generate_image
            result = generate_image(arg)
            return {
                'success': result.get('success', False),
                'message': f"Generated image: {result.get('path')}" if result.get('success') else result.get('error'),
                'data': result
            }

        # Time
        if tool_name == 'time':
            from datetime import datetime
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d")
            return {
                'success': True,
                'message': f"It's {time_str} on {date_str}",
                'data': {'time': time_str, 'date': date_str}
            }

        # Weather
        if tool_name == 'weather':
            from voice.commands import execute_command
            result = execute_command('weather', '', {})
            return {
                'success': result.success,
                'message': result.message,
                'data': result.data
            }

        # Tasks
        if tool_name == 'add_task':
            from tools.tasks import add_task
            task_id = add_task(arg)
            return {
                'success': bool(task_id),
                'message': f"Added task: {arg}" if task_id else "Failed to add task",
                'data': {'id': task_id}
            }

        if tool_name == 'list_tasks':
            from tools.tasks import list_tasks
            tasks = list_tasks()
            if tasks:
                task_list = "\n".join([f"- {t.get('text', t.get('description', 'Unknown'))}" for t in tasks[:5]])
                return {
                    'success': True,
                    'message': f"Your tasks:\n{task_list}",
                    'data': {'tasks': tasks}
                }
            return {
                'success': True,
                'message': "No tasks found",
                'data': {'tasks': []}
            }

        return {
            'success': False,
            'message': f"Unknown tool: {tool_name}",
            'data': None
        }

    except Exception as e:
        return {
            'success': False,
            'message': f"Tool error: {e}",
            'data': None
        }


def process_user_input(user_input: str, ai_generate_func=None) -> str:
    """
    Process user input - execute tool if detected, otherwise use AI.

    Args:
        user_input: User's text input
        ai_generate_func: Function to call for AI response (takes prompt, returns str)

    Returns:
        Response string
    """
    # Check for tool/command
    tool_name, arg = detect_tool(user_input)

    if tool_name:
        # Execute the tool
        result = execute_tool(tool_name, arg)

        if result['success']:
            # Tool succeeded - optionally have AI comment on it
            if ai_generate_func:
                from ai.ollama import generate
                comment = generate(
                    prompt=f"You just did this: {result['message']}. Give a brief sarcastic comment about it.",
                    system=get_system_prompt(),
                    temperature=0.7,
                    max_tokens=50
                )
                if comment.content:
                    return comment.content.strip()
            return result['message']
        else:
            return result['message']

    # No tool detected - use AI chat
    if ai_generate_func:
        return ai_generate_func(user_input)

    # Fallback: try ollama directly
    try:
        from ai.ollama import generate
        response = generate(
            prompt=user_input,
            system=get_system_prompt() + "\n\n" + get_tools_prompt(),
            temperature=0.7
        )
        if response.content:
            return response.content.strip()
    except Exception as e:
        return f"Error: {e}"

    return "I don't know what to do with that."


# Convenience function for conversation callback
def chat_callback(user_input: str) -> str:
    """
    Callback function for conversation mode.
    Processes input and returns response.
    """
    return process_user_input(user_input)


if __name__ == "__main__":
    print("=== Tool Executor Test ===\n")

    test_inputs = [
        "open config.py in code viewer",
        "show me the screenshot",
        "search for python tutorials",
        "what time is it",
        "show system stats",
        "take a screenshot",
        "imagine a dark forest at night",
        "hello how are you",
    ]

    for inp in test_inputs:
        print(f"Input: {inp}")
        tool, arg = detect_tool(inp)
        if tool:
            print(f"  -> Tool: {tool}, Arg: {arg}")
        else:
            print(f"  -> No tool detected (use AI chat)")
        print()

    print("=== Test Complete ===")
