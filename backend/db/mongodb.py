"""MongoDB connection management"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Global MongoDB client
_mongodb_client: Optional[AsyncIOMotorClient] = None
_mongodb_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb() -> AsyncIOMotorDatabase:
    """
    Initialize MongoDB connection with connection pooling.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
        
    Raises:
        ConnectionFailure: If connection fails
    """
    global _mongodb_client, _mongodb_database
    
    try:
        logger.info(f"Connecting to MongoDB: {settings.mongodb_url}")
        
        # Create client with connection pooling
        _mongodb_client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=settings.mongodb_max_pool_size,
            minPoolSize=settings.mongodb_min_pool_size,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True,
            w="majority",
        )
        
        # Verify connection
        await _mongodb_client.admin.command("ping")
        
        # Get database
        _mongodb_database = _mongodb_client[settings.mongodb_db_name]
        
        # Create indexes
        await _create_indexes(_mongodb_database)
        
        logger.info(f"✅ Connected to MongoDB database: {settings.mongodb_db_name}")
        return _mongodb_database
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise


async def _create_indexes(database: AsyncIOMotorDatabase):
    """
    Create database indexes for optimal query performance.
    
    Args:
        database: MongoDB database instance
    """
    try:
        # Jobs collection indexes
        jobs_collection = database["jobs"]
        
        # Index for user queries
        await jobs_collection.create_index([("user_id", 1), ("created_at", -1)])
        
        # Index for status queries
        await jobs_collection.create_index([("status", 1), ("created_at", -1)])
        
        # Index for job lookup
        await jobs_collection.create_index([("_id", 1)])
        
        # Compound index for filtering
        await jobs_collection.create_index([
            ("user_id", 1),
            ("status", 1),
            ("created_at", -1)
        ])
        
        # Processing logs collection indexes
        logs_collection = database["processing_logs"]
        await logs_collection.create_index([("job_id", 1), ("timestamp", -1)])
        await logs_collection.create_index([("level", 1), ("timestamp", -1)])
        
        # Transcripts collection indexes
        transcripts_collection = database["transcripts"]
        await transcripts_collection.create_index([("job_id", 1)])
        
        # Translations collection indexes
        translations_collection = database["translations"]
        await translations_collection.create_index([("job_id", 1)])
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to create some indexes: {e}")


async def close_database_connection():
    """Close MongoDB connection and cleanup resources."""
    global _mongodb_client, _mongodb_database
    
    if _mongodb_client:
        logger.info("Closing MongoDB connection...")
        _mongodb_client.close()
        _mongodb_client = None
        _mongodb_database = None
        logger.info("✅ MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the MongoDB database instance.
    
    Returns:
        AsyncIOMotorDatabase: Database instance
        
    Raises:
        RuntimeError: If database is not initialized
    """
    if _mongodb_database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return _mongodb_database


# Collection accessors
def get_jobs_collection():
    """Get jobs collection"""
    return get_database()["jobs"]


def get_logs_collection():
    """Get processing logs collection"""
    return get_database()["processing_logs"]


def get_transcripts_collection():
    """Get transcripts collection"""
    return get_database()["transcripts"]


def get_translations_collection():
    """Get translations collection"""
    return get_database()["translations"]
