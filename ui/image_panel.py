#!/usr/bin/env python3
"""
C.O.R.A Image Panel
Display screenshots and images in UI

Per ARCHITECTURE.md v2.2.0:
- Display screenshots in UI
- Support image carousel
- Thumbnail previews
- Fullscreen popup
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass

import tkinter as tk
from tkinter import ttk

# Optional imports
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Constants
PROJECT_DIR = Path(__file__).parent.parent
SCREENSHOT_DIR = PROJECT_DIR / 'data' / 'screenshots'

# Colors
BG_COLOR = "#1a1a2e"
ACCENT_COLOR = "#16213e"
TEXT_COLOR = "#eee"
BUTTON_COLOR = "#0f3460"


@dataclass
class ImageInfo:
    """Information about an image."""
    path: Path
    width: int = 0
    height: int = 0
    size_kb: float = 0


class ImagePanel(tk.Frame):
    """Panel for displaying images."""

    def __init__(
        self,
        parent: tk.Widget,
        images: Optional[List[Path]] = None,
        max_width: int = 500,
        max_height: int = 400,
        show_controls: bool = True,
        on_click: Optional[Callable[[Path], None]] = None
    ):
        """Initialize image panel.

        Args:
            parent: Parent widget
            images: List of image paths
            max_width: Max display width
            max_height: Max display height
            show_controls: Show navigation controls
            on_click: Callback when image clicked
        """
        super().__init__(parent, bg=ACCENT_COLOR)

        self.images = images or []
        self.max_width = max_width
        self.max_height = max_height
        self.show_controls = show_controls
        self.on_click = on_click

        self.current_idx = 0
        self._photo_refs = []  # Prevent garbage collection

        self._build_ui()

        if self.images:
            self.show_image(0)

    def _build_ui(self):
        """Build UI components."""
        # Image container
        self.image_frame = tk.Frame(self, bg=ACCENT_COLOR)
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Image label
        self.image_label = tk.Label(
            self.image_frame,
            bg=ACCENT_COLOR,
            cursor="hand2"
        )
        self.image_label.pack()
        self.image_label.bind("<Button-1>", self._on_image_click)

        # Image info
        self.info_label = tk.Label(
            self.image_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#aaa",
            bg=ACCENT_COLOR
        )
        self.info_label.pack(pady=(5, 0))

        # Navigation controls
        if self.show_controls:
            self._build_controls()

    def _build_controls(self):
        """Build navigation controls."""
        ctrl_frame = tk.Frame(self, bg=ACCENT_COLOR)
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))

        # Prev button
        self.prev_btn = tk.Button(
            ctrl_frame,
            text="< Prev",
            command=self.prev_image,
            bg=BUTTON_COLOR,
            fg=TEXT_COLOR,
            relief=tk.FLAT,
            padx=10
        )
        self.prev_btn.pack(side=tk.LEFT, padx=10)

        # Counter
        self.counter_label = tk.Label(
            ctrl_frame,
            text="0 / 0",
            font=("Segoe UI", 10),
            fg=TEXT_COLOR,
            bg=ACCENT_COLOR
        )
        self.counter_label.pack(side=tk.LEFT, expand=True)

        # Next button
        self.next_btn = tk.Button(
            ctrl_frame,
            text="Next >",
            command=self.next_image,
            bg=BUTTON_COLOR,
            fg=TEXT_COLOR,
            relief=tk.FLAT,
            padx=10
        )
        self.next_btn.pack(side=tk.RIGHT, padx=10)

    def show_image(self, idx: int):
        """Display image at index.

        Args:
            idx: Image index
        """
        if not self.images or not PIL_AVAILABLE:
            return

        idx = idx % len(self.images)
        self.current_idx = idx
        path = self.images[idx]

        try:
            # Load and resize image
            img = Image.open(path)
            original_size = img.size

            # Calculate resize ratio
            ratio = min(
                self.max_width / img.width,
                self.max_height / img.height,
                1.0  # Don't upscale
            )

            if ratio < 1.0:
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            self._photo_refs.append(photo)

            # Update label
            self.image_label.configure(image=photo)

            # Update info
            size_kb = path.stat().st_size / 1024
            info_text = f"{original_size[0]}x{original_size[1]} | {size_kb:.1f} KB"
            self.info_label.configure(text=info_text)

            # Update counter
            if self.show_controls:
                self.counter_label.configure(
                    text=f"{idx + 1} / {len(self.images)}"
                )

        except Exception as e:
            self.info_label.configure(text=f"Error: {e}")

    def prev_image(self):
        """Show previous image."""
        if self.images:
            self.show_image(self.current_idx - 1)

    def next_image(self):
        """Show next image."""
        if self.images:
            self.show_image(self.current_idx + 1)

    def _on_image_click(self, event):
        """Handle image click."""
        if self.on_click and self.images:
            self.on_click(self.images[self.current_idx])
        else:
            # Default: open fullscreen popup
            self.show_fullscreen()

    def show_fullscreen(self):
        """Show current image in fullscreen popup."""
        if not self.images or not PIL_AVAILABLE:
            return

        path = self.images[self.current_idx]
        FullscreenImage(self.winfo_toplevel(), path)

    def set_images(self, images: List[Path]):
        """Set new image list.

        Args:
            images: List of image paths
        """
        self.images = images
        self._photo_refs = []
        self.current_idx = 0

        if images:
            self.show_image(0)

    def add_image(self, path: Path):
        """Add image to list.

        Args:
            path: Image path
        """
        self.images.append(path)

        if len(self.images) == 1:
            self.show_image(0)
        elif self.show_controls:
            self.counter_label.configure(
                text=f"{self.current_idx + 1} / {len(self.images)}"
            )


class FullscreenImage(tk.Toplevel):
    """Fullscreen image popup."""

    def __init__(self, parent: tk.Widget, image_path: Path):
        """Initialize fullscreen image.

        Args:
            parent: Parent widget
            image_path: Path to image
        """
        super().__init__(parent)

        self.image_path = image_path
        self._photo_ref = None

        self._setup_window()
        self._show_image()

    def _setup_window(self):
        """Configure window."""
        self.title("Image Viewer")
        self.configure(bg="black")
        self.attributes("-topmost", True)

        # Get screen size
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        # Close on click or Escape
        self.bind("<Button-1>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

    def _show_image(self):
        """Display the image."""
        if not PIL_AVAILABLE:
            tk.Label(
                self,
                text="PIL not available",
                fg="white",
                bg="black"
            ).pack(expand=True)
            return

        try:
            img = Image.open(self.image_path)

            # Fit to screen
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()

            ratio = min(
                screen_w / img.width,
                screen_h / img.height
            )

            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

            self._photo_ref = ImageTk.PhotoImage(img)

            label = tk.Label(self, image=self._photo_ref, bg="black")
            label.pack(expand=True)
            label.bind("<Button-1>", lambda e: self.destroy())

        except Exception as e:
            tk.Label(
                self,
                text=f"Error: {e}",
                fg="white",
                bg="black"
            ).pack(expand=True)


class ThumbnailGrid(tk.Frame):
    """Grid of image thumbnails."""

    def __init__(
        self,
        parent: tk.Widget,
        images: Optional[List[Path]] = None,
        thumb_size: int = 100,
        columns: int = 4,
        on_select: Optional[Callable[[Path], None]] = None
    ):
        """Initialize thumbnail grid.

        Args:
            parent: Parent widget
            images: List of image paths
            thumb_size: Thumbnail size in pixels
            columns: Number of columns
            on_select: Callback when thumbnail selected
        """
        super().__init__(parent, bg=BG_COLOR)

        self.images = images or []
        self.thumb_size = thumb_size
        self.columns = columns
        self.on_select = on_select

        self._photo_refs = []

        if self.images:
            self._build_grid()

    def _build_grid(self):
        """Build thumbnail grid."""
        if not PIL_AVAILABLE:
            return

        for i, path in enumerate(self.images):
            row = i // self.columns
            col = i % self.columns

            try:
                img = Image.open(path)
                img.thumbnail((self.thumb_size, self.thumb_size))
                photo = ImageTk.PhotoImage(img)
                self._photo_refs.append(photo)

                btn = tk.Button(
                    self,
                    image=photo,
                    bg=ACCENT_COLOR,
                    relief=tk.FLAT,
                    command=lambda p=path: self._on_click(p)
                )
                btn.grid(row=row, column=col, padx=5, pady=5)

            except Exception:
                pass

    def _on_click(self, path: Path):
        """Handle thumbnail click."""
        if self.on_select:
            self.on_select(path)

    def set_images(self, images: List[Path]):
        """Set new image list.

        Args:
            images: List of image paths
        """
        # Clear existing
        for widget in self.winfo_children():
            widget.destroy()
        self._photo_refs = []

        self.images = images
        self._build_grid()


def get_recent_screenshots(limit: int = 10) -> List[Path]:
    """Get recent screenshots.

    Args:
        limit: Max screenshots to return

    Returns:
        List of screenshot paths, newest first
    """
    if not SCREENSHOT_DIR.exists():
        return []

    screenshots = list(SCREENSHOT_DIR.glob("*.png"))
    screenshots.extend(SCREENSHOT_DIR.glob("*.jpg"))
    screenshots.extend(SCREENSHOT_DIR.glob("*.jpeg"))

    # Sort by modification time, newest first
    screenshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return screenshots[:limit]


if __name__ == "__main__":
    print("=== IMAGE PANEL TEST ===")

    if not PIL_AVAILABLE:
        print("[!] PIL not available. Install: pip install Pillow")
        sys.exit(1)

    # Create test window
    root = tk.Tk()
    root.title("Image Panel Test")
    root.configure(bg=BG_COLOR)
    root.geometry("600x500")

    # Get recent screenshots
    screenshots = get_recent_screenshots(5)

    if screenshots:
        print(f"Found {len(screenshots)} screenshots")

        panel = ImagePanel(
            root,
            images=screenshots,
            show_controls=True
        )
        panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    else:
        print("No screenshots found")
        tk.Label(
            root,
            text="No screenshots found in data/screenshots",
            fg=TEXT_COLOR,
            bg=BG_COLOR
        ).pack(expand=True)

    root.mainloop()
