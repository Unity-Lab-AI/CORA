#!/usr/bin/env python3
"""PHASE 0.8: WAVEFORM INITIALIZATION

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
    # PHASE 0.8: WAVEFORM INITIALIZATION
    # ================================================================
    _m.display_phase("0.8 Waveform Init", "running")
    _m.display_log("PHASE 0.8: WAVEFORM VISUAL", "phase")
    print("\n[PHASE 0.8] Waveform Visual Initialization")
    print("=" * 50)

    waveform_ok = False
    waveform_errors = []

    try:
        from ui.boot_display import AudioWaveform, get_audio_buffer, set_audio_data, clear_audio_data, _audio_buffer_lock
        print("  [OK] AudioWaveform module loaded")
        _m.display_log("AudioWaveform module loaded", "ok")

        # Check 1: Boot display exists
        if not _m._boot_display:
            waveform_errors.append("Boot display not initialized")
            print("  [FAIL] Boot display not initialized")
            _m.display_log("Boot display not initialized", "fail")
        else:
            print("  [OK] Boot display exists")
            _m.display_log("Boot display exists", "ok")

            # Check 2: Waveform widget exists
            if not _m._boot_display.waveform:
                waveform_errors.append("Waveform widget is None")
                print("  [FAIL] Waveform widget is None")
                _m.display_log("Waveform widget is None", "fail")
            else:
                print("  [OK] Waveform widget created")
                _m.display_log("Waveform widget created", "ok")

                # Check 3: Audio buffer works
                try:
                    buf = get_audio_buffer()
                    print(f"  [OK] Audio buffer initialized (active={buf['active']})")
                    _m.display_log("Audio buffer initialized", "ok")
                except Exception as e:
                    waveform_errors.append(f"Audio buffer error: {e}")
                    print(f"  [FAIL] Audio buffer error: {e}")
                    _m.display_log(f"Audio buffer error: {e}", "fail")

                # Check 4: Test setting audio data
                try:
                    import numpy as np
                    # Create a test sine wave
                    test_samples = np.sin(np.linspace(0, 10 * np.pi, 2400)).astype(np.float32)
                    set_audio_data(test_samples, sample_rate=24000)
                    buf = get_audio_buffer()
                    if buf['active'] and buf['data'] is not None:
                        print(f"  [OK] Audio data injection works ({len(buf['data'])} samples)")
                        _m.display_log("Audio data injection works", "ok")
                    else:
                        waveform_errors.append("Audio data not received by buffer")
                        print("  [FAIL] Audio data not received by buffer")
                        _m.display_log("Audio data not received", "fail")
                except Exception as e:
                    waveform_errors.append(f"Audio injection error: {e}")
                    print(f"  [FAIL] Audio injection error: {e}")
                    _m.display_log(f"Audio injection error: {e}", "fail")

                # Check 5: Test waveform animation with audio data
                print("  Testing waveform animation with audio...")
                _m.display_log("Testing waveform animation", "info")
                try:
                    _m._boot_display.waveform.start()
                    # Let it animate for 1 second with our test data
                    for _ in range(10):
                        time.sleep(0.1)
                        if _m._boot_display.root:
                            _m._boot_display.root.update()
                    _m._boot_display.waveform.stop()
                    clear_audio_data()
                    print("  [OK] Waveform animation test passed")
                    _m.display_log("Waveform animation working", "ok")
                    waveform_ok = True
                except Exception as e:
                    waveform_errors.append(f"Animation error: {e}")
                    print(f"  [FAIL] Animation error: {e}")
                    _m.display_log(f"Animation error: {e}", "fail")

        # Summary
        if waveform_ok:
            print("  [OK] All waveform checks passed")
            _m.display_log("All waveform checks passed", "ok")
            _m.BOOT_STATUS['systems'].append({'name': 'Waveform Visual', 'status': 'OK'})
            _m.display_phase("0.8 Waveform Init", "ok")
        else:
            error_summary = "; ".join(waveform_errors) if waveform_errors else "Unknown error"
            print(f"  [WARN] Waveform issues: {error_summary}")
            _m.display_log(f"Issues: {error_summary}", "warn")
            _m.BOOT_STATUS['systems'].append({'name': 'Waveform Visual', 'status': 'WARN'})
            _m.display_phase("0.8 Waveform Init", "warn")

    except Exception as e:
        print(f"  [FAIL] Waveform init exception: {e}")
        _m.display_log(f"Waveform exception: {e}", "fail")
        _m.BOOT_STATUS['systems'].append({'name': 'Waveform Visual', 'status': 'FAIL'})
        _m.display_phase("0.8 Waveform Init", "fail")
