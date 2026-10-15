#!/usr/bin/env python3
"""The runtime of src.boot_sequence: what ran under `if __name__ == "__main__"` there, moved
out on 2026-10-14. `_m` is the live src.boot_sequence module (its names are read and assigned
through it), so the module stays the owner of every global."""
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
import types as _types
import src.boot_phases


def main(_m):
    import argparse
    import threading

    parser = argparse.ArgumentParser(description='C.O.R.A Boot Sequence')
    parser.add_argument('--quick', '-q', action='store_true', help='Skip TTS (silent boot)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Extra verbose output')
    parser.add_argument('--mpv-missing', default='', help='Flag if mpv is missing (set by CORA.bat)')
    args = parser.parse_args()

    # Everything printed from here on is also in data/logs/cora-YYYYMMDD.log
    try:
        from ai.log import setup as _log_setup
        _lp = _log_setup('cora')
        if _lp:
            print(f"[LOG] {_lp}")
    except Exception as _e:
        print(f"[LOG] file logging unavailable: {_e}")

    # Check for missing dependencies and show modal
    mpv_missing = args.mpv_missing == '1'
    if mpv_missing:
        import tkinter as tk
        import webbrowser

        # Create custom dialog with selectable text
        dialog = tk.Tk()
        dialog.title("Missing Dependency: mpv")
        dialog.configure(bg='#1a1a1a')
        dialog.geometry("520x480")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)

        # Center on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 520) // 2
        y = (dialog.winfo_screenheight() - 480) // 2
        dialog.geometry(f"520x480+{x}+{y}")

        # Use Text widget for selectable content
        info_text = tk.Text(dialog, font=('Consolas', 10), fg='#ffffff', bg='#1a1a1a',
                           bd=0, highlightthickness=0, wrap='word', cursor='arrow',
                           height=18, width=58)
        info_text.pack(padx=20, pady=(20, 10), fill='both')

        # Configure tags for styling
        info_text.tag_configure('header', font=('Consolas', 16, 'bold'), foreground='#ffaa00', justify='center')
        info_text.tag_configure('subheader', font=('Consolas', 10), foreground='#ffffff', justify='center')
        info_text.tag_configure('warning', font=('Consolas', 10, 'bold'), foreground='#ff6666')
        info_text.tag_configure('feature', font=('Consolas', 9), foreground='#cccccc')
        info_text.tag_configure('install', font=('Consolas', 10, 'bold'), foreground='#00ff88')
        info_text.tag_configure('link', font=('Consolas', 11, 'underline'), foreground='#00aaff')
        info_text.tag_configure('dim', font=('Consolas', 9), foreground='#888888')
        info_text.tag_configure('cmd', font=('Consolas', 11, 'bold'), foreground='#00ff88', background='#333333')
        info_text.tag_configure('center', justify='center')

        # Insert content
        info_text.insert('end', "Missing: mpv Media Player\n\n", ('header', 'center'))
        info_text.insert('end', "mpv is needed for YouTube and media playback.\n\n", ('subheader', 'center'))

        info_text.insert('end', "Without mpv, these features are DISABLED:\n", 'warning')
        info_text.insert('end', "  - YouTube video playback\n", 'feature')
        info_text.insert('end', "  - Audio streaming\n", 'feature')
        info_text.insert('end', "  - Media playback commands\n\n", 'feature')

        info_text.insert('end', "To enable, download and extract mpv:\n\n", 'install')

        # Clickable link
        info_text.insert('end', "https://sourceforge.net/projects/mpv-player-windows/", 'link')
        info_text.insert('end', "\n\n")

        info_text.tag_bind('link', '<Button-1>', lambda e: webbrowser.open('https://sourceforge.net/projects/mpv-player-windows/files/64bit/'))
        info_text.tag_bind('link', '<Enter>', lambda e: info_text.config(cursor='hand2'))
        info_text.tag_bind('link', '<Leave>', lambda e: info_text.config(cursor='arrow'))

        info_text.insert('end', "Steps:\n", 'dim')
        info_text.insert('end', "  1. Download the .7z or .zip file\n", 'feature')
        info_text.insert('end', "  2. Extract to: CORA/tools/\n", 'cmd')
        info_text.insert('end', "  3. Click 'Check & Continue' below\n\n", 'feature')

        info_text.insert('end', "⚠ WARNING: Site has DECEPTIVE ADS!\n", 'warning')
        info_text.insert('end', "Click DIRECTLY on the .7z filename in the list.\n", 'dim')
        info_text.insert('end', "Do NOT click any 'Download' buttons!\n\n", 'dim')

        info_text.insert('end', "Folder structure doesn't matter - CORA will\n", 'dim')
        info_text.insert('end', "find mpv.exe anywhere inside the tools folder.\n", 'dim')

        # Make text selectable but not editable
        info_text.config(state='disabled')

        # Enable selection
        def enable_select(event):
            info_text.config(state='normal')
        def disable_edit(event):
            info_text.config(state='disabled')
            return "break"

        info_text.bind('<Button-1>', enable_select)
        info_text.bind('<Key>', disable_edit)
        info_text.bind('<Control-c>', lambda e: None)  # Allow copy

        # Button frame
        btn_frame = tk.Frame(dialog, bg='#1a1a1a')
        btn_frame.pack(pady=(10, 20))

        def open_download():
            """Open mpv download page."""
            webbrowser.open('https://sourceforge.net/projects/mpv-player-windows/files/64bit/')
            download_btn.config(text="Opening...", bg='#00aaff')
            status_label.config(text="Download, extract to CORA/tools/, then click Check & Continue", fg='#00aaff')

        def check_mpv_and_continue():
            """Check if mpv is installed - if found, close dialog and continue boot."""
            import subprocess
            import shutil
            import os

            check_btn.config(text="Checking...", state='disabled')
            dialog.update()

            found = False
            mpv_location = None

            # Check system PATH
            mpv_path = shutil.which('mpv')
            if mpv_path:
                found = True
                mpv_location = mpv_path
                # Verify it runs
                try:
                    result = subprocess.run([mpv_path, '--version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version = result.stdout.split('\n')[0] if result.stdout else ""
                        status_label.config(text=f"Found: {version}", fg='#00ff88')
                except:
                    status_label.config(text=f"Found at: {mpv_path}", fg='#00ff88')

            # Check CORA tools folder (including subdirectories)
            if not found:
                cora_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                mpv_tools_dir = os.path.join(cora_dir, 'tools', 'mpv')

                # First check direct path
                mpv_local = os.path.join(mpv_tools_dir, 'mpv.exe')
                if os.path.exists(mpv_local):
                    found = True
                    mpv_location = mpv_local
                    os.environ['PATH'] = os.path.dirname(mpv_local) + os.pathsep + os.environ.get('PATH', '')
                    status_label.config(text=f"Found in CORA/tools/mpv/", fg='#00ff88')
                else:
                    # Search subdirectories for mpv.exe
                    if os.path.exists(mpv_tools_dir):
                        for root, dirs, files in os.walk(mpv_tools_dir):
                            if 'mpv.exe' in files:
                                mpv_local = os.path.join(root, 'mpv.exe')
                                found = True
                                mpv_location = mpv_local
                                os.environ['PATH'] = root + os.pathsep + os.environ.get('PATH', '')
                                status_label.config(text=f"Found in tools/mpv/", fg='#00ff88')
                                break

            # Check common install locations
            if not found:
                common_paths = [
                    os.path.expandvars(r'%LOCALAPPDATA%\Programs\mpv\mpv.exe'),
                    os.path.expandvars(r'%ProgramFiles%\mpv\mpv.exe'),
                    os.path.expandvars(r'%ProgramFiles(x86)%\mpv\mpv.exe'),
                    r'C:\mpv\mpv.exe',
                    os.path.expanduser(r'~\scoop\apps\mpv\current\mpv.exe'),
                ]

                for path in common_paths:
                    if os.path.exists(path):
                        found = True
                        mpv_location = path
                        os.environ['PATH'] = os.path.dirname(path) + os.pathsep + os.environ.get('PATH', '')
                        status_label.config(text=f"Found at: {path}", fg='#00ff88')
                        break

            if found:
                # mpv found! Show success and close dialog to continue boot
                check_btn.config(text="Found!", bg='#00ff88')
                status_label.config(text="mpv detected! Continuing boot...", fg='#00ff88')
                dialog.update()
                dialog.after(1500, dialog.destroy)  # Close after 1.5 seconds
            else:
                # Not found
                check_btn.config(text="Not Found", bg='#ff6666', state='normal')
                status_label.config(text="mpv not detected. Install it or click Skip.", fg='#ff6666')

        def open_download():
            """Open mpv download page."""
            webbrowser.open('https://sourceforge.net/projects/mpv-player-windows/files/64bit/')
            download_btn.config(text="Opening...", bg='#00aaff')
            status_label.config(text="Download, extract to CORA/tools/mpv/, then click Check & Continue", fg='#00aaff')

        download_btn = tk.Button(btn_frame, text="Download mpv", font=('Consolas', 11, 'bold'),
                               fg='#000000', bg='#00ff88', activebackground='#00cc66', bd=0,
                               padx=15, pady=8, command=open_download)
        download_btn.pack(side='left', padx=5)

        check_btn = tk.Button(btn_frame, text="Check & Continue", font=('Consolas', 11, 'bold'),
                             fg='#000000', bg='#00aaff', activebackground='#0088cc', bd=0,
                             padx=15, pady=8, command=check_mpv_and_continue)
        check_btn.pack(side='left', padx=5)

        tk.Button(btn_frame, text="Skip", font=('Consolas', 11, 'bold'),
                 fg='#000000', bg='#ff00ff', activebackground='#cc00cc', bd=0,
                 padx=15, pady=8, command=dialog.destroy).pack(side='left', padx=5)

        # Status label for install feedback
        status_label = tk.Label(dialog, text="", font=('Consolas', 9), fg='#888888', bg='#1a1a1a')
        status_label.pack(pady=(0, 10))

        dialog.mainloop()

    # Boot result storage
    boot_result = {'done': False, 'result': None}

    def run_boot_in_thread():
        """Run boot sequence in background thread."""
        try:
            if args.quick:
                boot_result['result'] = _m.quick_boot()
            else:
                boot_result['result'] = _m.full_boot()
        except Exception as e:
            print(f"[BOOT ERROR] {e}")
            boot_result['result'] = {'systems': [], 'tools_tested': [], 'errors': [str(e)]}
        finally:
            boot_result['done'] = True
            _m._boot_complete = True

            # Print final stats
            result = boot_result['result']
            if result:
                ok = len([s for s in result.get('systems', []) if s.get('status') == 'OK'])
                total = len(result.get('systems', []))
                tools = len([t for t in result.get('tools_tested', []) if t.get('status') == 'OK'])
                total_tools = len(result.get('tools_tested', []))
                print(f"\n[BOOT COMPLETE] Systems: {ok}/{total} | Tools: {tools}/{total_tools}")

            # Switch to operational monitoring mode
            if _m._boot_display:
                _m._safe_ui_call(lambda: _m._boot_display.switch_to_operational_mode())

            # Start STT after boot
            start_stt()

    def start_stt():
        """Start speech-to-text after boot completes."""
        try:
            from voice.stt import WakeWordDetector, SpeechRecognizer
            from voice.echo_filter import get_echo_filter

            echo_filter = get_echo_filter(filter_duration=3.0)

            # Debounce: track last wake word time to prevent double triggers
            last_wake_time = [0]  # Use list to allow mutation in closure
            DEBOUNCE_SECONDS = 2.0

            # Reuse recognizer for faster response
            recognizer = SpeechRecognizer()
            recognizer.initialize()

            def on_wake_word():
                import time as time_module

                # Debounce check - ignore if triggered too recently
                current_time = time_module.time()
                if current_time - last_wake_time[0] < DEBOUNCE_SECONDS:
                    print("[STT] Ignoring duplicate wake word (debounce)")
                    return
                last_wake_time[0] = current_time

                # Check if CORA is speaking
                if echo_filter and echo_filter.is_speaking():
                    print("[STT] Ignoring wake word - CORA is speaking")
                    return

                print("[STT] Wake word detected!")

                # Log that user said "CORA"
                if _m._boot_display:
                    _m._safe_ui_call(lambda: _m._boot_display.log_user("CORA..."))

                try:
                    # Small delay to let wake word audio clear from buffer
                    time_module.sleep(0.15)

                    # NOW show listening indicator (after buffer is ready)
                    if _m._boot_display:
                        _m._safe_ui_call(lambda: _m._boot_display.log("Listening...", 'info'))

                    # Listen for command
                    text = recognizer.listen_once(timeout=5, phrase_limit=10)

                    if text.strip():
                        if echo_filter and not echo_filter.should_process(text):
                            print(f"[STT] Ignoring echo: {text}")
                            return
                        print(f"[STT] Heard: {text}")
                        if _m._boot_display:
                            _m._safe_ui_call(lambda: _m._boot_display._process_user_input(text))
                    else:
                        print("[STT] No speech detected")
                        if _m._boot_display:
                            _m._safe_ui_call(lambda: _m._boot_display.log("Didn't catch that", 'warn'))
                except Exception as e:
                    print(f"[STT] Listen error: {e}")

            wake_detector = WakeWordDetector(wake_word="cora")
            wake_detector.start(on_wake_word)
            print("[STT] Wake word detection active - say 'CORA' to speak")
            if _m._boot_display:
                _m._safe_ui_call(lambda: _m._boot_display.log("Voice active - say 'CORA' to speak", 'ok'))

            # Start ambient awareness - CORA monitors and can interject naturally
            start_ambient_awareness(wake_detector)

        except Exception as e:
            print(f"[STT] Voice detection unavailable: {e}")
            if _m._boot_display:
                _m._safe_ui_call(lambda: _m._boot_display.log(f"Voice detection unavailable: {e}", 'warn'))

    def start_ambient_awareness(wake_detector):
        """Start CORA's ambient awareness - she monitors and interjects naturally."""
        try:
            from voice.ambient_awareness import get_ambient_awareness, InterjectReason
            from voice.stt import WakeWordDetector

            def on_ambient_interject(context_json: str, reason: InterjectReason):
                """Handle CORA deciding to interject on her own."""
                import json

                try:
                    context = json.loads(context_json)
                    hint = context.get('hint', '')
                    recent_speech = context.get('recent_speech', '')
                    user_activity = context.get('user_activity', '')
                    user_mood = context.get('user_mood', '')

                    # Build context for natural AI response - DON'T include instructions in the speech
                    # The key is to give context but let AI respond naturally
                    if reason == InterjectReason.HELPFUL_INFO:
                        context_info = f"Overheard: {recent_speech[:100]}"
                    elif reason == InterjectReason.JOKE:
                        context_info = f"Good moment for humor about: {hint[:50]}"
                    elif reason == InterjectReason.CHECK_IN:
                        context_info = f"User seems: {hint[:50]}"
                    elif reason == InterjectReason.VIBE:
                        context_info = f"Vibing, noticed: {hint[:50]}"
                    elif reason == InterjectReason.COMMENT:
                        context_info = f"Overheard interesting: {recent_speech[:80]}"
                    elif reason == InterjectReason.ALERT:
                        context_info = f"Important: {hint[:50]}"
                    else:
                        context_info = hint[:50]

                    # Log that CORA is interjecting
                    if _m._boot_display:
                        _m._safe_ui_call(lambda: _m._boot_display.log(f"[Ambient] {reason.value}: {hint[:50]}...", 'info'))

                    # Generate CORA's response using direct AI call (not cora_respond which adds boot context)
                    try:
                        from ai.ollama import generate

                        # Simple direct prompt - let CORA be natural
                        system = """You are CORA. Respond naturally in 1 short sentence. Be casual like a friend.
Don't repeat the context - just respond to it naturally. No quotes around your response."""

                        if reason == InterjectReason.HELPFUL_INFO:
                            prompt = f"You overheard '{recent_speech}'. Say something helpful briefly."
                        elif reason == InterjectReason.CHECK_IN:
                            prompt = f"User seems {hint}. Check in casually."
                        elif reason == InterjectReason.COMMENT:
                            prompt = f"You heard mention of '{recent_speech}'. Make a quick comment."
                        elif reason == InterjectReason.VIBE:
                            prompt = f"You're chilling with user. Say something friendly."
                        else:
                            prompt = f"Respond naturally to: {context_info}"

                        # her own persona + the one-line brief (generate returns an OllamaResponse)
                        response = generate(prompt=prompt, system=_m.get_system_prompt() + "\n\n" + system, max_tokens=60)
                        line = (response.content or '').strip().strip('"') if response and not response.error else ''

                        # Speak the interjection
                        if line:
                            _m.speak(line)
                    except Exception as ai_err:
                        print(f"[AMBIENT] AI generation error: {ai_err}")

                except Exception as e:
                    print(f"[AMBIENT] Interjection error: {e}")

            # Get ambient awareness with friend threshold from settings
            ambient = get_ambient_awareness(friend_threshold=0.5)

            def ambient_transcript_handler(text):
                """Feed transcripts to ambient awareness - except the wake word and
                the command that follows it (those are hers to answer properly),
                and anything heard while she is already working on a request."""
                import time as _t
                low = (text or '').lower()
                try:
                    if 'cora' in low or _t.time() - float(getattr(WakeWordDetector, 'last_wake_time', 0.0)) < 20.0:
                        return
                    from ai.dispatcher import get_dispatcher
                    if get_dispatcher()._lock.locked():
                        return
                except Exception:
                    pass
                # Update ambient awareness with what we're hearing
                ambient.update_audio_context(text)

            # Register the ambient awareness to receive all transcripts
            WakeWordDetector.add_transcript_callback(ambient_transcript_handler)

            # Start ambient monitoring
            ambient.start(on_ambient_interject)

            print("[AMBIENT] Ambient awareness active - CORA is listening and watching")
            if _m._boot_display:
                _m._safe_ui_call(lambda: _m._boot_display.log("Ambient awareness active", 'ok'))

        except Exception as e:
            print(f"[AMBIENT] Ambient awareness unavailable: {e}")
            if _m._boot_display:
                _m._safe_ui_call(lambda: _m._boot_display.log(f"Ambient awareness: {e}", 'warn'))

    # Create display first (must be on main thread for tkinter)
    # IMPORTANT: Must use ui.boot_display to get same singleton as tts.py
    from ui.boot_display import BootDisplay
    _m._boot_display = BootDisplay()
    _m._boot_display.create_window()
    # Waveform starts automatically in create_window() and runs continuously

    # Register display with TTS for speech text updates
    try:
        from voice.tts import set_boot_display
        set_boot_display(_m._boot_display)
    except ImportError:
        pass

    # Set up phases - short names with phase numbers
    phase_names = [
        "0.8 Waveform Init",
        "0.9 About CORA",
        "1.0 Voice Synthesis",
        "2.0 AI Engine",
        "2.1 AI Models",
        "3.0 Hardware Check",
        "3.1 Camera Feed",
        "4.0 Core Tools",
        "4.5 Daily Briefing",
        "4.1 Code Import",
        "4.2 YouTube Test",
        "4.3 Modal Windows",
        "5.0 Voice Systems",
        "6.0 External APIs",
        "6.1 Audio Test",
        "7.0 News Headlines",
        "8.0 Vision Test",
        "9.0 Image Gen",
        "10.0 Final Check"
    ]
    _m._boot_display.set_phases(phase_names)
    _m._boot_display.log_system("Visual boot display initialized")
    _m._boot_display.log_system(f"Boot started at {time.strftime('%H:%M:%S')}")

    # Start boot in background thread
    boot_thread = threading.Thread(target=run_boot_in_thread, daemon=True)
    boot_thread.start()

    # Run tkinter mainloop on main thread (keeps UI responsive)
    print("[MAIN] Starting UI mainloop - boot running in background")
    if _m._boot_display and _m._boot_display.root:
        try:
            _m._boot_display.run()  # This runs the tkinter mainloop
        except Exception as e:
            print(f"[ERROR] Mainloop error: {e}")
    else:
        print("\n[WARNING] Boot display not available")
