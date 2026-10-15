#!/usr/bin/env python3
"""PHASE 10: FINAL SYSTEM CHECK

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
    # PHASE 10: FINAL SYSTEM CHECK
    # ================================================================
    _m.display_phase("10.0 Final Check", "running")
    _m.display_log("PHASE 10: FINAL CHECK", "phase")
    print("\n[PHASE 10] Final System Check")
    print("=" * 50)

    # Calculate boot time
    _m.BOOT_STATUS['end_time'] = time.time()
    boot_time = _m.BOOT_STATUS['end_time'] - _m.BOOT_STATUS['start_time']

    # Count results
    ok_count = sum(1 for s in _m.BOOT_STATUS['systems'] if s['status'] == 'OK')
    warn_count = sum(1 for s in _m.BOOT_STATUS['systems'] if s['status'] == 'WARN')
    fail_count = sum(1 for s in _m.BOOT_STATUS['systems'] if s['status'] == 'FAIL')
    total_systems = len(_m.BOOT_STATUS['systems'])

    tools_passed = sum(1 for t in _m.BOOT_STATUS['tools_tested'] if t['status'] == 'OK')
    total_tools = len(_m.BOOT_STATUS['tools_tested'])

    print(f"  Systems: {ok_count} OK / {warn_count} WARN / {fail_count} FAIL")
    print(f"  Tools: {tools_passed}/{total_tools} passed")
    print(f"  Boot time: {boot_time:.1f} seconds")

    _m.display_log(f"Systems: {ok_count} OK / {warn_count} WARN / {fail_count} FAIL", "system")
    _m.display_log(f"Tools: {tools_passed}/{total_tools} passed", "system")
    _m.display_log(f"Boot time: {boot_time:.1f} seconds", "system")

    # Show warnings/failures in detail
    if warn_count > 0 or fail_count > 0:
        print("\n  --- Issues Detected ---")
        _m.display_log("─── Issues Detected ───", "warn")
        for s in _m.BOOT_STATUS['systems']:
            if s['status'] == 'WARN':
                print(f"  [WARN] {s['name']}")
                _m.display_log(f"System: {s['name']}", "warn")
            elif s['status'] == 'FAIL':
                print(f"  [FAIL] {s['name']}")
                _m.display_log(f"System: {s['name']}", "fail")
        for t in _m.BOOT_STATUS['tools_tested']:
            if t['status'] == 'WARN':
                print(f"  [WARN] Tool: {t['name']}")
                _m.display_log(f"Tool: {t['name']}", "warn")
            elif t['status'] == 'FAIL':
                err = t.get('error', 'Unknown error')
                print(f"  [FAIL] Tool: {t['name']} - {err}")
                _m.display_log(f"Tool: {t['name']} - {err}", "fail")

    # ================================================================
    # FINAL SUMMARY - SPOKEN
    # ================================================================
    _m.display_log("═══════════════════════════════════════════════════", "phase")
    _m.display_log("           BOOT SEQUENCE COMPLETE", "phase")
    _m.display_log("═══════════════════════════════════════════════════", "phase")

    print("")
    print("  +=========================================================+")
    print("  |              BOOT SEQUENCE COMPLETE                     |")
    print("  +=========================================================+")
    print("")

    # Build spoken summary
    L.now = datetime.now()
    time_str = L.now.strftime("%I:%M %p").lstrip('0')
    day_str = L.now.strftime("%A")
    date_str = L.now.strftime("%B %d")  # e.g., "December 24"
    hour = L.now.hour

    # Time greeting - natural phrasing
    if hour < 12:
        greeting = f"Good morning. Today is {day_str}, {date_str}. It's {time_str}."
    elif hour < 17:
        greeting = f"Good afternoon. Today is {day_str}, {date_str}. It's {time_str}."
    else:
        greeting = f"Evening. Today is {day_str}, {date_str}. It's {time_str}."

    _m.display_log(greeting, "system")

    # Weather
    weather_text = ""
    if L.weather_data and isinstance(L.weather_data, dict):
        temp = L.weather_data.get('temp', L.weather_data.get('temperature', ''))
        cond = L.weather_data.get('condition', L.weather_data.get('description', ''))
        if temp and cond:
            weather_text = f"Weather is {temp} and {cond.lower()}."
            _m.display_log(weather_text, "info")

    # System status - natural speech
    if fail_count > 0:
        status_text = f"Got {fail_count} systems that failed to load. Something's broken."
        _m.display_log(status_text, "fail")
    elif warn_count > 0:
        status_text = f"All the important stuff is working. Just {warn_count} minor issues, nothing serious."
        _m.display_log(status_text, "warn")
    else:
        status_text = "Everything is up and running perfectly."
        _m.display_log(status_text, "ok")

    # Hardware warnings
    hw_warning = ""
    if _m.BOOT_STATUS['cpu_percent'] > 70:
        hw_warning = f"CPU at {_m.BOOT_STATUS['cpu_percent']:.0f}%."
        _m.display_log(hw_warning, "warn")
    elif _m.BOOT_STATUS['memory_percent'] > 80:
        hw_warning = f"RAM at {_m.BOOT_STATUS['memory_percent']:.0f}%."
        _m.display_log(hw_warning, "warn")

    # Boot complete summary - just the facts
    summary_data = f"Boot complete. {greeting}"
    if hw_warning:
        summary_data += f" Warning: {hw_warning}"

    _m.display_phase("10.0 Final Check", "ok")
    response = _m.cora_respond("Boot Complete", summary_data, "ok")
    _m.speak(response)

    print("")
    print("  +=========================================================+")
    print("  |                 C.O.R.A IS READY                        |")
    print("  +=========================================================+")
    print("")

    _m.display_log("C.O.R.A IS READY", "ok")

    # ================================================================
    # CORA ANNOUNCES HER ABILITIES
    # ================================================================
    abilities_list = """
