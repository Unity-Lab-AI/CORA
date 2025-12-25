"""
C.O.R.A Text-to-Speech Module

TTS wrapper supporting Kokoro and pyttsx3 engines.
Per ARCHITECTURE.md: Emotion-aware TTS with af_bella voice.

Includes TTSQueue for non-blocking speech with queue management.
"""

import os
import queue
import subprocess
import tempfile
import threading
from typing import Optional, Callable

# Import TTS mutex for preventing overlapping speech
try:
    from voice.tts_mutex import get_mutex, speak_with_mutex
    TTS_MUTEX_AVAILABLE = True
except ImportError:
    TTS_MUTEX_AVAILABLE = False

# Import presence detection for "speak only when present"
try:
    from services.presence import check_human_present
    PRESENCE_AVAILABLE = True
except ImportError:
    PRESENCE_AVAILABLE = False


class TTSEngine:
    """Base TTS engine interface."""

    def __init__(self):
        self.is_initialized = False

    def initialize(self):
        """Initialize the TTS engine."""
        raise NotImplementedError

    def speak(self, text, emotion='neutral'):
        """Speak text with optional emotion."""
        raise NotImplementedError

    def get_audio(self, text, emotion='neutral'):
        """Get audio data without playing."""
        raise NotImplementedError


class KokoroTTS(TTSEngine):
    """Kokoro TTS engine (high-quality neural voice - af_bella)."""

    def __init__(self, voice='af_bella', speed=1.0):
        """Initialize Kokoro TTS.

        Args:
            voice: Voice ID (af_bella, af_heart, etc.)
            speed: Speech speed multiplier
        """
        super().__init__()
        self.voice = voice
        self.speed = speed
        self.pipeline = None

    def initialize(self):
        """Initialize Kokoro engine.

        Returns:
            bool: True if initialized successfully
        """
        try:
            from kokoro import KPipeline
            import sounddevice as sd
            # Initialize pipeline for English with American voice
            self.pipeline = KPipeline(lang_code='a')
            self.sd = sd
            self.is_initialized = True
            return True
        except ImportError as e:
            print(f"[!] Kokoro dependencies missing: {e}")
            print("[!] Run: pip install kokoro sounddevice")
            return False
        except Exception as e:
            print(f"[!] Failed to initialize Kokoro: {e}")
            return False

    def speak(self, text, emotion='neutral'):
        """Speak text with emotion.

        Args:
            text: Text to speak
            emotion: Emotion type (neutral, excited, concerned, etc.)

        Returns:
            bool: True if spoken successfully
        """
        if not self.is_initialized:
            if not self.initialize():
                return False

        try:
            # Clean text for TTS - remove action markers like *sighs* or *lights cigarette*
            import re
            clean_text = re.sub(r'\*[^*]+\*', '', text)  # Remove *action* markers
            clean_text = re.sub(r'_[^_]+_', '', clean_text)  # Remove _italic_ markers
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Clean up extra spaces

            if not clean_text:
                return True  # Nothing to speak after cleaning

            # Get speed modifier based on emotion
            speed = self._get_emotion_speed(emotion)

            # Generate audio using Kokoro pipeline
            for result in self.pipeline(clean_text, voice=self.voice, speed=speed):
                if result.audio is not None:
                    # Share audio data with waveform visualizer BEFORE playing
                    try:
                        import sys
                        from pathlib import Path
                        # Add project root to path
                        project_dir = Path(__file__).parent.parent
                        if str(project_dir) not in sys.path:
                            sys.path.insert(0, str(project_dir))
                        from ui.boot_display import set_audio_data, clear_audio_data
                        # Set audio data - waveform will read from this during playback
                        audio_len = len(result.audio) if result.audio is not None else 0
                        audio_max = float(max(abs(result.audio))) if audio_len > 0 else 0
                        print(f"[WAVEFORM] Setting audio: {audio_len} samples, max amplitude: {audio_max:.4f}")
                        set_audio_data(result.audio, sample_rate=24000)
                    except Exception as e:
                        print(f"[DEBUG] Waveform audio share failed: {e}")

                    # Play audio at 24kHz sample rate
                    self.sd.play(result.audio, samplerate=24000)
                    self.sd.wait()  # Block until audio finishes

                    # Clear audio data AFTER playback is done
                    try:
                        from ui.boot_display import clear_audio_data
                        clear_audio_data()
                    except:
                        pass
            return True
        except Exception as e:
            print(f"[!] Kokoro TTS error: {e}")
            return False

    def get_audio(self, text, emotion='neutral'):
        """Get audio data as numpy array.

        Args:
            text: Text to convert
            emotion: Emotion type

        Returns:
            numpy array: Audio data or None
        """
        if not self.is_initialized:
            if not self.initialize():
                return None

        try:
            import numpy as np
            speed = self._get_emotion_speed(emotion)
            audio_chunks = []

            for result in self.pipeline(text, voice=self.voice, speed=speed):
                if result.audio is not None:
                    audio_chunks.append(result.audio)

            if audio_chunks:
                return np.concatenate(audio_chunks)
            return None
        except Exception as e:
            print(f"[!] Audio generation error: {e}")
            return None

    def _get_emotion_speed(self, emotion):
        """Get speed modifier for emotion.

        Args:
            emotion: Emotion type

        Returns:
            float: Speed modifier
        """
        speeds = {
            'excited': 1.15,
            'urgent': 1.2,
            'annoyed': 1.05,
            'concerned': 0.95,
            'caring': 0.9,
            'playful': 1.1,
            'sarcastic': 0.95,
            'neutral': 1.0,
        }
        return speeds.get(emotion, self.speed)


