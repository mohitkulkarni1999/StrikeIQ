"""
WebSocket Manager
Manages websocket connections and binary message handling
"""

import asyncio
import logging
import websockets
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone

from ..ingestion.tick_ingestion_service import TickIngestionService
from ..processor.tick_processor import TickProcessor

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages websocket connections and routes binary data to ingestion service
    Isolates websocket handling from business logic
    """
    
    def __init__(self, ingestion_service: TickIngestionService, tick_processor: TickProcessor):
        self.ingestion_service = ingestion_service
        self.tick_processor = tick_processor
        
        # Connection management
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.connection_url: Optional[str] = None
        
        # Message tracking
        self.message_count = 0
        self.bytes_received = 0
        self.last_message_time: Optional[datetime] = None
        
        # Control flags
        self.is_running = False
        self.connection_task: Optional[asyncio.Task] = None
        
    async def connect(self, websocket_url: str) -> bool:
        """
        Connect to websocket and start message handling
        
        Args:
            websocket_url: WebSocket URL to connect to
            
        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"Connecting to websocket: {websocket_url}")
            
            # Connect to websocket
            self.websocket = await websockets.connect(
                websocket_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connection_url = websocket_url
            self.is_connected = True
            
            # Start message handling
            self.is_running = True
            self.connection_task = asyncio.create_task(self._message_handler_loop())
            
            logger.info(f"WebSocket connected successfully: {websocket_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to websocket {websocket_url}: {str(e)}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from websocket and cleanup"""
        logger.info("Disconnecting websocket")
        
        self.is_running = False
        
        if self.connection_task:
            self.connection_task.cancel()
            try:
                await self.connection_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket: {str(e)}")
        
        self.is_connected = False
        self.websocket = None
        logger.info("WebSocket disconnected")
    
    async def _message_handler_loop(self):
        """Main message handling loop"""
        logger.info("Starting websocket message handler")
        
        while self.is_running and self.is_connected:
            try:
                # Receive binary message with timeout
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=30.0  # 30 second timeout
                )
                
                # Handle the binary message
                await self._handle_binary_message(message)
                
            except asyncio.TimeoutError:
                logger.warning("WebSocket receive timeout")
                continue
                
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")
                break
                
            except Exception as e:
                logger.error(f"Error in message handler: {str(e)}")
                break
        
        self.is_connected = False
        logger.info("WebSocket message handler ended")
    
    async def _handle_binary_message(self, binary_data: bytes):
        """
        Handle incoming binary protobuf message
        
        Args:
            binary_data: Raw binary data from websocket
        """
        try:
            # Update message statistics
            self.message_count += 1
            self.bytes_received += len(binary_data)
            self.last_message_time = datetime.now(timezone.utc)
            
            # Generate message ID for tracking
            message_id = f"msg_{self.message_count}_{int(self.last_message_time.timestamp())}"
            
            # Send to ingestion service (non-blocking)
            success = await self.ingestion_service.ingest_binary_tick(
                binary_data, 
                message_id
            )
            
            if not success:
                logger.warning(f"Failed to queue message {message_id}")
            
            # Log message receipt periodically
            if self.message_count % 100 == 0:
                logger.info(f"Received {self.message_count} messages, {self.bytes_received} bytes")
                
        except Exception as e:
            logger.error(f"Error handling binary message: {str(e)}")
    
    async def send_message(self, message: str) -> bool:
        """
        Send text message through websocket
        
        Args:
            message: Text message to send
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_connected or not self.websocket:
            logger.warning("Cannot send message - not connected")
            return False
        
        try:
            await self.websocket.send(message)
            logger.debug(f"Sent message: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    async def send_binary_message(self, binary_data: bytes) -> bool:
        """
        Send binary message through websocket
        
        Args:
            binary_data: Binary data to send
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_connected or not self.websocket:
            logger.warning("Cannot send binary message - not connected")
            return False
        
        try:
            await self.websocket.send(binary_data)
            logger.debug(f"Sent binary message: {len(binary_data)} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send binary message: {str(e)}")
            return False
    
    def get_connection_statistics(self) -> Dict[str, Any]:
        """Get websocket connection statistics"""
        return {
            'is_connected': self.is_connected,
            'connection_url': self.connection_url,
            'message_count': self.message_count,
            'bytes_received': self.bytes_received,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'ingestion_stats': self.ingestion_service.get_ingestion_statistics(),
            'processor_stats': self.tick_processor.get_processing_statistics()
        }
    
    def is_healthy(self) -> bool:
        """Check if websocket connection is healthy"""
        if not self.is_connected or not self.websocket:
            return False
        
        # Check if we received messages recently (within last 60 seconds)
        if self.last_message_time:
            time_since_last = (datetime.now(timezone.utc) - self.last_message_time).total_seconds()
            if time_since_last > 60:
                return False
        
        # Check if ingestion service is healthy
        return self.ingestion_service.is_queue_healthy()