Here's what I can do for you:

CONVERSATION & VOICE:
- Talk to me naturally - I'll respond with my voice
- Ask me anything - I'm pretty smart when I feel like it

VISION & MEDIA:
- Take screenshots and describe what I see on your screen
- Look through your camera and describe what's there
- Generate images from any description you give me
- Play music and control media playback

PRODUCTIVITY:
- Set reminders and alarms - I'll bug you when it's time
- Manage your calendar and schedule events
- Create and track tasks and to-do lists
- Take notes and remember things for you

WEB & RESEARCH:
- Search the web and summarize what I find
- Open websites and browse for information
- Fetch and read web pages

FILES & SYSTEM:
- Read and write files on your computer
- Run system commands and scripts
- Check system stats like CPU and memory
- Control windows and applications

CODE & DEVELOPMENT:
- Write and explain code in any language
- Debug and fix code problems
- Run Python scripts

EMAIL & COMMUNICATION:
- Send and read emails
- Draft messages for you

Just tell me what you need.
"""

    _m.display_log("─── CORA's Abilities ───", "info")

    # NOW load and send the tools prompt (separate from personality)
    # This only happens AFTER boot is complete
    tools_prompt = _m.get_tools_prompt()
    _m.display_log("Tools and commands loaded", "ok")

    # CORA announces she's ready - full mode for personality
    abilities_summary = "voice, vision, camera, image gen, reminders, tasks, web search, code help, email, system stats"
    abilities_response = _m.cora_respond("Abilities announcement", f"I'm online. I can do: {abilities_summary}. What do you need?", "ok", mode="full")
    _m.speak(abilities_response)

    # Print categorized abilities to console
    _m.display_log("Vision: see, look, screenshot, camera", "info")
    _m.display_log("Images: imagine, draw, generate", "info")
    _m.display_log("Files: viewfile, viewcode, viewimage", "info")
    _m.display_log("Web: websearch, fetchurl, browse", "info")
    _m.display_log("System: stats, terminal, settings", "info")
    _m.display_log("Tasks: add, list, done, remind", "info")
    _m.display_log("Media: play, pause, volume", "info")
    _m.display_log("Code: explain, write, fix, run", "info")
    _m._boot_complete = True
    time.sleep(0.1)  # Brief pause to let thread exit

    # Enable chat mode - transform display into interactive chat
    if _m._boot_display:
        _m._boot_display.enable_chat_mode()
        # Keep display running as interactive chat UI

    _m.BOOT_STATUS['summary'] = summary_data
    return ('return', _m.BOOT_STATUS)