class Pyttsx3TTS(TTSEngine):
    """pyttsx3 TTS engine (fallback, offline)."""

    def __init__(self, rate=150, volume=1.0, voice_id=None):
        """Initialize pyttsx3 TTS.

        Args:
            rate: Speech rate (words per minute)
            volume: Volume (0.0 to 1.0)
            voice_id: Specific voice ID (optional)
        """
        super().__init__()
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.engine = None

    def initialize(self):
        """Initialize pyttsx3 engine.

        Returns:
            bool: True if initialized successfully
        """
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)

            # Set voice if specified
            if self.voice_id:
                self.engine.setProperty('voice', self.voice_id)
            else:
                # Try to use a female voice
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break

            self.is_initialized = True
            return True
        except ImportError:
            print("[!] pyttsx3 not installed. Run: pip install pyttsx3")
            return False
        except Exception as e:
            print(f"[!] Failed to initialize pyttsx3: {e}")
            return False

    def speak(self, text, emotion='neutral'):
        """Speak text (emotion affects rate/pitch).

        Args:
            text: Text to speak
            emotion: Emotion type

        Returns:
            bool: True if spoken successfully
        """
        if not self.is_initialized:
            if not self.initialize():
                return False

        try:
            # Adjust rate based on emotion
            rate_mod = self._get_emotion_rate_mod(emotion)
            self.engine.setProperty('rate', self.rate + rate_mod)

            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            print(f"[!] TTS error: {e}")
            return False

    def get_audio(self, text, emotion='neutral'):
        """Save audio to temporary file and return path.

        Args:
            text: Text to convert
            emotion: Emotion type

        Returns:
            str: Path to audio file or None
        """
        if not self.is_initialized:
            if not self.initialize():
                return None

        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name

            rate_mod = self._get_emotion_rate_mod(emotion)
            self.engine.setProperty('rate', self.rate + rate_mod)
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            return temp_path
        except Exception as e:
            print(f"[!] Audio save error: {e}")
            return None

    def _get_emotion_rate_mod(self, emotion):
        """Get rate modifier for emotion.

        Args:
            emotion: Emotion type

        Returns:
            int: Rate adjustment
        """
        mods = {
            'excited': 20,
            'urgent': 30,
            'annoyed': 10,
            'concerned': -10,
            'caring': -15,
            'playful': 15,
            'sarcastic': -5,
            'neutral': 0,
        }
        return mods.get(emotion, 0)


def get_tts_engine(config=None):
    """Get appropriate TTS engine based on config.

    CORA always uses Kokoro (af_bella voice) by default.

    Args:
        config: Configuration dict with TTS settings

    Returns:
        TTSEngine: Initialized TTS engine
    """
    if config is None:
        config = {}

    tts_config = config.get('tts', {})
    # Default to Kokoro (sexy af_bella voice) - CORA's signature voice
    engine_name = tts_config.get('engine', 'kokoro')

    if engine_name == 'kokoro':
        voice = tts_config.get('kokoro', {}).get('voice', 'af_bella')
        speed = tts_config.get('kokoro', {}).get('speed', 1.0)
        engine = KokoroTTS(voice=voice, speed=speed)
        if engine.initialize():
            return engine
        # Fallback to pyttsx3 if Kokoro fails
        print("[!] Kokoro failed, falling back to pyttsx3")

    # pyttsx3 fallback
    rate = tts_config.get('rate', 150)
    volume = tts_config.get('volume', 1.0)
    fallback = Pyttsx3TTS(rate=rate, volume=volume)
    if fallback.initialize():
        return fallback

    return None


def speak(text, emotion='neutral', config=None):
    """Quick speak function.

    Args:
        text: Text to speak
        emotion: Emotion type
        config: Optional config dict

    Returns:
        bool: True if spoken successfully
    """
    engine = get_tts_engine(config)
    if engine:
        return engine.speak(text, emotion)
    return False


