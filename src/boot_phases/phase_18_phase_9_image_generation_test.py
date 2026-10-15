#!/usr/bin/env python3
"""PHASE 9: IMAGE GENERATION TEST

One phase of src.boot_sequence.run_boot_sequence, split out on 2026-10-14. `_m` is the live
src.boot_sequence module (its names are read and assigned through it); `L` holds the locals
shared across phases.

2026-10-14 (evening): the picture is her selfie on her own local image engine, and it opens
in the viewer window every boot (config boot.selfie, default true) - the owner never saw it
when the demo gate kept it off."""
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

def _selfie_prompt(_m) -> str:
    """Her own idea for the moment of the selfie (picture words); her look itself comes from config
    image.selfie_look and is added by generate_image(selfie=True)."""
    try:
        from ai.ollama import generate
        r = generate(
            prompt=("Write the image prompt for a selfie you are taking right now, one line, max 30 words: "
                    "where you are, your pose and expression, the light. Picture words only, no quotes."),
            system=_m.get_system_prompt(), temperature=1.0, max_tokens=60)
        idea = (r.content or '').strip().strip('"\'')
        idea = re.sub(r'\*\*([^*]+)\*\*', r'\1', idea)
        idea = re.sub(r'\*([^*]+)\*', r'\1', idea)
        idea = re.sub(r'\s+', ' ', idea).strip()
        if 8 < len(idea) < 240:
            return idea
    except Exception as e:
        print(f"  [INFO] selfie idea skipped: {e}")
    return "at her desk, looking at the camera with a small smile"


def run(_m, L):

    # ================================================================
    # PHASE 9: IMAGE GENERATION (her selfie, on her own engine)
    # ================================================================
    _m.display_phase("9.0 Image Gen", "running")
    _m.display_log("PHASE 9: IMAGE GENERATION", "phase")
    print("\n[PHASE 9] Image Generation")
    print("=" * 50)

    try:
        from cora_tools.image_gen import generate_image, show_image, checkpoint_path, sidecar_health, ensure_sidecar
        ckpt = checkpoint_path()
        if not ckpt.exists():
            raise RuntimeError(f"image checkpoint not found: {ckpt} (config image.checkpoint)")
        ok, msg = ensure_sidecar()
        if not ok:
            raise RuntimeError(f"image engine: {msg}")
        h = sidecar_health()
        print(f"  [OK] Image engine online: {h.get('checkpoint')} on {h.get('device')} ({msg})")
        _m.display_log(f"Image engine online: local Stable Diffusion, {h.get('checkpoint')}", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Image Generation', 'status': 'OK'})
        if not bool(_m._boot_config().get('selfie', True)):
            raise _m._SkippedPhase("boot.selfie is false")

        print("  Taking her selfie...")
        _m.display_thinking("Taking a selfie...")
        _m.display_action("CORA is framing her selfie...")
        cora_prompt = _selfie_prompt(_m)
        print(f"  Selfie prompt: {cora_prompt}")
        _m.display_result(f"Selfie: {cora_prompt[:90]}")

        import random
        random_seed = random.randint(1, 999999999)
        print(f"  Seed: {random_seed}")
        _m.display_tool("Image engine", "Rendering 576x768 selfie")

        result = generate_image(prompt=cora_prompt, selfie=True, width=576, height=768, seed=random_seed)

        if result.get('success'):
            img_path = result.get('path')
            gen_time = result.get('inference_time', 0)
            print(f"  [OK] Selfie rendered: {img_path}")
            print(f"       Time: {gen_time:.1f}s")
            _m.display_result(f"Selfie rendered in {gen_time:.1f}s")
            _m.display_action(f"Saved to: {img_path}")
            _m.BOOT_STATUS['boot_image'] = img_path

            # the viewer is its own window (Save As / Open folder / Copy path); it stays open
            print("  Opening the selfie...")
            if show_image(img_path, caption=f"CORA's selfie: {cora_prompt}"):
                _m.display_result("Selfie shown in the viewer (Save As / Open folder there)")
            else:
                _m.display_log("Viewer could not open; the file is saved", "warn")

            # She looks at what she made
            image_description = None
            try:
                from ai.ollama import generate_with_image
                _m.display_action("Looking at her selfie...")
                vision_result = generate_with_image(
                    prompt="This is your selfie. Describe it in two sentences: your look, your expression, the light, the room.",
                    image_path=img_path,
                    system=_m.get_system_prompt()
                )
                if vision_result and vision_result.content:
                    image_description = vision_result.content.strip()
                    image_description = re.sub(r'\*\*([^*]+)\*\*', r'\1', image_description)
                    image_description = re.sub(r'\*([^*]+)\*', r'\1', image_description)
                    image_description = re.sub(r'\n+', ' ', image_description)
                    image_description = re.sub(r'\s+', ' ', image_description).strip()
                    print(f"  CORA sees: {image_description[:100]}...")
                    _m.display_result(f"Vision: {image_description[:80]}...")
                    _m.BOOT_STATUS['generated_image_description'] = image_description
            except Exception as e:
                print(f"  [INFO] Image vision analysis skipped: {e}")

            _m.display_phase("9.0 Image Gen", "ok")
            if image_description:
                _m.speak(image_description)
            else:
                response = _m.cora_respond("Image Generation", f"Selfie rendered in {gen_time:.1f}s and opened on screen.", "ok")
                _m.speak(response)
        else:
            L.error = result.get('error', 'Unknown error')
            print(f"  [WARN] Selfie failed: {L.error}")
            _m.display_log(f"Image generation failed: {L.error}", "warn")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Image Gen Test', 'status': 'WARN'})
            _m.display_phase("9.0 Image Gen", "warn")
            response = _m.cora_respond("Image Generation", f"Image gen failed: {L.error[:50]}", "fail")
            _m.speak(response)

    except _m._SkippedPhase as e:
        _m.display_log(f"Selfie skipped ({e})", "info")
        _m.display_phase("9.0 Image Gen", "ok")
    except Exception as e:
        print(f"  [WARN] Image generation: {e}")
        _m.display_log(f"Image generation error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Image Generation', 'status': 'WARN'})
        _m.display_phase("9.0 Image Gen", "warn")

    _m.responsive_sleep(0.3)
