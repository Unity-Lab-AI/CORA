#!/usr/bin/env python3
"""
C.O.R.A GUI Application
Main application window using CustomTkinter

CLASS-001: CoraApp class that inherits from customtkinter.CTk
INT-001: Wire _process_command to cora.py command processing
"""

import customtkinter as ctk
import threading
import sys
import json
from pathlib import Path
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import panel classes
try:
    from ui.panels import TasksPanel, SettingsPanel, KnowledgePanel
    PANELS_AVAILABLE = True
except ImportError:
    PANELS_AVAILABLE = False

# Import cora command processing
try:
    import cora
    CORA_AVAILABLE = True
except ImportError:
    CORA_AVAILABLE = False

# Import emotional state
try:
    from voice.emotion import get_mood, apply_event
    EMOTION_AVAILABLE = True
except ImportError:
    EMOTION_AVAILABLE = False

# Import speech recognition
try:
    from voice.stt import SpeechRecognizer
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

# Import presence detection (webcam/vision)
try:
    from services.presence import check_human_present, capture_webcam
    PRESENCE_AVAILABLE = True
except ImportError:
    PRESENCE_AVAILABLE = False

# Import wake word detection
try:
    from voice.wake_word import create_wake_detector
    WAKE_AVAILABLE = True
except ImportError:
    WAKE_AVAILABLE = False

# Import voice commands (P1-VOICE: Wire voice_command.json reading)
try:
    from voice.commands import execute_command, load_voice_config, get_voice_config
    VOICE_COMMANDS_AVAILABLE = True
    load_voice_config()  # Load on import
except ImportError:
    VOICE_COMMANDS_AVAILABLE = False

# Import boot console
try:
    from ui.boot_console import run_boot_sequence
    BOOT_CONSOLE_AVAILABLE = True
except ImportError:
    BOOT_CONSOLE_AVAILABLE = False

# Import splash screen
try:
    from ui.splash import show_splash
    SPLASH_AVAILABLE = True
except ImportError:
    SPLASH_AVAILABLE = False

# Import system tray
try:
    from ui.system_tray import create_system_tray
    SYSTEM_TRAY_AVAILABLE = True
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False



