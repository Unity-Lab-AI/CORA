#!/usr/bin/env python3
"""Shared base of the ui.boot_console_parts package (split from ui/boot_console.py on 2026-10-14): imports, module
state, the helpers and every function that rebinds a module global."""
from __future__ import annotations
#!/usr/bin/env python3
"""
C.O.R.A Boot Console
ASCII-style boot sequence with checkmarks and TTS narration

Per ARCHITECTURE.md v1.0.0:
- Display console log showing ALL startup checks
- CORA speaks SUMMARIZED version of each check via TTS
- Adjust tone based on time of day
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any
PROJECT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# Import emotion detection for dynamic TTS
try:
    from voice.emotion import (
        detect_emotion,
        get_voice_params,
        apply_event,
        get_mood,
        add_mood_flavor
    )
    EMOTION_AVAILABLE = True
except ImportError:
    EMOTION_AVAILABLE = False


def run_boot_sequence(speak_func=None, on_log=None) -> Dict[str, Any]:
    from ui.boot_console_parts.console import BootConsole
    from ui.boot_console_parts.checks import create_default_boot_checks
    """Run the full boot sequence.

    Args:
        speak_func: Optional TTS function
        on_log: Optional log callback

    Returns:
        Dict of check results
    """
    # If no speak function provided, try to load TTS
    if speak_func is None:
        speak_func = _get_default_speak_func()

    console = BootConsole(speak_func=speak_func, on_log=on_log)

    for name, check_func, tts_func in create_default_boot_checks():
        console.add_check(name, check_func, tts_func)

    return console.run_boot_sequence()


def _get_default_speak_func() -> Callable:
    """Get default TTS speak function with dynamic emotion detection.

    Returns:
        Speak function or no-op lambda
    """
    # Try voice.tts with emotion detection
    try:
        from voice.tts import queue_speak

        def speak_with_emotion(text):
            """Speak with detected emotion from text."""
            emotion = 'neutral'
            if EMOTION_AVAILABLE:
                emotion = detect_emotion(text)
                # Apply greeting event at boot start for mood
                if any(w in text.lower() for w in ['hello', 'good morning', 'hey']):
                    apply_event('greeting', 0.3)
                # Apply task event for completions
                elif any(w in text.lower() for w in ['complete', 'done', 'ready', 'success']):
                    apply_event('task_completed', 0.2)
            queue_speak(text, emotion=emotion, priority=3)

        return speak_with_emotion
    except ImportError as e:
        print(f"[BOOT-CONSOLE] voice unavailable: {e}")

    # No voice available (there is no fallback voice by design)
    return lambda x: None


def run_boot_with_tts(on_log=None) -> Dict[str, Any]:
    """Run boot sequence with TTS enabled.

    Args:
        on_log: Optional log callback

    Returns:
        Dict of check results
    """
    speak = _get_default_speak_func()
    return run_boot_sequence(speak_func=speak, on_log=on_log)