def list_voices():
    """List available pyttsx3 voices.

    Returns:
        list: Available voice info
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        return [{'id': v.id, 'name': v.name, 'languages': v.languages}
                for v in voices]
    except Exception:
        return []


# ============ TTS QUEUE (Non-blocking speech) ============

class TTSQueue:
    """Queue-based TTS for non-blocking speech.

    Queues multiple TTS requests and processes them in order.
    Runs in a background thread to not block the main application.
    Uses TTS mutex to prevent overlapping speech across processes.
    """

    def __init__(self, config=None, use_mutex: bool = True, check_presence: bool = True):
        """Initialize TTS queue.

        Args:
            config: TTS configuration dict
            use_mutex: Whether to use TTS mutex (prevents overlapping)
            check_presence: Whether to check if user is present before speaking
        """
        self.config = config or {}
        self.queue = queue.Queue()
        self.engine = None
        self.is_running = False
        self._thread = None
        self._stop_event = threading.Event()
        self.on_speak_start: Optional[Callable] = None
        self.on_speak_end: Optional[Callable] = None
        self.use_mutex = use_mutex and TTS_MUTEX_AVAILABLE
        self._mutex = None
        self.check_presence = check_presence and PRESENCE_AVAILABLE
        self._last_presence_check = 0
        self._presence_cache_seconds = 5  # Cache presence result for 5 seconds

        if self.use_mutex:
            self._mutex = get_mutex("CORA")

    def start(self):
        """Start the TTS queue processing thread."""
        if self.is_running:
            return

        self.engine = get_tts_engine(self.config)
        if not self.engine:
            print("[!] TTS engine failed to initialize")
            return

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._process_queue, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the TTS queue processing thread."""
        self._stop_event.set()
        self.is_running = False
        # Add None to wake up the queue
        self.queue.put(None)
        if self._thread:
            self._thread.join(timeout=2.0)

    def speak(self, text: str, emotion: str = 'neutral', priority: int = 5):
        """Add text to speak queue.

        Args:
            text: Text to speak
            emotion: Emotion for TTS
            priority: 1-10 (1=highest, processed first)
        """
        if not self.is_running:
            self.start()

        self.queue.put({
            'text': text,
            'emotion': emotion,
            'priority': priority
        })

    def speak_now(self, text: str, emotion: str = 'neutral'):
        """Interrupt current speech and speak immediately.

        Args:
            text: Text to speak
            emotion: Emotion for TTS
        """
        # Clear existing queue
        self.clear()
        # Add with highest priority
        self.speak(text, emotion, priority=1)

    def clear(self):
        """Clear all pending items from the queue."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def pending_count(self) -> int:
        """Get number of items waiting in queue."""
        return self.queue.qsize()

    def _is_user_present(self) -> bool:
        """Check if user is present (cached for performance).

        Returns:
            bool: True if user is present or presence check disabled
        """
        import time as time_module
        if not self.check_presence:
            return True

        # Check cache
        now = time_module.time()
        if now - self._last_presence_check < self._presence_cache_seconds:
            return getattr(self, '_presence_cache', True)

        # Do fresh check
        try:
            result = check_human_present()
            self._presence_cache = result.present
            self._last_presence_check = now
            return result.present
        except Exception:
            # On error, assume present
            return True

    def _process_queue(self):
        """Process queue items in background thread."""
        while not self._stop_event.is_set():
            try:
                item = self.queue.get(timeout=0.5)
                if item is None:
                    continue

                text = item.get('text', '')
                emotion = item.get('emotion', 'neutral')
                skip_presence = item.get('skip_presence', False)

                # Check if user is present before speaking
                if not skip_presence and not self._is_user_present():
                    print(f"[TTS] User not present, skipping: {text[:30]}...")
                    continue

                if text and self.engine:
                    # Callback for speech start
                    if self.on_speak_start:
                        self.on_speak_start(text)

                    # Speak with or without mutex
                    if self.use_mutex and self._mutex:
                        # Use mutex to prevent overlapping speech
                        with self._mutex.locked(timeout=10) as acquired:
                            if acquired:
                                self.engine.speak(text, emotion)
                            else:
                                print(f"[TTS] Skipped (someone else speaking): {text[:30]}...")
                    else:
                        # No mutex, speak directly
                        self.engine.speak(text, emotion)

                    # Callback for speech end
                    if self.on_speak_end:
                        self.on_speak_end(text)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[!] TTS queue error: {e}")


# Global TTS queue instance
_tts_queue: Optional[TTSQueue] = None


def get_tts_queue(config=None) -> TTSQueue:
    """Get or create the global TTS queue.

    Args:
        config: TTS configuration

    Returns:
        TTSQueue instance
    """
    global _tts_queue
    if _tts_queue is None:
        _tts_queue = TTSQueue(config)
        _tts_queue.start()
    return _tts_queue


def queue_speak(text: str, emotion: str = 'neutral', priority: int = 5):
    """Queue text for speaking (non-blocking).

    Args:
        text: Text to speak
        emotion: Emotion type
        priority: 1-10 (1=highest)
    """
    tts = get_tts_queue()
    tts.speak(text, emotion, priority)


def speak_interrupt(text: str, emotion: str = 'neutral'):
    """Clear queue and speak immediately.

    Args:
        text: Text to speak
        emotion: Emotion type
    """
    tts = get_tts_queue()
    tts.speak_now(text, emotion)
