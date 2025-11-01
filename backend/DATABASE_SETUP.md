# Database Setup Guide

## Overview

The video dubbing backend uses two primary databases:

1. **MongoDB** - Document database for job data, transcripts, translations, and processing logs
2. **Redis** - In-memory cache for session state, job status, and API response caching

## Quick Start

### 1. Install Dependencies

```bash
pip install motor pymongo redis google-cloud-storage
```

### 2. Start Database Services

#### Using Docker (Recommended for Development)

```bash
# Start MongoDB
docker run -d \
  --name videodubbing-mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7

# Start Redis
docker run -d \
  --name videodubbing-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine
```

#### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7
    container_name: videodubbing-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: videodubbing

  redis:
    image: redis:7-alpine
    container_name: videodubbing-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  mongodb_data:
  redis_data:
```

Start services:

```bash
docker-compose up -d
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
# For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 4. Test Connections

```bash
python backend/test_connections.py
```

Expected output:
```
=== Testing MongoDB Connection ===
✅ Connected to MongoDB: videodubbing
✅ Jobs collection accessible (count: 0)

=== Testing Redis Connection ===
✅ Connected to Redis
✅ Set test value in cache
✅ Retrieved value matches
✅ Deleted test value

🎉 All tests passed!
```

## Database Architecture

### MongoDB Collections

#### 1. **jobs** - Job Management
```javascript
{
  _id: ObjectId,
  user_id: String,
  status: Enum[QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED],
  current_stage: Enum[intake, transcription, translation, ...],
  progress_percent: Number,
  
  source_language: String,  // BCP-47 code
  target_language: String,
  
  voice_config: {
    primary_voice: String,
    secondary_voice: String,
    style_preferences: Object
  },
  
  input_video_url: String,   // gs://bucket/path
  output_video_url: String,
  
  metadata: {
    duration_seconds: Number,
    file_size_mb: Number,
    resolution: String,
    fps: Number,
    detected_speakers: Number
  },
  
  checkpoints: [{
    stage: String,
    status: String,
    timestamp: Date,
    data: Object
  }],
  
  error_message: String,
  created_at: Date,
  updated_at: Date,
  completed_at: Date
}
```

**Indexes:**
- `{ user_id: 1, created_at: -1 }`
- `{ status: 1, created_at: -1 }`
- `{ user_id: 1, status: 1, created_at: -1 }`

#### 2. **processing_logs** - Processing Logs
```javascript
{
  _id: ObjectId,
  job_id: String,
  level: Enum[INFO, WARNING, ERROR],
  message: String,
  stage: String,
  metadata: Object,
  timestamp: Date
}
```

**Indexes:**
- `{ job_id: 1, timestamp: -1 }`
- `{ level: 1, timestamp: -1 }`

#### 3. **transcripts** - Transcription Results
```javascript
{
  _id: ObjectId,
  job_id: String,
  transcript: {
    segments: [{
      speaker: String,
      start_time: Number,
      end_time: Number,
      text: String,
      confidence: Number
    }]
  },
  created_at: Date
}
```

**Indexes:**
- `{ job_id: 1 }`

#### 4. **translations** - Translation Results
```javascript
{
  _id: ObjectId,
  job_id: String,
  translation: {
    segments: [{
      original_text: String,
      translated_text: String,
      start_time: Number,
      end_time: Number,
      emotion_tag: String,
      formality_level: String
    }]
  },
  created_at: Date
}
```

**Indexes:**
- `{ job_id: 1 }`

### Redis Key Patterns

#### 1. Job Status Cache
```
Key: job:status:{job_id}
TTL: 24 hours
Value: {
  job_id: String,
  status: String,
  progress_percent: Number,
  current_stage: String
}
```

#### 2. Translation Cache
```
Key: translation:{source_lang}:{target_lang}:{text_hash}
TTL: 7 days
Value: String (translated text)
```

#### 3. TTS Audio Metadata Cache
```
Key: tts:{voice}:{style}:{text_hash}
TTL: 30 days
Value: {
  audio_url: String,
  duration_ms: Number,
  sample_rate: Number
}
```

