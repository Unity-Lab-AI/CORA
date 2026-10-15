#!/usr/bin/env python3
"""PHASE 3.1: LIVE CAMERA FEED TEST

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
    # PHASE 3.1: LIVE CAMERA FEED TEST
    # ================================================================
    _m.display_phase("3.1 Camera Feed", "running")
    _m.display_log("PHASE 3.1: LIVE CAMERA FEED TEST", "phase")
    print("\n[PHASE 3.1] Live Camera Feed Test")
    print("=" * 50)

    try:
        import cv2
        from ui.camera_feed import open_live_camera, close_live_camera, capture_from_live_camera

        print("  Testing live camera feed...")
        _m.display_tool("Live Camera", "Opening camera feed")
        _m.display_action("Starting live video stream...")

        # Open live camera
        parent = _m._boot_display.root if _m._boot_display else None
        L.camera = open_live_camera(parent=parent)

        if L.camera and L.camera.is_active():
            print("  [OK] Live camera feed started")
            _m.display_result("Live camera feed is active")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Live Camera Feed', 'status': 'OK'})
            _m.BOOT_STATUS['live_camera_available'] = True

            # Let it run for 3 seconds
            _m.display_action("Showing live feed for 3 seconds...")
            _m.responsive_sleep(3)

            # Take a test snapshot and analyze
            _m.display_action("Taking snapshot for AI analysis...")
            frame_path = capture_from_live_camera()

            if frame_path:
                print(f"  [OK] Snapshot captured: {frame_path}")
                _m.display_result("Snapshot captured successfully")

                # Analyze with AI vision
                try:
                    from ai.ollama import generate_with_image
                    _m.display_action("Analyzing camera view with AI vision...")

                    vision_result = generate_with_image(
                        prompt="What do you see through this camera? Describe the scene briefly.",
                        image_path=str(frame_path)
                    )

                    if vision_result and vision_result.content:
                        import re
                        camera_desc = vision_result.content.strip()
                        camera_desc = re.sub(r'\*\*([^*]+)\*\*', r'\1', camera_desc)
                        camera_desc = re.sub(r'\*([^*]+)\*', r'\1', camera_desc)
                        camera_desc = re.sub(r'\n+', ' ', camera_desc)
                        camera_desc = re.sub(r'\s+', ' ', camera_desc).strip()

                        print(f"  CORA sees: {camera_desc[:100]}...")
                        _m.display_result(f"Vision: {camera_desc[:80]}...")
                        _m.BOOT_STATUS['camera_description'] = camera_desc

                        # CORA announces camera + what she sees
                        response = _m.cora_respond("Live Camera", f"Camera online. I see: {camera_desc[:80]}", "ok")
                        _m.speak(response)
                    else:
                        response = _m.cora_respond("Live Camera", "Camera online but vision analysis failed.", "warn")
                        _m.speak(response)
                except Exception as e:
                    print(f"  [INFO] Vision analysis skipped: {e}")
                    response = _m.cora_respond("Live Camera", "Camera online. Vision skipped.", "ok")
                    _m.speak(response)
            else:
                response = _m.cora_respond("Live Camera", "Camera online.", "ok")
                _m.speak(response)

            # Close camera after test
            _m.display_action("Closing test camera feed...")
            close_live_camera()
            print("  [OK] Camera feed closed")

            _m.display_phase("3.1 Camera Feed", "ok")
        else:
            print("  [WARN] Live camera not available")
            _m.display_log("Live camera not available", "warn")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Live Camera Feed', 'status': 'WARN'})
            _m.BOOT_STATUS['live_camera_available'] = False
            _m.display_phase("3.1 Camera Feed", "warn")

            response = _m.cora_respond("Live Camera", "Camera not available.", "warn")
            _m.speak(response)

    except ImportError as e:
        print(f"  [WARN] Camera dependencies missing: {e}")
        _m.display_log(f"Camera dependencies: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Live Camera Feed', 'status': 'WARN'})
        _m.display_phase("3.1 Camera Feed", "warn")
    except Exception as e:
        print(f"  [WARN] Live camera test: {e}")
        _m.display_log(f"Live camera error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Live Camera Feed', 'status': 'WARN'})
        _m.display_phase("3.1 Camera Feed", "warn")

    _m.responsive_sleep(0.3)
