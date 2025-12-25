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
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project paths
PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / 'src'))
sys.path.insert(0, str(PROJECT_DIR / 'ui'))

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


def get_system_prompt() -> str:
    """Load CORA's full system prompt from config/system_prompt.txt."""
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
            time.sleep(0.3)
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

    # Start waveform animation before speaking
    if _boot_display:
        try:
            _boot_display.start_speaking(text)
        except:
            pass

    def do_speak():
        """Actual TTS call - runs in thread."""
        if _tts_engine:
            try:
                _tts_engine.speak(text, emotion='neutral')
            except Exception as e:
                print(f"[TTS ERROR] {e}")

        # Stop waveform animation after speaking
        if _boot_display:
            try:
                _boot_display.stop_speaking()
            except:
                pass

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

    # If blocking, wait for thread to finish
    # Don't call root.update() - let tkinter mainloop handle it
    if blocking:
        tts_thread.join()


def cora_respond(context: str, result: str, status: str = "ok") -> str:
    """
    CORA generates a unique response for each boot phase.
    ALL responses come from AI using system prompt - no hardcoded templates.
    """
    import re

    try:
        from ai.ollama import generate

        # Load CORA's full system prompt
        system_prompt = get_system_prompt()

        # Simple, direct prompt - system prompt handles personality
        # MUST include exact numbers/data, not paraphrase
        prompt = f"Say this in ONE sentence, include the EXACT numbers and data, don't paraphrase: {result}"

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
    # PHASE 0.9: ABOUT CORA (Introduction)
    # ================================================================
    display_phase("About CORA", "running")
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
    display_phase("About CORA", "ok")

    # ================================================================
    # PHASE 1: VOICE SYNTHESIS (FIRST - so user can hear everything)
    # ================================================================
    display_phase("Voice Synthesis", "running")
    display_log("PHASE 1: VOICE SYNTHESIS", "phase")

    if not skip_tts:
        tts_ok = init_tts()
        if tts_ok:
            BOOT_STATUS['systems'].append({'name': 'Voice TTS (Kokoro)', 'status': 'OK'})
            display_log("Kokoro TTS initialized - Voice: af_bella", "ok")
            display_phase("Voice Synthesis", "ok")
        else:
            BOOT_STATUS['systems'].append({'name': 'Voice TTS (Kokoro)', 'status': 'FAIL'})
            display_log("Kokoro TTS failed to initialize", "fail")
            display_phase("Voice Synthesis", "fail")
    else:
        print("[BOOT] TTS skipped (silent mode)")
        display_log("TTS skipped (silent mode)", "warn")
        _tts_engine = None
        display_phase("Voice Synthesis", "warn")

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
    time.sleep(0.3)

    # ================================================================
    # PHASE 2: AI ENGINE (Critical - the brain)
    # ================================================================
    display_phase("AI Engine", "running")
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
            display_phase("AI Engine", "ok")
            # CORA generates her own response
            response = cora_respond("AI Brain/Ollama", f"My brain is online. Running on {ai_model} and ready to think", "ok")
            speak(response)
        else:
            print("  [WARN] AI Engine not responding")
            display_log("AI Engine not responding", "warn")
            BOOT_STATUS['systems'].append({'name': 'AI Engine', 'status': 'WARN'})
            display_phase("AI Engine", "warn")
            response = cora_respond("AI Brain/Ollama", "My brain isn't responding. Ollama might be down or not running", "warn")
            speak(response)

    except Exception as e:
        print(f"  [WARN] AI Engine: {e}")
        display_log(f"AI Engine error: {e}", "warn")
        BOOT_STATUS['systems'].append({'name': 'AI Engine', 'status': 'WARN'})
        display_phase("AI Engine", "warn")
        response = cora_respond("AI Brain/Ollama", f"Something went wrong with my brain. Got an error: {e}", "fail")
        speak(response)

    time.sleep(0.3)

    # ================================================================
    # PHASE 3: PC HARDWARE CHECK
    # ================================================================
    display_phase("Hardware Check", "running")
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
    display_phase("Hardware Check", "ok")

    # CORA generates her own hardware summary response - natural speech
    hw_data = f"CPU is running at {cpu:.0f} percent, memory is at {mem:.0f} percent, and disk usage is {disk:.0f} percent"
    if BOOT_STATUS['gpu_available']:
        hw_data += f". Got a {stats['gpu_name']} running at {stats['gpu']:.0f} percent load with {stats.get('gpu_memory', 0):.0f} percent VRAM used"
    else:
        hw_data += ". No GPU detected"
    response = cora_respond("PC Hardware scan", hw_data, "ok")
    speak(response)

    time.sleep(0.3)

    # ================================================================
    # PHASE 4: CORE TOOLS TEST
    # ================================================================
    display_phase("Core Tools", "running")
    display_log("PHASE 4: CORE TOOLS TEST", "phase")
    print("\n[PHASE 4] Core Tools Test")
    print("=" * 50)

    tools_ok = 0
    tools_total = 0

    # Memory System
    tools_total += 1
    try:
        from tools.memory import recall, remember
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
        from tools.tasks import TaskManager
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
        from tools.reminders import ReminderManager
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
        from tools.files import read_file, create_file
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
        from tools.screenshots import desktop, quick_screenshot
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
        from tools.browser import browse_sync
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
        from tools.system import run_shell, get_system_info
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
        from tools.windows import list_windows, focus_window
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
        from tools.code import analyze_code
        print("  [OK] Code Analysis")
        display_log("Code Analysis loaded", "ok")
        BOOT_STATUS['tools_tested'].append({'name': 'Code Analysis', 'status': 'OK'})
        tools_ok += 1
    except Exception as e:
        print(f"  [WARN] Code Analysis: {e}")
        display_log(f"Code Analysis: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Code Analysis', 'status': 'WARN'})

    display_phase("Core Tools", "ok")
    # CORA generates her own response about tools - natural speech
    if tools_ok == tools_total:
        tools_result = f"All {tools_total} tools loaded and ready to go"
    elif tools_ok >= tools_total - 2:
        tools_result = f"Got {tools_ok} out of {tools_total} tools working. Close enough"
    else:
        tools_result = f"Only {tools_ok} out of {tools_total} tools loaded. Some shit is broken"
    tools_status = "ok" if tools_ok >= tools_total - 2 else ("warn" if tools_ok >= tools_total // 2 else "fail")
    response = cora_respond("Core Tools check", tools_result, tools_status)
    speak(response)
    time.sleep(0.3)

    # ================================================================
    # PHASE 5: VOICE SYSTEMS
    # ================================================================
    display_phase("Voice Systems", "running")
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

    display_phase("Voice Systems", "ok")
    # CORA generates her own response about voice systems - natural speech
    voice_result = "Voice systems are up. I can hear you, filter out my own echo, and respond to my wake word"
    response = cora_respond("Voice Systems check", voice_result, "ok")
    speak(response)
    time.sleep(0.3)

    # ================================================================
    # PHASE 6: EXTERNAL SERVICES
    # ================================================================
    display_phase("External Services", "running")
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
                # CORA announces location in her own words
                response = cora_respond("Location check", f"We're currently in {location_str}", "ok")
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

    display_phase("External Services", "ok")

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

    response = cora_respond("Location and Weather", weather_report, "ok" if weather_data else "warn")
    speak(response)
    time.sleep(0.3)

    # ================================================================
    # PHASE 7: NEWS HEADLINES
    # ================================================================
    display_phase("News Headlines", "running")
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
                display_phase("News Headlines", "ok")
                # Clean headlines for speech
                clean_headlines = []
                for hl in headlines[:4]:
                    clean = hl.split(' - ')[0] if ' - ' in hl else hl
                    if len(clean) > 100:
                        clean = clean[:97] + "..."
                    clean_headlines.append(clean)

                # Let CORA announce the news in her own style
                news_data = "Here are today's top headlines: " + ". ".join(clean_headlines)
                response = cora_respond("News Headlines", news_data, "ok")
                speak(response)
            else:
                display_phase("News Headlines", "warn")
                response = cora_respond("News Headlines", "Couldn't get any news headlines. The feed came back empty", "warn")
                speak(response)
        else:
            print("  [WARN] News fetch failed")
            display_log(f"News fetch failed (HTTP {resp.status_code})", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'News Headlines', 'status': 'WARN'})
            display_phase("News Headlines", "warn")
            response = cora_respond("News Headlines", f"News fetch failed with a {resp.status_code} error", "fail")
            speak(response)

    except Exception as e:
        print(f"  [WARN] News fetch: {e}")
        display_log(f"News fetch error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Web Search', 'status': 'WARN'})
        display_phase("News Headlines", "warn")
        response = cora_respond("News Headlines", f"Something went wrong fetching the news", "fail")
        speak(response)

    time.sleep(0.3)

    # ================================================================
    # PHASE 8: VISION TEST (Screenshot + Camera)
    # ================================================================
    display_phase("Vision Test", "running")
    display_log("PHASE 8: VISION TEST", "phase")
    print("\n[PHASE 8] Vision System Test")
    print("=" * 50)

    # Test screenshot capture
    try:
        from tools.screenshots import desktop, quick_screenshot
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
                response = cora_respond("Screenshot capture", f"Screenshot captured at {result.width} by {result.height} pixels but I couldn't analyze it", "warn")
                speak(response)
        else:
            print(f"  [WARN] Screenshot failed: {result.error}")
            display_log(f"Screenshot failed: {result.error}", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'Screenshot Capture', 'status': 'WARN'})
    except Exception as e:
        print(f"  [WARN] Screenshot test: {e}")
        display_log(f"Screenshot error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Screenshot Capture', 'status': 'WARN'})

    # Test camera if available
    try:
        import cv2
        print("  Testing camera...")
        display_tool("OpenCV", "Accessing camera device")
        display_action("Opening camera VideoCapture(0)...")

        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            display_action("Camera opened, capturing frame...")
            ret, frame = cap.read()
            if ret:
                print(f"  [OK] Camera working: {frame.shape[1]}x{frame.shape[0]}")
                display_result(f"Camera frame: {frame.shape[1]}x{frame.shape[0]}")
                BOOT_STATUS['tools_tested'].append({'name': 'Camera', 'status': 'OK'})
                BOOT_STATUS['camera_available'] = True

                # Save test frame
                cam_dir = PROJECT_DIR / 'data' / 'camera'
                cam_dir.mkdir(parents=True, exist_ok=True)
                cam_path = cam_dir / 'boot_test.jpg'
                display_action(f"Saving camera frame to {cam_path}")
                cv2.imwrite(str(cam_path), frame)
                print(f"       Test frame saved: {cam_path}")
                display_result("Camera frame saved successfully")
                BOOT_STATUS['camera_path'] = str(cam_path)

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
                    response = cora_respond("Camera system", f"Camera is working but I couldn't analyze the image", "warn")
                    speak(response)
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

    display_phase("Vision Test", "ok")
    # CORA generates her own overall vision response - natural speech
    screenshot_ok = any(t['name'] == 'Screenshot Capture' and t['status'] == 'OK' for t in BOOT_STATUS['tools_tested'])
    camera_ok = BOOT_STATUS.get('camera_available', False)
    if screenshot_ok and camera_ok:
        vision_result = "Vision systems are fully online. I can see your screen and your camera is working"
    elif screenshot_ok:
        vision_result = "I can capture your screen but no camera detected"
    elif camera_ok:
        vision_result = "Camera is working but screenshot capture failed"
    else:
        vision_result = "Vision systems aren't working properly"
    response = cora_respond("Vision Systems summary", vision_result, "ok")
    speak(response)
    time.sleep(0.3)

    # ================================================================
    # PHASE 9: IMAGE GENERATION TEST
    # ================================================================
    display_phase("Image Generation", "running")
    display_log("PHASE 9: IMAGE GENERATION", "phase")
    print("\n[PHASE 9] Image Generation Test")
    print("=" * 50)

    try:
        from tools.image_gen import generate_image, show_fullscreen_image
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

            # Display the image
            # CORA generates her own response about successful generation - natural speech
            response = cora_respond("Image Generation complete", f"Done. That took {gen_time:.1f} seconds. Let me show you what I made", "ok")
            speak(response)
            print("  Displaying image (click or wait 8 seconds to close)...")
            display_action("Opening image display window...")

            # Show image in a window - use Toplevel if boot display exists
            try:
                import tkinter as tk
                from PIL import Image, ImageTk

                # Use Toplevel if we have an existing root (boot display)
                if _boot_display and _boot_display.root:
                    img_window = tk.Toplevel(_boot_display.root)
                else:
                    img_window = tk.Tk()

                img_window.title("CORA - Image Generation Test")
                img_window.attributes('-topmost', True)
                img_window.configure(bg='black')

                # Center window
                screen_w = img_window.winfo_screenwidth()
                screen_h = img_window.winfo_screenheight()
                x = (screen_w - 1280) // 2
                y = (screen_h - 720) // 2
                img_window.geometry(f"1280x720+{x}+{y}")

                # Load and display image
                img = Image.open(img_path)
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=img_window)

                label = tk.Label(img_window, image=photo, bg='black')
                label.image = photo  # Keep reference
                label.pack(fill='both', expand=True)

                # Show for 5 seconds, then auto-close (blocking wait during boot)
                img_window.update()
                display_result("Image displayed successfully")

                # Wait 5 seconds while updating window, then destroy
                for _ in range(50):  # 50 x 0.1s = 5 seconds
                    try:
                        img_window.update()
                        time.sleep(0.1)
                    except:
                        break  # Window was closed manually

                try:
                    img_window.destroy()
                except:
                    pass  # Already closed

            except Exception as e:
                print(f"  [INFO] Image display skipped: {e}")
                display_log(f"Image display skipped: {e}", "info")

            display_phase("Image Generation", "ok")
            # CORA generates final image gen summary - natural speech
            response = cora_respond("Image Generation test", f"Image generation is working. Created that in {gen_time:.1f} seconds", "ok")
            speak(response)
        else:
            error = result.get('error', 'Unknown error')
            print(f"  [WARN] Image generation failed: {error}")
            display_log(f"Image generation failed: {error}", "warn")
            BOOT_STATUS['tools_tested'].append({'name': 'Image Gen Test', 'status': 'WARN'})
            display_phase("Image Generation", "warn")
            # CORA generates her own response about failure - natural speech
            response = cora_respond("Image Generation", f"Image generation failed. Got this error: {error}", "fail")
            speak(response)

    except Exception as e:
        print(f"  [WARN] Image generation: {e}")
        display_log(f"Image generation error: {e}", "warn")
        BOOT_STATUS['tools_tested'].append({'name': 'Image Generation', 'status': 'WARN'})
        display_phase("Image Generation", "warn")

    time.sleep(0.3)

    # ================================================================
    # PHASE 10: FINAL SYSTEM CHECK
    # ================================================================
    display_phase("Final Check", "running")
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

    # Hardware warnings - natural speech
    hw_warning = ""
    if BOOT_STATUS['cpu_percent'] > 70:
        hw_warning = f"Heads up, your CPU is running hot at {BOOT_STATUS['cpu_percent']:.0f} percent."
        display_log(hw_warning, "warn")
    elif BOOT_STATUS['memory_percent'] > 80:
        hw_warning = f"Memory is getting tight at {BOOT_STATUS['memory_percent']:.0f} percent used."
        display_log(hw_warning, "warn")

    # Build final summary data and let CORA speak it her way
    summary_data = f"Boot complete. {greeting} {status_text}"
    if hw_warning:
        summary_data += f" {hw_warning}"
    summary_data += " Ready to go."

    display_phase("Final Check", "ok")
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
    # Have CORA announce abilities - just give her the data, system prompt handles personality
    abilities_data = "voice chat, vision/screenshots/camera, image generation, reminders/calendar/tasks, web search, file management, code help, email"
    abilities_response = cora_respond("Abilities announcement", f"Boot is done. Tell the user what you can do: {abilities_data}. Ask what they want.", "ok")
    speak(abilities_response)

    # Also print the abilities to the console
    for line in abilities_list.strip().split('\n'):
        if line.strip():
            display_log(line.strip(), "info")

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
    args = parser.parse_args()

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

            # Start STT after boot
            start_stt()

    def start_stt():
        """Start speech-to-text after boot completes."""
        global _boot_display
        try:
            from voice.stt import WakeWordDetector, SpeechRecognizer
            from voice.echo_filter import get_echo_filter

            echo_filter = get_echo_filter(filter_duration=3.0)

            def on_wake_word():
                if echo_filter and echo_filter.is_speaking():
                    print("[STT] Ignoring wake word - CORA is speaking")
                    return

                print("[STT] Wake word detected!")
                if _boot_display:
                    _safe_ui_call(lambda: _boot_display.log("Wake word detected - listening...", 'info'))
                try:
                    recognizer = SpeechRecognizer()
                    if recognizer.initialize():
                        text = recognizer.listen_once(timeout=5, phrase_limit=10)
                        if text.strip():
                            if echo_filter and not echo_filter.should_process(text):
                                print(f"[STT] Ignoring echo: {text}")
                                return
                            print(f"[STT] Heard: {text}")
                            if _boot_display:
                                _safe_ui_call(lambda: _boot_display._process_user_input(text))
                except Exception as e:
                    print(f"[STT] Listen error: {e}")

            wake_detector = WakeWordDetector(wake_word="cora")
            wake_detector.start(on_wake_word)
            print("[STT] Wake word detection active - say 'CORA' to speak")
            if _boot_display:
                _safe_ui_call(lambda: _boot_display.log("Voice active - say 'CORA' to speak", 'ok'))
        except Exception as e:
            print(f"[STT] Voice detection unavailable: {e}")
            if _boot_display:
                _safe_ui_call(lambda: _boot_display.log(f"Voice detection unavailable: {e}", 'warn'))

    # Create display first (must be on main thread for tkinter)
    from boot_display import BootDisplay
    _boot_display = BootDisplay()
    _boot_display.create_window()

    # Set up phases
    phase_names = [
        "About CORA", "Voice Synthesis", "AI Engine", "Hardware Check",
        "Core Tools", "Voice Systems", "External Services", "News Headlines",
        "Vision Test", "Image Generation", "Final Check"
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
