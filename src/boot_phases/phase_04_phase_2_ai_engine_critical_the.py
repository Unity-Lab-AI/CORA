#!/usr/bin/env python3
"""PHASE 2: AI ENGINE (Critical - the brain)

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
    # PHASE 2: AI ENGINE (Critical - the brain)
    # ================================================================
    _m.display_phase("2.0 AI Engine", "running")
    _m.display_log("PHASE 2: AI ENGINE", "phase")
    print("\n[PHASE 2] AI Engine Initialization")
    print("=" * 50)

    ai_online = False
    ai_model = "Unknown"

    try:
        from ai.ollama import check_ollama, get_model_info
        print("  Checking Ollama connection...")
        _m.display_log("Checking Ollama connection...", "info")

        if check_ollama():
            ai_online = True
            try:
                info = get_model_info()
                ai_model = info.get('model', 'Ollama')
            except:
                ai_model = "Ollama"
            print(f"  [OK] AI Engine online - {ai_model}")
            _m.display_log(f"AI Engine online - Model: {ai_model}", "ok")
            _m.BOOT_STATUS['systems'].append({'name': f'AI Engine ({ai_model})', 'status': 'OK'})
            _m.display_phase("2.0 AI Engine", "ok")
            # CORA announces AI status - just the data
            response = _m.cora_respond("AI Brain/Ollama", f"AI engine online. Model: {ai_model}", "ok")
            _m.speak(response)
        else:
            print("  [WARN] AI Engine not responding")
            _m.display_log("AI Engine not responding", "warn")
            _m.BOOT_STATUS['systems'].append({'name': 'AI Engine', 'status': 'WARN'})
            _m.display_phase("2.0 AI Engine", "warn")
            response = _m.cora_respond("AI Brain/Ollama", "AI engine not responding. Ollama may be down.", "warn")
            _m.speak(response)

    except Exception as e:
        print(f"  [WARN] AI Engine: {e}")
        _m.display_log(f"AI Engine error: {e}", "warn")
        _m.BOOT_STATUS['systems'].append({'name': 'AI Engine', 'status': 'WARN'})
        _m.display_phase("AI Engine", "warn")
        response = _m.cora_respond("AI Brain/Ollama", f"AI engine error: {e}", "fail")
        _m.speak(response)

    _m.responsive_sleep(0.3)
