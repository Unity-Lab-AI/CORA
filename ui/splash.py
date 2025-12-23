#!/usr/bin/env python3
"""
C.O.R.A Splash Screen
Fullscreen boot splash with animated ASCII art and boot sequence

P2-BOOT: Add fullscreen boot image to startup
"""

import customtkinter as ctk
import threading
import time
from typing import Callable, Optional


class SplashScreen(ctk.CTkToplevel):
    """Fullscreen splash screen with animated boot sequence."""

    # ASCII art logo
    LOGO = """
    ██████╗  ██████╗ ██████╗  █████╗
   ██╔════╝ ██╔═══██╗██╔══██╗██╔══██╗
   ██║      ██║   ██║██████╔╝███████║
   ██║      ██║   ██║██╔══██╗██╔══██║
   ╚██████╗ ╚██████╔╝██║  ██║██║  ██║
    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
    """

    TAGLINE = "Cognitive Operations & Reasoning Assistant"

    def __init__(self, master=None, on_complete: Optional[Callable] = None,
                 boot_duration: float = 3.0):
        """Initialize splash screen.

        Args:
            master: Parent window (optional)
            on_complete: Callback when splash is done
            boot_duration: How long to show splash (seconds)
        """
        super().__init__(master)
        self.on_complete = on_complete
        self.boot_duration = boot_duration
        self._boot_messages = []
        self._current_msg_idx = 0
        self._is_running = True

        # Window setup - fullscreen
        self.title("C.O.R.A")
        self.attributes('-fullscreen', True)
        self.configure(fg_color="#0a0a0a")  # Near black

        # Bind escape to exit fullscreen
        self.bind("<Escape>", lambda e: self._skip_splash())
        self.bind("<space>", lambda e: self._skip_splash())
        self.bind("<Return>", lambda e: self._skip_splash())

        # Center layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)

        # Logo label (ASCII art)
        self.logo_label = ctk.CTkLabel(
            self,
            text=self.LOGO,
            font=ctk.CTkFont(family="Consolas", size=28, weight="bold"),
            text_color="#00ff88"  # Matrix green
        )
        self.logo_label.grid(row=0, column=0, pady=(100, 20), sticky="s")

        # Tagline
        self.tagline_label = ctk.CTkLabel(
            self,
            text=self.TAGLINE,
            font=ctk.CTkFont(size=16),
            text_color="#888888"
        )
        self.tagline_label.grid(row=1, column=0, pady=(0, 40))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self,
            width=400,
            height=4,
            mode="determinate"
        )
        self.progress_bar.grid(row=2, column=0, pady=20)
        self.progress_bar.set(0)

        # Boot status text
        self.status_label = ctk.CTkLabel(
            self,
            text="Initializing...",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#666666"
        )
        self.status_label.grid(row=3, column=0, pady=(20, 100), sticky="n")

        # Version in bottom right
        self.version_label = ctk.CTkLabel(
            self,
            text="v2.0.0",
            font=ctk.CTkFont(size=10),
            text_color="#444444"
        )
        self.version_label.place(relx=0.98, rely=0.98, anchor="se")

        # Skip hint in bottom left
        self.skip_label = ctk.CTkLabel(
            self,
            text="Press SPACE or ESC to skip",
            font=ctk.CTkFont(size=10),
            text_color="#333333"
        )
        self.skip_label.place(relx=0.02, rely=0.98, anchor="sw")

        # Define boot messages
        self._boot_messages = [
            "Loading core systems...",
            "Initializing neural pathways...",
            "Calibrating voice synthesis...",
            "Connecting to knowledge base...",
            "Scanning local environment...",
            "Establishing cognitive framework...",
            "Optimizing response algorithms...",
            "Systems ready.",
        ]

        # Start boot animation
        self._start_boot_animation()

    def _start_boot_animation(self):
        """Start the boot animation sequence."""
        threading.Thread(target=self._run_boot_animation, daemon=True).start()

    def _run_boot_animation(self):
        """Run boot animation in background thread."""
        msg_count = len(self._boot_messages)
        time_per_msg = self.boot_duration / msg_count

        for i, msg in enumerate(self._boot_messages):
            if not self._is_running:
                break

            # Update progress and status
            progress = (i + 1) / msg_count
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            self.after(0, lambda m=msg: self.status_label.configure(text=m))

            # Wait before next message
            time.sleep(time_per_msg)

        # Complete
        if self._is_running:
            self.after(0, self._complete)

    def _skip_splash(self):
        """Skip the splash screen."""
        self._is_running = False
        self._complete()

    def _complete(self):
        """Complete splash and call callback."""
        self._is_running = False

        # Fade out effect (quick)
        self.after(100, lambda: self.attributes('-alpha', 0.8))
        self.after(200, lambda: self.attributes('-alpha', 0.5))
        self.after(300, lambda: self.attributes('-alpha', 0.2))
        self.after(400, self._finish)

    def _finish(self):
        """Destroy splash and call completion callback."""
        if self.on_complete:
            self.on_complete()
        self.destroy()


class MinimalSplash(ctk.CTkToplevel):
    """Minimal splash for fast boot - just logo flash."""

    LOGO = """C.O.R.A"""

    def __init__(self, master=None, on_complete: Optional[Callable] = None,
                 duration: float = 1.0):
        super().__init__(master)
        self.on_complete = on_complete
        self.duration = duration

        # Window setup
        self.title("C.O.R.A")
        self.geometry("400x200")
        self.resizable(False, False)
        self.configure(fg_color="#0a0a0a")

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 200) // 2
        self.geometry(f"400x200+{x}+{y}")

        # Remove decorations
        self.overrideredirect(True)

        # Logo
        self.logo_label = ctk.CTkLabel(
            self,
            text=self.LOGO,
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="#00ff88"
        )
        self.logo_label.pack(expand=True)

        # Auto-dismiss
        self.after(int(duration * 1000), self._complete)

    def _complete(self):
        if self.on_complete:
            self.on_complete()
        self.destroy()


def show_splash(master=None, fullscreen: bool = True, duration: float = 3.0,
                on_complete: Optional[Callable] = None):
    """Show splash screen.

    Args:
        master: Parent window
        fullscreen: Use fullscreen splash (True) or minimal (False)
        duration: Splash duration in seconds
        on_complete: Callback when done

    Returns:
        Splash window instance
    """
    if fullscreen:
        return SplashScreen(master, on_complete=on_complete, boot_duration=duration)
    else:
        return MinimalSplash(master, on_complete=on_complete, duration=duration)


if __name__ == "__main__":
    # Test splash screen
    root = ctk.CTk()
    root.withdraw()  # Hide main window

    def on_done():
        print("Splash complete!")
        root.deiconify()
        root.title("Main App")
        root.geometry("800x600")
        ctk.CTkLabel(root, text="Main Application", font=ctk.CTkFont(size=24)).pack(expand=True)

    splash = show_splash(root, fullscreen=True, duration=3.0, on_complete=on_done)
    root.mainloop()
