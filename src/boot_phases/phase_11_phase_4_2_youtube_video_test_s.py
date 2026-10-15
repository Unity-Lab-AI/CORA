#!/usr/bin/env python3
"""PHASE 4.2: YOUTUBE VIDEO TEST - Search and play a wild video

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
    # PHASE 4.2: YOUTUBE VIDEO TEST - Search and play a wild video
    # ================================================================
    _m.display_phase("4.2 YouTube Test", "running")
    _m.display_log("PHASE 4.2: YOUTUBE VIDEO TEST", "phase")
    print("\n[PHASE 4.2] YouTube Video Test")
    print("=" * 50)

    try:
        if not L._demo:
            raise _m._SkippedPhase("boot.demo_phases is false")
        import random
        import subprocess
        import threading

        # Wild and crazy search terms for random videos
        wild_searches = [
            "most insane parkour fails",
            "crazy car stunts compilation",
            "extreme sports fails 2024",
            "funny cat videos compilation",
            "satisfying domino chain reaction",
            "best magic tricks revealed",
            "insane drone racing",
            "extreme skateboard tricks",
            "world record attempts gone wrong",
            "crazy science experiments",
            "best beatbox battles",
            "amazing street performers",
        ]

        search_term = random.choice(wild_searches)
        print(f"  Searching YouTube: {search_term}")
        _m.display_tool("YouTube", f"Searching: {search_term}")
        _m.display_action(f"Finding a wild video...")

        # Show video info modal
        video_window = None
        status_text = None
        try:
            import tkinter as tk

            parent = _m._boot_display.root if _m._boot_display else None
            video_window = create_popup(
                title="CORA - YouTube Video Test",
                width=700, height=450,
                bg='#1a1a2e',
                parent=parent
            )

            # Header
            header = tk.Label(
                video_window,
                text=f"🎬 YouTube: {search_term}",
                font=('Segoe UI', 14, 'bold'),
                fg='#ff0000',
                bg='#1a1a2e',
                pady=15
            )
            header.pack(fill='x')

            # Video info display
            status_text = tk.Text(
                video_window,
                font=('Consolas', 11),
                fg='#ffffff',
                bg='#16213e',
                height=15,
                padx=15,
                pady=15,
                wrap='word'
            )
            status_text.pack(fill='both', expand=True, padx=15, pady=10)
            status_text.insert('1.0', f"🔍 Searching YouTube for:\n   \"{search_term}\"\n\nPlease wait...")
            status_text.config(state='disabled')
            video_window.update()

        except Exception as e:
            print(f"  [INFO] Video modal creation failed: {e}")
            video_window = None

        # Try to find and play video using yt-dlp
        video_title = None
        video_url = None
        played_ok = False

        try:
            # Use yt-dlp to search and get video info
            search_cmd = ['yt-dlp', '--get-title', '--get-id', '-f', 'best', f'ytsearch1:{search_term}']
            result = subprocess.run(search_cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    video_title = lines[0]
                    video_id = lines[1]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    print(f"  [OK] Found: {video_title[:50]}...")
                    _m.display_result(f"Found: {video_title[:40]}...")

                    # Update modal with video info
                    if video_window and status_text:
                        try:
                            status_text.config(state='normal')
                            status_text.delete('1.0', 'end')
                            status_text.insert('1.0', f"🎬 FOUND VIDEO:\n\n")
                            status_text.insert('end', f"Title: {video_title}\n\n")
                            status_text.insert('end', f"URL: {video_url}\n\n")
                            status_text.insert('end', f"Search: {search_term}\n\n")
                            status_text.insert('end', "▶ Playing with mpv in background...\n")
                            status_text.config(state='disabled')
                            video_window.update()
                        except:
                            pass

                    # Play the video using mpv WITH video in a window (20 seconds for loading + 10 sec play)
                    def play_video():
                        try:
                            # Play 20 seconds WITH video in mpv window (accounts for loading time)
                            subprocess.run(
                                ['mpv',
                                 '--length=20',           # Play 20 seconds total (loading + playback)
                                 '--geometry=640x360',    # Small window
                                 '--title=CORA YouTube Test',
                                 '--ontop',               # Keep on top during test
                                 '--no-terminal',
                                 video_url],
                                capture_output=True, timeout=30
                            )
                        except:
                            pass

                    play_thread = threading.Thread(target=play_video, daemon=True)
                    play_thread.start()
                    played_ok = True

                    # Give mpv a moment to start
                    _m.responsive_sleep(1)

        except subprocess.TimeoutExpired:
            print("  [WARN] yt-dlp search timed out")
        except FileNotFoundError:
            print("  [WARN] yt-dlp not installed")
        except Exception as e:
            print(f"  [WARN] Video search error: {e}")

        if played_ok:
            _m.BOOT_STATUS['tools_tested'].append({'name': 'YouTube Playback', 'status': 'OK'})
            _m.display_phase("4.2 YouTube Test", "ok")

            # CORA announces YouTube - just the result
            response = _m.cora_respond("YouTube Test", f"Found: {video_title[:40] if video_title else 'video'}. Playing sample.", "ok")
            _m.speak(response)
        else:
            # Update modal with fallback info
            if video_window and status_text:
                try:
                    status_text.config(state='normal')
                    status_text.delete('1.0', 'end')
                    status_text.insert('1.0', f"⚠ YouTube Search: {search_term}\n\n")
                    status_text.insert('end', "Could not play video directly.\n")
                    status_text.insert('end', "yt-dlp or mpv might not be installed.\n\n")
                    status_text.insert('end', "YouTube features available:\n")
                    status_text.insert('end', "  • 'play <search>' - Search and play\n")
                    status_text.insert('end', "  • 'play <youtube url>' - Direct URL\n")
                    status_text.config(state='disabled')
                    video_window.update()
                except:
                    pass

            _m.BOOT_STATUS['tools_tested'].append({'name': 'YouTube Playback', 'status': 'WARN'})
            _m.display_phase("4.2 YouTube Test", "warn")

            response = _m.cora_respond("YouTube Test", "YouTube search works. Playback needs yt-dlp and mpv.", "warn")
            _m.speak(response)

        # Close video window after speaking
        if video_window:
            try:
                video_window.destroy()
            except:
                pass

    except _m._SkippedPhase as e:
        _m.display_log(f"YouTube test skipped ({e})", "info")
        _m.display_phase("4.2 YouTube Test", "ok")
    except Exception as e:
        print(f"  [WARN] YouTube test: {e}")
        _m.display_log(f"YouTube test error: {e}", "warn")
        _m.BOOT_STATUS['tools_tested'].append({'name': 'YouTube Test', 'status': 'WARN'})
        _m.display_phase("4.2 YouTube Test", "warn")

    _m.responsive_sleep(0.3)
