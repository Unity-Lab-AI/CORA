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
import os
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

# Project directory for loading system prompt
_PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent

# Cache for system prompt
_system_prompt_cache = None


def get_system_prompt() -> str:
    """Load CORA's full system prompt from config/system_prompt.txt."""
    global _system_prompt_cache
    if _system_prompt_cache is not None:
        return _system_prompt_cache

    system_prompt_path = _PROJECT_DIR / 'config' / 'system_prompt.txt'
    if system_prompt_path.exists():
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            _system_prompt_cache = f.read()
    else:
        _system_prompt_cache = ""
    return _system_prompt_cache

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


# Global audio buffer for sharing between TTS and waveform
_audio_buffer = None
_audio_buffer_lock = None

def get_audio_buffer():
    """Get the shared audio buffer for waveform visualization."""
    global _audio_buffer, _audio_buffer_lock
    if _audio_buffer_lock is None:
        import threading
        _audio_buffer_lock = threading.Lock()
    if _audio_buffer is None:
        _audio_buffer = {'data': None, 'position': 0, 'active': False}
    return _audio_buffer

def set_audio_data(audio_array):
    """Set audio data for waveform visualization (called by TTS)."""
    buf = get_audio_buffer()
    with _audio_buffer_lock:
        buf['data'] = audio_array
        buf['position'] = 0
        buf['active'] = True

def clear_audio_data():
    """Clear audio data when done speaking."""
    buf = get_audio_buffer()
    with _audio_buffer_lock:
        buf['active'] = False


