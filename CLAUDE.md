# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-language video dubbing application using **Google ADK** (Agent Development Kit) for intelligent agent orchestration, **Gemini API** for audio understanding/translation/speech generation, **FastAPI** for async backend processing, and **React** for the frontend.

**Current Status**: Early-stage project with comprehensive architecture documentation but minimal implementation. Backend folder exists but is empty. Frontend is a Vite+React boilerplate. Main entry point (main.py) is a placeholder.

## Commands

### Backend (Future Implementation)
- **Run development server**: `uvicorn main:app --reload`
- **Run tests**: `pytest` (when tests exist)
- **Install dependencies**: `uv sync` or `pip install -e .`

### Frontend
- **Development server**: `cd frontend && npm run dev`
- **Build**: `cd frontend && npm run build`
- **Lint**: `cd frontend && npm run lint`
- **Preview production build**: `cd frontend && npm run preview`

## Architecture Overview

### Multi-Agent System (Google ADK)

The core architecture uses Google ADK's agent patterns for video dubbing pipeline orchestration:

**Workflow Agents**:
- **Coordinator Agent (LLM)**: Makes intelligent decisions about processing strategy, resource allocation, and error recovery
- **Sequential Agent**: Manages the deterministic pipeline flow (upload → extract → transcribe → translate → synthesize → merge → QA)
- **Parallel Agent**: Handles concurrent processing of video segments for 5x speedup on long videos
- **Loop Agent**: Iterative quality validation with retry logic (max 3 iterations)

**Specialized Custom Agents**:
- `VideoAnalysisAgent`: Scene detection, speaker identification
- `TranscriptionAgent`: Gemini audio understanding with timestamps
- `TranslationAgent`: Context-aware translation preserving tone and emotion
- `SpeechSynthesisAgent`: Multi-speaker voice synthesis with emotion matching
- `TimingSyncAgent`: Lip-sync optimization and pace adjustment
- `QualityAssuranceAgent`: Validation and quality scoring

Reference: https://google.github.io/adk-docs/agents/

### Processing Pipeline (9 Stages)

1. **Intake**: Video validation, GCS upload, job creation, coordinator analysis
2. **Audio Extraction**: FFmpeg-based extraction (WAV, 16kHz), scene segmentation
3. **Transcription**: Gemini Audio API with speaker diarization (~1920 tokens/min of audio)
4. **Translation**: Gemini LLM with context preservation, emotion tagging
5. **Speech Synthesis**: Gemini TTS API with 30 voice options (Kore, Puck, Zephyr, etc.)
6. **Timing Sync**: Time-stretching algorithms, pitch preservation, lip-sync scoring
7. **Audio Merging**: FFmpeg concatenation with background music preservation
8. **Quality Assurance**: Automated validation triggering Loop Agent retries on failure
9. **Delivery**: GCS upload, signed URLs (24-hour validity), WebSocket notifications

### Technology Stack

**Backend** (to be implemented in `backend/`):
- FastAPI for async REST/WebSocket APIs
- Celery for distributed task queue (separate worker pools: video, AI, merge)
- Redis for job queue and caching (translation cache, TTS cache, session state)
- MongoDB for job metadata, user accounts, processing logs
- Google Cloud Storage for video files with lifecycle policies

**Frontend** (`frontend/`):
- React 19.1.1 with TypeScript
- Vite (using rolldown-vite fork) for bundling
- Components to implement: JobList, VideoUpload, LanguageSelector, VoiceConfigurator, ProgressTracker (WebSocket), VideoPreview

**Dependencies** (pyproject.toml):
- `google-adk>=1.17.0` - Agent orchestration
- `google-genai>=1.45.0` - Gemini API client
- `fastapi>=0.119.0` - Backend framework

## Gemini API Integration Patterns

### Transcription (Audio Understanding API)
- Upload audio to Gemini Files API, then request transcription
- Prompt: "Generate detailed transcript with speaker identification and precise timestamps in MM:SS format"
- Use structured output with JSON schema: `{segments: [{speaker, start_time, end_time, text, confidence}]}`
- Token usage: ~1920 tokens per minute of audio

### Translation (LLM API)
- System instruction: "Translate maintaining tone, emotion, and cultural context. Preserve timing constraints for dubbing."
- Batch segments, use structured output schema with metadata: `duration_ms`, `emotion_tag`, `formality_level`
- Cache translations (key: text_hash + lang_pair, TTL: 7 days)

### Speech Synthesis (TTS API)
- Controllable TTS: "Say in [emotion] tone with [pace]: [translated_text]"
- Auto-map speakers to voices (30 options available)
- Generate 24kHz PCM, validate duration vs original
- Cache TTS audio (key: text_hash + voice + style, TTL: 30 days)

