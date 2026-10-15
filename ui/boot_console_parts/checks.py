#!/usr/bin/env python3
"""ui.boot_console_parts: checks (split from ui/boot_console.py on 2026-10-14)."""
from __future__ import annotations

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any
from ui.boot_console_parts import _base  # noqa: F401
from ui.boot_console_parts._base import List, PROJECT_DIR, datetime, json, os, time  # noqa: F401




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
            from services.location import get_location
            data = get_location() or {}
            if data.get('city'):
                return {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', data.get('state', '')),
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
            from ai.ollama import check_ollama as _check
            from ai import settings
            st = _check()
            if st.get('connected'):
                names = st.get('model_names', [])
                primary = settings.chat_model()
                ordered = [primary] + [n for n in names if n != primary]
                return {
                    'connected': True,
                    'models': st.get('models', 0),
                    'model_names': ordered[:3]
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
        """Her own voice: the unity-voice-v2 sidecar (started if needed)."""
        try:
            from voice import unity_voice as uv
            ok, msg = uv.ensure_sidecar(timeout=30)
            return {'available': ok, 'engine': 'unity-voice-v2', 'url': uv.VOICE_URL, 'detail': msg}
        except Exception as e:
            return {'available': False, 'engine': None, 'detail': str(e)}

    def tts_tts(data):
        import random
        if data.get('available'):
            return random.choice([
                "Voice synthesis online. My own voice, version two.",
                "Speech systems ready. This is my real voice.",
                "Vocal interface initialized. Her own voice, live.",
            ])
        return random.choice([
            "Voice server offline. Text-only mode.",
            "My voice server isn't answering. Silent running.",
            "Voice unavailable. Reading text instead.",
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
            from cora_tools.calendar import get_today_events, get_events_summary
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
            from services.camera import camera_status
            st = camera_status()
            return {'available': bool(st.get('available')), 'resolution': st.get('resolution')}
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

    # STT CHECK - speech recognition / wake word status
    def check_vosk():
        try:
            from voice.stt import stt_status
            return stt_status()
        except Exception:
            pass
        try:
            import vosk  # noqa: F401
            return {'installed': True, 'model_found': False, 'status': 'partial', 'engine': 'vosk'}
        except ImportError:
            return {'installed': False, 'model_found': False, 'status': 'unavailable', 'engine': None}
        except Exception:
            return {'installed': False, 'model_found': False, 'status': 'error', 'engine': None}

    def tts_vosk(data):
        import random
        engine = data.get('engine') or 'speech'
        if data.get('status') == 'ready':
            return random.choice([
                "Voice recognition ready. Wake word listening enabled.",
                "Speech-to-text online. Say 'Cora' to activate.",
                f"{engine} initialized. Voice commands available.",
            ])
        elif data.get('installed'):
            return random.choice([
                f"{engine} installed but the model is not ready yet.",
                "STT partially configured. Model download needed.",
                "Voice recognition available, awaiting model setup.",
            ])
        return random.choice([
            "Voice recognition unavailable.",
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
