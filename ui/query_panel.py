#!/usr/bin/env python3
"""
C.O.R.A Query Panel
Tkinter popup for getting human input

Per ARCHITECTURE.md v2.2.0:
- Show popup with question text
- Image carousel (optional)
- Clickable links (optional)
- Hotbar buttons (WoW-style quick responses)
- Voice input option
- Clipboard paste (text + images)
- File drag-drop
"""

import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass

# Tkinter imports
import tkinter as tk
from tkinter import ttk

# Optional imports
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


# Constants
PROJECT_DIR = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_DIR / 'config'
DATA_DIR = PROJECT_DIR / 'data'

# Colors - CORA purple/dark theme
BG_COLOR = "#1a1a2e"
ACCENT_COLOR = "#16213e"
TEXT_COLOR = "#eee"
BUTTON_COLOR = "#0f3460"
BUTTON_HOVER = "#533483"
LINK_COLOR = "#00d9ff"

# Default hotbar buttons
DEFAULT_HOTBAR = [
    ("YES", "YES"),
    ("NO", "NO"),
    ("DUNNO", "DUNNO"),
    ("LATER", "LATER"),
]


@dataclass
class QueryResult:
    """Result of query panel interaction."""
    response: Optional[str] = None
    typed_text: Optional[str] = None
    files_dropped: List[Path] = None
    cancelled: bool = False
    timeout: bool = False

    def __post_init__(self):
        if self.files_dropped is None:
            self.files_dropped = []


