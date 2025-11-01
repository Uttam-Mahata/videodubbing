"""Repository pattern for database operations"""

from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from backend.db.mongodb import (
    get_jobs_collection,
    get_logs_collection,
    get_transcripts_collection,
    get_translations_collection,
)
from backend.models.job import Job, JobStatus, JobStage, Checkpoint


class JobRepository:
    """Repository for job-related database operations"""
    
    @staticmethod
    async def create(job: Job) -> str:
        """
        Create a new job in the database.
        
        Args:
            job: Job model instance
            
        Returns:
            str: Created job ID
        """
        collection = get_jobs_collection()
        job_dict = job.model_dump(by_alias=True, exclude={"id"})
        result = await collection.insert_one(job_dict)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_by_id(job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job model or None if not found
        """
        collection = get_jobs_collection()
        job_data = await collection.find_one({"_id": ObjectId(job_id)})
        if job_data:
            job_data["_id"] = str(job_data["_id"])
            return Job(**job_data)
        return None
    
    @staticmethod
    async def get_by_user(
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[JobStatus] = None
    ) -> List[Job]:
        """
        Get jobs by user ID.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            
        Returns:
            List of Job models
        """
        collection = get_jobs_collection()
        query = {"user_id": user_id}
        if status:
            query["status"] = status.value
        
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        jobs = []
        async for job_data in cursor:
            job_data["_id"] = str(job_data["_id"])
            jobs.append(Job(**job_data))
        return jobs
    
    @staticmethod
    async def count_by_user(user_id: str, status: Optional[JobStatus] = None) -> int:
        """
        Count jobs by user ID.
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            Count of jobs
        """
        collection = get_jobs_collection()
        query = {"user_id": user_id}
        if status:
            query["status"] = status.value
        return await collection.count_documents(query)
    
    @staticmethod
    async def update_status(
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            error_message: Optional error message
            
        Returns:
            True if updated successfully
        """
        collection = get_jobs_collection()
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }
        
        if error_message:
            update_data["error_message"] = error_message
        
        if status == JobStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
        
        result = await collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_progress(
        job_id: str,
        progress_percent: int,
        current_stage: Optional[JobStage] = None
    ) -> bool:
        """
        Update job progress.
        
        Args:
            job_id: Job ID
            progress_percent: Progress percentage (0-100)
            current_stage: Optional current processing stage
            
        Returns:
            True if updated successfully
        """
        collection = get_jobs_collection()
        update_data = {
            "progress_percent": progress_percent,
            "updated_at": datetime.utcnow(),
        }
        
        if current_stage:
            update_data["current_stage"] = current_stage.value
        
        result = await collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def add_checkpoint(job_id: str, checkpoint: Checkpoint) -> bool:
        """
        Add a checkpoint to job.
        
        Args:
            job_id: Job ID
            checkpoint: Checkpoint data
            
        Returns:
            True if added successfully
        """
        collection = get_jobs_collection()
        result = await collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$push": {"checkpoints": checkpoint.model_dump()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_output_url(job_id: str, output_url: str) -> bool:
        """
        Update job output video URL.
        
        Args:
            job_id: Job ID
            output_url: Output video URL
            
        Returns:
            True if updated successfully
        """
        collection = get_jobs_collection()
        result = await collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "output_video_url": output_url,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    async def delete(job_id: str) -> bool:
        """
        Delete a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if deleted successfully
        """
        collection = get_jobs_collection()
        result = await collection.delete_one({"_id": ObjectId(job_id)})
        return result.deleted_count > 0


class ProcessingLogRepository:
    """Repository for processing log operations"""
    
    @staticmethod
    async def create_log(
        job_id: str,
        level: str,
        message: str,
        stage: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Create a processing log entry.
        
        Args:
            job_id: Job ID
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            stage: Optional processing stage
            metadata: Optional additional metadata
            
        Returns:
            Created log ID
        """
        collection = get_logs_collection()
        log_data = {
            "job_id": job_id,
            "level": level,
            "message": message,
            "stage": stage,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow(),
        }
        result = await collection.insert_one(log_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_logs_by_job(
        job_id: str,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Get logs for a specific job.
        
        Args:
            job_id: Job ID
            level: Optional log level filter
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries
        """
        collection = get_logs_collection()
        query = {"job_id": job_id}
        if level:
            query["level"] = level
        
        cursor = collection.find(query).sort("timestamp", -1).limit(limit)
        logs = []
        async for log_data in cursor:
            log_data["_id"] = str(log_data["_id"])
            logs.append(log_data)
        return logs


class TranscriptRepository:
    """Repository for transcript operations"""
    
    @staticmethod
    async def save_transcript(job_id: str, transcript_data: dict) -> str:
        """
        Save transcript for a job.
        
        Args:
            job_id: Job ID
            transcript_data: Transcript data
            
        Returns:
            Created transcript ID
        """
        collection = get_transcripts_collection()
        data = {
            "job_id": job_id,
            "transcript": transcript_data,
            "created_at": datetime.utcnow(),
        }
        result = await collection.insert_one(data)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_transcript(job_id: str) -> Optional[dict]:
        """
        Get transcript for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Transcript data or None
        """
        collection = get_transcripts_collection()
        data = await collection.find_one({"job_id": job_id})
        if data:
            data["_id"] = str(data["_id"])
            return data
        return None


class TranslationRepository:
    """Repository for translation operations"""
    
    @staticmethod
    async def save_translation(job_id: str, translation_data: dict) -> str:
        """
        Save translation for a job.
        
        Args:
            job_id: Job ID
            translation_data: Translation data
            
        Returns:
            Created translation ID
        """
        collection = get_translations_collection()
        data = {
            "job_id": job_id,
            "translation": translation_data,
            "created_at": datetime.utcnow(),
        }
        result = await collection.insert_one(data)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_translation(job_id: str) -> Optional[dict]:
        """
        Get translation for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Translation data or None
        """
        collection = get_translations_collection()
        data = await collection.find_one({"job_id": job_id})
        if data:
            data["_id"] = str(data["_id"])
            return data
        return None
