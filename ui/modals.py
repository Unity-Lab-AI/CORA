#!/usr/bin/env python3
"""
C.O.R.A Modal Windows System

Separate popup windows for tool outputs so user can see both
CORA chat and tool results simultaneously.

Each modal is non-blocking and can be interacted with independently.

Uses centralized window_manager for consistent z-layering.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import threading

# Import centralized window manager
from ui.window_manager import create_modal as wm_create_modal, bring_to_front

# Track all open modals
_open_modals: Dict[str, tk.Toplevel] = {}

# Reference to main CORA window for positioning
_main_window: Optional[tk.Tk] = None


def set_main_window(window: tk.Tk):
    """Set reference to main CORA window for modal positioning."""
    global _main_window
    _main_window = window


def _create_base_modal(
    title: str,
    width: int = 800,
    height: int = 600,
    resizable: bool = True,
    on_close: Optional[Callable] = None
) -> tk.Toplevel:
    """Create a base modal window with CORA styling using window manager."""

    # Use centralized window manager for proper z-layering
    modal = wm_create_modal(
        title=f"CORA - {title}",
        width=width,
        height=height,
        bg='#1a1a2e',
        parent=_main_window,
        on_close=on_close
    )

    # Track modal
    _open_modals[str(modal.winfo_id())] = modal

    return modal


def _add_header(parent: tk.Widget, title: str, subtitle: str = "") -> tk.Frame:
    """Add a styled header to a modal."""
    header = tk.Frame(parent, bg='#16213e', height=60)
    header.pack(fill='x', padx=2, pady=2)
    header.pack_propagate(False)

    title_label = tk.Label(
        header,
        text=title,
        font=('Consolas', 14, 'bold'),
        fg='#e94560',
        bg='#16213e'
    )
    title_label.pack(side='left', padx=15, pady=10)

    if subtitle:
        sub_label = tk.Label(
            header,
            text=subtitle,
            font=('Consolas', 10),
            fg='#888',
            bg='#16213e'
        )
        sub_label.pack(side='left', padx=5, pady=10)

    return header


def _add_close_button(parent: tk.Widget, modal: tk.Toplevel) -> tk.Button:
    """Add a close button to the bottom of a modal."""
    btn_frame = tk.Frame(parent, bg='#1a1a2e')
    btn_frame.pack(fill='x', padx=10, pady=10)

    close_btn = tk.Button(
        btn_frame,
        text="Close",
        font=('Consolas', 10),
        fg='white',
        bg='#e94560',
        activebackground='#ff6b6b',
        activeforeground='white',
        relief='flat',
        padx=20,
        pady=5,
        command=modal.destroy
    )
    close_btn.pack(side='right')

    return close_btn


# ============================================================
# IMAGE MODAL
# ============================================================

def show_image_modal(
    image_path: str,
    title: str = "Generated Image",
    description: str = ""
) -> tk.Toplevel:
    """
    Display an image in a modal window.

    Args:
        image_path: Path to image file
        title: Modal title
        description: Optional description/prompt used

    Returns:
        The modal window
    """
    modal = _create_base_modal(title, width=1300, height=800)

    _add_header(modal, title, description[:50] + "..." if len(description) > 50 else description)

    # Image container
    img_frame = tk.Frame(modal, bg='#0f0f1a')
    img_frame.pack(fill='both', expand=True, padx=10, pady=5)

    try:
        from PIL import Image, ImageTk

        # Load and resize image to fit
        img = Image.open(image_path)

        # Calculate size to fit in window
        max_width = 1260
        max_height = 650

        ratio = min(max_width / img.width, max_height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(img, master=modal)

        img_label = tk.Label(img_frame, image=photo, bg='#0f0f1a')
        img_label.image = photo  # Keep reference
        img_label.pack(expand=True)

        # Info bar
        info_frame = tk.Frame(modal, bg='#16213e')
        info_frame.pack(fill='x', padx=10, pady=5)

        size_label = tk.Label(
            info_frame,
            text=f"Size: {img.width}x{img.height} | Path: {image_path}",
            font=('Consolas', 9),
            fg='#888',
            bg='#16213e'
        )
        size_label.pack(side='left', padx=10, pady=5)

        # Save as button
        def save_as():
            from tkinter import filedialog
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("All", "*.*")]
            )
            if save_path:
                import shutil
                shutil.copy(image_path, save_path)

        save_btn = tk.Button(
            info_frame,
            text="Save As...",
            font=('Consolas', 9),
            fg='white',
            bg='#4a4a6a',
            relief='flat',
            command=save_as
        )
        save_btn.pack(side='right', padx=10, pady=5)

    except Exception as e:
        error_label = tk.Label(
            img_frame,
            text=f"Failed to load image: {e}",
            font=('Consolas', 12),
            fg='#e94560',
            bg='#0f0f1a'
        )
        error_label.pack(expand=True)

    _add_close_button(modal, modal)

    return modal


# ============================================================
# CODE VIEWER MODAL
# ============================================================

def show_code_modal(
    code: str = "",
    file_path: str = "",
    language: str = "python",
    title: str = "Code Viewer"
) -> tk.Toplevel:
    """
    Display code in a syntax-highlighted modal.

    Args:
        code: Code string to display (or empty to load from file_path)
        file_path: Path to code file
        language: Language for syntax highlighting
        title: Modal title

    Returns:
        The modal window
    """
    modal = _create_base_modal(title, width=900, height=700)

    # Determine file info
    if file_path and not code:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            subtitle = file_path
        except Exception as e:
            code = f"# Error loading file: {e}"
            subtitle = "Error"
    else:
        subtitle = language

    _add_header(modal, title, subtitle)

    # Toolbar
    toolbar = tk.Frame(modal, bg='#16213e')
    toolbar.pack(fill='x', padx=10, pady=2)

    line_count = len(code.split('\n'))
    char_count = len(code)

    stats_label = tk.Label(
        toolbar,
        text=f"Lines: {line_count} | Characters: {char_count}",
        font=('Consolas', 9),
        fg='#888',
        bg='#16213e'
    )
    stats_label.pack(side='left', padx=10, pady=5)

    # Copy button
    def copy_code():
        modal.clipboard_clear()
        modal.clipboard_append(code)
        copy_btn.configure(text="Copied!")
        modal.after(1500, lambda: copy_btn.configure(text="Copy"))

    copy_btn = tk.Button(
        toolbar,
        text="Copy",
        font=('Consolas', 9),
        fg='white',
        bg='#4a4a6a',
        relief='flat',
        command=copy_code
    )
    copy_btn.pack(side='right', padx=5, pady=5)

    # Code display with line numbers
    code_frame = tk.Frame(modal, bg='#0f0f1a')
    code_frame.pack(fill='both', expand=True, padx=10, pady=5)

    # Line numbers
    line_numbers = tk.Text(
        code_frame,
        width=5,
        font=('Consolas', 11),
        fg='#555',
        bg='#0f0f1a',
        relief='flat',
        state='disabled',
        padx=5
    )
    line_numbers.pack(side='left', fill='y')

    # Code text
    code_text = scrolledtext.ScrolledText(
        code_frame,
        font=('Consolas', 11),
        fg='#e0e0e0',
        bg='#0f0f1a',
        insertbackground='#e94560',
        relief='flat',
        wrap='none',
        padx=10,
        pady=10
    )
    code_text.pack(side='left', fill='both', expand=True)

    # Insert code
    code_text.insert('1.0', code)
    code_text.configure(state='disabled')

    # Add line numbers
    line_numbers.configure(state='normal')
    for i in range(1, line_count + 1):
        line_numbers.insert('end', f"{i}\n")
    line_numbers.configure(state='disabled')

    # Sync scrolling
    def sync_scroll(*args):
        line_numbers.yview_moveto(args[0])

    code_text.configure(yscrollcommand=lambda *args: (code_text.yview(*args), sync_scroll(args[0]) if args else None))

    _add_close_button(modal, modal)

    return modal


# ============================================================
# WEB RESULTS MODAL
# ============================================================

def show_web_modal(
    content: str,
    url: str = "",
    title: str = "Web Results"
) -> tk.Toplevel:
    """
    Display web search/fetch results in a modal.

    Args:
        content: The web content or search results
        url: Source URL
        title: Modal title

    Returns:
        The modal window
    """
    modal = _create_base_modal(title, width=900, height=700)

    _add_header(modal, title, url[:60] + "..." if len(url) > 60 else url)

    # URL bar
    if url:
        url_frame = tk.Frame(modal, bg='#16213e')
        url_frame.pack(fill='x', padx=10, pady=2)

        url_entry = tk.Entry(
            url_frame,
            font=('Consolas', 10),
            fg='#888',
            bg='#0f0f1a',
            relief='flat',
            readonlybackground='#0f0f1a'
        )
        url_entry.insert(0, url)
        url_entry.configure(state='readonly')
        url_entry.pack(fill='x', padx=10, pady=5)

    # Content
    content_frame = tk.Frame(modal, bg='#0f0f1a')
    content_frame.pack(fill='both', expand=True, padx=10, pady=5)

    content_text = scrolledtext.ScrolledText(
        content_frame,
        font=('Consolas', 11),
        fg='#e0e0e0',
        bg='#0f0f1a',
        relief='flat',
        wrap='word',
        padx=15,
        pady=15
    )
    content_text.pack(fill='both', expand=True)
    content_text.insert('1.0', content)
    content_text.configure(state='disabled')

    _add_close_button(modal, modal)

    return modal


# ============================================================
# SYSTEM STATS MODAL
# ============================================================

def show_stats_modal(title: str = "System Stats") -> tk.Toplevel:
    """
    Display live system stats in a modal.

    Returns:
        The modal window
    """
    modal = _create_base_modal(title, width=500, height=400)

    _add_header(modal, title, "Live hardware monitoring")

    # Stats container
    stats_frame = tk.Frame(modal, bg='#0f0f1a')
    stats_frame.pack(fill='both', expand=True, padx=10, pady=5)

    # Labels for each stat
    labels = {}
    stats = ['CPU', 'Memory', 'Disk', 'GPU', 'Network']

    for i, stat in enumerate(stats):
        row = tk.Frame(stats_frame, bg='#0f0f1a')
        row.pack(fill='x', padx=20, pady=10)

        name_label = tk.Label(
            row,
            text=f"{stat}:",
            font=('Consolas', 12, 'bold'),
            fg='#e94560',
            bg='#0f0f1a',
            width=10,
            anchor='w'
        )
        name_label.pack(side='left')

        value_label = tk.Label(
            row,
            text="Loading...",
            font=('Consolas', 12),
            fg='#e0e0e0',
            bg='#0f0f1a',
            anchor='w'
        )
        value_label.pack(side='left', fill='x', expand=True)

        labels[stat] = value_label

    # Update function
    def update_stats():
        if not modal.winfo_exists():
            return

        try:
            import psutil

            # CPU
            cpu = psutil.cpu_percent(interval=0.1)
            labels['CPU'].configure(text=f"{cpu:.1f}%")

            # Memory
            mem = psutil.virtual_memory()
            labels['Memory'].configure(text=f"{mem.percent:.1f}% ({mem.used // (1024**3):.1f} GB used)")

            # Disk
            disk = psutil.disk_usage('/')
            labels['Disk'].configure(text=f"{disk.percent:.1f}% ({disk.free // (1024**3):.1f} GB free)")

            # GPU
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    labels['GPU'].configure(text=f"{gpu.load*100:.1f}% | {gpu.memoryUsed:.0f}/{gpu.memoryTotal:.0f} MB")
                else:
                    labels['GPU'].configure(text="Not detected")
            except:
                labels['GPU'].configure(text="Not available")

            # Network
            net = psutil.net_io_counters()
            labels['Network'].configure(text=f"Sent: {net.bytes_sent // (1024**2):.1f} MB | Recv: {net.bytes_recv // (1024**2):.1f} MB")

        except Exception as e:
            pass

        # Schedule next update
        if modal.winfo_exists():
            modal.after(1000, update_stats)

    # Start updates
    modal.after(100, update_stats)

    _add_close_button(modal, modal)

    return modal


# ============================================================
# FILE BROWSER MODAL
# ============================================================

def show_file_modal(
    file_path: str,
    content: str = "",
    title: str = "File Viewer"
) -> tk.Toplevel:
    """
    Display file content in a modal.

    Args:
        file_path: Path to file
        content: File content (or load from path)
        title: Modal title

    Returns:
        The modal window
    """
    path = Path(file_path)

    # Determine file type and use appropriate modal
    if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
        return show_image_modal(file_path, title=f"Image: {path.name}")
    elif path.suffix.lower() in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php', '.html', '.css', '.json', '.yaml', '.yml', '.xml', '.md', '.txt', '.sh', '.bat', '.ps1']:
        return show_code_modal(file_path=file_path, title=f"File: {path.name}")
    else:
        # Generic file viewer
        modal = _create_base_modal(title, width=800, height=600)
        _add_header(modal, title, str(path))

        if not content:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = f"Error reading file: {e}"

        content_text = scrolledtext.ScrolledText(
            modal,
            font=('Consolas', 11),
            fg='#e0e0e0',
            bg='#0f0f1a',
            relief='flat',
            wrap='word',
            padx=15,
            pady=15
        )
        content_text.pack(fill='both', expand=True, padx=10, pady=5)
        content_text.insert('1.0', content)
        content_text.configure(state='disabled')

        _add_close_button(modal, modal)

        return modal


# ============================================================
# TERMINAL/OUTPUT MODAL
# ============================================================

def show_terminal_modal(
    output: str = "",
    command: str = "",
    title: str = "Terminal Output"
) -> tk.Toplevel:
    """
    Display terminal/command output in a modal.

    Args:
        output: Command output
        command: The command that was run
        title: Modal title

    Returns:
        The modal window
    """
    modal = _create_base_modal(title, width=900, height=600)

    _add_header(modal, title, "")

    # Command bar
    if command:
        cmd_frame = tk.Frame(modal, bg='#16213e')
        cmd_frame.pack(fill='x', padx=10, pady=2)

        cmd_label = tk.Label(
            cmd_frame,
            text=f"$ {command}",
            font=('Consolas', 10),
            fg='#4ade80',
            bg='#16213e',
            anchor='w'
        )
        cmd_label.pack(fill='x', padx=10, pady=5)

    # Output
    output_text = scrolledtext.ScrolledText(
        modal,
        font=('Consolas', 10),
        fg='#e0e0e0',
        bg='#0a0a0a',
        insertbackground='#4ade80',
        relief='flat',
        padx=15,
        pady=15
    )
    output_text.pack(fill='both', expand=True, padx=10, pady=5)
    output_text.insert('1.0', output)
    output_text.configure(state='disabled')

    _add_close_button(modal, modal)

    return modal


# ============================================================
# GENERIC MESSAGE MODAL
# ============================================================

def show_message_modal(
    message: str,
    title: str = "CORA",
    message_type: str = "info"  # info, warning, error, success
) -> tk.Toplevel:
    """
    Display a simple message modal.

    Args:
        message: Message to display
        title: Modal title
        message_type: Type for styling (info, warning, error, success)

    Returns:
        The modal window
    """
    modal = _create_base_modal(title, width=500, height=300, resizable=False)

    # Color based on type
    colors = {
        'info': '#3b82f6',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'success': '#22c55e'
    }
    color = colors.get(message_type, '#e94560')

    # Icon/type label
    type_label = tk.Label(
        modal,
        text=message_type.upper(),
        font=('Consolas', 12, 'bold'),
        fg=color,
        bg='#1a1a2e'
    )
    type_label.pack(pady=(20, 10))

    # Message
    msg_label = tk.Label(
        modal,
        text=message,
        font=('Consolas', 11),
        fg='#e0e0e0',
        bg='#1a1a2e',
        wraplength=450,
        justify='center'
    )
    msg_label.pack(expand=True, padx=20, pady=10)

    _add_close_button(modal, modal)

    return modal


# ============================================================
# HELPER TO SHOW MODAL IN THREAD-SAFE WAY
# ============================================================

def show_modal_threadsafe(modal_func: Callable, *args, **kwargs):
    """
    Show a modal in a thread-safe way (for calling from background threads).

    Args:
        modal_func: The modal function to call (e.g., show_image_modal)
        *args, **kwargs: Arguments to pass to the modal function
    """
    if _main_window:
        _main_window.after(0, lambda: modal_func(*args, **kwargs))
    else:
        # No main window, try to create modal directly
        modal_func(*args, **kwargs)


def close_all_modals():
    """Close all open modals."""
    for modal_id, modal in list(_open_modals.items()):
        try:
            modal.destroy()
        except:
            pass
    _open_modals.clear()
