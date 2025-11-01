# Video Dubbing Application - AI Coding Instructions

## Project Overview
Multi-language video dubbing application using **Google ADK** (Agent Development Kit) for intelligent agent orchestration, **Gemini API** for audio understanding/translation/speech generation, **FastAPI** for async backend processing, and **React + Vite** for the frontend.

**Status**: Early-stage project with comprehensive architecture documentation but minimal implementation. Backend folder exists but is empty. Frontend is a Vite+React boilerplate.

## Architecture & Design Principles

### Multi-Agent System (Google ADK)
The core architecture uses Google ADK's agent patterns for video dubbing pipeline orchestration:

- **Coordinator Agent (LLM)**: Makes intelligent decisions about processing strategy, resource allocation, and error recovery
- **Sequential Agent**: Manages the deterministic pipeline flow (upload → extract → transcribe → translate → synthesize → merge → QA)
- **Parallel Agent**: Handles concurrent processing of video segments for 5x speedup on long videos
- **Loop Agent**: Iterative quality validation with retry logic (max 3 iterations)
- **Specialized Custom Agents**: 
  - `VideoAnalysisAgent`: Scene detection, speaker identification
  - `TranscriptionAgent`: Gemini audio understanding with timestamps
  - `TranslationAgent`: Context-aware translation preserving tone
  - `SpeechSynthesisAgent`: Multi-speaker voice synthesis with emotion matching
  - `TimingSyncAgent`: Lip-sync optimization and pace adjustment
  - `QualityAssuranceAgent`: Validation and quality scoring

**Key Pattern**: Use ADK's workflow agents (Sequential, Parallel, Loop) for orchestration, not just custom agents. Reference: https://google.github.io/adk-docs/agents/

### Pipeline Processing Stages
1. **Intake**: Video validation, GCS upload, job creation, coordinator analysis
2. **Audio Extraction**: FFmpeg-based extraction (WAV, 16kHz), scene segmentation
3. **Transcription**: Gemini Audio API with speaker diarization (JSON schema: `{segments: [{speaker, start_time, end_time, text, confidence}]}`)
4. **Translation**: Gemini LLM with context preservation (schema includes `emotion_tag`, `formality_level`)
5. **Speech Synthesis**: Gemini TTS API (30 voice options: Kore, Puck, Zephyr, etc.), controllable with emotion/pace prompts
6. **Timing Sync**: Time-stretching algorithms, pitch preservation, lip-sync scoring
7. **Audio Merging**: FFmpeg concatenation with background music preservation
8. **Quality Assurance**: Automated validation with pass/fail decision triggering Loop Agent retries
9. **Delivery**: GCS upload, signed URLs (24-hour validity), WebSocket notifications

### Technology Stack

**Backend** (not yet implemented):
- FastAPI for async REST/WebSocket APIs
- Celery for distributed task queue (separate worker pools: video, AI, merge)
- Redis for job queue, caching (translation cache, TTS cache, session state)
- MongoDB for job metadata, user accounts, processing logs
- Google Cloud Storage for video files with lifecycle policies (input: 7 days, output: 30 days)

**Frontend**:
- React 19.1.1 with TypeScript
- Vite (using rolldown-vite fork) for bundling
- Standard structure: `src/App.tsx`, `src/main.tsx`
- Future components per README: JobList, VideoUpload, LanguageSelector, VoiceConfigurator, ProgressTracker (WebSocket), VideoPreview

**Dependencies**:
- `google-adk>=1.17.0` - Agent orchestration
- `google-genai>=1.45.0` - Gemini API client
- `fastapi>=0.119.0` - Backend framework

## Development Workflows

### Running the Application
- **Backend**: Not yet implemented. Future: `uvicorn main:app --reload`
- **Frontend**: `cd frontend && npm run dev` (Vite dev server)
- **Build**: `cd frontend && npm run build` (TypeScript check + Vite build)

### Project Structure
```
/
├── main.py                 # Placeholder entry point (prints "Hello from videodubbing!")
├── pyproject.toml          # Python dependencies
├── backend/                # Empty - future FastAPI app, agents, workers
├── frontend/               # React + Vite SPA
│   ├── src/
│   │   ├── App.tsx        # Main component (boilerplate)
│   │   └── main.tsx       # React root
│   ├── package.json
│   └── vite.config.ts
└── README.md              # Comprehensive system design document (1000+ lines)
```

### Testing Strategy (Future)
Per README design:
- **Unit tests** (60%): pytest for Python, Jest for React, 80% coverage target
- **Integration tests** (30%): API endpoints, agent interactions, on every PR
- **E2E tests** (10%): Playwright/Cypress for critical journeys, pre-deployment
- **Performance tests**: Locust for load testing (target: 100 concurrent jobs), weekly

