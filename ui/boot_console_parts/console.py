#!/usr/bin/env python3
"""ui.boot_console_parts: console (split from ui/boot_console.py on 2026-10-14)."""
from __future__ import annotations

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any
from ui.boot_console_parts import _base  # noqa: F401
from ui.boot_console_parts._base import Any, Callable, Dict, List, Optional, datetime, run_boot_sequence, time  # noqa: F401




class BootCheck:
    """Represents a single boot check item."""

    def __init__(self, name: str, check_func: Callable, tts_summary: Callable):
        self.name = name
        self.check_func = check_func
        self.tts_summary = tts_summary
        self.status = None
        self.data = None
        self.error = None

    def run(self) -> bool:
        """Run the check and return success status."""
        try:
            self.data = self.check_func()
            self.status = True
            return True
        except Exception as e:
            self.error = str(e)
            self.status = False
            return False

    def get_tts_text(self) -> str:
        """Get the TTS summary text for this check."""
        if self.status and self.data is not None:
            return self.tts_summary(self.data)
        return ""


class BootConsole:
    """ASCII boot console with checkmarks and TTS."""

    def __init__(self, speak_func: Optional[Callable] = None, on_log: Optional[Callable] = None):
        """Initialize boot console.

        Args:
            speak_func: Function to speak text (TTS)
            on_log: Callback for log messages (for GUI display)
        """
        self.speak = speak_func or (lambda x: None)
        self.on_log = on_log or print
        self.checks: List[BootCheck] = []
        self.results: Dict[str, Any] = {}

    def add_check(self, name: str, check_func: Callable, tts_summary: Callable):
        """Add a boot check."""
        self.checks.append(BootCheck(name, check_func, tts_summary))

    def log(self, message: str, status: Optional[bool] = None):
        """Log a message to the console - Advanced System Diagnostics style."""
        if status is True:
            prefix = "║  [✓]"
            suffix = ""
        elif status is False:
            prefix = "║  [✗]"
            suffix = " << ERROR"
        else:
            prefix = "║  [○]"
            suffix = "..."
        self.on_log(f"{prefix} {message}{suffix}")

    def run_boot_sequence(self) -> Dict[str, Any]:
        """Run all boot checks and return results."""
        self._print_header()

        for check in self.checks:
            self.log(f"Checking {check.name}...", None)
            success = check.run()
            self.results[check.name] = {
                'status': success,
                'data': check.data,
                'error': check.error
            }

            if success:
                self.log(f"{check.name}: {self._format_data(check.data)}", True)
                tts_text = check.get_tts_text()
                if tts_text:
                    self.speak(tts_text)
            else:
                self.log(f"{check.name}: {check.error}", False)

            time.sleep(0.1)  # Small delay for visual effect

        self._print_footer()
        return self.results

    def _print_header(self):
        """Print boot sequence header - Advanced System Diagnostics style."""
        now = datetime.now()
        header = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██████╗ ██████╗ ██████╗  █████╗     ██████╗  ██████╗  ██████╗ ████████╗  ║
║    ██╔════╝██╔═══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝  ║
║    ██║     ██║   ██║██████╔╝███████║    ██████╔╝██║   ██║██║   ██║   ██║     ║
║    ██║     ██║   ██║██╔══██╗██╔══██║    ██╔══██╗██║   ██║██║   ██║   ██║     ║
║    ╚██████╗╚██████╔╝██║  ██║██║  ██║    ██████╔╝╚██████╔╝╚██████╔╝   ██║     ║
║     ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝  ╚═════╝  ╚═════╝    ╚═╝     ║
║                                                                              ║
║            Cognitive Operations & Reasoning Assistant v2.0                   ║
║                     ADVANCED SYSTEM DIAGNOSTICS                              ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Boot initiated: {now.strftime('%Y-%m-%d %H:%M:%S')}                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
"""
        self.on_log(header)

    def _print_footer(self):
        """Print boot sequence footer - Advanced System Diagnostics style."""
        passed = sum(1 for r in self.results.values() if r['status'])
        total = len(self.results)
        failed = total - passed

        if failed == 0:
            status_line = "ALL SYSTEMS OPERATIONAL"
            status_icon = "✓"
        elif failed <= 2:
            status_line = "MINOR ISSUES DETECTED"
            status_icon = "⚠"
        else:
            status_line = "CRITICAL FAILURES"
            status_icon = "✗"

        footer = f"""
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │  DIAGNOSTICS COMPLETE                                                   │ ║
║  │                                                                         │ ║
║  │  [{status_icon}] {status_line:<50}     │ ║
║  │                                                                         │ ║
║  │  Passed: {passed:>2}/{total:<2}   Failed: {failed:>2}   Success Rate: {(passed/total*100) if total > 0 else 0:>5.1f}%           │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║  Ready for input. Type 'help' for commands.                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self.on_log(footer)
        import random
        if failed == 0:
            options = [
                "All systems nominal. Awaiting instructions.",
                "Diagnostics complete. Full operational status. Ready.",
                "Boot sequence successful. At your service.",
                "Systems green across the board. What's the mission?",
                "Initialization complete. Standing by.",
            ]
            self.speak(random.choice(options))
        elif failed == 1:
            options = [
                f"Boot complete. One subsystem degraded. Proceeding anyway.",
                f"Initialization done. Minor issue detected but operational.",
                f"Systems mostly online. One module failed. Not critical.",
            ]
            self.speak(random.choice(options))
        elif failed <= 3:
            options = [
                f"Boot finished. {failed} subsystems offline. Limited capability.",
                f"Initialization complete with {failed} failures. Check diagnostics.",
                f"{failed} components down. Core functions available.",
            ]
            self.speak(random.choice(options))
        else:
            options = [
                f"Critical state. {failed} systems failed. Recommend troubleshooting.",
                f"Major issues detected. {failed} failures. Operating in safe mode.",
                f"Boot complete but {failed} critical failures. Functionality limited.",
            ]
            self.speak(random.choice(options))

    def _format_data(self, data: Any) -> str:
        """Format data for display."""
        if isinstance(data, dict):
            return ", ".join(f"{k}={v}" for k, v in list(data.items())[:3])
        elif isinstance(data, list):
            return f"{len(data)} items"
        else:
            return str(data)[:60]
