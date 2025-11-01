"""
Coordinator Agent
Intelligent decision-making for pipeline orchestration
"""

import logging
from typing import AsyncGenerator

from backend.agents.base import BaseCustomAgent, Event, InvocationContext

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseCustomAgent):
    """
    Coordinator Agent for intelligent orchestration
    
    Responsibilities:
    - Analyze video characteristics
    - Determine processing strategy
    - Make resource allocation decisions
    - Handle error recovery strategies
    """
    
    def __init__(self):
        super().__init__(
            name="CoordinatorAgent",
            description="Intelligent coordinator for dubbing pipeline"
        )
    
    async def _run_async_impl(
        self,
        ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Analyze job and determine processing strategy
        
        Context state expected:
        - job_id: str
        - video_metadata: dict
        - source_language: str
        - target_language: str
        
        Context state updated:
        - processing_strategy: str
        - should_segment: bool
        - estimated_duration: int
        """
        logger.info(f"[{self.name}] Analyzing job requirements")
        
        # Extract job metadata from context
        job_id = ctx.state.get("job_id")
        video_metadata = ctx.state.get("video_metadata", {})
        duration_seconds = video_metadata.get("duration_seconds", 0)
        
        yield Event(
            id=f"{self.name}_analysis_start",
            author=self.name,
            content={"stage": "analysis", "job_id": job_id},
            metadata={"progress": 5}
        )
        
        # Determine processing strategy
        if duration_seconds > 600:  # > 10 minutes
            strategy = "parallel"
            should_segment = True
            logger.info(f"[{self.name}] Long video detected: using parallel processing")
        else:
            strategy = "sequential"
            should_segment = False
            logger.info(f"[{self.name}] Short video detected: using sequential processing")
        
        # Estimate processing time
        # Rough estimate: 2x video duration for processing
        estimated_duration = int(duration_seconds * 2)
        
        # Update context state
        ctx.state["processing_strategy"] = strategy
        ctx.state["should_segment"] = should_segment
        ctx.state["estimated_duration_minutes"] = estimated_duration // 60
        
        yield Event(
            id=f"{self.name}_decision",
            author=self.name,
            content={
                "strategy": strategy,
                "should_segment": should_segment,
                "estimated_duration_minutes": estimated_duration // 60,
            },
            metadata={"progress": 10}
        )
        
        logger.info(
            f"[{self.name}] Strategy determined: {strategy}, "
            f"Estimated time: {estimated_duration // 60} minutes"
        )
