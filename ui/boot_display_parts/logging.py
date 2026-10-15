#!/usr/bin/env python3
"""LoggingMixin: the logging methods of BootDisplay (split from ui/boot_display.py on 2026-10-14).
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


class LoggingMixin:

    def _log_entry(self, text: str, tag: str = 'info'):
        """Add an entry to the scrolling log."""
        if not self.log_text:
            return
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.config(state='normal')
            self.log_text.insert('end', f"[{timestamp}] ", 'timestamp')
            self.log_text.insert('end', f"{text}\n", tag)
            self.log_text.see('end')  # Auto-scroll to bottom
            self.log_text.config(state='disabled')
            # Force immediate update so text shows before TTS
            if self.root:
                self.root.update_idletasks()
        except:
            pass

    def log(self, text: str, level: str = 'info'):
        """Add a log entry with specified level (info, ok, warn, fail, system, speech)."""
        self._log_entry(text, level)

    def log_speech(self, text: str):
        """Log CORA's speech."""
        self._log_entry(f'CORA: "{text}"', 'speech')

    def log_system(self, text: str):
        """Log system information."""
        self._log_entry(f"[SYS] {text}", 'system')

    def log_phase(self, text: str):
        """Log phase header."""
        self._log_entry(f"{'═' * 15} {text} {'═' * 15}", 'phase')

    def log_ok(self, text: str):
        """Log success message."""
        self._log_entry(f"✓ {text}", 'ok')

    def log_warn(self, text: str):
        """Log warning message."""
        self._log_entry(f"⚠ {text}", 'warn')

    def log_fail(self, text: str):
        """Log failure message."""
        self._log_entry(f"✗ {text}", 'fail')

    def log_user(self, text: str):
        """Log user input/command."""
        self._log_entry(f"USER: {text}", 'user')

    def log_action(self, text: str):
        """Log CORA action (tool use, file operation, etc)."""
        self._log_entry(f"→ ACTION: {text}", 'action')

    def log_tool(self, tool_name: str, details: str = ""):
        """Log tool execution."""
        if details:
            self._log_entry(f"⚡ TOOL [{tool_name}]: {details}", 'action')
        else:
            self._log_entry(f"⚡ TOOL [{tool_name}]", 'action')

    def log_result(self, text: str):
        """Log action result."""
        self._log_entry(f"← RESULT: {text}", 'result')

    def log_thinking(self, text: str):
        """Log CORA's reasoning/thinking."""
        self._log_entry(f"💭 {text}", 'thinking')