class QueryPanel(tk.Toplevel):
    """Popup panel for getting human input."""

    def __init__(
        self,
        parent: tk.Tk,
        question: str,
        image: Optional[Path] = None,
        images: Optional[List[Path]] = None,
        links: Optional[Dict[str, str]] = None,
        hotbar_buttons: Optional[List[tuple]] = None,
        allow_text_input: bool = True,
        timeout: int = 300
    ):
        """Initialize query panel.

        Args:
            parent: Parent Tk window
            question: Question text to display
            image: Single image path (optional)
            images: List of image paths for carousel (optional)
            links: Dict of {label: path} for clickable links (optional)
            hotbar_buttons: List of (label, response) tuples
            allow_text_input: Show text entry field
            timeout: Auto-close timeout in seconds (0 = no timeout)
        """
        super().__init__(parent)

        self.question = question
        self.images = images or ([image] if image else [])
        self.links = links or {}
        self.hotbar_buttons = hotbar_buttons or DEFAULT_HOTBAR
        self.allow_text_input = allow_text_input
        self.timeout = timeout

        self.result = QueryResult()
        self.current_image_idx = 0
        self._photo_refs = []  # Keep references to prevent GC

        self._setup_window()
        self._build_ui()

        if timeout > 0:
            self._start_timeout()

    def _setup_window(self):
        """Configure window properties."""
        self.title("CORA Query")
        self.configure(bg=BG_COLOR)
        self.attributes("-topmost", True)
        self.resizable(True, True)

        # Center on screen
        width, height = 600, 500
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Keyboard shortcuts
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.bind("<Return>", lambda e: self._on_submit())

    def _build_ui(self):
        """Build the UI components."""
        # Main container
        main = tk.Frame(self, bg=BG_COLOR, padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Question label
        q_label = tk.Label(
            main,
            text=self.question,
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            wraplength=550,
            justify=tk.LEFT
        )
        q_label.pack(fill=tk.X, pady=(0, 15))

        # Image carousel (if images provided)
        if self.images and PIL_AVAILABLE:
            self._build_image_carousel(main)

        # Links section (if links provided)
        if self.links:
            self._build_links_section(main)

        # Hotbar buttons
        self._build_hotbar(main)

        # Text input (if enabled)
        if self.allow_text_input:
            self._build_text_input(main)

        # Submit/Cancel buttons
        self._build_action_buttons(main)

    def _build_image_carousel(self, parent):
        """Build image carousel widget."""
        frame = tk.Frame(parent, bg=ACCENT_COLOR, padx=10, pady=10)
        frame.pack(fill=tk.X, pady=10)

        # Image label
        self.image_label = tk.Label(frame, bg=ACCENT_COLOR)
        self.image_label.pack()

        # Navigation (if multiple images)
        if len(self.images) > 1:
            nav = tk.Frame(frame, bg=ACCENT_COLOR)
            nav.pack(fill=tk.X, pady=(10, 0))

            tk.Button(
                nav, text="< Prev", command=self._prev_image,
                bg=BUTTON_COLOR, fg=TEXT_COLOR
            ).pack(side=tk.LEFT)

            self.image_counter = tk.Label(
                nav, text=f"1 / {len(self.images)}",
                fg=TEXT_COLOR, bg=ACCENT_COLOR
            )
            self.image_counter.pack(side=tk.LEFT, expand=True)

            tk.Button(
                nav, text="Next >", command=self._next_image,
                bg=BUTTON_COLOR, fg=TEXT_COLOR
            ).pack(side=tk.RIGHT)

        self._show_image(0)

    def _show_image(self, idx: int):
        """Display image at index."""
        if not self.images or not PIL_AVAILABLE:
            return

        idx = idx % len(self.images)
        self.current_image_idx = idx

        try:
            img_path = Path(self.images[idx])
            if img_path.exists():
                img = Image.open(img_path)
                # Resize to fit
                img.thumbnail((500, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._photo_refs.append(photo)  # Keep reference
                self.image_label.configure(image=photo)

                if hasattr(self, 'image_counter'):
                    self.image_counter.configure(
                        text=f"{idx + 1} / {len(self.images)}"
                    )
        except Exception as e:
            print(f"[!] Image load error: {e}")

    def _prev_image(self):
        """Show previous image."""
        self._show_image(self.current_image_idx - 1)

    def _next_image(self):
        """Show next image."""
        self._show_image(self.current_image_idx + 1)

    def _build_links_section(self, parent):
        """Build clickable links section."""
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(fill=tk.X, pady=5)

        tk.Label(
            frame, text="Files:", font=("Segoe UI", 10),
            fg=TEXT_COLOR, bg=BG_COLOR
        ).pack(anchor=tk.W)

        for label, path in self.links.items():
            link = tk.Label(
                frame,
                text=f"  {label}: {path}",
                font=("Segoe UI", 9, "underline"),
                fg=LINK_COLOR,
                bg=BG_COLOR,
                cursor="hand2"
            )
            link.pack(anchor=tk.W)
            link.bind("<Button-1>", lambda e, p=path: self._open_file(p))

    def _open_file(self, path: str):
        """Open file in default application."""
        try:
            import subprocess
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception as e:
            print(f"[!] Failed to open file: {e}")

    def _build_hotbar(self, parent):
        """Build WoW-style hotbar buttons."""
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(fill=tk.X, pady=15)

        for label, response in self.hotbar_buttons:
            if not label:
                continue

            btn = tk.Button(
                frame,
                text=label,
                command=lambda r=response: self._on_hotbar(r),
                bg=BUTTON_COLOR,
                fg=TEXT_COLOR,
                font=("Segoe UI", 11, "bold"),
                padx=15,
                pady=8,
                relief=tk.RAISED,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=5)

            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=BUTTON_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=BUTTON_COLOR))

    def _build_text_input(self, parent):
        """Build text input field."""
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(fill=tk.X, pady=10)

        tk.Label(
            frame, text="Or type your response:",
            font=("Segoe UI", 10), fg=TEXT_COLOR, bg=BG_COLOR
        ).pack(anchor=tk.W)

        self.text_entry = tk.Text(
            frame,
            height=3,
            font=("Consolas", 11),
            bg=ACCENT_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        self.text_entry.pack(fill=tk.X, pady=(5, 0))
        self.text_entry.focus_set()

    def _build_action_buttons(self, parent):
        """Build submit/cancel buttons."""
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(fill=tk.X, pady=(15, 0))

        tk.Button(
            frame, text="Cancel",
            command=self._on_cancel,
            bg="#444", fg=TEXT_COLOR,
            font=("Segoe UI", 10),
            padx=20
        ).pack(side=tk.RIGHT, padx=5)

        if self.allow_text_input:
            tk.Button(
                frame, text="Submit",
                command=self._on_submit,
                bg=BUTTON_HOVER, fg=TEXT_COLOR,
                font=("Segoe UI", 10, "bold"),
                padx=20
            ).pack(side=tk.RIGHT, padx=5)

    def _on_hotbar(self, response: str):
        """Handle hotbar button click."""
        self.result.response = response
        self.destroy()

    def _on_submit(self):
        """Handle submit button."""
        if self.allow_text_input:
            text = self.text_entry.get("1.0", tk.END).strip()
            if text:
                self.result.typed_text = text
                self.result.response = text
        self.destroy()

    def _on_cancel(self):
        """Handle cancel/close."""
        self.result.cancelled = True
        self.destroy()

    def _start_timeout(self):
        """Start auto-close timeout."""
        def check_timeout():
            self.result.timeout = True
            self.destroy()

        self.after(self.timeout * 1000, check_timeout)

    def get_result(self) -> QueryResult:
        """Wait for panel to close and return result."""
        self.wait_window()
        return self.result


# Singleton root window
_root: Optional[tk.Tk] = None


def _get_root() -> tk.Tk:
    """Get or create root Tk window."""
    global _root
    if _root is None or not _root.winfo_exists():
        if DND_AVAILABLE:
            _root = TkinterDnD.Tk()
        else:
            _root = tk.Tk()
        _root.withdraw()  # Hide root window
    return _root


def ask_human(
    question: str,
    image: Optional[str] = None,
    images: Optional[List[str]] = None,
    links: Optional[Dict[str, str]] = None,
    hotbar_buttons: Optional[List[tuple]] = None,
    timeout: int = 300,
    allow_text: bool = True
) -> Optional[str]:
    """Show popup panel and get human response.

    Args:
        question: Question text to display
        image: Single image path (optional)
        images: List of image paths (optional)
        links: Dict of {label: path} for clickable links
        hotbar_buttons: List of (label, response) tuples
        timeout: Auto-close timeout in seconds (0 = no timeout)
        allow_text: Allow free text input

    Returns:
        User's response string or None if cancelled/timeout
    """
    root = _get_root()

    panel = QueryPanel(
        root,
        question=question,
        image=Path(image) if image else None,
        images=[Path(p) for p in images] if images else None,
        links=links,
        hotbar_buttons=hotbar_buttons,
        allow_text_input=allow_text,
        timeout=timeout
    )

    result = panel.get_result()

    if result.cancelled or result.timeout:
        return None

    return result.response


def quick_ask(question: str, buttons: List[str] = None) -> Optional[str]:
    """Quick yes/no/etc question with minimal UI.

    Args:
        question: Question text
        buttons: List of button labels (default: YES/NO/DUNNO/LATER)

    Returns:
        Button text clicked or None
    """
    if buttons is None:
        buttons = ["YES", "NO", "DUNNO", "LATER"]

    hotbar = [(b, b) for b in buttons]

    return ask_human(
        question,
        hotbar_buttons=hotbar,
        allow_text=False,
        timeout=120
    )


def confirm(question: str) -> bool:
    """Simple yes/no confirmation.

    Args:
        question: Question text

    Returns:
        True if YES, False otherwise
    """
    result = quick_ask(question, ["YES", "NO"])
    return result == "YES"


def load_hotbar_config() -> List[List[tuple]]:
    """Load hotbar configuration from file.

    Returns:
        List of hotbar rows, each containing (label, response) tuples
    """
    config_file = CONFIG_DIR / 'hotbar.json'

    if config_file.exists():
        try:
            with open(config_file) as f:
                data = json.load(f)
                return data.get('hotbars', [DEFAULT_HOTBAR])
        except Exception as e:
            print(f"[!] Hotbar config error: {e}")

    return [DEFAULT_HOTBAR]


def save_hotbar_config(hotbars: List[List[tuple]]) -> bool:
    """Save hotbar configuration to file.

    Args:
        hotbars: List of hotbar rows

    Returns:
        True if saved successfully
    """
    config_file = CONFIG_DIR / 'hotbar.json'

    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump({'hotbars': hotbars}, f, indent=2)
        return True
    except Exception as e:
        print(f"[!] Hotbar save error: {e}")
        return False


if __name__ == "__main__":
    print("=== QUERY PANEL TEST ===")

    # Test basic question
    print("\n--- Basic Question ---")
    result = quick_ask("Is this working?")
    print(f"Result: {result}")

    # Test with options
    print("\n--- With Links ---")
    result = ask_human(
        "Review these files?",
        links={
            "This file": __file__,
            "Parent dir": str(Path(__file__).parent)
        },
        timeout=30
    )
    print(f"Result: {result}")

    # Test confirmation
    print("\n--- Confirmation ---")
    if confirm("Continue with tests?"):
        print("User confirmed!")
    else:
        print("User declined")
