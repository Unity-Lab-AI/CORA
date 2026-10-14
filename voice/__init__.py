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
    UnityVoiceTTS,
    get_tts_engine,
    speak,
    speak_async,
    queue_speak,
    speak_interrupt,
    stop_speaking,
    is_speaking,
    list_voices,
    voice_status,
)

# Legacy names kept so older call sites keep working (they get her voice).
KokoroTTS = UnityVoiceTTS
Pyttsx3TTS = UnityVoiceTTS

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
    'UnityVoiceTTS',
    'KokoroTTS',
    'Pyttsx3TTS',
    'get_tts_engine',
    'speak',
    'speak_async',
    'queue_speak',
    'speak_interrupt',
    'stop_speaking',
    'is_speaking',
    'list_voices',
    'voice_status',
]
