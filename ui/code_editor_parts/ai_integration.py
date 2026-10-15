#!/usr/bin/env python3
"""AiIntegrationMixin: the ai_integration methods of CodeEditorModal (split from ui/code_editor.py on 2026-10-14).
Module names of ui.code_editor are read through `_m` (imported lazily per method), so rebinding there is seen here."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from typing import Optional, Callable, Dict, Any, List, Tuple
from pathlib import Path
import threading
import difflib
import re
import os
import json
import urllib.request
import urllib.error

# Import window manager
from ui.window_manager import create_window, bring_to_front


class AiIntegrationMixin:

    # ==================== AI INTEGRATION ====================

    def _on_ai_focus(self, event=None):
        current = self.ai_entry.get()
        if current.startswith("e.g.,"):
            self.ai_entry.delete(0, 'end')
            self.ai_entry.config(fg=self.fg_color)

    def _on_ai_unfocus(self, event=None):
        if not self.ai_entry.get().strip():
            self.ai_entry.delete(0, 'end')
            self.ai_entry.insert(0, "e.g., 'add error handling' or 'rename variable x to count'")
            self.ai_entry.config(fg='#666666')

    def _on_ai_submit(self, event=None):
        command = self.ai_entry.get().strip()
        if not command or command.startswith("e.g.,"):
            return
        self.request_ai_edit(command)

    def request_ai_edit(self, command: str):
        """Request AI to edit the code."""
        if self.ai_processing:
            return

        self.ai_processing = True
        self.ai_status.config(text="Processing...", fg=self.accent_color)
        self.apply_btn.config(state='disabled')

        current_code = self.code_text.get('1.0', 'end-1c')

        def ai_thread():
            try:
                from ai.ollama import generate

                prompt = f"""You are a code editing assistant. Modify the following code according to the user's request.

USER REQUEST: {command}

CURRENT CODE:
```{self.language}
{current_code}
```

IMPORTANT:
- Return ONLY the modified code, no explanations
- Keep the same formatting style
- Make minimal changes necessary

MODIFIED CODE:"""

                result = generate(
                    prompt=prompt,
                    system="You are a precise code editor. Return only the modified code without markdown code blocks or explanations.",
                    temperature=0.3,
                    max_tokens=4000
                )

                if result.content:
                    new_code = result.content.strip()
                    if new_code.startswith('```'):
                        lines = new_code.split('\n')[1:]
                        if lines and lines[-1].strip() == '```':
                            lines = lines[:-1]
                        new_code = '\n'.join(lines)

                    self.window.after(0, lambda: self._show_diff(current_code, new_code))
                else:
                    self.window.after(0, lambda: self._show_status("AI returned no changes"))

            except Exception as e:
                self.window.after(0, lambda: self._show_status(f"AI error: {e}"))
            finally:
                self.ai_processing = False
                self.window.after(0, lambda: self.apply_btn.config(state='normal'))
                self.window.after(0, lambda: self.ai_status.config(text=""))

        threading.Thread(target=ai_thread, daemon=True).start()

    def _show_diff(self, old_code: str, new_code: str):
        """Show diff."""
        self.pending_changes = new_code

        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)

        diff = list(difflib.unified_diff(old_lines, new_lines, fromfile='Current', tofile='Proposed', lineterm=''))

        self.diff_frame.pack(fill='x', pady=5, before=self.code_text.master.master)

        self.diff_text.config(state='normal')
        self.diff_text.delete('1.0', 'end')

        for line in diff:
            if line.startswith('+++') or line.startswith('---'):
                self.diff_text.insert('end', line + '\n', 'header')
            elif line.startswith('+'):
                self.diff_text.insert('end', line + '\n', 'added')
            elif line.startswith('-'):
                self.diff_text.insert('end', line + '\n', 'removed')
            elif line.startswith('@@'):
                self.diff_text.insert('end', line + '\n', 'header')
            else:
                self.diff_text.insert('end', line + '\n', 'context')

        self.diff_text.config(state='disabled')
        self._show_status("Review changes and click Accept or Reject")

    def _accept_changes(self):
        """Accept changes."""
        if self.pending_changes:
            self._insert_content(self.pending_changes)
            self._apply_syntax_highlighting()
            self._check_modified()
            self.pending_changes = None
        self.diff_frame.pack_forget()
        self._show_status("Changes applied!")

    def _reject_changes(self):
        """Reject changes."""
        self.pending_changes = None
        self.diff_frame.pack_forget()
        self._show_status("Changes rejected")
