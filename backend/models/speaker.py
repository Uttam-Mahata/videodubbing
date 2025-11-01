"""Speaker analysis and voice mapping models"""

from pydantic import BaseModel, Field
from typing import Optional


class SpeakerProfile(BaseModel):
    """Profile for an identified speaker"""
    speaker_id: str = Field(..., description="Speaker identifier (e.g., Speaker_1)")
    segment_count: int = Field(..., description="Number of segments spoken")
    total_duration: float = Field(..., description="Total speaking time in seconds")
    dominant_emotion: Optional[str] = Field(default=None, description="Most common emotion")
    assigned_voice: Optional[str] = Field(default=None, description="Assigned TTS voice name")
    voice_characteristics: Optional[str] = Field(default=None, description="Inferred characteristics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "speaker_id": "Speaker_1",
                "segment_count": 15,
                "total_duration": 45.3,
                "dominant_emotion": "cheerful",
                "assigned_voice": "Kore",
                "voice_characteristics": "firm, professional"
            }
        }


class SpeakerAnalysis(BaseModel):
    """Complete speaker analysis for a job"""
    job_id: str = Field(..., description="Reference to job")
    total_speakers: int = Field(..., description="Number of unique speakers detected")
    speakers: list[SpeakerProfile] = Field(default_factory=list, description="Speaker profiles")
    detected_language: Optional[str] = Field(default=None, description="Auto-detected language")
    language_confidence: Optional[float] = Field(default=None, description="Language detection confidence", ge=0, le=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "507f1f77bcf86cd799439011",
                "total_speakers": 2,
                "detected_language": "en-US",
                "language_confidence": 0.98,
                "speakers": [
                    {
                        "speaker_id": "Speaker_1",
                        "segment_count": 15,
                        "total_duration": 45.3,
                        "dominant_emotion": "cheerful",
                        "assigned_voice": "Kore",
                        "voice_characteristics": "firm, professional"
                    }
                ]
            }
        }


class VoiceMapping(BaseModel):
    """Mapping of speakers to voices"""
    speaker_id: str
    voice_name: str
    emotion_preset: Optional[str] = None
    pace: str = "normal"
