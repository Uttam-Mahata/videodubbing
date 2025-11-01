"""
Speech Synthesis Agent
Handles TTS generation using Gemini TTS API
"""

import logging
from typing import AsyncGenerator
import os

from backend.agents.base import BaseCustomAgent, Event, InvocationContext
from backend.services.gemini_tts import GeminiTTSService
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class SpeechSynthesisAgent(BaseCustomAgent):
    """
    Speech Synthesis Agent for TTS generation
    
    Responsibilities:
    - Generate dubbed audio with appropriate voices
    - Handle single-speaker or multi-speaker synthesis
    - Apply emotion and pace controls
    - Validate audio duration
    """
    
    def __init__(self):
        super().__init__(
            name="SpeechSynthesisAgent",
            description="Generates dubbed audio with TTS"
        )
        self.tts_service = GeminiTTSService()
    
    async def _run_async_impl(
        self,
        ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Synthesize dubbed audio
        
        Context state expected:
        - job_id: str
        - translation_segments: list[TranslationSegment]
        - voice_config: VoiceConfiguration
        - speaker_count: int
        
        Context state updated:
        - audio_segments: list[str] (paths to generated audio)
        """
        logger.info(f"[{self.name}] Starting speech synthesis")
        
        job_id = ctx.state.get("job_id")
        translation_segments = ctx.state.get("translation_segments", [])
        voice_config = ctx.state.get("voice_config")
        speaker_count = ctx.state.get("speaker_count", 1)
        
        yield Event(
            id=f"{self.name}_start",
            author=self.name,
            content={"stage": "speech_synthesis", "job_id": job_id},
            metadata={"progress": 60}
        )
        
        try:
            audio_segments = []
            
            if speaker_count == 1:
                # Single-speaker synthesis
                for i, segment in enumerate(translation_segments):
                    output_path = os.path.join(
                        settings.temp_storage_path,
                        f"{job_id}_segment_{i}.wav"
                    )
                    
                    await self.tts_service.synthesize_single_speaker(
                        text=segment.translated_text,
                        voice_name=voice_config.primary_voice,
                        emotion=segment.emotion_tag,
                        output_path=output_path,
                    )
                    
                    audio_segments.append(output_path)
            else:
                # Multi-speaker synthesis
                # Group segments by speaker and synthesize
                logger.info(f"[{self.name}] Multi-speaker synthesis not yet implemented")
                # TODO: Implement multi-speaker logic
            
            # Update context state
            ctx.state["audio_segments"] = audio_segments
            
            yield Event(
                id=f"{self.name}_complete",
                author=self.name,
                content={
                    "audio_segments_count": len(audio_segments),
                },
                metadata={"progress": 75}
            )
            
            logger.info(
                f"[{self.name}] Speech synthesis completed: "
                f"{len(audio_segments)} audio segments"
            )
            
        except Exception as e:
            logger.error(f"[{self.name}] Speech synthesis failed: {e}")
            yield Event(
                id=f"{self.name}_error",
                author=self.name,
                content={"error": str(e)},
                metadata={"status": "error"}
            )
            raise
