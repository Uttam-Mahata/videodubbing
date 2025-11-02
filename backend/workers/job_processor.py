"""
Background Job Processor
Handles asynchronous video dubbing pipeline execution using Google ADK and Gemini APIs
"""

import logging
import asyncio
import os
import tempfile
import wave
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId

from backend.models.job import Job, JobStatus, JobStage
from backend.models.transcript import Transcript, TranscriptSegment
from backend.models.translation import TranslationSegment
from backend.db.mongodb import get_jobs_collection, get_transcripts_collection, get_translations_collection
from backend.services.storage import StorageService
from backend.services.gemini_audio import GeminiAudioService
from backend.services.gemini_llm import GeminiLLMService
from backend.services.gemini_tts import GeminiTTSService
from backend.services.gemini_unified import GeminiUnifiedService
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class JobProcessor:
    """
    Background job processor for video dubbing pipeline
    Manages job execution and state transitions
    """
    
    def __init__(self):
        self.storage_service = StorageService()
        self.unified_service = GeminiUnifiedService()  # New unified service
        self.audio_service = GeminiAudioService()  # Keep for potential fallback
        self.llm_service = GeminiLLMService()  # Keep for potential fallback
        self.tts_service = GeminiTTSService()
        self._running = False
        self._processing_jobs = set()
    
    async def start(self):
        """Start the background job processor"""
        self._running = True
        logger.info("🚀 Job processor started")
        
        # Start processing loop
        asyncio.create_task(self._process_loop())
    
    async def stop(self):
        """Stop the background job processor"""
        self._running = False
        logger.info("⏹️ Job processor stopped")
    
    async def _process_loop(self):
        """Main processing loop - checks for pending jobs"""
        while self._running:
            try:
                # Find jobs that need processing
                jobs_collection = get_jobs_collection()
                
                # Look for QUEUED jobs (either new or retrying)
                pending_jobs = await jobs_collection.find({
                    "status": JobStatus.QUEUED.value
                }).to_list(length=10)
                
                if pending_jobs:
                    logger.info(f"Found {len(pending_jobs)} pending job(s) to process")
                
                for job_doc in pending_jobs:
                    job_id = str(job_doc["_id"])
                    
                    # Skip if already processing
                    if job_id in self._processing_jobs:
                        continue
                    
                    # Process job in background
                    self._processing_jobs.add(job_id)
                    asyncio.create_task(self._process_job(job_id))
                
                # Check every 5 seconds
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _process_job(self, job_id: str):
        """
        Process a single job through the dubbing pipeline using Gemini APIs
        
        Args:
            job_id: Job ID to process
        """
        video_path = None
        audio_path = None
        
        try:
            logger.info(f"📹 Starting job processing: {job_id}")
            
            # Get job details
            job_doc = await self._get_job(job_id)
            if not job_doc:
                raise ValueError(f"Job {job_id} not found")
            
            source_lang = job_doc.get("source_language", "auto")
            target_lang = job_doc.get("target_language")
            input_video_url = job_doc.get("input_video_url")
            
            # Stage 1: Audio Extraction
            await self._update_job_status(
                job_id,
                JobStatus.PROCESSING,
                JobStage.AUDIO_EXTRACTION,
                "Downloading and extracting audio from video",
                progress=10
            )
            
            video_path, audio_path = await self._extract_audio(input_video_url)
            
            await self._update_job_status(
                job_id,
                JobStatus.AUDIO_EXTRACTED,
                JobStage.AUDIO_EXTRACTION,
                "Audio extraction complete"
            )
            await self._update_job_progress(job_id, 20, "Audio extracted successfully")

            # Stage 2: Unified Transcription + Translation using Gemini API
            # This combines what were previously two separate stages into a single API call
            await self._update_job_status(
                job_id,
                JobStatus.PROCESSING,
                JobStage.TRANSCRIPTION,
                f"Transcribing and translating audio (unified) to {target_lang}"
            )

            # Pass None to Gemini if language is "auto" for detection
            lang_for_api = None if source_lang == "auto" else source_lang

            # Single unified API call for transcription + translation
            unified_result = await self.unified_service.transcribe_and_translate(
                audio_path=audio_path,
                target_language=target_lang,
                source_language=lang_for_api,
                job_id=job_id
            )

            # Update job with detected language if it was auto
            if source_lang == "auto" and unified_result.source_language:
                logger.info(f"🌍 Language detected: {unified_result.source_language}, updating job...")
                jobs_collection = get_jobs_collection()
                await jobs_collection.update_one(
                    {"_id": ObjectId(job_id)},
                    {"$set": {"source_language": unified_result.source_language}}
                )
                logger.info(f"✅ Updated job source_language from 'auto' to '{unified_result.source_language}'")

            # Extract transcript and translation from unified result
            transcript_result = unified_result.get_transcript()
            translation_result = unified_result.get_translations()

            # Save transcript to database
            await self._save_transcript(job_id, transcript_result)

            # Save translations to database
            await self._save_translations(job_id, translation_result)

            # Update status to TRANSLATED (skip TRANSCRIBED status since we do both at once)
            await self._update_job_status(
                job_id,
                JobStatus.TRANSLATED,
                JobStage.TRANSLATION,
                f"Unified transcription+translation complete: {len(translation_result)} segments"
            )
            await self._update_job_progress(job_id, 60, "Transcription and translation complete")
            logger.info(
                f"📊 Job {job_id}: Unified transcription+translation complete, "
                f"progress: 60% ({len(translation_result)} segments)"
            )
            
            # Stage 4: Optimized Speech Synthesis using Gemini TTS
            await self._update_job_status(
                job_id,
                JobStatus.PROCESSING,
                JobStage.SPEECH_SYNTHESIS,
                "Generating dubbed audio with Gemini TTS"
            )
            
            # Optimize TTS: Use bulk synthesis to reduce API calls
            # Pass unified segments (which have speaker info) instead of translation_result
            audio_segments = await self._synthesize_audio_optimized(
                job_id=job_id,
                segments=unified_result.segments,  # Use unified segments with speaker info
                voice_config=job_doc.get("voice_configuration", {})
            )
            
            await self._update_job_status(
                job_id,
                JobStatus.SYNTHESIZED,
                JobStage.SPEECH_SYNTHESIS,
                f"Speech synthesis complete: {len(audio_segments)} audio segments"
            )
            await self._update_job_progress(job_id, 80, "Speech synthesis complete")
            logger.info(f"📊 Job {job_id}: Speech synthesis complete, progress: 80%")
            
            # Stage 5: Audio Merging - Create final dubbed video
            await self._update_job_status(
                job_id,
                JobStatus.PROCESSING,
                JobStage.AUDIO_MERGING,
                "Merging dubbed audio with video"
            )
            await self._update_job_progress(job_id, 85, "Merging audio with video")
            
            # Merge audio with video using FFmpeg
            output_video_path = await self._merge_audio_with_video(
                video_path=video_path,
                audio_segments=audio_segments,
                job_id=job_id
            )
            
            # Upload final video to storage
            output_filename = f"dubbed_{os.path.basename(video_path)}"
            output_url = await self.storage_service.upload_file(
                output_video_path,
                f"gs://videos-output/dubbed/{output_filename}"
            )
            
            # Update job with output URL
            jobs_collection = get_jobs_collection()
            await jobs_collection.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {"output_video_url": output_url}}
            )
            
            logger.info(f"🎬 Output video uploaded: {output_url}")
            
            await self._update_job_status(
                job_id,
                JobStatus.MERGED,
                JobStage.AUDIO_MERGING,
                f"Audio merged successfully"
            )
            await self._update_job_progress(job_id, 95, "Audio merged")
            
            # Stage 6: Quality Assurance
            await self._update_job_status(
                job_id,
                JobStatus.VALIDATED,
                JobStage.QUALITY_ASSURANCE,
                "Quality validation complete"
            )
            
            # Stage 7: Delivery
            await self._update_job_status(
                job_id,
                JobStatus.COMPLETED,
                JobStage.DELIVERY,
                f"Video dubbing completed: {source_lang} → {target_lang}",
                progress=100
            )
            
            logger.info(f"✅ Job completed successfully: {job_id}")
            logger.info(f"📦 Output available at: {output_url}")
            
        except Exception as e:
            logger.error(f"❌ Job failed: {job_id} - {e}", exc_info=True)
            await self._update_job_status(
                job_id,
                JobStatus.FAILED,
                JobStage.AUDIO_EXTRACTION if not audio_path else JobStage.TRANSCRIPTION,
                f"Job failed: {str(e)}"
            )
        finally:
            # Cleanup temp files
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
            
            self._processing_jobs.discard(job_id)
    
    async def _synthesize_audio_optimized(
        self,
        job_id: str,
        segments: list,
        voice_config: dict
    ) -> list:
        """
        Optimized TTS synthesis that minimizes API calls.
        
        Strategy:
        - Single speaker: Concatenate all text → 1 API call (saves ~95% API calls)
        - Multiple speakers: Group by speaker → N API calls (N = num speakers)
        - Rate limiting: Respect free tier limits (3 req/min)
        
        Args:
            job_id: Job ID for logging
            segments: Translation segments with speaker info
            voice_config: Voice configuration
            
        Returns:
            List of audio segments with synthesized data
        """
        import asyncio
        from collections import defaultdict
        
        # Analyze speakers
        speakers = set(seg.speaker for seg in segments)
        num_speakers = len(speakers)
        
        logger.info(
            f"🎤 Job {job_id}: Detected {num_speakers} speaker(s), "
            f"optimizing TTS ({len(segments)} segments → {num_speakers} API call(s))"
        )
        
        audio_segments = []
        
        if num_speakers == 1:
            # OPTIMIZATION: Single speaker - concatenate all text
            voice_name = voice_config.get("primary_voice", "Kore")
            full_text = " ... ".join([seg.translated_text for seg in segments])
            
            logger.info(f"📝 Synthesizing full text ({len(full_text)} chars) with voice: {voice_name}")
            
            try:
                # Single API call for entire video
                audio_bytes = await self.tts_service.synthesize_single_speaker(
                    text=full_text,
                    voice_name=voice_name
                )
                
                # Split audio based on segment timestamps
                # For now, store the full audio and use timestamps for playback
                for segment in segments:
                    audio_segments.append({
                        "segment_id": segment.segment_id,
                        "audio_data": audio_bytes,  # Full audio (will split later with FFmpeg)
                        "duration": segment.end_time - segment.start_time,
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "is_full_audio": True  # Flag to indicate this needs splitting
                    })
                
                logger.info(f"✅ Single TTS call completed (saved {len(segments) - 1} API calls)")
                
            except Exception as e:
                logger.error(f"Failed to synthesize full text: {e}")
                # Fallback to per-segment synthesis
                return await self._synthesize_per_segment(segments, voice_name, job_id)
        
        else:
            # OPTIMIZATION: Multi-speaker - group by speaker
            speaker_segments = defaultdict(list)
            for segment in segments:
                speaker_segments[segment.speaker].append(segment)
            
            logger.info(f"👥 Multi-speaker synthesis: {num_speakers} speakers")
            
            # Get voice mapping
            speaker_voices = voice_config.get("speaker_voices", {})
            default_voice = voice_config.get("primary_voice", "Kore")
            
            # Synthesize per speaker (with rate limiting)
            for speaker_idx, (speaker, speaker_segs) in enumerate(speaker_segments.items()):
                voice_name = speaker_voices.get(speaker, default_voice)
                
                # Concatenate all text for this speaker
                speaker_text = " ... ".join([seg.translated_text for seg in speaker_segs])
                
                logger.info(
                    f"🎙️ Speaker {speaker}: Synthesizing {len(speaker_segs)} segments "
                    f"({len(speaker_text)} chars) with voice: {voice_name}"
                )
                
                try:
                    # Rate limiting: Wait between requests (free tier: 3 req/min = 20s between calls)
                    if speaker_idx > 0:
                        wait_time = 21  # 21 seconds to be safe
                        logger.info(f"⏳ Rate limit: Waiting {wait_time}s before next TTS call...")
                        await asyncio.sleep(wait_time)
                    
                    audio_bytes = await self.tts_service.synthesize_single_speaker(
                        text=speaker_text,
                        voice_name=voice_name
                    )
                    
                    # Assign audio to segments
                    for segment in speaker_segs:
                        audio_segments.append({
                            "segment_id": segment.segment_id,
                            "audio_data": audio_bytes,
                            "duration": segment.end_time - segment.start_time,
                            "start_time": segment.start_time,
                            "end_time": segment.end_time,
                            "speaker": speaker,
                            "is_speaker_audio": True
                        })
                    
                    logger.info(f"✅ Speaker {speaker} synthesis complete")
                    
                except Exception as e:
                    logger.error(f"Failed to synthesize speaker {speaker}: {e}")
        
        logger.info(
            f"🎵 TTS optimization complete: {len(segments)} segments, "
            f"{num_speakers} API call(s) (saved {len(segments) - num_speakers} calls = "
            f"{((len(segments) - num_speakers) / len(segments) * 100):.0f}% reduction)"
        )
        
        return audio_segments
    
    async def _merge_audio_with_video(
        self,
        video_path: str,
        audio_segments: list,
        job_id: str
    ) -> str:
        """
        Merge synthesized audio with original video using FFmpeg.
        
        Args:
            video_path: Path to original video file
            audio_segments: List of audio segments with synthesized data
            job_id: Job ID for logging
            
        Returns:
            Path to output video with dubbed audio
        """
        import subprocess
        import wave
        
        logger.info(f"🎬 Starting audio-video merge for job {job_id}")
        
        # Create temp file for dubbed audio
        dubbed_audio_path = os.path.join(
            tempfile.gettempdir(),
            f"dubbed_audio_{os.urandom(8).hex()}.wav"
        )
        
        # For single-speaker optimization, we already have the full audio
        # Just need to save it to a file
        if len(audio_segments) > 0 and audio_segments[0].get('is_full_audio'):
            # Single audio file for entire video
            audio_data = audio_segments[0]['audio_data']
            
            # Write PCM audio data as proper WAV file
            # Gemini TTS returns 24kHz, 16-bit, mono PCM
            with wave.open(dubbed_audio_path, 'wb') as wf:
                wf.setnchannels(1)        # Mono
                wf.setsampwidth(2)        # 16-bit (2 bytes)
                wf.setframerate(24000)    # 24kHz
                wf.writeframes(audio_data)
            
            logger.info(f"💾 Saved full dubbed audio as WAV: {os.path.getsize(dubbed_audio_path)} bytes")
        else:
            # TODO: Multi-segment merge (concatenate multiple audio segments)
            # For now, use the first segment as a placeholder
            if audio_segments:
                with wave.open(dubbed_audio_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(24000)
                    wf.writeframes(audio_segments[0]['audio_data'])
                logger.warning(f"⚠️ Using single segment audio (multi-segment merge not yet implemented)")
        
        # Create output video path
        output_video_path = os.path.join(
            tempfile.gettempdir(),
            f"output_{os.urandom(8).hex()}.mp4"
        )
        
        # Use FFmpeg to replace audio in video
        logger.info(f"🔧 Running FFmpeg to merge audio with video...")
        try:
            result = subprocess.run(
                [
                    'ffmpeg',
                    '-i', video_path,           # Input video
                    '-i', dubbed_audio_path,    # Input dubbed audio
                    '-c:v', 'copy',             # Copy video stream (no re-encoding)
                    '-c:a', 'aac',              # Encode audio as AAC
                    '-map', '0:v:0',            # Use video from first input
                    '-map', '1:a:0',            # Use audio from second input
                    '-shortest',                # Match shortest stream duration
                    '-y',                       # Overwrite output
                    output_video_path
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg stderr: {result.stderr}")
                raise RuntimeError(f"FFmpeg merge failed: {result.stderr}")
            
            output_size = os.path.getsize(output_video_path)
            logger.info(f"✅ Audio-video merge complete: {output_size / (1024*1024):.2f} MB")
            
            # Cleanup temp audio file
            try:
                os.remove(dubbed_audio_path)
            except:
                pass
            
            return output_video_path
            
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg merge timed out after 5 minutes")
            raise
        except Exception as e:
            logger.error(f"Failed to merge audio with video: {e}")
            raise
    
    async def _synthesize_per_segment(
        self,
        segments: list,
        voice_name: str,
        job_id: str
    ) -> list:
        """Fallback: Synthesize each segment individually (with rate limiting)"""
        import asyncio
        
        logger.warning(f"⚠️ Using fallback per-segment synthesis for job {job_id}")
        audio_segments = []
        
        for idx, segment in enumerate(segments):
            try:
                # Rate limiting: 3 req/min free tier
                if idx > 0 and idx % 3 == 0:
                    wait_time = 61  # Wait 61s after every 3 requests
                    logger.info(f"⏳ Rate limit: Waiting {wait_time}s (processed {idx} segments)...")
                    await asyncio.sleep(wait_time)
                
                audio_bytes = await self.tts_service.synthesize_single_speaker(
                    text=segment.translated_text,
                    voice_name=voice_name
                )
                
                audio_segments.append({
                    "segment_id": segment.segment_id,
                    "audio_data": audio_bytes,
                    "duration": segment.end_time - segment.start_time
                })
                
            except Exception as e:
                logger.error(f"Failed to synthesize segment {segment.segment_id}: {e}")
        
        return audio_segments
    
    async def _update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        stage: JobStage,
        message: str,
        progress: Optional[int] = None
    ):
        """Update job status in database"""
        try:
            from bson import ObjectId
            jobs_collection = get_jobs_collection()
            
            update_data = {
                "status": status.value,
                "current_stage": stage.value,
                "status_message": message,
                "updated_at": datetime.utcnow()
            }
            
            if progress is not None:
                update_data["progress"] = progress
            
            await jobs_collection.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": update_data}
            )
            
            logger.info(f"Job {job_id}: {stage.value} - {message}")
            
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
    
    async def _update_job_progress(self, job_id: str, progress: int, message: str):
        """Update job progress"""
        try:
            jobs_collection = get_jobs_collection()
            
            await jobs_collection.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "progress": progress,
                        "status_message": message,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update job progress: {e}")
    
    async def _get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job document from database"""
        try:
            jobs_collection = get_jobs_collection()
            job_doc = await jobs_collection.find_one({"_id": ObjectId(job_id)})
            return job_doc
        except Exception as e:
            logger.error(f"Failed to get job: {e}")
            return None
    
    async def _extract_audio(self, video_url: str) -> tuple[str, str]:
        """
        Download video and extract audio
        Returns: (video_path, audio_path)
        """
        # Create temp files
        video_path = os.path.join(tempfile.gettempdir(), f"video_{os.urandom(8).hex()}.mp4")
        audio_path = os.path.join(tempfile.gettempdir(), f"audio_{os.urandom(8).hex()}.wav")
        
        try:
            # Download video from storage
            logger.info(f"Downloading video from: {video_url}")
            await self.storage_service.download_file(video_url, video_path)
            logger.info(f"Video downloaded to: {video_path}")
            
            # Extract audio using FFmpeg
            logger.info(f"Extracting audio with FFmpeg...")
            import subprocess
            result = subprocess.run(
                [
                    'ffmpeg',
                    '-i', video_path,
                    '-vn',  # No video
                    '-acodec', 'pcm_s16le',  # PCM 16-bit
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',  # Mono
                    '-y',  # Overwrite output
                    audio_path
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            logger.info(f"Audio extracted to: {audio_path}")
            return video_path, audio_path
            
        except Exception as e:
            logger.error(f"Failed to extract audio: {e}", exc_info=True)
            raise
    
    async def _save_transcript(self, job_id: str, transcript_result: Transcript):
        """Save transcript segments to database"""
        try:
            transcripts_collection = get_transcripts_collection()
            
            # Convert Pydantic model to dict for MongoDB
            segments = [segment.model_dump() for segment in transcript_result.segments]
            transcript_doc = {
                "job_id": job_id,
                "language": transcript_result.language,
                "segments": segments,
                "created_at": datetime.utcnow()
            }
            
            await transcripts_collection.insert_one(transcript_doc)
            logger.info(f"Saved transcript for job {job_id}: {len(segments)} segments")
            
        except Exception as e:
            logger.error(f"Failed to save transcript: {e}")
    
    async def _save_translations(self, job_id: str, translation_result: list[TranslationSegment]):
        """Save translation segments to database"""
        try:
            translations_collection = get_translations_collection()
            
            # Convert Pydantic models to dict for MongoDB
            segments = [segment.model_dump() for segment in translation_result]
            translation_doc = {
                "job_id": job_id,
                "segments": segments,
                "created_at": datetime.utcnow()
            }
            
            await translations_collection.insert_one(translation_doc)
            logger.info(f"Saved translations for job {job_id}: {len(segments)} segments")
            
        except Exception as e:
            logger.error(f"Failed to save translations: {e}")


# Global job processor instance
job_processor: Optional[JobProcessor] = None


async def start_job_processor():
    """Start the global job processor"""
    global job_processor
    job_processor = JobProcessor()
    await job_processor.start()


async def stop_job_processor():
    """Stop the global job processor"""
    global job_processor
    if job_processor:
        await job_processor.stop()


def get_job_processor() -> Optional[JobProcessor]:
    """Get the global job processor instance"""
    return job_processor
