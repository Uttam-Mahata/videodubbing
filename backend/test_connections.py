#!/usr/bin/env python3
"""
Database Connection Test Script
Tests MongoDB and Redis connections
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.mongodb import connect_to_mongodb, close_database_connection
from backend.db.redis_client import connect_to_redis, close_redis_connection, RedisCache
from backend.config.settings import settings


async def test_mongodb():
    """Test MongoDB connection"""
    print("\n=== Testing MongoDB Connection ===")
    try:
        db = await connect_to_mongodb()
        print(f"✅ Connected to MongoDB: {settings.mongodb_db_name}")
        
        # Test collection access
        from backend.db.mongodb import get_jobs_collection
        jobs = get_jobs_collection()
        count = await jobs.count_documents({})
        print(f"✅ Jobs collection accessible (count: {count})")
        
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False


async def test_redis():
    """Test Redis connection"""
    print("\n=== Testing Redis Connection ===")
    try:
        redis = await connect_to_redis()
        print(f"✅ Connected to Redis")
        
        # Test basic operations
        test_key = "test:connection"
        test_value = {"test": "value", "timestamp": "now"}
        
        await RedisCache.set(test_key, test_value, ttl=10)
        print(f"✅ Set test value in cache")
        
        retrieved = await RedisCache.get(test_key)
        if retrieved == test_value:
            print(f"✅ Retrieved value matches")
        else:
            print(f"⚠️ Retrieved value mismatch: {retrieved}")
        
        await RedisCache.delete(test_key)
        print(f"✅ Deleted test value")
        
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    print(f"\nEnvironment: {settings.environment}")
    print(f"MongoDB URL: {settings.mongodb_url}")
    print(f"Redis URL: {settings.redis_url}")
    
    mongodb_ok = await test_mongodb()
    redis_ok = await test_redis()
    
    # Cleanup
    print("\n=== Cleanup ===")
    await close_database_connection()
    await close_redis_connection()
    print("✅ Connections closed")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"MongoDB: {'✅ PASS' if mongodb_ok else '❌ FAIL'}")
    print(f"Redis: {'✅ PASS' if redis_ok else '❌ FAIL'}")
    
    if mongodb_ok and redis_ok:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check connections and configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
