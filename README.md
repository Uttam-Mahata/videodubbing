# **Video Dubbing Application - System Design Document**

## **1. Executive Summary**

### **1.1 System Overview**
A scalable, fault-tolerant video dubbing application leveraging:
- **Google ADK** for intelligent agent orchestration
- **Gemini API** for audio understanding, translation, and speech generation
- **FastAPI** backend for high-performance async processing
- **React** frontend for responsive user experience

### **1.2 Core Capabilities**
- Multi-language video dubbing with 24 language support
- Intelligent audio analysis and transcription with timestamps
- Context-aware translation preserving tone and emotion
- Multi-speaker voice synthesis with 30 voice options
- Automatic lip-sync timing optimization

---

## **2. Architecture Overview**

### **2.1 High-Level System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend (SPA)                                           │
│  ├─ Upload Manager         ├─ Real-time Dashboard               │
│  ├─ Language Selector      ├─ Preview Player                    │
│  └─ Voice Configuration    └─ Download Manager                  │
└─────────────────────────────────────────────────────────────────┘
                              ▼ ▲
                        WebSocket / REST API
                              ▼ ▲
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Gateway                                                 │
│  ├─ API Endpoints          ├─ WebSocket Server                  │
│  ├─ Authentication         ├─ Rate Limiting                      │
│  └─ Request Validation     └─ Error Handling                     │
└─────────────────────────────────────────────────────────────────┘
                              ▼ ▲
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER (ADK)                     │
├─────────────────────────────────────────────────────────────────┤
│  Multi-Agent System                                              │
│  ├─ Coordinator Agent (LLM)    - Decision making                │
│  ├─ Workflow Agents            - Pipeline orchestration         │
│  └─ Processing Agents          - Specialized tasks              │
└─────────────────────────────────────────────────────────────────┘
                              ▼ ▲
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  Distributed Task Queue (Celery/RQ)                             │
│  ├─ Video Processing Workers   ├─ AI Processing Workers         │
│  ├─ Audio Processing Workers   └─ Merge Workers                 │
│  └─ Priority Queue Management                                    │
└─────────────────────────────────────────────────────────────────┘
                              ▼ ▲
┌─────────────────────────────────────────────────────────────────┐
│                     INTEGRATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  Gemini API Services                                             │
│  ├─ Audio Understanding API    ├─ LLM API (Translation)         │
│  ├─ Speech Generation API      └─ Structured Output API         │
│  └─ Circuit Breaker & Retry Logic                               │
└─────────────────────────────────────────────────────────────────┘
                              ▼ ▲
┌─────────────────────────────────────────────────────────────────┐
│                      DATA & STORAGE LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  ├─ PostgreSQL (Metadata)     ├─ Redis (Cache & Queue)          │
│  ├─ Google Cloud Storage      ├─ MinIO (Local Development)      │
│  └─ Elasticsearch (Logging)   └─ Prometheus (Metrics)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## **3. Detailed Component Design**

### **3.1 Google ADK Agent Architecture**

#### **3.1.1 Multi-Agent System Design**

```
┌─────────────────────────────────────────────────────────────┐
│                   COORDINATOR AGENT (LLM)                    │
│  - Job intake and validation                                 │
│  - Language detection and verification                       │
│  - Resource allocation decisions                             │
│  - Error recovery strategies                                 │
└─────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ SEQUENTIAL  │  │  PARALLEL   │  │    LOOP     │
│   AGENT     │  │   AGENT     │  │   AGENT     │
│             │  │             │  │             │
│ Manages     │  │ Parallel    │  │ Retry &     │
│ pipeline    │  │ processing  │  │ quality     │
│ flow        │  │ of segments │  │ validation  │
└─────────────┘  └─────────────┘  └─────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
        ┌────────────────────────────────────┐
        │    SPECIALIZED CUSTOM AGENTS       │
        ├────────────────────────────────────┤
        │ 1. VideoAnalysisAgent              │
        │    - Scene detection               │
        │    - Speaker identification        │
        │    - Audio quality assessment      │
        │                                    │
        │ 2. TranscriptionAgent              │
        │    - Gemini audio understanding    │
        │    - Timestamp extraction          │
        │    - Speaker diarization           │
        │                                    │
        │ 3. TranslationAgent                │
        │    - Context-aware translation     │
        │    - Tone preservation             │
        │    - Cultural adaptation           │
        │                                    │
        │ 4. SpeechSynthesisAgent            │
        │    - Voice selection optimization  │
        │    - Multi-speaker coordination    │
        │    - Emotion & style matching      │
        │                                    │
        │ 5. TimingSyncAgent                 │
        │    - Lip-sync optimization         │
        │    - Pace adjustment               │
        │    - Scene boundary alignment      │
        │                                    │
        │ 6. QualityAssuranceAgent           │
        │    - Audio quality validation      │
        │    - Translation accuracy check    │
        │    - Sync verification             │
        └────────────────────────────────────┘
```

#### **3.1.2 Agent Responsibilities**

**Coordinator Agent (LLM Agent)**
- **Purpose**: Intelligent decision-making and orchestration
- **Capabilities**:
  - Analyzes video characteristics (length, speakers, complexity)
  - Determines optimal processing strategy
  - Allocates resources dynamically
  - Handles error recovery and fallback strategies
  - Makes human-like decisions on edge cases

