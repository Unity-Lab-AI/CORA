#!/usr/bin/env python3
"""
C.O.R.A GUI Launcher
Integrates CustomTkinter GUI with cora.py command processing

This launcher:
1. Imports the GUI from ui/app.py
2. Hooks the GUI's message handler to cora.py commands
3. Runs the GUI main loop

Usage:
    python gui_launcher.py           # Normal launch
    python gui_launcher.py --quick   # Quick launch (skip slow init, faster startup)
    python gui_launcher.py --test    # Test mode (imports only, validates syntax)
"""

import sys
import os
import io
import argparse
import threading
from pathlib import Path
from contextlib import redirect_stdout

# Add project root to path - gui_launcher.py is in src/, so go up one level
PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / 'src'))  # Also add src/ for cora module

# Import cora.py functions
import cora

# Import GUI
from ui.app import CoraApp

# Import hotkey system
try:
    from services.hotkeys import setup_cora_hotkeys, start_hotkeys, stop_hotkeys
    HOTKEYS_AVAILABLE = True
except ImportError:
    HOTKEYS_AVAILABLE = False


class CoraGUIApp(CoraApp):
    """Extended GUI that integrates with cora.py commands."""

    def __init__(self):
        super().__init__()

        # Load tasks from cora.py
        cora.load_config()
        self.tasks = cora.load_tasks()

        # Load personality for greeting
        personality = cora.load_personality()
        greeting = cora.generate_greeting(personality)
        self._clear_and_greet(greeting)

        # Setup global hotkeys (P2-FEATURE: Hotkey system)
        self._setup_hotkeys()

    def _setup_hotkeys(self):
        """Setup global keyboard shortcuts."""
        if not HOTKEYS_AVAILABLE:
            return

        # Define hotkey callbacks that use after() for thread-safety
        def on_push_to_talk():
            self.after(0, self._trigger_voice_input)

        def on_quick_query():
            self.after(0, lambda: self.input_entry.focus_set())

        def on_toggle_cora():
            self.after(0, self._toggle_visibility)

        # Setup default hotkeys
        setup_cora_hotkeys(
            on_push_to_talk=on_push_to_talk,
            on_quick_query=on_quick_query,
            on_toggle=on_toggle_cora
        )

        # Start hotkey listener
        if start_hotkeys():
            print("[HOTKEYS] Global shortcuts active")

    def _trigger_voice_input(self):
        """Trigger voice input (same as clicking mic button)."""
        if hasattr(self, '_on_mic_click'):
            self._on_mic_click()

    def _toggle_visibility(self):
        """Toggle window visibility (minimize to tray or restore)."""
        if self.state() == 'withdrawn':
            self.deiconify()
            self.lift()
            self.focus_force()
        else:
            self.withdraw()

    def _clear_and_greet(self, greeting):
        """Clear default welcome and show personality greeting."""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.insert("end", f"[CORA]: {greeting}\n\n")
        self.chat_display.configure(state="disabled")

    def _process_command(self, message):
        """Process a command using cora.py backend."""
        cmd, args = cora.parse_input(message)

        if not cmd:
            self.after(0, lambda: self._set_status("Ready"))
            return

        # Check for exit commands
        if cmd in ('exit', 'quit', 'q'):
            self.after(0, self._on_closing)
            return

        # Build command dispatch table (same as cora.py main())
        commands = {
            'add': cora.cmd_add,
            'list': cora.cmd_list,
            'ls': cora.cmd_list,
            'done': cora.cmd_done,
            'complete': cora.cmd_done,
            'delete': cora.cmd_delete,
            'del': cora.cmd_delete,
            'remove': cora.cmd_delete,
            'rm': cora.cmd_delete,
            'pri': cora.cmd_pri,
            'priority': cora.cmd_pri,
            'due': cora.cmd_due,
            'deadline': cora.cmd_due,
            'note': cora.cmd_note,
            'status': cora.cmd_status,
            'show': cora.cmd_show,
            'view': cora.cmd_show,
            'search': cora.cmd_search,
            'find': cora.cmd_search,
            'learn': cora.cmd_learn,
            'recall': cora.cmd_recall,
            'knowledge': cora.cmd_recall,
            'kb': cora.cmd_recall,
            'stats': cora.cmd_stats,
            'count': cora.cmd_stats,
            'pull': cora.cmd_pull_model,
            'chat': cora.cmd_chat,
            'ai': cora.cmd_chat,
            'chathistory': cora.cmd_chathistory,
            'history': cora.cmd_chathistory,
            'speak': cora.cmd_speak,
            'say': cora.cmd_speak,
            'backup': cora.cmd_backup,
            'edit': cora.cmd_edit,
            'modify': cora.cmd_edit,
            'settings': cora.cmd_settings,
            'config': cora.cmd_settings,
            'help': cora.cmd_help,
            '?': cora.cmd_help,
            'today': cora.cmd_today,
            'undo': cora.cmd_undo,
            'remind': cora.cmd_remind,
            'reminder': cora.cmd_remind,
            'open': cora.cmd_open,
            'launch': cora.cmd_open,
            'run': cora.cmd_open,
            'create_tool': cora.cmd_create_tool,
            'newtool': cora.cmd_create_tool,
            'modify_tool': cora.cmd_modify_tool,
            'edittool': cora.cmd_modify_tool,
            'list_tools': cora.cmd_list_tools,
            'tools': cora.cmd_list_tools,
            'see': cora.cmd_see,
            'look': cora.cmd_see,
            'vision': cora.cmd_see,
            'camera': cora.cmd_see,
            'imagine': cora.cmd_imagine,
            'generate': cora.cmd_imagine,
            'draw': cora.cmd_imagine,
            'create': cora.cmd_imagine,
            'cli': cora.cmd_open_cli,
            'terminal': cora.cmd_open_cli,
            'popup': cora.cmd_open_cli,
        }

        # Capture stdout to display in chat
        output = io.StringIO()

        if cmd in commands:
            try:
                with redirect_stdout(output):
                    self.tasks = commands[cmd](args, self.tasks)
            except Exception as e:
                output.write(f"[Error]: {e}\n")
        else:
            output.write(f"[CORA]: Unknown command: {cmd}. Type 'help' for available commands.\n")

        # Get captured output
        response = output.getvalue().strip()
        if response:
            # Update UI from main thread
            self.after(0, lambda: self._add_message("CORA", response))

        self.after(0, lambda: self._set_status("Ready"))


def main():
    """Run the CORA GUI application with cora.py integration."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='C.O.R.A GUI Launcher')
    parser.add_argument('--quick', action='store_true',
                        help='Quick launch - skip slow initialization for faster startup')
    parser.add_argument('--test', action='store_true',
                        help='Test mode - validate imports only, do not run mainloop')
    args = parser.parse_args()

    # Test mode - just validate imports and exit
    if args.test:
        print("[OK] gui_launcher.py - All imports successful")
        print(f"[OK] PROJECT_DIR: {PROJECT_DIR}")
        print("[OK] cora module loaded")
        print("[OK] CoraApp class available")
        print("[OK] CoraGUIApp class defined")
        print("[TEST PASS] gui_launcher.py syntax and imports validated")
        return 0

    # Quick mode - skip first run setup (for faster dev iteration)
    if not args.quick:
        cora.first_run_setup()
    else:
        print("[QUICK] Skipping first_run_setup for faster startup")
        cora.load_config()  # Still need config

    # Create and run GUI
    app = CoraGUIApp()
    try:
        app.mainloop()
    finally:
        # Cleanup hotkeys on exit
        if HOTKEYS_AVAILABLE:
            stop_hotkeys()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
