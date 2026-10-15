#!/usr/bin/env python3
"""PHASE 0.9: ABOUT CORA (Introduction)

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
    # PHASE 0.9: ABOUT CORA (Introduction)
    # ================================================================
    _m.display_phase("0.9 About CORA", "running")
    _m.display_log("PHASE 0.9: ABOUT CORA", "phase")
    print("\n[PHASE 0.9] About CORA")
    print("=" * 50)

    # Display the about info in the log
    _m.display_log("═══════════════════════════════════════════════", "system")
    _m.display_log("    C.O.R.A - Cognitive Operations & Reasoning Assistant", "system")
    _m.display_log("    Version 1.0.0 | Unity AI Lab | 2025", "system")
    _m.display_log("═══════════════════════════════════════════════", "system")
    _m.display_log("", "info")
    _m.display_log("Developers:", "info")
    try:
        from ai.settings import creators as _creators_cfg
        _c = _creators_cfg()
        for _n in _c['names']:
            _m.display_log(f"  {_n} - {_c['roles'].get(_n, 'Creator')}", "info")
    except Exception:
        for _line in ("Hackall360 - Lead Code Necromancer", "Sponge - Chaos Engineer",
                      "GFourteen - Digital Alchemist", "Alfreddo - Co-Creator"):
            _m.display_log(f"  {_line}", "info")
    _m.display_log("", "info")
    _m.display_log("Links:", "info")
    _m.display_log("  Website: https://www.unityailab.com", "info")
    _m.display_log("  GitHub: https://github.com/Unity-Lab-AI", "info")
    _m.display_log("  Discord: https://discord.gg/D33Bk6Ay", "info")
    _m.display_log("  Email: unityailabcontact@gmail.com", "info")
    _m.display_log("", "info")
    _m.display_log("© 2025 Unity AI Lab. All rights reserved.", "info")
    _m.display_log("═══════════════════════════════════════════════", "system")

    print("  C.O.R.A - Cognitive Operations & Reasoning Assistant")
    print("  Version: 1.0.0 | Unity AI Lab | 2025")
    print(f"  Creators: {', '.join(_c['names']) if '_c' in dir() else 'Hackall360, Sponge, GFourteen, Alfreddo'}")
    print("  www.unityailab.com | discord.gg/D33Bk6Ay")

    _m.BOOT_STATUS['version'] = _m._app_version()
    _m.BOOT_STATUS['creators'] = ', '.join(_c['names']) if '_c' in dir() else 'Hackall360, Sponge, GFourteen, Alfreddo'
    _m.display_phase("0.9 About CORA", "ok")
