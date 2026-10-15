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

# Split into the src.cora_parts package on 2026-10-14; this module keeps every name it always had.
from src.cora_parts import _base  # noqa: F401
from src.cora_parts._base import BACKUP_DIR, CHAT_HISTORY, CONFIG, CONFIG_DIR, DATA_DIR, KNOWLEDGE_FILE, PERSONALITY_FILE, Path, ROOT_DIR, TASKS_FILE, ThreadPoolExecutor, VERSION, _PROJECT_ROOT, _cora_system_prompt_cache, _last_deleted_task, _system_tray, add_to_chat_history, argparse, asyncio, cmd_chat, cmd_chathistory, cmd_delete, cmd_settings, cmd_undo, datetime, first_run_setup, generate_id, generate_knowledge_id, get_chat_history_context, get_path, get_system_prompt, init_paths, init_tts, json, knowledge_counter, load_chat_history, load_config, load_knowledge, load_tasks, logging, main, os, save_chat_history, save_knowledge, save_tasks, shutil, speak, subprocess, sys, task_counter, threading, timedelta  # noqa: F401
from src.cora_parts.logging_setup import CHAT_HISTORY_FILE, COMMANDS, CONFIG_FILE, LOG_DIR, LOG_FILE, MAX_CHAT_HISTORY, SYSTEM_PROMPT, SYSTEM_PROMPT_FILE, SYSTEM_TRAY_AVAILABLE, SystemTray, _PROJECT_DIR, async_progress, build_commands, console_formatter, console_handler, create_system_tray, file_formatter, file_handler, load_personality, load_system_prompt, logger, parse_input  # noqa: F401
from src.cora_parts.chat import ai_respond, detect_emotion, fallback_response, generate_greeting, respond  # noqa: F401
from src.cora_parts.system import auto_pull_model, check_ollama, cmd_about, cmd_backup, cmd_clear, cmd_help, cmd_open, cmd_open_cli, cmd_pull_model, cmd_remind, progress_spinner  # noqa: F401
from src.cora_parts.voice import auto_install_kokoro, check_tts, cmd_speak, get_tts_engine, say, speak_kokoro, speak_pyttsx3  # noqa: F401
from src.cora_parts.boot import boot_sequence  # noqa: F401
from src.cora_parts.knowledge import cmd_learn, cmd_recall, cmd_remember  # noqa: F401
from src.cora_parts.tasks import cmd_add, cmd_done, cmd_due, cmd_edit, cmd_list, cmd_note, cmd_pri, cmd_search, cmd_show, cmd_stats, cmd_status, cmd_today, get_task_context  # noqa: F401
from src.cora_parts.tools import cmd_create_tool, cmd_imagine, cmd_list_tools, cmd_modify_tool, cmd_see  # noqa: F401




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
