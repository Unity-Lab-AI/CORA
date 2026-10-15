#!/usr/bin/env python3
"""WindowMixin: the window methods of BootDisplay (split from ui/boot_display.py on 2026-10-14).
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


class WindowMixin:

    def create_window(self):
        from ui import boot_display as _m
        """Create the boot display window with waveform and scrolling log."""
        self.root = tk.Tk()
        self.root.title("C.O.R.A - Boot Sequence")
        self.root.configure(bg=self.bg_color)

        # Handle window close - exit entire application
        def on_close():
            """When GUI window is closed, exit the entire application: close the
            window (mainloop returns, the boot thread is a daemon), with a hard
            exit only as a 3 s safety net for anything stuck in a C call."""
            print("[CORA] Window closed - shutting down...")
            try:
                from voice.tts import stop_speaking
                stop_speaking()
            except Exception:
                pass
            self.close()
            import os
            import threading as _th
            _th.Timer(3.0, lambda: os._exit(0)).start()

        self.root.protocol("WM_DELETE_WINDOW", on_close)

        # Window size and position
        self.base_width = 1200
        self.base_height = 800
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - self.base_width) // 2
        y = (screen_h - self.base_height) // 2
        self.root.geometry(f"{self.base_width}x{self.base_height}+{x}+{y}")

        # Enable proper Windows behavior - maximize, resize, minimize all work
        self.root.resizable(True, True)
        self.root.minsize(800, 600)

        # Use window manager for proper z-layering
        try:
            from ui.window_manager import bring_to_front
            bring_to_front(self.root)
        except:
            self.root.lift()
            self.root.focus_force()

        # Track widgets that need scaling
        self._scalable_widgets = []

        # Bind resize event for scaling
        self.root.bind('<Configure>', self._on_window_resize)
        self._last_resize_time = 0  # Debounce resize events

        # Main container with two columns
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # LEFT COLUMN - Status and phases (use weight for proper resizing)
        left_frame = tk.Frame(main_frame, bg=self.bg_color)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Header
        self.header = tk.Label(
            left_frame,
            text="C.O.R.A",
            font=('Consolas', 42, 'bold'),
            fg=self.accent_color,
            bg=self.bg_color
        )
        self.header.pack(pady=(5, 0))
        self._scalable_widgets.append((self.header, 42, 'Consolas', 'bold'))

        self.subtitle = tk.Label(
            left_frame,
            text="Cognitive Operations & Reasoning Assistant",
            font=('Consolas', 10),
            fg=self.accent2_color,
            bg=self.bg_color
        )
        self.subtitle.pack(pady=(0, 10))
        self._scalable_widgets.append((self.subtitle, 10, 'Consolas', ''))

        # Waveform visualization
        wave_frame = tk.Frame(left_frame, bg=self.bg_color)
        wave_frame.pack(fill='x', pady=(5, 10))

        self.wave_label = tk.Label(
            wave_frame,
            text="▶ VOICE SYNTHESIS",
            font=('Consolas', 9),
            fg='#666666',
            bg=self.bg_color
        )
        self.wave_label.pack(anchor='w')
        self._scalable_widgets.append((self.wave_label, 9, 'Consolas', ''))

        # Waveform canvas - 100px tall for visible wave movement
        self.waveform = _m.AudioWaveform(wave_frame, width=480, height=100)
        self.waveform.pack(fill='x')

        # Start waveform animation immediately - it runs continuously
        # and automatically shows waves when receiving audio data
        self.waveform.start()

        # Current speech text (what CORA is saying)
        self.current_text = tk.Label(
            left_frame,
            text="",
            font=('Consolas', 10, 'italic'),
            fg=self.accent_color,
            bg=self.bg_color,
            wraplength=470
        )
        self.current_text.pack(pady=5, fill='x')
        self._scalable_widgets.append((self.current_text, 10, 'Consolas', 'italic'))

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

        # Phase indicators frame - 2 columns to save vertical space
        self.phases_outer = tk.Frame(left_frame, bg=self.bg_color, height=180)
        self.phases_outer.pack(fill='x', pady=5)
        self.phases_outer.pack_propagate(False)  # Keep fixed height

        # Container for 2-column phase layout
        self.phases_container = tk.Frame(self.phases_outer, bg=self.bg_color)
        self.phases_container.pack(fill='both', expand=True)

        # Left and right columns for phases
        self.phases_col_left = tk.Frame(self.phases_container, bg=self.bg_color)
        self.phases_col_left.pack(side='left', fill='both', expand=True)
        self.phases_col_right = tk.Frame(self.phases_container, bg=self.bg_color)
        self.phases_col_right.pack(side='left', fill='both', expand=True)

        # Status label
        self.status_label = tk.Label(
            left_frame,
            text="Initializing...",
            font=('Consolas', 12, 'bold'),
            fg=self.accent2_color,
            bg=self.bg_color
        )
        self.status_label.pack(pady=8)
        self._scalable_widgets.append((self.status_label, 12, 'Consolas', 'bold'))

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
        self._scalable_widgets.append((self.log_text, 9, 'Consolas', ''))

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

        # Close button (subtle) - use pack instead of place for better resize handling
        # Since we have native window decorations, this is a secondary close button
        self.close_btn = tk.Button(
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
        self.close_btn.place(relx=0.98, y=5, anchor='ne')
        self._scalable_widgets.append((self.close_btn, 18, 'Arial', 'bold'))

        # No hotkey bindings - user can close via X button only

        # Initial log entry
        self._log_entry("C.O.R.A Boot Sequence Initiated", 'phase')
        self._log_entry("─" * 50, 'info')

        # Create chat input frame (hidden until boot complete)
        self._create_chat_input()

        return self.root

    def close(self):
        """Close the display window."""
        self._closing = True
        # Stop stats collector thread
        self._stats_running = False
        # Stop the speech-text poller
        tid = getattr(self, '_speech_timer_id', None)
        if tid is not None:
            try:
                self.root.after_cancel(tid)
            except Exception:
                pass
            self._speech_timer_id = None
        # Stop stats UI updates
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

    def _on_window_resize(self, event):
        """Handle window resize - scale fonts and UI elements."""
        # Only respond to root window resize events
        if event.widget != self.root:
            return

        # Debounce resize events (only update every 100ms)
        current_time = time.time()
        if current_time - self._last_resize_time < 0.1:
            return
        self._last_resize_time = current_time

        # Calculate scale factor based on window size vs base size
        width_scale = event.width / self.base_width
        height_scale = event.height / self.base_height
        scale = (width_scale + height_scale) / 2

        # Clamp scale factor between 0.6 and 1.8
        scale = max(0.6, min(1.8, scale))

        # Update all registered scalable widgets
        for widget, base_size, font_family, font_weight in self._scalable_widgets:
            try:
                new_size = max(8, int(base_size * scale))  # Minimum font size of 8
                if font_weight:
                    widget.configure(font=(font_family, new_size, font_weight))
                else:
                    widget.configure(font=(font_family, new_size))
            except tk.TclError:
                pass  # Widget may have been destroyed
            except Exception:
                pass

        # Also update waveform dimensions if it exists
        if self.waveform and hasattr(self.waveform, 'width'):
            try:
                new_width = max(300, int(480 * width_scale))
                new_height = max(40, int(50 * height_scale))
                self.waveform.configure(width=new_width, height=new_height)
                self.waveform.width = new_width
                self.waveform.height = new_height
                # Recalculate bar dimensions
                self.waveform.bar_width = max(2, (new_width - 20) // self.waveform.num_bars)
                self.waveform._create_bars()
            except:
                pass

        # Update wraplength for current_text label
        if self.current_text:
            try:
                new_wrap = max(300, int(470 * width_scale))
                self.current_text.configure(wraplength=new_wrap)
            except:
                pass

    def run(self):
        """Run the tkinter mainloop with speech queue processing."""
        if self.root:
            # Start speech queue processor
            self._process_speech_queue()
            self.root.mainloop()
