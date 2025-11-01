"""
Transcription Agent
Handles audio transcription using Gemini Audio API
"""

import logging
from typing import AsyncGenerator

from backend.agents.base import BaseCustomAgent, Event, InvocationContext
from backend.services.gemini_audio import GeminiAudioService

logger = logging.getLogger(__name__)


class TranscriptionAgent(BaseCustomAgent):
    """
    Transcription Agent for audio understanding
    
    Responsibilities:
    - Upload audio to Gemini Files API
    - Generate transcript with speaker diarization
    - Extract timestamps and confidence scores
    """
    
    def __init__(self):
        super().__init__(
            name="TranscriptionAgent",
            description="Transcribes audio with speaker identification"
        )
        self.audio_service = GeminiAudioService()
    
    async def _run_async_impl(
        self,
        ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Transcribe audio file
        
        Context state expected:
        - job_id: str
        - audio_path: str
        - source_language: str
        
        Context state updated:
        - transcript: Transcript object
        - speaker_count: int
        """
        logger.info(f"[{self.name}] Starting transcription")
        
        job_id = ctx.state.get("job_id")
        audio_path = ctx.state.get("audio_path")
        source_language = ctx.state.get("source_language")
        
        yield Event(
            id=f"{self.name}_start",
            author=self.name,
            content={"stage": "transcription", "job_id": job_id},
            metadata={"progress": 20}
        )
        
        try:
            # Transcribe audio with retry logic
            transcript = await self.audio_service.transcribe_with_retry(
                audio_path=audio_path,
                language=source_language,
                job_id=job_id,
            )
            
            # Update context state
            ctx.state["transcript"] = transcript
            ctx.state["speaker_count"] = len(set(seg.speaker for seg in transcript.segments))
            
            yield Event(
                id=f"{self.name}_complete",
                author=self.name,
                content={
                    "segments_count": len(transcript.segments),
                    "speaker_count": ctx.state["speaker_count"],
                },
                metadata={"progress": 35}
            )
            
            logger.info(
                f"[{self.name}] Transcription completed: "
                f"{len(transcript.segments)} segments, "
                f"{ctx.state['speaker_count']} speakers"
            )
            
        except Exception as e:
            logger.error(f"[{self.name}] Transcription failed: {e}")
            yield Event(
                id=f"{self.name}_error",
                author=self.name,
                content={"error": str(e)},
                metadata={"status": "error"}
            )
            raise
