#!/usr/bin/env python3
"""
C.O.R.A Wake Word Detection
Always-listening detector for "Cora", "Hey Cora", "Yo Cora"

Per ARCHITECTURE.md v2.2.0:
- Run in background thread
- Detect wake words using Vosk
- On detection, activate full STT for command
- Play subtle audio cue when detected

VOSK MODEL SETUP:
1. Download model from: https://alphacephei.com/vosk/models
2. Recommended: vosk-model-small-en-us-0.15 (~40MB, fast)
3. Alternative: vosk-model-en-us-0.22 (~1GB, more accurate)
4. Extract to: models/vosk-model-small-en-us-0.15/
5. Model path configured at line 40 (MODEL_PATH)
"""

import os
import sys
import json
import queue
import threading
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

# Optional imports
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    import sounddevice as sd
    SD_AVAILABLE = True
except ImportError:
    SD_AVAILABLE = False


# Default wake words
WAKE_WORDS = ["cora", "hey cora", "yo cora", "okay cora", "hi cora"]

# Vosk model path (download from https://alphacephei.com/vosk/models)
MODEL_PATH = Path(__file__).parent.parent / 'models' / 'vosk-model-small-en-us-0.15'


@dataclass
class WakeWordResult:
    """Result of wake word detection."""
    detected: bool
    word: str
    confidence: float
    full_text: str
    timestamp: float


