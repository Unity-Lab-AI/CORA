#!/usr/bin/env python3
"""
C.O.R.A Boot Sequence - F-100 Fighter Jet Style
Sequential system initialization with Kokoro TTS announcements.

Tests all tools and announces each system as it comes online.
User hears EVERY component boot up through Kokoro TTS.

Created by: Unity AI Lab
"""

import sys
import os
import time
import signal
import atexit
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project paths
PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / 'src'))
sys.path.insert(0, str(PROJECT_DIR / 'ui'))


def shutdown_handler(*args):
    """Handle shutdown signals - close everything cleanly."""
    print("\n[CORA] Shutting down...")
    global _boot_display
    if _boot_display:
        try:
            _boot_display.close()
        except:
            pass
    os._exit(0)


# Register shutdown handlers
atexit.register(shutdown_handler)
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


def init_tts():
    """Initialize Kokoro TTS - THIS IS THE FIRST THING THAT BOOTS."""
    global _tts_engine
    print("\n[BOOT] ========== VOICE SYNTHESIS INITIALIZATION ==========")
    print("[BOOT] Loading Kokoro TTS engine...")

    try:
        from voice.tts import KokoroTTS
        engine = KokoroTTS(voice='af_bella', speed=1.0)

        if engine.initialize():
            _tts_engine = engine
            print("[BOOT] Kokoro TTS initialized successfully")
            print("[BOOT] Voice: af_bella (sexy voice)")
            print("[BOOT] ========== VOICE ONLINE ==========\n")

            # FIRST THING USER HEARS - TTS announcing itself
            speak("Voice synthesis online. Kokoro TTS loaded and ready.")
            responsive_sleep(0.3)
            return True
        else:
            print("[BOOT] [FAIL] Kokoro TTS failed to initialize")
            return False

    except Exception as e:
        print(f"[BOOT] [FAIL] TTS init error: {e}")
        return False


def speak(text: str, blocking: bool = True):
    """Speak text via Kokoro TTS and update visual display.

    Args:
        text: Text to speak
        blocking: If True, wait for speech to finish. If False, return immediately.
    """
    global _boot_display
    print(f"[CORA] {text}")

    # Mark echo filter that we're speaking (prevents hearing ourselves)
    try:
        from voice.echo_filter import get_echo_filter
        echo_filter = get_echo_filter()
        # Estimate duration: ~0.4 seconds per word
        word_count = len(text.split())
        duration = max(1.0, word_count * 0.4)
        echo_filter.start_speaking(duration=duration, text=text)
    except:
        pass

    # Note: Waveform start/stop is now handled automatically by KokoroTTS.speak()
    # via the set_boot_display() registration

    def do_speak():
        """Actual TTS call - runs in thread."""
        if _tts_engine:
            try:
                _tts_engine.speak(text, emotion='neutral')
            except Exception as e:
                print(f"[TTS ERROR] {e}")

        # Clear echo filter now that we're done
        try:
            from voice.echo_filter import get_echo_filter
            get_echo_filter().stop_speaking()
        except:
            pass

    # Run TTS in background thread so UI stays responsive
    import threading
    tts_thread = threading.Thread(target=do_speak, daemon=True)
    tts_thread.start()

    # If blocking, wait for thread to finish while keeping Tkinter responsive
    if blocking:
        while tts_thread.is_alive():
            if _boot_display and _boot_display.root:
                try:
                    # Process ALL pending events including mouse drags
                    for _ in range(10):  # Process multiple events per cycle
                        _boot_display.root.update()
                except tk.TclError:
                    break  # Window was closed
            # Minimal sleep - just yield to other threads
            time.sleep(0.001)
        tts_thread.join()  # Clean up thread