### API Optimization
- **Batch processing**: Combine segments to reduce overhead (60% API call reduction target)
- **Circuit breaker**: Fail after 5 consecutive errors, 60s timeout, half-open with 3 test requests
- **Retry logic**: Exponential backoff with jitter (3 attempts)
- **Model selection**: Use Gemini 2.5 Flash for simple tasks (70%), Pro for complex (30%)

## Fault Tolerance

### Job State Machine & Checkpointing
States: `QUEUED → AUDIO_EXTRACTED → TRANSCRIBED → TRANSLATED → SYNTHESIZED → SYNCHRONIZED → MERGED → VALIDATED → COMPLETED`
- Resume from last successful checkpoint on failure
- Persistence: Redis + MongoDB dual write
- Checkpoint after each major stage

### Failure Recovery Matrix
| Failure | Detection | Recovery | Fallback |
|---------|-----------|----------|----------|
| API Rate Limit | HTTP 429 | Exponential backoff + queue | Cached translations |
| Gemini Timeout | Request timeout | Circuit breaker | Retry with smaller segments |
| Worker Crash | Celery heartbeat loss | Auto-restart + reassignment | Alert + manual intervention |
| Invalid Audio | Quality check failure | Loop Agent retry | Notify user for re-upload |

## Performance & Scalability

### Parallel Processing Strategy
- Segment videos at scene boundaries (5-15 min segments, 5s overlap)
- Process segments concurrently (4-5x speedup target)
- Coordinate via ADK Sequential Agent

### Multi-Layer Caching
- **L1 (In-memory)**: Voice configs, API schemas (1 hour TTL, 100MB max)
- **L2 (Redis)**: Translations (7 days), TTS audio (30 days), job status (24 hours)
- **L3 (GCS)**: Completed videos (30 days)

### Horizontal Scaling (Future Kubernetes)
- FastAPI: 3-10 replicas (HPA on CPU >70%)
- Celery workers: Separate pools (video: 5-20, AI: 10-50, merge: 2-4) with auto-scaling on queue depth
- Redis cluster (3 replicas, StatefulSet)
- MongoDB: Replica set with sharding for horizontal scaling

## API Design

### REST Endpoints (Future Implementation)
- `POST /api/v1/jobs/create` - Create dubbing job (multipart/form-data)
- `GET /api/v1/jobs/{job_id}` - Get job status and progress
- `GET /api/v1/jobs/{job_id}/download` - Get signed download URL
- `DELETE /api/v1/jobs/{job_id}` - Cancel or delete job
- `GET /api/v1/voices` - List available voices with samples
- `GET /api/v1/languages` - List supported languages (24 languages)
- `POST /api/v1/jobs/{job_id}/retry` - Retry failed job

### WebSocket
- `WS /ws/jobs/{job_id}` - Real-time job progress updates
- Message types: `status`, `error`, `complete`, `log`
- Automatic reconnection with exponential backoff

### Rate Limiting
- Job creation: 10/hour per user
- Job status: 60/minute
- Job download: 100/hour

## Code Conventions

### Python
- Use async/await for FastAPI endpoints and Gemini API calls
- Type hints required (Python 3.12+)
- Pydantic models for request/response validation
- Structured logging with correlation IDs

### TypeScript/React
- Functional components with hooks
- Strict mode enabled
- ESLint with react-hooks and react-refresh plugins

## Implementation Guidance

**Start by implementing** (in order):
1. Basic FastAPI app skeleton in `backend/` with health check endpoint
2. Google ADK agent setup: Coordinator + Sequential agent for simple pipeline
3. Single-segment transcription using Gemini Audio API with structured output
4. Translation using Gemini LLM with caching
5. Basic TTS generation without multi-speaker or emotion control
6. Simple audio merge with FFmpeg subprocess
7. Frontend video upload component with drag-and-drop

**Avoid premature optimization**:
- Don't implement Celery/Redis queue until backend logic works synchronously
- Don't add parallel processing until single-segment pipeline is reliable
- Don't implement circuit breaker until hitting actual rate limits
- Focus on vertical slice (end-to-end for 1-minute video) before horizontal features

## Key Design Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Google ADK** | Intelligent agent coordination, built-in patterns | Learning curve, Google ecosystem dependency |
| **Gemini native APIs** | Unified API, controllable TTS, better integration | Limited to Gemini models |
| **Celery** | Mature task queue, good monitoring | Requires Redis/RabbitMQ |
| **MongoDB** | Flexible schema, native JSON support, horizontal scaling | Eventual consistency, requires careful schema design |
| **Parallel segmentation** | 5x speedup for long videos | Coordination complexity |

## Reference Links
- Google ADK: https://google.github.io/adk-docs/agents/
- Gemini Audio API: https://ai.google.dev/gemini-api/docs/audio
- Gemini Speech Generation: https://ai.google.dev/gemini-api/docs/speech-generation
- Gemini Structured Output: https://ai.google.dev/gemini-api/docs/structured-output
- Gemini Files API: https://ai.google.dev/gemini-api/docs/files
