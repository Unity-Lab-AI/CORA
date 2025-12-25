#!/usr/bin/env python3
"""
C.O.R.A Live Camera Feed
Real-time camera window that stays open for continuous viewing and snapshots.

Features:
- Live video feed from webcam
- Take snapshots on command ("what do you see", "how many fingers", etc.)
- Stays open while user interacts with CORA
- Normal z-layering (not forced topmost)

Created by: Unity AI Lab
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

# Try imports
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Project paths
PROJECT_DIR = Path(__file__).parent.parent
SNAPSHOTS_DIR = PROJECT_DIR / 'data' / 'camera'


class LiveCameraFeed:
    """Live camera feed window with snapshot capability."""

    def __init__(
        self,
        parent: Optional[tk.Tk] = None,
        camera_index: int = 0,
        width: int = 960,
        height: int = 720,
        on_snapshot: Optional[Callable] = None
    ):
        """
        Initialize live camera feed.

        Args:
            parent: Parent window (optional)
            camera_index: Camera device index (0 = default camera)
            width: Window width
            height: Window height
            on_snapshot: Callback when snapshot is taken (receives path)
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.on_snapshot = on_snapshot

        self.window = None
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.frame_label = None
        self._update_thread = None

        # Ensure snapshot directory exists
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        # Create window
        self._create_window(parent)

    def _create_window(self, parent: Optional[tk.Tk]):
        """Create the camera feed window."""
        from ui.window_manager import create_window, bring_to_front

        self.window = create_window(
            title="CORA - Live Camera",
            width=self.width,
            height=self.height + 60,  # Extra for controls
            bg='#1a1a2e',
            parent=parent,
            on_close=self.stop
        )

        # Header
        header = tk.Frame(self.window, bg='#16213e', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Live Camera Feed",
            font=('Segoe UI', 12, 'bold'),
            fg='#00ff88',
            bg='#16213e'
        ).pack(side='left', padx=15, pady=8)

        # Status indicator
        self.status_label = tk.Label(
            header,
            text="Connecting...",
            font=('Consolas', 10),
            fg='#888888',
            bg='#16213e'
        )
        self.status_label.pack(side='right', padx=15)

        # Video frame area
        self.frame_label = tk.Label(
            self.window,
            bg='black',
            text="Starting camera..." if CV2_AVAILABLE else "OpenCV not available",
            fg='white',
            font=('Segoe UI', 14)
        )
        self.frame_label.pack(fill='both', expand=True, padx=5, pady=5)

        # Control bar
        controls = tk.Frame(self.window, bg='#16213e', height=50)
        controls.pack(fill='x', side='bottom')
        controls.pack_propagate(False)

        # Snapshot button
        self.snapshot_btn = tk.Button(
            controls,
            text="Take Snapshot",
            font=('Segoe UI', 10, 'bold'),
            fg='white',
            bg='#0f3460',
            activebackground='#533483',
            activeforeground='white',
            relief='flat',
            padx=20,
            pady=5,
            command=self.take_snapshot
        )
        self.snapshot_btn.pack(side='left', padx=15, pady=10)

        # Last snapshot info
        self.snapshot_info = tk.Label(
            controls,
            text="",
            font=('Consolas', 9),
            fg='#888888',
            bg='#16213e'
        )
        self.snapshot_info.pack(side='left', padx=10)

        # Close button
        close_btn = tk.Button(
            controls,
            text="Close",
            font=('Segoe UI', 10),
            fg='white',
            bg='#cc0000',
            activebackground='#ff0000',
            activeforeground='white',
            relief='flat',
            padx=15,
            pady=5,
            command=self.stop
        )
        close_btn.pack(side='right', padx=15, pady=10)

    def start(self):
        """Start the camera feed."""
        if not CV2_AVAILABLE:
            self.status_label.config(text="OpenCV not installed", fg='#ff4444')
            return False

        if not PIL_AVAILABLE:
            self.status_label.config(text="Pillow not installed", fg='#ff4444')
            return False

        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                self.status_label.config(text="Camera not found", fg='#ff4444')
                return False

            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            self.is_running = True
            self.status_label.config(text="Live", fg='#00ff88')

            # Start update thread
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()

            return True

        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg='#ff4444')
            return False

    def _update_loop(self):
        """Background thread to update video frames."""
        while self.is_running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame = frame

                    # Convert to PhotoImage
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)

                    # Resize to fit window
                    img = img.resize((self.width - 10, self.height - 10), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                    # Update label (thread-safe)
                    if self.frame_label and self.is_running:
                        self.frame_label.configure(image=photo, text='')
                        self.frame_label.image = photo

                time.sleep(0.033)  # ~30 FPS

            except Exception as e:
                print(f"[Camera] Frame error: {e}")
                time.sleep(0.1)

    def take_snapshot(self) -> Optional[Path]:
        """
        Take a snapshot of the current frame.

        Returns:
            Path to saved snapshot or None
        """
        if self.current_frame is None:
            return None

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'snapshot_{timestamp}.jpg'
            path = SNAPSHOTS_DIR / filename

            cv2.imwrite(str(path), self.current_frame)

            # Update UI
            self.snapshot_info.config(text=f"Saved: {filename}")

            # Callback
            if self.on_snapshot:
                self.on_snapshot(path)

            print(f"[Camera] Snapshot saved: {path}")
            return path

        except Exception as e:
            print(f"[Camera] Snapshot error: {e}")
            self.snapshot_info.config(text=f"Error: {e}")
            return None

    def get_current_frame_path(self) -> Optional[Path]:
        """
        Save current frame and return path (for AI analysis).

        Returns:
            Path to temporary frame image
        """
        if self.current_frame is None:
            return None

        try:
            path = SNAPSHOTS_DIR / 'current_frame.jpg'
            cv2.imwrite(str(path), self.current_frame)
            return path
        except:
            return None

    def stop(self):
        """Stop the camera feed and close window."""
        self.is_running = False

        if self.cap:
            self.cap.release()
            self.cap = None

        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None

    def is_active(self) -> bool:
        """Check if camera feed is active."""
        return self.is_running and self.window is not None


# Global camera feed instance
_live_camera: Optional[LiveCameraFeed] = None


def open_live_camera(
    parent: Optional[tk.Tk] = None,
    on_snapshot: Optional[Callable] = None
) -> Optional[LiveCameraFeed]:
    """
    Open live camera feed window.

    Args:
        parent: Parent window
        on_snapshot: Callback when snapshot taken

    Returns:
        LiveCameraFeed instance or None
    """
    global _live_camera

    # Close existing if open
    if _live_camera and _live_camera.is_active():
        _live_camera.stop()

    _live_camera = LiveCameraFeed(parent=parent, on_snapshot=on_snapshot)
    if _live_camera.start():
        return _live_camera
    return None


def get_live_camera() -> Optional[LiveCameraFeed]:
    """Get current live camera instance."""
    global _live_camera
    if _live_camera and _live_camera.is_active():
        return _live_camera
    return None


def close_live_camera():
    """Close live camera feed."""
    global _live_camera
    if _live_camera:
        _live_camera.stop()
        _live_camera = None


def capture_from_live_camera() -> Optional[Path]:
    """
    Capture frame from live camera for AI analysis.

    Returns:
        Path to captured frame or None
    """
    global _live_camera
    if _live_camera and _live_camera.is_active():
        return _live_camera.get_current_frame_path()
    return None


# Test
if __name__ == "__main__":
    print("=== Live Camera Feed Test ===")

    if not CV2_AVAILABLE:
        print("OpenCV not available!")
    else:
        root = tk.Tk()
        root.withdraw()  # Hide main window

        def on_snap(path):
            print(f"Snapshot callback: {path}")

        camera = open_live_camera(parent=root, on_snapshot=on_snap)
        if camera:
            print("Camera started. Close window to exit.")
            root.mainloop()
        else:
            print("Failed to start camera")