**Sequential Agent (Workflow Agent)**
- **Purpose**: Manages deterministic pipeline flow
- **Flow Pattern**:
  1. Video Upload → 2. Audio Extraction → 3. Transcription → 
  4. Translation → 5. Speech Synthesis → 6. Audio Merge → 7. Quality Check

**Parallel Agent (Workflow Agent)**
- **Purpose**: Concurrent processing of video segments
- **Pattern**: 
  - Splits video into N segments
  - Processes each segment independently
  - Merges results maintaining temporal coherence

**Loop Agent (Workflow Agent)**
- **Purpose**: Iterative quality improvement
- **Pattern**:
  - Validates output quality
  - Retries failed segments
  - Iterates until quality threshold met (max 3 iterations)

---

### **3.2 Processing Pipeline Design**

#### **3.2.1 Dubbing Pipeline Architecture**

```
┌──────────────────────────────────────────────────────────────┐
│                    STAGE 1: INTAKE                            │
├──────────────────────────────────────────────────────────────┤
│  Input: Video file, Source lang, Target lang, Voice config   │
│  ├─ Video validation (format, size, duration)                │
│  ├─ Upload to Google Cloud Storage                           │
│  ├─ Job record creation in PostgreSQL                        │
│  ├─ Initial metadata extraction                              │
│  └─ Coordinator Agent analysis                               │
│  Output: Job ID, Processing strategy                         │
└──────────────────────────────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              STAGE 2: AUDIO EXTRACTION                        │
├──────────────────────────────────────────────────────────────┤
│  Tools: FFmpeg, VideoAnalysisAgent                           │
│  ├─ Extract audio track (WAV format, 16kHz)                  │
│  ├─ Scene detection and segmentation                         │
│  ├─ Speaker change detection                                 │
│  ├─ Background music/noise analysis                          │
│  └─ Generate segment metadata                                │
│  Output: Audio file(s), Segment boundaries, Metadata         │
└──────────────────────────────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│         STAGE 3: TRANSCRIPTION (Gemini Audio API)            │
├──────────────────────────────────────────────────────────────┤
│  Agent: TranscriptionAgent                                    │
│  Process:                                                     │
│  ├─ Upload audio to Gemini Files API                         │
│  ├─ Request transcription with timestamps                    │
│  │   Prompt: "Generate detailed transcript with speaker      │
│  │   identification and precise timestamps in MM:SS format"  │
│  ├─ Parse structured output (JSON schema)                    │
│  │   Schema: {segments: [{speaker, start_time, end_time,     │
│  │            text, confidence}]}                            │
│  ├─ Speaker diarization validation                           │
│  └─ Quality confidence scoring                               │
│  Output: Structured transcript with timestamps               │
│  Token Usage: ~1920 tokens per minute of audio               │
└──────────────────────────────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│         STAGE 4: TRANSLATION (Gemini LLM API)                │
├──────────────────────────────────────────────────────────────┤
│  Agent: TranslationAgent                                      │
│  Process:                                                     │
│  ├─ Context-aware translation request                        │
│  │   System Instructions:                                    │
│  │   "Translate maintaining tone, emotion, and cultural      │
│  │   context. Preserve timing constraints for dubbing."      │
│  ├─ Batch translation of segments                            │
│  ├─ Structured output with metadata                          │
│  │   Schema: {translations: [{original_text, translated_text,│
│  │            duration_ms, emotion_tag, formality_level}]}   │
│  ├─ Length optimization for lip-sync                         │
│  ├─ Cultural adaptation notes                                │
│  └─ Alternative translation generation (fallback)            │
│  Output: Translated text with metadata                       │
└──────────────────────────────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│      STAGE 5: SPEECH SYNTHESIS (Gemini TTS API)              │
├──────────────────────────────────────────────────────────────┤
│  Agent: SpeechSynthesisAgent                                  │
│  Process:                                                     │
│  ├─ Voice selection based on:                                │
│  │   - Original speaker characteristics                      │
│  │   - Target language appropriateness                       │
│  │   - Emotion/tone matching                                 │
│  ├─ Single-speaker OR Multi-speaker configuration            │
│  │   - Auto-detect speaker count from transcription          │
│  │   - Map speakers to appropriate voices                    │
│  ├─ Controllable TTS generation                              │
│  │   Prompt: "Say in [emotion] tone with [pace]:            │
│  │           [translated_text]"                              │
│  ├─ Generate audio segments (24kHz PCM)                      │
│  ├─ Duration validation against original                     │
│  └─ Prosody adjustment if needed                             │
│  Output: Audio segments (WAV format)                         │
│  Voices: 30 options (Kore, Puck, Zephyr, etc.)              │
└──────────────────────────────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│            STAGE 6: TIMING SYNCHRONIZATION                    │
├──────────────────────────────────────────────────────────────┤
│  Agent: TimingSyncAgent                                       │
│  Process:                                                     │
│  ├─ Compare original vs dubbed audio durations               │
│  ├─ Apply time-stretching algorithms                         │
│  │   - Preserve pitch                                        │
│  │   - Maintain natural speech patterns                      │
│  ├─ Scene boundary alignment                                 │
│  ├─ Silence insertion/removal optimization                   │
│  ├─ Lip-sync score calculation                               │
│  └─ Generate timing adjustment metadata                      │
│  Output: Time-aligned audio segments                         │
└──────────────────────────────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              STAGE 7: AUDIO MERGING                           │
├──────────────────────────────────────────────────────────────┤
│  Tools: FFmpeg, Audio mixing libraries                       │
│  Process:                                                     │
│  ├─ Concatenate time-aligned segments                        │
│  ├─ Background music/ambience preservation                   │
│  ├─ Volume normalization                                     │
│  ├─ Audio effects application                                │
│  ├─ Replace original audio track in video                    │
│  └─ Generate preview with side-by-side comparison            │
│  Output: Final dubbed video file                             │
└──────────────────────────────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│          STAGE 8: QUALITY ASSURANCE                           │
├──────────────────────────────────────────────────────────────┤
│  Agent: QualityAssuranceAgent                                 │
│  Validations:                                                 │
│  ├─ Audio-video sync verification                            │
│  ├─ Translation accuracy spot-check (Gemini validation)      │
│  ├─ Audio quality metrics (SNR, clarity)                     │
│  ├─ Duration match verification                              │
│  ├─ File integrity check                                     │
│  └─ Generate quality report (structured output)              │
│  Decision:                                                    │
│  ├─ PASS → Move to delivery                                  │
│  └─ FAIL → Loop Agent triggers retry                         │
└──────────────────────────────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                STAGE 9: DELIVERY                              │
├──────────────────────────────────────────────────────────────┤
│  ├─ Upload final video to Cloud Storage                      │
│  ├─ Generate signed download URL (time-limited)              │
│  ├─ Update job status to COMPLETED                           │
│  ├─ WebSocket notification to frontend                       │
│  ├─ Store processing analytics                               │
│  └─ Cleanup temporary files                                  │
└──────────────────────────────────────────────────────────────┘
```

