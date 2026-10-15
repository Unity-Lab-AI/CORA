#!/usr/bin/env python3
"""PHASE 4.5: DAILY BRIEFING - today's calendar, tasks, reminders

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
    # PHASE 4.5: DAILY BRIEFING - today's calendar, tasks, reminders
    # (the spec'd boot narration) + start the reminder scheduler
    # ================================================================
    _m.display_phase("4.5 Daily Briefing", "running")
    _m.display_log("PHASE 4.5: DAILY BRIEFING", "phase")
    print("\n[PHASE 4.5] Daily Briefing")
    print("=" * 50)
    try:
        briefing_parts = []

        # Calendar: today's events
        try:
            from cora_tools.calendar import get_today_events, format_event_time
            events = get_today_events()
            if events:
                names = []
                for ev in events[:4]:
                    try:
                        names.append(f"{ev.get('title', 'event')} at {format_event_time(ev)}")
                    except Exception:
                        names.append(str(ev.get('title', 'event')))
                briefing_parts.append(f"{len(events)} event{'s' if len(events) != 1 else ''} today: " + "; ".join(names) + ".")
                _m.display_log(f"Calendar: {len(events)} event(s) today", "ok")
                for n in names:
                    _m.display_log(f"  {n}", "info")
            else:
                briefing_parts.append("Nothing on the calendar today.")
                _m.display_log("Calendar: no events today", "info")
            _m.BOOT_STATUS['today_events'] = len(events)
        except Exception as e:
            _m.display_log(f"Calendar: {e}", "warn")

        # Tasks: overdue + pending
        try:
            from cora_tools.tasks import get_manager
            tm = get_manager()
            pending = tm.list_tasks('pending')
            overdue = tm.list_tasks('overdue')
            high = [t for t in pending if int(t.get('priority', 3) or 3) <= 1]
            if overdue:
                titles = ", ".join(str(t.get('text') or t.get('title') or 'task') for t in overdue[:3])
                briefing_parts.append(f"{len(overdue)} overdue task{'s' if len(overdue) != 1 else ''}: {titles}.")
                _m.display_log(f"Tasks: {len(overdue)} OVERDUE", "warn")
            if high:
                titles = ", ".join(str(t.get('text') or t.get('title') or 'task') for t in high[:3])
                briefing_parts.append(f"High priority: {titles}.")
            if pending:
                briefing_parts.append(f"{len(pending)} task{'s' if len(pending) != 1 else ''} pending.")
                _m.display_log(f"Tasks: {len(pending)} pending", "info")
            else:
                briefing_parts.append("No pending tasks.")
            _m.BOOT_STATUS['tasks_pending'] = len(pending)
            _m.BOOT_STATUS['tasks_overdue'] = len(overdue)
        except Exception as e:
            _m.display_log(f"Tasks: {e}", "warn")

        # Reminders: upcoming today + start the scheduler so they actually fire
        try:
            from cora_tools.reminders import ReminderManager, format_reminder
            _m._reminder_manager = ReminderManager()
            upcoming = []
            today = datetime.now().date()
            for r in _m._reminder_manager.list_all(enabled_only=True):
                when = r.get('time') or r.get('due') or r.get('datetime')
                try:
                    when_dt = datetime.fromisoformat(str(when)) if when else None
                except Exception:
                    when_dt = None
                if when_dt is None or when_dt.date() == today:
                    upcoming.append(r)
            if upcoming:
                texts = ", ".join(str(r.get('text') or r.get('message') or 'reminder') for r in upcoming[:3])
                briefing_parts.append(f"{len(upcoming)} reminder{'s' if len(upcoming) != 1 else ''} today: {texts}.")
                _m.display_log(f"Reminders: {len(upcoming)} today", "ok")

            def _on_reminder(rem):
                try:
                    line = format_reminder(rem)
                except Exception:
                    line = str(rem.get('text') or rem.get('message') or 'Reminder')
                _m.display_log(f"REMINDER: {line}", "warn")
                try:
                    from services.notifications import notify
                    notify("CORA Reminder", line)
                except Exception:
                    pass
                _m.speak(f"Reminder: {line}", blocking=False, emotion='urgent')

            _m._reminder_manager.set_callback(_on_reminder)
            _m._reminder_manager.start_checking(interval=30)
            _m.display_log("Reminder scheduler running (30 s)", "ok")
            _m.BOOT_STATUS['systems'].append({'name': 'Reminder Scheduler', 'status': 'OK'})
        except Exception as e:
            _m.display_log(f"Reminders: {e}", "warn")
            _m.BOOT_STATUS['systems'].append({'name': 'Reminder Scheduler', 'status': 'WARN'})

        _m.display_phase("4.5 Daily Briefing", "ok")
        briefing = " ".join(briefing_parts) if briefing_parts else "Nothing scheduled, nothing pending."
        response = _m.cora_respond("Daily Briefing", briefing, "ok", mode="full")
        _m.speak(response)
    except Exception as e:
        print(f"  [WARN] Daily briefing: {e}")
        _m.display_log(f"Daily briefing error: {e}", "warn")
        _m.display_phase("4.5 Daily Briefing", "warn")

    _m.responsive_sleep(0.3)

    # Demo phases (GitHub import, YouTube, modal test, audio test, image gen)
    # only run when config.json boot.demo_phases is true.
    _boot_cfg = _m._boot_config()
    L._demo = bool(_boot_cfg.get('demo_phases', False))
    L._github_import = bool(_boot_cfg.get('github_import', False))
