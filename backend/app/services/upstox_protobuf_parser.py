"""
Simple protobuf parser for Upstox V3 Market Data Feed
This is a basic implementation for the essential fields we need
"""

import struct
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FeedData:
    """Market data feed entry"""
    instrument_key: str = ""
    timestamp: int = 0
    ltp: float = 0.0
    volume: int = 0
    oi: int = 0
    bid_price: float = 0.0
    bid_quantity: int = 0
    ask_price: float = 0.0
    ask_quantity: int = 0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    previous_close_oi: int = 0

@dataclass
class FeedResponse:
    """Complete feed response"""
    feeds: List[FeedData] = None
    
    def __post_init__(self):
        if self.feeds is None:
            self.feeds = []

class SimpleProtobufParser:
    """
    Simple protobuf parser for Upstox V3 feed
    This handles the basic wire format for our use case
    """
    
    @staticmethod
    def parse_varint(buffer: bytes, offset: int) -> tuple[int, int]:
        """Parse varint from buffer"""
        result = 0
        shift = 0
        
        while offset < len(buffer):
            byte = buffer[offset]
            offset += 1
            
            result |= (byte & 0x7F) << shift
            shift += 7
            
            if (byte & 0x80) == 0:
                break
        
        return result, offset
    
    @staticmethod
    def parse_string(buffer: bytes, offset: int) -> tuple[str, int]:
        """Parse string field"""
        length, offset = SimpleProtobufParser.parse_varint(buffer, offset)
        string_bytes = buffer[offset:offset + length]
        string_value = string_bytes.decode('utf-8')
        return string_value, offset + length
    
    @staticmethod
    def parse_double(buffer: bytes, offset: int) -> tuple[float, int]:
        """Parse double field"""
        # Double is 8 bytes, little endian
        double_bytes = buffer[offset:offset + 8]
        double_value = struct.unpack('<d', double_bytes)[0]
        return double_value, offset + 8
    
    @staticmethod
    def parse_int64(buffer: bytes, offset: int) -> tuple[int, int]:
        """Parse int64 field"""
        # For simplicity, treat as varint
        return SimpleProtobufParser.parse_varint(buffer, offset)
    
    @staticmethod
    def parse_feed_data(buffer: bytes, offset: int) -> tuple[FeedData, int]:
        """Parse single FeedData message"""
        feed = FeedData()
        
        while offset < len(buffer):
            # Read tag (field number and wire type)
            tag, offset = SimpleProtobufParser.parse_varint(buffer, offset)
            field_number = tag >> 3
            wire_type = tag & 0x7
            
            try:
                if wire_type == 2:  # Length-delimited (string)
                    if field_number == 1:  # instrumentKey
                        feed.instrument_key, offset = SimpleProtobufParser.parse_string(buffer, offset)
                    else:
                        # Skip unknown string field
                        length, offset = SimpleProtobufParser.parse_varint(buffer, offset)
                        offset += length
                
                elif wire_type == 1:  # 64-bit (double/int64)
                    if field_number == 2:  # timestamp
                        feed.timestamp, offset = SimpleProtobufParser.parse_int64(buffer, offset)
                    elif field_number == 3:  # ltp
                        feed.ltp, offset = SimpleProtobufParser.parse_double(buffer, offset)
                    elif field_number == 4:  # volume
                        feed.volume, offset = SimpleProtobufParser.parse_int64(buffer, offset)
                    elif field_number == 5:  # oi
                        feed.oi, offset = SimpleProtobufParser.parse_int64(buffer, offset)
                    elif field_number == 6:  # bidPrice
                        feed.bid_price, offset = SimpleProtobufParser.parse_double(buffer, offset)
                    elif field_number == 7:  # bidQuantity
                        feed.bid_quantity, offset = SimpleProtobufParser.parse_int64(buffer, offset)
                    elif field_number == 8:  # askPrice
                        feed.ask_price, offset = SimpleProtobufParser.parse_double(buffer, offset)
                    elif field_number == 9:  # askQuantity
                        feed.ask_quantity, offset = SimpleProtobufParser.parse_int64(buffer, offset)
                    elif field_number == 10:  # open
                        feed.open, offset = SimpleProtobufParser.parse_double(buffer, offset)
                    elif field_number == 11:  # high
                        feed.high, offset = SimpleProtobufParser.parse_double(buffer, offset)
                    elif field_number == 12:  # low
                        feed.low, offset = SimpleProtobufParser.parse_double(buffer, offset)
                    elif field_number == 13:  # close
                        feed.close, offset = SimpleProtobufParser.parse_double(buffer, offset)
                    elif field_number == 14:  # previousCloseOI
                        feed.previous_close_oi, offset = SimpleProtobufParser.parse_int64(buffer, offset)
                    else:
                        # Skip unknown 64-bit field
                        offset += 8
                
                else:
                    # Skip unknown wire type
                    if wire_type == 0:  # varint
                        _, offset = SimpleProtobufParser.parse_varint(buffer, offset)
                    elif wire_type == 5:  # 32-bit
                        offset += 4
                    else:
                        break  # Unknown wire type, stop parsing
                        
            except Exception as e:
                logger.debug(f"Error parsing field {field_number}: {e}")
                break
        
        return feed, offset
    
    @staticmethod
    def parse_feed_response(buffer: bytes) -> FeedResponse:
        """Parse complete FeedResponse message"""
        response = FeedResponse()
        offset = 0
        
        try:
            while offset < len(buffer):
                # Read tag
                tag, offset = SimpleProtobufParser.parse_varint(buffer, offset)
                field_number = tag >> 3
                wire_type = tag & 0x7
                
                if field_number == 1 and wire_type == 2:  # feeds field (repeated)
                    # Read length of FeedData message
                    length, offset = SimpleProtobufParser.parse_varint(buffer, offset)
                    
                    # Parse FeedData message
                    feed_data, offset = SimpleProtobufParser.parse_feed_data(buffer, offset)
                    response.feeds.append(feed_data)
                else:
                    # Skip unknown field
                    if wire_type == 2:  # Length-delimited
                        length, offset = SimpleProtobufParser.parse_varint(buffer, offset)
                        offset += length
                    elif wire_type == 0:  # varint
                        _, offset = SimpleProtobufParser.parse_varint(buffer, offset)
                    elif wire_type == 1:  # 64-bit
                        offset += 8
                    elif wire_type == 5:  # 32-bit
                        offset += 4
                    else:
                        break
        
        except Exception as e:
            logger.error(f"Error parsing protobuf message: {e}")
            # Return empty response on error
            return FeedResponse()
        
        return response

def parse_upstox_feed(message: bytes) -> FeedResponse:
    """
    Parse Upstox V3 WebSocket feed message
    """
    try:
        return SimpleProtobufParser.parse_feed_response(message)
    except Exception as e:
        logger.error(f"Failed to parse Upstox feed: {e}")
        return FeedResponse()