class WakeWordDetector:
    """Always-listening wake word detector using Vosk."""

    def __init__(
        self,
        wake_words: Optional[List[str]] = None,
        model_path: Optional[Path] = None,
        on_wake: Optional[Callable[[WakeWordResult], None]] = None,
        on_command: Optional[Callable[[str], None]] = None,
        sample_rate: int = 16000
    ):
        """Initialize wake word detector.

        Args:
            wake_words: List of wake words to detect
            model_path: Path to Vosk model
            on_wake: Callback when wake word detected
            on_command: Callback with full command after wake word
            sample_rate: Audio sample rate
        """
        self.wake_words = [w.lower() for w in (wake_words or WAKE_WORDS)]
        self.model_path = model_path or MODEL_PATH
        self.on_wake = on_wake
        self.on_command = on_command
        self.sample_rate = sample_rate

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._model = None
        self._recognizer = None

    def _load_model(self) -> bool:
        """Load Vosk model."""
        if not VOSK_AVAILABLE:
            print("[!] Vosk not available. Install with: pip install vosk")
            return False

        try:
            if not self.model_path.exists():
                print(f"[!] Vosk model not found at: {self.model_path}")
                print("[!] Download from: https://alphacephei.com/vosk/models")
                return False

            vosk.SetLogLevel(-1)  # Suppress Vosk logging
            self._model = vosk.Model(str(self.model_path))
            self._recognizer = vosk.KaldiRecognizer(self._model, self.sample_rate)
            return True

        except Exception as e:
            print(f"[!] Failed to load Vosk model: {e}")
            return False

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio input."""
        if status:
            print(f"[!] Audio status: {status}")
        self._audio_queue.put(bytes(indata))

    def _detect_wake_word(self, text: str) -> Optional[str]:
        """Check if text contains a wake word.

        Args:
            text: Recognized text

        Returns:
            Matched wake word or None
        """
        text_lower = text.lower().strip()

        for wake_word in self.wake_words:
            if wake_word in text_lower:
                return wake_word

        return None

    def _listen_loop(self):
        """Main listening loop."""
        if not SD_AVAILABLE:
            print("[!] sounddevice not available. Install with: pip install sounddevice")
            return

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self._audio_callback
            ):
                print(f"[WAKE] Listening for: {', '.join(self.wake_words)}")

                while self._running:
                    try:
                        data = self._audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    if self._recognizer.AcceptWaveform(data):
                        result = json.loads(self._recognizer.Result())
                        text = result.get('text', '')

                        if text:
                            wake_word = self._detect_wake_word(text)
                            if wake_word:
                                self._handle_wake(wake_word, text)

        except Exception as e:
            print(f"[!] Listen loop error: {e}")

    def _handle_wake(self, wake_word: str, full_text: str):
        """Handle wake word detection."""
        import time

        result = WakeWordResult(
            detected=True,
            word=wake_word,
            confidence=0.9,
            full_text=full_text,
            timestamp=time.time()
        )

        print(f"[WAKE] Detected: '{wake_word}' in '{full_text}'")

        # Play audio cue (if available)
        self._play_wake_sound()

        # Call wake callback
        if self.on_wake:
            self.on_wake(result)

        # Listen for command after wake word
        if self.on_command:
            command = self._listen_for_command()
            if command:
                self.on_command(command)

    def _listen_for_command(self, timeout: float = 5.0) -> Optional[str]:
        """Listen for command after wake word.

        Args:
            timeout: Max time to wait for command

        Returns:
            Command text or None
        """
        import time

        start = time.time()
        collected_text = []

        while time.time() - start < timeout:
            try:
                data = self._audio_queue.get(timeout=0.5)
            except queue.Empty:
                if collected_text:
                    break
                continue

            if self._recognizer.AcceptWaveform(data):
                result = json.loads(self._recognizer.Result())
                text = result.get('text', '')
                if text:
                    collected_text.append(text)
                    # If we got some text and there's a pause, we're done
                    break

        return ' '.join(collected_text) if collected_text else None

    def _play_wake_sound(self):
        """Play a subtle audio cue when wake word detected."""
        try:
            import winsound
            # Play a short beep (frequency 800Hz, duration 100ms)
            winsound.Beep(800, 100)
        except Exception:
            pass  # Silently fail if sound doesn't work

    def start(self) -> bool:
        """Start listening for wake words.

        Returns:
            True if started successfully
        """
        if self._running:
            return True

        if not self._load_model():
            return False

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop listening."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def is_running(self) -> bool:
        """Check if detector is running."""
        return self._running


# Simplified fallback without Vosk
class SimpleWakeWordDetector:
    """Simple wake word detector using speech_recognition (fallback)."""

    def __init__(
        self,
        wake_words: Optional[List[str]] = None,
        on_wake: Optional[Callable] = None,
        on_command: Optional[Callable[[str], None]] = None
    ):
        self.wake_words = [w.lower() for w in (wake_words or WAKE_WORDS)]
        self.on_wake = on_wake
        self.on_command = on_command
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _listen_loop(self):
        """Listening loop using speech_recognition."""
        try:
            import speech_recognition as sr
        except ImportError:
            print("[!] speech_recognition not available")
            return

        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"[WAKE] Listening for: {', '.join(self.wake_words)}")

            while self._running:
                try:
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio).lower()

                    for wake_word in self.wake_words:
                        if wake_word in text:
                            print(f"[WAKE] Detected: '{wake_word}'")
                            if self.on_wake:
                                self.on_wake(wake_word)
                            if self.on_command:
                                # Extract command after wake word
                                idx = text.find(wake_word) + len(wake_word)
                                command = text[idx:].strip()
                                if command:
                                    self.on_command(command)
                            break

                except Exception:
                    continue

    def start(self) -> bool:
        """Start listening."""
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop listening."""
        self._running = False


# Factory function
def create_wake_detector(**kwargs) -> WakeWordDetector:
    """Create appropriate wake word detector.

    Returns:
        WakeWordDetector instance
    """
    if VOSK_AVAILABLE:
        return WakeWordDetector(**kwargs)
    else:
        return SimpleWakeWordDetector(**kwargs)


if __name__ == "__main__":
    print("=== WAKE WORD DETECTOR TEST ===")

    def on_wake(result):
        print(f"Wake word detected: {result}")

    def on_command(cmd):
        print(f"Command: {cmd}")

    detector = create_wake_detector(
        on_wake=on_wake,
        on_command=on_command
    )

    if detector.start():
        print("Listening... Press Ctrl+C to stop")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            detector.stop()
    else:
        print("Failed to start detector")
