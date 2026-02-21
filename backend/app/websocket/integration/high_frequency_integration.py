"""
High-Frequency Integration Example
Complete setup for production-ready high-frequency tick ingestion
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from ..architecture.orchestrator import WebSocketOrchestrator
from ..dto.market_tick_dto import MarketTickDTO

logger = logging.getLogger(__name__)

class HighFrequencyIntegration:
    """
    Production-ready high-frequency integration
    Demonstrates complete separation of concerns
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.orchestrator = WebSocketOrchestrator(config)
        self.is_running = False
        
    async def start(self, websocket_url: str) -> bool:
        """
        Start high-frequency integration
        
        Args:
            websocket_url: Authorized Upstox V3 websocket URL
            
        Returns:
            bool: True if started successfully
        """
        try:
            # Register built-in strategies
            await self._register_strategies()
            
            # Register broadcast handlers
            await self._register_broadcast_handlers()
            
            # Initialize orchestrator
            success = await self.orchestrator.initialize(websocket_url)
            
            if success:
                self.is_running = True
                logger.info("High-frequency integration started successfully")
                return True
            else:
                logger.error("Failed to start high-frequency integration")
                return False
                
        except Exception as e:
            logger.error(f"Error starting integration: {str(e)}")
            return False
    
    async def stop(self):
        """Stop high-frequency integration"""
        await self.orchestrator.shutdown()
        self.is_running = False
        logger.info("High-frequency integration stopped")
    
    async def _register_strategies(self):
        """Register built-in trading strategies"""
        
        # Momentum strategy
        async def momentum_strategy(tick_dto: MarketTickDTO):
            """Detect momentum based on price changes"""
            if tick_dto.last_price > 0:
                # Simple momentum logic
                if tick_dto.change_percent and abs(tick_dto.change_percent) > 0.5:
                    direction = 'bullish' if tick_dto.change_percent > 0 else 'bearish'
                    return {
                        'type': 'momentum',
                        'direction': direction,
                        'strength': min(abs(tick_dto.change_percent) / 2.0, 1.0),
                        'price': tick_dto.last_price,
                        'volume': tick_dto.volume
                    }
            return None
        
        # Volume spike strategy
        async def volume_spike_strategy(tick_dto: MarketTickDTO):
            """Detect unusual volume spikes"""
            if tick_dto.volume > 0:
                # Volume spike detection (would need historical comparison in production)
                avg_volume = 1000  # Placeholder
                if tick_dto.volume > avg_volume * 2:
                    return {
                        'type': 'volume_spike',
                        'volume': tick_dto.volume,
                        'avg_volume': avg_volume,
                        'spike_ratio': tick_dto.volume / avg_volume,
                        'price': tick_dto.last_price
                    }
            return None
        
        # Options flow strategy
        async def options_flow_strategy(tick_dto: MarketTickDTO):
            """Detect options flow activity"""
            if tick_dto.is_option_tick():
                # Large OI changes or unusual Greeks
                if abs(tick_dto.oi_change) > 100:
                    return {
                        'type': 'options_flow',
                        'instrument': tick_dto.instrument_key,
                        'oi_change': tick_dto.oi_change,
                        'delta': tick_dto.delta,
                        'theta': tick_dto.theta,
                        'price': tick_dto.last_price,
                        'volume': tick_dto.volume
                    }
            return None
        
        # Register strategies
        self.orchestrator.register_strategy('momentum', momentum_strategy)
        self.orchestrator.register_strategy('volume_spike', volume_spike_strategy)
        self.orchestrator.register_strategy('options_flow', options_flow_strategy)
        
        logger.info("Registered built-in strategies: momentum, volume_spike, options_flow")
    
    async def _register_broadcast_handlers(self):
        """Register UI broadcast handlers"""
        
        # WebSocket broadcast handler
        async def websocket_broadcast_handler(signal_data):
            """Broadcast signals to WebSocket clients"""
            try:
                signals = signal_data['signals']
                tick = signal_data['tick']
                
                # Prepare broadcast message
                broadcast_message = {
                    'type': 'market_signals',
                    'timestamp': signal_data['generated_at'].isoformat(),
                    'tick': tick.to_dict(),
                    'signals': signals
                }
                
                # This would connect to your WebSocket server
                # await websocket_manager.broadcast_to_clients(broadcast_message)
                
                logger.info(f"Broadcasting {len(signals)} signals for {tick.instrument_key}")
                
            except Exception as e:
                logger.error(f"Error in WebSocket broadcast: {str(e)}")
        
        # Redis broadcast handler
        async def redis_broadcast_handler(signal_data):
            """Broadcast signals to Redis channels"""
            try:
                signals = signal_data['signals']
                tick = signal_data['tick']
                
                # Prepare Redis message
                redis_message = {
                    'channel': f'market_signals:{tick.instrument_key}',
                    'data': {
                        'timestamp': signal_data['generated_at'].isoformat(),
                        'tick': tick.to_dict(),
                        'signals': signals
                    }
                }
                
                # This would publish to Redis
                # await redis_publisher.publish(redis_message['channel'], json.dumps(redis_message['data']))
                
                logger.debug(f"Published to Redis: {redis_message['channel']}")
                
            except Exception as e:
                logger.error(f"Error in Redis broadcast: {str(e)}")
        
        # Analytics broadcast handler
        async def analytics_broadcast_handler(signal_data):
            """Send signals to analytics system"""
            try:
                signals = signal_data['signals']
                tick = signal_data['tick']
                
                # Prepare analytics data
                analytics_data = {
                    'event_type': 'market_signals',
                    'timestamp': signal_data['generated_at'].isoformat(),
                    'instrument': tick.instrument_key,
                    'price': tick.last_price,
                    'volume': tick.volume,
                    'signal_count': len(signals),
                    'signal_types': [s['signal']['type'] for s in signals if 'type' in s.get('signal', {})]
                }
                
                # This would send to analytics system
                # await analytics_client.track_event(analytics_data)
                
                logger.debug(f"Sent to analytics: {analytics_data}")
                
            except Exception as e:
                logger.error(f"Error in analytics broadcast: {str(e)}")
        
        # Register broadcast handlers
        self.orchestrator.register_broadcast_handler(websocket_broadcast_handler)
        self.orchestrator.register_broadcast_handler(redis_broadcast_handler)
        self.orchestrator.register_broadcast_handler(analytics_broadcast_handler)
        
        logger.info("Registered broadcast handlers: websocket, redis, analytics")
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            'is_running': self.is_running,
            'health': self.orchestrator.get_health_status(),
            'performance': self.orchestrator.get_performance_summary()
        }


