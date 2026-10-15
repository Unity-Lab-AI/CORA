#!/usr/bin/env python3
"""PHASE 9: IMAGE GENERATION TEST

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
    # PHASE 9: IMAGE GENERATION TEST
    # ================================================================
    _m.display_phase("9.0 Image Gen", "running")
    _m.display_log("PHASE 9: IMAGE GENERATION", "phase")
    print("\n[PHASE 9] Image Generation Test")
    print("=" * 50)

    try:
        from cora_tools.image_gen import generate_image, show_fullscreen_image
        print("  [OK] Image generation module loaded (Pollinations)")
        _m.display_log("Pollinations image module loaded", "ok")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Image Generation', 'status': 'OK'})
        if not L._demo:
            raise _m._SkippedPhase("boot.demo_phases is false")

        # Have CORA generate her own unique prompt using Ollama
        print("  Asking CORA for a fucked up image idea...")
        _m.display_thinking("Creating something dark and twisted...")

        import random
        random_seed = random.randint(1, 999999999)
        cora_prompt = None

        try:
            from ai.ollama import generate

            _m.display_action("CORA is dreaming up something disturbing...")
            result = generate(
                prompt="Generate a fucked up crazy image thats disturbing",
                system=_m.get_system_prompt(),
                temperature=1.2,
                max_tokens=60
            )

            if result.content and len(result.content) > 10:
                cora_prompt = result.content.strip()
                # Clean up the prompt
                cora_prompt = cora_prompt.strip('"\'').strip()
                cora_prompt = re.sub(r'\*\*([^*]+)\*\*', r'\1', cora_prompt)
                cora_prompt = re.sub(r'\*([^*]+)\*', r'\1', cora_prompt)
                cora_prompt = re.sub(r'\n+', ' ', cora_prompt)
                cora_prompt = re.sub(r'\s+', ' ', cora_prompt).strip()
                print(f"  CORA's vision: {cora_prompt}")
                _m.display_result(f"Vision: {cora_prompt}")
        except Exception as e:
            print(f"  [INFO] AI prompt generation skipped: {e}")

        # Fallback if AI fails
        if not cora_prompt:
            cora_prompt = "Generate a fucked up crazy image thats disturbing"
            print(f"  Using fallback prompt")

        print(f"  Seed: {random_seed}")

        print("  Generating via Pollinations Flux model...")
        _m.display_tool("Pollinations API", f"Generating 1280x720 image")
        _m.display_action(f"Prompt: {cora_prompt}")

        result = generate_image(
            prompt=cora_prompt,
            width=1280,
            height=720,
            seed=random_seed
        )

        if result.get('success'):
            img_path = result.get('path')
            gen_time = result.get('inference_time', 0)
            print(f"  [OK] Image generated: {img_path}")
            print(f"       Time: {gen_time:.1f}s")
            _m.display_result(f"Image generated in {gen_time:.1f}s")
            _m.display_action(f"Saving to: {img_path}")
            _m.BOOT_STATUS['boot_image'] = img_path

            print("  Displaying image...")
            _m.display_action("Opening image display window...")

            # Show image in a window
            img_window = None
            try:
                import tkinter as tk
                from PIL import Image, ImageTk

                if not _m._popups_enabled():
                    raise _m._SkippedPhase("result popups are off (boot.popups)")
                # Use window manager for proper z-layering
                parent = _m._boot_display.root if _m._boot_display else None
                img_window = create_image_window(
                    title="CORA - Image Generation Test",
                    width=1280, height=720,
                    parent=parent
                )

                # Load and display image
                img = Image.open(img_path)
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=img_window)

                label = tk.Label(img_window, image=photo, bg='black')
                label.image = photo  # Keep reference
                label.pack(fill='both', expand=True)

                img_window.update()
                _m.display_result("Image displayed successfully")

            except _m._SkippedPhase as e:
                img_window = None
            except Exception as e:
                print(f"  [INFO] Image display skipped: {e}")
                _m.display_log(f"Image display skipped: {e}", "info")
                img_window = None

            # Use AI vision to describe what CORA actually generated
            image_description = None
            try:
                from ai.ollama import generate_with_image
                _m.display_action("Analyzing generated image with AI vision...")
                vision_result = generate_with_image(
                    prompt="Describe this image in detail. What do you see? Be specific about the scene, objects, colors, mood, and style.",
                    image_path=img_path,
                    system=_m.get_system_prompt()
                )
                if vision_result and vision_result.content:
                    image_description = vision_result.content.strip()
                    # Clean markdown
                    image_description = re.sub(r'\*\*([^*]+)\*\*', r'\1', image_description)
                    image_description = re.sub(r'\*([^*]+)\*', r'\1', image_description)
                    image_description = re.sub(r'\n+', ' ', image_description)
                    image_description = re.sub(r'\s+', ' ', image_description).strip()
                    print(f"  CORA sees: {image_description[:100]}...")
                    _m.display_result(f"Vision: {image_description[:80]}...")
                    _m.BOOT_STATUS['generated_image_description'] = image_description
            except Exception as e:
                print(f"  [INFO] Image vision analysis skipped: {e}")

            # CORA speaks what she sees in the generated image
            _m.display_phase("9.0 Image Gen", "ok")
            if image_description:
                _m.speak(image_description)
            else:
                response = _m.cora_respond("Image Generation", f"Image generated in {gen_time:.1f}s. Vision failed.", "warn")
                _m.speak(response)

            # Close image window after speaking
            if img_window:
                try:
                    img_window.destroy()
                except:
                    pass
        else:
            L.error = result.get('error', 'Unknown error')
            print(f"  [WARN] Image generation failed: {L.error}")
            _m.display_log(f"Image generation failed: {L.error}", "warn")
            _m.BOOT_STATUS['tools_tested'].append({'name': 'Image Gen Test', 'status': 'WARN'})
            _m.display_phase("9.0 Image Gen", "warn")
            # Image gen failed
            response = _m.cora_respond("Image Generation", f"Image gen failed: {L.error[:50]}", "fail")
            _m.speak(response)

    except _m._SkippedPhase as e:
        _m.display_log(f"Image generation test skipped ({e})", "info")
        _m.display_phase("9.0 Image Gen", "ok")
    except Exception as e:
        print(f"  [WARN] Image generation: {e}")
        _m.display_log(f"Image generation error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'Image Generation', 'status': 'WARN'})
        _m.display_phase("9.0 Image Gen", "warn")

    _m.responsive_sleep(0.3)
