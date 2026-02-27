#!/usr/bin/env python3
"""
Test script to verify the market data pipeline
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.websocket_market_feed import ws_feed_manager
from app.core.ws_manager import manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_pipeline():
    """Test the complete market data pipeline"""
    
    logger.info("🚀 Starting market data pipeline test...")
    
    try:
        # 1. Start the WebSocket feed
        logger.info("📡 Starting WebSocket feed...")
        feed = await ws_feed_manager.start_feed()
        
        if not feed or not feed.is_connected:
            logger.error("❌ Failed to start WebSocket feed")
            return False
        
        logger.info("✅ WebSocket feed connected successfully")
        
        # 2. Wait for some data to flow through
        logger.info("⏳ Waiting for market data (30 seconds)...")
        await asyncio.sleep(30)
        
        # 3. Check connection status
        if feed.is_connected:
            logger.info("✅ WebSocket still connected")
        else:
            logger.warning("⚠️ WebSocket disconnected")
        
        # 4. Check active connections
        active_channels = list(manager.active_connections.keys())
        logger.info(f"📊 Active WebSocket channels: {active_channels}")
        
        # 5. Test manual broadcast
        logger.info("📨 Testing manual broadcast...")
        try:
            await manager.broadcast_json(
                "market_data",
                {
                    "type": "test_tick",
                    "data": {
                        "symbol": "NSE_INDEX|Nifty 50",
                        "ltp": 22000.0,
                        "timestamp": 1710000000000
                    }
                }
            )
            logger.info("✅ Manual broadcast successful")
        except Exception as e:
            logger.error(f"❌ Manual broadcast failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            await ws_feed_manager.cleanup_all()
            logger.info("🧹 Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

async def main():
    """Main test function"""
    success = await test_pipeline()
    
    if success:
        logger.info("🎉 Pipeline test completed successfully")
        sys.exit(0)
    else:
        logger.error("💥 Pipeline test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
