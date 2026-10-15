#!/usr/bin/env python3
"""
C.O.R.A DPI pin (Windows).

Why (2026-10-14): on a high-DPI desktop the boot display changed size and
resolution at phase 4.0. The first import of cora_tools pulls in pyautogui,
which calls SetProcessDPIAware() for the whole process, and every Tk window
already on screen is re-rendered at the new scale ("the app closes and reopens
smaller"). Windows lets a process choose its DPI awareness exactly once, so
pinning it before the first window exists makes that later call a no-op and
the display keeps the look it started with.

    from ui.dpi import pin_process_dpi
    pin_process_dpi()        # call before any window is created
"""
import os
import sys

_pinned = False


def pin_process_dpi(level: int = 0) -> bool:
    """Set the process DPI awareness once (0 = unaware: Windows scales the
    window, the look stays constant; 1 = system aware; 2 = per-monitor).
    Later calls by any library fail silently. Returns True when the pin was
    applied by this call."""
    global _pinned
    if _pinned or sys.platform != 'win32':
        return False
    _pinned = True
    try:
        level = int(os.environ.get('CORA_DPI_AWARENESS', level))
    except ValueError:
        pass
    try:
        import ctypes
        r = ctypes.windll.shcore.SetProcessDpiAwareness(level)
        return r == 0
    except Exception:
        return False


def current_awareness() -> int:
    try:
        import ctypes
        v = ctypes.c_int()
        ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(v))
        return v.value
    except Exception:
        return -1
