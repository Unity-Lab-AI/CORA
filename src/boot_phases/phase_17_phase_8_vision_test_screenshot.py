#!/usr/bin/env python3
"""PHASE 8: VISION TEST (Screenshot + Camera)

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
try:
    import re
except Exception:
    pass


def run(_m, L):

    # ================================================================
    # PHASE 8: VISION TEST (Screenshot + Camera)
    # ================================================================
    _m.display_phase("8.0 Vision Test", "running")
    _m.display_log("PHASE 8: VISION TEST", "phase")
    print("\n[PHASE 8] Vision System Test")
    print("=" * 50)

    # Test screenshot capture
    try:
        from cora_tools.screenshots import desktop, quick_screenshot
        print("  Testing screenshot capture...")
        _m.display_tool("Screenshots", "Capturing desktop")
        _m.display_action("Taking screenshot of current display...")

        result = desktop()
        if result.success:
            print(f"  [OK] Screenshot captured: {result.path}")
            print(f"       Resolution: {result.width}x{result.height}")
            _m.display_result(f"Screenshot: {result.width}x{result.height}")
            _m.display_action(f"Saved to: {result.path}")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Screenshot Capture', 'status': 'OK'})
            _m.BOOT_STATUS['screenshot_path'] = result.path

            # Show screenshot popup (5 seconds like image gen)
            try:
                import tkinter as tk
                from PIL import Image, ImageTk

                if not _m._popups_enabled():
                    raise _m._SkippedPhase("result popups are off (boot.popups)")
                # Use window manager for proper z-layering
                parent = _m._boot_display.root if _m._boot_display else None
                ss_window = create_image_window(
                    title="CORA - Screenshot Capture",
                    width=1280, height=720,
                    parent=parent
                )

                # Load and display screenshot
                img = Image.open(result.path)
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=ss_window)

                label = tk.Label(ss_window, image=photo, bg='black')
                label.image = photo
                label.pack(fill='both', expand=True)
                ss_window.update()
                _m.display_action("Showing screenshot for 5 seconds...")
            except _m._SkippedPhase as e:
                ss_window = None
            except Exception as e:
                print(f"  [INFO] Screenshot popup failed: {e}")
                ss_window = None

            # Use AI vision to describe what CORA sees on screen
            screen_description = None
            try:
                from ai.ollama import generate_with_image
                _m.display_action("Analyzing screenshot with AI vision...")
                vision_result = generate_with_image(
                    prompt="What do you see on this screen? Describe the specific windows, apps, content, or anything interesting. Be detailed.",
                    image_path=result.path,
                    system=_m.get_system_prompt()
                )
                if vision_result and vision_result.content:
                    screen_description = vision_result.content.strip()
                    # Clean markdown
                    screen_description = re.sub(r'\*\*([^*]+)\*\*', r'\1', screen_description)
                    screen_description = re.sub(r'\*([^*]+)\*', r'\1', screen_description)
                    screen_description = re.sub(r'\n+', ' ', screen_description)
                    screen_description = re.sub(r'\s+', ' ', screen_description).strip()
                    print(f"  CORA sees: {screen_description}")
                    _m.display_result(f"Vision: {screen_description[:80]}...")
                    _m.BOOT_STATUS['screenshot_description'] = screen_description
            except Exception as e:
                print(f"  [INFO] Vision analysis skipped: {e}")

            # CORA speaks what she sees - the actual description
            if screen_description:
                _m.speak(screen_description)
            else:
                response = _m.cora_respond("Screenshot capture", f"Screenshot {result.width}x{result.height}. Vision failed.", "warn")
                _m.speak(response)

            # Close screenshot popup after speaking
            if ss_window:
                try:
                    ss_window.destroy()
                except:
                    pass
        else:
            print(f"  [WARN] Screenshot failed: {result.error}")
            _m.display_log(f"Screenshot failed: {result.error}", "warn")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Screenshot Capture', 'status': 'WARN'})
    except Exception as e:
        print(f"  [WARN] Screenshot test: {e}")
        _m.display_log(f"Screenshot error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Screenshot Capture', 'status': 'WARN'})

    # Test camera if available - try multiple camera indices
    try:
        import cv2
        print("  Testing camera...")
        _m.display_tool("OpenCV", "Accessing camera device")

        # services.camera probes the host's devices/backends with a hard
        # timeout per attempt (config camera.*), so a stalled device cannot
        # freeze the boot the way a phone-camera virtual webcam did.
        from services import camera as _camera
        cap = None
        _m.display_action("Probing camera devices (bounded)...")
        frame = _camera.capture_frame()
        dev = _camera.working_device()
        working_index = dev[0] if dev else -1
        if frame is not None:
            _m.display_result(f"Camera {working_index} ({dev[1]}) working!")
        else:
            _m.display_action(_camera.last_error() or "No camera responded")

        if frame is not None:
            print(f"  [OK] Camera {working_index} working: {frame.shape[1]}x{frame.shape[0]}")
            _m.display_result(f"Camera {working_index}: {frame.shape[1]}x{frame.shape[0]}")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'OK'})
            _m.BOOT_STATUS['camera_available'] = True
            _m.BOOT_STATUS['camera_index'] = working_index

            # Save test frame
            cam_dir = _m.PROJECT_DIR / 'data' / 'camera'
            cam_dir.mkdir(parents=True, exist_ok=True)
            cam_path = cam_dir / 'boot_test.jpg'
            _m.display_action(f"Saving camera frame to {cam_path}")
            cv2.imwrite(str(cam_path), frame)
            print(f"       Test frame saved: {cam_path}")
            _m.display_result("Camera frame saved successfully")
            _m.BOOT_STATUS['camera_path'] = str(cam_path)

            # Show camera popup (like screenshot and image gen)
            cam_window = None
            try:
                import tkinter as tk
                from PIL import Image, ImageTk

                if not _m._popups_enabled():
                    raise _m._SkippedPhase("result popups are off (boot.popups)")
                # Use window manager for proper z-layering
                parent = _m._boot_display.root if _m._boot_display else None
                cam_window = create_image_window(
                    title="CORA - Camera View",
                    width=1280, height=720,
                    parent=parent
                )

                # Load and display camera image
                img = Image.open(cam_path)
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=cam_window)

                label = tk.Label(cam_window, image=photo, bg='black')
                label.image = photo
                label.pack(fill='both', expand=True)
                cam_window.update()
                _m.display_action("Showing camera view for 5 seconds...")
            except _m._SkippedPhase as e:
                cam_window = None
            except Exception as e:
                print(f"  [INFO] Camera popup failed: {e}")
                cam_window = None

            # Use AI vision to describe what CORA sees through camera
            camera_description = None
            try:
                from ai.ollama import generate_with_image
                _m.display_action("Analyzing camera with AI vision...")
                vision_result = generate_with_image(
                    prompt="What do you see through this camera? Describe the person, their appearance, the room, objects, or anything interesting. Be detailed and specific.",
                    image_path=str(cam_path),
                    system=_m.get_system_prompt()
                )
                if vision_result and vision_result.content:
                    camera_description = vision_result.content.strip()
                    # Clean markdown
                    camera_description = re.sub(r'\*\*([^*]+)\*\*', r'\1', camera_description)
                    camera_description = re.sub(r'\*([^*]+)\*', r'\1', camera_description)
                    camera_description = re.sub(r'\n+', ' ', camera_description)
                    camera_description = re.sub(r'\s+', ' ', camera_description).strip()
                    print(f"  CORA sees: {camera_description}")
                    _m.display_result(f"Vision: {camera_description[:80]}...")
                    _m.BOOT_STATUS['camera_description'] = camera_description
            except Exception as e:
                print(f"  [INFO] Camera vision analysis skipped: {e}")

            # CORA speaks what she sees - the actual description
            if camera_description:
                _m.speak(camera_description)
            else:
                response = _m.cora_respond("Camera system", "Camera working. Vision failed.", "warn")
                _m.speak(response)

            # Close camera popup after speaking
            if cam_window:
                try:
                    cam_window.destroy()
                except:
                    pass
            else:
                print("  [WARN] Camera opened but no frame")
                _m.display_log("Camera opened but no frame captured", "warn")
                _m.BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'WARN'})
            if cap is not None:
                cap.release()
            _m.display_action("Camera released")
        else:
            print("  [INFO] No camera detected")
            _m.display_log("No camera detected", "info")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'INFO'})
            _m.BOOT_STATUS['camera_available'] = False
    except ImportError:
        print("  [INFO] OpenCV not installed - camera unavailable")
        _m.display_log("OpenCV not installed - camera unavailable", "info")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'INFO'})
    except Exception as e:
        print(f"  [WARN] Camera test: {e}")
        _m.display_log(f"Camera error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'WARN'})

    _m.display_phase("8.0 Vision Test", "ok")
    # CORA generates her own overall vision response - natural speech
    screenshot_ok = any(t['name'] == 'Screenshot Capture' and t['status'] == 'OK' for t in _m.BOOT_STATUS['tools_tested'])
    camera_ok = _m.BOOT_STATUS.get('camera_available', False)
    if screenshot_ok and camera_ok:
        vision_result = "Screenshot and camera both online."
    elif screenshot_ok:
        vision_result = "Screenshot working, no camera."
    elif camera_ok:
        vision_result = "Camera working, screenshot failed."
    else:
        vision_result = "Vision systems failed."
    response = _m.cora_respond("Vision Systems summary", vision_result, "ok")
    _m.speak(response)
    _m.responsive_sleep(0.3)
