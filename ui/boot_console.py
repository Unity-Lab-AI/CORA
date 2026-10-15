"""
C.O.R.A Boot Console
ASCII-style boot sequence with checkmarks and TTS narration

Per ARCHITECTURE.md v1.0.0:
- Display console log showing ALL startup checks
- CORA speaks SUMMARIZED version of each check via TTS
- Adjust tone based on time of day
"""

# Split into the ui.boot_console_parts package on 2026-10-14; this module keeps every name it always had.
from ui.boot_console_parts import _base  # noqa: F401
from ui.boot_console_parts._base import Any, Callable, Dict, EMOTION_AVAILABLE, List, Optional, PROJECT_DIR, Path, _get_default_speak_func, add_mood_flavor, apply_event, datetime, detect_emotion, get_mood, get_voice_params, json, os, run_boot_sequence, run_boot_with_tts, sys, threading, time  # noqa: F401
from ui.boot_console_parts.console import BootCheck, BootConsole  # noqa: F401
from ui.boot_console_parts.checks import create_default_boot_checks  # noqa: F401




if __name__ == "__main__":
    # Test boot sequence
    results = run_boot_sequence()
    print("\n=== RESULTS ===")
    for name, result in results.items():
        status = "PASS" if result['status'] else "FAIL"
        print(f"{name}: {status}")
