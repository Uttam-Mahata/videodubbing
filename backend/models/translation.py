"""Translation data models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TranslationSegment(BaseModel):
    """Individual translated segment with metadata"""
    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    start_time: float = Field(..., description="Start time in seconds", ge=0)
    end_time: float = Field(..., description="End time in seconds", ge=0)
    duration_ms: int = Field(..., description="Duration in milliseconds", ge=0)
    emotion_tag: Optional[str] = Field(default=None, description="Detected emotion")
    formality_level: Optional[str] = Field(default=None, description="Formality level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "Hello and welcome",
                "translated_text": "Hola y bienvenidos",
                "start_time": 0.5,
                "end_time": 2.8,
                "duration_ms": 2300,
                "emotion_tag": "neutral",
                "formality_level": "formal"
            }
        }


class Translation(BaseModel):
    """Complete translation for a job"""
    id: Optional[str] = Field(default=None, alias="_id")
    job_id: str = Field(..., description="Reference to job")
    transcript_id: str = Field(..., description="Reference to transcript")
    segments: list[TranslationSegment] = Field(default_factory=list)
    target_language: str = Field(..., description="Target language (BCP-47)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "job_id": "507f1f77bcf86cd799439011",
                "transcript_id": "507f1f77bcf86cd799439012",
                "target_language": "es-ES",
                "segments": [
                    {
                        "original_text": "Welcome",
                        "translated_text": "Bienvenido",
                        "start_time": 0.0,
                        "end_time": 1.5,
                        "duration_ms": 1500,
                        "emotion_tag": "neutral",
                        "formality_level": "formal"
                    }
                ]
            }
        }