---

### **3.3 Scalability Architecture**

#### **3.3.1 Horizontal Scaling Strategy**

```
┌────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCER (NGINX)                        │
│                  Round-robin / Least connections                │
└────────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  FastAPI    │  │  FastAPI    │  │  FastAPI    │
│  Instance 1 │  │  Instance 2 │  │  Instance N │
│  (Stateless)│  │  (Stateless)│  │  (Stateless)│
└─────────────┘  └─────────────┘  └─────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                   REDIS CLUSTER (HA)                            │
│  ├─ Job Queue (Bull/RQ)                                        │
│  ├─ Session Cache                                              │
│  ├─ Rate Limiting                                              │
│  ├─ Translation Cache                                          │
│  └─ Voice Selection Cache                                      │
└────────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│              CELERY WORKER POOLS (Auto-scaling)              │
├─────────────────────────────────────────────────────────────┤
│  Video Processing Pool    [●●●●○○] 4/6 active               │
│  AI Processing Pool        [●●●●●●●○○○] 7/10 active          │
│  Merge Processing Pool     [●●○○] 2/4 active                │
│                                                              │
│  Scaling Rules:                                              │
│  ├─ Queue depth > 50 → Add workers                          │
│  ├─ CPU utilization > 80% → Add workers                     │
│  ├─ Queue depth < 10 → Remove workers                       │
│  └─ Minimum 2 workers per pool                              │
└─────────────────────────────────────────────────────────────┘
```

#### **3.3.2 Database Scaling**

```
┌────────────────────────────────────────────────────────────┐
│              PostgreSQL PRIMARY (Write)                     │
│  ├─ Job metadata                                           │
│  ├─ User accounts                                          │
│  ├─ Processing logs                                        │
│  └─ Billing information                                    │
└────────────────────────────────────────────────────────────┘
                │         │
                ▼         ▼
┌──────────────────┐  ┌──────────────────┐
│  READ REPLICA 1  │  │  READ REPLICA 2  │
│  (Dashboard)     │  │  (Analytics)     │
└──────────────────┘  └──────────────────┘

Connection Pooling: PgBouncer (Transaction mode)
Max Connections: 100 per instance
```

#### **3.3.3 Storage Scaling**

```
┌────────────────────────────────────────────────────────────┐
│            GOOGLE CLOUD STORAGE (Multi-regional)            │
├────────────────────────────────────────────────────────────┤
│  Buckets:                                                   │
│  ├─ videos-input/          [Standard Storage]             │
│  │   └─ Lifecycle: Delete after 7 days                    │
│  ├─ videos-processing/     [Standard Storage]             │
│  │   └─ Lifecycle: Delete after 3 days                    │
│  ├─ videos-output/         [Standard Storage]             │
│  │   └─ Lifecycle: Delete after 30 days                   │
│  └─ videos-archive/        [Nearline/Coldline]            │
│      └─ Lifecycle: Move after 30 days                     │
│                                                            │
│  CDN Integration: Cloud CDN for output delivery           │
│  Signed URLs: Time-limited access (24 hours)              │
└────────────────────────────────────────────────────────────┘
```

---

### **3.4 Fault Tolerance Design**

#### **3.4.1 Failure Handling Matrix**

