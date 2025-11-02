"""
Gemini Audio Understanding Service
Handles transcription using Gemini Audio API with structured output
"""

import logging
import asyncio
from typing import Optional
from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.config.settings import settings
from backend.models.transcript import Transcript, TranscriptSegment
from backend.services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


class TranscriptSchema(BaseModel):
    """Structured output schema for transcription"""
    segments: list[TranscriptSegment]


class GeminiAudioService:
    """
    Service for audio understanding using Gemini API
    
    Features:
    - Upload audio files to Gemini Files API
    - Generate transcriptions with speaker diarization
    - Structured output with timestamps
    - Circuit breaker for fault tolerance
    - Retry logic with exponential backoff
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model_flash
        self.circuit_breaker = CircuitBreaker(
            name="gemini_audio",
            config=CircuitBreakerConfig(
                failure_threshold=settings.circuit_breaker_failure_threshold,
                timeout_seconds=settings.circuit_breaker_timeout_seconds,
                half_open_test_requests=settings.circuit_breaker_half_open_test_requests,
            )
        )
        logger.info(f"Initialized GeminiAudioService with model: {self.model}")
    
    async def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Transcript:
        """
        Transcribe audio file with speaker diarization
        
        Args:
            audio_path: Path to audio file (local or GCS)
            language: Expected language (BCP-47 code)
            job_id: Associated job ID for logging
            
        Returns:
            Transcript object with segments
        """
        logger.info(f"Starting transcription for job {job_id}: {audio_path}")
        
        try:
            # Upload audio file to Gemini Files API (sync operation)
            uploaded_file = self._upload_audio_file(audio_path)
            
            # Generate transcription with structured output (async operation)
            transcript = await self._generate_transcript(
                uploaded_file,
                language
            )
            
            # Add job_id reference
            if job_id:
                transcript.job_id = job_id
            
            logger.info(
                f"Transcription completed for job {job_id}: "
                f"{len(transcript.segments)} segments"
            )
            
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription failed for job {job_id}: {e}")
            raise
    
    def _upload_audio_file(self, audio_path: str) -> genai.types.File:
        """Upload audio file to Gemini Files API"""
        logger.debug(f"Uploading audio file: {audio_path}")
        
        try:
            uploaded_file = self.client.files.upload(file=audio_path)
            
            logger.info(
                f"Audio file uploaded successfully: {uploaded_file.name}, "
                f"Size: {uploaded_file.size_bytes} bytes"
            )
            
            return uploaded_file
            
        except Exception as e:
            logger.error(f"Failed to upload audio file: {e}")
            raise
    
    async def _generate_transcript(
        self,
        uploaded_file: genai.types.File,
        language: Optional[str] = None,
    ) -> Transcript:
        """Generate transcript with structured output including emotion detection"""
        
        # Build enhanced prompt for emotion and language detection
        prompt = (
            "Generate a detailed transcript with:\n"
            "1. Speaker identification (label each speaker as Speaker_1, Speaker_2, etc.)\n"
            "2. Precise timestamps in seconds (decimal format)\n"
            "3. Confidence scores for each segment\n"
            "4. Emotional tone for each segment (e.g., cheerful, serious, excited, calm, sad, angry, neutral)\n"
        )
        
        if language:
            prompt += f"\nThe audio is in {language}."
        else:
            prompt += "\nAuto-detect the language and include it in your analysis."
        
        logger.info(f"🎤 Generating transcript with emotion detection")
        
        try:
            # Call Gemini API with structured output (run in thread pool for sync API)
            loop = asyncio.get_event_loop()
            logger.info("📡 Calling Gemini API for transcription...")
            
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents=[prompt, uploaded_file],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=list[TranscriptSegment],
                            temperature=0.1,
                            response_modalities=["TEXT"],
                        )
                    )
                ),
                timeout=180.0  # 3 minute timeout
            )
            
            logger.info("✅ Received response from Gemini API")
            
            # Parse structured response
            segments_data = response.parsed
            
            if not segments_data:
                logger.warning("No segments returned from transcription")
                segments_data = []
            
            # Detect language from response if not provided
            detected_language = language
            if not detected_language or detected_language == "auto":
                # Use Gemini to detect language
                logger.info("🌐 Detecting language...")
                detected_language = await self._detect_language(uploaded_file)
                logger.info(f"✅ Language detected: {detected_language}")
            
            # Create Transcript object
            transcript = Transcript(
                job_id="",  # Will be set by caller
                segments=segments_data,
                language=detected_language or "unknown",
            )
            
            logger.info(
                f"✅ Parsed {len(transcript.segments)} transcript segments with emotions. "
                f"Language: {detected_language}"
            )
            
            return transcript
            
        except asyncio.TimeoutError:
            logger.error("⏱️ Transcription request timed out after 5 minutes")
            raise Exception("Transcription request timed out. The audio file may be too long or the API is slow.")
        except Exception as e:
            logger.error(f"Failed to generate transcript: {e}", exc_info=True)
            raise
    
    async def _detect_language(self, uploaded_file: genai.types.File) -> Optional[str]:
        """Detect language from audio file"""
        try:
            # Run in thread pool for sync API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=[
                        "What language is being spoken in this audio? "
                        "Respond with only the BCP-47 language code (e.g., en-US, es-ES, fr-FR).",
                        uploaded_file
                    ],
                )
            )
            
            detected_lang = response.text.strip()
            logger.info(f"Detected language: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None
    
    async def transcribe_with_retry(
        self,
        audio_path: str,
        language: Optional[str] = None,
        job_id: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Transcript:
        """
        Transcribe with exponential backoff retry logic
        
        Args:
            audio_path: Path to audio file
            language: Expected language
            job_id: Associated job ID
            max_retries: Maximum retry attempts (default from settings)
            
        Returns:
            Transcript object
        """
        max_retries = max_retries or settings.max_retry_attempts
        
        for attempt in range(max_retries):
            try:
                return await self.transcribe_audio(audio_path, language, job_id)
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"All retry attempts exhausted for job {job_id}")
                    raise
                
                # Calculate exponential backoff delay
                delay = min(
                    settings.retry_backoff_multiplier ** attempt,
                    settings.retry_max_delay_seconds
                )
                
                logger.warning(
                    f"Transcription attempt {attempt + 1}/{max_retries} failed for job {job_id}. "
                    f"Retrying in {delay}s: {e}"
                )
                
                await asyncio.sleep(delay)
    
    async def count_tokens(self, audio_path: str) -> dict:
        """
        Count tokens for audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Token count information
        """
        try:
            uploaded_file = self._upload_audio_file(audio_path)
            
            # Run in thread pool for sync API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.count_tokens(
                    model=self.model,
                    contents=[uploaded_file]
                )
            )
            
            # Gemini represents audio as 32 tokens/second
            estimated_duration = response.total_tokens / 32
            
            return {
                "total_tokens": response.total_tokens,
                "estimated_duration_seconds": estimated_duration,
            }
            
        except Exception as e:
            logger.error(f"Failed to count tokens: {e}")
            raise
