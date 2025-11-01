"""Processing log models"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class LogStatus(str, Enum):
    """Processing log status"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    WARNING = "WARNING"
    INFO = "INFO"


class ProcessingLog(BaseModel):
    """Processing log entry"""
    id: Optional[str] = Field(default=None, alias="_id")
    job_id: str = Field(..., description="Reference to job")
    stage: str = Field(..., description="Processing stage")
    status: LogStatus = Field(..., description="Log status")
    message: str = Field(..., description="Log message")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "job_id": "507f1f77bcf86cd799439011",
                "stage": "transcription",
                "status": "SUCCESS",
                "message": "Transcription completed successfully",
                "metadata": {
                    "segments_count": 45,
                    "duration_seconds": 120.5
                },
                "timestamp": "2024-01-01T12:05:00Z"
            }
        }
