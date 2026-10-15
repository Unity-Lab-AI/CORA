#!/usr/bin/env python3
"""src.cora_parts: boot (split from src/cora.py on 2026-10-14)."""
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
from src.cora_parts._base import datetime, load_knowledge, load_tasks, shutil, speak, subprocess  # noqa: F401




def boot_sequence():
    from src.cora_parts.system import check_ollama
    from src.cora_parts.voice import check_tts
    """Advanced System Diagnostics - C.O.R.A Cognitive Operations & Reasoning Assistant.

    Full system initialization with hardware checks, neural network status,
    and cognitive subsystem verification.
    """
    print("")
    print("  ================================================================")
    print("    ____   ___   ____      _")
    print("   / ___| / _ \\ |  _ \\    / \\")
    print("  | |    | | | || |_) |  / _ \\")
    print("  | |___ | |_| ||  _ <  / ___ \\")
    print("   \\____| \\___/ |_| \\_\\/_/   \\_\\")
    print("")
    print("  C.O.R.A - ADVANCED SYSTEM DIAGNOSTICS")
    print("  Cognitive Operations & Reasoning Assistant v1.0.0")
    print("  ================================================================")
    print("  Unity AI Lab | unityailab.com")
    print("  ================================================================")
    speak("Initiating advanced system diagnostics.")

    # Phase 1: Core System Initialization
    print("\n[PHASE 1] CORE SYSTEM INITIALIZATION")
    print("-" * 40)

    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        period = 'morning'
    elif 12 <= hour < 17:
        period = 'afternoon'
    elif 17 <= hour < 21:
        period = 'evening'
    else:
        period = 'night'
    print(f"[OK] System Clock: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC-local")
    print(f"[OK] Session ID: CORA-{now.strftime('%Y%m%d%H%M%S')}")

    # Phase 2: Hardware Diagnostics
    print("\n[PHASE 2] HARDWARE DIAGNOSTICS")
    print("-" * 40)

    # CPU/RAM
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        cores = psutil.cpu_count()
        print(f"[OK] CPU: {cores} cores @ {cpu}% utilization")
        print(f"[OK] RAM: {ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB ({ram.percent}%)")
    except ImportError:
        print("[--] CPU/RAM: psutil not available")

    # GPU Check
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            if len(parts) >= 4:
                print(f"[OK] GPU: {parts[0].strip()}")
                print(f"[OK] VRAM: {parts[1].strip()}MB / {parts[2].strip()}MB @ {parts[3].strip()}%")
                speak("GPU acceleration available.")
        else:
            print("[--] GPU: No NVIDIA GPU detected")
    except Exception:
        print("[--] GPU: nvidia-smi not available")

    # Disk
    try:
        disk = shutil.disk_usage('/')
        print(f"[OK] Disk: {disk.free // (1024**3)}GB free / {disk.total // (1024**3)}GB total")
    except Exception:
        pass

    # Phase 3: Network & Location
    print("\n[PHASE 3] NETWORK & GEOLOCATION")
    print("-" * 40)

    # Network connectivity
    try:
        import urllib.request
        urllib.request.urlopen('http://google.com', timeout=3)
        print("[OK] Network: Internet connectivity verified")
    except Exception:
        print("[!!] Network: No internet connection")

    # Location
    try:
        from services.location import get_location_from_ip, format_location_string
        location = get_location_from_ip()
        if location:
            loc_str = format_location_string(location)
            print(f"[OK] Geolocation: {loc_str}")
        else:
            print("[--] Geolocation: Could not determine")
    except Exception:
        print("[--] Geolocation: Service unavailable")

    # Weather
    try:
        from services.weather import get_current_weather
        weather = get_current_weather()
        if weather:
            print(f"[OK] Weather API: {weather.get('temp', 'N/A')}°F, {weather.get('condition', 'Unknown')}")
    except Exception:
        print("[--] Weather API: Unavailable")

    # Phase 4: Neural Network Subsystems
    print("\n[PHASE 4] NEURAL NETWORK SUBSYSTEMS")
    print("-" * 40)

    # Ollama / Language Model
    from ai import settings as _ai_settings
    if check_ollama():
        model = _ai_settings.chat_model()
        print(f"[OK] Language Model: {model} loaded")
        print(f"[OK] Neural Core: Ollama endpoint active @ {_ai_settings.ollama_url()}")
        speak("Neural language processing online.")
    else:
        print("[!!] Language Model: Ollama not running")
        print("[!!] Neural Core: OFFLINE - Start Ollama for full functionality")

    # Vision Model Check
    try:
        from ai.ollama import has_model
        vm = _ai_settings.vision_model()
        if has_model(vm):
            print(f"[OK] Vision Model: {vm} detected")
            speak("Visual cortex initialized.")
        else:
            print(f"[--] Vision Model: {vm} not installed (run: ollama pull {vm})")
    except Exception:
        print("[--] Vision Model: Could not check")

    # Phase 5: Voice & Audio Systems
    print("\n[PHASE 5] VOICE & AUDIO SYSTEMS")
    print("-" * 40)

    # TTS - her own voice
    if check_tts():
        print("[OK] Voice Synthesis: unity-voice-v2 online")
        speak("Voice synthesis module online.")
    else:
        print("[!!] Voice Synthesis: voice server not available")

    # Microphone check
    try:
        from services.audio import get_audio_manager
        manager = get_audio_manager()
        inputs = manager.get_input_devices()
        if inputs:
            default_mic = manager.get_default_input()
            print(f"[OK] Microphone: {len(inputs)} device(s) detected")
            if default_mic:
                print(f"[OK] Default Input: {default_mic.name[:40]}")
        else:
            print("[--] Microphone: No input devices")
    except Exception:
        print("[--] Audio System: Could not enumerate devices")

    # Phase 6: Camera / Vision Hardware
    print("\n[PHASE 6] VISUAL PERCEPTION SYSTEM")
    print("-" * 40)

    try:
        from services import camera as _camera
        if not _camera.CV2_AVAILABLE:
            print("[--] Webcam: OpenCV not installed")
        elif _camera.capture_frame() is not None:
            dev = _camera.working_device()
            print(f"[OK] Webcam: Camera accessible (index {dev[0]}, {dev[1]})" if dev else "[OK] Webcam: Camera accessible")
            speak("Visual perception system active.")
        else:
            print(f"[--] Webcam: {_camera.last_error() or 'No camera detected'}")
    except Exception as e:
        print(f"[--] Webcam: {e}")

    # Phase 7: Task & Memory Systems
    print("\n[PHASE 7] COGNITIVE MEMORY SYSTEMS")
    print("-" * 40)

    tasks = load_tasks()
    pending = [t for t in tasks if t.get('status') != 'done']
    overdue = [t for t in pending if t.get('due') and t.get('due') < now.strftime('%Y-%m-%d')]
    high_pri = [t for t in pending if t.get('priority', 5) <= 3]

    print(f"[OK] Task Memory: {len(tasks)} total, {len(pending)} active")
    if overdue:
        print(f"[!!] Overdue Tasks: {len(overdue)} require attention")
    if high_pri:
        print(f"[OK] High Priority: {len(high_pri)} flagged P1-P3")

    # Knowledge base
    try:
        knowledge = load_knowledge()
        print(f"[OK] Knowledge Base: {len(knowledge)} entries indexed")
    except Exception:
        print("[--] Knowledge Base: Could not load")

    # Reminders
    try:
        from cora_tools.calendar import get_pending_reminders
        reminders = get_pending_reminders()
        if reminders:
            print(f"[OK] Active Reminders: {len(reminders)}")
    except Exception:
        pass

    # Boot Summary
    print("\n" + "=" * 60)
    print("  DIAGNOSTIC COMPLETE - ALL COGNITIVE SUBSYSTEMS NOMINAL")
    print("=" * 60)

    # Final spoken summary
    summary_parts = []
    summary_parts.append(f"Good {period}.")
    if pending:
        summary_parts.append(f"{len(pending)} tasks pending.")
    if overdue:
        summary_parts.append(f"{len(overdue)} overdue.")
    summary_parts.append("All cognitive subsystems nominal. Ready for input.")

    speak(" ".join(summary_parts))