## Gemini API Integration Patterns

### Transcription (Audio Understanding API)
```python
# Upload audio to Gemini Files API, then request transcription
# Prompt: "Generate detailed transcript with speaker identification and precise timestamps in MM:SS format"
# Use structured output with JSON schema for parsing
# Token usage: ~1920 tokens per minute of audio
```

### Translation (LLM API)
```python
# System instruction: "Translate maintaining tone, emotion, and cultural context. Preserve timing constraints for dubbing."
# Batch segments, use structured output schema
# Include metadata: duration_ms, emotion_tag, formality_level
# Cache translations (key: text_hash + lang_pair, TTL: 7 days)
```

### Speech Synthesis (TTS API)
```python
# Controllable TTS: "Say in [emotion] tone with [pace]: [translated_text]"
# Auto-map speakers to voices (30 options)
# Generate 24kHz PCM, validate duration vs original
# Cache TTS audio (key: text_hash + voice + style, TTL: 30 days)
```

### API Optimization
- **Batch processing**: Combine segments to reduce overhead (60% API call reduction)
- **Circuit breaker**: Fail after 5 consecutive errors, 60s timeout, half-open with 3 test requests
- **Retry logic**: Exponential backoff with jitter (3 attempts)
- **Token management**: Pre-calculate usage, split strategically
- **Model selection**: Use Gemini 2.5 Flash for simple tasks (70%), Pro for complex (30%)

## Fault Tolerance & Error Handling

### Failure Matrix
| Failure | Detection | Recovery | Fallback |
|---------|-----------|----------|----------|
| API Rate Limit | HTTP 429 | Exponential backoff + queue | Cached translations |
| Gemini Timeout | Request timeout | Circuit breaker | Retry with smaller segments |
| Worker Crash | Celery heartbeat loss | Auto-restart + reassignment | Alert + manual intervention |
| Invalid Audio | Quality check failure | Loop Agent retry | Notify user for re-upload |

### Checkpointing
Job state machine: `QUEUED → AUDIO_EXTRACTED → TRANSCRIBED → TRANSLATED → SYNTHESIZED → SYNCHRONIZED → MERGED → VALIDATED → COMPLETED`
- Resume from last successful checkpoint
- Persistence: Redis + MongoDB dual write
- Checkpoint after each major stage

## Scalability & Performance

### Horizontal Scaling (Future Kubernetes)
- FastAPI: 3-10 replicas (HPA on CPU >70%)
- Celery workers: Separate pools (video: 5-20, AI: 10-50, merge: 2-4) with auto-scaling on queue depth
- Redis cluster (3 replicas, StatefulSet)
- MongoDB: Replica set with sharding for horizontal scaling

### Parallel Processing
- Segment videos at scene boundaries (5-15 min segments, 5s overlap)
- Process segments concurrently (4-5x speedup)
- Coordinate via ADK Sequential Agent

### Caching Strategy
- **L1 (In-memory)**: Voice configs, API schemas (1 hour, 100MB)
- **L2 (Redis)**: Translations (7 days), TTS audio (30 days), job status (24 hours)
- **L3 (GCS)**: Completed videos (30 days)

## Code Conventions (Inferred from Stack)

### Python
- Use async/await for FastAPI endpoints and Gemini API calls
- Type hints required (Python 3.12+)
- Pydantic models for request/response validation
- Structured logging with correlation IDs

### TypeScript/React
- Functional components with hooks (`useState`, `useEffect`)
- Strict mode enabled (`tsconfig.json`)
- ESLint with `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`

### API Design
- REST endpoints: `/api/v1/jobs/{action}`
- WebSocket: `/ws/jobs/{job_id}` for real-time progress
- Signed URLs for file downloads (24-hour validity)
- Rate limiting: 60 req/min per user

## Key Decisions & Trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Google ADK** | Intelligent agent coordination, built-in patterns | Learning curve, Google ecosystem dependency |
| **Gemini native APIs** | Unified API, controllable TTS, better integration | Limited to Gemini models |
| **Celery** | Mature task queue, good monitoring | Requires Redis/RabbitMQ |
| **MongoDB** | Flexible schema, native JSON support, horizontal scaling | Eventual consistency, requires careful schema design |
| **Parallel segmentation** | 5x speedup for long videos | Coordination complexity |

## Reference Links
- Google ADK Docs: https://google.github.io/adk-docs/agents/
- Gemini Audio API: https://ai.google.dev/gemini-api/docs/audio
- Gemini Speech Generation: https://ai.google.dev/gemini-api/docs/speech-generation
- Gemini Structured Output: https://ai.google.dev/gemini-api/docs/structured-output

## Implementation Guidance

**Start by implementing**:
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
