"""
Upstox V3 Integration
Complete integration example for binary protobuf market data streaming
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from ..manager.websocket_manager import WebSocketManager
from ..ingestion.tick_ingestion_service import TickIngestionService
from ..processor.tick_processor import TickProcessor
from ..dto.market_tick_dto import MarketTickDTO

logger = logging.getLogger(__name__)

class UpstoxV3Integration:
    """
    Complete Upstox V3 integration with protobuf decoding
    Demonstrates the separation between ingestion and signal generation
    """
    
    def __init__(self, queue_size: int = 10000):
        # Initialize components
        self.ingestion_service = TickIngestionService(queue_size)
        self.tick_processor = TickProcessor()
        self.websocket_manager = WebSocketManager(
            self.ingestion_service, 
            self.tick_processor
        )
        
        # Integration state
        self.is_initialized = False
        self.symbol_subscriptions: Dict[str, bool] = {}
    
    async def initialize(self) -> bool:
        """
        Initialize the integration components
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Start ingestion service
            await self.ingestion_service.start_ingestion()
            
            # Start tick processor
            await self.tick_processor.start_processing()
            
            self.is_initialized = True
            logger.info("Upstox V3 integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Upstox V3 integration: {str(e)}")
            return False
    
    async def shutdown(self):
        """Shutdown all integration components"""
        try:
            # Disconnect websocket
            await self.websocket_manager.disconnect()
            
            # Stop tick processor
            await self.tick_processor.stop_processing()
            
            # Stop ingestion service
            await self.ingestion_service.stop_ingestion()
            
            self.is_initialized = False
            logger.info("Upstox V3 integration shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
    
    async def connect_to_feed(self, websocket_url: str) -> bool:
        """
        Connect to Upstox V3 websocket feed
        
        Args:
            websocket_url: Authorized websocket URL from Upstox API
            
        Returns:
            bool: True if connection successful
        """
        if not self.is_initialized:
            logger.error("Integration not initialized")
            return False
        
        return await self.websocket_manager.connect(websocket_url)
    
    def register_strategy(self, strategy_name: str, strategy_handler):
        """
        Register a trading strategy
        
        Args:
            strategy_name: Name of the strategy
            strategy_handler: Strategy function (sync or async)
        """
        self.tick_processor.register_strategy(strategy_name, strategy_handler)
    
    def unregister_strategy(self, strategy_name: str):
        """
        Unregister a trading strategy
        
        Args:
            strategy_name: Name of the strategy to remove
        """
        self.tick_processor.unregister_strategy(strategy_name)
    
    async def get_next_tick(self) -> Optional[MarketTickDTO]:
        """
        Get next decoded tick from ingestion queue
        
        Returns:
            MarketTickDTO or None if no ticks available
        """
        return await self.ingestion_service.get_next_tick()
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get complete integration statistics"""
        return {
            'websocket_stats': self.websocket_manager.get_connection_statistics(),
            'ingestion_stats': self.ingestion_service.get_ingestion_statistics(),
            'processor_stats': self.tick_processor.get_processing_statistics(),
            'is_initialized': self.is_initialized,
            'symbol_subscriptions': self.symbol_subscriptions
        }
    
    def is_healthy(self) -> bool:
        """Check if integration is healthy"""
        if not self.is_initialized:
            return False
        
        return self.websocket_manager.is_healthy()


# Example strategy handlers
async def example_strategy_handler(tick_dto: MarketTickDTO):
    """
    Example async strategy handler
    
    Args:
        tick_dto: Decoded market tick
    """
    logger.info(f"Strategy processing tick: {tick_dto.instrument_key} @ {tick_dto.last_price}")
    
    # Example: Check for price movement
    if tick_dto.is_option_tick():
        # Handle options tick
        if tick_dto.delta > 0.5:
            logger.info(f"High delta option detected: {tick_dto.instrument_key}")
    
    # Add your strategy logic here
    await asyncio.sleep(0.001)  # Simulate processing

def example_sync_strategy_handler(tick_dto: MarketTickDTO):
    """
    Example sync strategy handler
    
    Args:
        tick_dto: Decoded market tick
    """
    logger.info(f"Sync strategy processing: {tick_dto.instrument_key}")
    
    # Add your synchronous strategy logic here
    if tick_dto.volume > 1000:
        logger.info(f"High volume tick: {tick_dto.instrument_key}")


# Usage example
async def main_example():
    """Example usage of Upstox V3 integration"""
    
    # Create integration
    integration = UpstoxV3Integration(queue_size=10000)
    
    try:
        # Initialize
        await integration.initialize()
        
        # Register strategies
        integration.register_strategy("async_example", example_strategy_handler)
        integration.register_strategy("sync_example", example_sync_strategy_handler)
        
        # Connect to feed (replace with actual authorized URL)
        websocket_url = "wss://api.upstox.com/v3/feed/market-data-feed"
        connected = await integration.connect_to_feed(websocket_url)
        
        if connected:
            logger.info("Connected to Upstox V3 feed")
            
            # Monitor ticks
            while True:
                tick = await integration.get_next_tick()
                if tick:
                    logger.info(f"Received tick: {tick.instrument_key} @ {tick.last_price}")
                
                # Print statistics every 10 seconds
                await asyncio.sleep(10)
                stats = integration.get_integration_statistics()
                logger.info(f"Integration stats: {stats}")
        else:
            logger.error("Failed to connect to feed")
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await integration.shutdown()


if __name__ == "__main__":
    asyncio.run(main_example())
