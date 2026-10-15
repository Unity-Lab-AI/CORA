#!/usr/bin/env python3
"""PHASE 3: PC HARDWARE CHECK

One phase of src.boot_sequence.run_boot_sequence, split out on 2026-10-14. `_m` is the live
src.boot_sequence module (its names are read and assigned through it); `L` holds the locals
shared across phases."""
from __future__ import annotations
import json
import os
import re
import sys
import time

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


# Import centralized window manager
from ui.window_manager import create_window, create_popup, create_image_window, create_code_window, bring_to_front


def run(_m, L):

    # ================================================================
    # PHASE 3: PC HARDWARE CHECK
    # ================================================================
    _m.display_phase("3.0 Hardware Check", "running")
    _m.display_log("PHASE 3: HARDWARE CHECK", "phase")
    print("\n[PHASE 3] Hardware Status Check")
    print("=" * 50)

    stats = _m.get_system_stats()

    # CPU
    cpu = stats['cpu']
    print(f"  CPU Usage: {cpu:.1f}%")
    _m.display_log(f"CPU Usage: {cpu:.1f}%", "system")
    _m.BOOT_STATUS['cpu_percent'] = cpu

    # Memory
    mem = stats['memory']
    mem_used = stats['memory_used_gb']
    mem_total = stats['memory_total_gb']
    print(f"  Memory: {mem:.1f}% ({mem_used:.1f} / {mem_total:.1f} GB)")
    _m.display_log(f"Memory: {mem:.1f}% ({mem_used:.1f}/{mem_total:.1f} GB)", "system")
    _m.BOOT_STATUS['memory_percent'] = mem

    # Disk
    disk = stats['disk']
    disk_free = stats['disk_free_gb']
    disk_total = stats['disk_total_gb']
    print(f"  Disk: {disk:.1f}% used ({disk_free:.1f} GB free)")
    _m.display_log(f"Disk: {disk:.1f}% used ({disk_free:.1f} GB free)", "system")
    _m.BOOT_STATUS['disk_percent'] = disk

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
            _m.display_log(f"GPU: {gpu_name}", "ok")
            _m.display_log(f"  VRAM: {gpu_used_mb:.0f}/{gpu_total_mb:.0f} MB ({gpu_mem:.1f}%)", "system")
            _m.display_log(f"  Load: {gpu:.1f}%", "system")
        else:
            print(f"       Load: {gpu:.1f}% | VRAM: {gpu_mem:.1f}%")
            _m.display_log(f"GPU: {gpu_name} (Load: {gpu:.1f}%, VRAM: {gpu_mem:.1f}%)", "ok")
        _m.BOOT_STATUS['gpu_available'] = True
        _m.BOOT_STATUS['gpu_name'] = gpu_name
    else:
        print("  GPU: Not detected")
        _m.display_log("GPU: Not detected", "warn")
        _m.BOOT_STATUS['gpu_available'] = False

    # Network
    net_status = "Connected" if stats['network_up'] else "Disconnected"
    print(f"  Network: {net_status}")
    _m.display_log(f"Network: {net_status}", "ok" if stats['network_up'] else "warn")

    # Process count
    print(f"  Running Processes: {stats['process_count']}")
    _m.display_log(f"Running Processes: {stats['process_count']}", "info")

    _m.BOOT_STATUS['systems'].append({'name': 'Hardware Check', 'status': 'OK'})
    _m.display_phase("3.0 Hardware Check", "ok")

    # Hardware summary - just the stats
    hw_data = f"CPU {cpu:.0f}%, RAM {mem:.0f}%, Disk {disk:.0f}%"
    if _m.BOOT_STATUS['gpu_available']:
        hw_data += f", GPU {stats['gpu_name']} at {stats['gpu']:.0f}%"
    else:
        hw_data += ", no GPU"
    response = _m.cora_respond("PC Hardware scan", hw_data, "ok")
    _m.speak(response)

    _m.responsive_sleep(0.3)