class AudioWaveform(tk.Canvas):
    """Real-time audio waveform visualization using shared audio buffer from TTS."""

    def __init__(self, parent, width=400, height=80, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg='#0a0a0a', highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.is_playing = False
        self.bars = []
        self.num_bars = 50
        self.bar_width = max(2, (width - 20) // self.num_bars)
        self.animation_id = None
        self.audio_data = [0] * self.num_bars
        self.target_heights = [0] * self.num_bars
        self.current_heights = [0.0] * self.num_bars
        self.smoothing = 0.3  # Smoothing factor for animation
        self.sample_rate = 24000  # Kokoro TTS sample rate
        self.samples_per_frame = self.sample_rate // 30  # ~30 FPS

        # Colors - goth/cyberpunk gradient
        self.color_low = (50, 0, 80)      # Dark purple
        self.color_mid = (180, 0, 180)    # Magenta
        self.color_high = (255, 50, 150)  # Hot pink

        self._create_bars()

    def _create_bars(self):
        """Create the waveform bars."""
        self.delete("all")
        self.bars = []
        gap = 2
        total_width = self.num_bars * (self.bar_width + gap)
        start_x = (self.width - total_width) // 2

        for i in range(self.num_bars):
            x = start_x + i * (self.bar_width + gap)
            bar = self.create_rectangle(
                x, self.height // 2 - 1,
                x + self.bar_width, self.height // 2 + 1,
                fill='#1a0a2a', outline=''
            )
            self.bars.append(bar)

    def _get_color(self, intensity):
        """Get color based on intensity (0-1)."""
        if intensity < 0.5:
            # Blend low to mid
            t = intensity * 2
            r = int(self.color_low[0] + (self.color_mid[0] - self.color_low[0]) * t)
            g = int(self.color_low[1] + (self.color_mid[1] - self.color_low[1]) * t)
            b = int(self.color_low[2] + (self.color_mid[2] - self.color_low[2]) * t)
        else:
            # Blend mid to high
            t = (intensity - 0.5) * 2
            r = int(self.color_mid[0] + (self.color_high[0] - self.color_mid[0]) * t)
            g = int(self.color_mid[1] + (self.color_high[1] - self.color_mid[1]) * t)
            b = int(self.color_mid[2] + (self.color_high[2] - self.color_mid[2]) * t)
        return f'#{r:02x}{g:02x}{b:02x}'

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

        # Animate bars back to flat
        self._fade_out()

    def _fade_out(self):
        """Smoothly fade bars to flat."""
        center_y = self.height // 2
        all_flat = True

        for i, bar in enumerate(self.bars):
            self.current_heights[i] *= 0.7
            if self.current_heights[i] > 0.5:
                all_flat = False

            height = max(1, int(self.current_heights[i]))
            x1, _, x2, _ = self.coords(bar)
            self.coords(bar, x1, center_y - height, x2, center_y + height)

            if height <= 1:
                self.itemconfig(bar, fill='#1a0a2a')

        if not all_flat and not self.is_playing:
            self.after(30, self._fade_out)

    def _animate(self):
        """Animate the waveform using real audio data from TTS."""
        if not self.is_playing:
            return

        center_y = self.height // 2
        max_height = (self.height // 2) - 5

        # Try to get real audio data from shared buffer
        has_real_audio = False
        buf = get_audio_buffer()

        if buf['active'] and buf['data'] is not None:
            try:
                with _audio_buffer_lock:
                    audio = buf['data']
                    pos = buf['position']

                    if audio is not None and len(audio) > 0:
                        # Get next chunk of audio samples
                        end_pos = min(pos + self.samples_per_frame, len(audio))

                        if pos < len(audio):
                            chunk = audio[pos:end_pos]
                            buf['position'] = end_pos

                            if len(chunk) > 0:
                                has_real_audio = True
                                # Split chunk into bars
                                samples_per_bar = max(1, len(chunk) // self.num_bars)

                                for i in range(self.num_bars):
                                    start = i * samples_per_bar
                                    end = min(start + samples_per_bar, len(chunk))
                                    if start < len(chunk):
                                        bar_chunk = chunk[start:end]
                                        # RMS amplitude
                                        if HAS_NUMPY:
                                            rms = float(np.sqrt(np.mean(bar_chunk**2)))
                                        else:
                                            rms = sum(abs(x) for x in bar_chunk) / len(bar_chunk)
                                        # Scale to 0-1 (adjust multiplier for sensitivity)
                                        self.target_heights[i] = min(1.0, rms * 8)
                                    else:
                                        self.target_heights[i] = 0
            except Exception as e:
                has_real_audio = False

        # If no real audio data, show flat/idle state (not fake waves)
        if not has_real_audio:
            for i in range(self.num_bars):
                self.target_heights[i] = 0.02  # Nearly flat when not speaking

        # Smooth animation towards target
        for i, bar in enumerate(self.bars):
            # Smooth interpolation
            self.current_heights[i] += (self.target_heights[i] - self.current_heights[i]) * self.smoothing

            height = int(self.current_heights[i] * max_height)
            height = max(2, height)

            x1, _, x2, _ = self.coords(bar)
            self.coords(bar, x1, center_y - height, x2, center_y + height)

            # Color based on height
            intensity = self.current_heights[i]
            color = self._get_color(intensity)
            self.itemconfig(bar, fill=color)

        self.animation_id = self.after(33, self._animate)  # ~30 FPS


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
        self._stats_running = False
        self._stats_data = {}
        self._stats_thread = None

        # Chat input (appears after boot)
        self.chat_frame = None
        self.chat_input = None
        self.send_button = None
        self.boot_complete = False
        self.on_user_input = None  # Callback for user input

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

        # Phase indicators frame - fixed height, don't expand so stats stay visible
        phases_frame = tk.Frame(left_frame, bg=self.bg_color, height=250)
        phases_frame.pack(fill='x', pady=5)
        phases_frame.pack_propagate(False)  # Keep fixed height
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

        # No hotkey bindings - user can close via X button only

        # Initial log entry
        self._log_entry("C.O.R.A Boot Sequence Initiated", 'phase')
        self._log_entry("─" * 50, 'info')

        # Create chat input frame (hidden until boot complete)
        self._create_chat_input()

        return self.root

    def _create_chat_input(self):
        """Create the chat input area at bottom of window."""
        # Chat frame at bottom of window
        self.chat_frame = tk.Frame(self.root, bg='#111111', height=60)
        self.chat_frame.pack(side='bottom', fill='x', padx=15, pady=(0, 10))
        self.chat_frame.pack_propagate(False)

        # Tool buttons row - these modify the system prompt
        btn_frame = tk.Frame(self.chat_frame, bg='#111111')
        btn_frame.pack(fill='x', pady=(5, 3))

        # Mode buttons - set the tool/action context
        self.current_mode = None
        self.mode_buttons = {}

        tools = [
            ("📸 Screenshot", "screenshot", "Take a screenshot and describe what you see"),
            ("👁 Vision", "vision", "Look through the camera and describe what you see"),
            ("🎨 Create", "imagine", "Generate an image based on the description"),
            ("📋 Tasks", "tasks", "Help manage my tasks and todo list"),
            ("💬 Chat", None, "Normal conversation"),
        ]

        for text, mode, desc in tools:
            btn = tk.Button(
                btn_frame,
                text=text,
                font=('Consolas', 8),
                fg='#cccccc',
                bg='#222222',
                activebackground='#333333',
                activeforeground=self.accent_color,
                bd=0,
                padx=8,
                pady=2,
                command=lambda m=mode, d=desc: self._set_mode(m, d)
            )
            btn.pack(side='left', padx=2)
            self.mode_buttons[mode] = btn

        # Mode indicator
        self.mode_label = tk.Label(
            btn_frame,
            text="",
            font=('Consolas', 8, 'italic'),
            fg='#888888',
            bg='#111111'
        )
        self.mode_label.pack(side='right', padx=5)

        # Input row
        input_frame = tk.Frame(self.chat_frame, bg='#111111')
        input_frame.pack(fill='x', pady=(0, 3))

        # Input field
        self.chat_input = tk.Entry(
            input_frame,
            font=('Consolas', 11),
            fg=self.fg_color,
            bg='#1a1a1a',
            insertbackground=self.accent_color,
            relief='flat',
            bd=0,
            highlightthickness=1,
            highlightbackground='#333333',
            highlightcolor=self.accent_color
        )
        self.chat_input.pack(side='left', fill='x', expand=True, padx=(0, 5), ipady=5)
        self.chat_input.insert(0, "Talk to CORA...")
        self.chat_input.bind('<FocusIn>', self._on_input_focus)
        self.chat_input.bind('<FocusOut>', self._on_input_unfocus)
        self.chat_input.bind('<Return>', self._on_send)

        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            font=('Consolas', 10, 'bold'),
            fg='#000000',
            bg=self.accent_color,
            activebackground=self.accent2_color,
            activeforeground='#000000',
            bd=0,
            padx=15,
            pady=5,
            command=self._on_send
        )
        self.send_button.pack(side='right')

    def _on_input_focus(self, event=None):
        """Clear placeholder when focused."""
        if self.chat_input.get() == "Talk to CORA...":
            self.chat_input.delete(0, 'end')
            self.chat_input.config(fg=self.fg_color)

    def _on_input_unfocus(self, event=None):
        """Restore placeholder if empty."""
        if not self.chat_input.get():
            self.chat_input.insert(0, "Talk to CORA...")
            self.chat_input.config(fg='#666666')

    def _on_send(self, event=None):
        """Handle send button/enter key."""
        text = self.chat_input.get().strip()
        if text and text != "Talk to CORA...":
            self.chat_input.delete(0, 'end')
            self._process_user_input(text)

    def _set_mode(self, mode: str, desc: str):
        """Set the current tool mode."""
        self.current_mode = mode

        # Update button colors
        for m, btn in self.mode_buttons.items():
            if m == mode:
                btn.config(bg=self.accent_color, fg='#000000')
            else:
                btn.config(bg='#222222', fg='#cccccc')

        # Update mode indicator
        if mode:
            self.mode_label.config(text=f"Mode: {mode.upper()}")
            self.log(f"Mode set to: {mode.upper()} - {desc}", 'info')
        else:
            self.mode_label.config(text="")
            self.log("Mode: Normal chat", 'info')

    def _process_user_input(self, text: str):
        """Process user input - route to AI chat with mode context."""
        self.log_user(text)

        if self.on_user_input:
            # Use callback to process input
            self.on_user_input(text)
        else:
            # Default: try to use AI chat directly
            self._default_process_input(text)

    def _default_process_input(self, text: str):
        """Default input processing using AI chat with mode-based tool use."""
        import threading

        mode = self.current_mode

        def process():
            try:
                # MODE: Screenshot - take screenshot, analyze with AI
                if mode == 'screenshot':
                    self.log_action("Taking screenshot...")
                    try:
                        from tools.screenshots import desktop
                        result = desktop()
                        if result.success:
                            self.log_result(f"Screenshot saved: {result.path}")
                            # Analyze with vision AI
                            from ai.ollama import generate_with_image
                            prompt = text if text else "Describe what you see on this screen"
                            vision_result = generate_with_image(prompt, result.path)
                            if vision_result.content:
                                self.log_result(vision_result.content)
                                self._speak(vision_result.content)
                            else:
                                self._speak(f"Screenshot captured. {result.width} by {result.height} pixels.")
                        else:
                            self.log_fail(f"Screenshot failed: {result.error}")
                    except Exception as e:
                        self.log_fail(f"Screenshot error: {e}")
                    return

                # MODE: Vision - look through camera with AI
                elif mode == 'vision':
                    prompt = text if text else "Describe what you see"
                    self.log_action("Looking through camera...")
                    try:
                        import cv2
                        from pathlib import Path
                        cap = cv2.VideoCapture(0)
                        if cap.isOpened():
                            ret, frame = cap.read()
                            cap.release()
                            if ret:
                                import os
                                proj_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
                                cam_path = proj_dir / 'data' / 'camera' / 'see_capture.jpg'
                                cam_path.parent.mkdir(parents=True, exist_ok=True)
                                cv2.imwrite(str(cam_path), frame)

                                from ai.ollama import generate_with_image
                                result = generate_with_image(prompt, str(cam_path))
                                if result.content:
                                    self.log_result(result.content)
                                    self._speak(result.content)
                                else:
                                    self.log_warn("Vision analysis failed")
                            else:
                                self.log_fail("Camera capture failed")
                        else:
                            self.log_fail("No camera available")
                    except Exception as e:
                        self.log_fail(f"Vision error: {e}")
                    return

                # MODE: Imagine - generate image from text
                elif mode == 'imagine':
                    if text:
                        self.log_action(f"Generating image: {text}")
                        self._speak(f"Creating {text}")
                        try:
                            from tools.image_gen import generate_image
                            result = generate_image(text)
                            if result.get('success'):
                                self.log_result(f"Image saved: {result.get('path')}")
                                self._speak("Image generated")
                            else:
                                self.log_fail(f"Generation failed: {result.get('error')}")
                        except Exception as e:
                            self.log_fail(f"Image gen error: {e}")
                    else:
                        self.log_warn("Please describe what image to create")
                    return

                # MODE: Tasks - task management with AI
                elif mode == 'tasks':
                    self.log_action("Loading tasks for context...")
                    task_context = ""
                    try:
                        from tools.tasks import TaskManager
                        tm = TaskManager()
                        if tm.tasks:
                            task_context = f"Current tasks: {[t.get('text', '') for t in tm.tasks[:10]]}"
                    except:
                        task_context = "No tasks loaded"

                    # Send to AI with task context
                    self.log_thinking("Thinking about your tasks...")
                    try:
                        from ai.ollama import chat
                        system_prompt = get_system_prompt()
                        if task_context:
                            system_prompt += f"\n\n{task_context}"
                        response = chat(
                            messages=[{'role': 'user', 'content': text}],
                            system=system_prompt,
                            temperature=0.7,
                            max_tokens=300
                        )
                        if response.content:
                            self.log_result(response.content)
                            self._speak(response.content)
                        elif response.error:
                            self.log_fail(f"AI error: {response.error}")
                    except Exception as e:
                        self.log_fail(f"Chat error: {e}")
                    return

                # DEFAULT MODE: Let AI decide what to do
                # First, ask AI if this requires image generation
                self.log_thinking("Thinking...")

                should_generate_image = False
                image_prompt = ""

                try:
                    from ai.ollama import generate

                    # Ask AI to decide if image generation is needed
                    decision = generate(
                        prompt=f'User request: "{text}"\n\nDoes this request require generating/creating/showing an image or picture? Reply with ONLY "YES: <image description>" or "NO".',
                        system="You decide if requests need image generation. Visual requests like 'show me a cat', 'draw a sunset', 'create an image of X' = YES. Questions, conversation, info requests = NO. Reply ONLY with YES: <description> or NO.",
                        temperature=0.1,
                        max_tokens=100
                    )

                    if decision.content:
                        response_text = decision.content.strip()
                        if response_text.upper().startswith("YES"):
                            should_generate_image = True
                            # Extract the image description
                            if ":" in response_text:
                                image_prompt = response_text.split(":", 1)[1].strip()
                            else:
                                image_prompt = text  # Fallback to original text
                except Exception as e:
                    pass  # If decision fails, fall through to regular chat

                if should_generate_image:
                    # Use AI-generated prompt or fall back to cleaned user text
                    prompt = image_prompt if image_prompt else text
                    self.log_action(f"Generating image: {prompt}")
                    self._speak(f"Fine, I'll make your fucking picture")
                    try:
                        from tools.image_gen import generate_image
                        result = generate_image(prompt)
                        if result.get('success'):
                            self.log_result(f"Image saved: {result.get('path')}")
                            self._speak("There. Your shitty image is done.")
                            # Show the image
                            try:
                                from tools.image_gen import show_fullscreen_image
                                show_fullscreen_image(result.get('path'), duration=5)
                            except:
                                pass
                        else:
                            self.log_fail(f"Generation failed: {result.get('error')}")
                            self._speak("Image generation fucked up. Try again.")
                    except Exception as e:
                        self.log_fail(f"Image gen error: {e}")
                        self._speak(f"Shit broke: {e}")
                else:
                    # Regular chat
                    self.log_thinking("Thinking...")
                    try:
                        from ai.ollama import chat
                        response = chat(
                            messages=[{'role': 'user', 'content': text}],
                            system=get_system_prompt(),
                            temperature=0.7,
                            max_tokens=300
                        )
                        if response.content:
                            self.log_result(response.content)
                            self._speak(response.content)
                        elif response.error:
                            self.log_fail(f"AI error: {response.error}")
                    except Exception as e:
                        self.log_fail(f"Chat error: {e}")

            except Exception as e:
                self.log_fail(f"Error: {e}")

        # Run in thread so UI doesn't freeze
        threading.Thread(target=process, daemon=True).start()

    def _speak(self, text: str):
        """Speak text via TTS - shows text first, then speaks in background."""
        # Show text in UI FIRST so user can read along while TTS plays
        self.start_speaking(text)

        def speak_thread():
            try:
                from voice.tts import KokoroTTS
                tts = KokoroTTS(voice='af_bella', speed=1.0)
                if tts.initialize():
                    tts.speak(text)

                # Update UI safely from thread
                if self.root:
                    self.root.after(0, self.stop_speaking)
            except Exception as e:
                if self.root:
                    self.root.after(0, self.stop_speaking)

        # Run TTS in separate thread so UI stays responsive
        threading.Thread(target=speak_thread, daemon=True).start()

    def set_input_callback(self, callback):
        """Set callback for user input processing."""
        self.on_user_input = callback

    def enable_chat_mode(self):
        """Enable chat mode after boot completes."""
        self.boot_complete = True
        if self.chat_input:
            self.chat_input.focus_set()
        self._log_entry("─" * 50, 'info')
        self._log_entry("Boot complete! Type below to chat with CORA.", 'ok')
        self._log_entry("Or use the tool buttons for quick commands.", 'info')

    def _log_entry(self, text: str, tag: str = 'info'):
        """Add an entry to the scrolling log."""
        if not self.log_text:
            return
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.config(state='normal')
            self.log_text.insert('end', f"[{timestamp}] ", 'timestamp')
            self.log_text.insert('end', f"{text}\n", tag)
            self.log_text.see('end')  # Auto-scroll to bottom
            self.log_text.config(state='disabled')
            # Force immediate update so text shows before TTS
            if self.root:
                self.root.update_idletasks()
        except:
            pass

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

    def start_speaking(self, text: str):
        """Start waveform animation when speaking."""
        self.is_speaking = True
        try:
            if self.current_text:
                # Show full text - no truncation
                self.current_text.config(text=f'"{text}"')
            # Log the full speech to the console
            self.log_speech(text)
            if self.waveform:
                self.waveform.start()
        except:
            pass

    def stop_speaking(self):
        """Stop waveform animation."""
        self.is_speaking = False
        try:
            if self.waveform:
                self.waveform.stop()
        except:
            pass

    def set_progress(self, value: float):
        """Set progress bar value (0-100)."""
        if self.progress_var:
            self.progress_var.set(value)
        if self.root:
            self.root.update()

    def close(self):
        """Close the display window."""
        # Stop stats collector thread
        self._stats_running = False
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
