#!/usr/bin/env python3
"""
C.O.R.A Boot Sequence - F-100 Fighter Jet Style
Sequential system initialization narrated in CORA's own voice (unity-voice-v2).

Tests all tools and announces each system as it comes online.
The user hears EVERY component boot up through her voice sidecar.

Demo phases (GitHub code import, YouTube test, modal test, audio test,
image generation) run only when config.json `boot.demo_phases` is true; the
default boot is the spec'd one: voice, AI, hardware, camera, core tools, the
day's calendar / tasks / reminders, voice systems, location + weather, news,
vision, final check.

Created by: Unity AI Lab
"""

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

# Add project paths
PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / 'src'))
sys.path.insert(0, str(PROJECT_DIR / 'ui'))

# The process picks its DPI awareness once, here, before the display exists: a later import
# (pyautogui at phase 4.0) used to flip it and the window re-rendered at another size.
from ui.dpi import pin_process_dpi
pin_process_dpi()


_shutting_down = False


def _orderly_shutdown():
    """Stop what we own (voice, ears, ambient awareness, window). Each step is
    bounded and best-effort; nothing here can hang the exit."""
    global _shutting_down, _boot_display
    if _shutting_down:
        return
    _shutting_down = True
    print("\n[CORA] Shutting down...")
    for step in (
        lambda: __import__('voice.tts', fromlist=['stop_speaking']).stop_speaking(),
        lambda: __import__('voice.tts', fromlist=['get_tts_queue']).get_tts_queue().stop(),
        lambda: __import__('voice.ambient_awareness', fromlist=['stop_ambient_monitoring']).stop_ambient_monitoring(),
        lambda: _boot_display.close() if _boot_display else None,
        lambda: __import__('ai.ollama', fromlist=['unload_models']).unload_models(),   # her models leave the GPU
    ):
        try:
            step()
        except Exception:
            pass


def shutdown_handler(signum=None, frame=None):
    """Signals (Ctrl+C, SIGTERM, Ctrl+Break): clean up, then leave. The hard
    exit is a 3 s safety net for a thread stuck in a C call, not the exit path."""
    _orderly_shutdown()
    if signum is not None:
        threading.Timer(3.0, lambda: os._exit(0)).start()
        raise SystemExit(0)


# Normal interpreter exit: just the cleanup (no os._exit at atexit; that killed
# the process before Tk, the voice queue and the log file could finish)
atexit.register(_orderly_shutdown)
signal.signal(signal.SIGINT, shutdown_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, shutdown_handler)  # Termination
if sys.platform == 'win32':
    signal.signal(signal.SIGBREAK, shutdown_handler)  # Ctrl+Break on Windows

# Visual boot display
_boot_display = None
_boot_complete = False  # Flag to stop display update thread

# Boot status tracking
BOOT_STATUS: Dict[str, Any] = {
    'systems': [],
    'tools_tested': [],
    'errors': [],
    'start_time': None,
    'end_time': None,
    'weather': None,
    'location': None,
    'cpu_percent': 0,
    'memory_percent': 0,
    'disk_percent': 0,
    'gpu_available': False,
    'gpu_name': None,
}

# Global TTS engine
_tts_engine = None

# Reminder scheduler (started in Phase 4.5 so reminders actually fire)
_reminder_manager = None


class _SkippedPhase(Exception):
    """Raised inside a demo phase when boot.demo_phases is off."""


# Cache for system prompt
_system_prompt_cache = None


def responsive_sleep(seconds: float):
    """Sleep while keeping the UI responsive (allows window dragging)."""
    global _boot_display
    end_time = time.time() + seconds
    while time.time() < end_time:
        if _boot_display and _boot_display.root:
            try:
                _boot_display.root.update_idletasks()
                _boot_display.root.update()
            except tk.TclError:
                break
        time.sleep(0.01)  # 100 FPS update rate


def get_system_prompt() -> str:
    """Load CORA's personality-only system prompt from config/system_prompt.txt."""
    global _system_prompt_cache
    if _system_prompt_cache is not None:
        return _system_prompt_cache

    system_prompt_path = PROJECT_DIR / 'config' / 'system_prompt.txt'
    if system_prompt_path.exists():
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            _system_prompt_cache = f.read()
    else:
        _system_prompt_cache = ""
    return _system_prompt_cache


# Separate cache for tools prompt
_tools_prompt_cache = None


def get_tools_prompt() -> str:
    """Load CORA's tools/commands from config/tools_prompt.txt.

    This is kept separate from personality so it can be sent after boot
    and doesn't bleed into boot phase responses.
    """
    global _tools_prompt_cache
    if _tools_prompt_cache is not None:
        return _tools_prompt_cache

    tools_prompt_path = PROJECT_DIR / 'config' / 'tools_prompt.txt'
    if tools_prompt_path.exists():
        with open(tools_prompt_path, 'r', encoding='utf-8') as f:
            _tools_prompt_cache = f.read()
    else:
        _tools_prompt_cache = ""
    return _tools_prompt_cache