# Production setup example
async def setup_high_frequency_system():
    """
    Example production setup for high-frequency system
    """
    
    # Production configuration
    prod_config = {
        # Larger queues for high-frequency trading
        'raw_queue_size': 20000,
        'decoded_queue_size': 10000,
        'signal_queue_size': 5000,
        
        # More workers for higher throughput
        'decode_workers': 8,
        'strategy_workers': 4,
        'broadcast_workers': 4,
        
        # Faster monitoring for production
        'health_check_interval': 2.0,
        'metrics_history_size': 200,
        
        # Stricter thresholds for production
        'max_queue_utilization': 0.7,
        'max_avg_decode_time_ms': 5.0,
        'max_avg_strategy_time_ms': 25.0,
        'max_avg_broadcast_time_ms': 3.0
    }
    
    # Create integration
    integration = HighFrequencyIntegration(prod_config)
    
    try:
        # Get authorized websocket URL (from your auth service)
        # websocket_url = await get_authorized_websocket_url()
        websocket_url = "wss://api.upstox.com/v3/feed/market-data-feed"
        
        # Start system
        success = await integration.start(websocket_url)
        
        if success:
            logger.info("High-frequency system started successfully")
            
            # Monitor system
            while True:
                await asyncio.sleep(5)
                status = integration.get_status()
                
                # Log status
                logger.info(f"System healthy: {status['health']['is_healthy']}")
                logger.info(f"Performance: {status['performance']}")
                
                # Check for issues
                if not status['health']['is_healthy']:
                    logger.warning(f"System health issues detected: {status['health']}")
                
        else:
            logger.error("Failed to start high-frequency system")
            
    except KeyboardInterrupt:
        logger.info("Shutting down high-frequency system...")
    finally:
        await integration.stop()


# Development setup example
async def setup_development_system():
    """
    Example development setup with lighter configuration
    """
    
    # Development configuration
    dev_config = {
        'raw_queue_size': 1000,
        'decoded_queue_size': 500,
        'signal_queue_size': 200,
        'decode_workers': 2,
        'strategy_workers': 1,
        'broadcast_workers': 1,
        'health_check_interval': 10.0
    }
    
    integration = HighFrequencyIntegration(dev_config)
    
    try:
        websocket_url = "wss://api.upstox.com/v3/feed/market-data-feed"
        success = await integration.start(websocket_url)
        
        if success:
            logger.info("Development system started")
            
            # Simple monitoring
            while True:
                await asyncio.sleep(30)
                status = integration.get_status()
                logger.info(f"Dev status: {status['health']['is_healthy']}")
                
        else:
            logger.error("Failed to start development system")
            
    except KeyboardInterrupt:
        logger.info("Shutting down development system...")
    finally:
        await integration.stop()


if __name__ == "__main__":
    # Choose setup based on environment
    import os
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        asyncio.run(setup_high_frequency_system())
    else:
        asyncio.run(setup_development_system())
