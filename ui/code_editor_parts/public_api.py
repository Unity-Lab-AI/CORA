#!/usr/bin/env python3
"""PublicApiMixin: the public_api methods of CodeEditorModal (split from ui/code_editor.py on 2026-10-14).
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


class PublicApiMixin:

    # ==================== PUBLIC API ====================

    def get_content(self) -> str:
        return self.code_text.get('1.0', 'end-1c')

    def set_content(self, content: str):
        self._insert_content(content)
        self._apply_syntax_highlighting()
        self._check_modified()

    def apply_edit(self, instruction: str):
        """Apply edit via voice command."""
        self.ai_entry.delete(0, 'end')
        self.ai_entry.insert(0, instruction)
        self.request_ai_edit(instruction)

    def save_file(self) -> bool:
        return self._save()

    def push_to_remote(self):
        self._push_to_github()
