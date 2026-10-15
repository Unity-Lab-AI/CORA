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
# Use a class to ensure single instance across imports
import threading

class _AudioBufferSingleton:
    """Singleton to share audio data between TTS and waveform."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.data = None
                    cls._instance.current_chunk = None
                    cls._instance.chunk_time = None  # None, not 0 - prevents false stale detection
                    cls._instance.start_time = None
                    cls._instance.sample_rate = 24000
                    cls._instance.active = False
                    cls._instance.data_lock = threading.Lock()
        return cls._instance

# Single global instance
_audio_buffer_singleton = _AudioBufferSingleton()

def get_audio_buffer():
    """Get the shared audio buffer for waveform visualization (thread-safe)."""
    with _audio_buffer_singleton.data_lock:
        return {
            'data': _audio_buffer_singleton.data,
            'current_chunk': _audio_buffer_singleton.current_chunk,
            'chunk_time': _audio_buffer_singleton.chunk_time,
            'start_time': _audio_buffer_singleton.start_time,
            'sample_rate': _audio_buffer_singleton.sample_rate,
            'active': _audio_buffer_singleton.active,
        }

# Lock for thread-safe access
_audio_buffer_lock = _audio_buffer_singleton.data_lock

def set_audio_data(audio_array, sample_rate=24000):
    """Set audio data for waveform visualization (called by TTS)."""
    with _audio_buffer_singleton.data_lock:
        _audio_buffer_singleton.data = audio_array
        _audio_buffer_singleton.start_time = time.time()
        _audio_buffer_singleton.sample_rate = sample_rate
        _audio_buffer_singleton.active = True

def clear_audio_data():
    """Clear audio data when done speaking."""
    with _audio_buffer_singleton.data_lock:
        _audio_buffer_singleton.active = False
        _audio_buffer_singleton.data = None
        _audio_buffer_singleton.current_chunk = None


def set_audio_chunk(chunk):
    """Set the current audio chunk being played RIGHT NOW (called from TTS callback)."""
    with _audio_buffer_singleton.data_lock:
        _audio_buffer_singleton.current_chunk = chunk
        _audio_buffer_singleton.chunk_time = time.time()
        _audio_buffer_singleton.active = True


class AudioWaveform(tk.Canvas):
    """Real-time audio waveform visualization - draws actual wave that follows voice."""

    def __init__(self, parent, width=480, height=100, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg='#0a0a0a', highlightthickness=1,
                        highlightbackground='#302050', **kwargs)
        self.width = width
        self.height = height
        self.is_playing = False
        self.animation_id = None
        self.wave_line = None
        self.glow_line = None
        self.num_points = 100  # More points = smoother wave
        self.wave_points = [0.0] * self.num_points
        self.sample_rate = 24000

        # Rolling buffer of actual sample values (not just amplitudes)
        # This stores downsampled audio samples that scroll across
        self.sample_buffer = [0.0] * self.num_points

        # Phase offset for animation smoothness
        self.phase = 0.0

        # Draw initial flat line
        self._draw_flat_line()

    def _draw_flat_line(self):
        """Draw a flat center line when idle."""
        self.delete("all")
        center_y = self.height // 2
        # Draw a dim baseline
        self.create_line(0, center_y, self.width, center_y,
                        fill='#301040', width=2)

    def _build_wave_coords(self, amplitudes):
        """Build coordinate list for smooth wave from amplitudes.

        Args:
            amplitudes: List of amplitude values (0-1 range) for each point

        Returns:
            List of [x0, y0, x1, y1, ...] coordinates for create_line
        """
        center_y = self.height // 2
        max_amplitude = (self.height // 2) - 4  # Leave margin

        coords = []
        step = self.width / (len(amplitudes) - 1) if len(amplitudes) > 1 else self.width

        for i, amp in enumerate(amplitudes):
            x = int(i * step)
            # Amplitude goes both up and down from center
            y_offset = int(amp * max_amplitude)
            y = center_y - y_offset  # Negative = up
            coords.extend([x, y])

        return coords

    def start(self):
        """Start the waveform animation - runs forever."""
        if not self.is_playing:
            self.is_playing = True
            self.wave_points = [0.0] * self.num_points
            self.sample_buffer = [0.0] * self.num_points
            self._animate()

    def stop(self):
        """Stop the animation timer (called on window close). While the window
        lives the waveform runs continuously and shows flat with no audio."""
        self.is_playing = False
        aid = getattr(self, 'animation_id', None)
        if aid is not None:
            try:
                self.after_cancel(aid)
            except Exception:
                pass
            self.animation_id = None

    def _fade_out(self):
        """Legacy fade out - no longer used."""
        pass

    def _animate(self):
        """Animate the waveform using real-time audio chunks from TTS.

        This creates a scrolling waveform effect where actual audio samples
        move from right to left, creating visible peaks and valleys that
        correspond to the voice.

        This runs FOREVER once started - never stops.
        """

        # Get audio chunk from TTS
        chunk = None
        has_audio = False

        try:
            with _audio_buffer_singleton.data_lock:
                raw_chunk = _audio_buffer_singleton.current_chunk
                chunk_time = _audio_buffer_singleton.chunk_time
                is_active = _audio_buffer_singleton.active

                if chunk_time is not None:
                    time_since_chunk = time.time() - chunk_time
                else:
                    time_since_chunk = 999

                # Accept chunks up to 300ms old
                if raw_chunk is not None and len(raw_chunk) > 0 and time_since_chunk < 0.3 and is_active:
                    has_audio = True
                    if HAS_NUMPY and hasattr(raw_chunk, 'copy'):
                        chunk = raw_chunk.copy()
                    else:
                        chunk = list(raw_chunk)
        except Exception as e:
            print(f"[WAVE ERROR] {e}")

        if has_audio and chunk is not None:
            try:
                if HAS_NUMPY:
                    if not isinstance(chunk, np.ndarray):
                        chunk = np.array(chunk, dtype=np.float32)

                    # Normalize if needed (int16 to float)
                    max_val = np.max(np.abs(chunk))
                    if max_val > 1.5:
                        chunk = chunk / 32768.0

                    # Downsample the chunk to get actual waveform samples
                    # We want to extract ~10-20 samples per frame to scroll in
                    chunk_len = len(chunk)
                    samples_to_add = min(20, self.num_points // 5)  # Add some samples each frame

                    if chunk_len >= samples_to_add:
                        # Evenly sample from the chunk
                        indices = np.linspace(0, chunk_len - 1, samples_to_add, dtype=int)
                        new_samples = chunk[indices]

                        # Amplify HEAVILY for visibility (Kokoro outputs tiny floats 0.01-0.3)
                        # First find the peak of this chunk for adaptive scaling
                        chunk_peak = np.max(np.abs(chunk))
                        if chunk_peak > 0.001:
                            # Scale so peaks nearly fill the display (0.95 = 95% of height)
                            scale_factor = 0.95 / chunk_peak
                            scale_factor = min(scale_factor, 40.0)  # Cap at 40x amplification
                        else:
                            scale_factor = 20.0
                        new_samples = new_samples * scale_factor

                        # Clamp to -1 to 1 range (prevents overflow past boundary)
                        new_samples = np.clip(new_samples, -1.0, 1.0)

                        # Shift existing samples left and add new ones on right
                        self.sample_buffer = self.sample_buffer[samples_to_add:] + list(new_samples)

                else:
                    # Fallback without numpy - take peak samples
                    chunk_len = len(chunk)
                    samples_to_add = min(10, self.num_points // 10)

                    if chunk_len >= samples_to_add:
                        # Find chunk peak for adaptive scaling
                        chunk_peak = max(abs(float(x)) for x in chunk)
                        if chunk_peak > 0.001:
                            scale_factor = min(0.95 / chunk_peak, 40.0)
                        else:
                            scale_factor = 20.0

                        step = chunk_len // samples_to_add
                        new_samples = []
                        for i in range(samples_to_add):
                            idx = i * step
                            val = float(chunk[idx]) * scale_factor
                            val = max(-1.0, min(1.0, val))
                            new_samples.append(val)

                        self.sample_buffer = self.sample_buffer[samples_to_add:] + new_samples

                # Copy sample buffer to wave points with smoothing
                for i in range(self.num_points):
                    target = self.sample_buffer[i]
                    # Smooth transition to prevent jitter
                    self.wave_points[i] = self.wave_points[i] * 0.3 + target * 0.7

            except Exception as e:
                # On error, just decay
                for i in range(self.num_points):
                    self.wave_points[i] *= 0.9
        else:
            # No audio - decay existing wave toward zero
            decay = 0.92
            for i in range(self.num_points):
                self.wave_points[i] *= decay
                self.sample_buffer[i] *= decay

        # Draw the wave
        self._draw_wave()

        # Schedule next frame (~40 FPS for smooth scrolling)
        if self.is_playing:
            self.animation_id = self.after(25, self._animate)

    def _draw_wave(self):
        """Draw the waveform on canvas."""
        self.delete("all")

        # Get actual canvas width (may have been resized)
        actual_width = self.winfo_width()
        if actual_width < 10:
            actual_width = self.width  # Fallback to configured width

        center_y = self.height // 2
        max_amp = (self.height // 2) - 5  # Leave small margin

        # Draw center reference line (dim) - full width
        self.create_line(0, center_y, actual_width, center_y,
                        fill='#201030', width=1)

        # Build coordinates for the wave - use actual width to fill entire box
        coords = []
        step = actual_width / (self.num_points - 1) if self.num_points > 1 else 1

        for i, amp in enumerate(self.wave_points):
            x = int(i * step)
            y = center_y - int(amp * max_amp)
            coords.extend([x, y])

        if len(coords) >= 4:
            # Draw outer glow (widest, dimmest)
            self.create_line(
                *coords,
                fill='#400060',
                width=8,
                smooth=True,
                splinesteps=16
            )

            # Draw mid glow
            self.create_line(
                *coords,
                fill='#8000a0',
                width=5,
                smooth=True,
                splinesteps=16
            )

            # Draw main wave line
            self.create_line(
                *coords,
                fill='#ff40ff',
                width=3,
                smooth=True,
                splinesteps=16
            )

            # Draw bright core
            self.create_line(
                *coords,
                fill='#ffc0ff',
                width=1,
                smooth=True,
                splinesteps=16
            )
from ui.boot_display_parts import WindowMixin, ChatInputMixin, LegacyInputMixin, LoggingMixin, PhasesMixin, StatsMixin, SpeechMixin  # the class's method groups, split on 2026-10-14


class BootDisplay(WindowMixin, ChatInputMixin, LegacyInputMixin, LoggingMixin, PhasesMixin, StatsMixin, SpeechMixin):
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
