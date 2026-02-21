"""
Async-Safe Latency Logger
High-performance logging for tick processing latencies
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timezone
import json
import aiofiles
import os

logger = logging.getLogger(__name__)

@dataclass
class LatencyLogEntry:
    """Single latency log entry"""
    timestamp: datetime
    tick_id: str
    stage: str
    duration_ns: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'tick_id': self.tick_id,
            'stage': self.stage,
            'duration_ns': self.duration_ns,
            'duration_ms': self.duration_ns / 1_000_000,
            'metadata': self.metadata
        }

class AsyncLatencyLogger:
    """
    Async-safe, high-performance latency logger
    Non-blocking logging with configurable outputs
    """
    
    def __init__(self, 
                 log_file: Optional[str] = None,
                 max_memory_entries: int = 10000,
                 flush_interval: float = 5.0,
                 enable_console_logging: bool = True):
        self.log_file = log_file
        self.max_memory_entries = max_memory_entries
        self.flush_interval = flush_interval
        self.enable_console_logging = enable_console_logging
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._log_buffer: deque = deque(maxlen=max_memory_entries)
        self._file_buffer: List[LatencyLogEntry] = []
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._total_logged = 0
        self._last_flush_time = 0
        
        # Ensure log directory exists
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    async def start(self) -> None:
        """Start the async logger"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._flush_task = asyncio.create_task(self._periodic_flush())
            logger.info("Async latency logger started")
    
    async def stop(self) -> None:
        """Stop the async logger"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            if self._flush_task:
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass
            
            # Final flush
            await self._flush_to_file()
            logger.info("Async latency logger stopped")
    
    def log_latency(self, 
                   tick_id: str, 
                   stage: str, 
                   duration_ns: int, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log latency measurement (thread-safe, non-blocking)
        
        Args:
            tick_id: Unique tick identifier
            stage: Processing stage name
            duration_ns: Duration in nanoseconds
            metadata: Additional metadata
        """
        if not self._running:
            return
        
        entry = LatencyLogEntry(
            timestamp=datetime.now(timezone.utc),
            tick_id=tick_id,
            stage=stage,
            duration_ns=duration_ns,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._log_buffer.append(entry)
            self._file_buffer.append(entry)
            self._total_logged += 1
            
            # Console logging (rate limited)
            if self.enable_console_logging and duration_ns > 10_000_000:  # > 10ms
                logger.debug(
                    f"Latency: {stage} for {tick_id}: {duration_ns / 1_000_000:.2f}ms"
                )
    
    def log_stage_transition(self, 
                           tick_id: str, 
                           from_stage: str, 
                           to_stage: str, 
                           transition_time_ns: int) -> None:
        """
        Log stage transition time
        
        Args:
            tick_id: Unique tick identifier
            from_stage: Source stage
            to_stage: Destination stage
            transition_time_ns: Transition duration in nanoseconds
        """
        self.log_latency(
            tick_id=tick_id,
            stage=f"{from_stage}_to_{to_stage}",
            duration_ns=transition_time_ns,
            metadata={
                'from_stage': from_stage,
                'to_stage': to_stage,
                'type': 'stage_transition'
            }
        )
    
    def log_queue_wait_time(self, 
                           tick_id: str, 
                           queue_name: str, 
                           wait_time_ns: int) -> None:
        """
        Log queue wait time
        
        Args:
            tick_id: Unique tick identifier
            queue_name: Queue identifier
            wait_time_ns: Wait time in nanoseconds
        """
        self.log_latency(
            tick_id=tick_id,
            stage=f"{queue_name}_queue_wait",
            duration_ns=wait_time_ns,
            metadata={
                'queue_name': queue_name,
                'type': 'queue_wait'
            }
        )
    
    def log_error(self, 
                  tick_id: str, 
                  stage: str, 
                  error: Exception, 
                  duration_ns: Optional[int] = None) -> None:
        """
        Log processing error
        
        Args:
            tick_id: Unique tick identifier
            stage: Processing stage where error occurred
            error: Exception object
            duration_ns: Optional duration before error
        """
        self.log_latency(
            tick_id=tick_id,
            stage=f"{stage}_error",
            duration_ns=duration_ns or 0,
            metadata={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'type': 'error'
            }
        )
    
    def get_recent_entries(self, count: int = 100) -> List[LatencyLogEntry]:
        """Get recent log entries"""
        with self._lock:
            return list(self._log_buffer)[-count:]
    
    def get_stage_statistics(self, stage: str, limit: int = 1000) -> Dict[str, Any]:
        """Get statistics for a specific stage"""
        with self._lock:
            stage_entries = [
                entry for entry in self._log_buffer 
                if entry.stage == stage
            ][-limit:]
            
            if not stage_entries:
                return {'error': f'No entries for stage: {stage}'}
            
            durations_ms = [entry.duration_ns / 1_000_000 for entry in stage_entries]
            
            return {
                'stage': stage,
                'sample_count': len(durations_ms),
                'duration_ms': {
                    'mean': sum(durations_ms) / len(durations_ms),
                    'min': min(durations_ms),
                    'max': max(durations_ms),
                    'p50': sorted(durations_ms)[len(durations_ms) // 2],
                    'p95': sorted(durations_ms)[int(len(durations_ms) * 0.95)],
                    'p99': sorted(durations_ms)[int(len(durations_ms) * 0.99)]
                },
                'time_range': {
                    'start': min(entry.timestamp for entry in stage_entries).isoformat(),
                    'end': max(entry.timestamp for entry in stage_entries).isoformat()
                }
            }
    
    async def _periodic_flush(self) -> None:
        """Periodic flush task"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_to_file()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
    
    async def _flush_to_file(self) -> None:
        """Flush buffered entries to file"""
        if not self.log_file or not self._file_buffer:
            return
        
        with self._lock:
            if not self._file_buffer:
                return
            
            entries_to_flush = self._file_buffer.copy()
            self._file_buffer.clear()
            self._last_flush_time = time.time()
        
        try:
            # Write to file asynchronously
            async with aiofiles.open(self.log_file, 'a') as f:
                for entry in entries_to_flush:
                    log_line = json.dumps(entry.to_dict())
                    await f.write(log_line + '\n')
            
            logger.debug(f"Flushed {len(entries_to_flush)} latency entries to {self.log_file}")
            
        except Exception as e:
            logger.error(f"Failed to flush latency log: {e}")
            # Re-add entries to buffer on failure
            with self._lock:
                self._file_buffer.extend(entries_to_flush)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall logger statistics"""
        with self._lock:
            return {
                'total_logged': self._total_logged,
                'buffer_size': len(self._log_buffer),
                'file_buffer_size': len(self._file_buffer),
                'last_flush_time': self._last_flush_time,
                'running': self._running,
                'log_file': self.log_file,
                'max_memory_entries': self.max_memory_entries
            }
    
    def export_recent_logs(self, filename: str, count: int = 1000) -> None:
        """Export recent logs to file"""
        recent_entries = self.get_recent_entries(count)
        
        export_data = {
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'entry_count': len(recent_entries),
            'entries': [entry.to_dict() for entry in recent_entries]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Exported {len(recent_entries)} log entries to {filename}")

class PerformanceAlertManager:
    """
    Alert manager for performance issues
    Non-blocking alerts with rate limiting
    """
    
    def __init__(self, 
                 latency_threshold_ms: float = 50.0,
                 alert_cooldown: float = 30.0):
        self.latency_threshold_ns = int(latency_threshold_ms * 1_000_000)
        self.alert_cooldown = alert_cooldown
        self._last_alert_time = 0
        self._alert_count = 0
        self._running = False
    
    async def start(self) -> None:
        """Start alert manager"""
        self._running = True
    
    async def stop(self) -> None:
        """Stop alert manager"""
        self._running = False
    
    def check_latency_alert(self, 
                         tick_id: str, 
                         stage: str, 
                         duration_ns: int) -> bool:
        """
        Check if latency alert should be triggered
        
        Returns:
            True if alert was triggered
        """
        if not self._running or duration_ns <= self.latency_threshold_ns:
            return False
        
        current_time = time.time()
        
        # Rate limit alerts
        if current_time - self._last_alert_time < self.alert_cooldown:
            return False
        
        self._last_alert_time = current_time
        self._alert_count += 1
        
        # Trigger alert (non-blocking)
        asyncio.create_task(self._send_alert(tick_id, stage, duration_ns))
        
        return True
    
    async def _send_alert(self, tick_id: str, stage: str, duration_ns: int) -> None:
        """Send performance alert"""
        duration_ms = duration_ns / 1_000_000
        threshold_ms = self.latency_threshold_ns / 1_000_000
        
        logger.warning(
            f"🚨 PERFORMANCE ALERT - "
            f"Stage: {stage}, Tick: {tick_id}, "
            f"Latency: {duration_ms:.2f}ms (threshold: {threshold_ms:.1f}ms), "
            f"Alert #{self._alert_count}"
        )
        
        # Could integrate with external alerting systems here
        # await send_to_slack(f"High latency detected: {stage} - {duration_ms:.2f}ms")
        # await send_to_pagerduty(f"Performance degradation in {stage}")

# Global instances
_global_logger: Optional[AsyncLatencyLogger] = None
_global_alert_manager: Optional[PerformanceAlertManager] = None

def get_latency_logger() -> AsyncLatencyLogger:
    """Get global latency logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AsyncLatencyLogger(
            log_file="logs/tick_latency.jsonl",
            enable_console_logging=True
        )
    return _global_logger

def get_alert_manager() -> PerformanceAlertManager:
    """Get global alert manager instance"""
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = PerformanceAlertManager()
    return _global_alert_manager

async def initialize_latency_logging(log_file: Optional[str] = None) -> None:
    """Initialize global latency logging system"""
    global _global_logger, _global_alert_manager
    
    if _global_logger is None:
        _global_logger = AsyncLatencyLogger(log_file=log_file)
        await _global_logger.start()
    
    if _global_alert_manager is None:
        _global_alert_manager = PerformanceAlertManager()
        await _global_alert_manager.start()
    
    logger.info("Latency logging system initialized")

async def shutdown_latency_logging() -> None:
    """Shutdown global latency logging system"""
    global _global_logger, _global_alert_manager
    
    if _global_logger:
        await _global_logger.stop()
        _global_logger = None
    
    if _global_alert_manager:
        await _global_alert_manager.stop()
        _global_alert_manager = None
    
    logger.info("Latency logging system shutdown")
