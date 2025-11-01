"""Circuit Breaker Pattern Implementation"""

import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    timeout_seconds: int = 60
    half_open_test_requests: int = 3
    success_threshold: int = 2


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    test_request_count: int = 0
    opened_at: Optional[float] = None


class CircuitBreaker:
    """
    Circuit Breaker implementation for fault tolerance
    
    States:
    - CLOSED: Normal operation, counting failures
    - OPEN: Blocking requests after threshold exceeded
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            # Check if circuit should transition states
            await self._check_state_transition()
            
            # If circuit is open, reject request
            if self.stats.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable until {self._get_timeout_remaining()}s"
                )
        
        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Record success
            await self._on_success()
            return result
            
        except Exception as e:
            # Record failure
            await self._on_failure(e)
            raise
    
    async def _check_state_transition(self):
        """Check if circuit breaker should transition states"""
        current_time = time.time()
        
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.stats.opened_at and (
                current_time - self.stats.opened_at >= self.config.timeout_seconds
            ):
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.test_request_count = 0
                self.stats.success_count = 0
        
        elif self.stats.state == CircuitState.HALF_OPEN:
            # Check if we've exceeded test request limit
            if self.stats.test_request_count >= self.config.half_open_test_requests:
                # Check if enough successes to close circuit
                if self.stats.success_count >= self.config.success_threshold:
                    logger.info(f"Circuit breaker '{self.name}' closing after successful tests")
                    self._reset()
                else:
                    logger.warning(f"Circuit breaker '{self.name}' reopening after failed tests")
                    self._open_circuit()
    
    async def _on_success(self):
        """Handle successful request"""
        async with self._lock:
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.success_count += 1
                self.stats.test_request_count += 1
                logger.debug(
                    f"Circuit breaker '{self.name}' half-open success: "
                    f"{self.stats.success_count}/{self.config.half_open_test_requests}"
                )
            elif self.stats.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.stats.failure_count = 0
    
    async def _on_failure(self, exception: Exception):
        """Handle failed request"""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.test_request_count += 1
                logger.warning(
                    f"Circuit breaker '{self.name}' test failed: {exception}"
                )
                # One failure in half-open state triggers reopening
                self._open_circuit()
                
            elif self.stats.state == CircuitState.CLOSED:
                logger.warning(
                    f"Circuit breaker '{self.name}' failure {self.stats.failure_count}/"
                    f"{self.config.failure_threshold}: {exception}"
                )
                
                # Check if we've hit failure threshold
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit"""
        self.stats.state = CircuitState.OPEN
        self.stats.opened_at = time.time()
        logger.error(
            f"Circuit breaker '{self.name}' OPENED after "
            f"{self.stats.failure_count} failures"
        )
    
    def _reset(self):
        """Reset circuit breaker to closed state"""
        self.stats.state = CircuitState.CLOSED
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self.stats.last_failure_time = None
        self.stats.test_request_count = 0
        self.stats.opened_at = None
    
    def _get_timeout_remaining(self) -> float:
        """Get remaining timeout duration"""
        if self.stats.opened_at:
            elapsed = time.time() - self.stats.opened_at
            return max(0, self.config.timeout_seconds - elapsed)
        return 0
    
    def get_stats(self) -> dict:
        """Get current circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "timeout_remaining": self._get_timeout_remaining() if self.stats.state == CircuitState.OPEN else None,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is in OPEN state"""
    pass