def get_full_prompt() -> str:
    """Get combined system prompt + tools prompt for post-boot use."""
    return get_system_prompt() + "\n\n" + get_tools_prompt()


def _boot_config() -> Dict[str, Any]:
    """config.json `boot` block (demo_phases, github_import, ...)."""
    try:
        from ai import config as _config
        return _config.section('boot')
    except Exception:
        return {}


def _popups_enabled() -> bool:
    """Result windows (screenshot / camera / generated image) during boot are
    opt-in: a 1280x720 capture of the desktop centred over the app read as
    "CORA reopened smaller". Results are always logged and spoken."""
    return bool(_boot_config().get('popups', False))


def _app_version() -> str:
    try:
        from ai import config as _config
        return _config.version()
    except Exception:
        return '3.0.0'


def init_tts():
    """Bring up CORA's own voice (unity-voice-v2 sidecar) - FIRST THING THAT BOOTS."""
    global _tts_engine
    print("\n[BOOT] ========== VOICE SYNTHESIS INITIALIZATION ==========")
    print("[BOOT] Connecting to unity-voice-v2 ...")

    try:
        from voice.tts import get_tts_queue, voice_status
        q = get_tts_queue()          # starts the sidecar if needed
        status = voice_status()
        if q.engine and q.engine.is_initialized:
            _tts_engine = q.engine
            print(f"[BOOT] unity-voice-v2 online at {status['url']}")
            print("[BOOT] ========== VOICE ONLINE ==========\n")

            # FIRST THING USER HEARS - her voice announcing itself
            speak("Voice synthesis online. My own voice, version two, loaded and ready.")
            responsive_sleep(0.3)
            return True
        err = getattr(q.engine, 'last_error', None) if q.engine else 'engine missing'
        print(f"[BOOT] [FAIL] unity-voice-v2 unavailable: {err}")
        return False

    except Exception as e:
        print(f"[BOOT] [FAIL] TTS init error: {e}")
        return False


def speak(text: str, blocking: bool = True, emotion: str = None):
    """Speak text in CORA's voice and update the visual display.

    Args:
        text: Text to speak
        blocking: If True, wait for speech to finish (keeping Tk responsive).
        emotion: Optional emotion label; detected from the text when omitted.
    """
    global _boot_display
    if not text:
        return
    print(f"[CORA] {text}")

    # Mark echo filter that we're speaking (prevents hearing ourselves)
    try:
        from voice.echo_filter import get_echo_filter
        echo_filter = get_echo_filter()
        word_count = len(text.split())
        duration = max(1.0, word_count * 0.4)
        echo_filter.start_speaking(duration=duration, text=text)
    except Exception:
        pass

    if emotion is None:
        try:
            from voice.emotion import detect_emotion
            emotion = detect_emotion(text)
        except Exception:
            emotion = 'neutral'

    try:
        from voice.tts import get_tts_queue, is_speaking
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return

    q = get_tts_queue()
    if not (q.engine and q.engine.is_initialized):
        # No voice: show the text, don't block the boot on it.
        try:
            from voice.echo_filter import get_echo_filter
            get_echo_filter().stop_speaking()
        except Exception:
            pass
        return

    q.speak(text, emotion=emotion, priority=3, skip_presence=True)

    if blocking:
        # Wait until the line has been picked up and finished, keeping Tk alive
        deadline = time.time() + 180
        started = False
        while time.time() < deadline:
            busy = q.pending_count() > 0 or is_speaking()
            if busy:
                started = True
            elif started or time.time() > deadline - 179.5:
                # queue empty and nothing playing: give the worker 150 ms to pick it up
                time.sleep(0.15)
                if q.pending_count() == 0 and not is_speaking():
                    break
            if _boot_display and _boot_display.root:
                try:
                    for _ in range(10):
                        _boot_display.root.update()
                except tk.TclError:
                    break
            time.sleep(0.005)
        try:
            from voice.echo_filter import get_echo_filter
            get_echo_filter().stop_speaking()
        except Exception:
            pass


