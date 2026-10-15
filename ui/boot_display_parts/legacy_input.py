#!/usr/bin/env python3
"""LegacyInputMixin: the legacy_input methods of BootDisplay (split from ui/boot_display.py on 2026-10-14).
Module names of ui.boot_display are read through `_m` (imported lazily per method), so rebinding there is seen here."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import threading
import time
import math
import random
import os
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass


# Global audio buffer for sharing between TTS and waveform
# Use a class to ensure single instance across imports
import threading


class LegacyInputMixin:

    def _default_process_input(self, text: str):
        from ui import boot_display as _m
        """Legacy input processing: regex command chain with mode-based tool use
        (enabled by config.json assistant.legacy_regex)."""
        import threading
        import re

        mode = self.current_mode
        text_lower = text.lower().strip()

        # ============================================================
        # NATURAL LANGUAGE COMMAND PARSING
        # Parse user intent and execute tools directly
        # ============================================================

        def process():
            nonlocal text_lower, text

            try:
                # ----------------------------------------------------------
                # CAMERA / VISION COMMANDS
                # ----------------------------------------------------------
                camera_patterns = [
                    r'(show|open|start|run|do|test).*(camera|webcam|cam)',
                    r'camera.*(feed|test|view)',
                    r'(look|see|what.*(see|looking))',
                    r'(show|let).*(see|look)',
                ]
                if any(re.search(p, text_lower) for p in camera_patterns):
                    self.log_action("Opening camera feed...")
                    self._speak("Opening camera")
                    try:
                        from ui.camera_feed import open_live_camera, close_live_camera
                        import time

                        # Open live camera
                        camera = open_live_camera(parent=self.root)
                        if camera and camera.is_active():
                            self.log_result("Camera feed is live")

                            # Keep it open for viewing - user can close manually
                            # Or auto-close after 10 seconds if just a test
                            if 'test' in text_lower:
                                self._speak("Camera test running. Closing in 5 seconds.")
                                time.sleep(5)
                                close_live_camera()
                                self.log_result("Camera test complete")
                        else:
                            self.log_fail("Could not open camera")
                            self._speak("Camera not available")
                    except Exception as e:
                        self.log_fail(f"Camera error: {e}")
                        self._speak("Camera error")
                    return

                # ----------------------------------------------------------
                # SCREENSHOT COMMANDS
                # ----------------------------------------------------------
                screenshot_patterns = [
                    r'(take|capture|grab|get).*(screenshot|screen|snap)',
                    r'screenshot',
                    r'(show|what.*(on|is)).*(screen|display)',
                ]
                if any(re.search(p, text_lower) for p in screenshot_patterns):
                    self.log_action("Taking screenshot...")
                    try:
                        from cora_tools.screenshots import desktop
                        result = desktop()
                        if result.success:
                            self.log_result(f"Screenshot saved: {result.path}")
                            # Analyze with vision AI if user asked a question
                            if '?' in text or 'what' in text_lower or 'describe' in text_lower:
                                from ai.ollama import generate_with_image
                                prompt = text if text else "Describe what you see on this screen"
                                vision_result = generate_with_image(prompt, result.path)
                                if vision_result.content:
                                    self.log_result(vision_result.content)
                                    self._speak(vision_result.content)
                            else:
                                self._speak(f"Screenshot captured")
                        else:
                            self.log_fail(f"Screenshot failed: {result.error}")
                    except Exception as e:
                        self.log_fail(f"Screenshot error: {e}")
                    return

                # ----------------------------------------------------------
                # YOUTUBE / MUSIC / PLAY COMMANDS
                # ----------------------------------------------------------
                play_patterns = [
                    r'(play|put on|start|listen).*(music|song|youtube|video|audio)',
                    r'play\s+(.+)',
                    r'(youtube|yt)\s+(.+)',
                ]
                play_match = re.search(r'play\s+(.+)', text_lower) or re.search(r'(put on|listen to)\s+(.+)', text_lower)
                if play_match or any(re.search(p, text_lower) for p in play_patterns[:2]):
                    # Extract what to play
                    query = play_match.group(1) if play_match else text_lower.replace('play', '').replace('music', '').strip()
                    if query:
                        self.log_action(f"Searching YouTube: {query}")
                        self._speak(f"Playing {query}")
                        try:
                            # Use the YouTube/media tool
                            import subprocess
                            import shutil

                            # Check if mpv is available
                            mpv_path = shutil.which('mpv')
                            if not mpv_path:
                                # Check tools folder
                                import os
                                tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')
                                for root, dirs, files in os.walk(tools_dir):
                                    if 'mpv.exe' in files:
                                        mpv_path = os.path.join(root, 'mpv.exe')
                                        break

                            if mpv_path:
                                # yt-dlp -> mpv pipeline with list args. No shell: the query
                                # is user/STT text and must never reach a command line.
                                ytdlp = shutil.which('yt-dlp')
                                if not ytdlp:
                                    raise FileNotFoundError("yt-dlp is not installed")
                                creation = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                                dl = subprocess.Popen(
                                    [ytdlp, '-o', '-', '--quiet', f'ytsearch1:{query}'],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    creationflags=creation)
                                subprocess.Popen(
                                    [mpv_path, '--no-video', '-'],
                                    stdin=dl.stdout, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, creationflags=creation)
                                dl.stdout.close()  # let mpv own the pipe
                                self.log_result(f"Playing: {query}")
                            else:
                                self.log_fail("mpv not installed - YouTube playback unavailable")
                                self._speak("mpv media player is needed for YouTube. Check the tools folder.")
                        except Exception as e:
                            self.log_fail(f"Playback error: {e}")
                    else:
                        self._speak("What would you like me to play?")
                    return

                # ----------------------------------------------------------
                # IMAGE GENERATION COMMANDS
                # ----------------------------------------------------------
                imagine_patterns = [
                    r'(imagine|create|generate|draw|make|show me).*(image|picture|photo|art)',
                    r'(imagine|draw|create)\s+(.+)',
                ]
                imagine_match = re.search(r'(imagine|draw|create|generate)\s+(.+)', text_lower)
                if imagine_match or 'generate' in text_lower and 'image' in text_lower:
                    prompt = imagine_match.group(2) if imagine_match else text
                    if prompt:
                        self.log_action(f"Generating image: {prompt}")
                        self._speak(f"Creating {prompt}")
                        try:
                            from cora_tools.image_gen import generate_image
                            result = generate_image(prompt)
                            if result.get('success'):
                                self.log_result(f"Image saved: {result.get('path')}")
                                self._speak("Image generated")
                            else:
                                self.log_fail(f"Generation failed: {result.get('error')}")
                        except Exception as e:
                            self.log_fail(f"Image gen error: {e}")
                    return

                # ----------------------------------------------------------
                # SYSTEM INFO COMMANDS
                # ----------------------------------------------------------
                if re.search(r'(system|cpu|ram|gpu|memory|disk).*(stats|info|status|usage)', text_lower) or \
                   re.search(r'(how.*(much|many)|what).*(memory|ram|cpu|gpu|disk)', text_lower):
                    self.log_action("Getting system stats...")
                    try:
                        import psutil
                        cpu = psutil.cpu_percent(interval=0.5)
                        ram = psutil.virtual_memory()
                        disk = psutil.disk_usage('/')

                        stats = f"CPU: {cpu}%, RAM: {ram.percent}% ({ram.used // (1024**3)}GB used), Disk: {disk.percent}%"
                        self.log_result(stats)
                        self._speak(f"CPU at {cpu} percent. RAM at {ram.percent} percent. Disk at {disk.percent} percent.")
                    except Exception as e:
                        self.log_fail(f"Stats error: {e}")
                    return

                # ----------------------------------------------------------
                # TIME / DATE COMMANDS
                # ----------------------------------------------------------
                if re.search(r'(what|tell).*(time|date|day)', text_lower) or text_lower in ['time', 'date']:
                    from datetime import datetime
                    now = datetime.now()
                    time_str = now.strftime("%I:%M %p")
                    date_str = now.strftime("%A, %B %d, %Y")
                    self.log_result(f"{time_str} - {date_str}")
                    self._speak(f"It's {time_str} on {date_str}")
                    return

                # ----------------------------------------------------------
                # WEATHER COMMANDS
                # ----------------------------------------------------------
                if re.search(r'(what|how).*(weather|temperature|temp)', text_lower) or 'weather' in text_lower:
                    self.log_action("Checking weather...")
                    try:
                        from services.weather import get_weather
                        weather = get_weather()
                        if weather:
                            self.log_result(str(weather))
                            self._speak(f"It's {weather.get('temp', 'unknown')} degrees and {weather.get('condition', 'unknown')}")
                        else:
                            self._speak("Couldn't get weather info")
                    except Exception as e:
                        self.log_fail(f"Weather error: {e}")
                    return

                # ----------------------------------------------------------
                # STOP / QUIET COMMANDS
                # ----------------------------------------------------------
                if text_lower in ['stop', 'quiet', 'shut up', 'be quiet', 'silence', 'mute']:
                    self.log("Okay, I'll be quiet", 'info')
                    try:
                        from voice.tts import stop_speaking
                        stop_speaking()
                    except:
                        pass
                    return

                # ----------------------------------------------------------
                # FALL THROUGH TO AI CHAT
                # If no command matched, use AI chat
                # ----------------------------------------------------------

                # MODE: Screenshot - take screenshot, analyze with AI
                if mode == 'screenshot':
                    self.log_action("Taking screenshot...")
                    try:
                        from cora_tools.screenshots import desktop
                        result = desktop()
                        if result.success:
                            self.log_result(f"Screenshot saved: {result.path}")
                            # Analyze with vision AI
                            from ai.ollama import generate_with_image
                            prompt = text if text else "Describe what you see on this screen"
                            vision_result = generate_with_image(prompt, result.path)
                            if vision_result.content:
                                self.log_result(vision_result.content)
                                self._speak(vision_result.content)
                            else:
                                self._speak(f"Screenshot captured. {result.width} by {result.height} pixels.")
                        else:
                            self.log_fail(f"Screenshot failed: {result.error}")
                    except Exception as e:
                        self.log_fail(f"Screenshot error: {e}")
                    return

                # MODE: Vision - look through camera with AI
                elif mode == 'vision':
                    prompt = text if text else "Describe what you see"
                    self.log_action("Looking through camera...")
                    try:
                        import os
                        from pathlib import Path
                        from services import camera as _camera
                        proj_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
                        cam_path = _camera.capture_to_file(proj_dir / 'data' / 'camera' / 'see_capture.jpg')
                        if cam_path:
                            from ai.ollama import generate_with_image
                            result = generate_with_image(prompt, str(cam_path))
                            if result.content:
                                self.log_result(result.content)
                                self._speak(result.content)
                            else:
                                self.log_warn("Vision analysis failed")
                        else:
                            self.log_fail(f"Camera: {_camera.last_error() or 'no camera available'}")
                    except Exception as e:
                        self.log_fail(f"Vision error: {e}")
                    return

                # MODE: Imagine - generate image from text
                elif mode == 'imagine':
                    if text:
                        self.log_action(f"Generating image: {text}")
                        self._speak(f"Creating {text}")
                        try:
                            from cora_tools.image_gen import generate_image
                            result = generate_image(text)
                            if result.get('success'):
                                self.log_result(f"Image saved: {result.get('path')}")
                                self._speak("Image generated")
                            else:
                                self.log_fail(f"Generation failed: {result.get('error')}")
                        except Exception as e:
                            self.log_fail(f"Image gen error: {e}")
                    else:
                        self.log_warn("Please describe what image to create")
                    return

                # MODE: Tasks - task management with AI
                elif mode == 'tasks':
                    self.log_action("Loading tasks for context...")
                    task_context = ""
                    try:
                        from cora_tools.tasks import TaskManager
                        tm = TaskManager()
                        if tm.tasks:
                            task_context = f"Current tasks: {[t.get('text', '') for t in tm.tasks[:10]]}"
                    except:
                        task_context = "No tasks loaded"

                    # Send to AI with task context + conversation history
                    self.log_thinking("Thinking about your tasks...")
                    try:
                        from ai.ollama import chat
                        from ai.history import get_history
                        history = get_history()
                        system_prompt = _m.get_system_prompt()
                        if task_context:
                            system_prompt += f"\n\n{task_context}"
                        messages = history.messages_for_model(system_prompt) + \
                            [{'role': 'user', 'content': text}]
                        response = chat(
                            messages=messages,
                            system=system_prompt,
                            temperature=0.7,
                            max_tokens=300
                        )
                        if response.content:
                            history.add_exchange(text, response.content)
                            self.log_result(response.content)
                            self._speak(response.content)
                        elif response.error:
                            self.log_fail(f"AI error: {response.error}")
                    except Exception as e:
                        self.log_fail(f"Chat error: {e}")
                    return

                # DEFAULT MODE: Let AI decide what to do
                # First, ask AI if this requires image generation
                self.log_thinking("Thinking...")

                should_generate_image = False
                image_prompt = ""

                try:
                    from ai.ollama import generate

                    # Ask AI to decide if image generation is needed
                    decision = generate(
                        prompt=f'User request: "{text}"\n\nDoes this request require generating/creating/showing an image or picture? Reply with ONLY "YES: <image description>" or "NO".',
                        system="You decide if requests need image generation. Visual requests like 'show me a cat', 'draw a sunset', 'create an image of X' = YES. Questions, conversation, info requests = NO. Reply ONLY with YES: <description> or NO.",
                        temperature=0.1,
                        max_tokens=100
                    )

                    if decision.content:
                        response_text = decision.content.strip()
                        if response_text.upper().startswith("YES"):
                            should_generate_image = True
                            # Extract the image description
                            if ":" in response_text:
                                image_prompt = response_text.split(":", 1)[1].strip()
                            else:
                                image_prompt = text  # Fallback to original text
                except Exception as e:
                    pass  # If decision fails, fall through to regular chat

                if should_generate_image:
                    # Use AI-generated prompt or fall back to cleaned user text
                    prompt = image_prompt if image_prompt else text
                    self.log_action(f"Generating image: {prompt}")
                    self._speak(f"Fine, I'll make your fucking picture")
                    try:
                        from cora_tools.image_gen import generate_image
                        result = generate_image(prompt)
                        if result.get('success'):
                            self.log_result(f"Image saved: {result.get('path')}")
                            self._speak("There. Your shitty image is done.")
                            # Show the image
                            try:
                                from cora_tools.image_gen import show_fullscreen_image
                                show_fullscreen_image(result.get('path'), duration=5)
                            except:
                                pass
                        else:
                            self.log_fail(f"Generation failed: {result.get('error')}")
                            self._speak("Image generation fucked up. Try again.")
                    except Exception as e:
                        self.log_fail(f"Image gen error: {e}")
                        self._speak(f"Shit broke: {e}")
                else:
                    # Regular chat with the shared conversation history
                    self.log_thinking("Thinking...")
                    try:
                        from ai.ollama import chat, summarize
                        from ai.history import get_history
                        history = get_history()
                        system_prompt = _m.get_system_prompt()
                        if history.needs_summary(system_prompt):
                            history.fold_into_summary(summarize)
                        messages = history.messages_for_model(system_prompt) + \
                            [{'role': 'user', 'content': text}]
                        response = chat(
                            messages=messages,
                            system=system_prompt,
                            temperature=0.7,
                            max_tokens=300
                        )
                        if response.content:
                            history.add_exchange(text, response.content)
                            self.log_result(response.content)
                            self._speak(response.content)
                        elif response.error:
                            self.log_fail(f"AI error: {response.error}")
                    except Exception as e:
                        self.log_fail(f"Chat error: {e}")

            except Exception as e:
                self.log_fail(f"Error: {e}")

        # Run in thread so UI doesn't freeze
        threading.Thread(target=process, daemon=True).start()
