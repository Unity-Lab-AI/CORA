#!/usr/bin/env python3
"""
C.O.R.A TTS Handler
Threaded text-to-speech handler for non-blocking UI

ASYNC-002: Run TTS in separate thread to not block UI
"""

import threading
import queue
from typing import Optional, Callable


class TTSHandler:
    """Threaded TTS handler for non-blocking speech."""

    def __init__(self, on_start: Optional[Callable] = None, on_complete: Optional[Callable] = None):
        """Initialize the TTS handler.

        Args:
            on_start: Callback when speech starts
            on_complete: Callback when speech completes
        """
        self.on_start = on_start
        self.on_complete = on_complete
        self._queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._engine = None
        self._config = {
            "rate": 150,
            "volume": 0.9,
            "engine": "pyttsx3"
        }

    def start(self):
        """Start the TTS worker thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the TTS worker thread."""
        self._running = False
        self._queue.put(None)  # Signal to stop
        if self._thread:
            self._thread.join(timeout=2)

    def speak(self, text: str, emotion: str = "neutral"):
        """Queue text to be spoken.

        Args:
            text: Text to speak
            emotion: Emotional tone (for future Kokoro support)
        """
        if self._running:
            self._queue.put({"text": text, "emotion": emotion})

    def configure(self, rate: int = None, volume: float = None, engine: str = None):
        """Configure TTS settings.

        Args:
            rate: Speech rate (words per minute)
            volume: Volume (0.0 to 1.0)
            engine: TTS engine ("pyttsx3" or "kokoro")
        """
        if rate is not None:
            self._config["rate"] = rate
        if volume is not None:
            self._config["volume"] = volume
        if engine is not None:
            self._config["engine"] = engine

    def _worker(self):
        """Background worker that processes the speech queue."""
        # Initialize TTS engine
        self._init_engine()

        while self._running:
            try:
                item = self._queue.get(timeout=1)
                if item is None:
                    break

                text = item.get("text", "")
                emotion = item.get("emotion", "neutral")

                if text and self._engine:
                    if self.on_start:
                        self.on_start()

                    self._speak_text(text, emotion)

                    if self.on_complete:
                        self.on_complete()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TTS Error]: {e}")

    def _init_engine(self):
        """Initialize the TTS engine."""
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._config["rate"])
            self._engine.setProperty("volume", self._config["volume"])
        except ImportError:
            self._engine = None
            print("[TTS] pyttsx3 not available")
        except Exception as e:
            self._engine = None
            print(f"[TTS] Init error: {e}")

    def _speak_text(self, text: str, emotion: str):
        """Speak text using the configured engine.

        Args:
            text: Text to speak
            emotion: Emotional tone
        """
        if self._config["engine"] == "kokoro":
            self._speak_kokoro(text, emotion)
        else:
            self._speak_pyttsx3(text)

    def _speak_pyttsx3(self, text: str):
        """Speak using pyttsx3."""
        if self._engine:
            try:
                self._engine.setProperty("rate", self._config["rate"])
                self._engine.setProperty("volume", self._config["volume"])
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                print(f"[TTS pyttsx3 Error]: {e}")

    def _speak_kokoro(self, text: str, emotion: str):
        """Speak using Kokoro TTS (if available)."""
        try:
            from kokoro import KPipeline
            import sounddevice as sd

            pipeline = KPipeline(lang_code="a")
            generator = pipeline(text, voice="af_bella", speed=1.0)

            for _, _, audio in generator:
                sd.play(audio, samplerate=24000)
                sd.wait()

        except ImportError:
            # Fall back to pyttsx3
            self._speak_pyttsx3(text)
        except Exception as e:
            print(f"[TTS Kokoro Error]: {e}")
            self._speak_pyttsx3(text)


class TTSManager:
    """Singleton manager for TTS operations."""

    _instance: Optional["TTSManager"] = None
    _handler: Optional[TTSHandler] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._handler is None:
            self._handler = TTSHandler()
            self._handler.start()

    def speak(self, text: str, emotion: str = "neutral"):
        """Speak text asynchronously."""
        if self._handler:
            self._handler.speak(text, emotion)

    def configure(self, **kwargs):
        """Configure TTS settings."""
        if self._handler:
            self._handler.configure(**kwargs)

    def shutdown(self):
        """Shutdown the TTS handler."""
        if self._handler:
            self._handler.stop()


# Convenience function
def speak_async(text: str, emotion: str = "neutral"):
    """Speak text asynchronously using the global TTS manager.

    Args:
        text: Text to speak
        emotion: Emotional tone
    """
    manager = TTSManager()
    manager.speak(text, emotion)
