#!/usr/bin/env python3
"""PHASE 1: VOICE SYNTHESIS (FIRST - so user can hear everything)

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
    # PHASE 1: VOICE SYNTHESIS (FIRST - so user can hear everything)
    # ================================================================
    _m.display_phase("1.0 Voice Synthesis", "running")
    _m.display_log("PHASE 1: VOICE SYNTHESIS", "phase")

    if not L.skip_tts:
        tts_ok = _m.init_tts()
        if tts_ok:
            _m.BOOT_STATUS['systems'].append({'name': 'Voice (unity-voice-v2)', 'status': 'OK'})
            _m.display_log("unity-voice-v2 online - her own voice", "ok")
            _m.display_phase("1.0 Voice Synthesis", "ok")
        else:
            _m.BOOT_STATUS['systems'].append({'name': 'Voice (unity-voice-v2)', 'status': 'FAIL'})
            _m.display_log("unity-voice-v2 sidecar unavailable (see data/voice-sidecar.log)", "fail")
            _m.display_phase("1.0 Voice Synthesis", "fail")
    else:
        # Silent boot: nothing is spoken, but her voice is still checked. Green when the
        # sidecar answers (muted for this boot), yellow only when her voice is really down
        # (owner, 2026-10-14: "step 1.0 still didnt green up" on a silent check boot).
        _m._tts_engine = None
        try:
            from voice.unity_voice import is_up as _voice_up, VOICE_URL as _voice_url
            up = _voice_up(2.0)
        except Exception:
            up, _voice_url = False, ''
        if up:
            print(f"[BOOT] Silent boot: her voice is up at {_voice_url}, muted for this run")
            _m.BOOT_STATUS['systems'].append({'name': 'Voice (unity-voice-v2)', 'status': 'OK'})
            _m.display_log("unity-voice-v2 online (silent boot: muted)", "ok")
            _m.display_phase("1.0 Voice Synthesis", "ok")
        else:
            print("[BOOT] Silent boot: her voice sidecar is not reachable")
            _m.display_log("Silent boot: unity-voice-v2 sidecar not reachable", "warn")
            _m.display_phase("1.0 Voice Synthesis", "warn")

    # Opening announcement - CORA generates her own intro dynamically
    # Who made her comes from config/config.json (one source for the screen, the CLI and her voice)
    try:
        from ai.settings import creators as _creators
        _who = _creators()
    except Exception:
        _who = {'lab': 'Unity AI Lab', 'spoken': 'Hackall360, Sponge, GFourteen, and Alfreddo'}
    about_data = {
        'name': 'CORA',
        'version': _m._app_version(),
        'creator': _who['lab'],
        'developers': _who['spoken'],
    }
    # CORA generates her own unique intro - natural speech. Every creator is
    # named in what she says, by name, every boot.
    response = _m.cora_respond(
        "About Me Introduction",
        f"Hey, I'm {about_data['name']}. Version {about_data['version']}. "
        f"Made by {about_data['developers']} over at {about_data['creator']}. "
        f"I've got voice, vision, and plenty of attitude. Let's get this boot going.",
        "ok", mode="full",
        must_include=list(_who.get('names') or []) + [about_data['creator']]
    )
    _m.speak(response)
    _m.responsive_sleep(0.3)