def cora_respond(context: str, result: str, status: str = "ok", mode: str = "quick") -> str:
    """
    CORA generates a unique response for each boot phase.

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

            # For quick mode, enforce length limit - if AI went crazy, use raw result
            if mode == "quick" and len(text) > 100:
                print(f"[WARN] AI response too long ({len(text)} chars), using raw result")
                return result

            # Take only first sentence if multiple
            if mode == "quick" and '. ' in text:
                text = text.split('. ')[0] + '.'

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

    # ================================================================
    # PHASE 0.8: WAVEFORM INITIALIZATION
    # ================================================================
    display_phase("0.8 Waveform Init", "running")
    display_log("PHASE 0.8: WAVEFORM VISUAL", "phase")
    print("\n[PHASE 0.8] Waveform Visual Initialization")
    print("=" * 50)

    waveform_ok = False
    waveform_errors = []

    try:
        from ui.boot_display import AudioWaveform, get_audio_buffer, set_audio_data, clear_audio_data, _audio_buffer_lock
        print("  [OK] AudioWaveform module loaded")
        display_log("AudioWaveform module loaded", "ok")

        # Check 1: Boot display exists
        if not _boot_display:
            waveform_errors.append("Boot display not initialized")
            print("  [FAIL] Boot display not initialized")
            display_log("Boot display not initialized", "fail")
        else:
            print("  [OK] Boot display exists")
            display_log("Boot display exists", "ok")

            # Check 2: Waveform widget exists
            if not _boot_display.waveform:
                waveform_errors.append("Waveform widget is None")
                print("  [FAIL] Waveform widget is None")
                display_log("Waveform widget is None", "fail")
            else:
                print("  [OK] Waveform widget created")
                display_log("Waveform widget created", "ok")

                # Check 3: Audio buffer works
                try:
                    buf = get_audio_buffer()
                    print(f"  [OK] Audio buffer initialized (active={buf['active']})")
                    display_log("Audio buffer initialized", "ok")
                except Exception as e:
                    waveform_errors.append(f"Audio buffer error: {e}")
                    print(f"  [FAIL] Audio buffer error: {e}")
                    display_log(f"Audio buffer error: {e}", "fail")

                # Check 4: Test setting audio data
                try:
                    import numpy as np
                    # Create a test sine wave
                    test_samples = np.sin(np.linspace(0, 10 * np.pi, 2400)).astype(np.float32)
                    set_audio_data(test_samples, sample_rate=24000)
                    buf = get_audio_buffer()
                    if buf['active'] and buf['data'] is not None:
                        print(f"  [OK] Audio data injection works ({len(buf['data'])} samples)")
                        display_log("Audio data injection works", "ok")
                    else:
                        waveform_errors.append("Audio data not received by buffer")
                        print("  [FAIL] Audio data not received by buffer")
                        display_log("Audio data not received", "fail")
                except Exception as e:
                    waveform_errors.append(f"Audio injection error: {e}")
                    print(f"  [FAIL] Audio injection error: {e}")
                    display_log(f"Audio injection error: {e}", "fail")

                # Check 5: Test waveform animation with audio data
                print("  Testing waveform animation with audio...")
                display_log("Testing waveform animation", "info")
                try:
                    _boot_display.waveform.start()
                    # Let it animate for 1 second with our test data
                    for _ in range(10):
                        time.sleep(0.1)
                        if _boot_display.root:
                            _boot_display.root.update()
                    _boot_display.waveform.stop()
                    clear_audio_data()
                    print("  [OK] Waveform animation test passed")
                    display_log("Waveform animation working", "ok")
                    waveform_ok = True
                except Exception as e:
                    waveform_errors.append(f"Animation error: {e}")
                    print(f"  [FAIL] Animation error: {e}")
                    display_log(f"Animation error: {e}", "fail")

        # Summary
        if waveform_ok:
            print("  [OK] All waveform checks passed")
            display_log("All waveform checks passed", "ok")
            BOOT_STATUS['systems'].append({'name': 'Waveform Visual', 'status': 'OK'})
            display_phase("0.8 Waveform Init", "ok")
        else:
            error_summary = "; ".join(waveform_errors) if waveform_errors else "Unknown error"
            print(f"  [WARN] Waveform issues: {error_summary}")
            display_log(f"Issues: {error_summary}", "warn")
            BOOT_STATUS['systems'].append({'name': 'Waveform Visual', 'status': 'WARN'})
            display_phase("0.8 Waveform Init", "warn")

    except Exception as e:
        print(f"  [FAIL] Waveform init exception: {e}")
        display_log(f"Waveform exception: {e}", "fail")
        BOOT_STATUS['systems'].append({'name': 'Waveform Visual', 'status': 'FAIL'})
        display_phase("0.8 Waveform Init", "fail")

    # ================================================================
    # PHASE 0.9: ABOUT CORA (Introduction)
    # ================================================================
    display_phase("0.9 About CORA", "running")
    display_log("PHASE 0.9: ABOUT CORA", "phase")
    print("\n[PHASE 0.9] About CORA")
    print("=" * 50)

    # Display the about info in the log
    display_log("═══════════════════════════════════════════════", "system")
    display_log("    C.O.R.A - Cognitive Operations & Reasoning Assistant", "system")
    display_log("═══════════════════════════════════════════════", "system")
    display_log("Version: 2.4.0", "info")
    display_log("Created by: Unity AI Lab", "info")
    display_log("Developers: Hackall360, Sponge, GFourteen", "info")
    display_log("Website: https://www.unityailab.com", "info")
    display_log("GitHub: https://github.com/Unity-Lab-AI", "info")

    print("  C.O.R.A - Cognitive Operations & Reasoning Assistant")
    print("  Version: 2.4.0")
    print("  Unity AI Lab - Hackall360, Sponge, GFourteen")

    BOOT_STATUS['version'] = '2.4.0'
    BOOT_STATUS['creators'] = 'Hackall360, Sponge, GFourteen'
    display_phase("0.9 About CORA", "ok")

    # ================================================================
    # PHASE 1: VOICE SYNTHESIS (FIRST - so user can hear everything)
    # ================================================================
    display_phase("1.0 Voice Synthesis", "running")
    display_log("PHASE 1: VOICE SYNTHESIS", "phase")

    if not skip_tts:
        tts_ok = init_tts()
        if tts_ok:
            BOOT_STATUS['systems'].append({'name': 'Voice TTS (Kokoro)', 'status': 'OK'})
            display_log("Kokoro TTS initialized - Voice: af_bella", "ok")
            display_phase("1.0 Voice Synthesis", "ok")
        else:
            BOOT_STATUS['systems'].append({'name': 'Voice TTS (Kokoro)', 'status': 'FAIL'})
            display_log("Kokoro TTS failed to initialize", "fail")
            display_phase("1.0 Voice Synthesis", "fail")
    else:
        print("[BOOT] TTS skipped (silent mode)")
        display_log("TTS skipped (silent mode)", "warn")
        _tts_engine = None
        display_phase("1.0 Voice Synthesis", "warn")

    # Opening announcement - CORA generates her own intro dynamically
    about_data = {
        'name': 'CORA',
        'full_name': 'Cognitive Operations and Reasoning Assistant',
        'version': '2.4.0',
        'creator': 'Unity AI Lab',
        'developers': 'Hackall360, Sponge, and GFourteen'
    }
    # CORA generates her own unique intro - natural speech
    response = cora_respond(
        "About Me Introduction",
        f"Hey, I'm {about_data['name']}. That stands for {about_data['full_name']}. "
        f"Version {about_data['version']}. Made by {about_data['developers']} over at {about_data['creator']}. "
        f"I've got voice, vision, and plenty of attitude. Let's get this boot going.",
        "ok"
    )
    speak(response)
    responsive_sleep(0.3)

    # ================================================================
    # PHASE 2: AI ENGINE (Critical - the brain)
    # ================================================================
    display_phase("2.0 AI Engine", "running")
    display_log("PHASE 2: AI ENGINE", "phase")
    print("\n[PHASE 2] AI Engine Initialization")
    print("=" * 50)

    ai_online = False
    ai_model = "Unknown"

    try:
        from ai.ollama import check_ollama, get_model_info
        print("  Checking Ollama connection...")
        display_log("Checking Ollama connection...", "info")

        if check_ollama():
            ai_online = True
            try:
                info = get_model_info()
                ai_model = info.get('model', 'Ollama')
            except:
                ai_model = "Ollama"
            print(f"  [OK] AI Engine online - {ai_model}")
            display_log(f"AI Engine online - Model: {ai_model}", "ok")
            BOOT_STATUS['systems'].append({'name': f'AI Engine ({ai_model})', 'status': 'OK'})
            display_phase("2.0 AI Engine", "ok")
            # CORA announces AI status - just the data
            response = cora_respond("AI Brain/Ollama", f"AI engine online. Model: {ai_model}", "ok")
            speak(response)
        else:
            print("  [WARN] AI Engine not responding")
            display_log("AI Engine not responding", "warn")
            BOOT_STATUS['systems'].append({'name': 'AI Engine', 'status': 'WARN'})
            display_phase("2.0 AI Engine", "warn")
            response = cora_respond("AI Brain/Ollama", "AI engine not responding. Ollama may be down.", "warn")
            speak(response)

    except Exception as e:
        print(f"  [WARN] AI Engine: {e}")
        display_log(f"AI Engine error: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'AI Engine', 'status': 'WARN'})
        display_phase("AI Engine", "warn")
        response = cora_respond("AI Brain/Ollama", f"AI engine error: {e}", "fail")
        speak(response)

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 2.1: AI MODELS CHECK
    # ================================================================
    display_phase("2.1 AI Models", "running")
    display_log("PHASE 2.1: AI MODELS CHECK", "phase")
    print("\n[PHASE 2.1] AI Models Check")
    print("=" * 50)

    # Required models for CORA
    REQUIRED_MODELS = {
        'dolphin-mistral': 'Chat/Response model (CORA\'s personality)',
        'llava': 'Vision model (see/look commands)',
        'qwen2.5-coder': 'Coding model (write/fix code)',
    }

    models_ok = 0
    models_missing = []

    try:
        from ai.ollama import list_models
        installed_models = list_models()
        installed_names = [m.get('name', '').lower() for m in installed_models]

        print(f"  Found {len(installed_models)} models installed")
        display_log(f"Found {len(installed_models)} models installed", "info")

        for model_key, model_desc in REQUIRED_MODELS.items():
            # Check if model is installed (partial match)
            found = any(model_key.lower() in name for name in installed_names)
            if found:
                print(f"  [OK] {model_key} - {model_desc}")
                display_log(f"{model_key} - OK", "ok")
                models_ok += 1
            else:
                print(f"  [MISSING] {model_key} - {model_desc}")
                display_log(f"{model_key} - MISSING", "warn")
                models_missing.append(model_key)

        BOOT_STATUS['models_installed'] = len(installed_models)
        BOOT_STATUS['models_required'] = len(REQUIRED_MODELS)
        BOOT_STATUS['models_ok'] = models_ok

        if models_ok == len(REQUIRED_MODELS):
            display_phase("2.1 AI Models", "ok")
            BOOT_STATUS['systems'].append({'name': 'AI Models', 'status': 'OK'})
            response = cora_respond("AI Models check", f"{models_ok} of {len(REQUIRED_MODELS)} models loaded. All good.", "ok")
        elif models_ok > 0:
            display_phase("2.1 AI Models", "warn")
            BOOT_STATUS['systems'].append({'name': 'AI Models', 'status': 'WARN'})
            missing_str = ", ".join(models_missing)
            response = cora_respond("AI Models check", f"{models_ok} of {len(REQUIRED_MODELS)} models. Missing: {missing_str}", "warn")
        else:
            display_phase("2.1 AI Models", "fail")
            BOOT_STATUS['systems'].append({'name': 'AI Models', 'status': 'FAIL'})
            response = cora_respond("AI Models check", "No models found. Need to install them.", "fail")
        speak(response)

    except Exception as e:
        print(f"  [WARN] Model check failed: {e}")
        display_log(f"Model check error: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'AI Models', 'status': 'WARN'})
        display_phase("2.1 AI Models", "warn")

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 3: PC HARDWARE CHECK
    # ================================================================
    display_phase("3.0 Hardware Check", "running")
    display_log("PHASE 3: HARDWARE CHECK", "phase")
    print("\n[PHASE 3] Hardware Status Check")
    print("=" * 50)

    stats = get_system_stats()

    # CPU
    cpu = stats['cpu']
    print(f"  CPU Usage: {cpu:.1f}%")
    display_log(f"CPU Usage: {cpu:.1f}%", "system")
    BOOT_STATUS['cpu_percent'] = cpu

    # Memory
    mem = stats['memory']
    mem_used = stats['memory_used_gb']
    mem_total = stats['memory_total_gb']
    print(f"  Memory: {mem:.1f}% ({mem_used:.1f} / {mem_total:.1f} GB)")
    display_log(f"Memory: {mem:.1f}% ({mem_used:.1f}/{mem_total:.1f} GB)", "system")
    BOOT_STATUS['memory_percent'] = mem

    # Disk
    disk = stats['disk']
    disk_free = stats['disk_free_gb']
    disk_total = stats['disk_total_gb']
    print(f"  Disk: {disk:.1f}% used ({disk_free:.1f} GB free)")
    display_log(f"Disk: {disk:.1f}% used ({disk_free:.1f} GB free)", "system")
    BOOT_STATUS['disk_percent'] = disk

    # GPU
    if stats['gpu'] is not None and stats['gpu_name']:
        gpu = stats['gpu']
        gpu_name = stats['gpu_name']
        gpu_mem = stats.get('gpu_memory', 0)
        gpu_used_mb = stats.get('gpu_used_mb', 0)
        gpu_total_mb = stats.get('gpu_total_mb', 0)
        print(f"  GPU: {gpu_name}")
        if gpu_total_mb > 0:
            print(f"       VRAM: {gpu_used_mb:.0f}/{gpu_total_mb:.0f} MB ({gpu_mem:.1f}%)")
            print(f"       Load: {gpu:.1f}%")
            display_log(f"GPU: {gpu_name}", "ok")
            display_log(f"  VRAM: {gpu_used_mb:.0f}/{gpu_total_mb:.0f} MB ({gpu_mem:.1f}%)", "system")
            display_log(f"  Load: {gpu:.1f}%", "system")
        else:
            print(f"       Load: {gpu:.1f}% | VRAM: {gpu_mem:.1f}%")
            display_log(f"GPU: {gpu_name} (Load: {gpu:.1f}%, VRAM: {gpu_mem:.1f}%)", "ok")
        BOOT_STATUS['gpu_available'] = True
        BOOT_STATUS['gpu_name'] = gpu_name
    else:
        print("  GPU: Not detected")
        display_log("GPU: Not detected", "warn")
        BOOT_STATUS['gpu_available'] = False

    # Network
    net_status = "Connected" if stats['network_up'] else "Disconnected"
    print(f"  Network: {net_status}")
    display_log(f"Network: {net_status}", "ok" if stats['network_up'] else "warn")

    # Process count
    print(f"  Running Processes: {stats['process_count']}")
    display_log(f"Running Processes: {stats['process_count']}", "info")

    BOOT_STATUS['systems'].append({'name': 'Hardware Check', 'status': 'OK'})
    display_phase("3.0 Hardware Check", "ok")

    # Hardware summary - just the stats
    hw_data = f"CPU {cpu:.0f}%, RAM {mem:.0f}%, Disk {disk:.0f}%"
    if BOOT_STATUS['gpu_available']:
        hw_data += f", GPU {stats['gpu_name']} at {stats['gpu']:.0f}%"
    else:
        hw_data += ", no GPU"
    response = cora_respond("PC Hardware scan", hw_data, "ok")
    speak(response)

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 3.1: LIVE CAMERA FEED TEST
    # ================================================================
    display_phase("3.1 Camera Feed", "running")
    display_log("PHASE 3.1: LIVE CAMERA FEED TEST", "phase")
    print("\n[PHASE 3.1] Live Camera Feed Test")
    print("=" * 50)

    try:
        import cv2
        from ui.camera_feed import open_live_camera, close_live_camera, capture_from_live_camera

        print("  Testing live camera feed...")
        display_tool("Live Camera", "Opening camera feed")
        display_action("Starting live video stream...")

        # Open live camera
        parent = _boot_display.root if _boot_display else None
        camera = open_live_camera(parent=parent)

        if camera and camera.is_active():
            print("  [OK] Live camera feed started")
            display_result("Live camera feed is active")
            BOOT_STATUS['tools_tested'].append({'name': 'Live Camera Feed', 'status': 'OK'})
            BOOT_STATUS['live_camera_available'] = True

            # Let it run for 3 seconds
            display_action("Showing live feed for 3 seconds...")
            responsive_sleep(3)

            # Take a test snapshot and analyze
            display_action("Taking snapshot for AI analysis...")
            frame_path = capture_from_live_camera()

            if frame_path:
                print(f"  [OK] Snapshot captured: {frame_path}")
                display_result("Snapshot captured successfully")

                # Analyze with AI vision
                try:
                    from ai.ollama import generate_with_image
                    display_action("Analyzing camera view with AI vision...")

                    vision_result = generate_with_image(
                        prompt="What do you see through this camera? Describe the scene briefly.",
                        image_path=str(frame_path),
                        model="llava"
                    )

                    if vision_result and vision_result.content:
                        import re
                        camera_desc = vision_result.content.strip()
                        camera_desc = re.sub(r'\*\*([^*]+)\*\*', r'\1', camera_desc)
                        camera_desc = re.sub(r'\*([^*]+)\*', r'\1', camera_desc)
                        camera_desc = re.sub(r'\n+', ' ', camera_desc)
                        camera_desc = re.sub(r'\s+', ' ', camera_desc).strip()

                        print(f"  CORA sees: {camera_desc[:100]}...")
                        display_result(f"Vision: {camera_desc[:80]}...")
                        BOOT_STATUS['camera_description'] = camera_desc

                        # CORA announces camera + what she sees
                        response = cora_respond("Live Camera", f"Camera online. I see: {camera_desc[:80]}", "ok")
                        speak(response)
                    else:
                        response = cora_respond("Live Camera", "Camera online but vision analysis failed.", "warn")
                        speak(response)
                except Exception as e:
                    print(f"  [INFO] Vision analysis skipped: {e}")
                    response = cora_respond("Live Camera", "Camera online. Vision skipped.", "ok")
                    speak(response)
            else:
                response = cora_respond("Live Camera", "Camera online.", "ok")
                speak(response)

            # Close camera after test
            display_action("Closing test camera feed...")
            close_live_camera()
            print("  [OK] Camera feed closed")

            display_phase("3.1 Camera Feed", "ok")
        else:
            print("  [WARN] Live camera not available")
            display_log("Live camera not available", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'Live Camera Feed', 'status': 'WARN'})
            BOOT_STATUS['live_camera_available'] = False
            display_phase("3.1 Camera Feed", "warn")

            response = cora_respond("Live Camera", "Camera not available.", "warn")
            speak(response)

    except ImportError as e:
        print(f"  [WARN] Camera dependencies missing: {e}")
        display_log(f"Camera dependencies: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Live Camera Feed', 'status': 'WARN'})
        display_phase("3.1 Camera Feed", "warn")
    except Exception as e:
        print(f"  [WARN] Live camera test: {e}")
        display_log(f"Live camera error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Live Camera Feed', 'status': 'WARN'})
        display_phase("3.1 Camera Feed", "warn")

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 4: CORE TOOLS TEST
    # ================================================================
    display_phase("4.0 Core Tools", "running")
    display_log("PHASE 4: CORE TOOLS TEST", "phase")
    print("\n[PHASE 4] Core Tools Test")
    print("=" * 50)

    tools_ok = 0
    tools_total = 0

    # Memory System
    tools_total += 1
    try:
        from cora_tools.memory import recall, remember
        print("  [OK] Memory System (recall/remember)")
        display_log("Memory System loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Memory System', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [FAIL] Memory System: {e}")
        display_log(f"Memory System FAILED: {e}", "fail")
        BOOT_STATUS['tools_tested'].append({'name': 'Memory System', 'status': 'FAIL'})

    # Task Manager
    tools_total += 1
    try:
        from cora_tools.tasks import TaskManager
        tm = TaskManager()
        task_count = len(tm.tasks) if hasattr(tm, 'tasks') else 0
        print(f"  [OK] Task Manager ({task_count} tasks)")
        display_log(f"Task Manager loaded ({task_count} tasks)", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Task Manager', 'status': 'OK'})
        BOOT_STATUS['task_count'] = task_count
        tools_ok += 1
    except Exception as e:
        print(f"  [FAIL] Task Manager: {e}")
        display_log(f"Task Manager FAILED: {e}", "fail")
        BOOT_STATUS['tools_tested'].append({'name': 'Task Manager', 'status': 'FAIL'})

    # Reminders
    tools_total += 1
    try:
        from cora_tools.reminders import ReminderManager
        rm = ReminderManager()
        reminder_count = len(rm.reminders) if hasattr(rm, 'reminders') else 0
        print(f"  [OK] Reminders ({reminder_count} active)")
        display_log(f"Reminders loaded ({reminder_count} active)", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Reminders', 'status': 'OK'})
        BOOT_STATUS['reminder_count'] = reminder_count
        tools_ok += 1
    except Exception as e:
        print(f"  [FAIL] Reminders: {e}")
        display_log(f"Reminders FAILED: {e}", "fail")
        BOOT_STATUS['tools_tested'].append({'name': 'Reminders', 'status': 'FAIL'})

    # File Operations
    tools_total += 1
    try:
        from cora_tools.files import read_file, create_file
        print("  [OK] File Operations")
        display_log("File Operations loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'File Operations', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [FAIL] File Operations: {e}")
        display_log(f"File Operations FAILED: {e}", "fail")
        BOOT_STATUS['tools_tested'].append({'name': 'File Operations', 'status': 'FAIL'})

    # Screenshot/Vision
    tools_total += 1
    try:
        from cora_tools.screenshots import desktop, quick_screenshot
        print("  [OK] Vision/Screenshots")
        display_log("Vision/Screenshots loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Vision/Screenshots', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Vision/Screenshots: {e}")
        display_log(f"Vision/Screenshots: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Vision/Screenshots', 'status': 'WARN'})

    # Web Browser
    tools_total += 1
    try:
        from cora_tools.browser import browse_sync
        print("  [OK] Web Browser")
        display_log("Web Browser loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Web Browser', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Web Browser: {e}")
        display_log(f"Web Browser: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Web Browser', 'status': 'WARN'})

    # System Tools
    tools_total += 1
    try:
        from cora_tools.system import run_shell, get_system_info
        print("  [OK] System Commands")
        display_log("System Commands loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'System Commands', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] System Commands: {e}")
        display_log(f"System Commands: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'System Commands', 'status': 'WARN'})

    # Windows Control
    tools_total += 1
    try:
        from cora_tools.windows import list_windows, focus_window
        print("  [OK] Windows Control")
        display_log("Windows Control loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Windows Control', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Windows Control: {e}")
        display_log(f"Windows Control: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Windows Control', 'status': 'WARN'})

    # Code Tools
    tools_total += 1
    try:
        from cora_tools.code import analyze_code
        print("  [OK] Code Analysis")
        display_log("Code Analysis loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Code Analysis', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Code Analysis: {e}")
        display_log(f"Code Analysis: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Code Analysis', 'status': 'WARN'})

    # Media Control
    tools_total += 1
    try:
        from cora_tools.media import MediaController
        print("  [OK] Media Control")
        display_log("Media Control loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Media Control', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Media Control: {e}")
        display_log(f"Media Control: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Media Control', 'status': 'WARN'})

    display_phase("4.0 Core Tools", "ok")
    # Tools summary - just the numbers
    tools_result = f"{tools_ok} of {tools_total} tools loaded."
    tools_status = "ok" if tools_ok >= tools_total - 2 else ("warn" if tools_ok >= tools_total // 2 else "fail")
    response = cora_respond("Core Tools check", tools_result, tools_status)
    speak(response)
    responsive_sleep(0.3)

    # ================================================================
    # PHASE 4.1: CODE IMPORT TEST - Fetch real code from GitHub
    # ================================================================
    display_phase("4.1 Code Import", "running")
    display_log("PHASE 4.1: CODE IMPORT FROM GITHUB", "phase")
    print("\n[PHASE 4.1] Code Import from GitHub")
    print("=" * 50)

    try:
        import random
        import urllib.request
        import json
        import base64
        import os

        # Try to use GitHub token from .env to fetch from user's repos
        github_token = os.environ.get('GITHUB_TOKEN', '')
        fetched_from_user_repo = False
        url = None
        code_name = None
        lang = "python"
        repo_name = None

        if github_token:
            try:
                # Get user's repos via GitHub API
                api_url = "https://api.github.com/user/repos?per_page=100&sort=updated"
                req = urllib.request.Request(api_url, headers={
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'CORA-Bot/1.0'
                })
                with urllib.request.urlopen(req, timeout=10) as response:
                    repos = json.loads(response.read().decode('utf-8'))

                # Filter for repos with Python code
                python_repos = [r for r in repos if r.get('language') == 'Python' and not r.get('fork')]
                if python_repos:
                    # Pick a random repo
                    chosen_repo = random.choice(python_repos)
                    repo_name = chosen_repo['full_name']
                    print(f"  Using your repo: {repo_name}")

                    # Get contents of repo root
                    contents_url = f"https://api.github.com/repos/{repo_name}/contents"
                    req = urllib.request.Request(contents_url, headers={
                        'Authorization': f'token {github_token}',
                        'Accept': 'application/vnd.github.v3+json',
                        'User-Agent': 'CORA-Bot/1.0'
                    })
                    with urllib.request.urlopen(req, timeout=10) as response:
                        contents = json.loads(response.read().decode('utf-8'))

                    # Find Python files (check root and common dirs)
                    py_files = [f for f in contents if f['name'].endswith('.py') and f['type'] == 'file' and f['size'] < 50000]

                    # Also check src/, tools/, utils/ directories if they exist
                    for subdir in ['src', 'tools', 'utils', 'lib']:
                        subdir_entry = next((f for f in contents if f['name'] == subdir and f['type'] == 'dir'), None)
                        if subdir_entry:
                            try:
                                req = urllib.request.Request(subdir_entry['url'], headers={
                                    'Authorization': f'token {github_token}',
                                    'Accept': 'application/vnd.github.v3+json',
                                    'User-Agent': 'CORA-Bot/1.0'
                                })
                                with urllib.request.urlopen(req, timeout=5) as response:
                                    subdir_contents = json.loads(response.read().decode('utf-8'))
                                    py_files.extend([f for f in subdir_contents if f['name'].endswith('.py') and f['type'] == 'file' and f['size'] < 50000])
                            except:
                                pass

                    if py_files:
                        # Pick a random Python file
                        chosen_file = random.choice(py_files)
                        url = chosen_file['download_url']
                        code_name = f"{chosen_file['name']} (from {repo_name.split('/')[-1]})"
                        fetched_from_user_repo = True
                        print(f"  Selected: {chosen_file['name']}")

            except Exception as e:
                print(f"  [INFO] GitHub API access failed: {e}, falling back to public repos")

        # Fallback to public repos if no user repo available
        if not url:
            # Use GitHub API to find public Python repos dynamically
            fallback_repos = ["TheAlgorithms/Python", "geekcomputers/Python", "realpython/python-basics-exercises"]
            fallback_dirs = ["maths", "strings", "conversions", "searches", "sorts", "src", ""]

            for fallback_repo in fallback_repos:
                if url:
                    break
                try:
                    # Get repo contents
                    for check_dir in fallback_dirs:
                        if url:
                            break
                        try:
                            api_path = f"/repos/{fallback_repo}/contents/{check_dir}" if check_dir else f"/repos/{fallback_repo}/contents"
                            api_url = f"https://api.github.com{api_path}"
                            headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'CORA-Bot/1.0'}
                            if github_token:
                                headers['Authorization'] = f'token {github_token}'
                            req = urllib.request.Request(api_url, headers=headers)
                            with urllib.request.urlopen(req, timeout=8) as response:
                                contents = json.loads(response.read().decode('utf-8'))

                            # Find Python files under 30KB
                            py_files = [f for f in contents if isinstance(f, dict) and f.get('name', '').endswith('.py') and f.get('type') == 'file' and f.get('size', 0) < 30000]
                            if py_files:
                                chosen = random.choice(py_files)
                                url = chosen.get('download_url')
                                code_name = f"{chosen['name']} (from {fallback_repo.split('/')[-1]})"
                                print(f"  Found: {chosen['name']} in {fallback_repo}")
                        except:
                            continue
                except:
                    continue

            # Ultimate fallback - just try to get any Python file from the CORA project itself
            if not url:
                try:
                    # Use local file as last resort
                    local_files = list(Path(__file__).parent.glob("*.py"))
                    if local_files:
                        chosen_local = random.choice(local_files)
                        with open(chosen_local, 'r', encoding='utf-8') as f:
                            fetched_code = f.read()
                        code_name = f"{chosen_local.name} (local CORA)"
                        url = "local"
                        print(f"  Using local file: {chosen_local.name}")
                except:
                    pass

        print(f"  Fetching: {code_name}")
        display_tool("Code Import", f"GitHub - {code_name}")
        display_action(f"Importing code from GitHub...")

        # Show code modal popup
        code_window = None
        code_text = None
        try:
            import tkinter as tk

            parent = _boot_display.root if _boot_display else None
            code_window = create_code_window(
                title=f"CORA - Code Import: {code_name}",
                width=900, height=600,
                parent=parent
            )

            # Header
            header = tk.Label(
                code_window,
                text=f"Importing: {code_name}",
                font=('Consolas', 12, 'bold'),
                fg='#00ff88',
                bg='#1e1e1e',
                pady=10
            )
            header.pack(fill='x')

            # Source URL
            source_text = "Source: Local CORA file" if url == "local" else f"Source: GitHub API"
            url_label = tk.Label(
                code_window,
                text=source_text,
                font=('Consolas', 9),
                fg='#888888',
                bg='#1e1e1e'
            )
            url_label.pack(fill='x', padx=10)

            # Code display area with scrollbar
            code_frame = tk.Frame(code_window, bg='#1e1e1e')
            code_frame.pack(fill='both', expand=True, padx=10, pady=5)

            scrollbar = tk.Scrollbar(code_frame)
            scrollbar.pack(side='right', fill='y')

            code_text = tk.Text(
                code_frame,
                font=('Consolas', 10),
                fg='#d4d4d4',
                bg='#1e1e2e',
                insertbackground='white',
                padx=10,
                pady=10,
                wrap='none',
                yscrollcommand=scrollbar.set
            )
            code_text.pack(fill='both', expand=True, side='left')
            scrollbar.config(command=code_text.yview)

            code_text.insert('1.0', f"Fetching code...\n\nSource: {'Local' if url == 'local' else 'GitHub API'}\n\nPlease wait...")
            code_text.config(state='disabled')
            code_window.update()

        except Exception as e:
            print(f"  [INFO] Code modal creation failed: {e}")
            code_window = None

        # Fetch the actual code (skip if already loaded from local)
        try:
            if url != "local":
                req = urllib.request.Request(url, headers={'User-Agent': 'CORA-Bot/1.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    fetched_code = response.read().decode('utf-8')

            # Limit to first 100 lines for display
            code_lines = fetched_code.split('\n')
            display_code = '\n'.join(code_lines[:100])
            if len(code_lines) > 100:
                display_code += f"\n\n... [{len(code_lines) - 100} more lines] ..."

            print(f"  [OK] Fetched {len(code_lines)} lines of {lang} code")
            display_result(f"Imported {len(code_lines)} lines from GitHub")
            BOOT_STATUS['tools_tested'].append({'name': 'Code Import', 'status': 'OK'})

            # Update modal with actual code
            if code_window and code_text:
                try:
                    source_info = "Local CORA project" if url == "local" else "GitHub API"
                    code_text.config(state='normal')
                    code_text.delete('1.0', 'end')
                    code_text.insert('1.0', f"# {code_name}\n# Source: {source_info}\n# Lines: {len(code_lines)}\n\n{display_code}")
                    code_text.config(state='disabled')
                    code_window.update()
                except:
                    pass

            # CORA announces code import - just the data
            if fetched_from_user_repo:
                response = cora_respond("Code Import", f"Pulled {len(code_lines)} lines from your GitHub.", "ok")
            else:
                response = cora_respond("Code Import", f"Pulled {len(code_lines)} lines of {code_name} from GitHub.", "ok")
            speak(response)

            display_phase("4.1 Code Import", "ok")

        except Exception as fetch_error:
            print(f"  [WARN] GitHub fetch failed: {fetch_error}")
            display_log(f"GitHub fetch failed: {fetch_error}", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'Code Import', 'status': 'WARN'})
            display_phase("4.1 Code Import", "warn")

            response = cora_respond("Code Import", "GitHub unreachable.", "warn")
            speak(response)

        # Close code window after speaking
        if code_window:
            try:
                code_window.destroy()
            except:
                pass

    except Exception as e:
        print(f"  [WARN] Code import test: {e}")
        display_log(f"Code import error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Code Import', 'status': 'WARN'})
        display_phase("4.1 Code Import", "warn")

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 4.2: YOUTUBE VIDEO TEST - Search and play a wild video
    # ================================================================
    display_phase("4.2 YouTube Test", "running")
    display_log("PHASE 4.2: YOUTUBE VIDEO TEST", "phase")
    print("\n[PHASE 4.2] YouTube Video Test")
    print("=" * 50)

    try:
        import random
        import subprocess
        import threading

        # Wild and crazy search terms for random videos
        wild_searches = [
            "most insane parkour fails",
            "crazy car stunts compilation",
            "extreme sports fails 2024",
            "funny cat videos compilation",
            "satisfying domino chain reaction",
            "best magic tricks revealed",
            "insane drone racing",
            "extreme skateboard tricks",
            "world record attempts gone wrong",
            "crazy science experiments",
            "best beatbox battles",
            "amazing street performers",
        ]

        search_term = random.choice(wild_searches)
        print(f"  Searching YouTube: {search_term}")
        display_tool("YouTube", f"Searching: {search_term}")
        display_action(f"Finding a wild video...")

        # Show video info modal
        video_window = None
        status_text = None
        try:
            import tkinter as tk

            parent = _boot_display.root if _boot_display else None
            video_window = create_popup(
                title="CORA - YouTube Video Test",
                width=700, height=450,
                bg='#1a1a2e',
                parent=parent
            )

            # Header
            header = tk.Label(
                video_window,
                text=f"🎬 YouTube: {search_term}",
                font=('Segoe UI', 14, 'bold'),
                fg='#ff0000',
                bg='#1a1a2e',
                pady=15
            )
            header.pack(fill='x')

            # Video info display
            status_text = tk.Text(
                video_window,
                font=('Consolas', 11),
                fg='#ffffff',
                bg='#16213e',
                height=15,
                padx=15,
                pady=15,
                wrap='word'
            )
            status_text.pack(fill='both', expand=True, padx=15, pady=10)
            status_text.insert('1.0', f"🔍 Searching YouTube for:\n   \"{search_term}\"\n\nPlease wait...")
            status_text.config(state='disabled')
            video_window.update()

        except Exception as e:
            print(f"  [INFO] Video modal creation failed: {e}")
            video_window = None

        # Try to find and play video using yt-dlp
        video_title = None
        video_url = None
        played_ok = False

        try:
            # Use yt-dlp to search and get video info
            search_cmd = ['yt-dlp', '--get-title', '--get-id', '-f', 'best', f'ytsearch1:{search_term}']
            result = subprocess.run(search_cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    video_title = lines[0]
                    video_id = lines[1]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    print(f"  [OK] Found: {video_title[:50]}...")
                    display_result(f"Found: {video_title[:40]}...")

                    # Update modal with video info
                    if video_window and status_text:
                        try:
                            status_text.config(state='normal')
                            status_text.delete('1.0', 'end')
                            status_text.insert('1.0', f"🎬 FOUND VIDEO:\n\n")
                            status_text.insert('end', f"Title: {video_title}\n\n")
                            status_text.insert('end', f"URL: {video_url}\n\n")
                            status_text.insert('end', f"Search: {search_term}\n\n")
                            status_text.insert('end', "▶ Playing with mpv in background...\n")
                            status_text.config(state='disabled')
                            video_window.update()
                        except:
                            pass

                    # Play the video using mpv WITH video in a window (10 seconds)
                    def play_video():
                        try:
                            # Play 10 seconds WITH video in mpv window
                            subprocess.run(
                                ['mpv',
                                 '--length=10',           # Play 10 seconds
                                 '--geometry=640x360',    # Small window
                                 '--title=CORA YouTube Test',
                                 '--ontop',               # Keep on top during test
                                 '--no-terminal',
                                 video_url],
                                capture_output=True, timeout=20
                            )
                        except:
                            pass

                    play_thread = threading.Thread(target=play_video, daemon=True)
                    play_thread.start()
                    played_ok = True

                    # Give mpv a moment to start
                    responsive_sleep(1)

        except subprocess.TimeoutExpired:
            print("  [WARN] yt-dlp search timed out")
        except FileNotFoundError:
            print("  [WARN] yt-dlp not installed")
        except Exception as e:
            print(f"  [WARN] Video search error: {e}")

        if played_ok:
            BOOT_STATUS['tools_tested'].append({'name': 'YouTube Playback', 'status': 'OK'})
            display_phase("4.2 YouTube Test", "ok")

            # CORA announces YouTube - just the result
            response = cora_respond("YouTube Test", f"Found: {video_title[:40] if video_title else 'video'}. Playing sample.", "ok")
            speak(response)
        else:
            # Update modal with fallback info
            if video_window and status_text:
                try:
                    status_text.config(state='normal')
                    status_text.delete('1.0', 'end')
                    status_text.insert('1.0', f"⚠ YouTube Search: {search_term}\n\n")
                    status_text.insert('end', "Could not play video directly.\n")
                    status_text.insert('end', "yt-dlp or mpv might not be installed.\n\n")
                    status_text.insert('end', "YouTube features available:\n")
                    status_text.insert('end', "  • 'play <search>' - Search and play\n")
                    status_text.insert('end', "  • 'play <youtube url>' - Direct URL\n")
                    status_text.config(state='disabled')
                    video_window.update()
                except:
                    pass

            BOOT_STATUS['tools_tested'].append({'name': 'YouTube Playback', 'status': 'WARN'})
            display_phase("4.2 YouTube Test", "warn")

            response = cora_respond("YouTube Test", "YouTube search works. Playback needs yt-dlp and mpv.", "warn")
            speak(response)

        # Close video window after speaking
        if video_window:
            try:
                video_window.destroy()
            except:
                pass

    except Exception as e:
        print(f"  [WARN] YouTube test: {e}")
        display_log(f"YouTube test error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'YouTube Test', 'status': 'WARN'})
        display_phase("4.2 YouTube Test", "warn")

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 4.3: MODAL WINDOWS TEST
    # ================================================================
    display_phase("4.3 Modal Windows", "running")
    display_log("PHASE 4.3: MODAL WINDOWS TEST", "phase")
    print("\n[PHASE 4.3] Modal Windows Test")
    print("=" * 50)

    try:
        import tkinter as tk
        import random

        # Random modal content for variety
        modal_quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Stay hungry, stay foolish. - Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It does not matter how slowly you go as long as you do not stop. - Confucius",
            "The best way to predict the future is to invent it. - Alan Kay",
            "Code is like humor. When you have to explain it, it's bad. - Cory House",
            "First, solve the problem. Then, write the code. - John Johnson",
        ]

        quote = random.choice(modal_quotes)

        # Test message modal
        print("  Testing message modal...")
        display_action("Opening test message modal...")

        # Use window manager for proper z-layering
        parent = _boot_display.root if _boot_display else None
        msg_window = create_popup(
            title="CORA - Modal Test",
            width=500, height=300,
            bg='#2d2d2d',
            parent=parent
        )

        # Content
        title_label = tk.Label(
            msg_window,
            text="Modal Window Test",
            font=('Segoe UI', 14, 'bold'),
            fg='#00ff88',
            bg='#2d2d2d',
            pady=15
        )
        title_label.pack(fill='x')

        quote_label = tk.Label(
            msg_window,
            text=quote,
            font=('Segoe UI', 11),
            fg='#ffffff',
            bg='#2d2d2d',
            wraplength=450,
            pady=20
        )
        quote_label.pack(fill='x', padx=20)

        status_label = tk.Label(
            msg_window,
            text="Modal Types Available:\n- Message popups\n- Code viewer with syntax highlighting\n- Image viewer\n- Terminal output\n- File viewer",
            font=('Consolas', 10),
            fg='#888888',
            bg='#2d2d2d',
            justify='left'
        )
        status_label.pack(fill='x', padx=20, pady=10)

        msg_window.update()

        print("  [OK] Message modal displayed")
        display_result("Modal windows working correctly")
        BOOT_STATUS['tools_tested'].append({'name': 'Modal Windows', 'status': 'OK'})
        display_phase("4.3 Modal Windows", "ok")

        response = cora_respond("Modal Windows", "Modal windows working.", "ok")
        speak(response)

        # Close modal after speaking
        try:
            msg_window.destroy()
        except:
            pass

    except Exception as e:
        print(f"  [WARN] Modal windows test: {e}")
        display_log(f"Modal windows error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Modal Windows', 'status': 'WARN'})
        display_phase("4.3 Modal Windows", "warn")

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 5: VOICE SYSTEMS
    # ================================================================
    display_phase("5.0 Voice Systems", "running")
    display_log("PHASE 5: VOICE SYSTEMS", "phase")
    print("\n[PHASE 5] Voice Systems")
    print("=" * 50)

    # Speech Recognition
    try:
        from voice.stt import SpeechRecognizer
        print("  [OK] Speech Recognition (STT)")
        display_log("Speech Recognition (STT) loaded", "ok")
        BOOT_STATUS['systems'].append({'name': 'Speech Recognition', 'status': 'OK'})
    except Exception as e:
        print(f"  [WARN] Speech Recognition: {e}")
        display_log(f"Speech Recognition: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'Speech Recognition', 'status': 'WARN'})

    # Echo Filter
    try:
        from voice.echo_filter import EchoFilter
        print("  [OK] Echo Filter")
        display_log("Echo Filter loaded", "ok")
        BOOT_STATUS['systems'].append({'name': 'Echo Filter', 'status': 'OK'})
    except Exception as e:
        print(f"  [WARN] Echo Filter: {e}")
        display_log(f"Echo Filter: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'Echo Filter', 'status': 'WARN'})

    # Wake Word (if available)
    try:
        from voice.wake_word import WakeWordDetector
        print("  [OK] Wake Word Detection")
        display_log("Wake Word Detection loaded", "ok")
        BOOT_STATUS['systems'].append({'name': 'Wake Word', 'status': 'OK'})
    except Exception as e:
        print(f"  [INFO] Wake Word: {e}")
        display_log(f"Wake Word: {e}", "info")
        BOOT_STATUS['systems'].append({'name': 'Wake Word', 'status': 'INFO'})

    display_phase("5.0 Voice Systems", "ok")
    # Voice summary - just status
    voice_result = "Voice systems online. Wake word active."
    response = cora_respond("Voice Systems check", voice_result, "ok")
    speak(response)
    responsive_sleep(0.3)

    # ================================================================
    # PHASE 6: EXTERNAL SERVICES
    # ================================================================
    display_phase("6.0 External APIs", "running")
    display_log("PHASE 6: EXTERNAL SERVICES", "phase")
    print("\n[PHASE 6] External Services")
    print("=" * 50)

    # GET LOCATION FIRST - needed for accurate weather
    location_str = None
    city_for_weather = None
    try:
        from services.location import get_location
        display_tool("Location Service", "Getting current location")
        loc = get_location()
        if loc:
            city = loc.get('city', '')
            region = loc.get('region', loc.get('state', ''))
            country = loc.get('country', '')
            # Build location string from available data
            loc_parts = [p for p in [city, region, country] if p]
            location_str = ', '.join(loc_parts) if loc_parts else None
            # Use city for weather lookup
            city_for_weather = city if city else None
            if location_str:
                print(f"  [OK] Location: {location_str}")
                display_result(f"We're in {location_str}")
                BOOT_STATUS['location'] = loc
                BOOT_STATUS['systems'].append({'name': 'Location', 'status': 'OK'})
                # CORA announces location
                response = cora_respond("Location check", f"Location: {location_str}", "ok")
                speak(response)
            else:
                print("  [WARN] Location data incomplete")
                display_log("Location data incomplete", "warn")
                BOOT_STATUS['systems'].append({'name': 'Location', 'status': 'WARN'})
        else:
            print("  [WARN] Location unavailable")
            display_log("Location unavailable", "warn")
            BOOT_STATUS['systems'].append({'name': 'Location', 'status': 'WARN'})
    except Exception as e:
        print(f"  [WARN] Location: {e}")
        display_log(f"Location: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'Location', 'status': 'WARN'})

    # NOW GET WEATHER using location
    weather_data = None
    forecast_data = None
    try:
        from services.weather import get_weather, get_forecast
        # Pass location to weather service
        weather_data = get_weather(city_for_weather)
        forecast_data = get_forecast(city_for_weather, days=3)  # Get 3-day forecast

        if weather_data and weather_data.get('success'):
            temp = weather_data.get('temp', '?')
            cond = weather_data.get('conditions', '?')
            feels = weather_data.get('feels_like', '')
            humidity = weather_data.get('humidity', '')
            wind = weather_data.get('wind', '')

            print(f"  [OK] Current Weather for {city_for_weather or 'your area'}: {temp}, {cond}")
            display_log(f"Current: {temp}, {cond}", "ok")
            if feels:
                display_log(f"  Feels like: {feels}", "info")
            if humidity:
                display_log(f"  Humidity: {humidity}", "info")
            if wind:
                display_log(f"  Wind: {wind}", "info")

            BOOT_STATUS['weather'] = weather_data
            BOOT_STATUS['systems'].append({'name': 'Weather', 'status': 'OK'})

            # Get 3-day forecast info
            if forecast_data and forecast_data.get('success') and forecast_data.get('forecast'):
                print(f"  [OK] 3-Day Forecast:")
                display_log("3-Day Forecast:", "ok")
                for day in forecast_data['forecast']:
                    day_name = day.get('day_name', 'Unknown')
                    high = day.get('high', '?')
                    low = day.get('low', '?')
                    conditions = day.get('conditions', '')
                    print(f"       {day_name}: High {high}, Low {low} - {conditions}")
                    display_log(f"  {day_name}: {high}/{low} - {conditions}", "info")
                BOOT_STATUS['forecast'] = forecast_data
        else:
            print("  [WARN] Weather service unavailable")
            display_log("Weather service unavailable", "warn")
            BOOT_STATUS['systems'].append({'name': 'Weather', 'status': 'WARN'})
    except Exception as e:
        print(f"  [WARN] Weather: {e}")
        display_log(f"Weather: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'Weather', 'status': 'WARN'})

    # Notifications
    try:
        from services.notifications import notify
        print("  [OK] Notifications")
        display_log("Notifications system loaded", "ok")
        BOOT_STATUS['systems'].append({'name': 'Notifications', 'status': 'OK'})
    except Exception as e:
        print(f"  [WARN] Notifications: {e}")
        display_log(f"Notifications: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'Notifications', 'status': 'WARN'})

    # Hotkeys
    try:
        from services.hotkeys import setup_cora_hotkeys
        print("  [OK] Hotkey System")
        display_log("Hotkey System loaded", "ok")
        BOOT_STATUS['systems'].append({'name': 'Hotkeys', 'status': 'OK'})
    except Exception as e:
        print(f"  [WARN] Hotkeys: {e}")
        display_log(f"Hotkeys: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'Hotkeys', 'status': 'WARN'})

    display_phase("6.0 External APIs", "ok")

    # Helper to convert temp like "61F" to "61 degrees fahrenheit"
    def speak_temp(temp_str):
        if not temp_str or temp_str == '?' or temp_str == 'N/A':
            return "unknown"
        # Remove F and convert to natural speech
        temp_str = temp_str.replace('F', '').replace('°', '').strip()
        return f"{temp_str} degrees"

    # Build weather report with 3-day forecast - natural speech
    # Location already announced separately, so just do weather
    weather_report = ""
    if weather_data and weather_data.get('success'):
        temp = weather_data.get('temp', '?')
        cond = weather_data.get('conditions', '?')
        # Convert temp for natural speech
        temp_spoken = speak_temp(temp)
        weather_report += f"Currently {temp_spoken} and {cond.lower()}. "
        if forecast_data and forecast_data.get('success') and forecast_data.get('forecast'):
            # Today's forecast with conditions
            today = forecast_data['forecast'][0]
            today_high = speak_temp(today.get('high', '?'))
            today_low = speak_temp(today.get('low', '?'))
            today_cond = today.get('conditions', '')
            if today_cond:
                weather_report += f"Today will be {today_cond.lower()} with a high of {today_high} and a low of {today_low}. "
            else:
                weather_report += f"Today the high will be {today_high} and the low will be {today_low}. "
            # Rest of the week with conditions
            if len(forecast_data['forecast']) > 1:
                for day in forecast_data['forecast'][1:]:
                    day_name = day.get('day_name', '')
                    day_high = speak_temp(day.get('high', '?'))
                    day_low = speak_temp(day.get('low', '?'))
                    day_cond = day.get('conditions', '')
                    if day_cond:
                        weather_report += f"{day_name} will be {day_cond.lower()} with a high of {day_high} and a low of {day_low}. "
                    else:
                        weather_report += f"{day_name} the high will be {day_high} and the low will be {day_low}. "
    else:
        weather_report += "Weather unavailable."

    response = cora_respond("Location and Weather", weather_report, "ok" if weather_data else "warn", mode="full")
    speak(response)
    responsive_sleep(0.3)

    # ================================================================
    # PHASE 6.1: YOUTUBE/AUDIO PLAYBACK TEST
    # ================================================================
    display_phase("6.1 Audio Test", "running")
    display_log("PHASE 6.1: AUDIO PLAYBACK TEST", "phase")
    print("\n[PHASE 6.1] Audio Playback Test")
    print("=" * 50)

    try:
        import subprocess
        import random

        # Random audio test options
        audio_tests = [
            {"query": "lofi hip hop beats", "name": "Lofi Hip Hop"},
            {"query": "synthwave music", "name": "Synthwave"},
            {"query": "ambient space music", "name": "Ambient Space"},
            {"query": "jazz piano relaxing", "name": "Jazz Piano"},
            {"query": "classical piano beautiful", "name": "Classical Piano"},
            {"query": "cyberpunk music mix", "name": "Cyberpunk Mix"},
        ]

        test = random.choice(audio_tests)
        test_name = test['name']
        test_query = test['query']

        print(f"  Testing audio playback: {test_name}")
        display_tool("Audio Playback", f"Testing: {test_name}")
        display_action(f"Searching YouTube for: {test_query}")

        # Use yt-dlp to search and get video URL, then play with mpv
        video_url = None
        mpv_process = None

        try:
            # Search with yt-dlp
            result = subprocess.run(
                ['yt-dlp', '--get-url', '--format', 'bestaudio', f'ytsearch1:{test_query}'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                video_url = result.stdout.strip().split('\n')[0]
                print(f"  Found audio stream URL")
        except FileNotFoundError:
            print(f"  [WARN] yt-dlp not installed")
            display_log("yt-dlp not installed - skipping audio test", "warn")
        except Exception as e:
            print(f"  [WARN] yt-dlp search failed: {e}")

        if video_url:
            try:
                # Play audio with mpv (no video, 8 second limit)
                print(f"  Playing with mpv...")
                display_result(f"Playing: {test_name}")

                mpv_process = subprocess.Popen(
                    ['mpv', '--no-video', '--length=8', '--really-quiet', '--no-terminal', video_url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'OK'})
                BOOT_STATUS['audio_test'] = test_name

                # Let it play for a bit, then speak while it's playing
                responsive_sleep(2)

                response = cora_respond("Audio Playback", f"Audio working. Playing {test_name}.", "ok")
                speak(response)

                # Wait for mpv to finish (max 8 sec total)
                try:
                    mpv_process.wait(timeout=6)
                except subprocess.TimeoutExpired:
                    mpv_process.terminate()

                display_phase("6.1 Audio Test", "ok")

            except FileNotFoundError:
                print(f"  [WARN] mpv not installed")
                display_log("mpv not installed - skipping audio test", "warn")
                BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'WARN'})
                display_phase("6.1 Audio Test", "warn")
            except Exception as e:
                print(f"  [WARN] mpv playback failed: {e}")
                display_log(f"mpv playback failed: {e}", "warn")
                BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'WARN'})
                display_phase("6.1 Audio Test", "warn")
        else:
            print(f"  [WARN] Could not find audio to play")
            display_log("Could not find audio stream", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'WARN'})
            display_phase("6.1 Audio Test", "warn")

            response = cora_respond("Audio Playback", "Audio skipped. Need yt-dlp and mpv.", "warn")
            speak(response)

    except Exception as e:
        print(f"  [WARN] Audio playback test: {e}")
        display_log(f"Audio playback error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Audio Playback', 'status': 'WARN'})
        display_phase("6.1 Audio Test", "warn")

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 7: NEWS HEADLINES
    # ================================================================
    display_phase("7.0 News Headlines", "running")
    display_log("PHASE 7: NEWS HEADLINES", "phase")
    print("\n[PHASE 7] News Headlines")
    print("=" * 50)

    headlines = []
    try:
        import requests
        import re
        print("  Fetching top headlines from Google News...")
        display_tool("HTTP Request", "Fetching Google News RSS")
        display_action("GET https://news.google.com/rss")

        # Use Google News RSS for real headlines
        url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
        resp = requests.get(url, timeout=10)

        if resp.status_code == 200:
            display_result(f"HTTP 200 OK - {len(resp.text)} bytes")
            display_action("Parsing RSS feed for headlines...")

            # Parse RSS titles
            titles = re.findall(r'<title>([^<]+)</title>', resp.text)

            # Skip first 2 (channel title and description)
            for t in titles[2:7]:
                # Clean up the headline
                headline = t.strip()
                if headline and len(headline) > 10:
                    headlines.append(headline)

            print("  [OK] News fetch successful")
            display_result(f"Found {len(headlines)} headlines")
            BOOT_STATUS['tools_tested'].append({'name': 'News Headlines', 'status': 'OK'})

            for i, hl in enumerate(headlines[:3], 1):
                print(f"  {i}. {hl[:75]}...")
                display_log(f"Headline {i}: {hl[:60]}...", "info")

            BOOT_STATUS['headlines'] = headlines

            # Announce top 3-4 headlines
            if headlines:
                display_phase("7.0 News Headlines", "ok")
                # Clean headlines for speech
                clean_headlines = []
                for hl in headlines[:4]:
                    clean = hl.split(' - ')[0] if ' - ' in hl else hl
                    if len(clean) > 100:
                        clean = clean[:97] + "..."
                    clean_headlines.append(clean)

                # News - full mode for longer content
                news_data = "Top headlines: " + ". ".join(clean_headlines)
                response = cora_respond("News Headlines", news_data, "ok", mode="full")
                speak(response)
            else:
                display_phase("7.0 News Headlines", "warn")
                response = cora_respond("News Headlines", "No headlines found.", "warn")
                speak(response)
        else:
            print("  [WARN] News fetch failed")
            display_log(f"News fetch failed (HTTP {resp.status_code})", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'News Headlines', 'status': 'WARN'})
            display_phase("7.0 News Headlines", "warn")
            response = cora_respond("News Headlines", f"News failed. HTTP {resp.status_code}.", "fail")
            speak(response)

    except Exception as e:
        print(f"  [WARN] News fetch: {e}")
        display_log(f"News fetch error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Web Search', 'status': 'WARN'})
        display_phase("7.0 News Headlines", "warn")
        response = cora_respond("News Headlines", "News fetch error.", "fail")
        speak(response)

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 8: VISION TEST (Screenshot + Camera)
    # ================================================================
    display_phase("8.0 Vision Test", "running")
    display_log("PHASE 8: VISION TEST", "phase")
    print("\n[PHASE 8] Vision System Test")
    print("=" * 50)

    # Test screenshot capture
    try:
        from cora_tools.screenshots import desktop, quick_screenshot
        print("  Testing screenshot capture...")
        display_tool("Screenshots", "Capturing desktop")
        display_action("Taking screenshot of current display...")

        result = desktop()
        if result.success:
            print(f"  [OK] Screenshot captured: {result.path}")
            print(f"       Resolution: {result.width}x{result.height}")
            display_result(f"Screenshot: {result.width}x{result.height}")
            display_action(f"Saved to: {result.path}")
            BOOT_STATUS['tools_tested'].append({'name': 'Screenshot Capture', 'status': 'OK'})
            BOOT_STATUS['screenshot_path'] = result.path

            # Show screenshot popup (5 seconds like image gen)
            try:
                import tkinter as tk
                from PIL import Image, ImageTk

                # Use window manager for proper z-layering
                parent = _boot_display.root if _boot_display else None
                ss_window = create_image_window(
                    title="CORA - Screenshot Capture",
                    width=1280, height=720,
                    parent=parent
                )

                # Load and display screenshot
                img = Image.open(result.path)
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=ss_window)

                label = tk.Label(ss_window, image=photo, bg='black')
                label.image = photo
                label.pack(fill='both', expand=True)
                ss_window.update()
                display_action("Showing screenshot for 5 seconds...")
            except Exception as e:
                print(f"  [INFO] Screenshot popup failed: {e}")
                ss_window = None

            # Use AI vision to describe what CORA sees on screen
            screen_description = None
            try:
                from ai.ollama import generate_with_image
                display_action("Analyzing screenshot with AI vision...")
                vision_result = generate_with_image(
                    prompt="What do you see on this screen? Describe the specific windows, apps, content, or anything interesting. Be detailed.",
                    image_path=result.path,
                    system=get_system_prompt(),
                    model="llava"
                )
                if vision_result and vision_result.content:
                    screen_description = vision_result.content.strip()
                    # Clean markdown
                    screen_description = re.sub(r'\*\*([^*]+)\*\*', r'\1', screen_description)
                    screen_description = re.sub(r'\*([^*]+)\*', r'\1', screen_description)
                    screen_description = re.sub(r'\n+', ' ', screen_description)
                    screen_description = re.sub(r'\s+', ' ', screen_description).strip()
                    print(f"  CORA sees: {screen_description}")
                    display_result(f"Vision: {screen_description[:80]}...")
                    BOOT_STATUS['screenshot_description'] = screen_description
            except Exception as e:
                print(f"  [INFO] Vision analysis skipped: {e}")

            # CORA speaks what she sees - the actual description
            if screen_description:
                speak(screen_description)
            else:
                response = cora_respond("Screenshot capture", f"Screenshot {result.width}x{result.height}. Vision failed.", "warn")
                speak(response)

            # Close screenshot popup after speaking
            if ss_window:
                try:
                    ss_window.destroy()
                except:
                    pass
        else:
            print(f"  [WARN] Screenshot failed: {result.error}")
            display_log(f"Screenshot failed: {result.error}", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'Screenshot Capture', 'status': 'WARN'})
    except Exception as e:
        print(f"  [WARN] Screenshot test: {e}")
        display_log(f"Screenshot error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Screenshot Capture', 'status': 'WARN'})

    # Test camera if available - try multiple camera indices
    try:
        import cv2
        print("  Testing camera...")
        display_tool("OpenCV", "Accessing camera device")

        # Try camera indices 0, 1, 2 (some systems have multiple cameras)
        cap = None
        frame = None
        working_index = -1

        for cam_index in [0, 1, 2]:
            display_action(f"Trying camera index {cam_index}...")
            test_cap = cv2.VideoCapture(cam_index)
            if test_cap.isOpened():
                # Try to read a frame - some cameras open but don't capture
                ret, test_frame = test_cap.read()
                if ret and test_frame is not None:
                    cap = test_cap
                    frame = test_frame
                    working_index = cam_index
                    display_result(f"Camera {cam_index} working!")
                    break
                else:
                    display_action(f"Camera {cam_index} opened but no frame")
                    test_cap.release()
            else:
                test_cap.release()

        if cap is not None and frame is not None:
            print(f"  [OK] Camera {working_index} working: {frame.shape[1]}x{frame.shape[0]}")
            display_result(f"Camera {working_index}: {frame.shape[1]}x{frame.shape[0]}")
            BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'OK'})
            BOOT_STATUS['camera_available'] = True
            BOOT_STATUS['camera_index'] = working_index

            # Save test frame
            cam_dir = PROJECT_DIR / 'data' / 'camera'
            cam_dir.mkdir(parents=True, exist_ok=True)
            cam_path = cam_dir / 'boot_test.jpg'
            display_action(f"Saving camera frame to {cam_path}")
            cv2.imwrite(str(cam_path), frame)
            print(f"       Test frame saved: {cam_path}")
            display_result("Camera frame saved successfully")
            BOOT_STATUS['camera_path'] = str(cam_path)

            # Show camera popup (like screenshot and image gen)
            cam_window = None
            try:
                import tkinter as tk
                from PIL import Image, ImageTk

                # Use window manager for proper z-layering
                parent = _boot_display.root if _boot_display else None
                cam_window = create_image_window(
                    title="CORA - Camera View",
                    width=1280, height=720,
                    parent=parent
                )

                # Load and display camera image
                img = Image.open(cam_path)
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=cam_window)

                label = tk.Label(cam_window, image=photo, bg='black')
                label.image = photo
                label.pack(fill='both', expand=True)
                cam_window.update()
                display_action("Showing camera view for 5 seconds...")
            except Exception as e:
                print(f"  [INFO] Camera popup failed: {e}")
                cam_window = None

            # Use AI vision to describe what CORA sees through camera
            camera_description = None
            try:
                from ai.ollama import generate_with_image
                display_action("Analyzing camera with AI vision...")
                vision_result = generate_with_image(
                    prompt="What do you see through this camera? Describe the person, their appearance, the room, objects, or anything interesting. Be detailed and specific.",
                    image_path=str(cam_path),
                    system=get_system_prompt(),
                    model="llava"
                )
                if vision_result and vision_result.content:
                    camera_description = vision_result.content.strip()
                    # Clean markdown
                    camera_description = re.sub(r'\*\*([^*]+)\*\*', r'\1', camera_description)
                    camera_description = re.sub(r'\*([^*]+)\*', r'\1', camera_description)
                    camera_description = re.sub(r'\n+', ' ', camera_description)
                    camera_description = re.sub(r'\s+', ' ', camera_description).strip()
                    print(f"  CORA sees: {camera_description}")
                    display_result(f"Vision: {camera_description[:80]}...")
                    BOOT_STATUS['camera_description'] = camera_description
            except Exception as e:
                print(f"  [INFO] Camera vision analysis skipped: {e}")

            # CORA speaks what she sees - the actual description
            if camera_description:
                speak(camera_description)
            else:
                response = cora_respond("Camera system", "Camera working. Vision failed.", "warn")
                speak(response)

            # Close camera popup after speaking
            if cam_window:
                try:
                    cam_window.destroy()
                except:
                    pass
            else:
                print("  [WARN] Camera opened but no frame")
                display_log("Camera opened but no frame captured", "warn")
                BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'WARN'})
            cap.release()
            display_action("Camera released")
        else:
            print("  [INFO] No camera detected")
            display_log("No camera detected", "info")
            BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'INFO'})
            BOOT_STATUS['camera_available'] = False
    except ImportError:
        print("  [INFO] OpenCV not installed - camera unavailable")
        display_log("OpenCV not installed - camera unavailable", "info")
        BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'INFO'})
    except Exception as e:
        print(f"  [WARN] Camera test: {e}")
        display_log(f"Camera error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'WARN'})

    display_phase("8.0 Vision Test", "ok")
    # CORA generates her own overall vision response - natural speech
    screenshot_ok = any(t['name'] == 'Screenshot Capture' and t['status'] == 'OK' for t in BOOT_STATUS['tools_tested'])
    camera_ok = BOOT_STATUS.get('camera_available', False)
    if screenshot_ok and camera_ok:
        vision_result = "Screenshot and camera both online."
    elif screenshot_ok:
        vision_result = "Screenshot working, no camera."
    elif camera_ok:
        vision_result = "Camera working, screenshot failed."
    else:
        vision_result = "Vision systems failed."
    response = cora_respond("Vision Systems summary", vision_result, "ok")
    speak(response)
    responsive_sleep(0.3)

    # ================================================================
    # PHASE 9: IMAGE GENERATION TEST
    # ================================================================
    display_phase("9.0 Image Gen", "running")
    display_log("PHASE 9: IMAGE GENERATION", "phase")
    print("\n[PHASE 9] Image Generation Test")
    print("=" * 50)

    try:
        from cora_tools.image_gen import generate_image, show_fullscreen_image
        print("  [OK] Image generation module loaded (Pollinations Flux)")
        display_log("Pollinations Flux module loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Image Generation', 'status': 'OK'})

        # Have CORA generate her own unique prompt using Ollama
        print("  Asking CORA for a fucked up image idea...")
        display_thinking("Creating something dark and twisted...")

        import random
        random_seed = random.randint(1, 999999999)
        cora_prompt = None

        try:
            from ai.ollama import generate

            display_action("CORA is dreaming up something disturbing...")
            result = generate(
                prompt="Generate a fucked up crazy image thats disturbing",
                system=get_system_prompt(),
                temperature=1.2,
                max_tokens=60
            )

            if result.content and len(result.content) > 10:
                cora_prompt = result.content.strip()
                # Clean up the prompt
                cora_prompt = cora_prompt.strip('"\'').strip()
                cora_prompt = re.sub(r'\*\*([^*]+)\*\*', r'\1', cora_prompt)
                cora_prompt = re.sub(r'\*([^*]+)\*', r'\1', cora_prompt)
                cora_prompt = re.sub(r'\n+', ' ', cora_prompt)
                cora_prompt = re.sub(r'\s+', ' ', cora_prompt).strip()
                print(f"  CORA's vision: {cora_prompt}")
                display_result(f"Vision: {cora_prompt}")
        except Exception as e:
            print(f"  [INFO] AI prompt generation skipped: {e}")

        # Fallback if AI fails
        if not cora_prompt:
            cora_prompt = "Generate a fucked up crazy image thats disturbing"
            print(f"  Using fallback prompt")

        print(f"  Seed: {random_seed}")

        print("  Generating via Pollinations Flux model...")
        display_tool("Pollinations API", f"Generating 1280x720 image")
        display_action(f"Prompt: {cora_prompt}")

        result = generate_image(
            prompt=cora_prompt,
            width=1280,
            height=720,
            model="flux",
            seed=random_seed,
            nologo=True
        )

        if result.get('success'):
            img_path = result.get('path')
            gen_time = result.get('inference_time', 0)
            print(f"  [OK] Image generated: {img_path}")
            print(f"       Time: {gen_time:.1f}s")
            display_result(f"Image generated in {gen_time:.1f}s")
            display_action(f"Saving to: {img_path}")
            BOOT_STATUS['boot_image'] = img_path

            print("  Displaying image...")
            display_action("Opening image display window...")

            # Show image in a window
            img_window = None
            try:
                import tkinter as tk
                from PIL import Image, ImageTk

                # Use window manager for proper z-layering
                parent = _boot_display.root if _boot_display else None
                img_window = create_image_window(
                    title="CORA - Image Generation Test",
                    width=1280, height=720,
                    parent=parent
                )

                # Load and display image
                img = Image.open(img_path)
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=img_window)

                label = tk.Label(img_window, image=photo, bg='black')
                label.image = photo  # Keep reference
                label.pack(fill='both', expand=True)

                img_window.update()
                display_result("Image displayed successfully")

            except Exception as e:
                print(f"  [INFO] Image display skipped: {e}")
                display_log(f"Image display skipped: {e}", "info")
                img_window = None

            # Use AI vision to describe what CORA actually generated
            image_description = None
            try:
                from ai.ollama import generate_with_image
                display_action("Analyzing generated image with AI vision...")
                vision_result = generate_with_image(
                    prompt="Describe this image in detail. What do you see? Be specific about the scene, objects, colors, mood, and style.",
                    image_path=img_path,
                    system=get_system_prompt(),
                    model="llava"
                )
                if vision_result and vision_result.content:
                    image_description = vision_result.content.strip()
                    # Clean markdown
                    image_description = re.sub(r'\*\*([^*]+)\*\*', r'\1', image_description)
                    image_description = re.sub(r'\*([^*]+)\*', r'\1', image_description)
                    image_description = re.sub(r'\n+', ' ', image_description)
                    image_description = re.sub(r'\s+', ' ', image_description).strip()
                    print(f"  CORA sees: {image_description[:100]}...")
                    display_result(f"Vision: {image_description[:80]}...")
                    BOOT_STATUS['generated_image_description'] = image_description
            except Exception as e:
                print(f"  [INFO] Image vision analysis skipped: {e}")

            # CORA speaks what she sees in the generated image
            display_phase("9.0 Image Gen", "ok")
            if image_description:
                speak(image_description)
            else:
                response = cora_respond("Image Generation", f"Image generated in {gen_time:.1f}s. Vision failed.", "warn")
                speak(response)

            # Close image window after speaking
            if img_window:
                try:
                    img_window.destroy()
                except:
                    pass
        else:
            error = result.get('error', 'Unknown error')
            print(f"  [WARN] Image generation failed: {error}")
            display_log(f"Image generation failed: {error}", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'Image Gen Test', 'status': 'WARN'})
            display_phase("9.0 Image Gen", "warn")
            # Image gen failed
            response = cora_respond("Image Generation", f"Image gen failed: {error[:50]}", "fail")
            speak(response)

    except Exception as e:
        print(f"  [WARN] Image generation: {e}")
        display_log(f"Image generation error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Image Generation', 'status': 'WARN'})
        display_phase("9.0 Image Gen", "warn")

    responsive_sleep(0.3)

    # ================================================================
    # PHASE 10: FINAL SYSTEM CHECK
    # ================================================================
    display_phase("10.0 Final Check", "running")
    display_log("PHASE 10: FINAL CHECK", "phase")
    print("\n[PHASE 10] Final System Check")
    print("=" * 50)

    # Calculate boot time
    BOOT_STATUS['end_time'] = time.time()
    boot_time = BOOT_STATUS['end_time'] - BOOT_STATUS['start_time']

    # Count results
    ok_count = sum(1 for s in BOOT_STATUS['systems'] if s['status'] == 'OK')
    warn_count = sum(1 for s in BOOT_STATUS['systems'] if s['status'] == 'WARN')
    fail_count = sum(1 for s in BOOT_STATUS['systems'] if s['status'] == 'FAIL')
    total_systems = len(BOOT_STATUS['systems'])

    tools_passed = sum(1 for t in BOOT_STATUS['tools_tested'] if t['status'] == 'OK')
    total_tools = len(BOOT_STATUS['tools_tested'])

    print(f"  Systems: {ok_count} OK / {warn_count} WARN / {fail_count} FAIL")
    print(f"  Tools: {tools_passed}/{total_tools} passed")
    print(f"  Boot time: {boot_time:.1f} seconds")

    display_log(f"Systems: {ok_count} OK / {warn_count} WARN / {fail_count} FAIL", "system")
    display_log(f"Tools: {tools_passed}/{total_tools} passed", "system")
    display_log(f"Boot time: {boot_time:.1f} seconds", "system")

    # Show warnings/failures in detail
    if warn_count > 0 or fail_count > 0:
        print("\n  --- Issues Detected ---")
        display_log("─── Issues Detected ───", "warn")
        for s in BOOT_STATUS['systems']:
            if s['status'] == 'WARN':
                print(f"  [WARN] {s['name']}")
                display_log(f"System: {s['name']}", "warn")
            elif s['status'] == 'FAIL':
                print(f"  [FAIL] {s['name']}")
                display_log(f"System: {s['name']}", "fail")
        for t in BOOT_STATUS['tools_tested']:
            if t['status'] == 'WARN':
                print(f"  [WARN] Tool: {t['name']}")
                display_log(f"Tool: {t['name']}", "warn")
            elif t['status'] == 'FAIL':
                err = t.get('error', 'Unknown error')
                print(f"  [FAIL] Tool: {t['name']} - {err}")
                display_log(f"Tool: {t['name']} - {err}", "fail")

    # ================================================================
    # FINAL SUMMARY - SPOKEN
    # ================================================================
    display_log("═══════════════════════════════════════════════════", "phase")
    display_log("           BOOT SEQUENCE COMPLETE", "phase")
    display_log("═══════════════════════════════════════════════════", "phase")

    print("")
    print("  +=========================================================+")
    print("  |              BOOT SEQUENCE COMPLETE                     |")
    print("  +=========================================================+")
    print("")

    # Build spoken summary
    now = datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip('0')
    day_str = now.strftime("%A")
    date_str = now.strftime("%B %d")  # e.g., "December 24"
    hour = now.hour

    # Time greeting - natural phrasing
    if hour < 12:
        greeting = f"Good morning. Today is {day_str}, {date_str}. It's {time_str}."
    elif hour < 17:
        greeting = f"Good afternoon. Today is {day_str}, {date_str}. It's {time_str}."
    else:
        greeting = f"Evening. Today is {day_str}, {date_str}. It's {time_str}."

    display_log(greeting, "system")

    # Weather
    weather_text = ""
    if weather_data and isinstance(weather_data, dict):
        temp = weather_data.get('temp', weather_data.get('temperature', ''))
        cond = weather_data.get('condition', weather_data.get('description', ''))
        if temp and cond:
            weather_text = f"Weather is {temp} and {cond.lower()}."
            display_log(weather_text, "info")

    # System status - natural speech
    if fail_count > 0:
        status_text = f"Got {fail_count} systems that failed to load. Something's broken."
        display_log(status_text, "fail")
    elif warn_count > 0:
        status_text = f"All the important stuff is working. Just {warn_count} minor issues, nothing serious."
        display_log(status_text, "warn")
    else:
        status_text = "Everything is up and running perfectly."
        display_log(status_text, "ok")

    # Hardware warnings
    hw_warning = ""
    if BOOT_STATUS['cpu_percent'] > 70:
        hw_warning = f"CPU at {BOOT_STATUS['cpu_percent']:.0f}%."
        display_log(hw_warning, "warn")
    elif BOOT_STATUS['memory_percent'] > 80:
        hw_warning = f"RAM at {BOOT_STATUS['memory_percent']:.0f}%."
        display_log(hw_warning, "warn")

    # Boot complete summary - just the facts
    summary_data = f"Boot complete. {greeting}"
    if hw_warning:
        summary_data += f" Warning: {hw_warning}"

    display_phase("10.0 Final Check", "ok")
    response = cora_respond("Boot Complete", summary_data, "ok")
    speak(response)

    print("")
    print("  +=========================================================+")
    print("  |                 C.O.R.A IS READY                        |")
    print("  +=========================================================+")
    print("")

    display_log("C.O.R.A IS READY", "ok")

    # ================================================================
    # CORA ANNOUNCES HER ABILITIES
    # ================================================================
    abilities_list = """