| **Failure Type** | **Detection** | **Recovery Strategy** | **Fallback** |
|------------------|---------------|----------------------|--------------|
| **API Rate Limit** | HTTP 429 response | Exponential backoff + queue | Use cached translations |
| **Gemini API Timeout** | Request timeout | Circuit breaker pattern | Retry with smaller segments |
| **Network Failure** | Connection error | Retry with jitter (3 attempts) | Queue for later |
| **Worker Crash** | Celery heartbeat loss | Auto-restart + job reassignment | Alert + manual intervention |
| **Database Failure** | Connection error | Automatic failover to replica | Read-only mode |
| **Storage Failure** | Upload/download error | Retry with alternate region | Local temporary storage |
| **Out of Memory** | Resource monitoring | Kill task + restart with smaller batch | Segment size reduction |
| **Invalid Audio** | Quality check failure | Loop Agent retry | Notify user for re-upload |

#### **3.4.2 Circuit Breaker Pattern**

```
┌────────────────────────────────────────────────────────┐
│              GEMINI API CIRCUIT BREAKER                 │
├────────────────────────────────────────────────────────┤
│  States:                                                │
│  ┌─────────┐  Error threshold   ┌─────────┐          │
│  │ CLOSED  │──────exceeded─────→ │  OPEN   │          │
│  │ (Normal)│                     │ (Block) │          │
│  └─────────┘                     └─────────┘          │
│       ▲                               │                │
│       │                               │                │
│       │                               ▼                │
│       │  Success threshold    ┌──────────────┐        │
│       └──────met─────────────│  HALF-OPEN   │        │
│                               │  (Test)      │        │
│                               └──────────────┘        │
│                                                        │
│  Configuration:                                        │
│  ├─ Failure threshold: 5 consecutive errors           │
│  ├─ Timeout: 60 seconds                               │
│  ├─ Half-open test requests: 3                        │
│  └─ Success threshold: 2/3 successful                 │
└────────────────────────────────────────────────────────┘
```

#### **3.4.3 Checkpointing System**

```
Job State Machine:

QUEUED → PROCESSING → COMPLETED
           │
           ├─→ AUDIO_EXTRACTED
           ├─→ TRANSCRIBED
           ├─→ TRANSLATED
           ├─→ SYNTHESIZED
           ├─→ SYNCHRONIZED
           ├─→ MERGED
           └─→ VALIDATED

Recovery: Resume from last successful checkpoint
Persistence: Redis + PostgreSQL (dual write)
Checkpoint Interval: After each major stage
```

---

### **3.5 Performance Optimization**

#### **3.5.1 Caching Strategy**

```
┌────────────────────────────────────────────────────────────┐
│                    MULTI-LAYER CACHE                        │
├────────────────────────────────────────────────────────────┤
│  L1: In-Memory Cache (Application)                         │
│  ├─ Voice configuration lookups                            │
│  ├─ API schema definitions                                 │
│  └─ TTL: 1 hour, Size: 100MB                              │
│                                                            │
│  L2: Redis Cache (Distributed)                            │
│  ├─ Translation cache (key: text_hash + lang_pair)        │
│  │   └─ TTL: 7 days                                       │
│  ├─ TTS audio cache (key: text_hash + voice + style)      │
│  │   └─ TTL: 30 days                                      │
│  ├─ User session data                                      │
│  │   └─ TTL: 24 hours                                     │
│  └─ Job status                                             │
│      └─ TTL: 24 hours                                      │
│                                                            │
│  L3: Google Cloud Storage (Persistent)                    │
│  └─ Completed video cache                                 │
│      └─ TTL: 30 days                                       │
└────────────────────────────────────────────────────────────┘

Cache Invalidation:
├─ On user request (force refresh)
├─ On language model update
└─ On voice model update
```

#### **3.5.2 Parallel Processing Strategy**

```
┌────────────────────────────────────────────────────────────┐
│            VIDEO SEGMENTATION FOR PARALLELIZATION           │
├────────────────────────────────────────────────────────────┤
│  Original Video (60 minutes)                               │
│  │                                                          │
│  ├─→ Segment 1 (0:00-10:00)  ───→ Worker Pool 1           │
│  ├─→ Segment 2 (10:00-20:00) ───→ Worker Pool 2           │
│  ├─→ Segment 3 (20:00-30:00) ───→ Worker Pool 3           │
│  ├─→ Segment 4 (30:00-40:00) ───→ Worker Pool 4           │
│  ├─→ Segment 5 (40:00-50:00) ───→ Worker Pool 5           │
│  └─→ Segment 6 (50:00-60:00) ───→ Worker Pool 6           │
│                                                            │
│  Parallel Processing:                                      │
│  ├─ Each segment processed independently                  │
│  ├─ Coordination via Sequential Agent                     │
│  ├─ Merge with overlap handling                           │
│  └─ Expected speedup: 4-5x                                │
│                                                            │
│  Segmentation Rules:                                       │
│  ├─ Segment at scene boundaries (if detected)             │
│  ├─ Segment at speaker changes                            │
│  ├─ Minimum segment: 5 minutes                            │
│  ├─ Maximum segment: 15 minutes                           │
│  └─ Overlap: 5 seconds for smooth transitions             │
└────────────────────────────────────────────────────────────┘
```

#### **3.5.3 API Optimization**

