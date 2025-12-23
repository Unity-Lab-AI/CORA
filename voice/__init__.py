"""
C.O.R.A Voice Module

Speech-to-text, text-to-speech, and emotion detection.
"""

from .emotion import (
    detect_emotion,
    get_emotion_instruction,
    analyze_emotional_context,
    get_voice_params,
    EMOTION_KEYWORDS,
    EMOTION_VOICE_PARAMS
)

from .stt import (
    SpeechRecognizer,
    WakeWordDetector,
    transcribe_file,
    list_microphones
)

from .tts import (
    TTSEngine,
    KokoroTTS,
    Pyttsx3TTS,
    get_tts_engine,
    speak,
    list_voices
)

__all__ = [
    # Emotion
    'detect_emotion',
    'get_emotion_instruction',
    'analyze_emotional_context',
    'get_voice_params',
    'EMOTION_KEYWORDS',
    'EMOTION_VOICE_PARAMS',
    # STT
    'SpeechRecognizer',
    'WakeWordDetector',
    'transcribe_file',
    'list_microphones',
    # TTS
    'TTSEngine',
    'KokoroTTS',
    'Pyttsx3TTS',
    'get_tts_engine',
    'speak',
    'list_voices',
]
