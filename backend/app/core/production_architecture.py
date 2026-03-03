"""
Production Architecture Orchestrator for StrikeIQ
Implements clean architecture pattern with proper separation of concerns
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from .production_redis_client import production_redis
from .production_ws_manager import ws_manager
from .production_market_state_manager import market_state_manager
from .async_db import async_db
from ai.async_ai_db import async_ai_db

logger = logging.getLogger(__name__)

class ProductionArchitectureOrchestrator:
    """
    Orchestrates the clean architecture flow:
    Upstox WebSocket Feed → Feed Parser → Market State Cache → Redis PubSub → 
    FastAPI WebSocket → Frontend WebSocket Service → Zustand Store → React UI
    """
    
    def __init__(self):
        self.is_initialized = False
        self.components = {}
        
    async def initialize(self):
        """Initialize all architecture components in proper order"""
        if self.is_initialized:
            return
        
        logger.info("🏗️ Initializing Production Architecture...")
        
        try:
            # 1. Initialize Database Layer
            await async_db.initialize()
            await async_ai_db.initialize()
            logger.info("✅ Database layer initialized")
            
            # 2. Initialize Redis Layer
            await production_redis.initialize()
            logger.info("✅ Redis layer initialized")
            
            # 3. Initialize Market State Manager
            await market_state_manager.start()
            logger.info("✅ Market state manager started")
            
            # 4. Initialize WebSocket Manager
            await ws_manager.start()
            logger.info("✅ WebSocket manager started")
            
            self.is_initialized = True
            logger.info("🎉 Production Architecture initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Architecture initialization failed: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown all components in reverse order"""
        if not self.is_initialized:
            return
        
        logger.info("🛑 Shutting down Production Architecture...")
        
        try:
            # 1. Stop WebSocket Manager
            await ws_manager.stop()
            logger.info("✅ WebSocket manager stopped")
            
            # 2. Stop Market State Manager
            await market_state_manager.stop()
            logger.info("✅ Market state manager stopped")
            
            # 3. Close Redis Connections
            await production_redis.close()
            logger.info("✅ Redis connections closed")
            
            # 4. Close Database Connections
            await async_db.close()
            logger.info("✅ Database connections closed")
            
            self.is_initialized = False
            logger.info("🎉 Production Architecture shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Architecture shutdown failed: {e}")
    
    async def process_market_feed(self, feed_data: Dict[str, Any]):
        """
        Process market feed through clean architecture pipeline
        """
        try:
            # Step 1: Parse and validate feed data
            parsed_data = await self._parse_market_feed(feed_data)
            
            # Step 2: Update market state cache
            await self._update_market_state(parsed_data)
            
            # Step 3: Publish to Redis PubSub
            await self._publish_to_redis(parsed_data)
            
            # Step 4: Broadcast to WebSocket clients
            await self._broadcast_to_clients(parsed_data)
            
            # Step 5: Store in database for analytics
            await self._store_for_analytics(parsed_data)
            
        except Exception as e:
            logger.error(f"Market feed processing failed: {e}")
            raise
    
    async def _parse_market_feed(self, feed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate market feed data"""
        # Add timestamp if not present
        if 'timestamp' not in feed_data:
            feed_data['timestamp'] = datetime.utcnow().isoformat()
        
        # Validate required fields
        required_fields = ['symbol', 'price', 'volume']
        for field in required_fields:
            if field not in feed_data:
                raise ValueError(f"Missing required field: {field}")
        
        return feed_data
    
    async def _update_market_state(self, parsed_data: Dict[str, Any]):
        """Update market state cache"""
        symbol = parsed_data['symbol']
        price = float(parsed_data['price'])
        volume = int(parsed_data['volume'])
        metadata = {k: v for k, v in parsed_data.items() if k not in ['symbol', 'price', 'volume']}
        
        await market_state_manager.update_market_state(symbol, price, volume, metadata)
    
    async def _publish_to_redis(self, parsed_data: Dict[str, Any]):
        """Publish to Redis PubSub for real-time distribution"""
        channel = f"market:{parsed_data['symbol']}"
        message = {
            'type': 'market_update',
            'data': parsed_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await production_redis.publish(channel, str(message))
        
        # Also publish to general market channel
        await production_redis.publish('market:all', str(message))
    
    async def _broadcast_to_clients(self, parsed_data: Dict[str, Any]):
        """Broadcast to WebSocket clients"""
        message = {
            'type': 'market_update',
            'symbol': parsed_data['symbol'],
            'price': parsed_data['price'],
            'volume': parsed_data['volume'],
            'timestamp': parsed_data['timestamp']
        }
        
        # Broadcast to market data channel
        await ws_manager.broadcast_to_channel('market_data', message)
    
    async def _store_for_analytics(self, parsed_data: Dict[str, Any]):
        """Store data for AI analytics"""
        try:
            # Store market snapshot for AI training
            snapshot_data = {
                'symbol': parsed_data['symbol'],
                'price_data': {
                    'price': parsed_data['price'],
                    'volume': parsed_data['volume']
                },
                'indicators': {},  # Add calculated indicators here
                'timestamp': datetime.utcnow(),
                'metadata': parsed_data.get('metadata', {})
            }
            
            await async_ai_db.store_market_snapshot(snapshot_data)
            
        except Exception as e:
            logger.error(f"Failed to store for analytics: {e}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            # Database health
            db_health = await async_db.test_connection()
            
            # Redis health
            redis_health = await production_redis.test_connection()
            
            # WebSocket stats
            ws_stats = await ws_manager.get_connection_stats()
            
            # Market state metrics
            market_metrics = await market_state_manager.get_performance_metrics()
            
            # AI database health
            ai_metrics = await async_ai_db.get_ai_metrics()
            
            return {
                'status': 'healthy' if all([db_health, redis_health]) else 'degraded',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'database': {'healthy': db_health},
                    'redis': {'healthy': redis_health},
                    'websocket': ws_stats,
                    'market_state': market_metrics,
                    'ai_engine': ai_metrics
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    async def get_architecture_metrics(self) -> Dict[str, Any]:
        """Get architecture performance metrics"""
        try:
            return {
                'initialized': self.is_initialized,
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'database_pool': 'active',
                    'redis_pool': 'active',
                    'websocket_connections': len(ws_manager.connections),
                    'market_symbols': len(market_state_manager.current_state),
                    'total_snapshots': sum(len(h) for h in market_state_manager.historical_data.values())
                }
            }
        except Exception as e:
            logger.error(f"Architecture metrics failed: {e}")
            return {'error': str(e)}

# Global orchestrator instance
architecture_orchestrator = ProductionArchitectureOrchestrator()

@asynccontextmanager
async def production_lifecycle():
    """Context manager for production architecture lifecycle"""
    try:
        await architecture_orchestrator.initialize()
        yield architecture_orchestrator
    finally:
        await architecture_orchestrator.shutdown()

async def get_architecture_orchestrator() -> ProductionArchitectureOrchestrator:
    """Get architecture orchestrator instance"""
    return architecture_orchestrator
