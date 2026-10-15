#!/usr/bin/env python3
"""PHASE 6.1: YOUTUBE/AUDIO PLAYBACK TEST

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
    # PHASE 6.1: YOUTUBE/AUDIO PLAYBACK TEST
    # ================================================================
    _m.display_phase("6.1 Audio Test", "running")
    _m.display_log("PHASE 6.1: AUDIO PLAYBACK TEST", "phase")
    print("\n[PHASE 6.1] Audio Playback Test")
    print("=" * 50)

    try:
        if not L._demo:
            raise _m._SkippedPhase("boot.demo_phases is false")
        import subprocess
        import random

        # Random audio test options
        audio_tests = [
            {"query": "lofi hip hop beats", "name": "Lofi Hip Hop"},
            {"query": "synthwave music", "name": "Synthwave"},
            {"query": "ambient space music", "name": "Ambient Space"},
            {"query": "jazz piano relaxing", "name": "Jazz Piano"},
            {"query": "classical piano beautiful", "name": "Classical Piano"},
            {"query": "cyberpunk music mix", "name": "Cyberpunk Mix"},
        ]

        test = random.choice(audio_tests)
        test_name = test['name']
        test_query = test['query']

        print(f"  Testing audio playback: {test_name}")
        _m.display_tool("Audio Playback", f"Testing: {test_name}")
        _m.display_action(f"Searching YouTube for: {test_query}")

        # Use yt-dlp to search and get video URL, then play with mpv
        video_url = None
        mpv_process = None

        try:
            # Search with yt-dlp
            result = subprocess.run(
                ['yt-dlp', '--get-url', '--format', 'bestaudio', f'ytsearch1:{test_query}'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                video_url = result.stdout.strip().split('\n')[0]
                print(f"  Found audio stream URL")
        except FileNotFoundError:
            print(f"  [WARN] yt-dlp not installed")
            _m.display_log("yt-dlp not installed - skipping audio test", "warn")
        except Exception as e:
            print(f"  [WARN] yt-dlp search failed: {e}")

        if video_url:
            try:
                # Play audio with mpv (no video, 20 second limit for loading + playback)
                print(f"  Playing with mpv...")
                _m.display_result(f"Playing: {test_name}")

                mpv_process = subprocess.Popen(
                    ['mpv', '--no-video', '--length=20', '--really-quiet', '--no-terminal', video_url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                _m.BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'OK'})
                _m.BOOT_STATUS['audio_test'] = test_name

                # Let it play for a bit, then speak while it's playing
                _m.responsive_sleep(3)

                response = _m.cora_respond("Audio Playback", f"Audio working. Playing {test_name}.", "ok")
                _m.speak(response)

                # Wait for mpv to finish (max 20 sec total for loading + 10 sec playback)
                try:
                    mpv_process.wait(timeout=18)
                except subprocess.TimeoutExpired:
                    mpv_process.terminate()

                _m.display_phase("6.1 Audio Test", "ok")

            except FileNotFoundError:
                print(f"  [WARN] mpv not installed")
                _m.display_log("mpv not installed - skipping audio test", "warn")
                _m.BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'WARN'})
                _m.display_phase("6.1 Audio Test", "warn")
            except Exception as e:
                print(f"  [WARN] mpv playback failed: {e}")
                _m.display_log(f"mpv playback failed: {e}", "warn")
                _m.BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'WARN'})
                _m.display_phase("6.1 Audio Test", "warn")
        else:
            print(f"  [WARN] Could not find audio to play")
            _m.display_log("Could not find audio stream", "warn")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'WARN'})
            _m.display_phase("6.1 Audio Test", "warn")

            response = _m.cora_respond("Audio Playback", "Audio skipped. Need yt-dlp and mpv.", "warn")
            _m.speak(response)

    except _m._SkippedPhase as e:
        _m.display_log(f"Audio test skipped ({e})", "info")
        _m.display_phase("6.1 Audio Test", "ok")
    except Exception as e:
        print(f"  [WARN] Audio playback test: {e}")
        _m.display_log(f"Audio playback error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'WARN'})
        _m.display_phase("6.1 Audio Test", "warn")

    _m.responsive_sleep(0.3)
