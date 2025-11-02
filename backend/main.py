"""
Main FastAPI Application
Production-level backend for video dubbing using Google ADK
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from google.genai.types import Part, Content
import time

from backend.config.settings import settings
from backend.api.routes import jobs, health, voices
from backend.utils.logging_config import setup_logging
from backend.db.mongodb import connect_to_mongodb, close_database_connection
from backend.db.redis_client import connect_to_redis, close_redis_connection
from backend.workers import start_job_processor, stop_job_processor

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global ADK Runner instance
runner = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    global runner
    
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    try:
        # Initialize database connections
        
        # Connect to MongoDB
        await connect_to_mongodb()
        
        # Connect to Redis
        await connect_to_redis()
        
        # Initialize Google ADK Runner
        from google.adk.runners import InMemoryRunner
        from backend.agents import root_agent
        
        runner = InMemoryRunner(
            agent=root_agent,
            app_name="videodubbing",
        )
        logger.info("✅ Google ADK InMemoryRunner initialized")
        
        # Start background job processor
        await start_job_processor()
        logger.info("✅ Background job processor started")
        
        logger.info("🚀 Application startup complete")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    try:
        # Stop background job processor
        await stop_job_processor()
        
        # Close database connections
        await close_database_connection()
        
        # Close Redis connection
        await close_redis_connection()
        
        # Cleanup ADK runner
        runner = None
        
        logger.info("✅ Application shutdown complete")
        
    except Exception as e:
        logger.error(f"⚠️ Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-level video dubbing API using Google ADK and Gemini APIs",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)


# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An error occurred",
        }
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(voices.router, prefix="/api/v1", tags=["Voices"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/api/docs" if settings.debug else "disabled",
    }


# Google ADK Agent execution endpoint
@app.post("/api/v1/jobs/execute")
async def execute_dubbing_job(request: dict):
    """
    Execute a video dubbing job using Google ADK agents.
    
    Example request:
    {
        "job_id": "job_123",
        "audio_path": "/path/to/audio.wav",
        "source_language": "en",
        "target_language": "es",
        "voice_config": {
            "voice_name": "Kore",
            "language": "es"
        }
    }
    """
    global runner
    
    if not runner:
        return JSONResponse(
            status_code=503,
            content={"error": "ADK runner not initialized"},
        )
    
    try:
        # Create ADK session
        session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=request.get("user_id", "default_user"),
        )
        
        # Set initial state
        session.state.update({
            "job_id": request.get("job_id"),
            "audio_path": request.get("audio_path"),
            "source_language": request.get("source_language"),
            "target_language": request.get("target_language"),
            "voice_config": request.get("voice_config"),
        })
        
        # Create user message
        user_message = Content(
            parts=[Part(text=f"Execute dubbing for job: {request.get('job_id')}")]
        )
        
        # Execute agent pipeline
        events = []
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=user_message,
        ):
            logger.info(f"Agent event: {event}")
            events.append(str(event))
        
        return {
            "status": "success",
            "session_id": session.id,
            "job_id": request.get("job_id"),
            "events_count": len(events),
            "final_state_keys": list(session.state.keys()),
        }
        
    except Exception as e:
        logger.error(f"Job execution failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