class CoraApp(ctk.CTk):
    """Main CORA application window."""

    def __init__(self):
        super().__init__()

        # GUI ready flag - prevents TTS race condition during boot
        self.gui_ready = False

        # Window setup
        self.title("C.O.R.A - Cognitive Operations & Reasoning Assistant")
        self.geometry("900x600")
        self.minsize(700, 500)

        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self._create_sidebar()

        # Create main content area
        self._create_main_content()

        # Create status bar
        self._create_status_bar()

        # Track current panel and create panel instances
        self.current_panel = "chat"
        self.panels = {}

        # Bind events
        self.bind("<Return>", self._on_enter_pressed)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Start wake word detector
        self.wake_detector = None
        self._start_wake_detector()

        # Presence detection throttling (SLAVE2-001)
        self._presence_cache = None  # Cached PresenceResult
        self._presence_cache_time = 0  # Time of last check
        self._presence_cache_ttl = 30  # Cache for 30 seconds

        # Run boot sequence in background
        self.boot_results = {}
        self._run_boot_sequence()

        # Mark GUI as ready for TTS after mainloop starts (fixes boot TTS race condition)
        # Using after(100) ensures event loop is running before TTS can start
        self.after(100, self._set_gui_ready)

    def _run_boot_sequence(self):
        """Run the boot sequence in a background thread."""
        if not BOOT_CONSOLE_AVAILABLE:
            return

        def boot_thread():
            # Wait for GUI to be ready before TTS
            import time
            while not self.gui_ready:
                time.sleep(0.1)

            def on_log(message):
                # Log to chat display if available
                if hasattr(self, 'chat_display') and self.gui_ready:
                    self.after(0, lambda: self._append_to_chat(message, "system"))

            self.boot_results = run_boot_sequence(on_log=on_log)

        thread = threading.Thread(target=boot_thread, daemon=True)
        thread.start()

    def _set_gui_ready(self):
        """Set GUI ready flag after mainloop starts (fixes boot TTS race condition).

        This is called via self.after() to ensure the event loop is running
        before TTS can start. Prevents TTS from initializing before tkinter
        is ready to handle audio callbacks.
        """
        self.gui_ready = True

    def _create_sidebar(self):
        """Create the sidebar with navigation buttons."""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="C.O.R.A",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="Cognitive Operations\n& Reasoning Assistant",
            font=ctk.CTkFont(size=11)
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Navigation buttons
        self.btn_chat = ctk.CTkButton(
            self.sidebar, text="Chat", command=self._show_chat
        )
        self.btn_chat.grid(row=2, column=0, padx=20, pady=5)

        self.btn_tasks = ctk.CTkButton(
            self.sidebar, text="Tasks", command=self._show_tasks
        )
        self.btn_tasks.grid(row=3, column=0, padx=20, pady=5)

        self.btn_knowledge = ctk.CTkButton(
            self.sidebar, text="Knowledge", command=self._show_knowledge
        )
        self.btn_knowledge.grid(row=4, column=0, padx=20, pady=5)

        self.btn_settings = ctk.CTkButton(
            self.sidebar, text="Settings", command=self._show_settings
        )
        self.btn_settings.grid(row=5, column=0, padx=20, pady=5)

        # Theme toggle at bottom
        self.theme_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Dark Mode",
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.grid(row=11, column=0, padx=20, pady=20)
        self.theme_switch.select()  # Start in dark mode

    def _create_main_content(self):
        """Create the main content area with chat interface."""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Chat display area
        self.chat_display = ctk.CTkTextbox(
            self.main_frame,
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Text input (BLOCK-001: Replace input() with GUI text entry)
        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type a command or message...",
            font=ctk.CTkFont(size=13),
            height=40
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # Send button
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send",
            width=80,
            command=self._send_message
        )
        self.send_button.grid(row=0, column=1)

        # Voice button
        self.voice_button = ctk.CTkButton(
            self.input_frame,
            text="Mic",
            width=40,
            command=self._voice_input
        )
        self.voice_button.grid(row=0, column=2, padx=(10, 0))

        # Add welcome message
        self._add_message("CORA", "Hey. What do you need?")

    def _create_status_bar(self):
        """Create status bar at bottom."""
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 5))

        # Loading spinner label (animated dots)
        self.spinner_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(size=11),
            width=30
        )
        self.spinner_label.pack(side="left", padx=(10, 0))
        self._spinner_running = False
        self._spinner_frame = 0

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=(5, 10))

        # Camera status indicator (right side of status bar)
        self.camera_status = ctk.CTkLabel(
            self.status_bar,
            text="📷 --",
            font=ctk.CTkFont(size=11)
        )
        self.camera_status.pack(side="right", padx=10)

        # Camera check button
        self.camera_btn = ctk.CTkButton(
            self.status_bar,
            text="Check",
            width=50,
            height=20,
            command=self._check_presence
        )
        self.camera_btn.pack(side="right", padx=5)

    def _add_message(self, sender, message):
        """Add a message to the chat display."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"[{sender}]: {message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _send_message(self):
        """Handle sending a message."""
        message = self.input_entry.get().strip()
        if not message:
            return

        self._add_message("You", message)
        self.input_entry.delete(0, "end")

        # Process command in background thread (ASYNC pattern)
        self._set_status("Processing...")
        threading.Thread(
            target=self._process_command,
            args=(message,),
            daemon=True
        ).start()

    def _process_command(self, message):
        """Process a command (runs in background thread).

        INT-001: Wire to cora.py command processing
        """
        response = ""

        if not CORA_AVAILABLE:
            response = "CORA module not available. Check imports."
            self.after(0, lambda: self._add_message("CORA", response))
            self.after(0, lambda: self._set_status("Ready"))
            return

        try:
            # Capture cora.py output
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            # Parse command like cora.py does
            parts = message.split()
            if not parts:
                response = "What?"
            else:
                cmd = parts[0].lower()
                args = parts[1:]

                # Check if it's a known command
                if hasattr(cora, 'COMMANDS') and cmd in cora.COMMANDS:
                    # Call the command handler
                    handler = cora.COMMANDS[cmd]
                    tasks = cora.load_tasks()
                    handler(args, tasks)
                    response = sys.stdout.getvalue().strip()
                    if not response:
                        response = "Done."

                    # Apply emotional event for task completion
                    if EMOTION_AVAILABLE:
                        if cmd in ['done', 'complete']:
                            apply_event('task_completed')
                        elif cmd in ['add', 'new']:
                            apply_event('help_given')
                elif cmd == 'chat' or not cmd.startswith('/'):
                    # Treat as chat message
                    if hasattr(cora, 'cmd_chat'):
                        if cmd != 'chat':
                            args = [message]  # Full message as chat
                        tasks = cora.load_tasks()
                        cora.cmd_chat(args, tasks)
                        response = sys.stdout.getvalue().strip()
                        if not response:
                            response = "..."
                else:
                    response = f"Unknown command: {cmd}"

            sys.stdout = old_stdout

        except Exception as e:
            sys.stdout = old_stdout
            response = f"Error: {str(e)}"
            if EMOTION_AVAILABLE:
                apply_event('error')

        # Get mood indicator
        mood_text = ""
        if EMOTION_AVAILABLE:
            mood = get_mood()
            if mood != 'neutral':
                mood_text = f" [{mood}]"

        # Update UI from main thread
        self.after(0, lambda: self._add_message(f"CORA{mood_text}", response))
        self.after(0, lambda: self._set_status("Ready"))

    def _on_enter_pressed(self, event):
        """Handle Enter key press."""
        self._send_message()

    def _set_status(self, text):
        """Update status bar text."""
        self.status_label.configure(text=text)
        # Start or stop spinner based on status
        if text.lower() in ("processing...", "listening..."):
            self._start_spinner()
        elif text.lower() == "ready":
            self._stop_spinner()

    def _start_spinner(self):
        """Start the loading spinner animation."""
        if self._spinner_running:
            return
        self._spinner_running = True
        self._spinner_frame = 0
        self._animate_spinner()

    def _stop_spinner(self):
        """Stop the loading spinner animation."""
        self._spinner_running = False
        self.spinner_label.configure(text="")

    def _animate_spinner(self):
        """Animate the spinner with rotating dots."""
        if not self._spinner_running:
            return
        # Simple dot animation: . .. ... ....
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_label.configure(text=frames[self._spinner_frame % len(frames)])
        self._spinner_frame += 1
        self.after(100, self._animate_spinner)

    def _toggle_theme(self):
        """Toggle between dark and light mode."""
        mode = self.theme_switch.get()
        ctk.set_appearance_mode(mode)

    def _check_presence(self):
        """Check if user is present via webcam - INT-003: Wire to presence detection."""
        if not PRESENCE_AVAILABLE:
            self.camera_status.configure(text="📷 N/A")
            self._set_status("Presence detection not available - install opencv-python")
            self.after(2000, lambda: self._set_status("Ready"))
            return

        self.camera_status.configure(text="📷 ...")
        self._set_status("Checking presence...")

        # Run presence check in background
        threading.Thread(
            target=self._do_presence_check,
            daemon=True
        ).start()

    def _do_presence_check(self):
        """Perform presence check in background thread."""
        try:
            result = check_human_present()

            if result.error:
                status_text = "📷 ERR"
                msg = f"Camera error: {result.error}"
            elif result.present:
                status_text = "📷 ✓"
                msg = f"User detected (conf: {result.confidence:.0%})"
                if EMOTION_AVAILABLE:
                    apply_event('greeting', 0.1)
            else:
                status_text = "📷 ✗"
                msg = "No user detected"

            self.after(0, lambda: self.camera_status.configure(text=status_text))
            self.after(0, lambda: self._set_status(msg))
            self.after(3000, lambda: self._set_status("Ready"))

        except Exception as e:
            self.after(0, lambda: self.camera_status.configure(text="📷 ERR"))
            self.after(0, lambda: self._set_status(f"Presence error: {str(e)[:30]}"))
            self.after(2000, lambda: self._set_status("Ready"))

    def _voice_input(self):
        """Handle voice input button - INT-002: Wire to STT."""
        if not STT_AVAILABLE:
            self._set_status("Voice not available - install speech_recognition")
            self.after(2000, lambda: self._set_status("Ready"))
            return

        self._set_status("Listening...")
        self.voice_button.configure(fg_color="red", text="...")

        # Run STT in background thread
        threading.Thread(
            target=self._do_voice_recognition,
            daemon=True
        ).start()

    def _do_voice_recognition(self):
        """Perform speech recognition in background."""
        try:
            recognizer = SpeechRecognizer()
            text = recognizer.listen_once(timeout=5, phrase_limit=10)

            if text:
                # Put recognized text in input field and process
                self.after(0, lambda: self.input_entry.delete(0, "end"))
                self.after(0, lambda: self.input_entry.insert(0, text))
                self.after(0, lambda: self._set_status(f"Heard: {text[:30]}..."))
                self.after(100, self._send_message)
            else:
                self.after(0, lambda: self._set_status("Didn't catch that"))

        except Exception as e:
            self.after(0, lambda: self._set_status(f"Voice error: {str(e)[:30]}"))

        finally:
            # Reset button
            self.after(0, lambda: self.voice_button.configure(fg_color=None, text="Mic"))
            self.after(2000, lambda: self._set_status("Ready"))

    def _show_chat(self):
        """Show chat panel."""
        if self.current_panel == "chat":
            return
        self._hide_current_panel()
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.current_panel = "chat"
        self._set_status("Chat")

    def _show_tasks(self):
        """Show tasks panel."""
        if not PANELS_AVAILABLE:
            self._set_status("Panels module not available")
            return
        if self.current_panel == "tasks":
            return
        self._hide_current_panel()
        if "tasks" not in self.panels:
            self.panels["tasks"] = TasksPanel(self.main_frame)
            self._load_tasks_into_panel()
        self.panels["tasks"].grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.current_panel = "tasks"
        self._set_status("Tasks")

    def _show_knowledge(self):
        """Show knowledge panel."""
        if not PANELS_AVAILABLE:
            self._set_status("Panels module not available")
            return
        if self.current_panel == "knowledge":
            return
        self._hide_current_panel()
        if "knowledge" not in self.panels:
            self.panels["knowledge"] = KnowledgePanel(self.main_frame)
        self.panels["knowledge"].grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.current_panel = "knowledge"
        self._set_status("Knowledge")

    def _show_settings(self):
        """Show settings panel."""
        if not PANELS_AVAILABLE:
            self._set_status("Panels module not available")
            return
        if self.current_panel == "settings":
            return
        self._hide_current_panel()
        if "settings" not in self.panels:
            self.panels["settings"] = SettingsPanel(self.main_frame)
        self.panels["settings"].grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.current_panel = "settings"
        self._set_status("Settings")

    def _hide_current_panel(self):
        """Hide the current panel."""
        if self.current_panel == "chat":
            self.chat_display.grid_forget()
            self.input_frame.grid_forget()
        elif self.current_panel in self.panels:
            self.panels[self.current_panel].grid_forget()

    def _load_tasks_into_panel(self):
        """Load tasks from cora into tasks panel."""
        if "tasks" not in self.panels:
            return
        try:
            if CORA_AVAILABLE:
                tasks = cora.load_tasks()
                task_list = [{"id": t.get("id", i), "text": t.get("text", ""),
                             "priority": t.get("priority", 5), "status": t.get("status", "pending")}
                            for i, t in enumerate(tasks)]
                self.panels["tasks"].load_tasks(task_list)
        except Exception:
            pass

    def _start_wake_detector(self):
        """Start the wake word detector in background."""
        if not WAKE_AVAILABLE:
            print("[!] Wake word detection not available")
            return

        try:
            self.wake_detector = create_wake_detector(
                on_wake=self._on_wake_word,
                on_command=self._on_voice_command
            )
            if self.wake_detector.start():
                self._set_status("Wake word listening...")
                self.after(2000, lambda: self._set_status("Ready"))
            else:
                print("[!] Failed to start wake word detector")
        except Exception as e:
            print(f"[!] Wake detector error: {e}")

    def _on_wake_word(self, result):
        """Called when wake word is detected."""
        self.after(0, lambda: self._set_status("Listening..."))
        self.after(0, lambda: self.voice_button.configure(fg_color="green", text="..."))

    def _on_voice_command(self, command):
        """Called when voice command is recognized after wake word.

        P1-VOICE: Wire voice_command.json reading into main loop.
        First tries to match against voice_commands.json, then falls back to text input.
        """
        if not command:
            self.after(0, lambda: self.voice_button.configure(fg_color=None, text="Mic"))
            return

        # Try to execute as voice command first (P1-VOICE)
        if VOICE_COMMANDS_AVAILABLE:
            # Parse command - first word is the command name
            parts = command.lower().split()
            cmd_name = parts[0] if parts else ""
            cmd_args = " ".join(parts[1:]) if len(parts) > 1 else ""

            # Try to execute via voice commands module
            result = execute_command(cmd_name, cmd_args, context={'source': 'voice'})

            if result.success:
                # Voice command executed successfully
                self.after(0, lambda: self._set_status(f"Voice: {cmd_name}"))
                self.after(0, lambda: self._add_message("You (voice)", command))
                self.after(0, lambda: self._add_message("CORA", result.message))

                # Speak response if configured
                if result.should_speak:
                    try:
                        from voice.tts import queue_speak
                        queue_speak(result.message)
                    except ImportError:
                        pass

                self.after(0, lambda: self.voice_button.configure(fg_color=None, text="Mic"))
                self.after(2000, lambda: self._set_status("Ready"))
                return

        # Fall back to regular command processing
        self.after(0, lambda: self.input_entry.delete(0, "end"))
        self.after(0, lambda: self.input_entry.insert(0, command))
        self.after(0, lambda: self._set_status(f"Heard: {command[:30]}"))
        self.after(100, self._send_message)
        self.after(0, lambda: self.voice_button.configure(fg_color=None, text="Mic"))

    def _on_closing(self):
        """Handle window close."""
        if self.wake_detector:
            self.wake_detector.stop()
        self.destroy()


def main(skip_splash: bool = False):
    """Run the CORA GUI application.

    Args:
        skip_splash: If True, skip the splash screen and boot directly
    """
    system_tray = None
    
    # Create hidden root window first
    app = CoraApp()

    # Initialize system tray
    if SYSTEM_TRAY_AVAILABLE:
        def on_tray_show():
            app.deiconify()
            app.lift()
            app.focus_force()

        def on_tray_quit():
            if system_tray:
                system_tray.stop()
            app._on_closing()

        system_tray = create_system_tray(
            on_show=on_tray_show,
            on_quit=on_tray_quit,
            on_settings=lambda: None
        )
        if system_tray:
            system_tray.start()
            app.system_tray = system_tray

    if SPLASH_AVAILABLE and not skip_splash:
        # Hide main window during splash
        app.withdraw()

        def on_splash_complete():
            """Called when splash screen finishes."""
            app.deiconify()  # Show main window
            app.lift()  # Bring to front
            app.focus_force()  # Focus it

        # Show fullscreen splash with 3 second boot sequence
        splash = show_splash(
            master=app,
            fullscreen=True,
            duration=3.0,
            on_complete=on_splash_complete
        )

    app.mainloop()


def main_quick():
    """Run CORA without splash screen (for quick testing)."""
    main(skip_splash=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="C.O.R.A GUI Application")
    parser.add_argument('--no-splash', action='store_true', help='Skip splash screen')
    parser.add_argument('--quick', action='store_true', help='Quick boot (no splash)')
    args = parser.parse_args()

    main(skip_splash=args.no_splash or args.quick)
