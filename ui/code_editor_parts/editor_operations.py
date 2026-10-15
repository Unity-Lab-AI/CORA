#!/usr/bin/env python3
"""EditorOperationsMixin: the editor_operations methods of CodeEditorModal (split from ui/code_editor.py on 2026-10-14).
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


class EditorOperationsMixin:

    # ==================== EDITOR OPERATIONS ====================

    def _insert_content(self, content: str):
        """Insert content into editor."""
        self.code_text.delete('1.0', 'end')
        self.code_text.insert('1.0', content)
        self._update_line_numbers()

    def _update_line_numbers(self):
        """Update line numbers."""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')

        content = self.code_text.get('1.0', 'end-1c')
        line_count = content.count('\n') + 1

        line_nums = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert('1.0', line_nums)
        self.line_numbers.config(state='disabled')

    def _sync_scroll(self, *args):
        """Sync line numbers scroll."""
        self.line_numbers.yview_moveto(args[0])
        return True

    def _scroll_both(self, *args):
        """Scroll both widgets."""
        self.code_text.yview(*args)
        self.line_numbers.yview(*args)

    def _apply_syntax_highlighting(self):
        """Apply syntax highlighting."""
        for tag in self.SYNTAX_COLORS.keys():
            self.code_text.tag_remove(tag, '1.0', 'end')

        content = self.code_text.get('1.0', 'end')
        patterns = self.SYNTAX_PATTERNS.get(self.language, {})

        for tag_name, pattern in patterns.items():
            for match in re.finditer(pattern, content, re.MULTILINE):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.code_text.tag_add(tag_name, start_idx, end_idx)

    def _on_key_release(self, event=None):
        """Handle key release."""
        self._update_line_numbers()
        self._update_cursor_position()
        self._update_stats()
        self._check_modified()

        if hasattr(self, '_highlight_after_id'):
            self.window.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.window.after(300, self._apply_syntax_highlighting)

    def _update_cursor_position(self):
        """Update cursor position."""
        pos = self.code_text.index('insert')
        line, col = pos.split('.')
        self.cursor_label.config(text=f"Ln {line}, Col {int(col) + 1}")

    def _update_stats(self):
        """Update stats."""
        content = self.code_text.get('1.0', 'end-1c')
        lines = content.count('\n') + 1
        chars = len(content)
        self.stats_label.config(text=f"Lines: {lines} | Chars: {chars}")

    def _check_modified(self):
        """Check if modified."""
        current = self.code_text.get('1.0', 'end-1c')
        self.is_modified = current != self.original_content
        self.modified_label.config(text="● Modified" if self.is_modified else "")
