"""
AI Engine Guard - Safety wrapper for all AI engines
Provides isolation, logging, and safe defaults for engine failures
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
import time
from typing import Dict, Any, Callable, Optional
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EngineSafetyConfig:
    """Safety configuration for AI engines"""
    max_execution_time: float = 0.001  # 1ms max execution time
    cooldown_seconds: int = 3
    max_failures: int = 5
    failure_reset_seconds: int = 60

@dataclass
class EngineExecutionResult:
    """Result of engine execution with safety metadata"""
    success: bool
    result: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None
    safe_default_used: bool = False

class AIEngineGuard:
    """
    Safety wrapper for AI engines
    Provides isolation, logging, and safe defaults
    """
    
    def __init__(self, engine_name: str, safe_default: Dict[str, Any]):
        self.engine_name = engine_name
        self.safe_default = safe_default
        self.config = EngineSafetyConfig()
        
        # Safety tracking
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_execution_time = 0
        self.total_executions = 0
        self.successful_executions = 0
        
        logger.info(f"AIEngineGuard initialized for {engine_name}")
    
    def safe_execute(self, engine_func: Callable, *args, **kwargs) -> EngineExecutionResult:
        """
        Safely execute an AI engine with isolation and fallbacks
        
        Args:
            engine_func: The engine function to execute
            *args, **kwargs: Arguments to pass to the engine function
            
        Returns:
            EngineExecutionResult with safe defaults on failure
        """
        start_time = time.time()
        self.total_executions += 1
        
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_execution_time < self.config.cooldown_seconds:
            logger.warning(f"{self.engine_name}: Cooldown active, returning safe default")
            return EngineExecutionResult(
                success=False,
                result=self.safe_default.copy(),
                execution_time=0.0,
                error="Cooldown active",
                safe_default_used=True
            )
        
        # Check failure threshold
        if (self.failure_count >= self.config.max_failures and 
            current_time - self.last_failure_time < self.config.failure_reset_seconds):
            logger.warning(f"{self.engine_name}: Failure threshold exceeded, returning safe default")
            return EngineExecutionResult(
                success=False,
                result=self.safe_default.copy(),
                execution_time=0.0,
                error="Failure threshold exceeded",
                safe_default_used=True
            )
        
        try:
            # Execute engine with timeout
            execution_start = time.time()
            result = engine_func(*args, **kwargs)
            execution_time = time.time() - execution_start
            
            # Check execution time
            if execution_time > self.config.max_execution_time:
                logger.warning(f"{self.engine_name}: Execution time exceeded: {execution_time:.4f}s")
                self._record_failure("Execution timeout")
                return EngineExecutionResult(
                    success=False,
                    result=self.safe_default.copy(),
                    execution_time=execution_time,
                    error="Execution timeout",
                    safe_default_used=True
                )
            
            # Validate result structure
            if not self._validate_result(result):
                logger.warning(f"{self.engine_name}: Invalid result structure")
                self._record_failure("Invalid result structure")
                return EngineExecutionResult(
                    success=False,
                    result=self.safe_default.copy(),
                    execution_time=execution_time,
                    error="Invalid result structure",
                    safe_default_used=True
                )
            
            # Success
            self.successful_executions += 1
            self.last_execution_time = current_time
            
            total_time = time.time() - start_time
            
            logger.debug(f"{self.engine_name}: Execution successful in {total_time:.4f}s")
            
            return EngineExecutionResult(
                success=True,
                result=result,
                execution_time=total_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{self.engine_name}: Engine execution failed - {str(e)}"
            logger.error(error_msg)
            
            self._record_failure(str(e))
            
            return EngineExecutionResult(
                success=False,
                result=self.safe_default.copy(),
                execution_time=execution_time,
                error=str(e),
                safe_default_used=True
            )
    
    def _validate_result(self, result: Any) -> bool:
        """Validate engine result structure"""
        if not isinstance(result, dict):
            return False
        
        # Check required fields based on engine type
        required_fields = ["signal", "confidence", "direction", "strength", "reason"]
        for field in required_fields:
            if field not in result:
                return False
        
        # Validate field types and ranges
        if not isinstance(result["signal"], str):
            return False
        
        if not isinstance(result["confidence"], (int, float)):
            return False
        
        if not (0 <= result["confidence"] <= 100):
            return False
        
        if not isinstance(result["direction"], str):
            return False
        
        if not isinstance(result["strength"], (int, float)):
            return False
        
        if not (0 <= result["strength"] <= 100):
            return False
        
        if not isinstance(result["reason"], str):
            return False
        
        return True
    
    def _record_failure(self, error: str):
        """Record a failure for tracking"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(f"{self.engine_name}: Failure recorded ({self.failure_count}/{self.config.max_failures}): {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            "engine_name": self.engine_name,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failure_count": self.failure_count,
            "success_rate": (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0,
            "last_execution_time": self.last_execution_time,
            "last_failure_time": self.last_failure_time
        }
    
    def reset_stats(self):
        """Reset execution statistics"""
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_execution_time = 0
        self.total_executions = 0
        self.successful_executions = 0
        logger.info(f"{self.engine_name}: Statistics reset")

# Global engine guards registry
_engine_guards = {}

def get_engine_guard(engine_name: str, safe_default: Dict[str, Any]) -> AIEngineGuard:
    """Get or create engine guard for an AI engine"""
    if engine_name not in _engine_guards:
        _engine_guards[engine_name] = AIEngineGuard(engine_name, safe_default)
    return _engine_guards[engine_name]

def safe_engine_execute(engine_name: str, safe_default: Dict[str, Any]):
    """
    Decorator for safe engine execution
    
    Usage:
    @safe_engine_execute("SmartMoneyEngine", safe_default)
    def analyze(self, live_metrics):
        # Engine logic here
        pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            guard = get_engine_guard(engine_name, safe_default)
            result = guard.safe_execute(func, self, *args, **kwargs)
            
            # Return just the result for backward compatibility
            return result.result
        
        return wrapper
    return decorator

# Predefined safe defaults for common engine types
SAFE_DEFAULTS = {
    "bias_engine": {
        "signal": "NEUTRAL",
        "confidence": 0.0,
        "direction": "NONE",
        "strength": 0.0,
        "reason": "invalid_metrics"
    },
    "liquidity_engine": {
        "signal": "NONE",
        "confidence": 0.0,
        "direction": "NONE",
        "strength": 0.0,
        "reason": "invalid_metrics"
    },
    "gamma_engine": {
        "signal": "GAMMA_NEUTRAL",
        "confidence": 0.0,
        "direction": "NONE",
        "strength": 0.0,
        "reason": "invalid_metrics"
    },
    "trap_engine": {
        "signal": "NONE",
        "confidence": 0.0,
        "direction": "NONE",
        "strength": 0.0,
        "reason": "invalid_metrics"
    },
    "vacuum_engine": {
        "signal": "NONE",
        "confidence": 0.0,
        "direction": "NONE",
        "strength": 0.0,
        "reason": "invalid_metrics"
    }
}

def get_all_engine_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all engine guards"""
    return {name: guard.get_stats() for name, guard in _engine_guards.items()}

def reset_all_engine_stats():
    """Reset statistics for all engine guards"""
    for guard in _engine_guards.values():
        guard.reset_stats()
