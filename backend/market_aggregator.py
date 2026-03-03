"""
Market Data Aggregator with Full Debug Logging
Processes decoded protobuf data and generates heatmap with trace tracking
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.logger import aggregator_logger, get_trace_id

class MarketAggregator:
    def __init__(self):
        self.processing_count = 0
        self.heatmap_count = 0
        self.current_market_data: Dict[str, Any] = {}
        self.heatmap_data: Dict[str, Any] = {}
        
    async def process_market_data(self, decoded_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process decoded market data with comprehensive logging"""
        try:
            logger.info(f"AGGREGATOR INPUT DATA={decoded_data}")
            
            # Market status detection
            market_open = True if decoded_data else False
            logger.info(f"MARKET STATUS DETECTED={'OPEN' if market_open else 'CLOSED'}")
            
            instrument_count = len(decoded_data.get('instruments', []))
            aggregator_logger.info(f"AGGREGATOR PROCESSING trace={get_trace_id()} instruments={instrument_count}")
            
            # Process each instrument
            processed_instruments = []
            for instrument in decoded_data.get('instruments', []):
                processed = await self._process_instrument(instrument)
                if processed:
                    processed_instruments.append(processed)
            
            # Update current market data
            self.current_market_data = {
                "timestamp": datetime.now().isoformat(),
                "instruments": processed_instruments,
                "trace_id": get_trace_id(),
                "feed_type": decoded_data.get('feed_type', 'market_data')
            }
            
            self.processing_count += 1
            aggregator_logger.info(f"AGGREGATOR PROCESSING SUCCESS trace={get_trace_id()} processed={len(processed_instruments)} total_processed={self.processing_count}")
            
            # Generate heatmap
            heatmap = await self._generate_heatmap(processed_instruments)
            if heatmap:
                self.heatmap_count += 1
                symbol_count = len(heatmap.get('symbols', []))
                aggregator_logger.info(f"AGGREGATOR HEATMAP GENERATED trace={get_trace_id()} symbols={symbol_count} total_heatmaps={self.heatmap_count}")
            
            logger.info(f"AGGREGATOR OUTPUT DATA={self.current_market_data}")
            return self.current_market_data
            
        except Exception as e:
            aggregator_logger.error(f"AGGREGATOR PROCESSING ERROR trace={get_trace_id()} error={str(e)}")
            return None
    
    async def _process_instrument(self, instrument: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual instrument data"""
        try:
            # Extract and validate instrument data
            instrument_key = instrument.get('instrument_key')
            ltp = instrument.get('ltp')
            volume = instrument.get('volume')
            
            if not all([instrument_key, ltp is not None, volume is not None]):
                aggregator_logger.warning(f"AGGREGATOR INSTRUMENT INVALID trace={get_trace_id()} instrument={instrument_key}")
                return None
            
            # Calculate derived metrics
            processed = {
                "instrument_key": instrument_key,
                "ltp": ltp,
                "volume": volume,
                "timestamp": instrument.get('timestamp', datetime.now().isoformat()),
                "change": self._calculate_change(instrument_key, ltp),
                "change_percent": self._calculate_change_percent(instrument_key, ltp),
                "oi": self._get_open_interest(instrument_key),
                "oi_change": self._get_oi_change(instrument_key)
            }
            
            aggregator_logger.debug(f"AGGREGATOR INSTRUMENT PROCESSED trace={get_trace_id()} instrument={instrument_key} ltp={ltp}")
            return processed
            
        except Exception as e:
            aggregator_logger.error(f"AGGREGATOR INSTRUMENT ERROR trace={get_trace_id()} error={str(e)}")
            return None
    
    async def _generate_heatmap(self, instruments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate heatmap data from processed instruments"""
        try:
            aggregator_logger.info(f"AGGREGATOR HEATMAP START trace={get_trace_id()} instruments={len(instruments)}")
            
            # Group instruments by category
            symbols = []
            for instrument in instruments:
                heatmap_symbol = {
                    "symbol": instrument['instrument_key'],
                    "price": instrument['ltp'],
                    "change": instrument['change'],
                    "change_percent": instrument['change_percent'],
                    "volume": instrument['volume'],
                    "oi": instrument['oi'],
                    "oi_change": instrument['oi_change'],
                    "color": self._calculate_heatmap_color(instrument['change_percent'])
                }
                symbols.append(heatmap_symbol)
            
            # Create heatmap structure
            heatmap = {
                "timestamp": datetime.now().isoformat(),
                "symbols": symbols,
                "market_status": self._get_market_status(),
                "trace_id": get_trace_id(),
                "total_symbols": len(symbols)
            }
            
            self.heatmap_data = heatmap
            aggregator_logger.info(f"AGGREGATOR HEATMAP COMPLETE trace={get_trace_id()} symbols={len(symbols)}")
            return heatmap
            
        except Exception as e:
            aggregator_logger.error(f"AGGREGATOR HEATMAP ERROR trace={get_trace_id()} error={str(e)}")
            return None
    
    def _calculate_change(self, instrument_key: str, current_ltp: float) -> float:
        """Calculate price change"""
        # Mock calculation - replace with actual logic
        return 0.0
    
    def _calculate_change_percent(self, instrument_key: str, current_ltp: float) -> float:
        """Calculate percentage change"""
        # Mock calculation - replace with actual logic
        return 0.0
    
    def _get_open_interest(self, instrument_key: str) -> int:
        """Get open interest for instrument"""
        # Mock data - replace with actual logic
        return 1000
    
    def _get_oi_change(self, instrument_key: str) -> int:
        """Get open interest change"""
        # Mock data - replace with actual logic
        return 0
    
    def _calculate_heatmap_color(self, change_percent: float) -> str:
        """Calculate heatmap color based on change"""
        if change_percent > 2:
            return "dark_green"
        elif change_percent > 0:
            return "light_green"
        elif change_percent > -2:
            return "light_red"
        else:
            return "dark_red"
    
    def _get_market_status(self) -> str:
        """Get current market status"""
        # Mock status - replace with actual logic
        return "OPEN"
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get current market data"""
        return self.current_market_data
    
    def get_heatmap_data(self) -> Dict[str, Any]:
        """Get current heatmap data"""
        return self.heatmap_data
    
    def get_stats(self) -> Dict[str, int]:
        """Get aggregator statistics"""
        return {
            "processing_count": self.processing_count,
            "heatmap_count": self.heatmap_count
        }

# Global aggregator instance
market_aggregator = MarketAggregator()

async def process_market_data(decoded_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Global function to process market data"""
    return await market_aggregator.process_market_data(decoded_data)

def get_aggregator_stats() -> Dict[str, int]:
    """Get aggregator statistics"""
    return market_aggregator.get_stats()
