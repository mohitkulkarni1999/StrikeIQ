"""
Async Task Orchestrator
Coordinates all high-frequency ingestion components
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .high_frequency_ingestion import HighFrequencyIngestion, IngestionMetrics
from ..dto.market_tick_dto import MarketTickDTO

logger = logging.getLogger(__name__)

class WebSocketOrchestrator:
    """
    Orchestrates the complete high-frequency websocket ingestion pipeline
    Manages lifecycle and coordination of all components
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        # Configuration
        self.config = config or self._default_config()
        
        # Core ingestion engine
        self.ingestion_engine = HighFrequencyIngestion(
            raw_queue_size=self.config['raw_queue_size'],
            decoded_queue_size=self.config['decoded_queue_size'],
            signal_queue_size=self.config['signal_queue_size'],
            decode_workers=self.config['decode_workers'],
            strategy_workers=self.config['strategy_workers'],
            broadcast_workers=self.config['broadcast_workers']
        )
        
        # Orchestrator state
        self.is_initialized = False
        self.is_running = False
        self.startup_time: Optional[datetime] = None
        
        # Monitoring
        self.metrics_history: List[IngestionMetrics] = []
        self.health_check_interval = self.config['health_check_interval']
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # External connections
        self.websocket_url: Optional[str] = None
        
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for high-frequency ingestion"""
        return {
            # Queue sizes
            'raw_queue_size': 10000,
            'decoded_queue_size': 5000,
            'signal_queue_size': 2000,
            
            # Worker counts
            'decode_workers': 4,
            'strategy_workers': 2,
            'broadcast_workers': 2,
            
            # Timing
            'health_check_interval': 5.0,
            'metrics_history_size': 100,
            
            # Performance thresholds
            'max_queue_utilization': 0.8,
            'max_avg_decode_time_ms': 10.0,
            'max_avg_strategy_time_ms': 50.0,
            'max_avg_broadcast_time_ms': 5.0
        }
    
    async def initialize(self, websocket_url: str) -> bool:
        """
        Initialize the orchestrator and connect to websocket
        
        Args:
            websocket_url: Upstox V3 websocket URL
            
        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Initializing WebSocket Orchestrator")
            
            self.websocket_url = websocket_url
            
            # Start ingestion engine
            success = await self.ingestion_engine.start_ingestion(websocket_url)
            
            if success:
                self.is_initialized = True
                self.startup_time = datetime.now(timezone.utc)
                
                # Start monitoring
                await self._start_monitoring()
                
                logger.info("WebSocket Orchestrator initialized successfully")
                return True
            else:
                logger.error("Failed to start ingestion engine")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            return False
    
    async def shutdown(self):
        """Shutdown the orchestrator gracefully"""
        logger.info("Shutting down WebSocket Orchestrator")
        
        self.is_running = False
        
        # Stop monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Stop ingestion engine
        await self.ingestion_engine.stop_ingestion()
        
        self.is_initialized = False
        logger.info("WebSocket Orchestrator shutdown complete")
    
    async def _start_monitoring(self):
        """Start health monitoring and metrics collection"""
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started orchestrator monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Starting monitoring loop")
        
        while self.is_running:
            try:
                # Collect metrics
                metrics = self.ingestion_engine.get_metrics()
                
                # Store in history
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.config['metrics_history_size']:
                    self.metrics_history = self.metrics_history[-self.config['metrics_history_size']:]
                
                # Health check
                await self._perform_health_check(metrics)
                
                # Log metrics periodically
                if self.metrics_history[-1].ticks_received % 1000 == 0:
                    await self._log_metrics(metrics)
                
                # Wait for next check
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.health_check_interval)
        
        logger.info("Monitoring loop ended")
    
    async def _perform_health_check(self, metrics: IngestionMetrics):
        """Perform health check and take corrective actions"""
        issues = []
        
        # Check queue utilization
        if metrics.raw_queue_size / self.config['raw_queue_size'] > self.config['max_queue_utilization']:
            issues.append(f"Raw queue utilization high: {metrics.raw_queue_size}/{self.config['raw_queue_size']}")
        
        if metrics.decoded_queue_size / self.config['decoded_queue_size'] > self.config['max_queue_utilization']:
            issues.append(f"Decoded queue utilization high: {metrics.decoded_queue_size}/{self.config['decoded_queue_size']}")
        
        if metrics.signal_queue_size / self.config['signal_queue_size'] > self.config['max_queue_utilization']:
            issues.append(f"Signal queue utilization high: {metrics.signal_queue_size}/{self.config['signal_queue_size']}")
        
        # Check processing times
        if metrics.avg_decode_time_ms > self.config['max_avg_decode_time_ms']:
            issues.append(f"High decode time: {metrics.avg_decode_time_ms:.2f}ms")
        
        if metrics.avg_strategy_time_ms > self.config['max_avg_strategy_time_ms']:
            issues.append(f"High strategy time: {metrics.avg_strategy_time_ms:.2f}ms")
        
        if metrics.avg_broadcast_time_ms > self.config['max_avg_broadcast_time_ms']:
            issues.append(f"High broadcast time: {metrics.avg_broadcast_time_ms:.2f}ms")
        
        # Check error rates
        total_ticks = max(metrics.ticks_received, 1)
        decode_error_rate = metrics.decode_errors / total_ticks
        strategy_error_rate = metrics.strategy_errors / max(metrics.ticks_processed, 1)
        broadcast_error_rate = metrics.broadcast_errors / max(metrics.signals_broadcast, 1)
        
        if decode_error_rate > 0.01:  # 1% error rate
            issues.append(f"High decode error rate: {decode_error_rate:.2%}")
        
        if strategy_error_rate > 0.01:
            issues.append(f"High strategy error rate: {strategy_error_rate:.2%}")
        
        if broadcast_error_rate > 0.01:
            issues.append(f"High broadcast error rate: {broadcast_error_rate:.2%}")
        
        # Log issues
        if issues:
            logger.warning(f"Health check issues: {'; '.join(issues)}")
            
            # Trigger alerts if needed
            await self._trigger_health_alerts(issues)
    
    async def _trigger_health_alerts(self, issues: List[str]):
        """Trigger health alerts (can be extended with external alerting)"""
        alert_data = {
            'timestamp': datetime.now(timezone.utc),
            'issues': issues,
            'metrics': self.ingestion_engine.get_metrics(),
            'uptime': (datetime.now(timezone.utc) - self.startup_time).total_seconds() if self.startup_time else 0
        }
        
        # Log alert
        logger.warning(f"Health alert: {alert_data}")
        
        # Can be extended to send to external monitoring systems
        # await self.send_alert_to_monitoring_system(alert_data)
    
    async def _log_metrics(self, metrics: IngestionMetrics):
        """Log detailed metrics"""
        logger.info(
            f"Metrics - "
            f"Received: {metrics.ticks_received}, "
            f"Decoded: {metrics.ticks_decoded}, "
            f"Processed: {metrics.ticks_processed}, "
            f"Broadcast: {metrics.signals_broadcast}, "
            f"Queues: {metrics.raw_queue_size}/{metrics.decoded_queue_size}/{metrics.signal_queue_size}, "
            f"Times: {metrics.avg_decode_time_ms:.1f}/{metrics.avg_strategy_time_ms:.1f}/{metrics.avg_broadcast_time_ms:.1f}ms"
        )
    
    # Public API for strategy and broadcast management
    def register_strategy(self, strategy_name: str, handler):
        """Register a strategy with the ingestion engine"""
        self.ingestion_engine.register_strategy(strategy_name, handler)
    
    def unregister_strategy(self, strategy_name: str):
        """Unregister a strategy from the ingestion engine"""
        self.ingestion_engine.unregister_strategy(strategy_name)
    
    def register_broadcast_handler(self, handler):
        """Register a UI broadcast handler"""
        self.ingestion_engine.register_broadcast_handler(handler)
    
    def unregister_broadcast_handler(self, handler):
        """Unregister a UI broadcast handler"""
        self.ingestion_engine.unregister_broadcast_handler(handler)
    
    # Public API for monitoring and control
    def get_current_metrics(self) -> IngestionMetrics:
        """Get current ingestion metrics"""
        return self.ingestion_engine.get_metrics()
    
    def get_metrics_history(self) -> List[IngestionMetrics]:
        """Get historical metrics"""
        return self.metrics_history.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        current_metrics = self.get_current_metrics()
        
        return {
            'is_healthy': self.ingestion_engine.is_healthy(),
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'uptime_seconds': (
                (datetime.now(timezone.utc) - self.startup_time).total_seconds()
                if self.startup_time else 0
            ),
            'current_metrics': current_metrics,
            'config': self.config,
            'registered_strategies': list(self.ingestion_engine.strategy_handlers.keys()),
            'broadcast_handlers_count': len(self.ingestion_engine.broadcast_handlers)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for dashboard"""
        if not self.metrics_history:
            return {}
        
        # Calculate aggregates from history
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        avg_throughput = sum(m.ticks_processed for m in recent_metrics) / len(recent_metrics)
        avg_decode_time = sum(m.avg_decode_time_ms for m in recent_metrics) / len(recent_metrics)
        avg_strategy_time = sum(m.avg_strategy_time_ms for m in recent_metrics) / len(recent_metrics)
        
        return {
            'avg_ticks_per_second': avg_throughput,
            'avg_decode_time_ms': avg_decode_time,
            'avg_strategy_time_ms': avg_strategy_time,
            'total_ticks_received': self.metrics_history[-1].ticks_received if self.metrics_history else 0,
            'total_errors': (
                self.metrics_history[-1].decode_errors + 
                self.metrics_history[-1].strategy_errors + 
                self.metrics_history[-1].broadcast_errors
            ) if self.metrics_history else 0,
            'queue_utilization': {
                'raw': self.metrics_history[-1].raw_queue_size / self.config['raw_queue_size'],
                'decoded': self.metrics_history[-1].decoded_queue_size / self.config['decoded_queue_size'],
                'signal': self.metrics_history[-1].signal_queue_size / self.config['signal_queue_size']
            } if self.metrics_history else {}
        }


# Example usage and integration
async def example_orchestrator_usage():
    """Example of how to use the WebSocket Orchestrator"""
    
    # Create orchestrator with custom config
    config = {
        'raw_queue_size': 5000,
        'decoded_queue_size': 2500,
        'signal_queue_size': 1000,
        'decode_workers': 2,
        'strategy_workers': 1,
        'broadcast_workers': 1
    }
    
    orchestrator = WebSocketOrchestrator(config)
    
    # Register strategies
    async def momentum_strategy(tick_dto: MarketTickDTO):
        """Example momentum strategy"""
        if tick_dto.last_price > 0:
            return {'signal': 'buy', 'strength': 0.8, 'price': tick_dto.last_price}
        return None
    
    async def volume_strategy(tick_dto: MarketTickDTO):
        """Example volume strategy"""
        if tick_dto.volume > 1000:
            return {'signal': 'high_volume', 'volume': tick_dto.volume}
        return None
    
    orchestrator.register_strategy('momentum', momentum_strategy)
    orchestrator.register_strategy('volume', volume_strategy)
    
    # Register broadcast handler
    async def ui_broadcast_handler(signal_data):
        """Example UI broadcast handler"""
        signals = signal_data['signals']
        tick = signal_data['tick']
        
        # Send to WebSocket clients, Redis, etc.
        logger.info(f"Broadcasting {len(signals)} signals for {tick.instrument_key}")
    
    orchestrator.register_broadcast_handler(ui_broadcast_handler)
    
    try:
        # Initialize with websocket URL
        websocket_url = "wss://api.upstox.com/v3/feed/market-data-feed"
        success = await orchestrator.initialize(websocket_url)
        
        if success:
            logger.info("Orchestrator started successfully")
            
            # Monitor performance
            while True:
                await asyncio.sleep(10)
                health = orchestrator.get_health_status()
                performance = orchestrator.get_performance_summary()
                
                logger.info(f"Health: {health['is_healthy']}")
                logger.info(f"Performance: {performance}")
        else:
            logger.error("Failed to start orchestrator")
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(example_orchestrator_usage())
