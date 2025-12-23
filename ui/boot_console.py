#!/usr/bin/env python3
"""
C.O.R.A Boot Console
ASCII-style boot sequence with checkmarks and TTS narration

Per ARCHITECTURE.md v2.0.0:
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

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
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


def create_default_boot_checks() -> List[tuple]:
    """Create default boot checks per ARCHITECTURE.md."""

    def check_time():
        now = datetime.now()
        return {
            'time': now.strftime('%I:%M %p'),
            'date': now.strftime('%Y-%m-%d'),
            'day': now.strftime('%A'),
            'hour': now.hour
        }

    def tts_time(data):
        import random
        hour = data['hour']
        time_str = data['time']
        day = data.get('day', '')

        # Advanced AI style - varied, contextual responses
        if 5 <= hour < 8:
            options = [
                f"Early bird mode activated. {time_str} on a {day}.",
                f"Rise and grind. It's {time_str}.",
                f"Dawn patrol. {time_str}, {day}.",
            ]
        elif 8 <= hour < 12:
            options = [
                f"Morning systems nominal. {time_str}.",
                f"Temporal sync complete. {day}, {time_str}.",
                f"Good morning. {time_str} on your {day}.",
            ]
        elif 12 <= hour < 14:
            options = [
                f"Midday checkpoint. {time_str}.",
                f"Solar apex approaching. {time_str}.",
                f"Noon-ish. {time_str} to be precise.",
            ]
        elif 14 <= hour < 17:
            options = [
                f"Afternoon operations. {time_str}.",
                f"Post-meridian. {time_str}, {day}.",
                f"Cruising through {day}. {time_str}.",
            ]
        elif 17 <= hour < 21:
            options = [
                f"Evening mode. {time_str}.",
                f"Sunset protocols engaged. {time_str}.",
                f"Winding down {day}. {time_str}.",
            ]
        else:
            options = [
                f"Night owl detected. {time_str}.",
                f"Burning the midnight oil at {time_str}.",
                f"Late night session. {time_str}. Sleep is for the weak.",
                f"Nocturnal operations. {time_str}.",
            ]
        return random.choice(options)

    def check_location():
        try:
            import requests
            resp = requests.get('http://ip-api.com/json/', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', ''),
                    'country': data.get('country', '')
                }
        except Exception:
            pass
        return {'city': 'Unknown', 'region': '', 'country': ''}

    def tts_location(data):
        import random
        city = data.get('city', 'Unknown')
        region = data.get('region', '')
        if city != 'Unknown':
            options = [
                f"Geolocation confirmed. {city}.",
                f"Broadcasting from {city}.",
                f"Location lock: {city}, {region}." if region else f"Pinned to {city}.",
                f"Operating from {city} today.",
            ]
            return random.choice(options)
        return random.choice([
            "Location services unavailable. Going dark.",
            "Geolocation failed. Stealth mode, I guess.",
            "Can't pin your location. VPN maybe?",
        ])

    def check_weather():
        try:
            import requests
            # Use wttr.in for simple weather
            resp = requests.get('https://wttr.in/?format=%t+%C', timeout=5)
            if resp.status_code == 200:
                return {'conditions': resp.text.strip()}
        except Exception:
            pass
        return {'conditions': 'Weather unavailable'}

    def tts_weather(data):
        import random
        conditions = data.get('conditions', 'unavailable')
        if conditions and conditions != 'Weather unavailable':
            # Parse temperature if present (format: "+5°C Cloudy")
            options = [
                f"Atmospheric conditions: {conditions}.",
                f"Weather report: {conditions}.",
                f"Outside it's {conditions}.",
                f"Environmental scan: {conditions}.",
            ]
            return random.choice(options)
        return random.choice([
            "Weather data unavailable. Assume unpredictable.",
            "Meteorological feed offline.",
            "Can't reach weather services. Check manually.",
        ])

    def check_tasks():
        tasks_file = PROJECT_DIR / 'tasks.json'
        if tasks_file.exists():
            try:
                with open(tasks_file) as f:
                    data = json.load(f)
                    tasks = data.get('tasks', [])
                    pending = [t for t in tasks if t.get('status') == 'pending']
                    overdue = []
                    today = datetime.now().strftime('%Y-%m-%d')
                    for t in tasks:
                        if t.get('due') and t['due'] < today and t.get('status') != 'done':
                            overdue.append(t)
                    return {
                        'total': len(tasks),
                        'pending': len(pending),
                        'overdue': len(overdue),
                        'overdue_tasks': overdue[:3]
                    }
            except Exception:
                pass
        return {'total': 0, 'pending': 0, 'overdue': 0, 'overdue_tasks': []}

    def tts_tasks(data):
        import random
        pending = data.get('pending', 0)
        overdue = data.get('overdue', 0)
        total = data.get('total', 0)

        if pending == 0 and overdue == 0:
            return random.choice([
                "Task queue empty. Rare occurrence.",
                "No pending items. Suspiciously productive.",
                "Clear backlog. Enjoy it while it lasts.",
                "Zero tasks pending. Take a breath.",
            ])

        parts = []
        if pending > 0:
            if pending == 1:
                parts.append("One task awaiting action.")
            elif pending <= 3:
                parts.append(f"{pending} tasks in queue. Manageable.")
            elif pending <= 7:
                parts.append(f"{pending} tasks pending. Getting busy.")
            else:
                parts.append(f"{pending} tasks stacked up. Prioritize.")

        if overdue > 0:
            if overdue == 1:
                parts.append("One overdue. Handle it.")
            else:
                parts.append(f"Alert: {overdue} overdue. Address immediately.")

        return " ".join(parts)

    def check_ollama():
        try:
            import requests
            resp = requests.get('http://localhost:11434/api/tags', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get('models', [])
                return {
                    'connected': True,
                    'models': len(models),
                    'model_names': [m.get('name', '') for m in models[:3]]
                }
        except Exception:
            pass
        return {'connected': False, 'models': 0, 'model_names': []}

    def tts_ollama(data):
        import random
        if data.get('connected'):
            models = data.get('models', 0)
            model_names = data.get('model_names', [])
            if models >= 3:
                return random.choice([
                    f"Neural network online. {models} models loaded and ready.",
                    f"Cognitive core active. {models} models at your disposal.",
                    f"AI backend operational. Full arsenal: {models} models.",
                ])
            elif models > 0:
                primary = model_names[0] if model_names else "unknown"
                return random.choice([
                    f"Brain online. Primary model: {primary}.",
                    f"Cognitive systems active. Running {primary}.",
                    f"Neural link established. {primary} loaded.",
                ])
            else:
                return "Ollama connected but no models found. Install some."
        return random.choice([
            "Ollama offline. Limited to scripted responses.",
            "Neural backend unavailable. Running in degraded mode.",
            "AI core disconnected. Start Ollama for full capability.",
        ])

    def check_tts():
        try:
            import pyttsx3
            return {'available': True, 'engine': 'pyttsx3'}
        except ImportError:
            pass
        try:
            from kokoro import KPipeline
            return {'available': True, 'engine': 'kokoro'}
        except ImportError:
            pass
        return {'available': False, 'engine': None}

    def tts_tts(data):
        import random
        if data.get('available'):
            engine = data.get('engine', 'unknown')
            if engine == 'kokoro':
                return random.choice([
                    "Voice synthesis online. Kokoro engine active.",
                    "Speech systems ready. Premium voice enabled.",
                    "Vocal interface initialized. High-fidelity mode.",
                ])
            else:
                return random.choice([
                    "Voice output ready. Standard synthesis.",
                    "Speech systems active. Basic engine loaded.",
                    "Text-to-speech operational.",
                ])
        return random.choice([
            "Voice systems offline. Text-only mode.",
            "No speech engine detected. Silent running.",
            "TTS unavailable. Reading text instead.",
        ])

    def check_system():
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            return {
                'cpu': f"{cpu:.0f}%",
                'ram': f"{ram.percent:.0f}%",
                'ram_used': f"{ram.used / (1024**3):.1f}GB"
            }
        except ImportError:
            return {'cpu': '?', 'ram': '?', 'ram_used': '?'}

    def tts_system(data):
        import random
        cpu = data.get('cpu', '?')
        ram = data.get('ram', '?')
        ram_used = data.get('ram_used', '?')

        # Parse CPU percentage for context
        try:
            cpu_val = int(cpu.replace('%', ''))
        except (ValueError, AttributeError):
            cpu_val = 50

        try:
            ram_val = int(ram.replace('%', ''))
        except (ValueError, AttributeError):
            ram_val = 50

        if cpu_val < 30 and ram_val < 50:
            return random.choice([
                f"System resources optimal. CPU {cpu}, RAM {ram}.",
                f"Hardware baseline nominal. Plenty of headroom.",
                f"Running light. {cpu} CPU, {ram_used} memory.",
            ])
        elif cpu_val < 70 and ram_val < 80:
            return random.choice([
                f"System load moderate. CPU {cpu}, RAM {ram}.",
                f"Resources adequate. {ram_used} memory in use.",
                f"Hardware chugging along. {cpu} processor load.",
            ])
        else:
            return random.choice([
                f"High system load. CPU {cpu}, RAM {ram}. Consider closing apps.",
                f"Resources strained. {ram_used} memory, {cpu} processor.",
                f"System under pressure. Optimize or expect slowdowns.",
            ])

    def check_calendar():
        try:
            from tools.calendar import get_today_events, get_events_summary
            events = get_today_events()
            return {
                'count': len(events),
                'events': events[:3],
                'summary': get_events_summary(events)
            }
        except Exception as e:
            return {'count': 0, 'events': [], 'summary': 'Calendar unavailable'}

    def tts_calendar(data):
        import random
        count = data.get('count', 0)
        events = data.get('events', [])
        summary = data.get('summary', '')

        if count == 0:
            return random.choice([
                "Calendar clear. No scheduled obligations.",
                "No events today. Freedom awaits.",
                "Schedule empty. Rare opportunity.",
                "Nothing on the books. Plan accordingly.",
            ])
        elif count == 1:
            # Try to mention the event if we have it
            if events and isinstance(events[0], dict):
                event_name = events[0].get('summary', events[0].get('title', 'one event'))
                return f"One event: {event_name}."
            return "Single event on schedule."
        elif count <= 3:
            return random.choice([
                f"{count} events today. Manageable schedule.",
                f"Light day. {count} appointments.",
                summary if summary else f"{count} items scheduled.",
            ])
        else:
            return random.choice([
                f"Busy day ahead. {count} events stacked.",
                f"Full calendar: {count} events. Pace yourself.",
                f"{count} scheduled items. Prioritize wisely.",
            ])

    def check_gpu():
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.free', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(', ')
                return {
                    'available': True,
                    'name': parts[0] if len(parts) > 0 else 'Unknown',
                    'memory_total': f"{parts[1]}MB" if len(parts) > 1 else '?',
                    'memory_free': f"{parts[2]}MB" if len(parts) > 2 else '?'
                }
        except Exception:
            pass
        return {'available': False, 'name': None, 'memory_total': '?', 'memory_free': '?'}

    def tts_gpu(data):
        import random
        if data.get('available'):
            name = data.get('name', 'GPU')
            return random.choice([
                f"Graphics processor ready. {name}.",
                f"GPU online. {name} standing by.",
                f"Visual compute unit active. {name}.",
            ])
        return random.choice([
            "No dedicated GPU detected.",
            "Graphics: integrated only.",
            "Discrete GPU unavailable.",
        ])

    def check_disk():
        try:
            import shutil
            path = 'C:\\' if os.name == 'nt' else '/'
            usage = shutil.disk_usage(path)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            percent_free = (usage.free / usage.total) * 100
            return {
                'free_gb': f"{free_gb:.1f}",
                'total_gb': f"{total_gb:.1f}",
                'percent_free': f"{percent_free:.1f}%"
            }
        except Exception:
            return {'free_gb': '?', 'total_gb': '?', 'percent_free': '?'}

    def tts_disk(data):
        import random
        free = data.get('free_gb', '?')
        return random.choice([
            f"Storage systems nominal. {free} gigabytes available.",
            f"Disk space: {free} GB free.",
            f"Storage check passed. {free} GB remaining.",
        ])

    def check_network():
        try:
            import socket
            start = time.time()
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            latency = (time.time() - start) * 1000
            return {'connected': True, 'latency_ms': f"{latency:.0f}"}
        except Exception:
            return {'connected': False, 'latency_ms': '?'}

    def tts_network(data):
        import random
        if data.get('connected'):
            latency = data.get('latency_ms', '?')
            return random.choice([
                f"Network connection verified. Latency {latency} milliseconds.",
                f"Online and connected. Ping: {latency}ms.",
                f"Network active. Response time: {latency}ms.",
            ])
        return random.choice([
            "Network connection unavailable.",
            "Offline mode. No internet detected.",
            "Network check failed. Running disconnected.",
        ])

    def check_microphone():
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            count = p.get_device_count()
            input_devices = []
            for i in range(count):
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    input_devices.append(info.get('name', 'Unknown'))
            p.terminate()
            return {
                'available': len(input_devices) > 0,
                'count': len(input_devices),
                'devices': input_devices[:3]
            }
        except Exception:
            return {'available': False, 'count': 0, 'devices': []}

    def tts_microphone(data):
        import random
        if data.get('available'):
            count = data.get('count', 0)
            return random.choice([
                f"Audio input detected. {count} device{'s' if count != 1 else ''} available.",
                f"Microphone online. {count} input source{'s' if count != 1 else ''}.",
                f"Voice input ready. {count} mic{'s' if count != 1 else ''} found.",
            ])
        return random.choice([
            "No microphone detected.",
            "Audio input unavailable.",
            "Voice input offline.",
        ])

    def check_webcam():
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, _ = cap.read()
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                return {
                    'available': ret,
                    'resolution': f"{width}x{height}" if ret else None
                }
            cap.release()
        except Exception:
            pass
        return {'available': False, 'resolution': None}

    def tts_webcam(data):
        import random
        if data.get('available'):
            res = data.get('resolution', '')
            return random.choice([
                f"Webcam online. Visual systems ready. {res}.",
                f"Camera active at {res}.",
                f"Visual input operational. {res} resolution.",
            ])
        return random.choice([
            "No webcam detected.",
            "Visual input unavailable.",
            "Camera offline.",
        ])

    # FORECAST CHECK - Weather forecast (high/low/precipitation)
    def check_forecast():
        try:
            import requests
            # Use wttr.in for forecast (same as weather but different format)
            resp = requests.get('https://wttr.in/?format=%t|%h|%w|%c', timeout=5)
            if resp.status_code == 200:
                parts = resp.text.strip().split('|')
                return {
                    'available': True,
                    'temp': parts[0] if len(parts) > 0 else '?',
                    'humidity': parts[1] if len(parts) > 1 else '?',
                    'wind': parts[2] if len(parts) > 2 else '?',
                    'condition': parts[3] if len(parts) > 3 else '?'
                }
        except Exception:
            pass
        return {'available': False}

    def tts_forecast(data):
        import random
        if data.get('available'):
            temp = data.get('temp', '?')
            humidity = data.get('humidity', '?')
            return random.choice([
                f"Weather forecast loaded. Current temp {temp}, humidity {humidity}.",
                f"Forecast data retrieved. {temp} with {humidity} humidity.",
                f"Weather systems online. {temp} today.",
            ])
        return random.choice([
            "Forecast unavailable.",
            "Weather data not retrieved.",
            "Forecast check skipped.",
        ])

    # REMINDERS CHECK - Time-based alerts from reminders.json
    def check_reminders():
        try:
            reminders_file = PROJECT_DIR / 'data' / 'reminders.json'
            if reminders_file.exists():
                with open(reminders_file, 'r') as f:
                    reminders = json.load(f)

                # Count active reminders
                now = datetime.now()
                active = []
                for r in reminders:
                    if isinstance(r, dict):
                        # Check if reminder is for today or overdue
                        due_str = r.get('due') or r.get('time') or r.get('date')
                        if due_str:
                            try:
                                # Try to parse date
                                from dateutil import parser
                                due = parser.parse(due_str)
                                if due.date() <= now.date():
                                    active.append(r.get('text', r.get('message', 'Reminder')))
                            except Exception:
                                pass
                        elif r.get('active', True):
                            active.append(r.get('text', r.get('message', 'Reminder')))

                return {
                    'total': len(reminders),
                    'active': len(active),
                    'items': active[:3]
                }
            return {'total': 0, 'active': 0, 'items': []}
        except Exception:
            return {'total': 0, 'active': 0, 'items': []}

    def tts_reminders(data):
        import random
        active = data.get('active', 0)
        total = data.get('total', 0)
        if active > 0:
            return random.choice([
                f"You have {active} active reminder{'s' if active != 1 else ''}.",
                f"{active} reminder{'s' if active != 1 else ''} pending.",
                f"Alert: {active} reminder{'s' if active != 1 else ''} need your attention.",
            ])
        elif total > 0:
            return random.choice([
                f"{total} reminders stored. None currently active.",
                f"Reminders loaded: {total} total, 0 active.",
                f"No immediate reminders. {total} in queue.",
            ])
        return random.choice([
            "No reminders set.",
            "Reminder list empty.",
            "No scheduled alerts.",
        ])

    # VOSK CHECK - STT/wake word status
    def check_vosk():
        try:
            # Check if vosk is installed
            import vosk
            vosk_available = True

            # Check for model directory
            vosk_model_path = PROJECT_DIR / 'models' / 'vosk'
            model_exists = vosk_model_path.exists() if vosk_model_path else False

            # Alternative paths
            if not model_exists:
                alt_paths = [
                    PROJECT_DIR / 'vosk-model-small-en-us-0.15',
                    PROJECT_DIR / 'vosk-model',
                    Path.home() / '.vosk' / 'model',
                ]
                for p in alt_paths:
                    if p.exists():
                        model_exists = True
                        break

            return {
                'installed': vosk_available,
                'model_found': model_exists,
                'status': 'ready' if (vosk_available and model_exists) else 'partial'
            }
        except ImportError:
            return {'installed': False, 'model_found': False, 'status': 'unavailable'}
        except Exception:
            return {'installed': False, 'model_found': False, 'status': 'error'}

    def tts_vosk(data):
        import random
        if data.get('status') == 'ready':
            return random.choice([
                "Voice recognition ready. Wake word listening enabled.",
                "Speech-to-text online. Say 'Hey Cora' to activate.",
                "Vosk STT initialized. Voice commands available.",
            ])
        elif data.get('installed'):
            return random.choice([
                "Vosk installed but model not found.",
                "STT partially configured. Model download needed.",
                "Voice recognition available, awaiting model setup.",
            ])
        return random.choice([
            "Voice recognition unavailable. Vosk not installed.",
            "STT offline. Text input only.",
            "No speech recognition. Keyboard mode active.",
        ])

    return [
        ('System Time', check_time, tts_time),
        ('Location', check_location, tts_location),
        ('Weather', check_weather, tts_weather),
        ('Forecast', check_forecast, tts_forecast),
        ('Calendar', check_calendar, tts_calendar),
        ('Tasks', check_tasks, tts_tasks),
        ('Reminders', check_reminders, tts_reminders),
        ('Ollama', check_ollama, tts_ollama),
        ('TTS', check_tts, tts_tts),
        ('Vosk STT', check_vosk, tts_vosk),
        ('System', check_system, tts_system),
        ('GPU', check_gpu, tts_gpu),
        ('Disk', check_disk, tts_disk),
        ('Network', check_network, tts_network),
        ('Microphone', check_microphone, tts_microphone),
        ('Webcam', check_webcam, tts_webcam),
    ]


def run_boot_sequence(speak_func=None, on_log=None) -> Dict[str, Any]:
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
    except ImportError:
        pass

    # Fallback to pyttsx3 with emotion-based rate/pitch
    try:
        import pyttsx3
        engine = pyttsx3.init()
        base_rate = engine.getProperty('rate') or 150

        def speak_sync_emotional(text):
            """Speak with emotion-adjusted rate/pitch."""
            if EMOTION_AVAILABLE:
                emotion = detect_emotion(text)
                params = get_voice_params(emotion, base_rate=base_rate)
                engine.setProperty('rate', params['rate'])
            engine.say(text)
            engine.runAndWait()

        return speak_sync_emotional
    except Exception:
        pass

    # No TTS available
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


if __name__ == "__main__":
    # Test boot sequence
    results = run_boot_sequence()
    print("\n=== RESULTS ===")
    for name, result in results.items():
        status = "PASS" if result['status'] else "FAIL"
        print(f"{name}: {status}")
