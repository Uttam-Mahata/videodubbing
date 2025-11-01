"""Job data models and schemas"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from typing import Optional
from bson import ObjectId


class JobStatus(str, Enum):
    """Job processing status"""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    AUDIO_EXTRACTED = "AUDIO_EXTRACTED"
    TRANSCRIBED = "TRANSCRIBED"
    TRANSLATED = "TRANSLATED"
    SYNTHESIZED = "SYNTHESIZED"
    SYNCHRONIZED = "SYNCHRONIZED"
    MERGED = "MERGED"
    VALIDATED = "VALIDATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobStage(str, Enum):
    """Current processing stage"""
    INTAKE = "intake"
    AUDIO_EXTRACTION = "audio_extraction"
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"
    SPEECH_SYNTHESIS = "speech_synthesis"
    TIMING_SYNC = "timing_sync"
    AUDIO_MERGING = "audio_merging"
    QUALITY_ASSURANCE = "quality_assurance"
    DELIVERY = "delivery"


class VideoMetadata(BaseModel):
    """Video file metadata"""
    duration_seconds: float
    file_size_mb: float
    resolution: str
    fps: Optional[float] = None
    detected_speakers: Optional[int] = None
    processing_time_seconds: Optional[float] = None


class VoiceConfiguration(BaseModel):
    """Voice configuration for dubbing"""
    primary_voice: str = "Kore"
    secondary_voice: Optional[str] = None
    style_preferences: dict = Field(default_factory=dict)
    
    @field_validator("primary_voice")
    @classmethod
    def validate_voice(cls, v: str) -> str:
        """Ensure voice name is valid"""
        valid_voices = {
            "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda",
            "Orus", "Aoede", "Callirrhoe", "Autonoe", "Enceladus", "Iapetus",
            "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi",
            "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima",
            "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"
        }
        if v not in valid_voices:
            raise ValueError(f"Invalid voice: {v}. Must be one of {valid_voices}")
        return v


class Checkpoint(BaseModel):
    """Processing checkpoint for recovery"""
    stage: JobStage
    status: str
    timestamp: datetime
    data: dict = Field(default_factory=dict)


class Job(BaseModel):
    """Job database model"""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    status: JobStatus = JobStatus.QUEUED
    current_stage: Optional[JobStage] = None
    progress_percent: int = 0
    
    source_language: str = Field(..., description="BCP-47 language code")
    target_language: str = Field(..., description="BCP-47 language code")
    
    voice_config: VoiceConfiguration
    
    input_video_url: str
    output_video_url: Optional[str] = None
    
    metadata: Optional[VideoMetadata] = None
    error_message: Optional[str] = None
    checkpoints: list[Checkpoint] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "source_language": "en-US",
                "target_language": "es-ES",
                "voice_config": {
                    "primary_voice": "Kore",
                    "style_preferences": {}
                },
                "input_video_url": "gs://videos-input/sample.mp4"
            }
        }


class JobCreate(BaseModel):
    """Request schema for creating a job"""
    source_language: str = Field(..., description="Source language (BCP-47 code)", examples=["en-US"])
    target_language: str = Field(..., description="Target language (BCP-47 code)", examples=["es-ES"])
    primary_voice: str = Field(default="Kore", description="Primary voice for TTS")
    secondary_voice: Optional[str] = Field(default=None, description="Secondary voice for multi-speaker")
    style_preferences: dict = Field(default_factory=dict, description="Voice style customization")
    
    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Basic validation for language codes"""
        if not v or len(v) < 2:
            raise ValueError("Invalid language code")
        return v


class JobResponse(BaseModel):
    """Response schema for job operations"""
    job_id: str
    status: JobStatus
    current_stage: Optional[JobStage] = None
    progress_percent: int = 0
    estimated_time_minutes: Optional[int] = None
    download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "507f1f77bcf86cd799439011",
                "status": "PROCESSING",
                "current_stage": "transcription",
                "progress_percent": 45,
                "estimated_time_minutes": 15,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:05:00Z"
            }
        }


class JobListResponse(BaseModel):
    """Response schema for listing jobs"""
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int