def cora_respond(context: str, result: str, status: str = "ok", mode: str = "quick",
                 must_include: Optional[List[str]] = None) -> str:
    """
    CORA generates a unique response for each boot phase.
    must_include: words the spoken line has to keep (names, numbers); if the
    model drops any of them the exact `result` text is spoken instead.

    Args:
        context: What phase this is (e.g., "AI Engine", "Camera")
        result: The data/result to announce
        status: "ok", "warn", or "fail"
        mode: "quick" for short status readouts, "full" for news/weather/longer content
    """
    import re

    try:
        from ai.ollama import generate

        if mode == "quick":
            # Use full system prompt but constrain the output
            system_prompt = get_system_prompt()

            # Add boot constraint to the prompt itself - 1-2 sentences, include all the data
            prompt = f"""[BOOT ANNOUNCEMENT - say this in 1-2 sentences with your usual attitude. Include ALL the data/numbers.]
{result}"""

            response = generate(
                prompt=prompt,
                system=system_prompt,
                temperature=0.9
            )

        else:
            # Full mode - news, weather, descriptions use full personality
            system_prompt = get_system_prompt()
            prompt = f"Announce this naturally in 1-2 sentences: {result}"

            response = generate(
                prompt=prompt,
                system=system_prompt,
                temperature=0.7
            )

        if response.content:
            text = response.content.strip().strip('"\'')
            # Remove CORA: prefix if present
            if text.lower().startswith('cora:'):
                text = text[5:].strip()
            # Remove markdown formatting
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
            text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *italic* -> italic
            text = re.sub(r'__([^_]+)__', r'\1', text)  # __bold__ -> bold
            text = re.sub(r'_([^_]+)_', r'\1', text)  # _italic_ -> italic
            text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # # headers
            text = re.sub(r'\n+', ' ', text)  # newlines to spaces
            text = re.sub(r'\s+', ' ', text).strip()  # clean up whitespace

            # Required data (creator names, counts) must survive the rewrite
            low = text.lower()
            missing = [w for w in (must_include or []) if w.lower() not in low]
            if missing:
                print(f"[WARN] AI response dropped {missing}, using raw result")
                return result

            # For quick mode, enforce length limit (1-2 short sentences) - if AI went crazy, use raw result
            if mode == "quick" and len(text) > 220:
                print(f"[WARN] AI response too long ({len(text)} chars), using raw result")
                return result

            # Quick mode: at most two sentences
            if mode == "quick":
                sentences = re.split(r'(?<=[.!?])\s+', text)
                if len(sentences) > 2:
                    text = ' '.join(sentences[:2])

            if len(text) > 10:
                return text

    except Exception as e:
        print(f"[WARN] AI response failed: {e}")

    # If AI fails completely, just return the raw result
    return result


def _safe_ui_call(func, *args):
    """Thread-safe UI call using root.after()."""
    global _boot_display
    if _boot_display and _boot_display.root:
        try:
            _boot_display.root.after(0, lambda: func(*args))
        except:
            pass


# Import centralized window manager
from ui.window_manager import create_window, create_popup, create_image_window, create_code_window, bring_to_front


def display_log(text: str, level: str = 'info'):
    """Log to the visual display (thread-safe)."""
    global _boot_display
    if _boot_display:
        def do_log():
            try:
                if level == 'ok':
                    _boot_display.log_ok(text)
                elif level == 'warn':
                    _boot_display.log_warn(text)
                elif level == 'fail':
                    _boot_display.log_fail(text)
                elif level == 'system':
                    _boot_display.log_system(text)
                elif level == 'phase':
                    _boot_display.log_phase(text)
                else:
                    _boot_display.log(text, level)
            except:
                pass
        _safe_ui_call(do_log)


def display_phase(phase_name: str, status: str):
    """Update phase status on the visual display (thread-safe)."""
    global _boot_display
    if _boot_display:
        def do_phase():
            try:
                _boot_display.update_phase(phase_name, status)
                _boot_display.set_status(f"{phase_name}: {status.upper()}")
            except:
                pass
        _safe_ui_call(do_phase)


def display_user_input(text: str):
    """Log user input/command to the visual display (thread-safe)."""
    global _boot_display
    if _boot_display:
        _safe_ui_call(lambda: _boot_display.log_user(text))


def display_action(text: str):
    """Log CORA action to the visual display (thread-safe)."""
    global _boot_display
    if _boot_display:
        _safe_ui_call(lambda: _boot_display.log_action(text))


def display_tool(tool_name: str, details: str = ""):
    """Log tool execution to the visual display (thread-safe)."""
    global _boot_display
    if _boot_display:
        _safe_ui_call(lambda: _boot_display.log_tool(tool_name, details))


def display_result(text: str):
    """Log action result to the visual display (thread-safe)."""
    global _boot_display
    if _boot_display:
        _safe_ui_call(lambda: _boot_display.log_result(text))


def display_thinking(text: str):
    """Log CORA's reasoning/thinking to the visual display (thread-safe)."""
    global _boot_display
    if _boot_display:
        _safe_ui_call(lambda: _boot_display.log_thinking(text))


