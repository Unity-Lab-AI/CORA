"""
C.O.R.A Speech-to-Text Module

Speech recognition wrapper using Vosk for offline speech-to-text.
Per ARCHITECTURE.md: Wake word detection, voice command processing.
"""

import json
import os
import queue
import threading
from pathlib import Path


def load_stt_settings():
    """Load STT settings from config/settings.json.

    Returns:
        dict: STT settings with sensitivity, wake_word, etc.
    """
    defaults = {
        'stt_enabled': False,
        'stt_sensitivity': 0.5,
        'wake_word': 'cora',
        'push_to_talk_key': 'ctrl+shift+space'
    }

    try:
        settings_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        if settings_path.exists():
            with open(settings_path) as f:
                data = json.load(f)
                voice = data.get('voice', {})
                return {
                    'stt_enabled': voice.get('stt_enabled', defaults['stt_enabled']),
                    'stt_sensitivity': voice.get('stt_sensitivity', defaults['stt_sensitivity']),
                    'wake_word': voice.get('wake_word', defaults['wake_word']),
                    'push_to_talk_key': voice.get('push_to_talk_key', defaults['push_to_talk_key'])
                }
    except Exception:
        pass

    return defaults


class SpeechRecognizer:
    """Speech recognition using Vosk (offline)."""

    def __init__(self, model_path=None, sample_rate=16000):
        """Initialize speech recognizer.

        Args:
            model_path: Path to Vosk model directory
            sample_rate: Audio sample rate (default 16000)
        """
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.recognizer = None
        self.model = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self._thread = None

    def initialize(self):
        """Initialize Vosk model and recognizer.

        Returns:
            bool: True if initialized successfully
        """
        try:
            from vosk import Model, KaldiRecognizer

            if self.model_path:
                self.model = Model(self.model_path)
            else:
                # Try to use small model
                self.model = Model(lang="en-us")

            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            return True
        except ImportError:
            print("[!] Vosk not installed. Run: pip install vosk")
            return False
        except Exception as e:
            print(f"[!] Failed to initialize STT: {e}")
            return False

    def recognize(self, audio_data):
        """Recognize speech from audio data.

        Args:
            audio_data: Raw audio bytes

        Returns:
            str: Recognized text or empty string
        """
        if not self.recognizer:
            return ""

        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            return result.get('text', '')
        else:
            # Partial result
            partial = json.loads(self.recognizer.PartialResult())
            return partial.get('partial', '')

    def start_listening(self, callback):
        """Start continuous listening in background thread.

        Args:
            callback: Function to call with recognized text
        """
        if self.is_listening:
            return

        self.is_listening = True
        self._thread = threading.Thread(target=self._listen_loop, args=(callback,))
        self._thread.daemon = True
        self._thread.start()

    def stop_listening(self):
        """Stop continuous listening."""
        self.is_listening = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def listen_once(self, timeout=5, phrase_limit=10):
        """Listen for a single phrase and return recognized text.

        This method is called by ui/app.py when the Mic button is clicked.

        Args:
            timeout: Maximum seconds to wait for speech (default 5)
            phrase_limit: Maximum seconds for a single phrase (default 10)

        Returns:
            str: Recognized text or empty string if nothing heard
        """
        if not self.initialize():
            return ""

        try:
            import sounddevice as sd
            import time

            # Reset recognizer to clear any buffered audio from wake word
            self.recognizer.Reset()

            # Collect audio for the duration
            audio_data = []
            start_time = time.time()
            has_speech = [False]  # Track if we've heard speech

            def audio_callback(indata, frames, time_info, status):
                if status:
                    pass  # Ignore status messages
                audio_data.append(bytes(indata))

            # Record audio - start immediately
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=4000,  # Smaller blocks for faster response
                dtype='int16',
                channels=1,
                callback=audio_callback
            ):
                # Wait for timeout or phrase_limit (whichever is shorter)
                listen_time = min(timeout, phrase_limit)
                while time.time() - start_time < listen_time:
                    time.sleep(0.05)  # Check more frequently

            # Process collected audio
            if not audio_data:
                return ""

            # Feed all audio to recognizer
            for chunk in audio_data:
                self.recognizer.AcceptWaveform(chunk)

            # Get final result
            import json
            result = json.loads(self.recognizer.FinalResult())
            return result.get('text', '')

        except ImportError:
            print("[!] sounddevice not installed")
            return ""
        except Exception as e:
            print(f"[!] Listen error: {e}")
            return ""

    def _listen_loop(self, callback):
        """Internal listening loop."""
        try:
            import sounddevice as sd

            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"[!] Audio status: {status}")
                self.audio_queue.put(bytes(indata))

            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=audio_callback
            ):
                while self.is_listening:
                    try:
                        data = self.audio_queue.get(timeout=0.5)
                        text = self.recognize(data)
                        if text.strip():
                            callback(text)
                    except queue.Empty:
                        continue
        except ImportError:
            print("[!] sounddevice not installed. Run: pip install sounddevice")
        except Exception as e:
            print(f"[!] Listening error: {e}")


