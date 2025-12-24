#!/usr/bin/env python3
"""
C.O.R.A Visual Boot Display
Displays boot sequence progress with audio waveform visualization.

Shows:
- Boot phase progress bars
- System status indicators
- Real-time audio waveform when CORA speaks
- Cool cyberpunk/goth aesthetic

Created by: Unity AI Lab
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import math
import random
from typing import Optional, Callable, List
from dataclasses import dataclass

# Try to import audio visualization dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class BootPhase:
    """Represents a boot phase."""
    name: str
    status: str = "pending"  # pending, running, ok, warn, fail
    message: str = ""


class AudioWaveform(tk.Canvas):
    """Animated audio waveform visualization."""

    def __init__(self, parent, width=400, height=80, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg='#0a0a0a', highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.is_playing = False
        self.bars = []
        self.num_bars = 40
        self.bar_width = width // self.num_bars - 2
        self.animation_id = None

        # Colors - goth/cyberpunk aesthetic
        self.colors = ['#ff00ff', '#ff44ff', '#cc00cc', '#9900ff', '#6600cc']

        self._create_bars()

    def _create_bars(self):
        """Create the waveform bars."""
        self.delete("all")
        self.bars = []

        for i in range(self.num_bars):
            x = i * (self.bar_width + 2) + 2
            bar = self.create_rectangle(
                x, self.height // 2 - 2,
                x + self.bar_width, self.height // 2 + 2,
                fill='#333333', outline=''
            )
            self.bars.append(bar)

    def start(self):
        """Start the waveform animation."""
        self.is_playing = True
        self._animate()

    def stop(self):
        """Stop the waveform animation."""
        self.is_playing = False
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None

        # Reset bars to flat
        for bar in self.bars:
            self.coords(
                bar,
                self.coords(bar)[0], self.height // 2 - 2,
                self.coords(bar)[2], self.height // 2 + 2
            )
            self.itemconfig(bar, fill='#333333')

    def _animate(self):
        """Animate the waveform."""
        if not self.is_playing:
            return

        center_y = self.height // 2

        for i, bar in enumerate(self.bars):
            # Create wave-like motion with randomness
            phase = time.time() * 5 + i * 0.3
            base_height = abs(math.sin(phase)) * 30 + 5
            random_height = random.uniform(0.7, 1.3)
            height = int(base_height * random_height)

            x1, _, x2, _ = self.coords(bar)
            self.coords(bar, x1, center_y - height, x2, center_y + height)

            # Color based on height
            intensity = min(255, int(height * 8))
            color = f'#{intensity:02x}00{255-intensity//2:02x}'
            self.itemconfig(bar, fill=color)

        self.animation_id = self.after(50, self._animate)


class BootDisplay:
    """Visual boot sequence display with waveform, scrolling log, and live stats."""

    def __init__(self):
        self.root = None
        self.phases: List[BootPhase] = []
        self.phase_labels = {}
        self.phase_indicators = {}
        self.status_label = None
        self.waveform = None
        self.progress_var = None
        self.current_text = None
        self.is_speaking = False
        self.log_text = None  # Scrolling log widget
        self.log_frame = None

        # Live stats labels
        self.stats_frame = None
        self.cpu_label = None
        self.mem_label = None
        self.disk_label = None
        self.gpu_label = None
        self.gpu_mem_label = None
        self.net_label = None
        self.stats_update_id = None

        # Theme colors - dark goth/cyberpunk
        self.bg_color = '#0a0a0a'
        self.fg_color = '#ffffff'
        self.accent_color = '#ff00ff'  # Magenta/pink
        self.accent2_color = '#00ffff'  # Cyan
        self.ok_color = '#00ff88'
        self.warn_color = '#ffaa00'
        self.fail_color = '#ff3333'
        self.pending_color = '#444444'

    def create_window(self):
        """Create the boot display window with waveform and scrolling log."""
        self.root = tk.Tk()
        self.root.title("C.O.R.A - Boot Sequence")
        self.root.configure(bg=self.bg_color)
        # Don't set topmost - let user put other windows in front
        # self.root.attributes('-topmost', True)

        # Larger window to fit log panel
        width, height = 1200, 800
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Keep window decorations so user can minimize/move/resize
        # self.root.overrideredirect(True)

        # Main container with two columns
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # LEFT COLUMN - Status and phases
        left_frame = tk.Frame(main_frame, bg=self.bg_color, width=500)
        left_frame.pack(side='left', fill='both', padx=(0, 10))
        left_frame.pack_propagate(False)

        # Header
        header = tk.Label(
            left_frame,
            text="C.O.R.A",
            font=('Consolas', 42, 'bold'),
            fg=self.accent_color,
            bg=self.bg_color
        )
        header.pack(pady=(5, 0))

        subtitle = tk.Label(
            left_frame,
            text="Cognitive Operations & Reasoning Assistant",
            font=('Consolas', 10),
            fg=self.accent2_color,
            bg=self.bg_color
        )
        subtitle.pack(pady=(0, 10))

        # Waveform visualization
        wave_frame = tk.Frame(left_frame, bg=self.bg_color)
        wave_frame.pack(fill='x', pady=5)

        wave_label = tk.Label(
            wave_frame,
            text="▶ VOICE SYNTHESIS",
            font=('Consolas', 9),
            fg='#666666',
            bg=self.bg_color
        )
        wave_label.pack()

        self.waveform = AudioWaveform(wave_frame, width=480, height=50)
        self.waveform.pack(pady=3)

        # Current speech text (what CORA is saying)
        self.current_text = tk.Label(
            left_frame,
            text="",
            font=('Consolas', 10, 'italic'),
            fg=self.accent_color,
            bg=self.bg_color,
            wraplength=470,
            height=3
        )
        self.current_text.pack(pady=5)

        # Progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#1a1a1a',
            background=self.accent_color,
            darkcolor=self.accent_color,
            lightcolor=self.accent_color,
            bordercolor='#333333'
        )

        self.progress_var = tk.DoubleVar(value=0)
        progress = ttk.Progressbar(
            left_frame,
            variable=self.progress_var,
            maximum=100,
            style="Custom.Horizontal.TProgressbar",
            length=480
        )
        progress.pack(pady=8)

        # Phase indicators frame
        phases_frame = tk.Frame(left_frame, bg=self.bg_color)
        phases_frame.pack(fill='both', expand=True, pady=5)
        self.phases_container = phases_frame

        # Status label
        self.status_label = tk.Label(
            left_frame,
            text="Initializing...",
            font=('Consolas', 12, 'bold'),
            fg=self.accent2_color,
            bg=self.bg_color
        )
        self.status_label.pack(pady=8)

        # LIVE SYSTEM STATS PANEL
        self.stats_frame = tk.Frame(left_frame, bg='#111111', bd=1, relief='groove')
        self.stats_frame.pack(fill='x', pady=5, padx=10)

        stats_header = tk.Label(
            self.stats_frame,
            text="── LIVE SYSTEM STATS ──",
            font=('Consolas', 9, 'bold'),
            fg=self.accent2_color,
            bg='#111111'
        )
        stats_header.pack(pady=(3, 2))

        # Stats grid
        stats_grid = tk.Frame(self.stats_frame, bg='#111111')
        stats_grid.pack(fill='x', padx=5, pady=3)

        # CPU
        tk.Label(stats_grid, text="CPU:", font=('Consolas', 9), fg='#888888', bg='#111111', width=6, anchor='e').grid(row=0, column=0, sticky='e')
        self.cpu_label = tk.Label(stats_grid, text="---%", font=('Consolas', 9, 'bold'), fg=self.ok_color, bg='#111111', width=8, anchor='w')
        self.cpu_label.grid(row=0, column=1, sticky='w', padx=(2, 10))

        # Memory
        tk.Label(stats_grid, text="MEM:", font=('Consolas', 9), fg='#888888', bg='#111111', width=6, anchor='e').grid(row=0, column=2, sticky='e')
        self.mem_label = tk.Label(stats_grid, text="---%", font=('Consolas', 9, 'bold'), fg=self.ok_color, bg='#111111', width=8, anchor='w')
        self.mem_label.grid(row=0, column=3, sticky='w', padx=(2, 10))

        # Disk
        tk.Label(stats_grid, text="DISK:", font=('Consolas', 9), fg='#888888', bg='#111111', width=6, anchor='e').grid(row=0, column=4, sticky='e')
        self.disk_label = tk.Label(stats_grid, text="---%", font=('Consolas', 9, 'bold'), fg=self.ok_color, bg='#111111', width=8, anchor='w')
        self.disk_label.grid(row=0, column=5, sticky='w')

        # GPU row
        tk.Label(stats_grid, text="GPU:", font=('Consolas', 9), fg='#888888', bg='#111111', width=6, anchor='e').grid(row=1, column=0, sticky='e')
        self.gpu_label = tk.Label(stats_grid, text="---%", font=('Consolas', 9, 'bold'), fg=self.ok_color, bg='#111111', width=8, anchor='w')
        self.gpu_label.grid(row=1, column=1, sticky='w', padx=(2, 10))

        tk.Label(stats_grid, text="VRAM:", font=('Consolas', 9), fg='#888888', bg='#111111', width=6, anchor='e').grid(row=1, column=2, sticky='e')
        self.gpu_mem_label = tk.Label(stats_grid, text="---%", font=('Consolas', 9, 'bold'), fg=self.ok_color, bg='#111111', width=8, anchor='w')
        self.gpu_mem_label.grid(row=1, column=3, sticky='w', padx=(2, 10))

        tk.Label(stats_grid, text="NET:", font=('Consolas', 9), fg='#888888', bg='#111111', width=6, anchor='e').grid(row=1, column=4, sticky='e')
        self.net_label = tk.Label(stats_grid, text="---", font=('Consolas', 9, 'bold'), fg=self.ok_color, bg='#111111', width=8, anchor='w')
        self.net_label.grid(row=1, column=5, sticky='w')

        # Start live stats update
        self._start_stats_update()

        # RIGHT COLUMN - Scrolling log
        right_frame = tk.Frame(main_frame, bg='#111111', bd=2, relief='sunken')
        right_frame.pack(side='right', fill='both', expand=True)

        # Log header
        log_header = tk.Label(
            right_frame,
            text="═══════════════ SYSTEM LOG ═══════════════",
            font=('Consolas', 10, 'bold'),
            fg=self.accent2_color,
            bg='#111111'
        )
        log_header.pack(pady=(8, 5))

        # Scrolling log text widget
        self.log_frame = tk.Frame(right_frame, bg='#111111')
        self.log_frame.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        # Create text widget with scrollbar
        scrollbar = tk.Scrollbar(self.log_frame)
        scrollbar.pack(side='right', fill='y')

        self.log_text = tk.Text(
            self.log_frame,
            bg='#0d0d0d',
            fg='#cccccc',
            font=('Consolas', 9),
            wrap='word',
            bd=0,
            highlightthickness=1,
            highlightbackground='#333333',
            insertbackground=self.accent_color,
            yscrollcommand=scrollbar.set
        )
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Configure text tags for colored log entries
        self.log_text.tag_configure('timestamp', foreground='#666666')
        self.log_text.tag_configure('speech', foreground=self.accent_color)
        self.log_text.tag_configure('system', foreground=self.accent2_color)
        self.log_text.tag_configure('ok', foreground=self.ok_color)
        self.log_text.tag_configure('warn', foreground=self.warn_color)
        self.log_text.tag_configure('fail', foreground=self.fail_color)
        self.log_text.tag_configure('phase', foreground='#ffffff', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('info', foreground='#888888')
        # New tags for user input and CORA actions
        self.log_text.tag_configure('user', foreground='#ffff00', font=('Consolas', 9, 'bold'))  # Yellow for user
        self.log_text.tag_configure('action', foreground='#ff9933')  # Orange for actions
        self.log_text.tag_configure('result', foreground='#66ff66')  # Light green for results
        self.log_text.tag_configure('thinking', foreground='#9999ff', font=('Consolas', 9, 'italic'))  # Purple for thinking

        # Make log read-only but allow selection
        self.log_text.config(state='disabled')

        # Close button (subtle)
        close_btn = tk.Button(
            main_frame,
            text="×",
            font=('Arial', 18, 'bold'),
            fg='#666666',
            bg=self.bg_color,
            activebackground='#333333',
            activeforeground='#ff0000',
            bd=0,
            command=self.close
        )
        close_btn.place(x=1160, y=5)

        # Bind escape to close
        self.root.bind('<Escape>', lambda e: self.close())

        # Initial log entry
        self._log_entry("C.O.R.A Boot Sequence Initiated", 'phase')
        self._log_entry("─" * 50, 'info')

        return self.root

    def _log_entry(self, text: str, tag: str = 'info'):
        """Add an entry to the scrolling log."""
        if not self.log_text:
            return

        timestamp = time.strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] ", 'timestamp')
        self.log_text.insert('end', f"{text}\n", tag)
        self.log_text.see('end')  # Auto-scroll to bottom
        self.log_text.config(state='disabled')

        if self.root:
            self.root.update()

    def log(self, text: str, level: str = 'info'):
        """Add a log entry with specified level (info, ok, warn, fail, system, speech)."""
        self._log_entry(text, level)

    def log_speech(self, text: str):
        """Log CORA's speech."""
        self._log_entry(f'CORA: "{text}"', 'speech')

    def log_system(self, text: str):
        """Log system information."""
        self._log_entry(f"[SYS] {text}", 'system')

    def log_phase(self, text: str):
        """Log phase header."""
        self._log_entry(f"{'═' * 15} {text} {'═' * 15}", 'phase')

    def log_ok(self, text: str):
        """Log success message."""
        self._log_entry(f"✓ {text}", 'ok')

    def log_warn(self, text: str):
        """Log warning message."""
        self._log_entry(f"⚠ {text}", 'warn')

    def log_fail(self, text: str):
        """Log failure message."""
        self._log_entry(f"✗ {text}", 'fail')

    def log_user(self, text: str):
        """Log user input/command."""
        self._log_entry(f"USER: {text}", 'user')

    def log_action(self, text: str):
        """Log CORA action (tool use, file operation, etc)."""
        self._log_entry(f"→ ACTION: {text}", 'action')

    def log_tool(self, tool_name: str, details: str = ""):
        """Log tool execution."""
        if details:
            self._log_entry(f"⚡ TOOL [{tool_name}]: {details}", 'action')
        else:
            self._log_entry(f"⚡ TOOL [{tool_name}]", 'action')

    def log_result(self, text: str):
        """Log action result."""
        self._log_entry(f"← RESULT: {text}", 'result')

    def log_thinking(self, text: str):
        """Log CORA's reasoning/thinking."""
        self._log_entry(f"💭 {text}", 'thinking')

    def set_phases(self, phase_names: List[str]):
        """Set up the phase indicators."""
        # Clear existing
        for widget in self.phases_container.winfo_children():
            widget.destroy()

        self.phases = [BootPhase(name=name) for name in phase_names]
        self.phase_labels = {}
        self.phase_indicators = {}

        for i, phase in enumerate(self.phases):
            frame = tk.Frame(self.phases_container, bg=self.bg_color)
            frame.pack(fill='x', pady=2)

            # Status indicator (circle)
            indicator = tk.Label(
                frame,
                text="○",
                font=('Consolas', 14),
                fg=self.pending_color,
                bg=self.bg_color,
                width=3
            )
            indicator.pack(side='left')
            self.phase_indicators[phase.name] = indicator

            # Phase name
            label = tk.Label(
                frame,
                text=phase.name,
                font=('Consolas', 11),
                fg='#888888',
                bg=self.bg_color,
                anchor='w'
            )
            label.pack(side='left', padx=10)
            self.phase_labels[phase.name] = label

    def update_phase(self, phase_name: str, status: str, message: str = ""):
        """Update a phase status."""
        if phase_name not in self.phase_indicators:
            return

        indicator = self.phase_indicators[phase_name]
        label = self.phase_labels[phase_name]

        if status == "running":
            indicator.config(text="◐", fg=self.accent_color)
            label.config(fg=self.accent_color)
        elif status == "ok":
            indicator.config(text="●", fg=self.ok_color)
            label.config(fg=self.ok_color)
        elif status == "warn":
            indicator.config(text="●", fg=self.warn_color)
            label.config(fg=self.warn_color)
        elif status == "fail":
            indicator.config(text="●", fg=self.fail_color)
            label.config(fg=self.fail_color)
        else:
            indicator.config(text="○", fg=self.pending_color)
            label.config(fg='#888888')

        # Update progress
        completed = sum(1 for p in self.phases if p.status in ['ok', 'warn', 'fail'])
        self.progress_var.set((completed / len(self.phases)) * 100)

        # Update phase object
        for p in self.phases:
            if p.name == phase_name:
                p.status = status
                p.message = message
                break

        if self.root:
            self.root.update()

    def set_status(self, text: str):
        """Update the status label."""
        if self.status_label:
            self.status_label.config(text=text)
            if self.root:
                self.root.update()

    def _start_stats_update(self):
        """Start the live stats update loop."""
        self._update_stats()

    def _update_stats(self):
        """Update live system stats every second."""
        if not self.root:
            return

        try:
            import psutil
            import subprocess

            # CPU
            cpu = psutil.cpu_percent(interval=0)
            cpu_color = self.ok_color if cpu < 70 else (self.warn_color if cpu < 90 else self.fail_color)
            if self.cpu_label:
                self.cpu_label.config(text=f"{cpu:.1f}%", fg=cpu_color)

            # Memory
            mem = psutil.virtual_memory()
            mem_pct = mem.percent
            mem_color = self.ok_color if mem_pct < 70 else (self.warn_color if mem_pct < 90 else self.fail_color)
            if self.mem_label:
                self.mem_label.config(text=f"{mem_pct:.1f}%", fg=mem_color)

            # Disk
            try:
                disk = psutil.disk_usage('C:\\')
            except:
                disk = psutil.disk_usage('/')
            disk_pct = disk.percent
            disk_color = self.ok_color if disk_pct < 80 else (self.warn_color if disk_pct < 95 else self.fail_color)
            if self.disk_label:
                self.disk_label.config(text=f"{disk_pct:.1f}%", fg=disk_color)

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
            if self.net_label:
                self.net_label.config(text="UP" if net_up else "DOWN", fg=self.ok_color if net_up else self.fail_color)

            # GPU via nvidia-smi
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split(', ')
                    if len(parts) >= 3:
                        gpu_util = float(parts[0])
                        gpu_mem_used = float(parts[1])
                        gpu_mem_total = float(parts[2])
                        gpu_mem_pct = (gpu_mem_used / gpu_mem_total) * 100 if gpu_mem_total > 0 else 0

                        gpu_color = self.ok_color if gpu_util < 70 else (self.warn_color if gpu_util < 90 else self.fail_color)
                        vram_color = self.ok_color if gpu_mem_pct < 70 else (self.warn_color if gpu_mem_pct < 90 else self.fail_color)

                        if self.gpu_label:
                            self.gpu_label.config(text=f"{gpu_util:.0f}%", fg=gpu_color)
                        if self.gpu_mem_label:
                            self.gpu_mem_label.config(text=f"{gpu_mem_pct:.0f}%", fg=vram_color)
            except:
                if self.gpu_label:
                    self.gpu_label.config(text="N/A", fg='#666666')
                if self.gpu_mem_label:
                    self.gpu_mem_label.config(text="N/A", fg='#666666')

        except Exception as e:
            pass

        # Schedule next update in 1 second
        if self.root:
            self.stats_update_id = self.root.after(1000, self._update_stats)

    def start_speaking(self, text: str):
        """Start waveform animation when speaking."""
        self.is_speaking = True
        if self.current_text:
            # Truncate long text for display
            display_text = text[:100] + "..." if len(text) > 100 else text
            self.current_text.config(text=f'"{display_text}"')
        # Log the full speech to the console
        self.log_speech(text)
        if self.waveform:
            self.waveform.start()
        if self.root:
            self.root.update()

    def stop_speaking(self):
        """Stop waveform animation."""
        self.is_speaking = False
        if self.waveform:
            self.waveform.stop()
        if self.root:
            self.root.update()

    def set_progress(self, value: float):
        """Set progress bar value (0-100)."""
        if self.progress_var:
            self.progress_var.set(value)
        if self.root:
            self.root.update()

    def close(self):
        """Close the display window."""
        # Stop stats updates
        if self.stats_update_id:
            try:
                self.root.after_cancel(self.stats_update_id)
            except:
                pass
            self.stats_update_id = None
        if self.waveform:
            self.waveform.stop()
        if self.root:
            self.root.destroy()
            self.root = None

    def run(self):
        """Run the tkinter mainloop."""
        if self.root:
            self.root.mainloop()


