# Backend README

## Video Dubbing Application - Backend

Production-level FastAPI backend using **Google ADK** (Agent Development Kit) and **Gemini APIs** for intelligent video dubbing pipeline orchestration.

## Architecture Overview

### Multi-Agent System (Google ADK)
- **Coordinator Agent**: Intelligent decision-making for pipeline strategy
- **Sequential Agent**: Manages deterministic pipeline flow
- **Parallel Agent**: Concurrent processing of video segments
- **Loop Agent**: Iterative quality validation with retry logic
- **Custom Agents**: Transcription, Translation, Speech Synthesis, Timing Sync, QA

### Technology Stack
- **FastAPI**: High-performance async REST API
- **Google ADK**: Agent orchestration framework
- **Gemini API**: Audio understanding, translation, and TTS
- **MongoDB**: Job metadata and state storage
- **Redis**: Caching and session management
- **Celery**: Distributed task queue (future)

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config/
│   └── settings.py        # Centralized configuration
├── models/                # Pydantic data models
│   ├── job.py            # Job status and metadata
│   ├── transcript.py     # Transcription results
│   ├── translation.py    # Translation segments
│   └── voice.py          # Voice configurations
├── services/             # Business logic services
│   ├── gemini_audio.py   # Audio understanding service
│   ├── gemini_tts.py     # Text-to-speech service
│   ├── gemini_llm.py     # LLM translation service
│   ├── circuit_breaker.py # Fault tolerance
│   └── storage.py        # GCS operations
├── agents/               # Google ADK agents
│   ├── base.py           # Base agent class
│   ├── coordinator.py    # Pipeline coordinator
│   ├── transcription.py  # Transcription agent
│   ├── translation.py    # Translation agent
│   └── speech_synthesis.py # TTS agent
├── api/
│   └── routes/          # API endpoints
│       ├── health.py    # Health checks
│       ├── jobs.py      # Job management
│       └── voices.py    # Voice configuration
└── utils/
    └── logging_config.py # Structured logging

```

## Features Implemented

### ✅ Configuration Management
- Environment-based settings with Pydantic
- Validation and type safety
- Support for multiple environments

### ✅ Data Models
- Job lifecycle management (10 states)
- Transcript with speaker diarization
- Translation with emotion/formality tags
- Voice configuration (30 voice options)

### ✅ Gemini API Integration
- **Audio Understanding**: Transcription with structured output
- **Text-to-Speech**: Single and multi-speaker synthesis
- **LLM Translation**: Context-aware translation
- Circuit breaker pattern for fault tolerance
- Exponential backoff retry logic

### ✅ Agent System (Google ADK)
- Base agent architecture
- Coordinator for intelligent orchestration
- Specialized agents for each pipeline stage
- Event-driven communication

### ✅ FastAPI Application
- REST API endpoints
- CORS middleware
- Request timing tracking
- Global exception handling
- Health and readiness checks

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

Required environment variables:
- `GEMINI_API_KEY`: Your Gemini API key
- `MONGODB_URL`: MongoDB connection string
- `REDIS_URL`: Redis connection string

### 3. Run the Application

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn backend.main:app --reload --port 8000
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API Endpoints

### Health Checks
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/ready` - Readiness probe

### Job Management
- `POST /api/v1/jobs/create` - Create dubbing job
- `GET /api/v1/jobs/{job_id}` - Get job status
- `GET /api/v1/jobs` - List jobs (paginated)
- `GET /api/v1/jobs/{job_id}/download` - Get download URL
- `DELETE /api/v1/jobs/{job_id}` - Cancel job
- `POST /api/v1/jobs/{job_id}/retry` - Retry failed job

### Voice Configuration
- `GET /api/v1/voices` - List available voices
- `GET /api/v1/languages` - List supported languages

## Pipeline Architecture

### 9-Stage Dubbing Pipeline

1. **INTAKE**: Video validation, GCS upload, job creation
2. **AUDIO_EXTRACTION**: FFmpeg extraction, scene detection
3. **TRANSCRIPTION**: Gemini Audio API with timestamps
4. **TRANSLATION**: Context-aware translation with Gemini LLM
5. **SPEECH_SYNTHESIS**: Multi-speaker TTS with Gemini
6. **TIMING_SYNC**: Time-stretching and lip-sync optimization
7. **AUDIO_MERGING**: FFmpeg concatenation
8. **QUALITY_ASSURANCE**: Automated validation
9. **DELIVERY**: GCS upload, signed URLs

### Circuit Breaker Protection

All Gemini API calls are protected by circuit breakers:
- **CLOSED**: Normal operation
- **OPEN**: Service unavailable (after 5 failures)
- **HALF_OPEN**: Testing recovery

Configuration:
- Failure threshold: 5 consecutive errors
- Timeout: 60 seconds
- Half-open test requests: 3

## Development Status

### Completed
- ✅ Configuration management
- ✅ Data models and schemas
- ✅ Gemini API service clients
- ✅ Circuit breaker implementation
- ✅ Agent base architecture
- ✅ FastAPI application structure
- ✅ Health check endpoints

### In Progress
- 🔄 Database layer (MongoDB)
- 🔄 Redis caching
- 🔄 WebSocket for real-time updates
- 🔄 Complete agent implementations

### Planned
- ⏳ Celery worker setup
- ⏳ Complete pipeline orchestration
- ⏳ Authentication & authorization
- ⏳ Rate limiting
- ⏳ Monitoring and metrics
- ⏳ End-to-end testing

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=backend --cov-report=html

# Specific test file
pytest tests/test_agents.py
```

## Next Steps

1. **Implement Database Layer**
   - MongoDB connection manager
   - Repository pattern for collections
   - Indexing strategy

2. **Complete Agent Pipeline**
   - Sequential agent orchestration
   - Parallel segment processing
   - Loop agent for quality validation

3. **Add WebSocket Support**
   - Real-time job progress updates
   - Connection management
   - Reconnection logic

4. **Implement Celery Workers**
   - Worker pools (video, AI, merge)
   - Task distribution
   - Auto-scaling logic

## Documentation References

- [Google ADK Documentation](https://google.github.io/adk-docs/agents/)
- [Gemini Audio API](https://ai.google.dev/gemini-api/docs/audio)
- [Gemini Speech Generation](https://ai.google.dev/gemini-api/docs/speech-generation)
- [Gemini Structured Output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini Files API](https://ai.google.dev/gemini-api/docs/files)

## License

Copyright © 2025 Video Dubbing Application
