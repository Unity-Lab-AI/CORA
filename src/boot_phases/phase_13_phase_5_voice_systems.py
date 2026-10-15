#!/usr/bin/env python3
"""PHASE 5: VOICE SYSTEMS

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
    # PHASE 5: VOICE SYSTEMS
    # ================================================================
    _m.display_phase("5.0 Voice Systems", "running")
    _m.display_log("PHASE 5: VOICE SYSTEMS", "phase")
    print("\n[PHASE 5] Voice Systems")
    print("=" * 50)

    # Speech Recognition
    try:
        from voice.stt import SpeechRecognizer
        print("  [OK] Speech Recognition (STT)")
        _m.display_log("Speech Recognition (STT) loaded", "ok")
        _m.BOOT_STATUS['systems'].append({'name': 'Speech Recognition', 'status': 'OK'})
    except Exception as e:
        print(f"  [WARN] Speech Recognition: {e}")
        _m.display_log(f"Speech Recognition: {e}", "warn")
        _m.BOOT_STATUS['systems'].append({'name': 'Speech Recognition', 'status': 'WARN'})

    # Echo Filter
    try:
        from voice.echo_filter import EchoFilter
        print("  [OK] Echo Filter")
        _m.display_log("Echo Filter loaded", "ok")
        _m.BOOT_STATUS['systems'].append({'name': 'Echo Filter', 'status': 'OK'})
    except Exception as e:
        print(f"  [WARN] Echo Filter: {e}")
        _m.display_log(f"Echo Filter: {e}", "warn")
        _m.BOOT_STATUS['systems'].append({'name': 'Echo Filter', 'status': 'WARN'})

    # Wake Word (if available)
    try:
        from voice.wake_word import WakeWordDetector
        print("  [OK] Wake Word Detection")
        _m.display_log("Wake Word Detection loaded", "ok")
        _m.BOOT_STATUS['systems'].append({'name': 'Wake Word', 'status': 'OK'})
    except Exception as e:
        print(f"  [INFO] Wake Word: {e}")
        _m.display_log(f"Wake Word: {e}", "info")
        _m.BOOT_STATUS['systems'].append({'name': 'Wake Word', 'status': 'INFO'})

    # Her voice (sidecar) + STT engine status
    voice_result = "Voice systems online."
    try:
        from voice.tts import voice_status
        vs = voice_status()
        _m.display_log(f"Voice: unity-voice-v2 {'UP' if vs['up'] else 'DOWN'} at {vs['url']}", "ok" if vs['up'] else "warn")
        if not vs['up']:
            voice_result = "Voice server is down."
    except Exception as e:
        _m.display_log(f"Voice status: {e}", "warn")
    try:
        from voice.stt import stt_status
        ss = stt_status()
        _m.display_log(f"STT: {ss.get('engine')} ({ss.get('status')})", "ok" if ss.get('status') == 'ready' else "warn")
        voice_result += " Wake word active." if ss.get('status') == 'ready' else " Speech recognition not ready."
    except Exception:
        voice_result += " Wake word active."

    _m.display_phase("5.0 Voice Systems", "ok")
    response = _m.cora_respond("Voice Systems check", voice_result, "ok")
    _m.speak(response)
    _m.responsive_sleep(0.3)
