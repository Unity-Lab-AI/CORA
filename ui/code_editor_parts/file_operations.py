#!/usr/bin/env python3
"""FileOperationsMixin: the file_operations methods of CodeEditorModal (split from ui/code_editor.py on 2026-10-14).
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


class FileOperationsMixin:

    # ==================== FILE OPERATIONS ====================

    def _copy_all(self):
        content = self.code_text.get('1.0', 'end-1c')
        self.window.clipboard_clear()
        self.window.clipboard_append(content)
        self._show_status("Copied to clipboard!")

    def _undo(self):
        try:
            self.code_text.edit_undo()
            self._on_key_release()
        except:
            pass

    def _redo(self):
        try:
            self.code_text.edit_redo()
            self._on_key_release()
        except:
            pass

    def _save(self):
        """Save file."""
        if not self.file_path:
            return self._save_as()

        try:
            content = self.code_text.get('1.0', 'end-1c')
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.original_content = content
            self.is_modified = False
            self.modified_label.config(text="")
            self._show_status(f"Saved: {Path(self.file_path).name}")

            if self.on_save_callback:
                self.on_save_callback(self.file_path, content)
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save: {e}")
            return False

    def _save_as(self):
        """Save as."""
        file_types = [("Python", "*.py"), ("JavaScript", "*.js"), ("JSON", "*.json"), ("All", "*.*")]
        path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=file_types)

        if path:
            self.file_path = path
            self.file_label.config(text=Path(path).name)
            self.path_label.config(text=path if len(path) <= 50 else "..." + path[-47:])
            return self._save()
        return False

    def _push_to_github(self):
        """Push to GitHub."""
        if not self.file_path:
            messagebox.showwarning("Push", "Save the file locally first.")
            return

        if self.is_modified:
            if not self._save():
                return

        def push_thread():
            try:
                from cora_tools.git_ops import get_git

                git = get_git(str(Path(self.file_path).parent))
                self._show_status("Staging changes...")

                result = git.add(self.file_path)
                if not result['success']:
                    self._show_status(f"Git add failed: {result.get('error')}")
                    return

                commit_msg = f"Update {Path(self.file_path).name} via CORA"
                result = git.commit(commit_msg)
                if not result['success']:
                    self._show_status(f"Commit failed: {result.get('error')}")
                    return

                self._show_status("Pushing...")
                result = git.push()
                if result['success']:
                    self._show_status("✓ Pushed to GitHub!")
                else:
                    self._show_status(f"Push failed: {result.get('error')}")

            except Exception as e:
                self._show_status(f"Error: {e}")

        threading.Thread(target=push_thread, daemon=True).start()

    def _on_close(self):
        from ui import code_editor as _m
        """Handle close."""
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Close anyway?"):
                return
        _m._active_editor = None
        if self.window:
            self.window.destroy()

    def _show_status(self, message: str):
        """Show status message."""
        self.ai_status.config(text=message, fg='#888888')
        if hasattr(self, '_status_after_id'):
            self.window.after_cancel(self._status_after_id)
        self._status_after_id = self.window.after(3000, lambda: self.ai_status.config(text=""))
