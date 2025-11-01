"""
Voice Configuration Endpoints
Available voices and language support
"""

from fastapi import APIRouter
from typing import List

from backend.models.voice import VoiceOption, VoiceStyle, AVAILABLE_VOICES, SUPPORTED_LANGUAGES

router = APIRouter()


@router.get("/voices", response_model=List[VoiceOption])
async def list_voices():
    """
    List all available TTS voices
    
    **Returns:**
    - Voice name
    - Style characteristic
    - Language support
    - Sample URL
    
    **Cache:** 1 hour
    """
    voices = [
        VoiceOption(
            name=name,
            style=style,
            language_support=SUPPORTED_LANGUAGES[:5],  # Mock: first 5 languages
            sample_url=f"https://example.com/samples/{name.lower()}.mp3"
        )
        for name, style in AVAILABLE_VOICES.items()
    ]
    
    return voices


@router.get("/languages")
async def list_languages():
    """
    List supported languages
    
    **Returns:**
    - Language code (BCP-47)
    - Language name
    - TTS support
    - Audio understanding support
    
    **Cache:** 1 hour
    """
    # Language code to name mapping (subset)
    language_names = {
        "en-US": "English (US)",
        "es-US": "Spanish (US)",
        "fr-FR": "French (France)",
        "de-DE": "German (Germany)",
        "ja-JP": "Japanese (Japan)",
        "ko-KR": "Korean (Korea)",
        "pt-BR": "Portuguese (Brazil)",
        "hi-IN": "Hindi (India)",
        "ar-EG": "Arabic (Egyptian)",
        "ru-RU": "Russian (Russia)",
    }
    
    languages = [
        {
            "code": code,
            "name": language_names.get(code, code),
            "tts_support": True,
            "audio_support": True,
        }
        for code in SUPPORTED_LANGUAGES
    ]
    
    return {"languages": languages}
