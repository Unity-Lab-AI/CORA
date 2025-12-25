"""
C.O.R.A Tools Module
Utilities for TTS, file ops, AI, system integration, and more.

Usage:
    from tools import speak_async, remember, recall, take_screenshot
    from tools.files import read_file, write_json
    from tools.system import get_system_info
"""

# TTS Handler - Speech synthesis
from .tts_handler import TTSHandler, TTSManager, speak_async

# Memory - Working memory for context
from .memory import Memory, get_memory, remember, recall, forget, remember_context, recall_context

# Files - File operations
from .files import (
    create_file, read_file, append_file, delete_file,
    move_file, copy_file, rename_file, get_file_info,
    list_directory, create_directory, delete_directory,
    read_json, write_json, search_in_file, get_recent_files
)

# System - System utilities
from .system import (
    get_system_info, launch_app, open_file, open_folder,
    search_files, get_running_processes, kill_process,
    get_gpu_info, get_memory_usage, set_volume,
    notify, clipboard_paste, clipboard_copy,
    take_screenshot, calculate, run_shell
)

# Calendar - Events and reminders
from .calendar import (
    add_event, get_event, delete_event,
    get_today_events, get_upcoming, get_events_on_date,
    remind_me, get_pending_reminders
)

# Reminders - Reminder management
from .reminders import ReminderManager, parse_time_string

# Screenshots - Screen capture
from .screenshots import (
    desktop as screenshot_desktop,
    window as screenshot_window,
    region as screenshot_region,
    list_windows, quick_screenshot,
    get_screenshot_dir, set_screenshot_dir
)

# AI Tools - Ollama integration
from .ai_tools import (
    check_ollama, list_models, pull_model,
    chat as ai_chat, generate_code, explain_code
)

# Code - Code analysis and execution
from .code import (
    CodeAssistant, CodeResult, CodeAnalysis,
    get_code_assistant, write_code, fix_code,
    run_code, analyze_code, detect_language
)

# Image Generation
from .image_gen import generate_image, show_fullscreen_image, get_recent_images

# Browser Control
from .browser import BrowserController, browse_sync, search_and_screenshot

# Web Tools
from .web import (
    fetch as web_fetch,
    search as web_search,
    web_search as web_search_detailed,
    fetch_url, summarize_url
)

# Email
from .email_tool import send_email, read_emails, add_contact, list_contacts, parse_email_command

# Media Control
from .media import EmbyControl, play as media_play, pause as media_pause, now as media_now

# Windows Control
from .windows import (
    list_windows as get_windows,
    focus_window, minimize_window, maximize_window as maximize_win,
    close_window, arrange_windows
)

# Self-Modify - Script creation and execution
from .self_modify import (
    create_script, run_script, delete_script,
    list_scripts, cleanup_scripts, create_and_run,
    get_script_content
)

# Tasks - Task management
from .tasks import TaskManager, add_task, list_tasks, complete_task, delete_task

__all__ = [
    # TTS
    "TTSHandler", "TTSManager", "speak_async",
    # Memory
    "Memory", "get_memory", "remember", "recall", "forget",
    "remember_context", "recall_context",
    # Files
    "create_file", "read_file", "append_file", "delete_file",
    "move_file", "copy_file", "rename_file", "get_file_info",
    "list_directory", "create_directory", "delete_directory",
    "read_json", "write_json", "search_in_file", "get_recent_files",
    # System
    "get_system_info", "launch_app", "open_file", "open_folder",
    "search_files", "get_running_processes", "kill_process",
    "get_gpu_info", "get_memory_usage", "set_volume",
    "notify", "clipboard_paste", "clipboard_copy",
    "take_screenshot", "calculate", "run_shell",
    # Calendar
    "add_event", "get_event", "delete_event",
    "get_today_events", "get_upcoming", "get_events_on_date",
    "remind_me", "get_pending_reminders",
    # Reminders
    "ReminderManager", "parse_time_string",
    # Screenshots
    "screenshot_desktop", "screenshot_window", "screenshot_region",
    "list_windows", "quick_screenshot",
    "get_screenshot_dir", "set_screenshot_dir",
    # AI Tools
    "check_ollama", "list_models", "pull_model",
    "ai_chat", "generate_code", "explain_code",
    # Code
    "CodeAssistant", "CodeResult", "CodeAnalysis",
    "get_code_assistant", "write_code", "fix_code",
    "run_code", "analyze_code", "detect_language",
    # Image Gen
    "generate_image", "show_fullscreen_image", "get_recent_images",
    # Browser
    "BrowserController", "browse_sync", "search_and_screenshot",
    # Web
    "web_fetch", "web_search", "web_search_detailed",
    "fetch_url", "summarize_url",
    # Email
    "send_email", "read_emails", "add_contact", "list_contacts", "parse_email_command",
    # Media
    "EmbyControl", "media_play", "media_pause", "media_now",
    # Windows
    "get_windows", "focus_window", "minimize_window", "maximize_win",
    "close_window", "arrange_windows",
    # Self-Modify
    "create_script", "run_script", "delete_script",
    "list_scripts", "cleanup_scripts", "create_and_run",
    "get_script_content",
    # Tasks
    "TaskManager", "add_task", "list_tasks", "complete_task", "delete_task",
]
