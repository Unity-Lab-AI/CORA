#!/usr/bin/env python3
"""
C.O.R.A Monitor Panel
Live system monitoring panel with CPU/RAM/GPU/Disk/Network display.

Per ARCHITECTURE.md v1.0.0:
- Dedicated system monitoring panel
- Live updating metrics display
- Integration with main UI

Created by: Unity AI Lab
Date: 2025-12-23
"""

import threading
import time
from typing import Optional, Callable, Dict, Any
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MonitorPanel:
    """
    System monitoring panel with live CPU/RAM/GPU/Disk/Network display.

    Can be used standalone or integrated into main UI.
    """

    def __init__(
        self,
        parent=None,
        update_interval: float = 2.0,
        on_alert: Optional[Callable[[str, float], None]] = None,
        **kwargs
    ):
        """Initialize monitor panel.

        Args:
            parent: Parent tkinter widget (or None for standalone data)
            update_interval: Seconds between updates
            on_alert: Callback for threshold alerts (metric_name, value)
        """
        self.parent = parent
        self.update_interval = update_interval
        self.on_alert = on_alert

        # Thresholds for alerts
        self.thresholds = {
            'cpu': 90.0,
            'memory': 85.0,
            'disk': 95.0,
            'gpu': 95.0
        }

        # Current values
        self._metrics: Dict[str, Any] = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_used_gb': 0.0,
            'memory_total_gb': 0.0,
            'disk_percent': 0.0,
            'disk_used_gb': 0.0,
            'disk_total_gb': 0.0,
            'network_sent_mb': 0.0,
            'network_recv_mb': 0.0,
            'gpu_percent': None,
            'gpu_memory_percent': None,
            'process_count': 0,
            'uptime_hours': 0.0
        }

        self._running = False
        self._update_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # UI elements (if parent provided and ctk available)
        self.frame = None
        self._labels: Dict[str, Any] = {}
        self._progress_bars: Dict[str, Any] = {}

        if parent and ctk:
            self._create_ui(parent, **kwargs)

    def _create_ui(self, parent, **kwargs):
        """Create the UI components."""
        self.frame = ctk.CTkFrame(parent, **kwargs)
        self.frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            self.frame,
            text="System Monitor",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 15))

        # CPU Section
        self._create_metric_row(1, "CPU", "cpu")

        # Memory Section
        self._create_metric_row(2, "Memory", "memory")

        # Disk Section
        self._create_metric_row(3, "Disk", "disk")

        # Network Section (no progress bar)
        self._create_network_row(4)

        # GPU Section (optional)
        self._create_metric_row(5, "GPU", "gpu")

        # Process count and uptime
        self._create_info_row(6)

        # Status indicator
        self._create_status_row(7)

    def _create_metric_row(self, row: int, label: str, key: str):
        """Create a metric row with label, progress bar, and value."""
        # Label
        lbl = ctk.CTkLabel(
            self.frame,
            text=f"{label}:",
            font=ctk.CTkFont(size=13),
            width=70,
            anchor="w"
        )
        lbl.grid(row=row, column=0, sticky="w", padx=(15, 5), pady=5)

        # Progress bar
        progress = ctk.CTkProgressBar(self.frame, width=150, height=15)
        progress.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        progress.set(0)
        self._progress_bars[key] = progress

        # Value label
        value_lbl = ctk.CTkLabel(
            self.frame,
            text="---%",
            font=ctk.CTkFont(size=12),
            width=60,
            anchor="e"
        )
        value_lbl.grid(row=row, column=2, sticky="e", padx=(5, 15), pady=5)
        self._labels[f"{key}_value"] = value_lbl

    def _create_network_row(self, row: int):
        """Create network stats row."""
        lbl = ctk.CTkLabel(
            self.frame,
            text="Network:",
            font=ctk.CTkFont(size=13),
            width=70,
            anchor="w"
        )
        lbl.grid(row=row, column=0, sticky="w", padx=(15, 5), pady=5)

        net_lbl = ctk.CTkLabel(
            self.frame,
            text="Up: --- MB | Down: --- MB",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        net_lbl.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        self._labels['network'] = net_lbl

    def _create_info_row(self, row: int):
        """Create info row with process count and uptime."""
        info_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        info_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=15, pady=5)

        proc_lbl = ctk.CTkLabel(
            info_frame,
            text="Processes: ---",
            font=ctk.CTkFont(size=11)
        )
        proc_lbl.pack(side="left", padx=(0, 20))
        self._labels['processes'] = proc_lbl

        uptime_lbl = ctk.CTkLabel(
            info_frame,
            text="Uptime: ---",
            font=ctk.CTkFont(size=11)
        )
        uptime_lbl.pack(side="left")
        self._labels['uptime'] = uptime_lbl

    def _create_status_row(self, row: int):
        """Create status indicator row."""
        self._status_label = ctk.CTkLabel(
            self.frame,
            text="Status: Stopped",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self._status_label.grid(row=row, column=0, columnspan=3, sticky="w", padx=15, pady=(5, 10))

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        metrics = {}

        if not HAS_PSUTIL:
            return metrics

        try:
            # CPU
            metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)

            # Memory
            mem = psutil.virtual_memory()
            metrics['memory_percent'] = mem.percent
            metrics['memory_used_gb'] = mem.used / (1024**3)
            metrics['memory_total_gb'] = mem.total / (1024**3)

            # Disk
            disk = psutil.disk_usage('/')
            metrics['disk_percent'] = disk.percent
            metrics['disk_used_gb'] = disk.used / (1024**3)
            metrics['disk_total_gb'] = disk.total / (1024**3)

            # Network
            net = psutil.net_io_counters()
            metrics['network_sent_mb'] = net.bytes_sent / (1024**2)
            metrics['network_recv_mb'] = net.bytes_recv / (1024**2)

            # Process count
            metrics['process_count'] = len(psutil.pids())

            # Uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            metrics['uptime_hours'] = uptime_seconds / 3600

            # Try GPU (nvidia-smi or similar)
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    metrics['gpu_percent'] = gpu.load * 100
                    metrics['gpu_memory_percent'] = gpu.memoryUtil * 100
            except Exception:
                metrics['gpu_percent'] = None
                metrics['gpu_memory_percent'] = None

        except Exception as e:
            print(f"[MonitorPanel] Error collecting metrics: {e}")

        return metrics

    def _check_thresholds(self, metrics: Dict[str, Any]):
        """Check if any metrics exceed thresholds."""
        if not self.on_alert:
            return

        checks = [
            ('cpu', metrics.get('cpu_percent', 0)),
            ('memory', metrics.get('memory_percent', 0)),
            ('disk', metrics.get('disk_percent', 0)),
        ]

        if metrics.get('gpu_percent') is not None:
            checks.append(('gpu', metrics['gpu_percent']))

        for name, value in checks:
            if value and value >= self.thresholds.get(name, 100):
                self.on_alert(name, value)

    def _update_ui(self, metrics: Dict[str, Any]):
        """Update UI with new metrics."""
        if not self.frame or not ctk:
            return

        try:
            # CPU
            cpu = metrics.get('cpu_percent', 0)
            if 'cpu' in self._progress_bars:
                self._progress_bars['cpu'].set(cpu / 100)
            if 'cpu_value' in self._labels:
                self._labels['cpu_value'].configure(text=f"{cpu:.1f}%")

            # Memory
            mem = metrics.get('memory_percent', 0)
            mem_used = metrics.get('memory_used_gb', 0)
            mem_total = metrics.get('memory_total_gb', 0)
            if 'memory' in self._progress_bars:
                self._progress_bars['memory'].set(mem / 100)
            if 'memory_value' in self._labels:
                self._labels['memory_value'].configure(
                    text=f"{mem:.1f}% ({mem_used:.1f}/{mem_total:.1f}GB)"
                )

            # Disk
            disk = metrics.get('disk_percent', 0)
            if 'disk' in self._progress_bars:
                self._progress_bars['disk'].set(disk / 100)
            if 'disk_value' in self._labels:
                self._labels['disk_value'].configure(text=f"{disk:.1f}%")

            # Network
            sent = metrics.get('network_sent_mb', 0)
            recv = metrics.get('network_recv_mb', 0)
            if 'network' in self._labels:
                self._labels['network'].configure(
                    text=f"Up: {sent:.1f} MB | Down: {recv:.1f} MB"
                )

            # GPU
            gpu = metrics.get('gpu_percent')
            if 'gpu' in self._progress_bars:
                if gpu is not None:
                    self._progress_bars['gpu'].set(gpu / 100)
                    if 'gpu_value' in self._labels:
                        self._labels['gpu_value'].configure(text=f"{gpu:.1f}%")
                else:
                    self._progress_bars['gpu'].set(0)
                    if 'gpu_value' in self._labels:
                        self._labels['gpu_value'].configure(text="N/A")

            # Info
            procs = metrics.get('process_count', 0)
            uptime = metrics.get('uptime_hours', 0)
            if 'processes' in self._labels:
                self._labels['processes'].configure(text=f"Processes: {procs}")
            if 'uptime' in self._labels:
                hours = int(uptime)
                mins = int((uptime - hours) * 60)
                self._labels['uptime'].configure(text=f"Uptime: {hours}h {mins}m")

            # Status
            if hasattr(self, '_status_label'):
                self._status_label.configure(
                    text="Status: Running",
                    text_color="green"
                )

        except Exception as e:
            print(f"[MonitorPanel] Error updating UI: {e}")

    def _update_loop(self):
        """Background update loop."""
        while self._running:
            metrics = self._collect_metrics()

            with self._lock:
                self._metrics = metrics

            self._check_thresholds(metrics)

            if self.frame:
                try:
                    self.frame.after(0, lambda m=metrics: self._update_ui(m))
                except Exception:
                    pass

            time.sleep(self.update_interval)

    def start(self):
        """Start the monitoring loop."""
        if self._running:
            return

        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()

    def stop(self):
        """Stop the monitoring loop."""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=2.0)
            self._update_thread = None

        if hasattr(self, '_status_label') and self._status_label:
            try:
                self._status_label.configure(
                    text="Status: Stopped",
                    text_color="gray"
                )
            except Exception:
                pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics (thread-safe)."""
        with self._lock:
            return self._metrics.copy()

    def get_metric(self, key: str) -> Any:
        """Get a specific metric value."""
        with self._lock:
            return self._metrics.get(key)

    def set_threshold(self, metric: str, value: float):
        """Set alert threshold for a metric."""
        self.thresholds[metric] = value

    def get_summary(self) -> str:
        """Get a text summary of current metrics."""
        m = self.get_metrics()

        lines = [
            f"CPU: {m.get('cpu_percent', 0):.1f}%",
            f"Memory: {m.get('memory_percent', 0):.1f}% ({m.get('memory_used_gb', 0):.1f}/{m.get('memory_total_gb', 0):.1f} GB)",
            f"Disk: {m.get('disk_percent', 0):.1f}%",
            f"Network: Up {m.get('network_sent_mb', 0):.1f} MB / Down {m.get('network_recv_mb', 0):.1f} MB",
            f"Processes: {m.get('process_count', 0)}",
        ]

        if m.get('gpu_percent') is not None:
            lines.insert(3, f"GPU: {m['gpu_percent']:.1f}%")

        return "\n".join(lines)


# Convenience function
def create_monitor_panel(parent=None, **kwargs) -> MonitorPanel:
    """Create and return a MonitorPanel instance."""
    return MonitorPanel(parent, **kwargs)


# Standalone test
if __name__ == '__main__':
    print("=== MONITOR PANEL TEST ===\n")

    # Test without UI
    monitor = MonitorPanel(update_interval=1.0)

    # Collect once
    print("Collecting metrics...")
    metrics = monitor._collect_metrics()

    if metrics:
        print(f"\nCPU: {metrics.get('cpu_percent', 0):.1f}%")
        print(f"Memory: {metrics.get('memory_percent', 0):.1f}%")
        print(f"Disk: {metrics.get('disk_percent', 0):.1f}%")
        print(f"Processes: {metrics.get('process_count', 0)}")
        print(f"Uptime: {metrics.get('uptime_hours', 0):.2f} hours")
    else:
        print("(psutil not available)")

    # Test summary
    print(f"\n--- Summary ---")
    print(monitor.get_summary())

    print("\n=== TEST COMPLETE ===")
