#!/usr/bin/env python3
"""ChatInputMixin: the chat_input methods of BootDisplay (split from ui/boot_display.py on 2026-10-14).
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


class ChatInputMixin:

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
        self._scalable_widgets.append((self.chat_input, 11, 'Consolas', ''))

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
        self._scalable_widgets.append((self.send_button, 10, 'Consolas', 'bold'))

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
        """Process user input - route to the assistant dispatcher (or a custom callback)."""
        self.log_user(text)

        if self.on_user_input:
            # Use callback to process input
            self.on_user_input(text)
        elif self._legacy_regex_enabled():
            self._default_process_input(text)
        else:
            self._dispatch_input(text)

    @staticmethod
    def _legacy_regex_enabled() -> bool:
        from ui import boot_display as _m
        """config.json assistant.legacy_regex -> use the old regex command chain
        instead of the LLM tool dispatcher (kept for comparison/debugging)."""
        try:
            import json
            with open(_m._PROJECT_DIR / 'config' / 'config.json', 'r', encoding='utf-8') as f:
                return bool((json.load(f).get('assistant') or {}).get('legacy_regex', False))
        except Exception:
            return False

    def _dispatch_input(self, text: str):
        """Send the message through ai.dispatcher: the model picks tools, CORA
        speaks sentence by sentence while the reply streams in."""
        mode = self.current_mode
        prompt = text
        # The mode buttons become hints the model can act on with its tools
        hints = {
            'screenshot': 'Take a screenshot and describe what is on screen, then answer: ',
            'vision': 'Look through the camera and describe what you see, then answer: ',
            'imagine': 'Generate an image of: ',
            'tasks': 'This is about my tasks (use the task tools): ',
        }
        if mode in hints:
            prompt = hints[mode] + text

        def run():
            try:
                from ai.dispatcher import get_dispatcher
                d = get_dispatcher()
                d.confirm_callback = self._confirm_on_ui
                self.log_thinking("Thinking...")
                tokens = []

                def on_event(kind, payload):
                    if kind == 'token':
                        tokens.append(payload)
                    elif kind == 'tool_call':
                        self.log_tool(payload['tool'], str(payload.get('arguments') or '')[:120])
                    elif kind == 'tool_result':
                        r = payload.get('result') or {}
                        msg = r.get('message') or r.get('error') or ''
                        if r.get('ok', True) and not r.get('error'):
                            self.log_result(f"{payload['tool']}: {str(msg)[:200]}")
                        else:
                            self.log_fail(f"{payload['tool']}: {str(msg)[:200]}")
                    elif kind == 'sentence':
                        pass   # logged by the voice when it actually plays (start_speaking)
                    elif kind == 'confirm_needed':
                        self.log_warn(f"Needs your OK: {payload['tool']} {payload.get('arguments')} - say yes or no")
                    elif kind == 'error':
                        self.log_fail(str(payload))

                result = d.handle(prompt, speak=True, on_event=on_event)
                if result.error:
                    self.log_fail(f"AI error: {result.error}")
                elif result.text:
                    voice_up = True
                    try:
                        from voice.tts import voice_status
                        voice_up = bool(voice_status().get('up'))
                    except Exception:
                        pass
                    if not result.spoke or not voice_up:
                        self.log_result(result.text)
                try:
                    self.update_operational_status(activity="Ready - Awaiting commands",
                                                   last_action=(result.tool_calls[-1]['name'] if result.tool_calls else 'chat'))
                except Exception:
                    pass
            except Exception as e:
                self.log_fail(f"Error: {e}")

        threading.Thread(target=run, daemon=True, name='dispatch').start()

    def _confirm_on_ui(self, question: str):
        """Ask the user to confirm a destructive tool. Runs the dialog on the Tk
        thread and blocks the calling worker thread for the answer (<= 2 min)."""
        if not self.root:
            return None
        import threading as _th
        done = _th.Event()
        answer = {'v': None}

        def ask():
            try:
                from tkinter import messagebox
                answer['v'] = bool(messagebox.askyesno("CORA needs your OK", f"Allow this action?\n\n{question}", parent=self.root))
            except Exception:
                answer['v'] = None
            finally:
                done.set()

        try:
            self.root.after(0, ask)
        except Exception:
            return None
        done.wait(120)
        return answer['v']

    def _speak(self, text: str, emotion: str = None):
        """Speak text through the shared unity-voice-v2 queue (non-blocking).

        The waveform is fed by the engine's playback callback via the shared
        audio buffer, so nothing here needs to start or stop it.
        """
        self.log_speech(text)
        try:
            from voice.tts import queue_speak
            if emotion is None:
                try:
                    from voice.emotion import detect_emotion
                    emotion = detect_emotion(text)
                except Exception:
                    emotion = 'neutral'
            queue_speak(text, emotion)
        except Exception as e:
            print(f"[TTS ERROR] {e}")

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