```
┌────────────────────────────────────────────────────────────┐
│              GEMINI API OPTIMIZATION STRATEGIES             │
├────────────────────────────────────────────────────────────┤
│  1. Batch Processing                                        │
│     ├─ Combine multiple segments in single API call        │
│     ├─ Max batch size: Based on token limits               │
│     └─ Reduces API overhead by 60%                         │
│                                                            │
│  2. Token Management                                        │
│     ├─ Audio: 32 tokens/second                            │
│     ├─ Pre-calculate token usage                          │
│     ├─ Split long audio strategically                     │
│     └─ Monitor and optimize context windows               │
│                                                            │
│  3. Structured Output                                      │
│     ├─ Use JSON schemas for predictable parsing           │
│     ├─ Reduce post-processing time by 80%                 │
│     └─ Enable parallel deserialization                    │
│                                                            │
│  4. Concurrent Requests                                    │
│     ├─ Use asyncio for non-blocking calls                 │
│     ├─ Max concurrent: 10 per API type                    │
│     ├─ Rate limiting: 60 requests/minute                  │
│     └─ Connection pooling                                 │
│                                                            │
│  5. Model Selection                                        │
│     ├─ Gemini 2.5 Flash for quick operations              │
│     ├─ Gemini 2.5 Pro for complex translations            │
│     └─ Dynamic selection based on complexity              │
└────────────────────────────────────────────────────────────┘
```

---

## **4. API Design**

### **4.1 REST API Endpoints**

```
POST   /api/v1/jobs/create
├─ Creates dubbing job
├─ Request: multipart/form-data (video file + metadata)
├─ Response: { job_id, status, estimated_time }
└─ Rate Limit: 10/hour per user

GET    /api/v1/jobs/{job_id}
├─ Get job status and progress
├─ Response: { job_id, status, progress_percent, stage, metadata }
└─ Rate Limit: 60/minute

GET    /api/v1/jobs/{job_id}/download
├─ Download dubbed video
├─ Response: Signed URL (24-hour validity)
└─ Rate Limit: 100/hour

DELETE /api/v1/jobs/{job_id}
├─ Cancel or delete job
└─ Response: { success, message }

GET    /api/v1/voices
├─ List available voices with samples
├─ Response: { voices: [{name, style, language, sample_url}] }
└─ Cached: 1 hour

GET    /api/v1/languages
├─ List supported languages
├─ Response: { languages: [{code, name, tts_support, audio_support}] }
└─ Cached: 1 hour

POST   /api/v1/jobs/{job_id}/retry
├─ Retry failed job
└─ Response: { job_id, status }

GET    /api/v1/jobs
├─ List user's jobs
├─ Query params: status, page, limit
└─ Response: Paginated job list
```

### **4.2 WebSocket API**

```
WS     /ws/jobs/{job_id}
├─ Real-time job progress updates
├─ Messages:
│  ├─ {"type": "status", "stage": "transcribing", "progress": 45}
│  ├─ {"type": "error", "message": "API rate limit", "retry_in": 60}
│  ├─ {"type": "complete", "download_url": "..."}
│  └─ {"type": "log", "message": "Processing segment 3/10"}
└─ Reconnection: Automatic with exponential backoff
```

---

## **5. Data Models**

### **5.1 Core Entities**

```python
Job:
├─ id: UUID
├─ user_id: UUID
├─ status: Enum [QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED]
├─ current_stage: String
├─ progress_percent: Integer
├─ source_language: String (BCP-47 code)
├─ target_language: String (BCP-47 code)
├─ voice_config: JSON
│  ├─ primary_voice: String
│  ├─ secondary_voice: String (optional)
│  └─ style_preferences: Object
├─ input_video_url: String
├─ output_video_url: String (nullable)
├─ metadata: JSON
│  ├─ duration_seconds: Float
│  ├─ file_size_mb: Float
│  ├─ resolution: String
│  ├─ detected_speakers: Integer
│  └─ processing_time_seconds: Float
├─ error_message: Text (nullable)
├─ checkpoints: JSON []
├─ created_at: Timestamp
├─ updated_at: Timestamp
└─ completed_at: Timestamp (nullable)

Transcript:
├─ id: UUID
├─ job_id: UUID (FK)
├─ segments: JSON []
│  └─ [{
│      speaker: String,
│      start_time: Float,
│      end_time: Float,
│      text: String,
│      confidence: Float
│    }]
└─ language: String

Translation:
├─ id: UUID
├─ transcript_id: UUID (FK)
├─ segments: JSON []
│  └─ [{
│      original_text: String,
│      translated_text: String,
│      start_time: Float,
│      end_time: Float,
│      duration_ms: Integer,
│      emotion_tag: String,
│      formality: Enum
│    }]
└─ target_language: String

ProcessingLog:
├─ id: UUID
├─ job_id: UUID (FK)
├─ stage: String
├─ status: Enum [SUCCESS, FAILURE, RETRY]
├─ message: Text
├─ metadata: JSON
└─ timestamp: Timestamp
```

---

## **6. Security Architecture**

### **6.1 Authentication & Authorization**