# Global display instance
_boot_display: Optional[BootDisplay] = None
_display_thread: Optional[threading.Thread] = None


def create_boot_display() -> BootDisplay:
    """Create and return a boot display instance."""
    global _boot_display
    _boot_display = BootDisplay()
    return _boot_display


def get_boot_display() -> Optional[BootDisplay]:
    """Get the current boot display instance."""
    return _boot_display


def close_boot_display():
    """Close the boot display."""
    global _boot_display
    if _boot_display:
        _boot_display.close()
        _boot_display = None


# Test the display
if __name__ == '__main__':
    print("Testing Boot Display...")

    display = BootDisplay()
    display.create_window()

    # Set up phases
    phases = [
        "Voice Synthesis",
        "AI Engine",
        "Hardware Check",
        "Core Tools",
        "Voice Systems",
        "External Services",
        "News Headlines",
        "Vision Test",
        "Image Generation",
        "Final Check"
    ]
    display.set_phases(phases)

    def simulate_boot():
        time.sleep(1)

        for i, phase in enumerate(phases):
            display.update_phase(phase, "running")
            display.set_status(f"Running: {phase}...")

            # Simulate speaking
            display.start_speaking(f"Now checking {phase}...")
            time.sleep(1.5)
            display.stop_speaking()

            # Complete phase
            status = "ok" if random.random() > 0.1 else "warn"
            display.update_phase(phase, status)
            time.sleep(0.3)

        display.set_status("Boot Complete - All Systems Online")
        time.sleep(3)
        display.close()

    # Run simulation in thread
    thread = threading.Thread(target=simulate_boot, daemon=True)
    thread.start()

    display.run()
    print("Test complete!")
