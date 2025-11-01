"""Transcript data models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TranscriptSegment(BaseModel):
    """Individual transcript segment with speaker and timing"""
    speaker: str = Field(..., description="Speaker identifier")
    start_time: float = Field(..., description="Start time in seconds", ge=0)
    end_time: float = Field(..., description="End time in seconds", ge=0)
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Confidence score", ge=0, le=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "speaker": "Speaker_1",
                "start_time": 0.5,
                "end_time": 3.2,
                "text": "Hello and welcome to our presentation.",
                "confidence": 0.95
            }
        }


class Transcript(BaseModel):
    """Complete transcript for a job"""
    id: Optional[str] = Field(default=None, alias="_id")
    job_id: str = Field(..., description="Reference to job")
    segments: list[TranscriptSegment] = Field(default_factory=list)
    language: str = Field(..., description="Source language (BCP-47)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "job_id": "507f1f77bcf86cd799439011",
                "language": "en-US",
                "segments": [
                    {
                        "speaker": "Speaker_1",
                        "start_time": 0.0,
                        "end_time": 3.5,
                        "text": "Welcome to the video.",
                        "confidence": 0.98
                    }
                ]
            }
        }
