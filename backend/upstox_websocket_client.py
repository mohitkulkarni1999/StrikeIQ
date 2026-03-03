"""
Upstox WebSocket Client with Full Debug Logging
Handles connection, data reception, and reconnection with trace tracking
"""

import asyncio
import json
import websockets
from typing import Optional, Dict, Any
from core.logger import upstox_logger, start_trace, get_trace_id, with_trace

class UpstoxWebSocketClient:
    def __init__(self, api_key: str, access_token: str):
        self.api_key = api_key
        self.access_token = access_token
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 3  # seconds
        
    @with_trace
    async def connect(self) -> bool:
        """Connect to Upstox WebSocket with logging"""
        try:
            # Start trace for connection
            trace_id = get_trace_id()
            upstox_logger.info(f"UPSTOX CONNECTING trace={trace_id}")
            
            # Build WebSocket URL
            ws_url = f"wss://api-v2.upstox.com/feed/market-data-feed"
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                ws_url,
                extra_headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "x-api-key": self.api_key
                }
            )
            
            self.is_connected = True
            self.reconnect_attempts = 0
            upstox_logger.info(f"UPSTOX CONNECTED trace={trace_id}")
            
            # Send subscription request
            await self._send_subscription()
            
            return True
            
        except Exception as e:
            upstox_logger.error(f"UPSTOX CONNECT ERROR trace={get_trace_id()} error={str(e)}")
            self.is_connected = False
            return False
    
    async def _send_subscription(self):
        """Send subscription request to Upstox"""
        try:
            subscription_data = {
                "method": "sub",
                "params": {
                    "feeds": [
                        {"instrument_key": "NSE_INDEX|Nifty 50"},
                        {"instrument_key": "NSE_INDEX|Bank Nifty"}
                    ]
                }
            }
            
            await self.websocket.send(json.dumps(subscription_data))
            upstox_logger.info(f"UPSTOX SUBSCRIPTION SENT trace={get_trace_id()}")
            
        except Exception as e:
            upstox_logger.error(f"UPSTOX SUBSCRIPTION ERROR trace={get_trace_id()} error={str(e)}")
    
    @with_trace
    async def listen(self):
        """Listen for messages from Upstox with logging"""
        if not self.is_connected or not self.websocket:
            upstox_logger.warning(f"UPSTOX NOT CONNECTED trace={get_trace_id()}")
            return
        
        try:
            upstox_logger.info(f"UPSTOX LISTENING trace={get_trace_id()}")
            
            async for message in self.websocket:
                # Log raw message size
                message_size = len(message) if isinstance(message, (str, bytes)) else 0
                upstox_logger.info(f"UPSTOX DATA RECEIVED trace={get_trace_id()} size={message_size}")
                
                # Process message
                await self._process_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            upstox_logger.warning(f"UPSTOX DISCONNECTED trace={get_trace_id()}")
            self.is_connected = False
            await self._handle_reconnect()
            
        except Exception as e:
            upstox_logger.error(f"UPSTOX LISTEN ERROR trace={get_trace_id()} error={str(e)}")
            self.is_connected = False
            await self._handle_reconnect()
    
    async def _process_message(self, message):
        """Process incoming message from Upstox"""
        try:
            # Parse message
            if isinstance(message, bytes):
                # Handle binary/protobuf data
                upstox_logger.info(f"UPSTOX BINARY DATA trace={get_trace_id()} size={len(message)}")
                await self._handle_binary_data(message)
            else:
                # Handle JSON data
                data = json.loads(message)
                upstox_logger.info(f"UPSTOX JSON DATA trace={get_trace_id()} type={data.get('type', 'unknown')}")
                await self._handle_json_data(data)
                
        except Exception as e:
            upstox_logger.error(f"UPSTOX PROCESS ERROR trace={get_trace_id()} error={str(e)}")
    
    async def _handle_binary_data(self, data: bytes):
        """Handle binary/protobuf data"""
        upstox_logger.info(f"UPSTOX PROTOBUF DATA trace={get_trace_id()} size={len(data)}")
        # Pass to protobuf decoder
        from protobuf_decoder import decode_protobuf_data
        await decode_protobuf_data(data)
    
    async def _handle_json_data(self, data: Dict[str, Any]):
        """Handle JSON data"""
        if data.get('type') == 'heartbeat':
            upstox_logger.info(f"UPSTOX HEARTBEAT trace={get_trace_id()}")
        else:
            upstox_logger.info(f"UPSTOX MESSAGE trace={get_trace_id()} type={data.get('type')}")
    
    async def _handle_reconnect(self):
        """Handle reconnection logic"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            upstox_logger.info(f"UPSTOX RECONNECT trace={get_trace_id()} attempt={self.reconnect_attempts}")
            
            await asyncio.sleep(self.reconnect_delay)
            await self.connect()
            await self.listen()
        else:
            upstox_logger.error(f"UPSTOX RECONNECT FAILED trace={get_trace_id()} max_attempts={self.max_reconnect_attempts}")
    
    async def disconnect(self):
        """Disconnect from Upstox WebSocket"""
        if self.websocket:
            upstox_logger.info(f"UPSTOX DISCONNECTING trace={get_trace_id()}")
            await self.websocket.close()
            self.is_connected = False
            upstox_logger.info(f"UPSTOX DISCONNECTED trace={get_trace_id()}")

# Global client instance
upstox_client: Optional[UpstoxWebSocketClient] = None

async def get_upstox_client() -> UpstoxWebSocketClient:
    """Get or create Upstox client"""
    global upstox_client
    if not upstox_client:
        # Initialize with credentials from environment
        import os
        api_key = os.getenv("UPSTOX_API_KEY")
        access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        
        upstox_client = UpstoxWebSocketClient(api_key, access_token)
    
    return upstox_client
