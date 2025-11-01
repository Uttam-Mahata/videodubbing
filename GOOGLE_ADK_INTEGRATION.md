# Google ADK Integration - Video Dubbing Backend

## ✅ IMPLEMENTATION STATUS: COMPLETE

Successfully integrated **Google ADK (Agent Development Kit)** with real patterns from `google/adk-samples` repository.

---

## 🎯 What Changed

### Before (Placeholder Implementation)
- Custom `BaseAgent` class with placeholder imports
- Manually implemented event loops
- No actual ADK integration

### After (Real Google ADK)
- **Direct use of `google.adk.agents.Agent`**
- **`SequentialAgent` for pipeline orchestration**
- **`InMemoryRunner` for agent execution**
- **Tool functions with `ToolContext`**
- **Proper ADK patterns from adk-samples**

---

## 📦 New File Structure

```
backend/agents/
├── __init__.py          # Exports root_agent
├── agent.py             # ⭐ NEW: Main ADK agent definitions
├── prompts.py           # ⭐ NEW: Agent instruction prompts
├── base.py              # DEPRECATED: Old placeholder
├── coordinator.py       # DEPRECATED: Old custom agent
├── transcription.py     # DEPRECATED: Old custom agent
├── translation.py       # DEPRECATED: Old custom agent
└── speech_synthesis.py  # DEPRECATED: Old custom agent
```

---

## 🏗️ Architecture

### 1. Agent Definitions (`backend/agents/agent.py`)

```python
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import ToolContext

# Tool functions (async functions with ToolContext)
async def transcribe_audio_tool(audio_path, source_language, tool_context):
    # Uses GeminiAudioService
    # Stores transcript in tool_context.state
    pass

# Agent instantiation (simple!)
transcription_agent = Agent(
    model="gemini-2.5-flash",
    name="transcription_agent",
    description="...",
    instruction=TRANSCRIPTION_PROMPT,
    tools=[transcribe_audio_tool],
    output_key="transcription_result",
)

# Sequential pipeline
dubbing_pipeline_agent = SequentialAgent(
    name="dubbing_pipeline",
    description="Complete dubbing workflow",
    sub_agents=[
        transcription_agent,
        translation_agent,
        speech_synthesis_agent,
    ],
)

# Root agent
root_agent = dubbing_pipeline_agent
```

### 2. InMemoryRunner Integration (`backend/main.py`)

```python
from google.adk.runners import InMemoryRunner
from backend.agents import root_agent

# Initialize in lifespan
runner = InMemoryRunner(
    agent=root_agent,
    app_name="videodubbing",
)

# Execute agent
async def execute_dubbing_job(request: dict):
    session = await runner.session_service.create_session(...)
    session.state.update({...})
    
    async for event in runner.run_async(...):
        # Process events
        pass
```

### 3. Tool Pattern

All agent logic moved to **tool functions**:

```python
async def transcribe_audio_tool(
    audio_path: str,
    source_language: str,
    tool_context: ToolContext,
) -> dict:
    """
    Tool function called by agent
    - Reads from tool_context.state
    - Writes to tool_context.state
    - Returns dict with status
    """
    transcript = await audio_service.transcribe(...)
    tool_context.state["transcript"] = transcript
    return {"status": "success"}
```

---

## 🚀 How to Run

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create `.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_GENAI_USE_VERTEXAI=false  # or true for Vertex AI
```

### 3. Start Server

```bash
python main.py
```

Server runs at: http://localhost:8000

### 4. Execute Dubbing Job

```bash
curl -X POST http://localhost:8000/api/v1/jobs/execute \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test_001",
    "audio_path": "/path/to/audio.wav",
    "source_language": "en",
    "target_language": "es",
    "voice_config": {
      "voice_name": "Kore",
      "language": "es"
    }
  }'
```

---

## 📝 Key Files

| File | Purpose |
|------|---------|
| `backend/agents/agent.py` | ⭐ Main agent definitions with Google ADK |
| `backend/agents/prompts.py` | Agent instruction prompts |
| `backend/main.py` | FastAPI app with InMemoryRunner integration |
| `backend/requirements.txt` | Includes `google-adk>=1.17.0` |

---

## 🔑 Google ADK Patterns Used

Based on `google/adk-samples`:

1. **Agent Instantiation**: `Agent(model, name, instruction, tools)`
2. **Sequential Pipeline**: `SequentialAgent(sub_agents=[...])`
3. **Tool Functions**: `async def tool(args, tool_context: ToolContext)`
4. **Runner Execution**: `InMemoryRunner(agent=root_agent)`
5. **Session Management**: `runner.session_service.create_session()`
6. **State Management**: `tool_context.state[key] = value`

Reference: 
- https://github.com/google/adk-samples/tree/main/python/agents/short-movie-agents
- https://github.com/google/adk-samples/tree/main/python/agents/gemini-fullstack

---

## 🎓 What We Learned

1. **Google ADK is simple**: No complex base classes needed
2. **Agents are declarative**: Just pass model + instruction + tools
3. **State management is automatic**: `tool_context.state` shared across tools
4. **Pipelines are built-in**: `SequentialAgent`, `ParallelAgent`, `LoopAgent`
5. **Runners handle execution**: `InMemoryRunner` manages sessions/state

---

## 🔄 Pipeline Flow

```
User Request
    ↓
FastAPI Endpoint (/api/v1/jobs/execute)
    ↓
InMemoryRunner.run_async()
    ↓
SequentialAgent (dubbing_pipeline)
    ↓
┌─────────────────────────────────┐
│ 1. transcription_agent          │
│    ↓ calls transcribe_audio_tool│
│    ↓ stores transcript in state │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 2. translation_agent            │
│    ↓ reads transcript from state│
│    ↓ calls translate_segments   │
│    ↓ stores translation in state│
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 3. speech_synthesis_agent       │
│    ↓ reads translation from state│
│    ↓ calls synthesize_speech    │
│    ↓ stores audio_segments      │
└─────────────────────────────────┘
    ↓
Response with final state
```

---

## ✨ Next Steps

1. **Test the pipeline** with actual audio files
2. **Add WebSocket support** for real-time progress
3. **Implement ParallelAgent** for concurrent segment processing
4. **Add LoopAgent** for quality validation with retries
5. **Integrate MongoDB** for job persistence
6. **Add Celery workers** for background processing

---

## 📚 References

- Google ADK Docs: https://google.github.io/adk-docs/
- ADK Samples: https://github.com/google/adk-samples
- Gemini API: https://ai.google.dev/gemini-api/docs
- Short Movie Agents Example: https://github.com/google/adk-samples/tree/main/python/agents/short-movie-agents