```
┌────────────────────────────────────────────────────────────┐
│                 AUTHENTICATION FLOW                         │
├────────────────────────────────────────────────────────────┤
│  1. User Login                                              │
│     ├─ OAuth 2.0 / JWT-based                               │
│     ├─ Google Sign-In integration                          │
│     └─ Token expiry: 1 hour                                │
│                                                            │
│  2. API Key for Programmatic Access                        │
│     ├─ API key generation per user                         │
│     ├─ Scope-based permissions                             │
│     └─ Rate limiting per API key                           │
│                                                            │
│  3. Authorization                                          │
│     ├─ Role-Based Access Control (RBAC)                    │
│     │  ├─ Admin: Full access                              │
│     │  ├─ Premium: Higher limits                          │
│     │  └─ Free: Basic access                              │
│     └─ Resource ownership validation                       │
└────────────────────────────────────────────────────────────┘
```

### **6.2 Data Security**

```
┌────────────────────────────────────────────────────────────┐
│                  DATA PROTECTION                            │
├────────────────────────────────────────────────────────────┤
│  In Transit:                                                │
│  ├─ TLS 1.3 for all API communications                     │
│  ├─ Certificate pinning for mobile apps                    │
│  └─ HTTPS only (HSTS enabled)                              │
│                                                            │
│  At Rest:                                                  │
│  ├─ Google Cloud Storage encryption (AES-256)             │
│  ├─ Database encryption (PostgreSQL native)               │
│  └─ Encrypted backups                                      │
│                                                            │
│  Access Control:                                           │
│  ├─ Signed URLs with expiration                           │
│  ├─ IP whitelisting for admin APIs                        │
│  ├─ API key rotation (90 days)                            │
│  └─ Audit logging                                          │
│                                                            │
│  Privacy:                                                  │
│  ├─ Automatic PII detection in transcripts                │
│  ├─ Data retention policies (30 days default)             │
│  ├─ User data deletion on request                         │
│  └─ GDPR compliance                                        │
└────────────────────────────────────────────────────────────┘
```

---

## **7. Monitoring & Observability**

### **7.1 Metrics & Monitoring**

```
┌────────────────────────────────────────────────────────────┐
│              MONITORING STACK                               │
├────────────────────────────────────────────────────────────┤
│  Prometheus (Metrics Collection)                           │
│  ├─ System Metrics                                         │
│  │  ├─ CPU, Memory, Disk usage                            │
│  │  ├─ Network I/O                                         │
│  │  └─ Worker health                                       │
│  ├─ Application Metrics                                    │
│  │  ├─ API request rate                                    │
│  │  ├─ Response times (p50, p95, p99)                     │
│  │  ├─ Error rates                                         │
│  │  └─ Job processing times                                │
│  ├─ Business Metrics                                       │
│  │  ├─ Jobs completed per hour                            │
│  │  ├─ Average processing time per minute of video        │
│  │  ├─ API cost per job                                   │
│  │  └─ User satisfaction (quality scores)                 │
│  └─ External API Metrics                                   │
│     ├─ Gemini API latency                                  │
│     ├─ Gemini API error rates                              │
│     ├─ Token usage                                         │
│     └─ Rate limit proximity                                │
│                                                            │
│  Grafana (Visualization)                                   │
│  └─ Dashboards                                             │
│     ├─ System health                                       │
│     ├─ Job processing pipeline                             │
│     ├─ Cost tracking                                       │
│     └─ User analytics                                      │
│                                                            │
│  ELK Stack (Logging)                                       │
│  ├─ Elasticsearch: Log storage & search                   │
│  ├─ Logstash: Log aggregation                             │
│  └─ Kibana: Log visualization                             │
│                                                            │
│  Alerting (PagerDuty / Slack)                             │
│  ├─ High error rates (>5%)                                │
│  ├─ API downtime                                           │
│  ├─ Worker pool exhaustion                                │
│  ├─ Storage capacity warnings                             │
│  └─ Cost budget exceeded                                   │
└────────────────────────────────────────────────────────────┘
```

### **7.2 Distributed Tracing**

```
Using OpenTelemetry + Jaeger

Trace Example: Job Processing
├─ Span 1: API Request (POST /jobs/create)
│  └─ Duration: 150ms
├─ Span 2: File Upload to GCS
│  └─ Duration: 2.5s
├─ Span 3: Job Queue Enqueue
│  └─ Duration: 50ms
├─ Span 4: Worker Pickup
│  └─ Duration: 100ms
├─ Span 5: ADK Coordinator Agent Decision
│  └─ Duration: 300ms
├─ Span 6: Audio Extraction
│  └─ Duration: 5s
├─ Span 7: Gemini Audio API (Transcription)
│  └─ Duration: 12s
├─ Span 8: Gemini LLM API (Translation)
│  └─ Duration: 8s
├─ Span 9: Gemini TTS API (Speech Synthesis)
│  └─ Duration: 15s
├─ Span 10: Audio Merging
│  └─ Duration: 4s
└─ Span 11: Final Upload
   └─ Duration: 3s

Total: 50s (for 10-minute video)
```

---

## **8. Deployment Architecture**

### **8.1 Container Orchestration (Kubernetes)**

