#!/usr/bin/env python3
"""
C.O.R.A Fullscreen Image Display
Display images in fullscreen with controls

Per ARCHITECTURE.md v2.2.0:
- show_fullscreen_image(path) - display image fullscreen
- show_boot_image() - generate and display boot image
- FullscreenImageWindow class for UI integration
"""

import tkinter as tk
from pathlib import Path
from typing import Optional, Callable
import threading


class FullscreenImageWindow:
    """Fullscreen image display window with close button."""

    def __init__(
        self,
        image_path: str,
        on_close: Optional[Callable] = None,
        auto_close_seconds: int = 0
    ):
        """Initialize fullscreen image window.

        Args:
            image_path: Path to image file
            on_close: Callback when window closes
            auto_close_seconds: Auto-close after N seconds (0 = never)
        """
        self.image_path = Path(image_path)
        self.on_close = on_close
        self.auto_close_seconds = auto_close_seconds
        self.root = None
        self.photo = None

    def show(self) -> bool:
        """Display the image in fullscreen.

        Returns:
            True if displayed successfully
        """
        try:
            from PIL import Image, ImageTk
        except ImportError:
            print("[!] PIL not available. Install with: pip install pillow")
            return False

        if not self.image_path.exists():
            print(f"[!] Image not found: {self.image_path}")
            return False

        try:
            from ui.window_manager import create_image_window

            # Use window manager for proper z-layering
            self.root = create_image_window(
                title="CORA",
                maximized=True
            )

            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            # Load and resize image
            img = Image.open(self.image_path)
            img = img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)

            # Display image
            label = tk.Label(self.root, image=self.photo, bg='black')
            label.pack(fill=tk.BOTH, expand=True)

            # Close button (red X, top-right)
            close_btn = tk.Button(
                self.root,
                text="X",
                command=self._close,
                font=('Arial', 16, 'bold'),
                fg='white',
                bg='#cc0000',
                activebackground='#ff0000',
                activeforeground='white',
                width=3,
                height=1,
                relief=tk.FLAT,
                cursor='hand2'
            )
            close_btn.place(x=screen_width - 50, y=10)

            # Bind Escape to close
            self.root.bind('<Escape>', lambda e: self._close())
            # Click anywhere to close
            label.bind('<Button-1>', lambda e: self._close())

            # Auto-close timer
            if self.auto_close_seconds > 0:
                self.root.after(
                    self.auto_close_seconds * 1000,
                    self._close
                )

            # Start mainloop if we created the root
            if not tk._default_root or self.root == tk._default_root:
                self.root.mainloop()

            return True

        except Exception as e:
            print(f"[!] Display error: {e}")
            return False

    def _close(self):
        """Close the window and call callback."""
        if self.root:
            self.root.destroy()
        if self.on_close:
            self.on_close()


def show_fullscreen_image(
    image_path: str,
    on_close: Optional[Callable] = None,
    auto_close_seconds: int = 0
) -> bool:
    """Display an image in fullscreen.

    Args:
        image_path: Path to the image file
        on_close: Optional callback when window closes
        auto_close_seconds: Auto-close after N seconds (0 = never)

    Returns:
        True if displayed successfully
    """
    window = FullscreenImageWindow(
        image_path,
        on_close=on_close,
        auto_close_seconds=auto_close_seconds
    )
    return window.show()


def show_boot_image(
    prompt: Optional[str] = None,
    on_close: Optional[Callable] = None,
    auto_close_seconds: int = 5
) -> bool:
    """Generate and display a boot image.

    Args:
        prompt: Custom image prompt (or use default)
        on_close: Optional callback when window closes
        auto_close_seconds: Auto-close after N seconds

    Returns:
        True if generated and displayed successfully
    """
    try:
        from tools.image_gen import generate_boot_image

        print("[*] Generating boot image...")
        result = generate_boot_image(prompt)

        if result.get("success"):
            return show_fullscreen_image(
                result["path"],
                on_close=on_close,
                auto_close_seconds=auto_close_seconds
            )
        else:
            print(f"[!] Image generation failed: {result.get('error')}")
            return False

    except ImportError:
        print("[!] Image generation not available")
        return False
    except Exception as e:
        print(f"[!] Boot image error: {e}")
        return False


def show_image_async(
    image_path: str,
    on_close: Optional[Callable] = None,
    auto_close_seconds: int = 0
):
    """Display an image in a separate thread (non-blocking).

    Args:
        image_path: Path to the image file
        on_close: Optional callback when window closes
        auto_close_seconds: Auto-close after N seconds
    """
    def display_thread():
        show_fullscreen_image(
            image_path,
            on_close=on_close,
            auto_close_seconds=auto_close_seconds
        )

    thread = threading.Thread(target=display_thread, daemon=True)
    thread.start()


if __name__ == "__main__":
    print("=== CORA Fullscreen Image Test ===")

    # Test with a generated boot image
    print("\n1. Testing boot image generation and display...")
    show_boot_image(auto_close_seconds=3)

    print("\n=== Test Complete ===")
