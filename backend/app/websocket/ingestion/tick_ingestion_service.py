"""
Tick Ingestion Service
Handles websocket tick ingestion and queues for strategy processing
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from ..decoder.protobuf_decoder import ProtobufDecoder, DecodingResult
from ..dto.market_tick_dto import MarketTickDTO

logger = logging.getLogger(__name__)

class TickIngestionService:
    """
    Non-blocking tick ingestion service with queue-based processing
    Separates websocket ingestion from strategy execution
    """
    
    def __init__(self, queue_size: int = 10000):
        self.queue_size = queue_size
        self.tick_queue = asyncio.Queue(maxsize=queue_size)
        self.decoder = ProtobufDecoder()
        
        # Statistics
        self.ticks_received = 0
        self.ticks_processed = 0
        self.ticks_dropped = 0
        self.queue_overflows = 0
        
        # Control flags
        self.is_running = False
        self.ingestion_task: Optional[asyncio.Task] = None
        
    async def start_ingestion(self):
        """Start the tick ingestion service"""
        if self.is_running:
            logger.warning("Tick ingestion service already running")
            return
            
        self.is_running = True
        self.ingestion_task = asyncio.create_task(self._ingestion_loop())
        logger.info("Tick ingestion service started")
    
    async def stop_ingestion(self):
        """Stop the tick ingestion service"""
        self.is_running = False
        
        if self.ingestion_task:
            self.ingestion_task.cancel()
            try:
                await self.ingestion_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Tick ingestion service stopped")
    
    async def ingest_binary_tick(self, binary_data: bytes, message_id: str = None) -> bool:
        """
        Ingest binary protobuf tick data
        
        Args:
            binary_data: Raw binary protobuf data from websocket
            message_id: Optional message identifier
            
        Returns:
            bool: True if successfully queued, False if queue full
        """
        try:
            # Check queue capacity
            if self.tick_queue.qsize() >= self.queue_size:
                self.queue_overflows += 1
                self.ticks_dropped += 1
                logger.warning(f"Tick queue overflow, dropping tick {message_id}")
                return False
            
            # Queue the raw binary data for processing
            await self.tick_queue.put({
                'binary_data': binary_data,
                'message_id': message_id,
                'received_at': datetime.now(timezone.utc)
            })
            
            self.ticks_received += 1
            return True
            
        except asyncio.QueueFull:
            self.queue_overflows += 1
            self.ticks_dropped += 1
            logger.error(f"Tick queue full, dropping tick {message_id}")
            return False
    
    async def get_next_tick(self) -> Optional[MarketTickDTO]:
        """
        Get next decoded tick from queue
        
        Returns:
            MarketTickDTO or None if queue empty
        """
        try:
            # Get raw tick data with timeout
            tick_data = await asyncio.wait_for(
                self.tick_queue.get(), 
                timeout=0.1  # 100ms timeout
            )
            
            # Decode protobuf to DTO
            decode_result = await self.decoder.decode_binary_message(
                tick_data['binary_data'],
                tick_data['message_id']
            )
            
            if decode_result.success:
                self.ticks_processed += 1
                return decode_result.tick_dto
            else:
                logger.error(f"Failed to decode tick {tick_data['message_id']}: {decode_result.error}")
                return None
                
        except asyncio.TimeoutError:
            # No ticks available, return None
            return None
        except Exception as e:
            logger.error(f"Error getting next tick: {str(e)}")
            return None
    
    async def _ingestion_loop(self):
        """Main ingestion loop - handles background processing"""
        logger.info("Starting tick ingestion loop")
        
        while self.is_running:
            try:
                # The actual processing happens in get_next_tick()
                # This loop can be used for maintenance tasks
                await asyncio.sleep(1.0)
                
                # Log statistics periodically
                if self.ticks_received % 1000 == 0 and self.ticks_received > 0:
                    stats = self.get_ingestion_statistics()
                    logger.info(f"Tick ingestion stats: {stats}")
                    
            except asyncio.CancelledError:
                logger.info("Tick ingestion loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in ingestion loop: {str(e)}")
                await asyncio.sleep(1.0)  # Prevent tight error loop
        
        logger.info("Tick ingestion loop ended")
    
    def get_ingestion_statistics(self) -> Dict[str, Any]:
        """Get ingestion service statistics"""
        queue_size = self.tick_queue.qsize()
        
        return {
            'ticks_received': self.ticks_received,
            'ticks_processed': self.ticks_processed,
            'ticks_dropped': self.ticks_dropped,
            'queue_size': queue_size,
            'queue_capacity': self.queue_size,
            'queue_utilization': queue_size / self.queue_size,
            'queue_overflows': self.queue_overflows,
            'processing_rate': (
                self.ticks_processed / max(self.ticks_received, 1)
            ),
            'decoder_stats': self.decoder.get_decode_statistics()
        }
    
    async def clear_queue(self):
        """Clear all pending ticks from queue"""
        cleared_count = 0
        
        while not self.tick_queue.empty():
            try:
                self.tick_queue.get_nowait()
                cleared_count += 1
            except asyncio.QueueEmpty:
                break
        
        logger.info(f"Cleared {cleared_count} ticks from queue")
    
    def is_queue_healthy(self) -> bool:
        """Check if queue is in healthy state"""
        queue_utilization = self.tick_queue.qsize() / self.queue_size
        return queue_utilization < 0.8  # Less than 80% full
