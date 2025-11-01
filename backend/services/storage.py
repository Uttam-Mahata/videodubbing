"""
Google Cloud Storage Service
Handles file upload/download operations
"""

import logging
from typing import Optional
from datetime import timedelta, datetime
import os
import uuid
import aiofiles
from fastapi import UploadFile

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service for Google Cloud Storage operations
    
    Features:
    - Upload/download files
    - Generate signed URLs
    - Lifecycle management
    """
    
    def __init__(self):
        """Initialize Google Cloud Storage client"""
        self._client = None
        self._force_mock = False  # Flag to force mock mode after billing error
        
        # Try to initialize GCS client
        try:
            from google.cloud import storage
            
            # Try gcloud CLI authentication first
            try:
                self._client = storage.Client(project=settings.gcs_project_id)
                logger.info("✅ Google Cloud Storage client initialized (using gcloud auth)")
            except Exception as gcloud_error:
                # Fallback to credentials file if provided
                if settings.gcs_credentials_path and os.path.exists(settings.gcs_credentials_path):
                    self._client = storage.Client.from_service_account_json(
                        settings.gcs_credentials_path,
                        project=settings.gcs_project_id
                    )
                    logger.info("✅ Google Cloud Storage client initialized (using service account)")
                else:
                    logger.warning(f"⚠️ Failed to initialize GCS client: {gcloud_error}")
                    logger.info("Running in mock mode for development")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize GCS client: {e}")
            logger.info("Running in mock mode for development")
    
    @property
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode"""
        return self._client is None or self._force_mock
    
    async def upload_video(
        self,
        video_file: UploadFile,
        bucket_name: str,
    ) -> str:
        """
        Upload video file to GCS
        
        Args:
            video_file: FastAPI UploadFile object
            bucket_name: GCS bucket name
            
        Returns:
            GCS URI (gs://bucket/path)
        """
        try:
            # Generate unique blob name
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_ext = os.path.splitext(video_file.filename or "video.mp4")[1]
            blob_name = f"videos/{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"
            
            if self.is_mock_mode:
                # Mock mode: save to local temp storage
                local_path = os.path.join(settings.temp_storage_path, blob_name)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                async with aiofiles.open(local_path, 'wb') as f:
                    content = await video_file.read()
                    await f.write(content)
                
                logger.info(f"📁 Mock upload: saved to {local_path}")
                return f"gs://{bucket_name}/{blob_name}"
            
            # Real GCS upload
            logger.info(f"Uploading to gs://{bucket_name}/{blob_name}")
            
            try:
                bucket = self._client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                
                # Upload from file-like object
                await video_file.seek(0)
                content = await video_file.read()
                blob.upload_from_string(content, content_type=video_file.content_type)
                
                logger.info(f"✅ Uploaded to gs://{bucket_name}/{blob_name}")
                return f"gs://{bucket_name}/{blob_name}"
                
            except Exception as gcs_error:
                # Fallback to local storage on any GCS error
                error_msg = str(gcs_error)
                if "billing" in error_msg.lower() or "accountDisabled" in error_msg or "403" in error_msg:
                    logger.warning(f"⚠️ GCS error (billing/permissions), permanently switching to local storage")
                    self._force_mock = True  # Force all future operations to use local storage
                else:
                    logger.warning(f"⚠️ GCS upload failed, falling back to local storage: {error_msg}")
                
                # Save to local storage
                local_path = os.path.join(settings.temp_storage_path, blob_name)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                await video_file.seek(0)
                async with aiofiles.open(local_path, 'wb') as f:
                    content = await video_file.read()
                    await f.write(content)
                
                logger.info(f"📁 Saved to local storage: {local_path}")
                return f"gs://{bucket_name}/{blob_name}"
            
        except Exception as e:
            logger.error(f"Failed to upload video: {e}", exc_info=True)
            raise
    
    async def upload_file(
        self,
        local_path: str,
        bucket_name: str,
        blob_name: str,
    ) -> str:
        """
        Upload file from local path to GCS
        
        Args:
            local_path: Local file path
            bucket_name: GCS bucket name
            blob_name: Destination blob name
            
        Returns:
            GCS URI
        """
        logger.info(f"Uploading {local_path} to gs://{bucket_name}/{blob_name}")
        
        if self.is_mock_mode:
            logger.info(f"📁 Mock mode: file at {local_path}")
            return f"gs://{bucket_name}/{blob_name}"
        
        # Real GCS upload
        bucket = self._client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        
        logger.info(f"✅ Uploaded to gs://{bucket_name}/{blob_name}")
        return f"gs://{bucket_name}/{blob_name}"
    
    async def download_file(
        self,
        gcs_uri: str,
        local_path: str,
    ):
        """
        Download file from GCS
        
        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            local_path: Local destination path
        """
        # Parse GCS URI
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        uri_parts = gcs_uri[5:].split("/", 1)
        bucket_name = uri_parts[0]
        blob_name = uri_parts[1] if len(uri_parts) > 1 else ""
        
        logger.info(f"Downloading gs://{bucket_name}/{blob_name} to {local_path}")
        
        if self.is_mock_mode:
            # Mock mode: copy from temp storage
            mock_path = os.path.join(settings.temp_storage_path, blob_name)
            if os.path.exists(mock_path):
                async with aiofiles.open(mock_path, 'rb') as src:
                    content = await src.read()
                    async with aiofiles.open(local_path, 'wb') as dst:
                        await dst.write(content)
                logger.info(f"📁 Mock download: copied from {mock_path}")
            else:
                logger.warning(f"⚠️ Mock file not found: {mock_path}")
            return
        
        # Real GCS download
        bucket = self._client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_path)
        
        logger.info(f"✅ Downloaded to {local_path}")
    
    async def generate_signed_url(
        self,
        gcs_uri: str,
        expiration_hours: int = 24,
    ) -> str:
        """
        Generate signed URL for temporary access
        
        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            expiration_hours: URL validity in hours
            
        Returns:
            Signed URL
        """
        # Parse GCS URI
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        uri_parts = gcs_uri[5:].split("/", 1)
        bucket_name = uri_parts[0]
        blob_name = uri_parts[1] if len(uri_parts) > 1 else ""
        
        logger.info(f"Generating signed URL for gs://{bucket_name}/{blob_name}")
        
        if self.is_mock_mode:
            # Mock URL for development
            return f"https://storage.googleapis.com/{bucket_name}/{blob_name}?expires={expiration_hours}h&mock=true"
        
        # Real GCS signed URL
        bucket = self._client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=expiration_hours),
            method="GET",
        )
        
        logger.info(f"✅ Generated signed URL (expires in {expiration_hours}h)")
        return url
    
    async def delete_file(self, gcs_uri: str) -> bool:
        """
        Delete file from GCS
        
        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            
        Returns:
            True if deleted successfully
        """
        # Parse GCS URI
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        uri_parts = gcs_uri[5:].split("/", 1)
        bucket_name = uri_parts[0]
        blob_name = uri_parts[1] if len(uri_parts) > 1 else ""
        
        logger.info(f"Deleting gs://{bucket_name}/{blob_name}")
        
        try:
            if self.is_mock_mode:
                # Mock mode: delete from temp storage
                mock_path = os.path.join(settings.temp_storage_path, blob_name)
                if os.path.exists(mock_path):
                    os.remove(mock_path)
                    logger.info(f"📁 Mock delete: removed {mock_path}")
                return True
            
            # Real GCS delete
            bucket = self._client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            
            logger.info(f"✅ Deleted gs://{bucket_name}/{blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    async def file_exists(self, gcs_uri: str) -> bool:
        """
        Check if file exists in GCS
        
        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            
        Returns:
            True if file exists
        """
        # Parse GCS URI
        if not gcs_uri.startswith("gs://"):
            return False
        
        uri_parts = gcs_uri[5:].split("/", 1)
        bucket_name = uri_parts[0]
        blob_name = uri_parts[1] if len(uri_parts) > 1 else ""
        
        try:
            if self.is_mock_mode:
                mock_path = os.path.join(settings.temp_storage_path, blob_name)
                return os.path.exists(mock_path)
            
            bucket = self._client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.exists()
            
        except Exception as e:
            logger.error(f"Failed to check file existence: {e}")
            return False
