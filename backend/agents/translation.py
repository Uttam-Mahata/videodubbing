"""
Translation Agent
Handles context-aware translation using Gemini LLM API
"""

import logging
from typing import AsyncGenerator

from backend.agents.base import BaseCustomAgent, Event, InvocationContext
from backend.services.gemini_llm import GeminiLLMService

logger = logging.getLogger(__name__)


class TranslationAgent(BaseCustomAgent):
    """
    Translation Agent for context-aware translation
    
    Responsibilities:
    - Translate transcript segments
    - Preserve tone and emotion
    - Maintain timing constraints
    - Detect formality levels
    """
    
    def __init__(self):
        super().__init__(
            name="TranslationAgent",
            description="Translates with context and emotion preservation"
        )
        self.llm_service = GeminiLLMService()
    
    async def _run_async_impl(
        self,
        ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Translate transcript segments
        
        Context state expected:
        - job_id: str
        - transcript: Transcript object
        - source_language: str
        - target_language: str
        
        Context state updated:
        - translation_segments: list[TranslationSegment]
        """
        logger.info(f"[{self.name}] Starting translation")
        
        job_id = ctx.state.get("job_id")
        transcript = ctx.state.get("transcript")
        source_language = ctx.state.get("source_language")
        target_language = ctx.state.get("target_language")
        
        yield Event(
            id=f"{self.name}_start",
            author=self.name,
            content={"stage": "translation", "job_id": job_id},
            metadata={"progress": 40}
        )
        
        try:
            # Prepare segments for translation
            segments_data = [
                {
                    "text": seg.text,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "speaker": seg.speaker,
                }
                for seg in transcript.segments
            ]
            
            # Translate with context preservation
            translation_segments = await self.llm_service.translate_segments(
                segments=segments_data,
                source_language=source_language,
                target_language=target_language,
                job_id=job_id,
            )
            
            # Update context state
            ctx.state["translation_segments"] = translation_segments
            
            yield Event(
                id=f"{self.name}_complete",
                author=self.name,
                content={
                    "translated_count": len(translation_segments),
                },
                metadata={"progress": 55}
            )
            
            logger.info(
                f"[{self.name}] Translation completed: "
                f"{len(translation_segments)} segments"
            )
            
        except Exception as e:
            logger.error(f"[{self.name}] Translation failed: {e}")
            yield Event(
                id=f"{self.name}_error",
                author=self.name,
                content={"error": str(e)},
                metadata={"status": "error"}
            )
            raise
