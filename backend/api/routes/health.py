"""
Health Check Endpoints
System health and readiness checks
"""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from backend.config.settings import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response"""
    ready: bool
    services: dict


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint
    
    Returns application status and version
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check endpoint
    
    Checks if application is ready to serve requests
    """
    # TODO: Check database connection
    # TODO: Check Redis connection
    # TODO: Check Gemini API connectivity
    
    services = {
        "database": "unknown",
        "redis": "unknown",
        "gemini_api": "unknown",
    }
    
    return ReadinessResponse(
        ready=True,
        services=services,
    )
