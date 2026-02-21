"""
Pipeline Instrumentation
Non-intrusive wrappers for tick processing pipeline stages
"""

import time
import asyncio
import functools
import logging
from typing import Any, Callable, Optional, Dict, Union
from .tick_latency_tracker import get_latency_tracker

logger = logging.getLogger(__name__)

class TickInstrumentation:
    """
    Non-intrusive instrumentation wrapper for tick processing stages
    Provides latency tracking without modifying business logic
    """
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.tracker = get_latency_tracker()
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for instrumenting functions"""
        if asyncio.iscoroutinefunction(func):
            return self._wrap_async(func)
        else:
            return self._wrap_sync(func)
    
    def _wrap_sync(self, func: Callable) -> Callable:
        """Wrap synchronous function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract tick_id from kwargs or create new one
            tick_id = kwargs.get('tick_id') or self._extract_tick_id_from_args(args)
            
            if tick_id and self.tracker.should_track_tick():
                # Record start timestamp
                self._record_start(tick_id)
                
                try:
                    result = func(*args, **kwargs)
                    # Record completion timestamp
                    self._record_completion(tick_id)
                    return result
                except Exception as e:
                    # Record error (still track timing)
                    self._record_completion(tick_id)
                    logger.error(f"Error in {self.stage_name}: {e}")
                    raise
            else:
                return func(*args, **kwargs)
        
        return wrapper
    
    def _wrap_async(self, func: Callable) -> Callable:
        """Wrap asynchronous function"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract tick_id from kwargs or create new one
            tick_id = kwargs.get('tick_id') or self._extract_tick_id_from_args(args)
            
            if tick_id and self.tracker.should_track_tick():
                # Record start timestamp
                self._record_start(tick_id)
                
                try:
                    result = await func(*args, **kwargs)
                    # Record completion timestamp
                    self._record_completion(tick_id)
                    return result
                except Exception as e:
                    # Record error (still track timing)
                    self._record_completion(tick_id)
                    logger.error(f"Error in {self.stage_name}: {e}")
                    raise
            else:
                return await func(*args, **kwargs)
        
        return wrapper
    
    def _extract_tick_id_from_args(self, args: tuple) -> Optional[str]:
        """Extract tick_id from function arguments"""
        # Common patterns for tick_id extraction
        for arg in args:
            if isinstance(arg, str) and arg.startswith('tick_'):
                return arg
            elif hasattr(arg, 'tick_id'):
                return arg.tick_id
            elif hasattr(arg, 'message_id'):
                return f"tick_{arg.message_id}"
        return None
    
    def _record_start(self, tick_id: str) -> None:
        """Record stage start timestamp"""
        timestamp_method = getattr(self.tracker, f'record_{self.stage_name}_started', None)
        if timestamp_method:
            timestamp_method(tick_id)
    
    def _record_completion(self, tick_id: str) -> None:
        """Record stage completion timestamp"""
        timestamp_method = getattr(self.tracker, f'record_{self.stage_name}_completed', None)
        if timestamp_method:
            timestamp_method(tick_id)

class TickMetadataWrapper:
    """
    Wrapper for adding tick metadata to objects
    Non-intrusive way to track tick IDs through pipeline
    """
    
    def __init__(self, obj: Any, tick_id: str):
        self.obj = obj
        self.tick_id = tick_id
        self.created_at = time.perf_counter_ns()
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped object"""
        attr = getattr(self.obj, name)
        if callable(attr):
            # Wrap methods to pass tick_id
            @functools.wraps(attr)
            def wrapper(*args, **kwargs):
                kwargs['tick_id'] = self.tick_id
                return attr(*args, **kwargs)
            return wrapper
        return attr
    
    def __repr__(self) -> str:
        return f"TickMetadataWrapper({self.obj}, tick_id={self.tick_id})"
    
    def unwrap(self) -> Any:
        """Get the original object"""
        return self.obj

