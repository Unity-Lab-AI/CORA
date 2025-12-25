#!/usr/bin/env python3
"""
C.O.R.A Window Manager
Centralized window creation, z-layering, resizing, and scaling for all CORA windows.

All windows behave like proper Windows applications:
- Maximize button works
- Border drag resizing with cursor change
- Proper scaling of UI elements on resize

Created by: Unity AI Lab
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Tuple, List
from pathlib import Path

# Track all open windows
_open_windows = {}

# Base font sizes for scaling
_BASE_FONTS = {
    'title': 24,
    'header': 16,
    'body': 11,
    'small': 9,
    'code': 11,
}


class ScalableWindow:
    """Mixin for windows that scale their content on resize."""

    def __init__(self):
        self._scale_factor = 1.0
        self._base_width = 1200
        self._base_height = 800
        self._scalable_widgets = []

    def register_scalable(self, widget, font_type: str = 'body', base_size: int = None):
        """Register a widget for font scaling on resize."""
        if base_size is None:
            base_size = _BASE_FONTS.get(font_type, 11)
        self._scalable_widgets.append((widget, font_type, base_size))

    def _on_resize(self, event):
        """Handle window resize - scale fonts."""
        if event.widget == self._root:
            # Calculate scale factor based on window size
            width_scale = event.width / self._base_width
            height_scale = event.height / self._base_height
            self._scale_factor = min(max(0.7, (width_scale + height_scale) / 2), 1.5)

            # Update all registered widgets
            for widget, font_type, base_size in self._scalable_widgets:
                try:
                    new_size = int(base_size * self._scale_factor)
                    new_size = max(8, new_size)  # Minimum font size
                    current_font = widget.cget('font')
                    if isinstance(current_font, str):
                        # Parse font string like "Consolas 11"
                        parts = current_font.split()
                        if len(parts) >= 2:
                            family = parts[0]
                            weight = parts[2] if len(parts) > 2 else ''
                            widget.configure(font=(family, new_size, weight))
                        else:
                            widget.configure(font=(current_font, new_size))
                    else:
                        widget.configure(font=(current_font[0], new_size) + current_font[2:])
                except:
                    pass


def create_window(
    title: str = "CORA",
    width: int = 800,
    height: int = 600,
    bg: str = "#1a1a2e",
    resizable: bool = True,
    center: bool = True,
    maximized: bool = False,
    parent: Optional[tk.Tk] = None,
    on_close: Optional[Callable] = None,
    min_width: int = 400,
    min_height: int = 300
) -> tk.Toplevel:
    """
    Create a new window with proper Windows behavior.

    - Maximize/minimize/close buttons work
    - Border drag resizing with proper cursors
    - Normal z-layering (not forced topmost)

    Args:
        title: Window title
        width: Initial window width
        height: Initial window height
        bg: Background color
        resizable: Allow resizing (default True)
        center: Center on screen
        maximized: Start maximized
        parent: Parent window
        on_close: Callback when window closes
        min_width: Minimum window width
        min_height: Minimum window height

    Returns:
        tk.Toplevel window with proper Windows behavior
    """
    # Create window
    if parent:
        window = tk.Toplevel(parent)
    elif tk._default_root:
        window = tk.Toplevel(tk._default_root)
    else:
        window = tk.Tk()

    window.title(title)
    window.configure(bg=bg)

    # CRITICAL: Do NOT use overrideredirect - keeps normal Windows decorations
    # This gives us maximize, minimize, close buttons and border resize handles

    # Size and position
    if maximized:
        window.geometry(f"{width}x{height}")
        window.state('zoomed')
    else:
        if center:
            x, y = _center_position(window, width, height)
            window.geometry(f"{width}x{height}+{x}+{y}")
        else:
            window.geometry(f"{width}x{height}")

    # Resizable with minimum size
    if resizable:
        window.resizable(True, True)
        window.minsize(min_width, min_height)
    else:
        window.resizable(False, False)

    # Normal z-layering - bring to front initially but don't force topmost
    _bring_to_front(window)

    # Close handler
    def handle_close():
        window_id = str(window.winfo_id())
        if window_id in _open_windows:
            del _open_windows[window_id]
        if on_close:
            on_close()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", handle_close)

    # Track window
    _open_windows[str(window.winfo_id())] = window

    return window


def create_popup(
    title: str = "CORA",
    width: int = 500,
    height: int = 300,
    bg: str = "#1a1a2e",
    parent: Optional[tk.Tk] = None,
    on_close: Optional[Callable] = None,
    auto_close_seconds: int = 0,
    resizable: bool = True
) -> tk.Toplevel:
    """
    Create a popup window with proper Windows behavior.

    Args:
        title: Window title
        width: Popup width
        height: Popup height
        bg: Background color
        parent: Parent window
        on_close: Callback when closed
        auto_close_seconds: Auto-close after N seconds (0 = disabled)
        resizable: Allow resizing (default True now)

    Returns:
        tk.Toplevel popup
    """
    popup = create_window(
        title=title,
        width=width,
        height=height,
        bg=bg,
        resizable=resizable,
        center=True,
        parent=parent,
        on_close=on_close,
        min_width=300,
        min_height=200
    )

    # Auto-close timer
    if auto_close_seconds > 0:
        popup.after(auto_close_seconds * 1000, lambda: _safe_destroy(popup))

    return popup


def create_image_window(
    title: str = "CORA - Image",
    width: int = 1280,
    height: int = 720,
    parent: Optional[tk.Tk] = None,
    on_close: Optional[Callable] = None,
    maximized: bool = False
) -> tk.Toplevel:
    """
    Create a window for displaying images with proper resize behavior.

    Args:
        title: Window title
        width: Window width
        height: Window height
        parent: Parent window
        on_close: Callback when closed
        maximized: Start maximized

    Returns:
        tk.Toplevel window with black background
    """
    return create_window(
        title=title,
        width=width,
        height=height,
        bg="black",
        resizable=True,
        center=True,
        maximized=maximized,
        parent=parent,
        on_close=on_close,
        min_width=400,
        min_height=300
    )


def create_code_window(
    title: str = "CORA - Code",
    width: int = 900,
    height: int = 600,
    parent: Optional[tk.Tk] = None,
    on_close: Optional[Callable] = None
) -> tk.Toplevel:
    """
    Create a window for displaying code with proper resize behavior.

    Args:
        title: Window title
        width: Window width
        height: Window height
        parent: Parent window
        on_close: Callback when closed

    Returns:
        tk.Toplevel window with dark code theme
    """
    return create_window(
        title=title,
        width=width,
        height=height,
        bg="#1e1e1e",
        resizable=True,
        center=True,
        parent=parent,
        on_close=on_close,
        min_width=500,
        min_height=400
    )


def create_modal(
    title: str = "CORA",
    width: int = 600,
    height: int = 450,
    bg: str = "#1a1a2e",
    parent: Optional[tk.Tk] = None,
    on_close: Optional[Callable] = None
) -> tk.Toplevel:
    """
    Create a modal dialog window with proper resize behavior.

    Args:
        title: Window title
        width: Modal width
        height: Modal height
        bg: Background color
        parent: Parent window
        on_close: Callback when closed

    Returns:
        tk.Toplevel modal
    """
    return create_window(
        title=title,
        width=width,
        height=height,
        bg=bg,
        resizable=True,
        center=True,
        parent=parent,
        on_close=on_close,
        min_width=400,
        min_height=300
    )


def create_terminal_window(
    title: str = "CORA - Terminal",
    width: int = 900,
    height: int = 500,
    parent: Optional[tk.Tk] = None,
    on_close: Optional[Callable] = None
) -> tk.Toplevel:
    """
    Create a terminal-style window.

    Args:
        title: Window title
        width: Window width
        height: Window height
        parent: Parent window
        on_close: Callback when closed

    Returns:
        tk.Toplevel terminal window
    """
    return create_window(
        title=title,
        width=width,
        height=height,
        bg="#0c0c0c",
        resizable=True,
        center=True,
        parent=parent,
        on_close=on_close,
        min_width=500,
        min_height=300
    )


def bring_to_front(window: tk.Toplevel):
    """
    Bring window to front with normal z-layering.
    Public wrapper for _bring_to_front.
    """
    _bring_to_front(window)


def close_window(window: tk.Toplevel):
    """Safely close a window."""
    _safe_destroy(window)


def close_all_windows():
    """Close all tracked windows."""
    for window_id, window in list(_open_windows.items()):
        _safe_destroy(window)
    _open_windows.clear()


def get_open_windows() -> dict:
    """Get all currently open windows."""
    return _open_windows.copy()


def setup_scaling(window: tk.Toplevel, base_width: int = 1200, base_height: int = 800):
    """
    Setup font scaling for a window based on its size.

    Call this after adding all widgets, then use register_for_scaling() on each widget.

    Args:
        window: The window to setup scaling for
        base_width: The base width for 1.0 scale factor
        base_height: The base height for 1.0 scale factor

    Returns:
        A function to register widgets for scaling
    """
    scalable_widgets = []

    def on_resize(event):
        if event.widget == window:
            # Calculate scale factor
            width_scale = event.width / base_width
            height_scale = event.height / base_height
            scale = min(max(0.7, (width_scale + height_scale) / 2), 1.5)

            # Update all registered widgets
            for widget, base_size, font_family, font_weight in scalable_widgets:
                try:
                    new_size = max(8, int(base_size * scale))
                    if font_weight:
                        widget.configure(font=(font_family, new_size, font_weight))
                    else:
                        widget.configure(font=(font_family, new_size))
                except:
                    pass

    window.bind('<Configure>', on_resize)

    def register(widget, base_size: int = 11, font_family: str = 'Consolas', font_weight: str = ''):
        """Register a widget for font scaling."""
        scalable_widgets.append((widget, base_size, font_family, font_weight))

    return register


# =============================================================================
# Internal helpers
# =============================================================================

def _center_position(window: tk.Toplevel, width: int, height: int) -> Tuple[int, int]:
    """Calculate centered position for a window."""
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    return x, y


def _bring_to_front(window: tk.Toplevel):
    """
    Bring window to front with normal z-layering.
    Uses Windows API for proper behavior, falls back to tkinter.
    """
    try:
        import ctypes

        # Windows constants
        HWND_TOP = 0  # Normal z-order (NOT HWND_TOPMOST)
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_SHOWWINDOW = 0x0040

        # Ensure NOT topmost (normal stacking)
        window.attributes('-topmost', False)
        window.update_idletasks()

        # Get window handle
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if hwnd == 0:
            hwnd = window.winfo_id()

        # Bring to front with normal z-order
        ctypes.windll.user32.SetWindowPos(
            hwnd, HWND_TOP, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
        )

        # Set as foreground window
        ctypes.windll.user32.SetForegroundWindow(hwnd)

        # Tkinter lift and focus
        window.lift()
        window.focus_force()

    except Exception:
        # Fallback to basic tkinter
        try:
            window.attributes('-topmost', False)
            window.lift()
            window.focus_force()
        except:
            pass


def _safe_destroy(window: tk.Toplevel):
    """Safely destroy a window."""
    try:
        window_id = str(window.winfo_id())
        if window_id in _open_windows:
            del _open_windows[window_id]
        window.destroy()
    except:
        pass


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("=== Window Manager Test ===")
    print("Testing proper Windows behavior:")
    print("- Maximize button should work")
    print("- Border drag resize should work")
    print("- Normal z-layering (not always on top)")

    root = tk.Tk()
    root.title("Main Window - Try Resizing!")
    root.geometry("600x400")
    root.minsize(400, 300)

    # Setup scaling for root
    register_scale = setup_scaling(root, 600, 400)

    main_label = tk.Label(
        root,
        text="This window should resize properly!\nTry dragging the borders or maximizing.",
        font=("Consolas", 14),
        bg="#1a1a2e",
        fg="white"
    )
    main_label.pack(expand=True, fill='both')
    register_scale(main_label, 14, "Consolas")

    root.configure(bg="#1a1a2e")

    def open_popup():
        popup = create_popup(
            title="Test Popup - Resizable!",
            width=500,
            height=350,
            parent=root
        )
        lbl = tk.Label(
            popup,
            text="This popup is resizable!\nDrag borders or maximize.",
            fg="white",
            bg="#1a1a2e",
            font=("Consolas", 12)
        )
        lbl.pack(expand=True, fill='both')

    def open_modal():
        modal = create_modal(
            title="Test Modal - Resizable!",
            width=600,
            height=400,
            parent=root
        )
        lbl = tk.Label(
            modal,
            text="Modal with proper Windows behavior!",
            fg="white",
            bg="#1a1a2e",
            font=("Consolas", 12)
        )
        lbl.pack(expand=True, fill='both')

    btn_frame = tk.Frame(root, bg="#1a1a2e")
    btn_frame.pack(pady=20)

    tk.Button(btn_frame, text="Open Popup", command=open_popup).pack(side='left', padx=10)
    tk.Button(btn_frame, text="Open Modal", command=open_modal).pack(side='left', padx=10)
    tk.Button(btn_frame, text="Close All", command=close_all_windows).pack(side='left', padx=10)

    root.mainloop()
