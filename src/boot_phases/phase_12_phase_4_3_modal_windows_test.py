#!/usr/bin/env python3
"""PHASE 4.3: MODAL WINDOWS TEST

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
    # PHASE 4.3: MODAL WINDOWS TEST
    # ================================================================
    _m.display_phase("4.3 Modal Windows", "running")
    _m.display_log("PHASE 4.3: MODAL WINDOWS TEST", "phase")
    print("\n[PHASE 4.3] Modal Windows Test")
    print("=" * 50)

    try:
        if not L._demo:
            raise _m._SkippedPhase("boot.demo_phases is false")
        import tkinter as tk
        import random

        # Random modal content for variety
        modal_quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Stay hungry, stay foolish. - Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It does not matter how slowly you go as long as you do not stop. - Confucius",
            "The best way to predict the future is to invent it. - Alan Kay",
            "Code is like humor. When you have to explain it, it's bad. - Cory House",
            "First, solve the problem. Then, write the code. - John Johnson",
        ]

        quote = random.choice(modal_quotes)

        # Test message modal
        print("  Testing message modal...")
        _m.display_action("Opening test message modal...")

        # Use window manager for proper z-layering
        parent = _m._boot_display.root if _m._boot_display else None
        msg_window = create_popup(
            title="CORA - Modal Test",
            width=500, height=300,
            bg='#2d2d2d',
            parent=parent
        )

        # Content
        title_label = tk.Label(
            msg_window,
            text="Modal Window Test",
            font=('Segoe UI', 14, 'bold'),
            fg='#00ff88',
            bg='#2d2d2d',
            pady=15
        )
        title_label.pack(fill='x')

        quote_label = tk.Label(
            msg_window,
            text=quote,
            font=('Segoe UI', 11),
            fg='#ffffff',
            bg='#2d2d2d',
            wraplength=450,
            pady=20
        )
        quote_label.pack(fill='x', padx=20)

        status_label = tk.Label(
            msg_window,
            text="Modal Types Available:\n- Message popups\n- Code viewer with syntax highlighting\n- Image viewer\n- Terminal output\n- File viewer",
            font=('Consolas', 10),
            fg='#888888',
            bg='#2d2d2d',
            justify='left'
        )
        status_label.pack(fill='x', padx=20, pady=10)

        msg_window.update()

        print("  [OK] Message modal displayed")
        _m.display_result("Modal windows working correctly")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Modal Windows', 'status': 'OK'})
        _m.display_phase("4.3 Modal Windows", "ok")

        response = _m.cora_respond("Modal Windows", "Modal windows working.", "ok")
        _m.speak(response)

        # Close modal after speaking
        try:
            msg_window.destroy()
        except:
            pass

    except _m._SkippedPhase as e:
        _m.display_log(f"Modal test skipped ({e})", "info")
        _m.display_phase("4.3 Modal Windows", "ok")
    except Exception as e:
        print(f"  [WARN] Modal windows test: {e}")
        _m.display_log(f"Modal windows error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Modal Windows', 'status': 'WARN'})
        _m.display_phase("4.3 Modal Windows", "warn")

    _m.responsive_sleep(0.3)
