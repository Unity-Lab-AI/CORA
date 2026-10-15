#!/usr/bin/env python3
"""FileTreeOperationsMixin: the file_tree_operations methods of CodeEditorModal (split from ui/code_editor.py on 2026-10-14).
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


class FileTreeOperationsMixin:

    # ==================== FILE TREE OPERATIONS ====================

    def _populate_file_tree(self, root_path: str):
        """Populate file tree with local folder contents."""
        # Clear tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        root_path = Path(root_path)
        if not root_path.exists():
            return

        # Add root
        root_id = self.file_tree.insert('', 'end', text=f"📂 {root_path.name}", open=True)
        self.file_tree.item(root_id, tags=('folder',))

        # Recursively add contents
        self._add_folder_contents(root_id, root_path)

    def _add_folder_contents(self, parent_id: str, folder_path: Path, depth: int = 0):
        """Recursively add folder contents to tree."""
        if depth > 5:  # Limit depth
            return

        try:
            items = sorted(folder_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

            for item in items:
                # Skip hidden files and common ignore patterns
                if item.name.startswith('.') or item.name in ('__pycache__', 'node_modules', 'venv', '.git'):
                    continue

                if item.is_dir():
                    icon = self.FILE_ICONS.get('folder', '📁')
                    folder_id = self.file_tree.insert(parent_id, 'end', text=f"{icon} {item.name}")
                    self.file_tree.item(folder_id, values=(str(item),), tags=('folder',))
                    self._add_folder_contents(folder_id, item, depth + 1)
                else:
                    ext = item.suffix.lower()
                    icon = self.FILE_ICONS.get(ext, '📄')
                    file_id = self.file_tree.insert(parent_id, 'end', text=f"{icon} {item.name}")
                    self.file_tree.item(file_id, values=(str(item),), tags=('file',))
        except PermissionError:
            pass

    def _populate_github_tree(self):
        """Populate file tree with GitHub repo contents."""
        if not self.github_repo:
            return

        # Clear tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        owner, repo = self.github_repo

        def fetch_tree():
            try:
                # Get repo tree
                url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{self.github_branch}?recursive=1"
                req = urllib.request.Request(url, headers={'User-Agent': 'CORA-Assistant'})

                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read().decode())

                # Build tree structure
                self.window.after(0, lambda: self._build_github_tree(data.get('tree', []), repo))

            except Exception as e:
                self.window.after(0, lambda: self._show_status(f"GitHub error: {e}"))

        threading.Thread(target=fetch_tree, daemon=True).start()
        self._show_status("Loading GitHub repo...")

    def _build_github_tree(self, tree_data: List[Dict], repo_name: str):
        """Build tree view from GitHub API data."""
        root_id = self.file_tree.insert('', 'end', text=f"🐙 {repo_name}", open=True)

        # Create folder structure
        folders = {}
        folders[''] = root_id

        for item in tree_data:
            path = item['path']
            item_type = item['type']

            # Get parent folder
            parts = path.split('/')
            parent_path = '/'.join(parts[:-1])
            name = parts[-1]

            parent_id = folders.get(parent_path, root_id)

            if item_type == 'tree':  # folder
                icon = self.FILE_ICONS.get('folder', '📁')
                folder_id = self.file_tree.insert(parent_id, 'end', text=f"{icon} {name}")
                self.file_tree.item(folder_id, values=(path, 'github_folder'), tags=('folder',))
                folders[path] = folder_id
            else:  # file
                ext = Path(name).suffix.lower()
                icon = self.FILE_ICONS.get(ext, '📄')
                file_id = self.file_tree.insert(parent_id, 'end', text=f"{icon} {name}")
                self.file_tree.item(file_id, values=(path, 'github_file'), tags=('file',))

        self._show_status(f"Loaded {len(tree_data)} items from GitHub")

    def _on_file_select(self, event=None):
        """Handle file selection in tree."""
        selection = self.file_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.file_tree.item(item, 'values')
        tags = self.file_tree.item(item, 'tags')

        if 'folder' in tags:
            # Toggle folder
            if self.file_tree.item(item, 'open'):
                self.file_tree.item(item, open=False)
            else:
                self.file_tree.item(item, open=True)
            return

        if not values:
            return

        path = values[0]

        # Check if GitHub file
        if len(values) > 1 and values[1] == 'github_file':
            self._open_github_file(path)
        else:
            self._open_local_file(path)

    def _open_local_file(self, path: str):
        """Open a local file in the editor."""
        # Check for unsaved changes
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "Discard current changes?"):
                return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.file_path = path
            self.original_content = content
            self.language = self._detect_language(path)

            self._insert_content(content)
            self._apply_syntax_highlighting()

            self.file_label.config(text=Path(path).name)
            self.lang_label.config(text=f"[{self.language.upper()}]")
            self.path_label.config(text=path if len(path) <= 50 else "..." + path[-47:])
            self.is_modified = False
            self.modified_label.config(text="")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def _open_github_file(self, path: str):
        """Open a file from GitHub in the editor."""
        if not self.github_repo:
            return

        owner, repo = self.github_repo

        def fetch_file():
            try:
                url = f"https://raw.githubusercontent.com/{owner}/{repo}/{self.github_branch}/{path}"
                req = urllib.request.Request(url, headers={'User-Agent': 'CORA-Assistant'})

                with urllib.request.urlopen(req, timeout=30) as response:
                    content = response.read().decode('utf-8')

                self.window.after(0, lambda: self._load_github_content(path, content))

            except Exception as e:
                self.window.after(0, lambda: self._show_status(f"Failed to fetch: {e}"))

        self._show_status(f"Fetching {path}...")
        threading.Thread(target=fetch_file, daemon=True).start()

    def _load_github_content(self, path: str, content: str):
        """Load fetched GitHub content into editor."""
        self.file_path = None  # Not a local file
        self.github_url = f"https://github.com/{self.github_repo[0]}/{self.github_repo[1]}/blob/{self.github_branch}/{path}"
        self.original_content = content
        self.language = self._detect_language(path)

        self._insert_content(content)
        self._apply_syntax_highlighting()

        filename = Path(path).name
        self.file_label.config(text=f"🐙 {filename}")
        self.lang_label.config(text=f"[{self.language.upper()}]")
        self.path_label.config(text=path)
        self.is_modified = False
        self.modified_label.config(text="")
        self._show_status(f"Opened {filename} from GitHub")

    def _refresh_tree(self):
        """Refresh the file tree."""
        if self.root_path:
            self._populate_file_tree(self.root_path)
        elif self.github_repo:
            self._populate_github_tree()

    def _open_folder(self):
        """Open a local folder."""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.root_path = folder
            self.github_repo = None
            self.github_url = None
            self._populate_file_tree(folder)
            self.window.title(f"CORA IDE - {Path(folder).name}")

    def _open_github_repo(self):
        """Open a GitHub repository."""
        # Simple dialog for repo URL
        dialog = tk.Toplevel(self.window)
        dialog.title("Open GitHub Repository")
        dialog.geometry("500x150")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.window)
        dialog.grab_set()

        tk.Label(
            dialog, text="Enter GitHub repository URL:",
            font=('Consolas', 11),
            fg=self.fg_color, bg=self.bg_color
        ).pack(pady=15)

        entry = tk.Entry(
            dialog, font=('Consolas', 11),
            fg=self.fg_color, bg='#1a1a1a',
            insertbackground=self.accent_color,
            width=50
        )
        entry.pack(padx=20, pady=5, ipady=5)
        entry.insert(0, "https://github.com/owner/repo")
        entry.select_range(0, 'end')
        entry.focus()

        def on_ok():
            url = entry.get().strip()
            if url:
                self._parse_github_url(url)
                if self.github_repo:
                    self.root_path = None
                    self._populate_github_tree()
                    self.window.title(f"CORA IDE - {self.github_repo[1]}")
            dialog.destroy()

        def on_key(e):
            if e.keysym == 'Return':
                on_ok()

        entry.bind('<Key>', on_key)

        btn_frame = tk.Frame(dialog, bg=self.bg_color)
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame, text="Open", font=('Consolas', 10),
            fg='black', bg=self.accent_color,
            activebackground='#ff6b6b',
            relief='flat', padx=20, pady=5,
            command=on_ok
        ).pack(side='left', padx=10)

        tk.Button(
            btn_frame, text="Cancel", font=('Consolas', 10),
            fg='white', bg='#4a4a6a',
            activebackground='#5a5a7a',
            relief='flat', padx=20, pady=5,
            command=dialog.destroy
        ).pack(side='left', padx=10)
