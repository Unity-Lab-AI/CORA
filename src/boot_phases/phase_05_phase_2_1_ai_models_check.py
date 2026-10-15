#!/usr/bin/env python3
"""PHASE 2.1: AI MODELS CHECK

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
    # PHASE 2.1: AI MODELS CHECK
    # ================================================================
    _m.display_phase("2.1 AI Models", "running")
    _m.display_log("PHASE 2.1: AI MODELS CHECK", "phase")
    print("\n[PHASE 2.1] AI Models Check")
    print("=" * 50)

    # Required models for CORA come from config (ai.settings), never hardcoded
    from ai import settings as _ai_settings
    REQUIRED_MODELS = {_ai_settings.chat_model(): "Chat/Response model (CORA's personality)",
                       _ai_settings.vision_model(): 'Vision model (see/look commands)'}
    if _ai_settings.code_model() not in REQUIRED_MODELS:
        REQUIRED_MODELS[_ai_settings.code_model()] = 'Coding model (write/fix code)'

    models_ok = 0
    models_missing = []

    try:
        from ai.ollama import list_models
        installed_models = list_models()
        installed_names = [m.get('name', '').lower() for m in installed_models]

        print(f"  Found {len(installed_models)} models installed")
        _m.display_log(f"Found {len(installed_models)} models installed", "info")

        for model_key, model_desc in REQUIRED_MODELS.items():
            # Check if model is installed (exact tag or same base name)
            base = model_key.lower().split(':')[0]
            found = any(name == model_key.lower() or name.split(':')[0] == base for name in installed_names)
            if found:
                print(f"  [OK] {model_key} - {model_desc}")
                _m.display_log(f"{model_key} - OK", "ok")
                models_ok += 1
            else:
                print(f"  [MISSING] {model_key} - {model_desc}")
                _m.display_log(f"{model_key} - MISSING", "warn")
                models_missing.append(model_key)

        _m.BOOT_STATUS['models_installed'] = len(installed_models)
        _m.BOOT_STATUS['models_required'] = len(REQUIRED_MODELS)
        _m.BOOT_STATUS['models_ok'] = models_ok

        if models_ok == len(REQUIRED_MODELS):
            _m.display_phase("2.1 AI Models", "ok")
            _m.BOOT_STATUS['systems'].append({'name': 'AI Models', 'status': 'OK'})
            response = _m.cora_respond("AI Models check", f"{models_ok} of {len(REQUIRED_MODELS)} models loaded. All good.", "ok")
        elif models_ok > 0:
            _m.display_phase("2.1 AI Models", "warn")
            _m.BOOT_STATUS['systems'].append({'name': 'AI Models', 'status': 'WARN'})
            missing_str = ", ".join(models_missing)
            response = _m.cora_respond("AI Models check", f"{models_ok} of {len(REQUIRED_MODELS)} models. Missing: {missing_str}", "warn")
        else:
            _m.display_phase("2.1 AI Models", "fail")
            _m.BOOT_STATUS['systems'].append({'name': 'AI Models', 'status': 'FAIL'})
            response = _m.cora_respond("AI Models check", "No models found. Need to install them.", "fail")
        _m.speak(response)

    except Exception as e:
        print(f"  [WARN] Model check failed: {e}")
        _m.display_log(f"Model check error: {e}", "warn")
        _m.BOOT_STATUS['systems'].append({'name': 'AI Models', 'status': 'WARN'})
        _m.display_phase("2.1 AI Models", "warn")

    _m.responsive_sleep(0.3)
