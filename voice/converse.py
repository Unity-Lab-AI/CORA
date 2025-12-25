#!/usr/bin/env python3
"""
C.O.R.A Conversation Mode
Full conversation loop with wake word + echo filtering

Per ARCHITECTURE.md v1.0.0:
- Listen for wake word
- Filter out CORA's own speech (echo filtering)
- Process user speech
- Respond via AI callback
- Loop until stop word
"""

import os
import sys
import time
import threading
import queue
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

# Optional imports
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


# Stop words to end conversation
STOP_WORDS = ["goodbye", "bye", "stop", "shut up", "exit", "quit", "that's all"]

# Project root
PROJECT_DIR = Path(__file__).parent.parent


@dataclass
class ConversationConfig:
    """Configuration for conversation mode."""
    wake_word: str = "cora"
    stop_words: List[str] = None
    silence_timeout: float = 2.0  # Seconds of silence before processing
    phrase_timeout: float = 10.0  # Max phrase length
    energy_threshold: int = 300  # Microphone sensitivity
    echo_filter_duration: float = 3.0  # Ignore audio for N seconds after TTS

    def __post_init__(self):
        if self.stop_words is None:
            self.stop_words = STOP_WORDS


class EchoFilter:
    """Filters out CORA's own speech from microphone input."""

    def __init__(self, filter_duration: float = 3.0):
        """Initialize echo filter.

        Args:
            filter_duration: Seconds to filter after TTS starts
        """
        self.filter_duration = filter_duration
        self._speaking_until = 0.0
        self._lock = threading.Lock()

    def start_speaking(self, duration: float = None):
        """Mark that TTS is starting.

        Args:
            duration: Expected speech duration (or use default)
        """
        with self._lock:
            self._speaking_until = time.time() + (duration or self.filter_duration)

    def stop_speaking(self):
        """Mark that TTS has stopped."""
        with self._lock:
            self._speaking_until = 0.0

    def is_speaking(self) -> bool:
        """Check if CORA is currently speaking.

        Returns:
            True if speaking (should filter input)
        """
        with self._lock:
            return time.time() < self._speaking_until

    def should_process(self, text: str) -> bool:
        """Check if input should be processed.

        Args:
            text: Recognized text

        Returns:
            True if should process (not echo)
        """
        if self.is_speaking():
            return False

        # Additional echo detection (if text matches common TTS patterns)
        # This helps catch delayed recognition of TTS output
        return True


