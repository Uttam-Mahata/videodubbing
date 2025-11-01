"""Voice configuration models"""

from pydantic import BaseModel, Field
from enum import Enum


class VoiceStyle(str, Enum):
    """Voice style characteristics"""
    BRIGHT = "Bright"
    UPBEAT = "Upbeat"
    INFORMATIVE = "Informative"
    FIRM = "Firm"
    EXCITABLE = "Excitable"
    YOUTHFUL = "Youthful"
    BREEZY = "Breezy"
    EASY_GOING = "Easy-going"
    BREATHY = "Breathy"
    CLEAR = "Clear"
    SMOOTH = "Smooth"
    GRAVELLY = "Gravelly"
    SOFT = "Soft"
    EVEN = "Even"
    MATURE = "Mature"
    FORWARD = "Forward"
    FRIENDLY = "Friendly"
    CASUAL = "Casual"
    GENTLE = "Gentle"
    LIVELY = "Lively"
    KNOWLEDGEABLE = "Knowledgeable"
    WARM = "Warm"


class VoiceOption(BaseModel):
    """Available voice option with metadata"""
    name: str = Field(..., description="Voice name")
    style: VoiceStyle = Field(..., description="Voice style characteristic")
    language_support: list[str] = Field(default_factory=list, description="Supported languages")
    sample_url: Optional[str] = Field(default=None, description="Sample audio URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Kore",
                "style": "Firm",
                "language_support": ["en-US", "es-ES"],
                "sample_url": "https://example.com/samples/kore.mp3"
            }
        }


class VoiceConfig(BaseModel):
    """Voice configuration for synthesis"""
    voice_name: str = Field(..., description="Selected voice name")
    emotion: Optional[str] = Field(default=None, description="Emotion to convey")
    pace: Optional[str] = Field(default="normal", description="Speech pace: slow, normal, fast")
    pitch: Optional[float] = Field(default=1.0, description="Pitch adjustment", ge=0.5, le=2.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "voice_name": "Kore",
                "emotion": "cheerful",
                "pace": "normal",
                "pitch": 1.0
            }
        }


# All 30 voice options from Gemini TTS
AVAILABLE_VOICES: dict[str, VoiceStyle] = {
    "Zephyr": VoiceStyle.BRIGHT,
    "Puck": VoiceStyle.UPBEAT,
    "Charon": VoiceStyle.INFORMATIVE,
    "Kore": VoiceStyle.FIRM,
    "Fenrir": VoiceStyle.EXCITABLE,
    "Leda": VoiceStyle.YOUTHFUL,
    "Orus": VoiceStyle.FIRM,
    "Aoede": VoiceStyle.BREEZY,
    "Callirrhoe": VoiceStyle.EASY_GOING,
    "Autonoe": VoiceStyle.BRIGHT,
    "Enceladus": VoiceStyle.BREATHY,
    "Iapetus": VoiceStyle.CLEAR,
    "Umbriel": VoiceStyle.EASY_GOING,
    "Algieba": VoiceStyle.SMOOTH,
    "Despina": VoiceStyle.SMOOTH,
    "Erinome": VoiceStyle.CLEAR,
    "Algenib": VoiceStyle.GRAVELLY,
    "Rasalgethi": VoiceStyle.INFORMATIVE,
    "Laomedeia": VoiceStyle.UPBEAT,
    "Achernar": VoiceStyle.SOFT,
    "Alnilam": VoiceStyle.FIRM,
    "Schedar": VoiceStyle.EVEN,
    "Gacrux": VoiceStyle.MATURE,
    "Pulcherrima": VoiceStyle.FORWARD,
    "Achird": VoiceStyle.FRIENDLY,
    "Zubenelgenubi": VoiceStyle.CASUAL,
    "Vindemiatrix": VoiceStyle.GENTLE,
    "Sadachbia": VoiceStyle.LIVELY,
    "Sadaltager": VoiceStyle.KNOWLEDGEABLE,
    "Sulafat": VoiceStyle.WARM,
}


# Supported languages for TTS
SUPPORTED_LANGUAGES = [
    "ar-EG", "de-DE", "en-US", "es-US", "fr-FR", "hi-IN",
    "id-ID", "it-IT", "ja-JP", "ko-KR", "pt-BR", "ru-RU",
    "nl-NL", "pl-PL", "th-TH", "tr-TR", "vi-VN", "ro-RO",
    "uk-UA", "bn-BD", "en-IN", "mr-IN", "ta-IN", "te-IN"
]
