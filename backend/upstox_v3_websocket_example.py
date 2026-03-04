#!/usr/bin/env python3
"""
Upstox V3 WebSocket Market Data Feed - Complete Working Example
Following official Upstox documentation and SDK patterns
"""

import asyncio
import json
import logging
import websockets
import httpx
from typing import List, Dict, Any
from google.protobuf.json_format import MessageToJson

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UpstoxV3WebSocket:
    """
    Complete Upstox V3 WebSocket implementation following official documentation
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.websocket = None
        self.is_connected = False
        
        # Correct instrument keys for NIFTY indices based on documentation
        self.instrument_keys = [
            "NSE_INDEX|NIFTY 50",
            "NSE_INDEX|NIFTY BANK"
        ]
        
    async def get_websocket_url(self) -> str:
        """Get authorized WebSocket URL from Upstox V3 API"""
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.upstox.com/v3/feed/market-data-feed/authorize",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Authorization failed: {response.status_code} - {response.text}")
            
            data = response.json()
            ws_url = data.get("data", {}).get("authorizedRedirectUri")
            
            if not ws_url:
                raise Exception("No WebSocket URL in response")
                
            return ws_url
    
    async def connect(self):
        """Connect to Upstox V3 WebSocket"""
        
        try:
            # Get authorized WebSocket URL
            ws_url = await self.get_websocket_url()
            logger.info(f"Connecting to: {ws_url}")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=20
            )
            self.is_connected = True
            
            logger.info("🟢 UPSTOX V3 WS CONNECTED")
            
            # Subscribe to instruments
            await self.subscribe_instruments()
            
            # Start message processing
            await self.process_messages()
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    async def subscribe_instruments(self):
        """Subscribe to market data for specified instruments"""
        
        # Correct subscription payload following Upstox documentation
        payload = {
            "guid": "strikeiq-feed",
            "method": "sub",
            "data": {
                "mode": "full",  # Full mode for comprehensive data
                "instrumentKeys": self.instrument_keys
            }
        }
        
        logger.info("SUBSCRIPTION PAYLOAD:")
        logger.info(json.dumps(payload, indent=2))
        
        await self.websocket.send(json.dumps(payload))
        logger.info(f"📡 SUBSCRIPTION SENT for {len(self.instrument_keys)} instruments")
    
    async def process_messages(self):
        """Process incoming WebSocket messages"""
        
        try:
            async for message in self.websocket:
                
                # Log message details
                logger.info(f"RAW PACKET SIZE = {len(message)}")
                logger.info(f"MESSAGE TYPE = {type(message)}")
                
                if isinstance(message, bytes):
                    await self.handle_binary_message(message)
                else:
                    await self.handle_text_message(message)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    async def handle_binary_message(self, message: bytes):
        """Handle binary protobuf messages"""
        
        try:
            # Try to parse as V3 protobuf format
            await self.parse_v3_protobuf(message)
            
        except Exception as e:
            logger.error(f"Binary message parsing failed: {e}")
            # Log raw bytes for debugging
            logger.info(f"RAW BYTES (first 50): {message[:50]}")
    
    async def handle_text_message(self, message: str):
        """Handle text messages (JSON)"""
        
        try:
            data = json.loads(message)
            logger.info(f"TEXT MESSAGE: {json.dumps(data, indent=2)}")
            
            # Handle different message types
            if data.get("type") == "heartbeat":
                logger.debug("Heartbeat received")
            elif data.get("type") == "error":
                logger.error(f"Error message: {data}")
            else:
                logger.info(f"Other message: {data}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
    
    async def parse_v3_protobuf(self, message: bytes):
        """Parse V3 protobuf message using correct format"""
        
        try:
            # Import the correct protobuf classes
            from app.proto.MarketDataFeed_pb2 import FeedResponse
            
            # Parse the protobuf message
            feed_response = FeedResponse()
            feed_response.ParseFromString(message)
            
            logger.info(f"PROTOBUF FEEDS COUNT = {len(feed_response.feeds)}")
            
            if not feed_response.feeds:
                logger.info("HEARTBEAT OR EMPTY FEED")
                return
            
            ticks = []
            
            # Parse each feed
            for instrument_key, feed in feed_response.feeds.items():
                logger.info(f"FEED KEY = {instrument_key}")
                logger.info(f"FEED OBJECT TYPE = {type(feed)}")
                
                # Extract LTP based on feed structure
                ltp = await self.extract_ltp(feed)
                
                if ltp and ltp > 0:
                    tick = {
                        "instrument": instrument_key,
                        "ltp": float(ltp),
                        "type": "index_tick" if "INDEX" in instrument_key else "option_tick",
                        "timestamp": feed_response.timestamp if hasattr(feed_response, 'timestamp') else None
                    }
                    ticks.append(tick)
                    
                    logger.info(f"✅ TICK EXTRACTED: {instrument_key} = {ltp}")
                else:
                    logger.info(f"❌ NO VALID LTP for {instrument_key}")
            
            logger.info(f"📊 TOTAL TICKS EXTRACTED = {len(ticks)}")
            
            # Print ticks to console as requested
            for tick in ticks:
                print(f"🎯 MARKET TICK: {tick}")
                
        except Exception as e:
            logger.error(f"Protobuf parsing failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def extract_ltp(self, feed) -> float:
        """Extract LTP from feed based on V3 structure"""
        
        try:
            # V3 structure: Feed -> ff -> indexFF -> ltpc -> ltp
            if hasattr(feed, 'ff') and feed.ff:
                ff = feed.ff
                
                # Index feed
                if hasattr(ff, 'indexFF') and ff.indexFF:
                    index_ff = ff.indexFF
                    if hasattr(index_ff, 'ltpc') and index_ff.ltpc:
                        logger.info("INDEX FEED DETECTED")
                        return float(index_ff.ltpc.ltp)
                
                # Market feed (for options)
                elif hasattr(ff, 'marketFF') and ff.marketFF:
                    market_ff = ff.marketFF
                    if hasattr(market_ff, 'ltpc') and market_ff.ltpc:
                        logger.info("MARKET FEED DETECTED")
                        return float(market_ff.ltpc.ltp)
            
            # Direct LTPC structure (less common)
            if hasattr(feed, 'ltpc') and feed.ltpc:
                logger.info("DIRECT LTPC FEED DETECTED")
                return float(feed.ltpc.ltp)
            
            logger.info("NO RECOGNIZED LTP STRUCTURE")
            return 0.0
            
        except Exception as e:
            logger.error(f"LTP extraction failed: {e}")
            return 0.0
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False
        logger.info("🔌 WebSocket disconnected")

async def main():
    """Main function to test the WebSocket connection"""
    
    # You need to provide a valid access token
    # This should be obtained from Upstox OAuth flow
    access_token = "YOUR_ACCESS_TOKEN_HERE"
    
    if access_token == "YOUR_ACCESS_TOKEN_HERE":
        logger.error("Please provide a valid Upstox access token")
        logger.info("Get token from: https://api.upstox.com/v2/login/authorization/token")
        return
    
    # Create WebSocket client
    ws_client = UpstoxV3WebSocket(access_token)
    
    try:
        # Connect and start receiving data
        await ws_client.connect()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await ws_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
