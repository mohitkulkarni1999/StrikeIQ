# Generated protobuf definitions for Upstox V3 Feed Response
# This file should be generated using: protoc --python_out=. upstox_feed.proto

from google.protobuf import descriptor
from google.protobuf import message
from google.protobuf import reflection
import sys

# Placeholder for generated protobuf classes
# In production, this would be auto-generated from .proto file

class FeedResponse(message.Message):
    """Upstox V3 Feed Response Message"""
    
    def __init__(self):
        self._fields = {
            'timestamp': 0,
            'instrument_key': '',
            'last_price': 0.0,
            'volume': 0,
            'bid_price': 0.0,
            'ask_price': 0.0,
            'open_interest': 0,
            'oi_change': 0,
            'greeks': {}
        }
    
    def ParseFromString(self, data: bytes):
        """Parse binary protobuf data"""
        # Placeholder implementation
        # Real implementation would parse binary protobuf format
        pass
    
    def HasField(self, field_name: str) -> bool:
        return field_name in self._fields
    
    def ClearField(self, field_name: str):
        if field_name in self._fields:
            self._fields[field_name] = type(self._fields[field_name])()
    
    def MergeFrom(self, other):
        self._fields.update(other._fields)