class QueueInstrumentation:
    """
    Instrumentation for queue operations
    Tracks queue wait times without affecting performance
    """
    
    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        self.tracker = get_latency_tracker()
    
    async def put_with_tracking(self, queue: asyncio.Queue, item: Any, tick_id: Optional[str] = None) -> None:
        """Put item in queue with timestamp tracking"""
        if tick_id and self.tracker.should_track_tick():
            # Record queue entry time
            if self.queue_name == 'raw':
                self.tracker.record_queue_entered(tick_id)
            elif self.queue_name == 'decoded':
                self.tracker.record_strategy_started(tick_id)
            elif self.queue_name == 'signals':
                self.tracker.record_broadcast_started(tick_id)
        
        await queue.put(item)
    
    async def get_with_tracking(self, queue: asyncio.Queue) -> Any:
        """Get item from queue with timestamp tracking"""
        item = await queue.get()
        
        # Extract tick_id and record start of processing
        tick_id = self._extract_tick_id(item)
        if tick_id and self.tracker.should_track_tick():
            if self.queue_name == 'raw':
                self.tracker.record_decode_started(tick_id)
            elif self.queue_name == 'decoded':
                self.tracker.record_signal_generated(tick_id)
            elif self.queue_name == 'signals':
                self.tracker.record_broadcast_completed(tick_id)
        
        return item
    
    def _extract_tick_id(self, item: Any) -> Optional[str]:
        """Extract tick_id from queue item"""
        if isinstance(item, dict):
            return item.get('tick_id') or item.get('message_id')
        elif hasattr(item, 'tick_id'):
            return item.tick_id
        elif hasattr(item, 'message_id'):
            return f"tick_{item.message_id}"
        return None

# Instrumentation decorators for each pipeline stage
websocket_receive = TickInstrumentation('websocket')
protobuf_decode = TickInstrumentation('decode')
dto_mapping = TickInstrumentation('dto_mapped')
strategy_execution = TickInstrumentation('strategy')
signal_generation = TickInstrumentation('signal_generated')
ui_broadcast = TickInstrumentation('broadcast')

# Queue instrumentation instances
raw_queue_instrumentation = QueueInstrumentation('raw')
decoded_queue_instrumentation = QueueInstrumentation('decoded')
signal_queue_instrumentation = QueueInstrumentation('signals')

class LatencyContextManager:
    """
    Context manager for measuring arbitrary code blocks
    Useful for ad-hoc latency measurements
    """
    
    def __init__(self, operation_name: str, tick_id: Optional[str] = None):
        self.operation_name = operation_name
        self.tick_id = tick_id
        self.tracker = get_latency_tracker()
        self.start_time: Optional[int] = None
    
    def __enter__(self):
        if self.tick_id and self.tracker.should_track_tick():
            self.start_time = time.perf_counter_ns()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.tick_id and self.start_time and self.tracker.should_track_tick():
            end_time = time.perf_counter_ns()
            duration_ns = end_time - self.start_time
            
            # Log custom operation timing
            logger.debug(
                f"Custom operation '{self.operation_name}' for tick {self.tick_id}: "
                f"{duration_ns / 1_000_000:.2f}ms"
            )

def measure_latency(operation_name: str):
    """
    Decorator for measuring arbitrary function latency
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tick_id = kwargs.get('tick_id')
            if tick_id and get_latency_tracker().should_track_tick():
                with LatencyContextManager(operation_name, tick_id):
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tick_id = kwargs.get('tick_id')
            if tick_id and get_latency_tracker().should_track_tick():
                with LatencyContextManager(operation_name, tick_id):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

class WebSocketInstrumentation:
    """
    Specialized instrumentation for WebSocket operations
    Tracks receive timestamps without affecting message processing
    """
    
    def __init__(self):
        self.tracker = get_latency_tracker()
    
    def instrument_websocket_message(self, message_data: bytes, message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Instrument WebSocket message with tracking metadata
        Returns wrapped message data
        """
        if not self.tracker.should_track_tick():
            return {'data': message_data}
        
        tick_id = message_id or self.tracker.create_tick_id()
        
        # Record WebSocket receive timestamp
        self.tracker.record_websocket_received(tick_id)
        
        # Wrap message with metadata
        return {
            'data': message_data,
            'tick_id': tick_id,
            'received_at': time.perf_counter_ns()
        }
    
    def extract_tick_id(self, message: Dict[str, Any]) -> Optional[str]:
        """Extract tick_id from instrumented message"""
        return message.get('tick_id')

# Global instrumentation instances
websocket_instrumentation = WebSocketInstrumentation()

# Utility functions for easy integration
def create_instrumented_tick(data: Any, tick_id: Optional[str] = None) -> TickMetadataWrapper:
    """Create an instrumented tick wrapper"""
    tracker = get_latency_tracker()
    if not tick_id:
        tick_id = tracker.create_tick_id()
    return TickMetadataWrapper(data, tick_id)

def extract_tick_from_instrumented(obj: Any) -> Any:
    """Extract original object from instrumented wrapper"""
    if isinstance(obj, TickMetadataWrapper):
        return obj.unwrap()
    return obj

def get_tick_id(obj: Any) -> Optional[str]:
    """Get tick_id from any object (instrumented or not)"""
    if isinstance(obj, TickMetadataWrapper):
        return obj.tick_id
    elif hasattr(obj, 'tick_id'):
        return obj.tick_id
    elif isinstance(obj, dict):
        return obj.get('tick_id') or obj.get('message_id')
    return None
