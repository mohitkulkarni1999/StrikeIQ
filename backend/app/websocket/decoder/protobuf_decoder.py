"""
Protobuf Decoder Module
Handles binary protobuf message decoding without blocking event loop
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from ..protobuf.feed_response_pb2 import FeedResponse
from ..dto.market_tick_dto import MarketTickDTO

logger = logging.getLogger(__name__)

@dataclass
class DecodingResult:
    """Result of protobuf decoding operation"""
    success: bool
    tick_dto: Optional[MarketTickDTO] = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0

class ProtobufDecoder:
    """
    Non-blocking protobuf decoder for Upstox V3 feed messages
    Isolates decoding logic from strategy execution
    """
    
    def __init__(self):
        self.decode_count = 0
        self.error_count = 0
        self.total_decode_time_ms = 0.0
    
    async def decode_binary_message(self, binary_data: bytes, message_id: str = None) -> DecodingResult:
        """
        Decode binary protobuf message to MarketTickDTO
        
        Args:
            binary_data: Raw binary protobuf data
            message_id: Optional message identifier for logging
            
        Returns:
            DecodingResult with decoded tick or error
        """
        start_time = datetime.now()
        
        try:
            # Run CPU-intensive protobuf parsing in thread pool
            # This prevents blocking the asyncio event loop
            tick_dto = await asyncio.to_thread(
                self._decode_protobuf_sync, 
                binary_data, 
                message_id
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update statistics
            self.decode_count += 1
            self.total_decode_time_ms += processing_time
            
            logger.debug(f"Decoded protobuf message {message_id} in {processing_time:.2f}ms")
            
            return DecodingResult(
                success=True,
                tick_dto=tick_dto,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.error_count += 1
            
            error_msg = f"Protobuf decode failed for message {message_id}: {str(e)}"
            logger.error(error_msg)
            
            return DecodingResult(
                success=False,
                error=error_msg,
                processing_time_ms=processing_time
            )
    
    def _decode_protobuf_sync(self, binary_data: bytes, message_id: str = None) -> MarketTickDTO:
        """
        Synchronous protobuf parsing - runs in thread pool
        
        Args:
            binary_data: Raw binary protobuf data
            message_id: Optional message identifier
            
        Returns:
            MarketTickDTO with decoded data
        """
        # Parse protobuf message
        feed_response = FeedResponse()
        feed_response.ParseFromString(binary_data)
        
        # Map protobuf fields to internal DTO
        return self._map_to_tick_dto(feed_response, message_id)
    
    def _map_to_tick_dto(self, feed_response: FeedResponse, message_id: str = None) -> MarketTickDTO:
        """
        Map protobuf FeedResponse to internal MarketTickDTO
        
        Args:
            feed_response: Parsed protobuf message
            message_id: Optional message identifier
            
        Returns:
            MarketTickDTO with mapped data
        """
        timestamp = datetime.now(timezone.utc)
        
        # Extract basic price data
        last_price = getattr(feed_response, 'last_price', 0.0)
        volume = getattr(feed_response, 'volume', 0)
        bid_price = getattr(feed_response, 'bid_price', 0.0)
        ask_price = getattr(feed_response, 'ask_price', 0.0)
        
        # Extract options data if available
        open_interest = getattr(feed_response, 'open_interest', 0)
        oi_change = getattr(feed_response, 'oi_change', 0)
        
        # Extract Greeks if available
        greeks = getattr(feed_response, 'greeks', {})
        delta = greeks.get('delta', 0.0)
        theta = greeks.get('theta', 0.0)
        gamma = greeks.get('gamma', 0.0)
        vega = greeks.get('vega', 0.0)
        
        return MarketTickDTO(
            message_id=message_id,
            instrument_key=getattr(feed_response, 'instrument_key', ''),
            timestamp=timestamp,
            last_price=last_price,
            volume=volume,
            bid_price=bid_price,
            ask_price=ask_price,
            open_interest=open_interest,
            oi_change=oi_change,
            delta=delta,
            theta=theta,
            gamma=gamma,
            vega=vega
        )
    
    def get_decode_statistics(self) -> Dict[str, Any]:
        """Get decoder performance statistics"""
        avg_decode_time = (
            self.total_decode_time_ms / self.decode_count 
            if self.decode_count > 0 else 0.0
        )
        
        return {
            'total_decodes': self.decode_count,
            'total_errors': self.error_count,
            'success_rate': (self.decode_count - self.error_count) / max(self.decode_count, 1),
            'average_decode_time_ms': avg_decode_time,
            'total_decode_time_ms': self.total_decode_time_ms
        }
    
    def reset_statistics(self):
        """Reset decoder statistics"""
        self.decode_count = 0
        self.error_count = 0
        self.total_decode_time_ms = 0.0
