"""
Gemini Text-to-Speech Service
Handles speech synthesis using Gemini TTS API
"""

import logging
import wave
from typing import Optional
from google import genai
from google.genai import types

from backend.config.settings import settings
from backend.models.voice import AVAILABLE_VOICES
from backend.services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


class GeminiTTSService:
    """
    Service for text-to-speech using Gemini TTS API
    
    Features:
    - Single-speaker and multi-speaker TTS
    - Controllable speech style with prompts
    - 30 voice options with different characteristics
    - Circuit breaker protection
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_tts_model
        self.circuit_breaker = CircuitBreaker(
            name="gemini_tts",
            config=CircuitBreakerConfig(
                failure_threshold=settings.circuit_breaker_failure_threshold,
                timeout_seconds=settings.circuit_breaker_timeout_seconds,
            )
        )
        logger.info(f"Initialized GeminiTTSService with model: {self.model}")
    
    async def synthesize_single_speaker(
        self,
        text: str,
        voice_name: str = "Kore",
        emotion: Optional[str] = None,
        pace: str = "normal",
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Synthesize single-speaker audio
        
        Args:
            text: Text to convert to speech
            voice_name: Voice name from AVAILABLE_VOICES
            emotion: Optional emotion (e.g., "cheerful", "serious")
            pace: Speech pace ("slow", "normal", "fast")
            output_path: Optional path to save WAV file
            
        Returns:
            Audio data as bytes (PCM 24kHz)
        """
        logger.info(f"Synthesizing single-speaker audio with voice: {voice_name}")
        
        # Validate voice
        if voice_name not in AVAILABLE_VOICES:
            raise ValueError(f"Invalid voice: {voice_name}")
        
        # Build prompt with style controls
        prompt = f"Say"
        if emotion:
            prompt += f" in {emotion} tone"
        if pace != "normal":
            prompt += f" with {pace} pace"
        prompt += f": {text}"
        
        try:
            audio_data = await self.circuit_breaker.call(
                self._generate_audio,
                prompt,
                voice_name
            )
            
            # Save to file if path provided
            if output_path:
                self._save_wav_file(output_path, audio_data)
                logger.info(f"Audio saved to: {output_path}")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Failed to synthesize audio: {e}")
            raise
    
    async def synthesize_multi_speaker(
        self,
        dialogue: list[dict],
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Synthesize multi-speaker audio
        
        Args:
            dialogue: List of {"speaker": "name", "text": "...", "voice": "Kore"}
            output_path: Optional path to save WAV file
            
        Returns:
            Audio data as bytes
        """
        logger.info(f"Synthesizing multi-speaker audio with {len(dialogue)} turns")
        
        # Build prompt from dialogue
        prompt_lines = []
        speaker_voices = {}
        
        for turn in dialogue:
            speaker = turn["speaker"]
            text = turn["text"]
            voice = turn.get("voice", "Kore")
            
            speaker_voices[speaker] = voice
            prompt_lines.append(f"{speaker}: {text}")
        
        prompt = "TTS the following conversation:\n" + "\n".join(prompt_lines)
        
        # Build speaker voice configs
        speaker_voice_configs = [
            types.SpeakerVoiceConfig(
                speaker=speaker,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            )
            for speaker, voice_name in speaker_voices.items()
        ]
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=speaker_voice_configs
                        )
                    ),
                )
            )
            
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            if output_path:
                self._save_wav_file(output_path, audio_data)
                logger.info(f"Multi-speaker audio saved to: {output_path}")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Failed to synthesize multi-speaker audio: {e}")
            raise
    
    def _generate_audio(self, prompt: str, voice_name: str) -> bytes:
        """Generate audio using Gemini TTS API"""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                ),
            )
        )
        
        return response.candidates[0].content.parts[0].inline_data.data
    
    def _save_wav_file(
        self,
        filename: str,
        pcm_data: bytes,
        channels: int = 1,
        rate: int = 24000,
        sample_width: int = 2,
    ):
        """Save PCM data as WAV file"""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)
