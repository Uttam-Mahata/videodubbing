"""
Video Dubbing Agents using Google ADK

This module defines agents for the video dubbing pipeline using the actual
Google Agent Development Kit (ADK) patterns from adk-samples.
"""

import logging
import os
import tempfile
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import ToolContext

from backend.config.settings import settings
from backend.services.gemini_audio import GeminiAudioService
from backend.services.gemini_llm import GeminiLLMService
from backend.services.gemini_tts import GeminiTTSService
from backend.agents.prompts import (
    TRANSCRIPTION_PROMPT,
    TRANSLATION_PROMPT,
    SPEECH_SYNTHESIS_PROMPT,
)

logger = logging.getLogger(__name__)

# Initialize services
audio_service = GeminiAudioService(api_key=settings.gemini_api_key)
llm_service = GeminiLLMService(api_key=settings.gemini_api_key)
tts_service = GeminiTTSService(api_key=settings.gemini_api_key)


# ====================
# TOOL FUNCTIONS
# ====================


async def transcribe_audio_tool(
    audio_path: str,
    source_language: str,
    tool_context: ToolContext,
) -> dict:
    """
    Tool to transcribe audio using Gemini Audio API.

    Args:
        audio_path: Path to the audio file
        source_language: Source language code (e.g., 'en', 'es')
        tool_context: ADK tool context for state management

    Returns:
        Dictionary with transcript and speaker_count
    """
    logger.info(f"Transcribing audio: {audio_path}")

    try:
        # Call Gemini Audio API with retry logic
        transcript = await audio_service.transcribe_with_retry(
            audio_path=audio_path,
            source_language=source_language,
        )

        # Calculate speaker count
        speakers = set(seg.speaker for seg in transcript.segments if seg.speaker)
        speaker_count = len(speakers)

        # Store in tool context
        tool_context.state["transcript"] = transcript
        tool_context.state["speaker_count"] = speaker_count

        logger.info(
            f"Transcription complete: {len(transcript.segments)} segments, {speaker_count} speakers"
        )

        return {
            "status": "success",
            "segments_count": len(transcript.segments),
            "speaker_count": speaker_count,
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"status": "error", "message": str(e)}


async def translate_segments_tool(
    source_language: str,
    target_language: str,
    tool_context: ToolContext,
) -> dict:
    """
    Tool to translate transcript segments using Gemini LLM.

    Args:
        source_language: Source language code
        target_language: Target language code
        tool_context: ADK tool context

    Returns:
        Dictionary with translation status and count
    """
    transcript = tool_context.state.get("transcript")

    if not transcript:
        return {"status": "error", "message": "No transcript found in context"}

    logger.info(
        f"Translating: {source_language} → {target_language} ({len(transcript.segments)} segments)"
    )

    try:
        # Prepare segments data
        segments_data = [
            {
                "text": seg.text,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "speaker": seg.speaker,
            }
            for seg in transcript.segments
        ]

        # Call Gemini LLM for translation
        translation_segments = await llm_service.translate_segments(
            segments=segments_data,
            source_language=source_language,
            target_language=target_language,
            model="gemini-2.5-flash",
        )

        # Store in context
        tool_context.state["translation_segments"] = translation_segments

        logger.info(f"Translation complete: {len(translation_segments)} segments")

        return {
            "status": "success",
            "segments_count": len(translation_segments),
        }

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return {"status": "error", "message": str(e)}


async def synthesize_speech_tool(
    tool_context: ToolContext,
) -> dict:
    """
    Tool to generate speech from translated segments using Gemini TTS.

    Args:
        tool_context: ADK tool context

    Returns:
        Dictionary with synthesis status and audio segment paths
    """
    translation_segments = tool_context.state.get("translation_segments")
    voice_config = tool_context.state.get("voice_config")
    job_id = tool_context.state.get("job_id", "unknown")

    if not translation_segments or not voice_config:
        return {
            "status": "error",
            "message": "Missing translation segments or voice config",
        }

    logger.info(f"Synthesizing speech for {len(translation_segments)} segments")

    try:
        # Create temporary directory for audio files
        temp_dir = tempfile.mkdtemp(prefix=f"job_{job_id}_")
        audio_segments = []

        # Generate audio for each segment
        for i, segment in enumerate(translation_segments):
            audio_path = os.path.join(temp_dir, f"segment_{i:04d}.wav")

            # Use single-speaker synthesis (TODO: multi-speaker)
            await tts_service.synthesize_single_speaker(
                text=segment.translated_text,
                voice_name=voice_config.voice_name,
                language=voice_config.language,
                output_path=audio_path,
                emotion=segment.emotion_tag,
                pace="normal",
            )

            audio_segments.append(audio_path)

        # Store in context
        tool_context.state["audio_segments"] = audio_segments
        tool_context.state["temp_storage_path"] = temp_dir

        logger.info(f"Synthesis complete: {len(audio_segments)} audio files")

        return {
            "status": "success",
            "segments_count": len(audio_segments),
            "temp_dir": temp_dir,
        }

    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        return {"status": "error", "message": str(e)}


# ====================
# AGENT DEFINITIONS
# ====================


# Individual agents for each stage
transcription_agent = Agent(
    model="gemini-2.5-flash",
    name="transcription_agent",
    description="Transcribes audio files using Gemini Audio API with speaker diarization",
    instruction=TRANSCRIPTION_PROMPT,
    tools=[transcribe_audio_tool],
    output_key="transcription_result",
)

translation_agent = Agent(
    model="gemini-2.5-flash",
    name="translation_agent",
    description="Translates transcript segments preserving tone and emotion",
    instruction=TRANSLATION_PROMPT,
    tools=[translate_segments_tool],
    output_key="translation_result",
)

speech_synthesis_agent = Agent(
    model="gemini-2.5-flash",
    name="speech_synthesis_agent",
    description="Generates speech audio from translated text using Gemini TTS",
    instruction=SPEECH_SYNTHESIS_PROMPT,
    tools=[synthesize_speech_tool],
    output_key="synthesis_result",
)


# Sequential pipeline for dubbing workflow
dubbing_pipeline_agent = SequentialAgent(
    name="dubbing_pipeline",
    description="Complete video dubbing pipeline: transcription → translation → synthesis",
    sub_agents=[
        transcription_agent,
        translation_agent,
        speech_synthesis_agent,
    ],
)


# Root agent for the application
root_agent = dubbing_pipeline_agent
