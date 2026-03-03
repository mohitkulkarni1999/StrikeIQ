"""
Global Logger for StrikeIQ Realtime Trading System
Structured logging with service prefixes and trace IDs
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

# Global trace context
class TraceContext:
    def __init__(self):
        self.trace_id: Optional[str] = None
    
    def start_trace(self) -> str:
        self.trace_id = str(uuid.uuid4())[:8].upper()
        return self.trace_id
    
    def get_trace_id(self) -> str:
        return self.trace_id or "NO_TRACE"
    
    def clear_trace(self):
        self.trace_id = None

# Global trace context
trace_context = TraceContext()

# Custom formatter with trace ID
class TraceFormatter(logging.Formatter):
    def format(self, record):
        # Safely get optional attributes
        service = getattr(record, "service", "APP")
        trace = getattr(record, "trace_prefix", "")
        
        # Add trace ID if available
        trace_id = trace_context.get_trace_id()
        if trace_id != "NO_TRACE":
            trace = f"[TRACE {trace_id}] "
        else:
            trace = ""
        
        # Format with service prefix
        return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{record.levelname}] [{service}] {trace}{record.getMessage()}"

# Configure logging
def setup_logger(service_name: str) -> logging.Logger:
    """Setup logger with service name and trace formatting"""
    logger = logging.getLogger(service_name)
    
    if not logger.handlers:
        # Create handler
        handler = logging.StreamHandler()
        handler.setFormatter(TraceFormatter())
        
        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate logs
        logger.propagate = False
    
    # Create adapter with service context
    return logging.LoggerAdapter(logger, {'service': service_name})

# Service-specific loggers
upstox_logger = setup_logger("UPSTOX")
protobuf_logger = setup_logger("PROTOBUF")
aggregator_logger = setup_logger("AGGREGATOR")
ws_logger = setup_logger("WS")
auth_logger = setup_logger("AUTH")
market_logger = setup_logger("MARKET")
api_logger = setup_logger("API")

# Helper functions for trace management
def start_trace() -> str:
    """Start a new trace and return trace ID"""
    return trace_context.start_trace()

def get_trace_id() -> str:
    """Get current trace ID"""
    return trace_context.get_trace_id()

def clear_trace():
    """Clear current trace"""
    trace_context.clear_trace()

# Decorator for automatic trace management
def with_trace(func):
    """Decorator to automatically manage trace for a function"""
    def wrapper(*args, **kwargs):
        trace_id = start_trace()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            clear_trace()
    return wrapper

# Export all loggers and utilities
__all__ = [
    'upstox_logger',
    'protobuf_logger', 
    'aggregator_logger',
    'ws_logger',
    'auth_logger',
    'market_logger',
    'api_logger',
    'start_trace',
    'get_trace_id',
    'clear_trace',
    'with_trace'
]
