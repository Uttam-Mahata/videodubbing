"""
Job Management Endpoints
CRUD operations for dubbing jobs
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from typing import Optional
import logging
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

from backend.models.job import (
    JobCreate,
    JobResponse,
    JobListResponse,
    JobStatus,
    JobStage,
    Job,
    VoiceConfiguration,
    VideoMetadata,
)
from backend.db import (
    JobRepository,
    ProcessingLogRepository,
    JobStatusCache,
)
from backend.services.storage import StorageService
from backend.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/jobs/create", response_model=JobResponse, status_code=201)
async def create_job(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(..., description="Video file to dub"),
    source_language: str = Form(..., description="Source language (BCP-47)"),
    target_language: str = Form(..., description="Target language (BCP-47)"),
    primary_voice: str = Form(default="Kore", description="Primary voice for TTS"),
    secondary_voice: Optional[str] = Form(default=None, description="Secondary voice"),
    user_id: str = Form(default="default_user", description="User ID"),
):
    """
    Create a new dubbing job
    
    **Process:**
    1. Upload video file to temporary storage
    2. Create job record in database
    3. Queue job for processing
    4. Return job ID and initial status
    
    **Rate Limit:** 10 requests/hour per user
    """
    logger.info(f"Creating job: {source_language} -> {target_language}")
    
    try:
        # Validate video file
        if not video.content_type or not video.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Invalid video file")
        
        # Check file size
        file_size_mb = 0
        if video.size:
            file_size_mb = video.size / (1024 * 1024)
            if file_size_mb > settings.max_upload_size_mb:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum of {settings.max_upload_size_mb}MB"
                )
        
        # Upload to GCS
        storage_service = StorageService()
        input_video_url = await storage_service.upload_video(
            video_file=video,
            bucket_name=settings.gcs_bucket_input
        )
        logger.info(f"Video uploaded to: {input_video_url}")
        
        # Create voice configuration
        voice_config = VoiceConfiguration(
            primary_voice=primary_voice,
            secondary_voice=secondary_voice,
            style_preferences={}
        )
        
        # Create job record
        job = Job(
            user_id=user_id,
            status=JobStatus.QUEUED,
            source_language=source_language,
            target_language=target_language,
            voice_config=voice_config,
            input_video_url=input_video_url,
            metadata=VideoMetadata(
                duration_seconds=0.0,  # Will be populated during processing
                file_size_mb=file_size_mb,
                resolution="unknown",
            )
        )
        
        # Save to MongoDB
        job_id = await JobRepository.create(job)
        logger.info(f"Job created with ID: {job_id}")
        
        # Create processing log
        await ProcessingLogRepository.create_log(
            job_id=job_id,
            level="INFO",
            message="Job created successfully",
            stage="intake",
            metadata={
                "source_language": source_language,
                "target_language": target_language,
                "video_url": input_video_url,
            }
        )
        
        # Queue job for processing (background task)
        # TODO: Implement job queue trigger
        # background_tasks.add_task(trigger_job_processing, job_id)
        
        # Cache job status
        await JobStatusCache.set_status(job_id, {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "progress_percent": 0,
        })
        
        return JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            current_stage=None,
            progress_percent=0,
            estimated_time_minutes=15,  # TODO: Calculate based on video duration
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """
    Get job status and progress
    
    **Returns:**
    - Job ID
    - Current status
    - Processing stage
    - Progress percentage
    - Download URL (if completed)
    
    **Rate Limit:** 60 requests/minute
    """
    logger.info(f"Getting job: {job_id}")
    
    try:
        # Validate job ID format
        try:
            ObjectId(job_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Try cache first
        cached_status = await JobStatusCache.get_status(job_id)
        if cached_status:
            logger.debug(f"Job status retrieved from cache: {job_id}")
        
        # Fetch from database
        job = await JobRepository.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Generate download URL if completed
        download_url = None
        if job.status == JobStatus.COMPLETED and job.output_video_url:
            storage_service = StorageService()
            download_url = await storage_service.generate_signed_url(
                job.output_video_url,
                expiration_hours=24
            )
        
        # Estimate remaining time
        estimated_time = None
        if job.status in [JobStatus.PROCESSING, JobStatus.QUEUED]:
            # Simple estimation based on progress
            if job.progress_percent > 0:
                elapsed_minutes = (datetime.utcnow() - job.created_at).total_seconds() / 60
                estimated_total = elapsed_minutes / (job.progress_percent / 100)
                estimated_time = int(estimated_total - elapsed_minutes)
        
        return JobResponse(
            job_id=str(job.id) if job.id else job_id,
            status=job.status,
            current_stage=job.current_stage,
            progress_percent=job.progress_percent,
            estimated_time_minutes=estimated_time,
            download_url=download_url,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    user_id: str = Query(default="default_user", description="User ID"),
    status: Optional[JobStatus] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
):
    """
    List user's jobs with pagination
    
    **Query Parameters:**
    - user_id: User ID
    - status: Filter by job status
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    """
    logger.info(f"Listing jobs: user_id={user_id}, status={status}, page={page}")
    
    try:
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Fetch jobs from MongoDB
        jobs = await JobRepository.get_by_user(
            user_id=user_id,
            skip=skip,
            limit=page_size,
            status=status
        )
        
        # Get total count
        total = await JobRepository.count_by_user(user_id=user_id, status=status)
        
        # Convert to response models
        job_responses = []
        for job in jobs:
            # Generate download URL if completed
            download_url = None
            if job.status == JobStatus.COMPLETED and job.output_video_url:
                storage_service = StorageService()
                download_url = await storage_service.generate_signed_url(
                    job.output_video_url,
                    expiration_hours=24
                )
            
            job_responses.append(JobResponse(
                job_id=str(job.id) if job.id else "",
                status=job.status,
                current_stage=job.current_stage,
                progress_percent=job.progress_percent,
                download_url=download_url,
                created_at=job.created_at,
                updated_at=job.updated_at,
            ))
        
        return JobListResponse(
            jobs=job_responses,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/jobs/{job_id}/download")
async def download_job(job_id: str):
    """
    Get download URL for completed job
    
    **Returns:**
    - Signed URL with 24-hour validity
    
    **Rate Limit:** 100 requests/hour
    """
    logger.info(f"Getting download URL for job: {job_id}")
    
    try:
        # Validate job ID
        try:
            ObjectId(job_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Check job status
        job = await JobRepository.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Job is not completed (current status: {job.status.value})"
            )
        
        if not job.output_video_url:
            raise HTTPException(status_code=500, detail="Output video URL not found")
        
        # Generate signed URL
        storage_service = StorageService()
        signed_url = await storage_service.generate_signed_url(
            job.output_video_url,
            expiration_hours=24
        )
        
        return {
            "job_id": job_id,
            "download_url": signed_url,
            "expires_in_hours": 24,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get download URL: {str(e)}")


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel or delete a job
    
    **Actions:**
    - If processing: Cancel and clean up
    - If completed: Delete output files
    - Update job status to CANCELLED
    """
    logger.info(f"Cancelling job: {job_id}")
    
    try:
        # Validate job ID
        try:
            ObjectId(job_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Get job
        job = await JobRepository.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Cancel job processing
        # TODO: Send cancellation signal to worker if job is processing
        
        # Update job status
        await JobRepository.update_status(
            job_id=job_id,
            status=JobStatus.CANCELLED
        )
        
        # Create log entry
        await ProcessingLogRepository.create_log(
            job_id=job_id,
            level="INFO",
            message="Job cancelled by user",
            stage="cancellation",
        )
        
        # Clear cache
        await JobStatusCache.delete_status(job_id)
        
        # Clean up files (optional, can be done in background)
        # storage_service = StorageService()
        # if job.output_video_url:
        #     await storage_service.delete_file(job.output_video_url)
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"Job {job_id} cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: str):
    """
    Retry a failed job
    
    **Conditions:**
    - Job must be in FAILED status
    - Retry count must be below maximum
    """
    logger.info(f"Retrying job: {job_id}")
    
    try:
        # Validate job ID
        try:
            ObjectId(job_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Check job status
        job = await JobRepository.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != JobStatus.FAILED:
            raise HTTPException(
                status_code=400,
                detail=f"Job cannot be retried (current status: {job.status.value})"
            )
        
        # Reset job state
        await JobRepository.update_status(
            job_id=job_id,
            status=JobStatus.QUEUED,
            error_message=None
        )
        
        await JobRepository.update_progress(
            job_id=job_id,
            progress_percent=0,
            current_stage=None
        )
        
        # Create log entry
        await ProcessingLogRepository.create_log(
            job_id=job_id,
            level="INFO",
            message="Job retry initiated",
            stage="retry",
        )
        
        # Clear cache and update
        await JobStatusCache.set_status(job_id, {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "progress_percent": 0,
        })
        
        # Requeue for processing
        # TODO: Trigger job processing
        
        return JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            current_stage=None,
            progress_percent=0,
            estimated_time_minutes=15,
            created_at=job.created_at,
            updated_at=datetime.utcnow(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retry job: {str(e)}")


@router.get("/jobs/{job_id}/speakers")
async def get_speaker_analysis(job_id: str):
    """
    Get speaker analysis for a job
    
    **Returns:**
    - Number of detected speakers
    - Speaker profiles with emotions and voice assignments
    - Detected language
    
    **Note:** Only available after transcription stage
    """
    logger.info(f"Getting speaker analysis for job: {job_id}")
    
    try:
        # Validate job ID
        try:
            ObjectId(job_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Get job
        job = await JobRepository.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if job has progressed past transcription
        if job.status == JobStatus.QUEUED or job.status == JobStatus.PROCESSING:
            return {
                "job_id": job_id,
                "status": "pending",
                "message": "Speaker analysis not yet available"
            }
        
        # Get metadata
        metadata = job.metadata
        if not metadata:
            raise HTTPException(status_code=404, detail="Metadata not available")
        
        # For now, return metadata-level speaker info
        # TODO: Implement full SpeakerAnalysis with detailed profiles from transcript
        return {
            "job_id": job_id,
            "status": "completed",
            "total_speakers": metadata.detected_speakers or 1,
            "detected_language": metadata.detected_language or job.source_language,
            "language_confidence": metadata.language_confidence or 1.0,
            "voice_assignments": job.voice_config.speaker_voice_map if job.voice_config else {},
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get speaker analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get speaker analysis: {str(e)}")
