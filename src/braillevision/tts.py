"""Optional server-side text-to-speech helpers."""

from __future__ import annotations

from pathlib import Path


def speak_offline(text: str) -> bool:
    """Speak text with pyttsx3 when installed."""

    try:
        import pyttsx3
    except Exception:
        return False
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return True


def save_speech_mp3(text: str, path: str | Path) -> bool:
    """Save speech with gTTS when installed and network is available."""

    try:
        from gtts import gTTS
    except Exception:
        return False
    tts = gTTS(text=text, lang="en")
    tts.save(str(path))
    return True