```
┌────────────────────────────────────────────────────────────┐
│                KUBERNETES CLUSTER                           │
├────────────────────────────────────────────────────────────┤
│  Namespaces:                                                │
│  ├─ production                                              │
│  ├─ staging                                                 │
│  └─ development                                             │
│                                                            │
│  Deployments:                                              │
│  ├─ fastapi-api (3 replicas)                              │
│  │  ├─ Resource requests: 2 CPU, 4GB RAM                  │
│  │  ├─ Resource limits: 4 CPU, 8GB RAM                    │
│  │  └─ HPA: Scale 3-10 based on CPU >70%                  │
│  │                                                          │
│  ├─ celery-workers-video (5 replicas)                     │
│  │  ├─ Resource requests: 4 CPU, 8GB RAM                  │
│  │  ├─ Resource limits: 8 CPU, 16GB RAM                   │
│  │  └─ HPA: Scale 5-20 based on queue depth               │
│  │                                                          │
│  ├─ celery-workers-ai (10 replicas)                       │
│  │  ├─ Resource requests: 2 CPU, 4GB RAM                  │
│  │  ├─ Resource limits: 4 CPU, 8GB RAM                    │
│  │  └─ HPA: Scale 10-50 based on queue depth              │
│  │                                                          │
│  └─ redis-cluster (3 replicas)                            │
│     ├─ StatefulSet                                         │
│     └─ PersistentVolumeClaims                             │
│                                                            │
│  Services:                                                 │
│  ├─ api-service (LoadBalancer)                            │
│  ├─ redis-service (ClusterIP)                             │
│  └─ postgresql-service (ClusterIP)                        │
│                                                            │
│  Ingress:                                                  │
│  ├─ NGINX Ingress Controller                              │
│  ├─ SSL/TLS termination                                   │
│  └─ Rate limiting middleware                              │
└────────────────────────────────────────────────────────────┘
```

### **8.2 CI/CD Pipeline**

```
┌────────────────────────────────────────────────────────────┐
│                    CI/CD WORKFLOW                           │
├────────────────────────────────────────────────────────────┤
│  1. Development                                             │
│     ├─ Git push to feature branch                         │
│     └─ Automated unit tests (pytest)                       │
│                                                            │
│  2. Build                                                  │
│     ├─ Docker image build                                 │
│     ├─ Security scanning (Trivy)                          │
│     └─ Push to Container Registry                         │
│                                                            │
│  3. Staging Deployment                                     │
│     ├─ Deploy to staging namespace                        │
│     ├─ Integration tests                                  │
│     ├─ Performance tests (Locust)                         │
│     └─ Smoke tests                                         │
│                                                            │
│  4. Production Deployment                                  │
│     ├─ Manual approval gate                               │
│     ├─ Blue-green deployment strategy                     │
│     ├─ Health checks                                       │
│     ├─ Gradual traffic shift (10% → 50% → 100%)          │
│     └─ Rollback capability                                │
│                                                            │
│  5. Post-Deployment                                        │
│     ├─ Monitoring alerts verification                     │
│     └─ Automated E2E tests                                │
└────────────────────────────────────────────────────────────┘
```

---

## **9. Cost Optimization Strategy**

### **9.1 Gemini API Cost Management**

```
┌────────────────────────────────────────────────────────────┐
│               API COST OPTIMIZATION                         │
├────────────────────────────────────────────────────────────┤
│  1. Smart Caching                                           │
│     ├─ Cache translations (hit rate target: 40%)          │
│     ├─ Cache TTS audio (hit rate target: 30%)             │
│     └─ Estimated savings: $500/month                      │
│                                                            │
│  2. Batch Processing                                       │
│     ├─ Combine API calls where possible                   │
│     ├─ Reduce API overhead by 60%                         │
│     └─ Estimated savings: $300/month                      │
│                                                            │
│  3. Model Selection                                        │
│     ├─ Use Flash models for simple tasks (70% of jobs)    │
│     ├─ Reserve Pro models for complex translations        │
│     └─ Estimated savings: $400/month                      │
│                                                            │
│  4. Token Optimization                                     │
│     ├─ Compress prompts                                   │
│     ├─ Remove redundant context                           │
│     └─ Estimated savings: $200/month                      │
│                                                            │
│  5. Rate Limiting & Quotas                                 │
│     ├─ User tier-based limits                             │
│     ├─ Peak hour throttling                               │
│     └─ Cost cap per job                                   │
└────────────────────────────────────────────────────────────┘

Estimated Monthly Costs (1000 jobs, avg 10-min videos):
├─ Audio Understanding API: $800
├─ Translation API: $1,200
├─ TTS API: $1,500
├─ Infrastructure (GCP): $600
├─ Storage: $200
└─ Total: $4,300 ($4.30/job)
```

---

## **10. Frontend Architecture (React)**

### **10.1 Component Hierarchy**

```
App
├─ AuthProvider
│  └─ AuthContext
├─ Router
│  ├─ HomePage
│  ├─ DashboardPage
│  │  ├─ JobList
│  │  │  └─ JobCard
│  │  └─ JobStats
│  ├─ CreateJobPage
│  │  ├─ VideoUpload (Dropzone)
│  │  ├─ LanguageSelector
│  │  ├─ VoiceConfigurator
│  │  │  ├─ VoicePreview
│  │  │  └─ StyleOptions
│  │  └─ SubmitButton
│  ├─ JobDetailPage
│  │  ├─ ProgressTracker (WebSocket)
│  │  ├─ ProcessingLogs
│  │  ├─ VideoPreview
│  │  │  ├─ OriginalPlayer
│  │  │  └─ DubbedPlayer
│  │  └─ DownloadButton
│  └─ SettingsPage
└─ Notifications (Toast)
```