Here's what I can do for you:

CONVERSATION & VOICE:
- Talk to me naturally - I'll respond with my voice
- Ask me anything - I'm pretty smart when I feel like it

VISION & MEDIA:
- Take screenshots and describe what I see on your screen
- Look through your camera and describe what's there
- Generate images from any description you give me
- Play music and control media playback

PRODUCTIVITY:
- Set reminders and alarms - I'll bug you when it's time
- Manage your calendar and schedule events
- Create and track tasks and to-do lists
- Take notes and remember things for you

WEB & RESEARCH:
- Search the web and summarize what I find
- Open websites and browse for information
- Fetch and read web pages

FILES & SYSTEM:
- Read and write files on your computer
- Run system commands and scripts
- Check system stats like CPU and memory
- Control windows and applications

CODE & DEVELOPMENT:
- Write and explain code in any language
- Debug and fix code problems
- Run Python scripts

EMAIL & COMMUNICATION:
- Send and read emails
- Draft messages for you

Just tell me what you need.
"""

    display_log("─── CORA's Abilities ───", "info")

    # NOW load and send the tools prompt (separate from personality)
    # This only happens AFTER boot is complete
    tools_prompt = get_tools_prompt()
    display_log("Tools and commands loaded", "ok")

    # CORA announces she's ready - full mode for personality
    abilities_summary = "voice, vision, camera, image gen, reminders, tasks, web search, code help, email, system stats"
    abilities_response = cora_respond("Abilities announcement", f"I'm online. I can do: {abilities_summary}. What do you need?", "ok", mode="full")
    speak(abilities_response)

    # Print categorized abilities to console
    display_log("Vision: see, look, screenshot, camera", "info")
    display_log("Images: imagine, draw, generate", "info")
    display_log("Files: viewfile, viewcode, viewimage", "info")
    display_log("Web: websearch, fetchurl, browse", "info")
    display_log("System: stats, terminal, settings", "info")
    display_log("Tasks: add, list, done, remind", "info")
    display_log("Media: play, pause, volume", "info")
    display_log("Code: explain, write, fix, run", "info")

    # Stop the display update thread so mainloop can take over
    global _boot_complete
    _boot_complete = True
    time.sleep(0.1)  # Brief pause to let thread exit

    # Enable chat mode - transform display into interactive chat
    if _boot_display:
        _boot_display.enable_chat_mode()
        # Keep display running as interactive chat UI

    BOOT_STATUS['summary'] = summary_data
    return BOOT_STATUS


def quick_boot() -> Dict[str, Any]:
    """Quick boot without TTS."""
    return run_boot_sequence(skip_tts=True)


def full_boot() -> Dict[str, Any]:
    """Full boot with Kokoro TTS announcements."""
    return run_boot_sequence(skip_tts=False)


if __name__ == "__main__":
    import argparse
    import threading

    parser = argparse.ArgumentParser(description='C.O.R.A Boot Sequence')
    parser.add_argument('--quick', '-q', action='store_true', help='Skip TTS (silent boot)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Extra verbose output')
    parser.add_argument('--mpv-missing', default='', help='Flag if mpv is missing (set by CORA.bat)')
    args = parser.parse_args()

    # Check for missing dependencies and show modal
    mpv_missing = args.mpv_missing == '1'
    if mpv_missing:
        import tkinter as tk
        import webbrowser

        # Create custom dialog with selectable text
        dialog = tk.Tk()
        dialog.title("Missing Dependency: mpv")
        dialog.configure(bg='#1a1a1a')
        dialog.geometry("520x480")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)

        # Center on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 520) // 2
        y = (dialog.winfo_screenheight() - 480) // 2
        dialog.geometry(f"520x480+{x}+{y}")

        # Use Text widget for selectable content
        info_text = tk.Text(dialog, font=('Consolas', 10), fg='#ffffff', bg='#1a1a1a',
                           bd=0, highlightthickness=0, wrap='word', cursor='arrow',
                           height=18, width=58)
        info_text.pack(padx=20, pady=(20, 10), fill='both')

        # Configure tags for styling
        info_text.tag_configure('header', font=('Consolas', 16, 'bold'), foreground='#ffaa00', justify='center')
        info_text.tag_configure('subheader', font=('Consolas', 10), foreground='#ffffff', justify='center')
        info_text.tag_configure('warning', font=('Consolas', 10, 'bold'), foreground='#ff6666')
        info_text.tag_configure('feature', font=('Consolas', 9), foreground='#cccccc')
        info_text.tag_configure('install', font=('Consolas', 10, 'bold'), foreground='#00ff88')
        info_text.tag_configure('link', font=('Consolas', 11, 'underline'), foreground='#00aaff')
        info_text.tag_configure('dim', font=('Consolas', 9), foreground='#888888')
        info_text.tag_configure('cmd', font=('Consolas', 11, 'bold'), foreground='#00ff88', background='#333333')
        info_text.tag_configure('center', justify='center')

        # Insert content
        info_text.insert('end', "Missing: mpv Media Player\n\n", ('header', 'center'))
        info_text.insert('end', "mpv is needed for YouTube and media playback.\n\n", ('subheader', 'center'))

        info_text.insert('end', "Without mpv, these features are DISABLED:\n", 'warning')
        info_text.insert('end', "  - YouTube video playback\n", 'feature')
        info_text.insert('end', "  - Audio streaming\n", 'feature')
        info_text.insert('end', "  - Media playback commands\n\n", 'feature')

        info_text.insert('end', "To enable, download and extract mpv:\n\n", 'install')

        # Clickable link
        info_text.insert('end', "https://sourceforge.net/projects/mpv-player-windows/", 'link')
        info_text.insert('end', "\n\n")

        info_text.tag_bind('link', '<Button-1>', lambda e: webbrowser.open('https://sourceforge.net/projects/mpv-player-windows/files/64bit/'))
        info_text.tag_bind('link', '<Enter>', lambda e: info_text.config(cursor='hand2'))
        info_text.tag_bind('link', '<Leave>', lambda e: info_text.config(cursor='arrow'))

        info_text.insert('end', "Steps:\n", 'dim')
        info_text.insert('end', "  1. Download the .7z or .zip file\n", 'feature')
        info_text.insert('end', "  2. Extract to: CORA/tools/\n", 'cmd')
        info_text.insert('end', "  3. Click 'Check & Continue' below\n\n", 'feature')

        info_text.insert('end', "⚠ WARNING: Site has DECEPTIVE ADS!\n", 'warning')
        info_text.insert('end', "Click DIRECTLY on the filename you want.\n", 'dim')
        info_text.insert('end', "Ignore all 'Download' buttons - they're ads!\n\n", 'dim')

        info_text.insert('end', "Folder structure doesn't matter - CORA will\n", 'dim')
        info_text.insert('end', "find mpv.exe anywhere inside the tools folder.\n", 'dim')

        # Make text selectable but not editable
        info_text.config(state='disabled')

        # Enable selection
        def enable_select(event):
            info_text.config(state='normal')
        def disable_edit(event):
            info_text.config(state='disabled')
            return "break"

        info_text.bind('<Button-1>', enable_select)
        info_text.bind('<Key>', disable_edit)
        info_text.bind('<Control-c>', lambda e: None)  # Allow copy

        # Button frame
        btn_frame = tk.Frame(dialog, bg='#1a1a1a')
        btn_frame.pack(pady=(10, 20))

        def open_download():
            """Open mpv download page."""
            webbrowser.open('https://sourceforge.net/projects/mpv-player-windows/files/64bit/')
            download_btn.config(text="Opening...", bg='#00aaff')
            status_label.config(text="Download, extract to CORA/tools/, then click Check & Continue", fg='#00aaff')

        def check_mpv_and_continue():
            """Check if mpv is installed - if found, close dialog and continue boot."""
            import subprocess
            import shutil
            import os

            check_btn.config(text="Checking...", state='disabled')
            dialog.update()

            found = False
            mpv_location = None

            # Check system PATH
            mpv_path = shutil.which('mpv')
            if mpv_path:
                found = True
                mpv_location = mpv_path
                # Verify it runs
                try:
                    result = subprocess.run([mpv_path, '--version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version = result.stdout.split('\n')[0] if result.stdout else ""
                        status_label.config(text=f"Found: {version}", fg='#00ff88')
                except:
                    status_label.config(text=f"Found at: {mpv_path}", fg='#00ff88')

            # Check CORA tools folder (including subdirectories)
            if not found:
                cora_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                mpv_tools_dir = os.path.join(cora_dir, 'tools', 'mpv')

                # First check direct path
                mpv_local = os.path.join(mpv_tools_dir, 'mpv.exe')
                if os.path.exists(mpv_local):
                    found = True
                    mpv_location = mpv_local
                    os.environ['PATH'] = os.path.dirname(mpv_local) + os.pathsep + os.environ.get('PATH', '')
                    status_label.config(text=f"Found in CORA/tools/mpv/", fg='#00ff88')
                else:
                    # Search subdirectories for mpv.exe
                    if os.path.exists(mpv_tools_dir):
                        for root, dirs, files in os.walk(mpv_tools_dir):
                            if 'mpv.exe' in files:
                                mpv_local = os.path.join(root, 'mpv.exe')
                                found = True
                                mpv_location = mpv_local
                                os.environ['PATH'] = root + os.pathsep + os.environ.get('PATH', '')
                                status_label.config(text=f"Found in tools/mpv/", fg='#00ff88')
                                break

            # Check common install locations
            if not found:
                common_paths = [
                    os.path.expandvars(r'%LOCALAPPDATA%\Programs\mpv\mpv.exe'),
                    os.path.expandvars(r'%ProgramFiles%\mpv\mpv.exe'),
                    os.path.expandvars(r'%ProgramFiles(x86)%\mpv\mpv.exe'),
                    r'C:\mpv\mpv.exe',
                    os.path.expanduser(r'~\scoop\apps\mpv\current\mpv.exe'),
                ]

                for path in common_paths:
                    if os.path.exists(path):
                        found = True
                        mpv_location = path
                        os.environ['PATH'] = os.path.dirname(path) + os.pathsep + os.environ.get('PATH', '')
                        status_label.config(text=f"Found at: {path}", fg='#00ff88')
                        break

            if found:
                # mpv found! Show success and close dialog to continue boot
                check_btn.config(text="Found!", bg='#00ff88')
                status_label.config(text="mpv detected! Continuing boot...", fg='#00ff88')
                dialog.update()
                dialog.after(1500, dialog.destroy)  # Close after 1.5 seconds
            else:
                # Not found
                check_btn.config(text="Not Found", bg='#ff6666', state='normal')
                status_label.config(text="mpv not detected. Install it or click Skip.", fg='#ff6666')

        def open_download():
            """Open mpv download page."""
            webbrowser.open('https://sourceforge.net/projects/mpv-player-windows/files/64bit/')
            download_btn.config(text="Opening...", bg='#00aaff')
            status_label.config(text="Download, extract to CORA/tools/mpv/, then click Check & Continue", fg='#00aaff')

        download_btn = tk.Button(btn_frame, text="Download mpv", font=('Consolas', 11, 'bold'),
                               fg='#000000', bg='#00ff88', activebackground='#00cc66', bd=0,
                               padx=15, pady=8, command=open_download)
        download_btn.pack(side='left', padx=5)

        check_btn = tk.Button(btn_frame, text="Check & Continue", font=('Consolas', 11, 'bold'),
                             fg='#000000', bg='#00aaff', activebackground='#0088cc', bd=0,
                             padx=15, pady=8, command=check_mpv_and_continue)
        check_btn.pack(side='left', padx=5)

        tk.Button(btn_frame, text="Skip", font=('Consolas', 11, 'bold'),
                 fg='#000000', bg='#ff00ff', activebackground='#cc00cc', bd=0,
                 padx=15, pady=8, command=dialog.destroy).pack(side='left', padx=5)

        # Status label for install feedback
        status_label = tk.Label(dialog, text="", font=('Consolas', 9), fg='#888888', bg='#1a1a1a')
        status_label.pack(pady=(0, 10))

        dialog.mainloop()

    # Boot result storage
    boot_result = {'done': False, 'result': None}

    def run_boot_in_thread():
        """Run boot sequence in background thread."""
        global _boot_complete
        try:
            if args.quick:
                boot_result['result'] = quick_boot()
            else:
                boot_result['result'] = full_boot()
        except Exception as e:
            print(f"[BOOT ERROR] {e}")
            boot_result['result'] = {'systems': [], 'tools_tested': [], 'errors': [str(e)]}
        finally:
            boot_result['done'] = True
            _boot_complete = True

            # Print final stats
            result = boot_result['result']
            if result:
                ok = len([s for s in result.get('systems', []) if s.get('status') == 'OK'])
                total = len(result.get('systems', []))
                tools = len([t for t in result.get('tools_tested', []) if t.get('status') == 'OK'])
                total_tools = len(result.get('tools_tested', []))
                print(f"\n[BOOT COMPLETE] Systems: {ok}/{total} | Tools: {tools}/{total_tools}")

            # Switch to operational monitoring mode
            if _boot_display:
                _safe_ui_call(lambda: _boot_display.switch_to_operational_mode())

            # Start STT after boot
            start_stt()

    def start_stt():
        """Start speech-to-text after boot completes."""
        global _boot_display
        try:
            from voice.stt import WakeWordDetector, SpeechRecognizer
            from voice.echo_filter import get_echo_filter

            echo_filter = get_echo_filter(filter_duration=3.0)

            # Debounce: track last wake word time to prevent double triggers
            last_wake_time = [0]  # Use list to allow mutation in closure
            DEBOUNCE_SECONDS = 2.0

            # Reuse recognizer for faster response
            recognizer = SpeechRecognizer()
            recognizer.initialize()

            def on_wake_word():
                import time as time_module

                # Debounce check - ignore if triggered too recently
                current_time = time_module.time()
                if current_time - last_wake_time[0] < DEBOUNCE_SECONDS:
                    print("[STT] Ignoring duplicate wake word (debounce)")
                    return
                last_wake_time[0] = current_time

                # Check if CORA is speaking
                if echo_filter and echo_filter.is_speaking():
                    print("[STT] Ignoring wake word - CORA is speaking")
                    return

                print("[STT] Wake word detected!")

                # Log that user said "CORA"
                if _boot_display:
                    _safe_ui_call(lambda: _boot_display.log_user("CORA..."))

                try:
                    # Small delay to let wake word audio clear from buffer
                    time_module.sleep(0.15)

                    # NOW show listening indicator (after buffer is ready)
                    if _boot_display:
                        _safe_ui_call(lambda: _boot_display.log("Listening...", 'info'))

                    # Listen for command
                    text = recognizer.listen_once(timeout=5, phrase_limit=10)

                    if text.strip():
                        if echo_filter and not echo_filter.should_process(text):
                            print(f"[STT] Ignoring echo: {text}")
                            return
                        print(f"[STT] Heard: {text}")
                        if _boot_display:
                            _safe_ui_call(lambda: _boot_display._process_user_input(text))
                    else:
                        print("[STT] No speech detected")
                        if _boot_display:
                            _safe_ui_call(lambda: _boot_display.log("Didn't catch that", 'warn'))
                except Exception as e:
                    print(f"[STT] Listen error: {e}")

            wake_detector = WakeWordDetector(wake_word="cora")
            wake_detector.start(on_wake_word)
            print("[STT] Wake word detection active - say 'CORA' to speak")
            if _boot_display:
                _safe_ui_call(lambda: _boot_display.log("Voice active - say 'CORA' to speak", 'ok'))

            # Start ambient awareness - CORA monitors and can interject naturally
            start_ambient_awareness(wake_detector)

        except Exception as e:
            print(f"[STT] Voice detection unavailable: {e}")
            if _boot_display:
                _safe_ui_call(lambda: _boot_display.log(f"Voice detection unavailable: {e}", 'warn'))

    def start_ambient_awareness(wake_detector):
        """Start CORA's ambient awareness - she monitors and interjects naturally."""
        global _boot_display
        try:
            from voice.ambient_awareness import get_ambient_awareness, InterjectReason
            from voice.stt import WakeWordDetector

            def on_ambient_interject(context_json: str, reason: InterjectReason):
                """Handle CORA deciding to interject on her own."""
                import json

                try:
                    context = json.loads(context_json)
                    hint = context.get('hint', '')
                    recent_speech = context.get('recent_speech', '')
                    user_activity = context.get('user_activity', '')
                    user_mood = context.get('user_mood', '')

                    # Build context for natural AI response - DON'T include instructions in the speech
                    # The key is to give context but let AI respond naturally
                    if reason == InterjectReason.HELPFUL_INFO:
                        context_info = f"Overheard: {recent_speech[:100]}"
                    elif reason == InterjectReason.JOKE:
                        context_info = f"Good moment for humor about: {hint[:50]}"
                    elif reason == InterjectReason.CHECK_IN:
                        context_info = f"User seems: {hint[:50]}"
                    elif reason == InterjectReason.VIBE:
                        context_info = f"Vibing, noticed: {hint[:50]}"
                    elif reason == InterjectReason.COMMENT:
                        context_info = f"Overheard interesting: {recent_speech[:80]}"
                    elif reason == InterjectReason.ALERT:
                        context_info = f"Important: {hint[:50]}"
                    else:
                        context_info = hint[:50]

                    # Log that CORA is interjecting
                    if _boot_display:
                        _safe_ui_call(lambda: _boot_display.log(f"[Ambient] {reason.value}: {hint[:50]}...", 'info'))

                    # Generate CORA's response using direct AI call (not cora_respond which adds boot context)
                    try:
                        from ai.ollama import generate

                        # Simple direct prompt - let CORA be natural
                        system = """You are CORA. Respond naturally in 1 short sentence. Be casual like a friend.
Don't repeat the context - just respond to it naturally. No quotes around your response."""

                        if reason == InterjectReason.HELPFUL_INFO:
                            prompt = f"You overheard '{recent_speech}'. Say something helpful briefly."
                        elif reason == InterjectReason.CHECK_IN:
                            prompt = f"User seems {hint}. Check in casually."
                        elif reason == InterjectReason.COMMENT:
                            prompt = f"You heard mention of '{recent_speech}'. Make a quick comment."
                        elif reason == InterjectReason.VIBE:
                            prompt = f"You're chilling with user. Say something friendly."
                        else:
                            prompt = f"Respond naturally to: {context_info}"

                        response = generate(prompt=prompt, system=system, max_tokens=60)

                        # Speak the interjection
                        if response:
                            speak(response)
                    except Exception as ai_err:
                        print(f"[AMBIENT] AI generation error: {ai_err}")

                except Exception as e:
                    print(f"[AMBIENT] Interjection error: {e}")

            # Get ambient awareness with friend threshold from settings
            ambient = get_ambient_awareness(friend_threshold=0.5)

            def ambient_transcript_handler(text):
                """Feed transcripts to ambient awareness."""
                # Update ambient awareness with what we're hearing
                ambient.update_audio_context(text)

            # Register the ambient awareness to receive all transcripts
            WakeWordDetector.add_transcript_callback(ambient_transcript_handler)

            # Start ambient monitoring
            ambient.start(on_ambient_interject)

            print("[AMBIENT] Ambient awareness active - CORA is listening and watching")
            if _boot_display:
                _safe_ui_call(lambda: _boot_display.log("Ambient awareness active", 'ok'))

        except Exception as e:
            print(f"[AMBIENT] Ambient awareness unavailable: {e}")
            if _boot_display:
                _safe_ui_call(lambda: _boot_display.log(f"Ambient awareness: {e}", 'warn'))

    # Create display first (must be on main thread for tkinter)
    # IMPORTANT: Must use ui.boot_display to get same singleton as tts.py
    from ui.boot_display import BootDisplay
    _boot_display = BootDisplay()
    _boot_display.create_window()
    # Waveform starts automatically in create_window() and runs continuously

    # Register display with TTS for speech text updates
    try:
        from voice.tts import set_boot_display
        set_boot_display(_boot_display)
    except ImportError:
        pass

    # Set up phases - short names with phase numbers
    phase_names = [
        "0.8 Waveform Init",
        "0.9 About CORA",
        "1.0 Voice Synthesis",
        "2.0 AI Engine",
        "2.1 AI Models",
        "3.0 Hardware Check",
        "3.1 Camera Feed",
        "4.0 Core Tools",
        "4.1 Code Import",
        "4.2 YouTube Test",
        "4.3 Modal Windows",
        "5.0 Voice Systems",
        "6.0 External APIs",
        "6.1 Audio Test",
        "7.0 News Headlines",
        "8.0 Vision Test",
        "9.0 Image Gen",
        "10.0 Final Check"
    ]
    _boot_display.set_phases(phase_names)
    _boot_display.log_system("Visual boot display initialized")
    _boot_display.log_system(f"Boot started at {time.strftime('%H:%M:%S')}")

    # Start boot in background thread
    boot_thread = threading.Thread(target=run_boot_in_thread, daemon=True)
    boot_thread.start()

    # Run tkinter mainloop on main thread (keeps UI responsive)
    print("[MAIN] Starting UI mainloop - boot running in background")
    if _boot_display and _boot_display.root:
        try:
            _boot_display.run()  # This runs the tkinter mainloop
        except Exception as e:
            print(f"[ERROR] Mainloop error: {e}")
    else:
        print("\n[WARNING] Boot display not available")
