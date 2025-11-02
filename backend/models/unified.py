"""Unified data models for combined transcription and translation"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from .transcript import TranscriptSegment, Transcript
from .translation import TranslationSegment


class TranscriptTranslationSegment(BaseModel):
    """Unified segment containing both transcription and translation data"""

    # Unique identifier
    segment_id: str = Field(..., description="Unique segment identifier")

    # Speaker & timing
    speaker: str = Field(..., description="Speaker identifier (e.g., Speaker_1, Speaker_2)")
    start_time: float = Field(..., description="Start time in seconds", ge=0)
    end_time: float = Field(..., description="End time in seconds", ge=0)
    duration_ms: int = Field(..., description="Duration in milliseconds", ge=0)

    # Original transcription data
    original_text: str = Field(..., description="Transcribed text in source language")
    confidence: float = Field(..., description="Transcription confidence score", ge=0, le=1)
    emotion: str = Field(..., description="Detected emotional tone")

    # Translation data
    translated_text: str = Field(..., description="Translated text in target language")
    formality_level: str = Field(..., description="Formality level of translation")

    class Config:
        json_schema_extra = {
            "example": {
                "segment_id": "seg_0_0.5",
                "speaker": "Speaker_1",
                "start_time": 0.5,
                "end_time": 2.8,
                "duration_ms": 2300,
                "original_text": "Hello and welcome to this video",
                "confidence": 0.95,
                "emotion": "cheerful",
                "translated_text": "Hola y bienvenidos a este video",
                "formality_level": "neutral"
            }
        }


class TranscriptTranslation(BaseModel):
    """Unified result containing both transcript and translation data"""

    job_id: str = Field(..., description="Associated job ID")
    source_language: str = Field(..., description="Source language (BCP-47)")
    target_language: str = Field(..., description="Target language (BCP-47)")
    segments: list[TranscriptTranslationSegment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_transcript(self) -> Transcript:
        """
        Extract transcript-only data from unified result

        Returns:
            Transcript object with original transcription segments
        """
        transcript_segments = [
            TranscriptSegment(
                speaker=seg.speaker,
                start_time=seg.start_time,
                end_time=seg.end_time,
                text=seg.original_text,
                confidence=seg.confidence,
                emotion=seg.emotion
            )
            for seg in self.segments
        ]

        return Transcript(
            job_id=self.job_id,
            segments=transcript_segments,
            language=self.source_language,
            created_at=self.created_at
        )

    def get_translations(self) -> list[TranslationSegment]:
        """
        Extract translation-only data from unified result

        Returns:
            List of TranslationSegment objects
        """
        return [
            TranslationSegment(
                segment_id=seg.segment_id,
                original_text=seg.original_text,
                translated_text=seg.translated_text,
                start_time=seg.start_time,
                end_time=seg.end_time,
                duration_ms=seg.duration_ms,
                emotion_tag=seg.emotion,
                formality_level=seg.formality_level
            )
            for seg in self.segments
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "507f1f77bcf86cd799439011",
                "source_language": "en-US",
                "target_language": "es-ES",
                "segments": [
                    {
                        "segment_id": "seg_0_0.5",
                        "speaker": "Speaker_1",
                        "start_time": 0.5,
                        "end_time": 2.8,
                        "duration_ms": 2300,
                        "original_text": "Hello and welcome",
                        "confidence": 0.95,
                        "emotion": "cheerful",
                        "translated_text": "Hola y bienvenidos",
                        "formality_level": "neutral"
                    }
                ]
            }
        }