#### 4. Rate Limiting
```
Key: ratelimit:{user_id}:{endpoint}:{minute}
TTL: 60 seconds
Value: Number (request count)
```

## Repository Pattern

The codebase uses the Repository pattern for database operations:

### Example: JobRepository

```python
from backend.db import JobRepository, JobStatusCache

# Create a job
job_id = await JobRepository.create(job)

# Get a job
job = await JobRepository.get_by_id(job_id)

# Update status
await JobRepository.update_status(job_id, JobStatus.PROCESSING)

# Update progress
await JobRepository.update_progress(job_id, progress_percent=45)

# Cache job status
await JobStatusCache.set_status(job_id, {
    "job_id": job_id,
    "status": "PROCESSING",
    "progress_percent": 45
})
```

## Production Deployment

### MongoDB Atlas (Recommended)

1. Create cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Whitelist IP addresses
3. Create database user
4. Get connection string:
   ```
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/videodubbing?retryWrites=true&w=majority
   ```

### Redis Cloud

1. Create instance at [Redis Cloud](https://redis.com/try-free/)
2. Get connection string:
   ```
   REDIS_URL=redis://default:password@endpoint:port
   ```

### Google Cloud Platform

#### MongoDB on GKE
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
spec:
  serviceName: mongodb
  replicas: 3
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: data
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

#### Redis on GKE
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: redis-pvc
```

## Monitoring

### MongoDB Monitoring

```python
# Get database stats
from backend.db import get_database

db = get_database()
stats = await db.command("dbStats")
print(f"Database size: {stats['dataSize']} bytes")
print(f"Collections: {stats['collections']}")
```

### Redis Monitoring

```python
from backend.db import get_redis

redis = get_redis()
info = await redis.info()
print(f"Connected clients: {info['connected_clients']}")
print(f"Used memory: {info['used_memory_human']}")
print(f"Total keys: {await redis.dbsize()}")
```

## Backup & Recovery

### MongoDB Backup

```bash
# Backup
mongodump --uri="mongodb://localhost:27017/videodubbing" --out=/backup

# Restore
mongorestore --uri="mongodb://localhost:27017/videodubbing" /backup/videodubbing
```

### Redis Backup

```bash
# Trigger save
redis-cli BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backup/
```

## Troubleshooting

### MongoDB Connection Issues

```bash
# Test connection
mongosh "mongodb://localhost:27017/videodubbing"

# Check logs
docker logs videodubbing-mongodb
```

### Redis Connection Issues

```bash
# Test connection
redis-cli -h localhost -p 6379 PING

# Check logs
docker logs videodubbing-redis

# Monitor commands
redis-cli MONITOR
```

### Common Issues

1. **Connection Timeout**: Check firewall rules and network connectivity
2. **Authentication Failed**: Verify credentials in `.env`
3. **Database Not Found**: Ensure database name matches configuration
4. **Out of Memory (Redis)**: Increase maxmemory or enable eviction policy

## Performance Tuning

### MongoDB

```javascript
// Create compound indexes for common queries
db.jobs.createIndex({ user_id: 1, status: 1, created_at: -1 })

// Enable profiling
db.setProfilingLevel(1, { slowms: 100 })

// Analyze slow queries
db.system.profile.find().sort({ ts: -1 }).limit(5)
```

### Redis

```bash
# Configure maxmemory policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Monitor slow queries
redis-cli CONFIG SET slowlog-log-slower-than 10000
redis-cli SLOWLOG GET 10
```

## Security Best Practices

1. **Use strong passwords** for database connections
2. **Enable authentication** on both MongoDB and Redis
3. **Use TLS/SSL** for connections in production
4. **Whitelist IP addresses** for network access
5. **Regular backups** with encrypted storage
6. **Rotate credentials** periodically
7. **Monitor access logs** for suspicious activity

## References

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Redis Documentation](https://redis.io/documentation)
- [Motor (Async MongoDB)](https://motor.readthedocs.io/)
- [Redis-py](https://redis-py.readthedocs.io/)
