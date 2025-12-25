#!/usr/bin/env python3
"""
C.O.R.A Code Editor / IDE Modal
Full-featured code editor with:
- File tree browser (local folders + GitHub repos)
- Syntax highlighting with line numbers
- AI-powered editing (tell CORA what to change)
- Diff preview before accepting changes
- Save locally / Push to GitHub
- Copy, Undo, Redo functionality
- Voice/text command integration

Created by: Unity AI Lab
"""

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

# Track active editor instance for voice commands
_active_editor: Optional['CodeEditorModal'] = None


def get_active_editor() -> Optional['CodeEditorModal']:
    """Get the currently active code editor for voice commands."""
    return _active_editor


class CodeEditorModal:
    """Full-featured code editor/IDE with file tree and AI integration."""

    # Syntax highlighting patterns by language
    SYNTAX_PATTERNS = {
        'python': {
            'keywords': r'\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|raise|break|continue|pass|lambda|and|or|not|in|is|None|True|False|async|await|global|nonlocal)\b',
            'strings': r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'|\"[^\"\\]*(?:\\.[^\"\\]*)*\"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            'comments': r'(#.*$)',
            'functions': r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'numbers': r'\b(\d+\.?\d*)\b',
            'decorators': r'(@\w+)',
        },
        'javascript': {
            'keywords': r'\b(const|let|var|function|class|if|else|for|while|do|switch|case|break|continue|return|try|catch|finally|throw|new|this|super|extends|import|export|from|default|async|await|null|undefined|true|false)\b',
            'strings': r'(`[\s\S]*?`|\"[^\"\\]*(?:\\.[^\"\\]*)*\"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            'comments': r'(//.*$|/\*[\s\S]*?\*/)',
            'functions': r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'numbers': r'\b(\d+\.?\d*)\b',
        },
        'json': {
            'keys': r'\"([^\"]+)\"(?=\s*:)',
            'strings': r':\s*(\"[^\"]*\")',
            'numbers': r':\s*(\d+\.?\d*)',
            'booleans': r'\b(true|false|null)\b',
        },
        'html': {
            'tags': r'(</?[a-zA-Z][a-zA-Z0-9]*)',
            'attributes': r'\s([a-zA-Z-]+)=',
            'strings': r'(\"[^\"]*\"|\'[^\']*\')',
            'comments': r'(<!--[\s\S]*?-->)',
        },
        'css': {
            'selectors': r'([.#]?[a-zA-Z][a-zA-Z0-9_-]*)\s*\{',
            'properties': r'([a-zA-Z-]+)\s*:',
            'values': r':\s*([^;]+)',
            'comments': r'(/\*[\s\S]*?\*/)',
        }
    }

    # Colors for syntax highlighting (Dracula theme)
    SYNTAX_COLORS = {
        'keywords': '#ff79c6',      # Pink
        'strings': '#f1fa8c',       # Yellow
        'comments': '#6272a4',      # Gray-blue
        'functions': '#50fa7b',     # Green
        'numbers': '#bd93f9',       # Purple
        'decorators': '#ffb86c',    # Orange
        'keys': '#8be9fd',          # Cyan
        'booleans': '#ff79c6',      # Pink
        'tags': '#ff79c6',          # Pink
        'attributes': '#50fa7b',    # Green
        'selectors': '#8be9fd',     # Cyan
        'properties': '#66d9ef',    # Light blue
        'values': '#f8f8f2',        # White
    }

    # File icons by extension
    FILE_ICONS = {
        '.py': '🐍', '.pyw': '🐍',
        '.js': '📜', '.jsx': '⚛️', '.ts': '📘', '.tsx': '⚛️',
        '.html': '🌐', '.htm': '🌐',
        '.css': '🎨', '.scss': '🎨', '.sass': '🎨',
        '.json': '📋', '.yaml': '📋', '.yml': '📋', '.xml': '📋',
        '.md': '📝', '.txt': '📄', '.rst': '📄',
        '.java': '☕', '.kt': '🅺',
        '.cpp': '⚙️', '.c': '⚙️', '.h': '⚙️', '.hpp': '⚙️',
        '.go': '🐹', '.rs': '🦀', '.rb': '💎', '.php': '🐘',
        '.sh': '🖥️', '.bat': '🖥️', '.ps1': '🖥️',
        '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️', '.svg': '🖼️',
        '.git': '📦', '.gitignore': '🚫',
        'folder': '📁', 'folder_open': '📂',
    }

    def __init__(self):
        self.window = None
        self.code_text = None
        self.line_numbers = None
        self.file_tree = None
        self.file_path = None
        self.root_path = None  # Root folder being browsed
        self.original_content = ""
        self.current_content = ""
        self.language = "python"
        self.is_modified = False
        self.github_url = None
        self.github_repo = None  # (owner, repo) tuple
        self.github_branch = "main"
        self.on_save_callback = None
        self.diff_mode = False
        self.pending_changes = None
        self.open_files = {}  # path -> content cache

        # Theme colors
        self.bg_color = '#1a1a2e'
        self.editor_bg = '#0d0d0d'
        self.fg_color = '#e0e0e0'
        self.accent_color = '#e94560'
        self.accent2_color = '#00ffff'
        self.tree_bg = '#111111'
        self.tree_select = '#2a2a4a'
        self.line_num_bg = '#0a0a0a'
        self.line_num_fg = '#555555'

        # AI integration
        self.ai_processing = False

    def open(self,
             file_path: str = None,
             folder_path: str = None,
             content: str = "",
             language: str = None,
             github_url: str = None,
             title: str = "Code Editor",
             on_save: Callable = None) -> tk.Toplevel:
        """
        Open the code editor modal.

        Args:
            file_path: Local file path to open
            folder_path: Local folder to browse
            content: Initial content (if not loading from file)
            language: Programming language for syntax highlighting
            github_url: GitHub repo or file URL
            title: Window title
            on_save: Callback when file is saved

        Returns:
            The editor window
        """
        global _active_editor
        _active_editor = self

        self.file_path = file_path
        self.on_save_callback = on_save

        # Determine root path for file tree
        if folder_path:
            self.root_path = folder_path
        elif file_path:
            self.root_path = str(Path(file_path).parent)
        elif github_url:
            self.github_url = github_url
            self._parse_github_url(github_url)

        # Load content from file if path provided
        if file_path and not content:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = f"# Error loading file: {e}"

        self.original_content = content
        self.current_content = content

        # Detect language from file extension
        if language:
            self.language = language
        elif file_path:
            self.language = self._detect_language(file_path)

        # Create window
        display_title = f"CORA IDE - {title}"
        if folder_path:
            display_title = f"CORA IDE - {Path(folder_path).name}"
        elif file_path:
            display_title = f"CORA IDE - {Path(file_path).parent.name}"
        elif github_url and self.github_repo:
            display_title = f"CORA IDE - {self.github_repo[1]}"

        self.window = create_window(
            title=display_title,
            width=1400,
            height=850,
            bg=self.bg_color,
            resizable=True,
            center=True,
            on_close=self._on_close,
            min_width=900,
            min_height=500
        )

        self._create_ui()

        # Load file tree
        if self.root_path:
            self._populate_file_tree(self.root_path)
        elif self.github_repo:
            self._populate_github_tree()

        # Load initial file content
        if content:
            self._insert_content(content)
            self._apply_syntax_highlighting()

        return self.window

    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()
        lang_map = {
            '.py': 'python', '.pyw': 'python',
            '.js': 'javascript', '.jsx': 'javascript', '.ts': 'javascript', '.tsx': 'javascript',
            '.json': 'json',
            '.html': 'html', '.htm': 'html',
            '.css': 'css', '.scss': 'css', '.sass': 'css',
            '.java': 'java',
            '.cpp': 'cpp', '.c': 'cpp', '.h': 'cpp', '.hpp': 'cpp',
            '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php',
            '.sh': 'bash', '.bat': 'bash', '.ps1': 'powershell',
            '.md': 'markdown', '.yaml': 'yaml', '.yml': 'yaml', '.xml': 'xml',
        }
        return lang_map.get(ext, 'text')

    def _parse_github_url(self, url: str):
        """Parse GitHub URL to extract owner/repo/branch."""
        # https://github.com/owner/repo
        # https://github.com/owner/repo/tree/branch
        # https://github.com/owner/repo/blob/branch/path/to/file
        try:
            parts = url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                self.github_repo = (parts[0], parts[1])
                if len(parts) > 3 and parts[2] in ('tree', 'blob'):
                    self.github_branch = parts[3]
        except:
            pass

    def _create_ui(self):
        """Create the editor UI."""
        # Main container with PanedWindow for resizable split
        self.paned = tk.PanedWindow(
            self.window, orient='horizontal',
            bg=self.bg_color, sashwidth=4, sashrelief='flat'
        )
        self.paned.pack(fill='both', expand=True, padx=5, pady=5)

        # === LEFT PANEL - File Tree ===
        left_panel = tk.Frame(self.paned, bg=self.tree_bg, width=280)
        self.paned.add(left_panel, minsize=200)

        self._create_file_tree(left_panel)

        # === RIGHT PANEL - Editor ===
        right_panel = tk.Frame(self.paned, bg=self.bg_color)
        self.paned.add(right_panel, minsize=500)

        # Top toolbar
        self._create_toolbar(right_panel)

        # AI command bar
        self._create_ai_bar(right_panel)

        # Editor area
        self._create_editor(right_panel)

        # Diff preview panel (hidden)
        self._create_diff_panel(right_panel)

        # Status bar
        self._create_status_bar(right_panel)

    def _create_file_tree(self, parent):
        """Create the file tree browser panel."""
        # Header
        header = tk.Frame(parent, bg='#16213e', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header, text="📂 FILES",
            font=('Consolas', 10, 'bold'),
            fg=self.accent2_color, bg='#16213e'
        ).pack(side='left', padx=10, pady=8)

        # Buttons
        btn_frame = tk.Frame(header, bg='#16213e')
        btn_frame.pack(side='right', padx=5)

        # Refresh button
        refresh_btn = tk.Button(
            btn_frame, text="⟳", font=('Consolas', 12),
            fg='#888888', bg='#16213e', bd=0,
            activebackground='#2a2a4a', cursor='hand2',
            command=self._refresh_tree
        )
        refresh_btn.pack(side='left', padx=2)

        # Open folder button
        open_btn = tk.Button(
            btn_frame, text="📁", font=('Consolas', 12),
            fg='#888888', bg='#16213e', bd=0,
            activebackground='#2a2a4a', cursor='hand2',
            command=self._open_folder
        )
        open_btn.pack(side='left', padx=2)

        # GitHub button
        github_btn = tk.Button(
            btn_frame, text="🐙", font=('Consolas', 12),
            fg='#888888', bg='#16213e', bd=0,
            activebackground='#2a2a4a', cursor='hand2',
            command=self._open_github_repo
        )
        github_btn.pack(side='left', padx=2)

        # Tree view with scrollbar
        tree_frame = tk.Frame(parent, bg=self.tree_bg)
        tree_frame.pack(fill='both', expand=True)

        # Scrollbars
        y_scroll = tk.Scrollbar(tree_frame)
        y_scroll.pack(side='right', fill='y')

        x_scroll = tk.Scrollbar(tree_frame, orient='horizontal')
        x_scroll.pack(side='bottom', fill='x')

        # Style the treeview
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Dark.Treeview",
            background=self.tree_bg,
            foreground=self.fg_color,
            fieldbackground=self.tree_bg,
            font=('Consolas', 10)
        )
        style.configure(
            "Dark.Treeview.Heading",
            background='#16213e',
            foreground=self.fg_color,
            font=('Consolas', 10, 'bold')
        )
        style.map("Dark.Treeview", background=[('selected', self.tree_select)])

        # Treeview
        self.file_tree = ttk.Treeview(
            tree_frame, style="Dark.Treeview",
            show='tree', selectmode='browse',
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        self.file_tree.pack(fill='both', expand=True)

        y_scroll.config(command=self.file_tree.yview)
        x_scroll.config(command=self.file_tree.xview)

        # Bind events
        self.file_tree.bind('<Double-1>', self._on_file_select)
        self.file_tree.bind('<Return>', self._on_file_select)

    def _create_toolbar(self, parent):
        """Create the top toolbar."""
        toolbar = tk.Frame(parent, bg='#16213e', height=45)
        toolbar.pack(fill='x', pady=(0, 5))
        toolbar.pack_propagate(False)

        # Left side - File info
        left_frame = tk.Frame(toolbar, bg='#16213e')
        left_frame.pack(side='left', fill='y', padx=10)

        # File name label
        file_name = Path(self.file_path).name if self.file_path else "No file open"
        self.file_label = tk.Label(
            left_frame, text=file_name,
            font=('Consolas', 11, 'bold'),
            fg=self.accent_color, bg='#16213e'
        )
        self.file_label.pack(side='left', pady=10)

        # Modified indicator
        self.modified_label = tk.Label(
            left_frame, text="",
            font=('Consolas', 10),
            fg='#ffaa00', bg='#16213e'
        )
        self.modified_label.pack(side='left', padx=5, pady=10)

        # Language label
        self.lang_label = tk.Label(
            left_frame, text=f"[{self.language.upper()}]",
            font=('Consolas', 9),
            fg='#888888', bg='#16213e'
        )
        self.lang_label.pack(side='left', padx=10, pady=10)

        # Right side - Buttons
        btn_frame = tk.Frame(toolbar, bg='#16213e')
        btn_frame.pack(side='right', fill='y', padx=10)

        btn_style = {
            'font': ('Consolas', 9),
            'fg': 'white',
            'relief': 'flat',
            'padx': 10, 'pady': 3,
            'cursor': 'hand2'
        }

        # Copy
        tk.Button(
            btn_frame, text="📋 Copy", bg='#4a4a6a',
            activebackground='#5a5a7a', command=self._copy_all, **btn_style
        ).pack(side='left', padx=2, pady=8)

        # Undo
        tk.Button(
            btn_frame, text="↩ Undo", bg='#4a4a6a',
            activebackground='#5a5a7a', command=self._undo, **btn_style
        ).pack(side='left', padx=2, pady=8)

        # Redo
        tk.Button(
            btn_frame, text="↪ Redo", bg='#4a4a6a',
            activebackground='#5a5a7a', command=self._redo, **btn_style
        ).pack(side='left', padx=2, pady=8)

        # Separator
        tk.Frame(btn_frame, bg='#333333', width=2).pack(side='left', fill='y', padx=5, pady=8)

        # Save
        tk.Button(
            btn_frame, text="💾 Save", bg='#22c55e',
            activebackground='#16a34a', command=self._save, **btn_style
        ).pack(side='left', padx=2, pady=8)

        # Save As
        tk.Button(
            btn_frame, text="📁 Save As", bg='#3b82f6',
            activebackground='#2563eb', command=self._save_as, **btn_style
        ).pack(side='left', padx=2, pady=8)

        # Push
        tk.Button(
            btn_frame, text="🚀 Push", bg='#8b5cf6',
            activebackground='#7c3aed', command=self._push_to_github, **btn_style
        ).pack(side='left', padx=2, pady=8)

    def _create_ai_bar(self, parent):
        """Create the AI command bar."""
        ai_frame = tk.Frame(parent, bg='#111111', height=50)
        ai_frame.pack(fill='x', pady=(0, 5))
        ai_frame.pack_propagate(False)

        tk.Label(
            ai_frame, text="🤖 Ask CORA to edit:",
            font=('Consolas', 10, 'bold'),
            fg=self.accent_color, bg='#111111'
        ).pack(side='left', padx=10, pady=10)

        self.ai_entry = tk.Entry(
            ai_frame, font=('Consolas', 11),
            fg=self.fg_color, bg='#1a1a1a',
            insertbackground=self.accent_color,
            relief='flat', width=50
        )
        self.ai_entry.pack(side='left', fill='x', expand=True, padx=5, pady=10, ipady=3)
        self.ai_entry.insert(0, "e.g., 'add error handling' or 'rename variable x to count'")
        self.ai_entry.bind('<FocusIn>', self._on_ai_focus)
        self.ai_entry.bind('<FocusOut>', self._on_ai_unfocus)
        self.ai_entry.bind('<Return>', self._on_ai_submit)

        self.apply_btn = tk.Button(
            ai_frame, text="Apply Changes",
            font=('Consolas', 10, 'bold'),
            fg='black', bg=self.accent_color,
            activebackground='#ff6b6b',
            relief='flat', padx=15,
            command=self._on_ai_submit
        )
        self.apply_btn.pack(side='left', padx=10, pady=10)

        self.ai_status = tk.Label(
            ai_frame, text="",
            font=('Consolas', 9),
            fg='#888888', bg='#111111'
        )
        self.ai_status.pack(side='left', padx=5)

    def _create_editor(self, parent):
        """Create the main code editor."""
        editor_frame = tk.Frame(parent, bg=self.editor_bg)
        editor_frame.pack(fill='both', expand=True)

        # Line numbers
        self.line_numbers = tk.Text(
            editor_frame, width=5,
            font=('Consolas', 11),
            fg=self.line_num_fg, bg=self.line_num_bg,
            relief='flat', state='disabled',
            padx=5, pady=10, cursor='arrow'
        )
        self.line_numbers.pack(side='left', fill='y')

        # Editor container
        editor_container = tk.Frame(editor_frame, bg=self.editor_bg)
        editor_container.pack(side='left', fill='both', expand=True)

        # Scrollbars
        scrollbar = tk.Scrollbar(editor_container)
        scrollbar.pack(side='right', fill='y')

        h_scrollbar = tk.Scrollbar(editor_container, orient='horizontal')
        h_scrollbar.pack(side='bottom', fill='x')

        # Code text
        self.code_text = tk.Text(
            editor_container, font=('Consolas', 11),
            fg=self.fg_color, bg=self.editor_bg,
            insertbackground=self.accent_color,
            selectbackground='#44475a',
            selectforeground=self.fg_color,
            relief='flat', wrap='none',
            padx=10, pady=10,
            undo=True, maxundo=-1,
            yscrollcommand=self._sync_scroll,
            xscrollcommand=h_scrollbar.set
        )
        self.code_text.pack(fill='both', expand=True)

        scrollbar.config(command=self._scroll_both)
        h_scrollbar.config(command=self.code_text.xview)

        # Syntax tags
        for tag, color in self.SYNTAX_COLORS.items():
            self.code_text.tag_configure(tag, foreground=color)

        # Bindings
        self.code_text.bind('<KeyRelease>', self._on_key_release)
        self.code_text.bind('<Control-s>', lambda e: self._save())
        self.code_text.bind('<Control-z>', lambda e: self._undo())
        self.code_text.bind('<Control-y>', lambda e: self._redo())

    def _create_diff_panel(self, parent):
        """Create diff preview panel."""
        self.diff_frame = tk.Frame(parent, bg='#111111')

        diff_header = tk.Frame(self.diff_frame, bg='#16213e')
        diff_header.pack(fill='x')

        tk.Label(
            diff_header, text="📝 Proposed Changes - Review before accepting",
            font=('Consolas', 11, 'bold'),
            fg=self.accent2_color, bg='#16213e'
        ).pack(side='left', padx=10, pady=8)

        btn_frame = tk.Frame(diff_header, bg='#16213e')
        btn_frame.pack(side='right', padx=10, pady=5)

        tk.Button(
            btn_frame, text="✓ Accept",
            font=('Consolas', 10, 'bold'),
            fg='white', bg='#22c55e',
            activebackground='#16a34a',
            relief='flat', padx=15,
            command=self._accept_changes
        ).pack(side='left', padx=5)

        tk.Button(
            btn_frame, text="✗ Reject",
            font=('Consolas', 10, 'bold'),
            fg='white', bg='#ef4444',
            activebackground='#dc2626',
            relief='flat', padx=15,
            command=self._reject_changes
        ).pack(side='left', padx=5)

        self.diff_text = tk.Text(
            self.diff_frame, font=('Consolas', 10),
            fg=self.fg_color, bg='#0a0a0a',
            relief='flat', height=10,
            padx=10, pady=10, state='disabled'
        )
        self.diff_text.pack(fill='both', expand=True, padx=5, pady=5)

        self.diff_text.tag_configure('added', foreground='#22c55e', background='#0a2a0a')
        self.diff_text.tag_configure('removed', foreground='#ef4444', background='#2a0a0a')
        self.diff_text.tag_configure('context', foreground='#888888')
        self.diff_text.tag_configure('header', foreground=self.accent2_color)

    def _create_status_bar(self, parent):
        """Create status bar."""
        status_frame = tk.Frame(parent, bg='#16213e', height=30)
        status_frame.pack(fill='x', pady=(5, 0))
        status_frame.pack_propagate(False)

        self.cursor_label = tk.Label(
            status_frame, text="Ln 1, Col 1",
            font=('Consolas', 9),
            fg='#888888', bg='#16213e'
        )
        self.cursor_label.pack(side='left', padx=10, pady=5)

        path_text = self.file_path or self.github_url or "No file"
        if len(path_text) > 50:
            path_text = "..." + path_text[-47:]
        self.path_label = tk.Label(
            status_frame, text=path_text,
            font=('Consolas', 9),
            fg='#666666', bg='#16213e'
        )
        self.path_label.pack(side='left', padx=20, pady=5)

        self.stats_label = tk.Label(
            status_frame, text="",
            font=('Consolas', 9),
            fg='#888888', bg='#16213e'
        )
        self.stats_label.pack(side='right', padx=10, pady=5)

        self._update_stats()

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
                from tools.git_ops import get_git

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
        """Handle close."""
        global _active_editor
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Close anyway?"):
                return
        _active_editor = None
        if self.window:
            self.window.destroy()

    def _show_status(self, message: str):
        """Show status message."""
        self.ai_status.config(text=message, fg='#888888')
        if hasattr(self, '_status_after_id'):
            self.window.after_cancel(self._status_after_id)
        self._status_after_id = self.window.after(3000, lambda: self.ai_status.config(text=""))

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


# ==================== CONVENIENCE FUNCTIONS ====================

def open_code_editor(
    file_path: str = None,
    folder_path: str = None,
    content: str = "",
    language: str = None,
    github_url: str = None,
    title: str = "Code Editor"
) -> CodeEditorModal:
    """Open the code editor."""
    editor = CodeEditorModal()
    editor.open(
        file_path=file_path,
        folder_path=folder_path,
        content=content,
        language=language,
        github_url=github_url,
        title=title
    )
    return editor


def open_folder(folder_path: str) -> CodeEditorModal:
    """Open a folder in the code editor."""
    return open_code_editor(folder_path=folder_path)


def open_github_repo(url: str) -> CodeEditorModal:
    """Open a GitHub repository in the code editor."""
    return open_code_editor(github_url=url)


# Test
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    # Test with current directory
    editor = open_code_editor(folder_path=os.getcwd())

    root.mainloop()
