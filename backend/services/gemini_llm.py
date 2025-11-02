"""
Gemini LLM Service
Handles translation and text generation using Gemini LLM API
"""

import logging
from typing import Optional
from google import genai
from google.genai import types

from backend.config.settings import settings
from backend.models.translation import Translation, TranslationSegment
from backend.services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


class GeminiLLMService:
    """
    Service for LLM operations using Gemini API
    
    Features:
    - Context-aware translation
    - Structured output with metadata
    - Emotion and formality detection
    - Circuit breaker protection
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_flash = settings.gemini_model_flash
        self.model_pro = settings.gemini_model_pro
        self.circuit_breaker = CircuitBreaker(
            name="gemini_llm",
            config=CircuitBreakerConfig(
                failure_threshold=settings.circuit_breaker_failure_threshold,
                timeout_seconds=settings.circuit_breaker_timeout_seconds,
            )
        )
        logger.info(f"Initialized GeminiLLMService")
    
    async def translate_segments(
        self,
        segments: list[dict],
        source_language: str,
        target_language: str,
        job_id: Optional[str] = None,
        use_pro_model: bool = False,
    ) -> list[TranslationSegment]:
        """
        Translate transcript segments with context preservation
        
        Args:
            segments: List of transcript segments
            source_language: Source language (BCP-47)
            target_language: Target language (BCP-47)
            job_id: Associated job ID
            use_pro_model: Use Pro model for complex translations
            
        Returns:
            List of translation segments with metadata
        """
        logger.info(
            f"Translating {len(segments)} segments from {source_language} "
            f"to {target_language} for job {job_id}"
        )
        
        model = self.model_pro if use_pro_model else self.model_flash
        
        # Build translation prompt
        system_instruction = (
            f"You are a professional translator specializing in dubbing and subtitles. "
            f"Translate from {source_language} to {target_language} while maintaining "
            f"tone, emotion, and cultural context. Preserve timing constraints for dubbing. "
            f"Detect and tag emotions and formality levels."
        )
        
        # Batch segments for efficient processing
        translated_segments = []
        batch_size = 10  # Process 10 segments at a time

        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]
            batch_start_idx = i  # Track the starting index for this batch

            try:
                batch_result = await self.circuit_breaker.call(
                    self._translate_batch,
                    batch,
                    system_instruction,
                    model,
                    batch_start_idx
                )
                translated_segments.extend(batch_result)

            except Exception as e:
                logger.error(f"Failed to translate batch {i}-{i+batch_size}: {e}")
                raise

        logger.info(f"Translation completed: {len(translated_segments)} segments")
        return translated_segments
    
    def _translate_batch(
        self,
        segments: list[dict],
        system_instruction: str,
        model: str,
        batch_start_idx: int = 0,
    ) -> list[TranslationSegment]:
        """Translate a batch of segments"""

        # Format segments for translation
        segments_text = "\n".join([
            f"{i+1}. [{seg.get('start_time')}-{seg.get('end_time')}s] {seg.get('text')}"
            for i, seg in enumerate(segments)
        ])

        prompt = (
            f"Translate the following segments and provide translations with metadata:\n\n"
            f"{segments_text}\n\n"
            f"For each segment, provide: segment_id, translated_text, emotion_tag, formality_level\n"
            f"Use segment_id format: seg_{{index}}_{{start_time}}"
        )

        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[TranslationSegment],
                system_instruction=system_instruction,
            )
        )

        # Ensure segment_ids are set correctly if Gemini doesn't provide them
        parsed_segments = response.parsed
        for i, seg in enumerate(parsed_segments):
            if not hasattr(seg, 'segment_id') or not seg.segment_id:
                # Generate segment_id if missing
                original_segment = segments[i] if i < len(segments) else {}
                start_time = original_segment.get('start_time', 0)
                seg.segment_id = f"seg_{batch_start_idx + i}_{start_time}"

        return parsed_segments
    
    async def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        use_pro_model: bool = False,
    ) -> str:
        """
        Generate text content using Gemini LLM
        
        Args:
            prompt: User prompt
            system_instruction: Optional system instructions
            use_pro_model: Use Pro model for complex tasks
            
        Returns:
            Generated text
        """
        model = self.model_pro if use_pro_model else self.model_flash
        
        try:
            response = await self.circuit_breaker.call(
                self._generate_text,
                prompt,
                system_instruction,
                model
            )
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            raise
    
    def _generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str],
        model: str,
    ) -> str:
        """Generate text using Gemini API"""
        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction
        
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config) if config else None,
        )
        
        return response.text
