"""Database connection management"""

from backend.db.mongodb import (
    get_database,
    close_database_connection,
    connect_to_mongodb,
    get_jobs_collection,
    get_logs_collection,
    get_transcripts_collection,
    get_translations_collection,
)
from backend.db.redis_client import (
    get_redis,
    close_redis_connection,
    connect_to_redis,
    RedisCache,
    JobStatusCache,
    TranslationCache,
    TTSCache,
)
from backend.db.repositories import (
    JobRepository,
    ProcessingLogRepository,
    TranscriptRepository,
    TranslationRepository,
)

__all__ = [
    # MongoDB
    "get_database",
    "close_database_connection",
    "connect_to_mongodb",
    "get_jobs_collection",
    "get_logs_collection",
    "get_transcripts_collection",
    "get_translations_collection",
    # Redis
    "get_redis",
    "close_redis_connection",
    "connect_to_redis",
    "RedisCache",
    "JobStatusCache",
    "TranslationCache",
    "TTSCache",
    # Repositories
    "JobRepository",
    "ProcessingLogRepository",
    "TranscriptRepository",
    "TranslationRepository",
]
