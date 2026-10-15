#!/usr/bin/env python3
"""StatsMixin: the stats methods of BootDisplay (split from ui/boot_display.py on 2026-10-14).
Module names of ui.boot_display are read through `_m` (imported lazily per method), so rebinding there is seen here."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import threading
import time
import math
import random
import os
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass


# Global audio buffer for sharing between TTS and waveform
# Use a class to ensure single instance across imports
import threading


class StatsMixin:

    def _start_stats_update(self):
        """Start the live stats update loop."""
        # Initialize CPU percent tracking (first call returns 0)
        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except:
            pass
        # Start the background stats collector thread
        self._stats_running = True
        self._stats_data = {}
        self._stats_thread = threading.Thread(target=self._stats_collector, daemon=True)
        self._stats_thread.start()
        # Start UI update loop
        self._update_stats_ui()

    def _stats_collector(self):
        """Background thread that collects system stats without blocking UI."""
        import subprocess
        try:
            import psutil
        except ImportError:
            return

        while self._stats_running and self.root:
            try:
                stats = {}

                # CPU (non-blocking, uses data from previous call)
                stats['cpu'] = psutil.cpu_percent(interval=None)

                # Memory
                mem = psutil.virtual_memory()
                stats['mem'] = mem.percent

                # Disk
                try:
                    disk = psutil.disk_usage('C:\\')
                except:
                    disk = psutil.disk_usage('/')
                stats['disk'] = disk.percent

                # Network
                net_up = False
                try:
                    net = psutil.net_if_stats()
                    for iface, data in net.items():
                        if data.isup and iface != 'lo' and 'Loopback' not in iface:
                            net_up = True
                            break
                except:
                    pass
                stats['net'] = net_up

                # GPU via nvidia-smi (this can be slow, but we're in a thread)
                try:
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, timeout=1
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        parts = result.stdout.strip().split(', ')
                        if len(parts) >= 3:
                            stats['gpu'] = float(parts[0])
                            gpu_mem_used = float(parts[1])
                            gpu_mem_total = float(parts[2])
                            stats['gpu_mem'] = (gpu_mem_used / gpu_mem_total) * 100 if gpu_mem_total > 0 else 0
                except:
                    stats['gpu'] = None
                    stats['gpu_mem'] = None

                # Store the stats for UI thread to read
                self._stats_data = stats

            except Exception:
                pass

            # Sleep 1 second before next collection
            time.sleep(1)

    def _update_stats_ui(self):
        """Update UI labels from collected stats (runs in main thread)."""
        if not self.root:
            return

        try:
            stats = self._stats_data

            # CPU
            if 'cpu' in stats:
                cpu = stats['cpu']
                cpu_color = self.ok_color if cpu < 70 else (self.warn_color if cpu < 90 else self.fail_color)
                if self.cpu_label:
                    self.cpu_label.config(text=f"{cpu:.1f}%", fg=cpu_color)

            # Memory
            if 'mem' in stats:
                mem_pct = stats['mem']
                mem_color = self.ok_color if mem_pct < 70 else (self.warn_color if mem_pct < 90 else self.fail_color)
                if self.mem_label:
                    self.mem_label.config(text=f"{mem_pct:.1f}%", fg=mem_color)

            # Disk
            if 'disk' in stats:
                disk_pct = stats['disk']
                disk_color = self.ok_color if disk_pct < 80 else (self.warn_color if disk_pct < 95 else self.fail_color)
                if self.disk_label:
                    self.disk_label.config(text=f"{disk_pct:.1f}%", fg=disk_color)

            # Network
            if 'net' in stats:
                net_up = stats['net']
                if self.net_label:
                    self.net_label.config(text="UP" if net_up else "DOWN", fg=self.ok_color if net_up else self.fail_color)

            # GPU
            if 'gpu' in stats and stats['gpu'] is not None:
                gpu_util = stats['gpu']
                gpu_color = self.ok_color if gpu_util < 70 else (self.warn_color if gpu_util < 90 else self.fail_color)
                if self.gpu_label:
                    self.gpu_label.config(text=f"{gpu_util:.0f}%", fg=gpu_color)
            elif self.gpu_label:
                self.gpu_label.config(text="N/A", fg='#666666')

            # GPU Memory
            if 'gpu_mem' in stats and stats['gpu_mem'] is not None:
                gpu_mem_pct = stats['gpu_mem']
                vram_color = self.ok_color if gpu_mem_pct < 70 else (self.warn_color if gpu_mem_pct < 90 else self.fail_color)
                if self.gpu_mem_label:
                    self.gpu_mem_label.config(text=f"{gpu_mem_pct:.0f}%", fg=vram_color)
            elif self.gpu_mem_label:
                self.gpu_mem_label.config(text="N/A", fg='#666666')

        except Exception:
            pass

        # Schedule next UI update in 1 second
        if self.root:
            self.stats_update_id = self.root.after(1000, self._update_stats_ui)
