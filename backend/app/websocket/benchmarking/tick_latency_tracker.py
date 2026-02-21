"""
Tick Latency Tracker
High-precision latency measurement for real-time tick processing pipeline
"""

import time
import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from datetime import datetime, timezone
import statistics
import json

logger = logging.getLogger(__name__)

class TickTimestamps(NamedTuple):
    """Immutable timestamps for tick processing stages"""
    websocket_received: int  # When WebSocket received the tick
    queue_entered: int      # When tick entered raw queue
    decode_started: int       # When protobuf decode started
    decode_completed: int     # When protobuf decode completed
    dto_mapped: int          # When DTO mapping completed
    strategy_started: int     # When strategy execution started
    strategy_completed: int   # When strategy execution completed
    signal_generated: int     # When signal generation completed
    broadcast_started: int    # When UI broadcast started
    broadcast_completed: int  # When UI broadcast completed

@dataclass
class TickLatencyMetrics:
    """Per-tick latency metrics"""
    tick_id: str
    timestamps: TickTimestamps
    
    # Computed latencies (in nanoseconds)
    websocket_to_queue: int = field(init=False)
    queue_wait_time: int = field(init=False)
    decode_duration: int = field(init=False)
    dto_mapping_duration: int = field(init=False)
    strategy_duration: int = field(init=False)
    signal_generation_duration: int = field(init=False)
    broadcast_duration: int = field(init=False)
    total_end_to_end: int = field(init=False)
    
    def __post_init__(self):
        """Compute latencies from timestamps"""
        ts = self.timestamps
        
        self.websocket_to_queue = ts.queue_entered - ts.websocket_received
        self.queue_wait_time = ts.decode_started - ts.queue_entered
        self.decode_duration = ts.decode_completed - ts.decode_started
        self.dto_mapping_duration = ts.dto_mapped - ts.decode_completed
        self.strategy_duration = ts.strategy_completed - ts.strategy_started
        self.signal_generation_duration = ts.signal_generated - ts.strategy_completed
        self.broadcast_duration = ts.broadcast_completed - ts.broadcast_started
        self.total_end_to_end = ts.broadcast_completed - ts.websocket_received
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'tick_id': self.tick_id,
            'latencies_ns': {
                'websocket_to_queue': self.websocket_to_queue,
                'queue_wait_time': self.queue_wait_time,
                'decode_duration': self.decode_duration,
                'dto_mapping_duration': self.dto_mapping_duration,
                'strategy_duration': self.strategy_duration,
                'signal_generation_duration': self.signal_generation_duration,
                'broadcast_duration': self.broadcast_duration,
                'total_end_to_end': self.total_end_to_end
            },
            'latencies_ms': {
                'websocket_to_queue': self.websocket_to_queue / 1_000_000,
                'queue_wait_time': self.queue_wait_time / 1_000_000,
                'decode_duration': self.decode_duration / 1_000_000,
                'dto_mapping_duration': self.dto_mapping_duration / 1_000_000,
                'strategy_duration': self.strategy_duration / 1_000_000,
                'signal_generation_duration': self.signal_generation_duration / 1_000_000,
                'broadcast_duration': self.broadcast_duration / 1_000_000,
                'total_end_to_end': self.total_end_to_end / 1_000_000
            }
        }

