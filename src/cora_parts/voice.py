#!/usr/bin/env python3
"""src.cora_parts: voice (split from src/cora.py on 2026-10-14)."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import shutil
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from src.cora_parts import _base  # noqa: F401
from src.cora_parts._base import speak  # noqa: F401




def check_tts():
    """Check if CORA's voice (unity-voice-v2 sidecar) is reachable, starting it if needed."""
    try:
        from voice import unity_voice as uv
        ok, _msg = uv.ensure_sidecar(timeout=30)
        return ok
    except Exception:
        return False


def auto_install_kokoro():
    """Kept for callers: CORA's voice is the unity-voice-v2 sidecar now, so this
    just makes sure the sidecar is up (nothing is pip-installed)."""
    return check_tts()


def speak_kokoro(text, emotion='neutral'):
    """Legacy name - routes to her voice."""
    return speak(text)


def speak_pyttsx3(text):
    """Legacy name - routes to her voice."""
    return speak(text)


def get_tts_engine(config=None):
    """Factory kept for callers: returns the engine name when the voice is reachable."""
    if config is None:
        config = _base.CONFIG or {}
    if not config.get('tts', {}).get('enabled', True):
        return None
    return 'unity-voice-v2' if check_tts() else None


def say(text):
    """Print text and optionally speak it. Convenience function."""
    print(text)
    speak(text)


def cmd_speak(args, tasks):
    from src.cora_parts.chat import respond
    """Speak text aloud using text-to-speech. Usage: speak <text>"""
    if not args:
        respond('error', {'message': "Please provide text to speak. Usage: speak <text>"})
        return tasks

    text = ' '.join(args)
    respond('info', {'message': f"Speaking: {text}"}, speak_it=False)

    if speak(text):
        respond('info', {'message': "Done speaking."}, speak_it=False)
    else:
        respond('error', {'message': "Voice not available (unity-voice-v2 sidecar down)"})

    return tasks
