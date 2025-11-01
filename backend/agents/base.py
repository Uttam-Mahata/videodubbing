"""
Base Custom Agent
Foundation for all custom agents using Google ADK
"""

import logging
from typing import AsyncGenerator, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

# Note: These are placeholder imports for Google ADK
# In production, import from actual ADK package
# from adk.agents import BaseAgent
# from adk.events import Event
# from adk.agents.invocation_context import InvocationContext

logger = logging.getLogger(__name__)


class Event(BaseModel):
    """Event emitted by agents (placeholder)"""
    id: str
    author: str
    content: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class InvocationContext(BaseModel):
    """Agent invocation context (placeholder)"""
    session: dict = Field(default_factory=dict)
    state: dict = Field(default_factory=dict)


class BaseCustomAgent(ABC):
    """
    Base class for custom ADK agents
    
    Implements the agent pattern for video dubbing pipeline
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        logger.info(f"Initialized agent: {name}")
    
    @abstractmethod
    async def _run_async_impl(
        self,
        ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Core agent execution logic
        
        Args:
            ctx: Invocation context with session state
            
        Yields:
            Events during processing
        """
        pass
    
    async def run_async(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute agent with error handling
        
        Args:
            ctx: Invocation context
            
        Yields:
            Processing events
        """
        logger.info(f"[{self.name}] Starting execution")
        
        try:
            async for event in self._run_async_impl(ctx):
                yield event
                
        except Exception as e:
            logger.error(f"[{self.name}] Execution failed: {e}")
            # Yield error event
            yield Event(
                id=f"{self.name}_error",
                author=self.name,
                content={"error": str(e)},
                metadata={"status": "error"}
            )
            raise
        
        logger.info(f"[{self.name}] Execution completed")
