"""
Application Settings
Centralized configuration using Pydantic BaseSettings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, Union
import os
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="null"
    )
    
    # Application
    app_name: str = "Video Dubbing API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    
    # API Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 4
    
    # Security
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Google Gemini API
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    gemini_model_flash: str = "gemini-2.5-flash"
    gemini_model_pro: str = "gemini-2.5-pro"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    
    # Google Cloud Storage
    gcs_bucket_input: str = "videos-input"
    gcs_bucket_processing: str = "videos-processing"
    gcs_bucket_output: str = "videos-output"
    gcs_project_id: Optional[str] = Field(default=None, validation_alias="GCS_PROJECT_ID")
    gcs_credentials_path: Optional[str] = Field(default=None, validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
    use_local_storage: bool = False  # Force local storage instead of GCS
    
    # MongoDB
    mongodb_url: str = Field(default="mongodb://localhost:27017", validation_alias="MONGODB_URL")
    mongodb_db_name: str = "videodubbing"
    mongodb_max_pool_size: int = 50
    mongodb_min_pool_size: int = 10
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    redis_max_connections: int = 50
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1", validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", validation_alias="CELERY_RESULT_BACKEND")
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 100
    
    # File Upload
    max_upload_size_mb: int = 500
    allowed_video_formats: list[str] = ["mp4", "avi", "mov", "mkv", "webm"]
    temp_storage_path: str = "/tmp/videodubbing"
    
    # Processing
    max_video_duration_minutes: int = 120
    segment_min_duration_seconds: int = 300  # 5 minutes
    segment_max_duration_seconds: int = 900  # 15 minutes
    segment_overlap_seconds: int = 5
    max_parallel_segments: int = 6
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60
    circuit_breaker_half_open_test_requests: int = 3
    
    # Retry Logic
    max_retry_attempts: int = 3
    retry_backoff_multiplier: float = 2.0
    retry_max_delay_seconds: int = 60
    
    # Cache TTL (seconds)
    cache_ttl_translation: int = 604800  # 7 days
    cache_ttl_tts: int = 2592000  # 30 days
    cache_ttl_job_status: int = 86400  # 24 hours
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    # CORS
    cors_origins: Union[str, list[str]] = "http://localhost:5173,http://localhost:3000"
    
    @field_validator("temp_storage_path")
    @classmethod
    def create_temp_dir(cls, v: str) -> str:
        """Ensure temp storage directory exists"""
        os.makedirs(v, exist_ok=True)
        return v
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


# Global settings instance
settings = Settings()