### **10.2 State Management**

```
┌────────────────────────────────────────────────────────────┐
│              STATE MANAGEMENT STRATEGY                      │
├────────────────────────────────────────────────────────────┤
│  Global State (Redux Toolkit / Zustand)                    │
│  ├─ auth: { user, token, isAuthenticated }                │
│  ├─ jobs: { list, activeJob, filters }                    │
│  └─ ui: { theme, notifications, modals }                  │
│                                                            │
│  Server State (React Query)                                │
│  ├─ Queries:                                               │
│  │  ├─ useJobs() - Fetch job list                        │
│  │  ├─ useJob(id) - Fetch single job                     │
│  │  ├─ useVoices() - Fetch available voices              │
│  │  └─ useLanguages() - Fetch supported languages        │
│  ├─ Mutations:                                             │
│  │  ├─ useCreateJob() - Create new job                   │
│  │  ├─ useDeleteJob() - Delete job                       │
│  │  └─ useRetryJob() - Retry failed job                  │
│  └─ Caching:                                               │
│     ├─ Job list: 30 seconds                               │
│     ├─ Job detail: Real-time (WebSocket)                  │
│     └─ Voices/Languages: 1 hour                           │
│                                                            │
│  Local State                                               │
│  └─ Component-specific (useState, useReducer)             │
└────────────────────────────────────────────────────────────┘
```

### **10.3 Real-time Updates**

```
WebSocket Integration:

useWebSocket(jobId) {
  ├─ Connect on mount
  ├─ Subscribe to job events
  ├─ Update React Query cache
  ├─ Show toast notifications
  ├─ Automatic reconnection
  └─ Disconnect on unmount
}

Events:
├─ job.status.update → Update progress bar
├─ job.stage.change → Update stage indicator
├─ job.error → Show error toast
├─ job.complete → Show success + enable download
└─ job.log → Append to log viewer
```

---

## **11. Quality Assurance**

### **11.1 Testing Strategy**

```
┌────────────────────────────────────────────────────────────┐
│                 TESTING PYRAMID                             │
├────────────────────────────────────────────────────────────┤
│  E2E Tests (10%)                                            │
│  ├─ Playwright / Cypress                                   │
│  ├─ Critical user journeys                                 │
│  └─ Run: Pre-deployment                                    │
│                                                            │
│  Integration Tests (30%)                                   │
│  ├─ API endpoint tests                                     │
│  ├─ Agent interaction tests                                │
│  ├─ Database integration                                   │
│  └─ Run: On every PR                                       │
│                                                            │
│  Unit Tests (60%)                                          │
│  ├─ pytest (Python)                                        │
│  ├─ Jest (React)                                           │
│  ├─ Coverage target: 80%                                   │
│  └─ Run: On every commit                                   │
│                                                            │
│  Performance Tests                                         │
│  ├─ Locust (load testing)                                  │
│  ├─ Target: 100 concurrent jobs                           │
│  └─ Run: Weekly                                            │
│                                                            │
│  Security Tests                                            │
│  ├─ OWASP ZAP                                              │
│  ├─ Dependency scanning                                    │
│  └─ Run: Weekly + Pre-deployment                           │
└────────────────────────────────────────────────────────────┘
```

---

## **12. Future Enhancements**

### **12.1 Roadmap**

**Phase 1 (Months 1-3): MVP**
- ✓ Basic video dubbing pipeline
- ✓ Single-language support
- ✓ Web interface

**Phase 2 (Months 4-6): Enhancement**
- Batch video processing
- API for programmatic access
- Advanced voice customization
- Subtitle generation

**Phase 3 (Months 7-9): Intelligence**
- Emotion detection and matching
- Background music preservation
- Automatic quality scoring
- A/B testing of voices

**Phase 4 (Months 10-12): Scale**
- Multi-region deployment
- Real-time dubbing (Live API)
- Video editing integration
- White-label solution

---

## **13. Key Design Decisions Summary**

| **Decision** | **Rationale** | **Trade-off** |
|--------------|---------------|---------------|
| **Google ADK for orchestration** | Provides intelligent agent coordination with built-in patterns | Learning curve, Google ecosystem dependency |
| **Gemini native audio APIs** | Unified API, better integration, controllable TTS | Limited to Gemini models |
| **FastAPI async** | High performance, native async support, OpenAPI docs | Python-specific |
| **Celery for task queue** | Mature, reliable, good monitoring | Requires Redis/RabbitMQ |
| **PostgreSQL** | ACID compliance, JSON support, mature ecosystem | Not as horizontally scalable as NoSQL |
| **Google Cloud Storage** | Native integration, CDN, lifecycle policies | Vendor lock-in |
| **Parallel segment processing** | 5x speedup for long videos | Complexity in coordination |

---

## References:
- https://google.github.io/adk-docs/agents/ 
- https://ai.google.dev/gemini-api/docs/audio
- https://ai.google.dev/gemini-api/docs/speech-generation
- https://ai.google.dev/gemini-api/docs/structured-output
- https://ai.google.dev/gemini-api/docs/files