class ConversationLoop:
    """Full conversation loop with CORA."""

    def __init__(
        self,
        config: Optional[ConversationConfig] = None,
        ai_callback: Optional[Callable[[str], str]] = None,
        speak_callback: Optional[Callable[[str], None]] = None,
        on_wake: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None
    ):
        """Initialize conversation loop.

        Args:
            config: Conversation configuration
            ai_callback: Function to get AI response (takes text, returns response)
            speak_callback: Function to speak text (TTS)
            on_wake: Called when wake word detected
            on_stop: Called when conversation ends
        """
        self.config = config or ConversationConfig()
        self.ai_callback = ai_callback
        self.speak_callback = speak_callback
        self.on_wake = on_wake
        self.on_stop = on_stop

        self.echo_filter = EchoFilter(self.config.echo_filter_duration)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._recognizer = None
        self._microphone = None

    def _init_speech(self) -> bool:
        """Initialize speech recognition."""
        if not SR_AVAILABLE:
            print("[!] speech_recognition not available")
            return False

        try:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = self.config.energy_threshold
            self._recognizer.pause_threshold = self.config.silence_timeout
            self._microphone = sr.Microphone()

            # Calibrate for ambient noise
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=1)

            return True
        except Exception as e:
            print(f"[!] Speech init error: {e}")
            return False

    def _listen_once(self) -> Optional[str]:
        """Listen for a single phrase.

        Returns:
            Recognized text or None
        """
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=self.config.phrase_timeout
                )

            # Use Google Speech Recognition
            text = self._recognizer.recognize_google(audio)
            return text.lower().strip()

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"[!] Listen error: {e}")
            return None

    def _is_wake_word(self, text: str) -> bool:
        """Check if text contains wake word."""
        return self.config.wake_word.lower() in text.lower()

    def _is_stop_word(self, text: str) -> bool:
        """Check if text contains stop word."""
        text_lower = text.lower()
        return any(stop in text_lower for stop in self.config.stop_words)

    def _process_input(self, text: str) -> Optional[str]:
        """Process user input and get AI response.

        Args:
            text: User's spoken text

        Returns:
            AI response or None
        """
        if not self.echo_filter.should_process(text):
            return None

        if self.ai_callback:
            return self.ai_callback(text)
        return None

    def _speak(self, text: str):
        """Speak response with echo filtering."""
        if self.speak_callback:
            # Estimate speech duration (rough: 1 second per 10 characters)
            duration = len(text) / 10.0
            self.echo_filter.start_speaking(duration)

            try:
                self.speak_callback(text)
            finally:
                self.echo_filter.stop_speaking()

    def _conversation_loop(self):
        """Main conversation loop."""
        print(f"[CONVERSE] Listening for wake word: '{self.config.wake_word}'")
        print(f"[CONVERSE] Say {self.config.stop_words[:3]} to end")

        wake_detected = False

        while self._running:
            text = self._listen_once()

            if text is None:
                continue

            print(f"[HEARD] {text}")

            # Skip if echo filter active
            if not self.echo_filter.should_process(text):
                print("[ECHO] Filtered (CORA speaking)")
                continue

            # Check for stop word
            if self._is_stop_word(text):
                self._speak("Alright, catch you later.")
                if self.on_stop:
                    self.on_stop()
                break

            # If not wake mode, check for wake word
            if not wake_detected:
                if self._is_wake_word(text):
                    wake_detected = True
                    if self.on_wake:
                        self.on_wake()
                    self._speak("Yeah?")

                    # Extract command after wake word
                    idx = text.lower().find(self.config.wake_word) + len(self.config.wake_word)
                    command = text[idx:].strip()

                    if command:
                        response = self._process_input(command)
                        if response:
                            self._speak(response)
                continue

            # In active conversation
            response = self._process_input(text)
            if response:
                self._speak(response)

    def start(self) -> bool:
        """Start conversation loop.

        Returns:
            True if started successfully
        """
        if self._running:
            return True

        if not self._init_speech():
            return False

        self._running = True
        self._thread = threading.Thread(target=self._conversation_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop conversation loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def is_running(self) -> bool:
        """Check if conversation is active."""
        return self._running


def quick_converse(
    ai_callback: Callable[[str], str],
    speak_callback: Optional[Callable[[str], None]] = None
) -> ConversationLoop:
    """Start a quick conversation with minimal setup.

    Args:
        ai_callback: Function to get AI responses
        speak_callback: Optional TTS function

    Returns:
        Running ConversationLoop
    """
    loop = ConversationLoop(
        ai_callback=ai_callback,
        speak_callback=speak_callback
    )
    loop.start()
    return loop


if __name__ == "__main__":
    print("=== CONVERSATION MODE TEST ===")

    if not SR_AVAILABLE:
        print("[!] Install: pip install SpeechRecognition pyaudio")
        sys.exit(1)

    # Simple echo callback for testing
    def echo_ai(text: str) -> str:
        return f"You said: {text}"

    def print_speak(text: str):
        print(f"[SPEAK] {text}")

    loop = ConversationLoop(
        ai_callback=echo_ai,
        speak_callback=print_speak,
        on_wake=lambda: print("[WAKE] Activated!"),
        on_stop=lambda: print("[STOP] Conversation ended")
    )

    if loop.start():
        print("Say 'Cora' to start, 'goodbye' to stop")
        try:
            while loop.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            loop.stop()
    else:
        print("Failed to start")
