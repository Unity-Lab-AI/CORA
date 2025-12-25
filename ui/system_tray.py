#!/usr/bin/env python3
"""
C.O.R.A System Tray Integration
System tray icon with quick access menu

Per ARCHITECTURE.md v1.0.0:
- System tray icon using pystray
- Quick access to common actions
- Show/hide main window
- Status indicators
"""

import threading
from pathlib import Path
from typing import Optional, Callable
from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import MenuItem as Item, Menu
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("[!] pystray not available. Install with: pip install pystray")


# Project paths
PROJECT_DIR = Path(__file__).parent.parent
ICON_PATH = PROJECT_DIR / 'assets' / 'icon.png'


def create_default_icon(size: int = 64) -> Image.Image:
    """Create a default CORA icon if asset not found.

    Args:
        size: Icon size in pixels

    Returns:
        PIL Image
    """
    # Create a simple circular icon with "C" letter
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Blue circle background
    margin = 4
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(30, 144, 255, 255),  # Dodger blue
        outline=(255, 255, 255, 255),
        width=2
    )

    # Draw "C" for CORA
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("arial.ttf", int(size * 0.5))
    except Exception:
        font = None

    text = "C"
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - 2
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    else:
        # Fallback without font
        draw.text((size // 3, size // 4), text, fill=(255, 255, 255, 255))

    return img


def load_icon() -> Image.Image:
    """Load the CORA icon.

    Returns:
        PIL Image
    """
    if ICON_PATH.exists():
        try:
            return Image.open(ICON_PATH)
        except Exception:
            pass
    return create_default_icon()


class SystemTray:
    """System tray icon manager for CORA."""

    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_hide: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        on_settings: Optional[Callable] = None
    ):
        """Initialize system tray.

        Args:
            on_show: Callback to show main window
            on_hide: Callback to hide main window
            on_quit: Callback to quit application
            on_settings: Callback to open settings
        """
        self.on_show = on_show
        self.on_hide = on_hide
        self.on_quit = on_quit
        self.on_settings = on_settings
        self.icon = None
        self._thread = None
        self._running = False
        self._visible = True

    def _create_menu(self) -> Menu:
        """Create the system tray menu.

        Returns:
            pystray Menu
        """
        return Menu(
            Item(
                "Show CORA",
                self._on_show_click,
                visible=lambda item: not self._visible
            ),
            Item(
                "Hide CORA",
                self._on_hide_click,
                visible=lambda item: self._visible
            ),
            Menu.SEPARATOR,
            Item("Settings", self._on_settings_click),
            Item("About", self._on_about_click),
            Menu.SEPARATOR,
            Item("Quit", self._on_quit_click)
        )

    def _on_show_click(self, icon, item):
        """Handle Show menu click."""
        self._visible = True
        if self.on_show:
            self.on_show()

    def _on_hide_click(self, icon, item):
        """Handle Hide menu click."""
        self._visible = False
        if self.on_hide:
            self.on_hide()

    def _on_settings_click(self, icon, item):
        """Handle Settings menu click."""
        if self.on_settings:
            self.on_settings()

    def _on_about_click(self, icon, item):
        """Handle About menu click."""
        # Could show an about dialog
        print("[CORA] C.O.R.A - Cognitive Operations & Reasoning Assistant v2.0")

    def _on_quit_click(self, icon, item):
        """Handle Quit menu click."""
        self.stop()
        if self.on_quit:
            self.on_quit()

    def start(self):
        """Start the system tray icon in a background thread."""
        if not PYSTRAY_AVAILABLE:
            print("[!] Cannot start system tray - pystray not installed")
            return False

        if self._running:
            return True

        self._running = True

        def run_tray():
            self.icon = pystray.Icon(
                name="CORA",
                icon=load_icon(),
                title="C.O.R.A - Cognitive Operations & Reasoning Assistant",
                menu=self._create_menu()
            )
            self.icon.run()

        self._thread = threading.Thread(target=run_tray, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop the system tray icon."""
        self._running = False
        if self.icon:
            self.icon.stop()
            self.icon = None

    def update_icon(self, image: Image.Image = None):
        """Update the tray icon.

        Args:
            image: New icon image (or reload default)
        """
        if self.icon:
            self.icon.icon = image or load_icon()

    def notify(self, title: str, message: str):
        """Show a system notification.

        Args:
            title: Notification title
            message: Notification message
        """
        if self.icon and hasattr(self.icon, 'notify'):
            self.icon.notify(message, title)

    def set_visible(self, visible: bool):
        """Update visibility state.

        Args:
            visible: Whether main window is visible
        """
        self._visible = visible


def create_system_tray(
    on_show: Optional[Callable] = None,
    on_hide: Optional[Callable] = None,
    on_quit: Optional[Callable] = None,
    on_settings: Optional[Callable] = None
) -> Optional[SystemTray]:
    """Factory function to create system tray.

    Args:
        on_show: Show window callback
        on_hide: Hide window callback
        on_quit: Quit app callback
        on_settings: Open settings callback

    Returns:
        SystemTray instance or None if unavailable
    """
    if not PYSTRAY_AVAILABLE:
        return None

    tray = SystemTray(
        on_show=on_show,
        on_hide=on_hide,
        on_quit=on_quit,
        on_settings=on_settings
    )
    return tray


if __name__ == "__main__":
    print("=== CORA System Tray Test ===")

    if not PYSTRAY_AVAILABLE:
        print("[!] pystray not installed. Run: pip install pystray")
        exit(1)

    def on_show():
        print("[TEST] Show window clicked")

    def on_hide():
        print("[TEST] Hide window clicked")

    def on_quit():
        print("[TEST] Quit clicked")
        exit(0)

    def on_settings():
        print("[TEST] Settings clicked")

    print("Starting system tray icon...")
    print("Look for the CORA icon in your system tray.")
    print("Right-click to see the menu. Click Quit to exit.")

    tray = create_system_tray(
        on_show=on_show,
        on_hide=on_hide,
        on_quit=on_quit,
        on_settings=on_settings
    )

    if tray:
        tray.start()
        # Keep main thread alive
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            tray.stop()
            print("\n[TEST] Stopped")
