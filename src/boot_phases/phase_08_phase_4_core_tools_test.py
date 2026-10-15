#!/usr/bin/env python3
"""PHASE 4: CORE TOOLS TEST

One phase of src.boot_sequence.run_boot_sequence, split out on 2026-10-14. `_m` is the live
src.boot_sequence module (its names are read and assigned through it); `L` holds the locals
shared across phases."""
from __future__ import annotations
import json
import os
import re
import sys
import time

import sys
import os
import time
import signal
import atexit
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


# Import centralized window manager
from ui.window_manager import create_window, create_popup, create_image_window, create_code_window, bring_to_front


def run(_m, L):

    # ================================================================
    # PHASE 4: CORE TOOLS TEST
    # ================================================================
    _m.display_phase("4.0 Core Tools", "running")
    _m.display_log("PHASE 4: CORE TOOLS TEST", "phase")
    print("\n[PHASE 4] Core Tools Test")
    print("=" * 50)

    tools_ok = 0
    tools_total = 0

    # Memory System
    tools_total += 1
    try:
        from cora_tools.memory import recall, remember
        print("  [OK] Memory System (recall/remember)")
        _m.display_log("Memory System loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Memory System', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [FAIL] Memory System: {e}")
        _m.display_log(f"Memory System FAILED: {e}", "fail")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Memory System', 'status': 'FAIL'})

    # Task Manager
    tools_total += 1
    try:
        from cora_tools.tasks import TaskManager
        tm = TaskManager()
        task_count = len(tm.tasks) if hasattr(tm, 'tasks') else 0
        print(f"  [OK] Task Manager ({task_count} tasks)")
        _m.display_log(f"Task Manager loaded ({task_count} tasks)", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Task Manager', 'status': 'OK'})
        _m.BOOT_STATUS['task_count'] = task_count
        tools_ok += 1
    except Exception as e:
        print(f"  [FAIL] Task Manager: {e}")
        _m.display_log(f"Task Manager FAILED: {e}", "fail")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Task Manager', 'status': 'FAIL'})

    # Reminders
    tools_total += 1
    try:
        from cora_tools.reminders import ReminderManager
        rm = ReminderManager()
        reminder_count = len(rm.reminders) if hasattr(rm, 'reminders') else 0
        print(f"  [OK] Reminders ({reminder_count} active)")
        _m.display_log(f"Reminders loaded ({reminder_count} active)", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Reminders', 'status': 'OK'})
        _m.BOOT_STATUS['reminder_count'] = reminder_count
        tools_ok += 1
    except Exception as e:
        print(f"  [FAIL] Reminders: {e}")
        _m.display_log(f"Reminders FAILED: {e}", "fail")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Reminders', 'status': 'FAIL'})

    # File Operations
    tools_total += 1
    try:
        from cora_tools.files import read_file, create_file
        print("  [OK] File Operations")
        _m.display_log("File Operations loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'File Operations', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [FAIL] File Operations: {e}")
        _m.display_log(f"File Operations FAILED: {e}", "fail")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'File Operations', 'status': 'FAIL'})

    # Screenshot/Vision
    tools_total += 1
    try:
        from cora_tools.screenshots import desktop, quick_screenshot
        print("  [OK] Vision/Screenshots")
        _m.display_log("Vision/Screenshots loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Vision/Screenshots', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Vision/Screenshots: {e}")
        _m.display_log(f"Vision/Screenshots: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Vision/Screenshots', 'status': 'WARN'})

    # Web Browser
    tools_total += 1
    try:
        from cora_tools.browser import browse_sync
        print("  [OK] Web Browser")
        _m.display_log("Web Browser loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Web Browser', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Web Browser: {e}")
        _m.display_log(f"Web Browser: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Web Browser', 'status': 'WARN'})

    # System Tools
    tools_total += 1
    try:
        from cora_tools.system import run_shell, get_system_info
        print("  [OK] System Commands")
        _m.display_log("System Commands loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'System Commands', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] System Commands: {e}")
        _m.display_log(f"System Commands: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'System Commands', 'status': 'WARN'})

    # Windows Control
    tools_total += 1
    try:
        from cora_tools.windows import list_windows, focus_window
        print("  [OK] Windows Control")
        _m.display_log("Windows Control loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Windows Control', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Windows Control: {e}")
        _m.display_log(f"Windows Control: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Windows Control', 'status': 'WARN'})

    # Code Tools
    tools_total += 1
    try:
        from cora_tools.code import analyze_code
        print("  [OK] Code Analysis")
        _m.display_log("Code Analysis loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Code Analysis', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Code Analysis: {e}")
        _m.display_log(f"Code Analysis: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Code Analysis', 'status': 'WARN'})

    # Media Control
    tools_total += 1
    try:
        from cora_tools.media import MediaController
        print("  [OK] Media Control")
        _m.display_log("Media Control loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Media Control', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Media Control: {e}")
        _m.display_log(f"Media Control: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Media Control', 'status': 'WARN'})

    _m.display_phase("4.0 Core Tools", "ok")
    # Tools summary - just the numbers
    tools_result = f"{tools_ok} of {tools_total} tools loaded."
    tools_status = "ok" if tools_ok >= tools_total - 2 else ("warn" if tools_ok >= tools_total // 2 else "fail")
    response = _m.cora_respond("Core Tools check", tools_result, tools_status)
    _m.speak(response)
    _m.responsive_sleep(0.3)
