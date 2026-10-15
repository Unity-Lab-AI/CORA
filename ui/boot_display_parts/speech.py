#!/usr/bin/env python3
"""SpeechMixin: the speech methods of BootDisplay (split from ui/boot_display.py on 2026-10-14).
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


class SpeechMixin:

    def start_speaking(self, text: str):
        """Called when CORA starts speaking - updates UI text.

        Note: The waveform runs continuously and automatically shows waves
        when receiving audio data. No need to start/stop it.
        """
        self.is_speaking = True
        try:
            if self.current_text:
                # Show full text - no truncation
                self.current_text.config(text=f'"{text}"')
            # Log the full speech to the console
            self.log_speech(text)
        except Exception:
            pass

    def stop_speaking(self):
        """Called when CORA stops speaking - clears UI text.

        Note: The waveform runs continuously and naturally decays
        when there's no audio data.
        """
        self.is_speaking = False
        try:
            if self.current_text:
                self.current_text.config(text="")
        except:
            pass

    def _process_speech_queue(self):
        """Process TTS speech queue updates (runs on main thread)."""
        try:
            from voice.tts import process_speech_queue
            process_speech_queue()
        except ImportError:
            pass
        except Exception:
            pass
        # Schedule next check in 50ms
        if self.root and not getattr(self, '_closing', False):
            try:
                self._speech_timer_id = self.root.after(50, self._process_speech_queue)
            except:
                pass