class TickLatencyTracker:
    """
    High-performance tick latency tracker
    Thread-safe, async-safe, minimal overhead
    """
    
    def __init__(self, 
                 sampling_rate: int = 1,  # Track 1 out of N ticks
                 max_samples: int = 10000,
                 latency_threshold_ms: float = 50.0):
        self.sampling_rate = sampling_rate
        self.max_samples = max_samples
        self.latency_threshold_ns = int(latency_threshold_ms * 1_000_000)
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._tick_counter = 0
        self._active_ticks: Dict[str, TickTimestamps] = {}
        self._completed_metrics: deque = deque(maxlen=max_samples)
        
        # Performance statistics
        self._stage_latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._queue_wait_times: deque = deque(maxlen=1000)
        
        # Background logging
        self._logger_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Warning tracking
        self._threshold_violations = 0
        self._last_warning_time = 0
    
    def start_tracking(self) -> None:
        """Start the latency tracking system"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._logger_task = asyncio.create_task(self._background_logger())
            logger.info("Tick latency tracker started")
    
    def stop_tracking(self) -> None:
        """Stop the latency tracking system"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            if self._logger_task:
                self._logger_task.cancel()
            
            logger.info("Tick latency tracker stopped")
    
    def should_track_tick(self) -> bool:
        """Check if this tick should be tracked based on sampling rate"""
        with self._lock:
            self._tick_counter += 1
            return (self._tick_counter % self.sampling_rate) == 0
    
    def create_tick_id(self) -> str:
        """Generate unique tick ID for tracking"""
        return f"tick_{self._tick_counter}_{int(time.time_ns() / 1_000_000)}"
    
    def record_websocket_received(self, tick_id: str) -> None:
        """Record WebSocket receive timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id not in self._active_ticks:
                self._active_ticks[tick_id] = TickTimestamps(
                    websocket_received=timestamp,
                    queue_entered=0,
                    decode_started=0,
                    decode_completed=0,
                    dto_mapped=0,
                    strategy_started=0,
                    strategy_completed=0,
                    signal_generated=0,
                    broadcast_started=0,
                    broadcast_completed=0
                )
    
    def record_queue_entered(self, tick_id: str) -> None:
        """Record queue entry timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                self._active_ticks[tick_id] = self._active_ticks[tick_id]._replace(
                    queue_entered=timestamp
                )
    
    def record_decode_started(self, tick_id: str) -> None:
        """Record decode start timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                self._active_ticks[tick_id] = self._active_ticks[tick_id]._replace(
                    decode_started=timestamp
                )
    
    def record_decode_completed(self, tick_id: str) -> None:
        """Record decode completion timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                self._active_ticks[tick_id] = self._active_ticks[tick_id]._replace(
                    decode_completed=timestamp
                )
    
    def record_dto_mapped(self, tick_id: str) -> None:
        """Record DTO mapping completion timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                self._active_ticks[tick_id] = self._active_ticks[tick_id]._replace(
                    dto_mapped=timestamp
                )
    
    def record_strategy_started(self, tick_id: str) -> None:
        """Record strategy execution start timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                self._active_ticks[tick_id] = self._active_ticks[tick_id]._replace(
                    strategy_started=timestamp
                )
    
    def record_strategy_completed(self, tick_id: str) -> None:
        """Record strategy execution completion timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                self._active_ticks[tick_id] = self._active_ticks[tick_id]._replace(
                    strategy_completed=timestamp
                )
    
    def record_signal_generated(self, tick_id: str) -> None:
        """Record signal generation completion timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                self._active_ticks[tick_id] = self._active_ticks[tick_id]._replace(
                    signal_generated=timestamp
                )
    
    def record_broadcast_started(self, tick_id: str) -> None:
        """Record UI broadcast start timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                self._active_ticks[tick_id] = self._active_ticks[tick_id]._replace(
                    broadcast_started=timestamp
                )
    
    def record_broadcast_completed(self, tick_id: str) -> None:
        """Record UI broadcast completion timestamp"""
        if not self._should_track(tick_id):
            return
        
        timestamp = time.perf_counter_ns()
        with self._lock:
            if tick_id in self._active_ticks:
                completed_ts = self._active_ticks[tick_id]._replace(
                    broadcast_completed=timestamp
                )
                
                # Create metrics and store
                metrics = TickLatencyMetrics(tick_id, completed_ts)
                self._completed_metrics.append(metrics)
                
                # Update stage latencies
                self._stage_latencies['decode'].append(metrics.decode_duration)
                self._stage_latencies['strategy'].append(metrics.strategy_duration)
                self._stage_latencies['broadcast'].append(metrics.broadcast_duration)
                self._queue_wait_times.append(metrics.queue_wait_time)
                
                # Check threshold violation
                if metrics.total_end_to_end > self.latency_threshold_ns:
                    self._handle_threshold_violation(metrics)
                
                # Clean up active tick
                del self._active_ticks[tick_id]
    
    def _should_track(self, tick_id: str) -> bool:
        """Check if tick should be tracked"""
        if not self._running:
            return False
        
        with self._lock:
            return tick_id in self._active_ticks
    
    def _handle_threshold_violation(self, metrics: TickLatencyMetrics) -> None:
        """Handle latency threshold violations"""
        self._threshold_violations += 1
        current_time = time.time()
        
        # Rate limit warnings to avoid log spam
        if current_time - self._last_warning_time > 10:  # Max one warning per 10 seconds
            self._last_warning_time = current_time
            
            logger.warning(
                f"🚨 HIGH LATENCY DETECTED - "
                f"Tick {metrics.tick_id}: {metrics.total_end_to_end / 1_000_000:.2f}ms "
                f"(threshold: {self.latency_threshold_ns / 1_000_000:.1f}ms) - "
                f"Decode: {metrics.decode_duration / 1_000_000:.2f}ms, "
                f"Strategy: {metrics.strategy_duration / 1_000_000:.2f}ms, "
                f"Queue wait: {metrics.queue_wait_time / 1_000_000:.2f}ms"
            )
    
    async def _background_logger(self) -> None:
        """Background task for periodic logging"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Log every 30 seconds
                self._log_periodic_stats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background logger: {e}")
    
    def _log_periodic_stats(self) -> None:
        """Log periodic performance statistics"""
        with self._lock:
            if not self._completed_metrics:
                return
            
            # Calculate percentiles
            total_times = [m.total_end_to_end for m in self._completed_metrics]
            if len(total_times) < 10:
                return
            
            p50 = statistics.quantiles(total_times, n=2)[0] / 1_000_000
            p90 = statistics.quantiles(total_times, n=10)[8] / 1_000_000
            p99 = statistics.quantiles(total_times, n=100)[98] / 1_000_000
            
            # Calculate averages
            avg_decode = statistics.mean(self._stage_latencies['decode']) / 1_000_000 if self._stage_latencies['decode'] else 0
            avg_strategy = statistics.mean(self._stage_latencies['strategy']) / 1_000_000 if self._stage_latencies['strategy'] else 0
            avg_queue_wait = statistics.mean(self._queue_wait_times) / 1_000_000 if self._queue_wait_times else 0
            
            logger.info(
                f"📊 LATENCY STATS (last {len(self._completed_metrics)} samples) - "
                f"P50: {p50:.2f}ms, P90: {p90:.2f}ms, P99: {p99:.2f}ms | "
                f"Avg Decode: {avg_decode:.2f}ms, Avg Strategy: {avg_strategy:.2f}ms, "
                f"Avg Queue Wait: {avg_queue_wait:.2f}ms | "
                f"Threshold violations: {self._threshold_violations}"
            )
    
    def get_percentile_report(self) -> Dict[str, Any]:
        """Get comprehensive percentile report"""
        with self._lock:
            if not self._completed_metrics:
                return {'error': 'No data available'}
            
            # Extract all latency types
            metrics_data = {
                'total_end_to_end': [m.total_end_to_end for m in self._completed_metrics],
                'decode_duration': [m.decode_duration for m in self._completed_metrics],
                'strategy_duration': [m.strategy_duration for m in self._completed_metrics],
                'broadcast_duration': [m.broadcast_duration for m in self._completed_metrics],
                'queue_wait_time': [m.queue_wait_time for m in self._completed_metrics]
            }
            
            report = {
                'sample_count': len(self._completed_metrics),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'percentiles_ms': {},
                'statistics_ms': {}
            }
            
            # Calculate percentiles for each metric
            for metric_name, values in metrics_data.items():
                if not values:
                    continue
                
                sorted_values = sorted(values)
                n = len(sorted_values)
                
                if n < 4:
                    continue
                
                # Calculate percentiles
                p50 = sorted_values[n // 2] / 1_000_000
                p90 = sorted_values[int(n * 0.9)] / 1_000_000
                p95 = sorted_values[int(n * 0.95)] / 1_000_000
                p99 = sorted_values[int(n * 0.99)] / 1_000_000
                
                report['percentiles_ms'][metric_name] = {
                    'p50': p50,
                    'p90': p90,
                    'p95': p95,
                    'p99': p99
                }
                
                # Calculate statistics
                mean_val = statistics.mean(sorted_values) / 1_000_000
                median_val = statistics.median(sorted_values) / 1_000_000
                min_val = min(sorted_values) / 1_000_000
                max_val = max(sorted_values) / 1_000_000
                std_val = statistics.stdev(sorted_values) / 1_000_000 if n > 1 else 0
                
                report['statistics_ms'][metric_name] = {
                    'mean': mean_val,
                    'median': median_val,
                    'min': min_val,
                    'max': max_val,
                    'std': std_val
                }
            
            # Add queue wait time distribution
            if self._queue_wait_times:
                queue_times_ms = [t / 1_000_000 for t in self._queue_wait_times]
                report['queue_wait_distribution'] = {
                    'mean_ms': statistics.mean(queue_times_ms),
                    'median_ms': statistics.median(queue_times_ms),
                    'p95_ms': sorted(queue_times_ms)[int(len(queue_times_ms) * 0.95)],
                    'max_ms': max(queue_times_ms),
                    'samples': len(queue_times_ms)
                }
            
            # Add threshold violations
            report['threshold_violations'] = self._threshold_violations
            report['violation_rate'] = (self._threshold_violations / len(self._completed_metrics)) * 100
            
            return report
    
    def get_decode_vs_strategy_comparison(self) -> Dict[str, Any]:
        """Compare decode vs strategy execution performance"""
        with self._lock:
            if not self._completed_metrics:
                return {'error': 'No data available'}
            
            decode_times = [m.decode_duration / 1_000_000 for m in self._completed_metrics]
            strategy_times = [m.strategy_duration / 1_000_000 for m in self._completed_metrics]
            
            if not decode_times or not strategy_times:
                return {'error': 'Insufficient data'}
            
            return {
                'sample_count': len(self._completed_metrics),
                'decode_performance': {
                    'mean_ms': statistics.mean(decode_times),
                    'median_ms': statistics.median(decode_times),
                    'p95_ms': sorted(decode_times)[int(len(decode_times) * 0.95)],
                    'max_ms': max(decode_times),
                    'std_ms': statistics.stdev(decode_times) if len(decode_times) > 1 else 0
                },
                'strategy_performance': {
                    'mean_ms': statistics.mean(strategy_times),
                    'median_ms': statistics.median(strategy_times),
                    'p95_ms': sorted(strategy_times)[int(len(strategy_times) * 0.95)],
                    'max_ms': max(strategy_times),
                    'std_ms': statistics.stdev(strategy_times) if len(strategy_times) > 1 else 0
                },
                'comparison': {
                    'decode_to_strategy_ratio': statistics.mean(decode_times) / statistics.mean(strategy_times) if statistics.mean(strategy_times) > 0 else float('inf'),
                    'faster_stage': 'decode' if statistics.mean(decode_times) < statistics.mean(strategy_times) else 'strategy',
                    'performance_gap_ms': abs(statistics.mean(decode_times) - statistics.mean(strategy_times))
                }
            }
    
    def export_metrics(self, filename: Optional[str] = None) -> str:
        """Export metrics to JSON file"""
        report = {
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'percentile_report': self.get_percentile_report(),
            'decode_vs_strategy': self.get_decode_vs_strategy_comparison(),
            'configuration': {
                'sampling_rate': self.sampling_rate,
                'max_samples': self.max_samples,
                'latency_threshold_ms': self.latency_threshold_ns / 1_000_000
            }
        }
        
        json_str = json.dumps(report, indent=2, default=str)
        
        if filename:
            with open(filename, 'w') as f:
                f.write(json_str)
            logger.info(f"Latency metrics exported to {filename}")
        
        return json_str

# Global tracker instance
_global_tracker: Optional[TickLatencyTracker] = None

def get_latency_tracker() -> TickLatencyTracker:
    """Get global latency tracker instance"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TickLatencyTracker()
    return _global_tracker

def initialize_latency_tracking(sampling_rate: int = 1, latency_threshold_ms: float = 50.0) -> None:
    """Initialize global latency tracker"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TickLatencyTracker(
            sampling_rate=sampling_rate,
            latency_threshold_ms=latency_threshold_ms
        )
        _global_tracker.start_tracking()
        logger.info(f"Latency tracking initialized (sampling: 1/{sampling_rate}, threshold: {latency_threshold_ms}ms)")

def shutdown_latency_tracking() -> None:
    """Shutdown global latency tracker"""
    global _global_tracker
    if _global_tracker:
        _global_tracker.stop_tracking()
        _global_tracker = None