def get_system_stats() -> Dict[str, Any]:
    """Get CPU, RAM, Disk, GPU stats."""
    stats = {
        'cpu': 0,
        'memory': 0,
        'memory_used_gb': 0,
        'memory_total_gb': 0,
        'disk': 0,
        'disk_free_gb': 0,
        'disk_total_gb': 0,
        'gpu': None,
        'gpu_name': None,
        'gpu_memory': None,
        'network_up': False,
        'process_count': 0,
    }

    try:
        import psutil

        # CPU
        stats['cpu'] = psutil.cpu_percent(interval=0.5)

        # Memory
        mem = psutil.virtual_memory()
        stats['memory'] = mem.percent
        stats['memory_used_gb'] = mem.used / (1024**3)
        stats['memory_total_gb'] = mem.total / (1024**3)

        # Disk (use C: on Windows)
        try:
            disk = psutil.disk_usage('C:\\')
        except:
            disk = psutil.disk_usage('/')
        stats['disk'] = disk.percent
        stats['disk_free_gb'] = disk.free / (1024**3)
        stats['disk_total_gb'] = disk.total / (1024**3)

        # Network check
        try:
            net = psutil.net_if_stats()
            for iface, data in net.items():
                if data.isup and iface != 'lo':
                    stats['network_up'] = True
                    break
        except:
            pass

        # Process count
        stats['process_count'] = len(psutil.pids())

    except ImportError:
        print("[BOOT] [WARN] psutil not available")

    # GPU - try nvidia-smi first (more reliable), then GPUtil as fallback
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(', ')
            if len(parts) >= 4:
                stats['gpu_name'] = parts[0].strip()
                total_mem = float(parts[1].strip())
                used_mem = float(parts[2].strip())
                stats['gpu'] = float(parts[3].strip())  # GPU utilization %
                stats['gpu_memory'] = (used_mem / total_mem) * 100 if total_mem > 0 else 0
                stats['gpu_total_mb'] = total_mem
                stats['gpu_used_mb'] = used_mem
    except Exception:
        # Fallback to GPUtil
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                stats['gpu'] = gpu.load * 100
                stats['gpu_name'] = gpu.name
                stats['gpu_memory'] = gpu.memoryUtil * 100
        except Exception:
            pass

    return stats


def test_tool(name: str, test_func, announce: bool = True) -> bool:
    """Test a tool and optionally announce result."""
    try:
        result = test_func()
        status = "OK" if result else "WARN"
        print(f"  [{status}] {name}")
        BOOT_STATUS['tools_tested'].append({'name': name, 'status': status})
        return result if result else False
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        BOOT_STATUS['tools_tested'].append({'name': name, 'status': 'FAIL', 'error': str(e)})
        return False
import types as _types
import src.boot_phases


def run_boot_sequence(skip_tts: bool = False, show_display: bool = True) -> Dict[str, Any]:
    """
    Run full F-100 style boot sequence.
    Tests ALL tools and announces each system via Kokoro TTS.
    Shows visual display with waveform and scrolling log.
    """
    global BOOT_STATUS, _tts_engine, _boot_display

    BOOT_STATUS = {
        'systems': [],
        'tools_tested': [],
        'errors': [],
        'start_time': time.time(),
        'end_time': None,
        'weather': None,
        'cpu_percent': 0,
        'memory_percent': 0,
        'disk_percent': 0,
        'gpu_available': False,
    }

    # ASCII banner
    print("")
    print("  +=========================================================+")
    print("  |        C.O.R.A BOOT SEQUENCE INITIATED                  |")
    print("  |     Cognitive Operations & Reasoning Assistant          |")
    print("  +=========================================================+")
    print("")

    # Visual display should already be created by main thread before boot starts
    # If not, we can't create it here (tkinter must run on main thread)
    if show_display and _boot_display is None:
        print("[BOOT] Visual display not pre-initialized - running without display")
    elif _boot_display:
        print("[BOOT] Using pre-initialized visual display")
    L = _types.SimpleNamespace(_demo=None, _github_import=None, camera=None, error=None, now=None, show_display=show_display, skip_tts=skip_tts, weather_data=None)
    _m = sys.modules[__name__]
    for _phase in src.boot_phases.PHASES:   # one module per boot phase (src/boot_phases/)
        _r = _phase.run(_m, L)
        if isinstance(_r, tuple) and _r and _r[0] == 'return':
            return _r[1]


def quick_boot() -> Dict[str, Any]:
    """Quick boot without TTS."""
    return run_boot_sequence(skip_tts=True)


def full_boot() -> Dict[str, Any]:
    """Full boot with Kokoro TTS announcements."""
    return run_boot_sequence(skip_tts=False)
if __name__ == "__main__":
    # the runtime moved to src.boot_runtime on 2026-10-14 (this module stays the owner of its globals)
    import importlib
    importlib.import_module("src.boot_runtime").main(sys.modules[__name__])
