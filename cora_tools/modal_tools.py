#!/usr/bin/env python3
"""
C.O.R.A Modal Tools
Functions for opening content in modal popup windows.

These are the tools CORA uses when the user asks to view, open, or display files,
search results, system stats, etc.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


def viewfile(path: str) -> Dict[str, Any]:
    """
    Open any file in an appropriate modal viewer.
    Auto-detects file type and uses the right modal.

    Args:
        path: Path to the file to view

    Returns:
        Dict with success status and info
    """
    path = Path(path)

    if not path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    try:
        from ui.modals import show_file_modal, show_modal_threadsafe
        show_modal_threadsafe(show_file_modal, str(path))
        return {"success": True, "path": str(path), "message": f"Opened {path.name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def viewcode(path: str, language: str = None) -> Dict[str, Any]:
    """
    Open a code file with syntax highlighting and line numbers.

    Args:
        path: Path to the code file
        language: Optional language hint (auto-detected if not provided)

    Returns:
        Dict with success status and info
    """
    path = Path(path)

    if not path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    # Auto-detect language from extension
    if not language:
        ext_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.h': 'c',
            '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php',
            '.html': 'html', '.css': 'css', '.json': 'json',
            '.yaml': 'yaml', '.yml': 'yaml', '.xml': 'xml',
            '.md': 'markdown', '.sh': 'bash', '.bat': 'batch',
            '.ps1': 'powershell', '.sql': 'sql'
        }
        language = ext_map.get(path.suffix.lower(), 'text')

    try:
        from ui.modals import show_code_modal, show_modal_threadsafe
        show_modal_threadsafe(show_code_modal, "", str(path), language, f"Code: {path.name}")
        return {"success": True, "path": str(path), "language": language}
    except Exception as e:
        return {"success": False, "error": str(e)}


def viewimage(path: str) -> Dict[str, Any]:
    """
    Display an image in a popup window.

    Args:
        path: Path to the image file

    Returns:
        Dict with success status and info
    """
    path = Path(path)

    if not path.exists():
        return {"success": False, "error": f"Image not found: {path}"}

    # Check if it's actually an image
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico'}
    if path.suffix.lower() not in valid_extensions:
        return {"success": False, "error": f"Not a valid image file: {path.suffix}"}

    try:
        from ui.modals import show_image_modal, show_modal_threadsafe
        show_modal_threadsafe(show_image_modal, str(path), f"Image: {path.name}")
        return {"success": True, "path": str(path)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def websearch(query: str) -> Dict[str, Any]:
    """
    Search the web and show results in a modal.

    Args:
        query: Search query

    Returns:
        Dict with success status and search results
    """
    if not query or not query.strip():
        return {"success": False, "error": "Empty search query"}

    try:
        from cora_tools.web import web_search
        # web_search already shows modal, just call it
        result = web_search(query)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetchurl(url: str) -> Dict[str, Any]:
    """
    Fetch a webpage and display content in a modal.

    Args:
        url: URL to fetch

    Returns:
        Dict with success status and content info
    """
    if not url or not url.strip():
        return {"success": False, "error": "Empty URL"}

    try:
        from cora_tools.web import fetch_url
        # fetch_url already shows modal, just call it
        result = fetch_url(url)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def systemstats() -> Dict[str, Any]:
    """
    Open live system stats monitor showing CPU, RAM, GPU, disk.

    Returns:
        Dict with success status
    """
    try:
        from ui.modals import show_stats_modal, show_modal_threadsafe
        show_modal_threadsafe(show_stats_modal, "System Stats")
        return {"success": True, "message": "System stats monitor opened"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def terminal(command: str) -> Dict[str, Any]:
    """
    Run a command and show output in terminal modal.

    Args:
        command: Command to execute

    Returns:
        Dict with success status and output
    """
    if not command or not command.strip():
        return {"success": False, "error": "Empty command"}

    try:
        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout if result.stdout else result.stderr
        success = result.returncode == 0

        # Show in modal
        from ui.modals import show_terminal_modal, show_modal_threadsafe
        show_modal_threadsafe(show_terminal_modal, output, command, "Terminal")

        return {
            "success": success,
            "command": command,
            "output": output,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out after 30 seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def message(text: str, msg_type: str = "info") -> Dict[str, Any]:
    """
    Show a popup message to the user.

    Args:
        text: Message to display
        msg_type: Type of message (info, warning, error, success)

    Returns:
        Dict with success status
    """
    if not text or not text.strip():
        return {"success": False, "error": "Empty message"}

    try:
        from ui.modals import show_message_modal, show_modal_threadsafe
        show_modal_threadsafe(show_message_modal, text, "CORA", msg_type)
        return {"success": True, "message": text, "type": msg_type}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Aliases for convenience
def openfile(path: str) -> Dict[str, Any]:
    """Alias for viewfile."""
    return viewfile(path)


def showfile(path: str) -> Dict[str, Any]:
    """Alias for viewfile."""
    return viewfile(path)


def opencode(path: str) -> Dict[str, Any]:
    """Alias for viewcode."""
    return viewcode(path)


def showcode(path: str) -> Dict[str, Any]:
    """Alias for viewcode."""
    return viewcode(path)


def openimage(path: str) -> Dict[str, Any]:
    """Alias for viewimage."""
    return viewimage(path)


def showimage(path: str) -> Dict[str, Any]:
    """Alias for viewimage."""
    return viewimage(path)


def search(query: str) -> Dict[str, Any]:
    """Alias for websearch."""
    return websearch(query)


def stats() -> Dict[str, Any]:
    """Alias for systemstats."""
    return systemstats()


def run(command: str) -> Dict[str, Any]:
    """Alias for terminal."""
    return terminal(command)


def alert(text: str) -> Dict[str, Any]:
    """Show an alert message."""
    return message(text, "warning")


def notify(text: str) -> Dict[str, Any]:
    """Show a notification."""
    return message(text, "info")


# Tool registry for AI to discover
MODAL_TOOLS = {
    "viewfile": viewfile,
    "viewcode": viewcode,
    "viewimage": viewimage,
    "websearch": websearch,
    "fetchurl": fetchurl,
    "systemstats": systemstats,
    "terminal": terminal,
    "message": message,
    # Aliases
    "openfile": openfile,
    "showfile": showfile,
    "opencode": opencode,
    "showcode": showcode,
    "openimage": openimage,
    "showimage": showimage,
    "search": search,
    "stats": stats,
    "run": run,
    "alert": alert,
    "notify": notify,
}


def execute_tool(tool_name: str, *args, **kwargs) -> Dict[str, Any]:
    """
    Execute a modal tool by name.

    Args:
        tool_name: Name of the tool to execute
        *args, **kwargs: Arguments to pass to the tool

    Returns:
        Tool result dict
    """
    tool_name = tool_name.lower().strip()

    if tool_name not in MODAL_TOOLS:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    try:
        return MODAL_TOOLS[tool_name](*args, **kwargs)
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_tools() -> Dict[str, str]:
    """
    List all available modal tools.

    Returns:
        Dict mapping tool names to descriptions
    """
    return {
        "viewfile": "Open any file in appropriate modal viewer",
        "viewcode": "Open code file with syntax highlighting",
        "viewimage": "Display image in popup window",
        "websearch": "Search web and show results in modal",
        "fetchurl": "Fetch webpage and display content",
        "systemstats": "Open live system stats monitor",
        "terminal": "Run command and show output",
        "message": "Show popup message to user",
    }


if __name__ == "__main__":
    print("=== Modal Tools Test ===\n")

    print("Available tools:")
    for name, desc in list_tools().items():
        print(f"  {name}: {desc}")

    print("\n=== Test Complete ===")