class WakeWordDetector:
    """Detect wake word in audio stream."""

    # Class-level buffer of recent transcripts (shared across instances)
    _recent_transcripts = []
    _max_transcripts = 20  # Keep last 20 phrases
    _transcript_lock = threading.Lock()

    # Callbacks for when new transcripts are added (for ambient awareness)
    _transcript_callbacks = []
    _callback_lock = threading.Lock()

    def __init__(self, wake_word=None, sensitivity=None):
        """Initialize wake word detector.

        Args:
            wake_word: Word to listen for (default from settings or "cora")
            sensitivity: Detection sensitivity 0.0-1.0 (default from settings or 0.5)
        """
        # Load from settings if not specified
        settings = load_stt_settings()
        self.wake_word = (wake_word or settings['wake_word']).lower()
        self.sensitivity = sensitivity if sensitivity is not None else settings['stt_sensitivity']
        self.recognizer = SpeechRecognizer()

    def start(self, on_wake):
        """Start listening for wake word.

        Args:
            on_wake: Callback when wake word detected
        """
        if not self.recognizer.initialize():
            print("[!] Cannot start wake word detection")
            return

        def check_wake(text):
            text_lower = text.lower().strip()

            # Store all transcripts in buffer (before checking for wake word)
            if text_lower and text_lower != self.wake_word:
                with WakeWordDetector._transcript_lock:
                    import time
                    WakeWordDetector._recent_transcripts.append({
                        'text': text,
                        'time': time.time()
                    })
                    # Keep only recent transcripts
                    if len(WakeWordDetector._recent_transcripts) > WakeWordDetector._max_transcripts:
                        WakeWordDetector._recent_transcripts.pop(0)

                # Notify ambient awareness and other listeners
                WakeWordDetector._notify_transcript_callbacks(text)

            if self.wake_word in text_lower:
                on_wake()

        self.recognizer.start_listening(check_wake)

    def stop(self):
        """Stop listening for wake word."""
        self.recognizer.stop_listening()

    @classmethod
    def get_recent_transcripts(cls, seconds: float = 30.0) -> list:
        """Get transcripts from the last N seconds before wake word.

        Args:
            seconds: How far back to look (default 30 seconds)

        Returns:
            list of transcript strings
        """
        import time
        cutoff = time.time() - seconds

        with cls._transcript_lock:
            recent = [t['text'] for t in cls._recent_transcripts if t['time'] > cutoff]
            return recent

    @classmethod
    def get_last_heard(cls) -> str:
        """Get a summary of what was heard recently.

        Returns:
            str: Summary of recent speech or "nothing" if buffer is empty
        """
        transcripts = cls.get_recent_transcripts(seconds=30.0)
        if transcripts:
            # Join recent transcripts, remove duplicates
            seen = set()
            unique = []
            for t in transcripts:
                t_clean = t.strip().lower()
                if t_clean and t_clean not in seen:
                    seen.add(t_clean)
                    unique.append(t.strip())
            if unique:
                return ' '.join(unique[-5:])  # Last 5 unique phrases
        return ""

    @classmethod
    def clear_transcripts(cls):
        """Clear the transcript buffer."""
        with cls._transcript_lock:
            cls._recent_transcripts.clear()

    @classmethod
    def add_transcript_callback(cls, callback):
        """Register a callback to be notified when new transcripts are added.

        Args:
            callback: Function that takes (text: str) as argument
        """
        with cls._callback_lock:
            cls._transcript_callbacks.append(callback)

    @classmethod
    def remove_transcript_callback(cls, callback):
        """Remove a transcript callback."""
        with cls._callback_lock:
            if callback in cls._transcript_callbacks:
                cls._transcript_callbacks.remove(callback)

    @classmethod
    def _notify_transcript_callbacks(cls, text: str):
        """Notify all registered callbacks of new transcript."""
        with cls._callback_lock:
            callbacks = list(cls._transcript_callbacks)
        for callback in callbacks:
            try:
                callback(text)
            except Exception as e:
                print(f"[!] Transcript callback error: {e}")


def transcribe_file(audio_file, model_path=None):
    """Transcribe an audio file.

    Args:
        audio_file: Path to audio file (WAV format)
        model_path: Path to Vosk model

    Returns:
        str: Transcribed text
    """
    try:
        from vosk import Model, KaldiRecognizer
        import wave

        if model_path:
            model = Model(model_path)
        else:
            model = Model(lang="en-us")

        wf = wave.open(audio_file, "rb")
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                results.append(result.get('text', ''))

        # Final result
        final = json.loads(rec.FinalResult())
        results.append(final.get('text', ''))

        return ' '.join(results).strip()

    except ImportError:
        print("[!] Vosk not installed")
        return ""
    except Exception as e:
        print(f"[!] Transcription error: {e}")
        return ""


def list_microphones():
    """List available microphones.

    Returns:
        list: Available input devices
    """
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        inputs = []
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                inputs.append({
                    'id': i,
                    'name': d['name'],
                    'channels': d['max_input_channels'],
                    'sample_rate': d['default_samplerate']
                })
        return inputs
    except ImportError:
        return []
