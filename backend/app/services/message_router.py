"""
Message Router for StrikeIQ
Routes parsed protobuf ticks to appropriate processors
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageRouter:
    """Routes market data ticks to appropriate processors"""
    
    def __init__(self):
        self.last_index_prices = {}  # Track last prices for change calculation
    
    def route_tick(self, tick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Route a single tick to appropriate message type
        
        Args:
            tick: Parsed tick from protobuf parser
            Format: {"instrument_key": "NSE_INDEX|NIFTY 50", "ltp": 24555.30}
        
        Returns:
            Structured message object or None if routing fails
        """
        try:
            instrument_key = tick.get("instrument_key", "")
            ltp = tick.get("ltp", 0)
            
            if not instrument_key or ltp <= 0:
                logger.warning(f"Invalid tick data: {tick}")
                return None
            
            # Parse instrument key to extract symbol and type
            parsed = self._parse_instrument_key(instrument_key)
            if not parsed:
                logger.warning(f"Could not parse instrument key: {instrument_key}")
                return None
            
            symbol = parsed["symbol"]
            instrument_type = parsed["type"]
            
            timestamp = int(datetime.now().timestamp())
            
            # Route based on instrument type
            if instrument_type == "INDEX":
                return self._create_index_tick(symbol, ltp, timestamp)
            elif instrument_type == "OPTION":
                return self._create_option_tick(symbol, parsed, ltp, timestamp)
            else:
                logger.warning(f"Unknown instrument type: {instrument_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error routing tick: {e}")
            return None
    
    def _parse_instrument_key(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """Parse instrument key to extract symbol and type"""
        try:
            parts = instrument_key.split("|")
            if len(parts) < 2:
                return None
            
            segment = parts[0]
            symbol_part = parts[1]
            
            # Handle index instruments
            if segment == "NSE_INDEX":
                if "Nifty 50" in symbol_part:
                    return {"symbol": "NIFTY", "type": "INDEX"}
                elif "Nifty Bank" in symbol_part:
                    return {"symbol": "BANKNIFTY", "type": "INDEX"}
                else:
                    logger.debug(f"Unknown index symbol: {symbol_part}")
                    return None
            
            # Handle option instruments
            elif segment == "NSE_FO":
                # Extract symbol from option key
                if "NIFTY" in symbol_part:
                    base_symbol = "NIFTY"
                elif "BANKNIFTY" in symbol_part:
                    base_symbol = "BANKNIFTY"
                else:
                    return None
                
                # Parse strike and right from symbol
                option_parts = symbol_part.split()
                if len(option_parts) >= 3:
                    try:
                        strike = float(option_parts[-2])
                        right = option_parts[-1]  # CE or PE
                        return {
                            "symbol": base_symbol,
                            "type": "OPTION",
                            "strike": strike,
                            "right": right
                        }
                    except (ValueError, IndexError):
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing instrument key {instrument_key}: {e}")
            return None
    
    def _create_index_tick(self, symbol: str, ltp: float, timestamp: int) -> Dict[str, Any]:
        """Create index tick message with change calculation"""
        last_price = self.last_index_prices.get(symbol, ltp)
        change = ltp - last_price
        change_percent = (change / last_price * 100) if last_price > 0 else 0
        
        # Update last price
        self.last_index_prices[symbol] = ltp
        
        return {
            "type": "index_tick",
            "symbol": symbol,
            "timestamp": timestamp,
            "data": {
                "ltp": ltp,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2)
            }
        }
    
    def _create_option_tick(self, symbol: str, parsed: Dict[str, Any], ltp: float, timestamp: int) -> Dict[str, Any]:
        """Create option tick message"""
        return {
            "type": "option_tick",
            "symbol": symbol,
            "timestamp": timestamp,
            "data": {
                "strike": parsed["strike"],
                "right": parsed["right"],
                "ltp": ltp,
                "oi": 0,  # Will be populated by option chain builder
                "volume": 0  # Will be populated by option chain builder
            }
        }

# Global instance
message_router = MessageRouter()
