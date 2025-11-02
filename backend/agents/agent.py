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
audio_service = GeminiAudioService()
llm_service = GeminiLLMService()
tts_service = GeminiTTSService()


# ====================
# TOOL FUNCTIONS
# ====================


async def transcribe_audio_tool(
    audio_path: str,
    source_language: str,
    tool_context: ToolContext,
) -> dict:
    """
    Tool to transcribe audio using Gemini Audio API with speaker and emotion detection.

    Args:
        audio_path: Path to the audio file
        source_language: Source language code (e.g., 'en-US', 'es-ES') or None for auto-detection
        tool_context: ADK tool context for state management

    Returns:
        Dictionary with transcript, speaker_count, emotions, and detected_language
    """
    logger.info(f"Transcribing audio: {audio_path}")

    try:
        # Call Gemini Audio API with retry logic (supports language auto-detection)
        transcript = await audio_service.transcribe_with_retry(
            audio_path=audio_path,
            language=source_language if source_language and source_language.lower() != "auto" else None,
        )

        # Analyze speakers and emotions
        speakers = {}
        for seg in transcript.segments:
            if seg.speaker:
                if seg.speaker not in speakers:
                    speakers[seg.speaker] = {
                        "segment_count": 0,
                        "total_duration": 0.0,
                        "emotions": []
                    }
                speakers[seg.speaker]["segment_count"] += 1
                speakers[seg.speaker]["total_duration"] += (seg.end_time - seg.start_time)
                if seg.emotion:
                    speakers[seg.speaker]["emotions"].append(seg.emotion)
        
        speaker_count = len(speakers)
        
        # Determine dominant emotion for each speaker
        speaker_profiles = {}
        for speaker_id, data in speakers.items():
            dominant_emotion = None
            if data["emotions"]:
                # Most common emotion
                emotion_counts = {}
                for emotion in data["emotions"]:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                dominant_emotion = max(emotion_counts, key=emotion_counts.get)
            
            speaker_profiles[speaker_id] = {
                "segment_count": data["segment_count"],
                "total_duration": data["total_duration"],
                "dominant_emotion": dominant_emotion
            }

        # Store in tool context
        tool_context.state["transcript"] = transcript
        tool_context.state["speaker_count"] = speaker_count
        tool_context.state["speaker_profiles"] = speaker_profiles
        tool_context.state["detected_language"] = transcript.language

        logger.info(
            f"Transcription complete: {len(transcript.segments)} segments, "
            f"{speaker_count} speakers, language: {transcript.language}"
        )

        return {
            "status": "success",
            "segments_count": len(transcript.segments),
            "speaker_count": speaker_count,
            "detected_language": transcript.language,
            "speaker_profiles": speaker_profiles,
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
    Tool to generate speech from translated segments using Gemini TTS with auto voice assignment.

    Args:
        tool_context: ADK tool context

    Returns:
        Dictionary with synthesis status, audio segment paths, and voice mappings
    """
    translation_segments = tool_context.state.get("translation_segments")
    transcript = tool_context.state.get("transcript")
    speaker_profiles = tool_context.state.get("speaker_profiles", {})
    speaker_count = tool_context.state.get("speaker_count", 1)
    job_id = tool_context.state.get("job_id", "unknown")

    if not translation_segments or not transcript:
        return {
            "status": "error",
            "message": "Missing translation segments or transcript",
        }

    logger.info(f"Synthesizing speech for {len(translation_segments)} segments with {speaker_count} speakers")

    try:
        # Auto-assign voices to speakers based on characteristics
        voice_assignments = _auto_assign_voices(speaker_profiles, speaker_count)
        
        # Create temporary directory for audio files
        temp_dir = tempfile.mkdtemp(prefix=f"job_{job_id}_")
        audio_segments = []

        # Generate audio for each segment
        for i, (trans_seg, orig_seg) in enumerate(zip(translation_segments, transcript.segments)):
            audio_path = os.path.join(temp_dir, f"segment_{i:04d}.wav")
            
            # Get speaker-specific voice
            speaker_id = orig_seg.speaker
            voice_name = voice_assignments.get(speaker_id, "Kore")
            emotion = orig_seg.emotion or "neutral"

            # Synthesize with speaker's assigned voice and detected emotion
            await tts_service.synthesize_single_speaker(
                text=trans_seg.translated_text,
                voice_name=voice_name,
                emotion=emotion,
                pace="normal",
                output_path=audio_path,
            )

            audio_segments.append(audio_path)

        # Store in context
        tool_context.state["audio_segments"] = audio_segments
        tool_context.state["temp_storage_path"] = temp_dir
        tool_context.state["voice_assignments"] = voice_assignments

        logger.info(
            f"Synthesis complete: {len(audio_segments)} audio files, "
            f"voice assignments: {voice_assignments}"
        )

        return {
            "status": "success",
            "segments_count": len(audio_segments),
            "temp_dir": temp_dir,
            "voice_assignments": voice_assignments,
        }

    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        return {"status": "error", "message": str(e)}


def _auto_assign_voices(speaker_profiles: dict, speaker_count: int) -> dict:
    """
    Auto-assign voices to speakers based on their characteristics.
    
    Args:
        speaker_profiles: Dictionary of speaker profiles with emotion data
        speaker_count: Number of unique speakers
    
    Returns:
        Dictionary mapping speaker_id to voice_name
    """
    from backend.models.voice import AVAILABLE_VOICES, VoiceStyle
    
    # Define voice pools by characteristic
    professional_voices = ["Kore", "Orus", "Charon", "Alnilam", "Schedar"]
    friendly_voices = ["Puck", "Aoede", "Achird", "Laomedeia", "Sulafat"]
    calm_voices = ["Algieba", "Despina", "Umbriel", "Achernar", "Vindemiatrix"]
    energetic_voices = ["Zephyr", "Fenrir", "Leda", "Sadachbia"]
    mature_voices = ["Gacrux", "Rasalgethi", "Sadaltager"]
    
    assignments = {}
    available_voices = list(AVAILABLE_VOICES.keys())
    
    for idx, (speaker_id, profile) in enumerate(speaker_profiles.items()):
        # Select voice based on dominant emotion
        emotion = profile.get("dominant_emotion", "neutral")
        
        if emotion in ["cheerful", "excited", "happy"]:
            voice_pool = energetic_voices
        elif emotion in ["serious", "professional", "informative"]:
            voice_pool = professional_voices
        elif emotion in ["calm", "gentle", "soft"]:
            voice_pool = calm_voices
        elif emotion in ["friendly", "casual", "warm"]:
            voice_pool = friendly_voices
        else:
            voice_pool = available_voices
        
        # Assign voice, cycling through pool if needed
        voice_idx = idx % len(voice_pool)
        assignments[speaker_id] = voice_pool[voice_idx]
    
    # If no speaker profiles, use default assignment
    if not assignments and speaker_count > 0:
        for i in range(speaker_count):
            speaker_id = f"Speaker_{i+1}"
            assignments[speaker_id] = available_voices[i % len(available_voices)]
    
    return assignments


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
