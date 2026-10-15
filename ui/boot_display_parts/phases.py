#!/usr/bin/env python3
"""PhasesMixin: the phases methods of BootDisplay (split from ui/boot_display.py on 2026-10-14).
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


class PhasesMixin:

    def set_phases(self, phase_names: List[str]):
        from ui import boot_display as _m
        """Set up the phase indicators in 2 columns."""
        # Clear existing
        for widget in self.phases_col_left.winfo_children():
            widget.destroy()
        for widget in self.phases_col_right.winfo_children():
            widget.destroy()

        # Remove old phase widgets from scalable list
        self._scalable_widgets = [w for w in self._scalable_widgets
                                   if w[0] not in list(self.phase_labels.values()) + list(self.phase_indicators.values())]

        self.phases = [_m.BootPhase(name=name) for name in phase_names]
        self.phase_labels = {}
        self.phase_indicators = {}

        # Split phases into 2 columns
        half = (len(self.phases) + 1) // 2  # First column gets extra if odd

        for i, phase in enumerate(self.phases):
            # Choose column - first half goes left, second half goes right
            parent = self.phases_col_left if i < half else self.phases_col_right

            frame = tk.Frame(parent, bg=self.bg_color)
            frame.pack(fill='x', pady=0)  # Tight packing

            # Status indicator (circle) - smaller font
            indicator = tk.Label(
                frame,
                text="○",
                font=('Consolas', 8),
                fg=self.pending_color,
                bg=self.bg_color,
                width=2
            )
            indicator.pack(side='left')
            self.phase_indicators[phase.name] = indicator
            self._scalable_widgets.append((indicator, 8, 'Consolas', ''))

            # Phase name - smaller font, truncate if needed
            display_name = phase.name[:18] if len(phase.name) > 18 else phase.name
            label = tk.Label(
                frame,
                text=display_name,
                font=('Consolas', 8),
                fg='#888888',
                bg=self.bg_color,
                anchor='w'
            )
            label.pack(side='left', padx=2)
            self.phase_labels[phase.name] = label
            self._scalable_widgets.append((label, 8, 'Consolas', ''))

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

    def switch_to_operational_mode(self):
        """Switch from boot phases view to operational monitoring mode."""
        if not self.phases_outer:
            return

        # Clear the phases display
        for widget in self.phases_container.winfo_children():
            widget.destroy()

        # Create operational monitoring panel
        self.phases_container.pack_forget()

        # Operational status frame
        op_frame = tk.Frame(self.phases_outer, bg=self.bg_color)
        op_frame.pack(fill='both', expand=True)

        # Header
        header = tk.Label(
            op_frame,
            text="── OPERATIONAL STATUS ──",
            font=('Consolas', 9, 'bold'),
            fg=self.accent2_color,
            bg=self.bg_color
        )
        header.pack(pady=(5, 3))
        self._scalable_widgets.append((header, 9, 'Consolas', 'bold'))

        # Current activity label
        activity_frame = tk.Frame(op_frame, bg='#111111', bd=1, relief='groove')
        activity_frame.pack(fill='x', padx=5, pady=2)

        status_lbl = tk.Label(
            activity_frame,
            text="STATUS:",
            font=('Consolas', 8),
            fg='#888888',
            bg='#111111'
        )
        status_lbl.pack(side='left', padx=5)
        self._scalable_widgets.append((status_lbl, 8, 'Consolas', ''))

        self.activity_label = tk.Label(
            activity_frame,
            text="Ready - Awaiting commands",
            font=('Consolas', 9, 'bold'),
            fg=self.ok_color,
            bg='#111111'
        )
        self.activity_label.pack(side='left', padx=5, pady=3)
        self._scalable_widgets.append((self.activity_label, 9, 'Consolas', 'bold'))

        # Systems status grid
        systems_frame = tk.Frame(op_frame, bg='#111111', bd=1, relief='groove')
        systems_frame.pack(fill='x', padx=5, pady=2)

        systems_grid = tk.Frame(systems_frame, bg='#111111')
        systems_grid.pack(fill='x', padx=5, pady=3)

        # System indicators (2 columns)
        systems = [
            ('Voice', 'voice_status'),
            ('AI', 'ai_status'),
            ('Tools', 'tools_status'),
            ('Memory', 'memory_status'),
        ]

        self.system_status_labels = {}
        for i, (name, key) in enumerate(systems):
            row = i // 2
            col = (i % 2) * 2

            name_lbl = tk.Label(
                systems_grid,
                text=f"{name}:",
                font=('Consolas', 8),
                fg='#888888',
                bg='#111111',
                width=8,
                anchor='e'
            )
            name_lbl.grid(row=row, column=col, sticky='e', padx=(5, 2))
            self._scalable_widgets.append((name_lbl, 8, 'Consolas', ''))

            status_label = tk.Label(
                systems_grid,
                text="●",
                font=('Consolas', 10),
                fg=self.ok_color,
                bg='#111111',
                width=3
            )
            status_label.grid(row=row, column=col + 1, sticky='w')
            self.system_status_labels[key] = status_label
            self._scalable_widgets.append((status_label, 10, 'Consolas', ''))

        # Last action frame
        action_frame = tk.Frame(op_frame, bg='#111111', bd=1, relief='groove')
        action_frame.pack(fill='x', padx=5, pady=2)

        last_lbl = tk.Label(
            action_frame,
            text="LAST:",
            font=('Consolas', 8),
            fg='#888888',
            bg='#111111'
        )
        last_lbl.pack(side='left', padx=5)
        self._scalable_widgets.append((last_lbl, 8, 'Consolas', ''))

        self.last_action_label = tk.Label(
            action_frame,
            text="Boot complete",
            font=('Consolas', 8),
            fg='#aaaaaa',
            bg='#111111'
        )
        self.last_action_label.pack(side='left', padx=5, pady=3)
        self._scalable_widgets.append((self.last_action_label, 8, 'Consolas', ''))

        if self.root:
            self.root.update()

    def update_operational_status(self, activity: str = None, last_action: str = None, systems: dict = None):
        """Update the operational monitoring display."""
        try:
            if activity and hasattr(self, 'activity_label'):
                self.activity_label.config(text=activity)

            if last_action and hasattr(self, 'last_action_label'):
                # Truncate if too long
                display_action = last_action[:40] + "..." if len(last_action) > 40 else last_action
                self.last_action_label.config(text=display_action)

            if systems and hasattr(self, 'system_status_labels'):
                for key, status in systems.items():
                    if key in self.system_status_labels:
                        color = self.ok_color if status == 'ok' else (self.warn_color if status == 'warn' else self.fail_color)
                        self.system_status_labels[key].config(fg=color)

            if self.root:
                self.root.update()
        except:
            pass

    def set_progress(self, value: float):
        """Set progress bar value (0-100)."""
        if self.progress_var:
            self.progress_var.set(value)
        if self.root:
            self.root.update()
