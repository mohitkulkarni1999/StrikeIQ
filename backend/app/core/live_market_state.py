"""
Live Market State Manager
Manages in-memory market data state for real-time processing
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class InstrumentData:
    """Data structure for individual instrument"""
    instrument_key: str
    ltp: Optional[float] = None
    ltt: Optional[str] = None
    ltq: Optional[int] = None
    cp: Optional[float] = None  # Close price
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    iv: Optional[float] = None
    volume: Optional[int] = None
    oi: Optional[int] = None
    last_update: Optional[datetime] = None

@dataclass
class StrikeData:
    """Data structure for option strike (both CE and PE)"""
    strike: float
    call: Optional[InstrumentData] = None
    put: Optional[InstrumentData] = None
    last_update: Optional[datetime] = None

@dataclass
class SymbolMarketState:
    """Data structure for symbol market state"""
    symbol: str
    spot: Optional[float] = None
    spot_instrument_key: Optional[str] = None
    spot_change: Optional[float] = 0
    spot_change_percent: Optional[float] = 0
    strikes: Dict[float, StrikeData] = field(default_factory=dict)
    last_update: Optional[datetime] = None
    total_oi_calls: int = 0
    total_oi_puts: int = 0
    
    def get_atm_strike(self) -> Optional[float]:
        """Get ATM strike based on current spot price"""
        if not self.spot or not self.strikes:
            return None
        
        return min(self.strikes.keys(), key=lambda x: abs(x - self.spot))
    
    def get_strike_range(self, count: int = 10) -> List[float]:
        """Get range of strikes around ATM"""
        atm = self.get_atm_strike()
        if not atm:
            return []
        
        all_strikes = sorted(self.strikes.keys())
        atm_idx = all_strikes.index(atm)
        
        start_idx = max(0, atm_idx - count)
        end_idx = min(len(all_strikes), atm_idx + count + 1)
        
        return all_strikes[start_idx:end_idx]

class MarketStateManager:
    """
    Manages live market state across all symbols
    Thread-safe and optimized for real-time updates
    """
    
    def __init__(self):
        self.market_states: Dict[str, SymbolMarketState] = {}
        self._lock = asyncio.Lock()
        
    async def get_symbol_state(self, symbol: str) -> Optional[SymbolMarketState]:
        """Get market state for a symbol"""
        async with self._lock:
            return self.market_states.get(symbol)
    
    async def update_instrument_data(self, symbol: str, instrument_key: str, data: Dict[str, Any]) -> None:
        """
        Update data for a specific instrument
        """
        async with self._lock:
            # Get or create symbol state
            if symbol not in self.market_states:
                self.market_states[symbol] = SymbolMarketState(symbol=symbol)
            
            state = self.market_states[symbol]
            state.last_update = datetime.now(timezone.utc)
            
            # Parse instrument key to determine type
            instrument_type = self._parse_instrument_type(instrument_key)
            
            if instrument_type == "spot":
                # Update spot price - handle both ltp and last_price formats
                spot_price = data.get("ltp") or data.get("last_price")
                if spot_price:
                    # Calculate change from previous spot price
                    old_spot = state.spot
                    change = spot_price - old_spot if old_spot else 0
                    change_percent = (change / old_spot * 100) if old_spot and old_spot != 0 else 0
                    
                    state.spot = float(spot_price)
                    state.spot_instrument_key = instrument_key
                    state.spot_change = change
                    state.spot_change_percent = change_percent
                    state.last_update = datetime.now(timezone.utc)
                    logger.debug(f"Updated spot price for {symbol}: {spot_price} (change: {change:+.2f}, {change_percent:+.2f}%)")
                else:
                    logger.warning(f"No spot price found in data for {symbol}: {data}")
                
            elif instrument_type in ["call", "put"]:
                # Update option data
                strike = self._extract_strike_from_key(instrument_key)
                if strike:
                    # Create strike data if not exists
                    if strike not in state.strikes:
                        state.strikes[strike] = StrikeData(strike=strike)
                    
                    strike_data = state.strikes[strike]
                    
                    # Create instrument data
                    instrument_data = InstrumentData(
                        instrument_key=instrument_key,
                        ltp=data.get("ltp"),
                        ltt=data.get("ltt"),
                        ltq=data.get("ltq"),
                        cp=data.get("cp"),
                        delta=data.get("delta"),
                        gamma=data.get("gamma"),
                        theta=data.get("theta"),
                        vega=data.get("vega"),
                        iv=data.get("iv"),
                        last_update=datetime.now(timezone.utc)
                    )
                    
                    # Update call or put data
                    if instrument_type == "call":
                        strike_data.call = instrument_data
                    else:
                        strike_data.put = instrument_data
                    
                    strike_data.last_update = datetime.now(timezone.utc)
            
            # Recalculate totals
            self._recalculate_totals(state)
    
    def _parse_instrument_type(self, instrument_key: str) -> str:
        """Parse instrument type from key"""
        if "INDEX" in instrument_key:
            return "spot"
        elif instrument_key.endswith("-CE"):
            return "call"
        elif instrument_key.endswith("-PE"):
            return "put"
        return "unknown"
    
    def _extract_strike_from_key(self, instrument_key: str) -> Optional[float]:
        """Extract strike price from instrument key"""
        try:
            # Format: NFO_FO|25500-CE or NFO_FO|25500-PE
            parts = instrument_key.split("|")
            if len(parts) >= 2:
                strike_part = parts[1]
                strike = float(strike_part.split("-")[0])
                return strike
        except:
            pass
        return None
    
    def _recalculate_totals(self, state: SymbolMarketState) -> None:
        """Recalculate total OI and other aggregates"""
        total_calls = 0
        total_puts = 0
        
        for strike_data in state.strikes.values():
            if strike_data.call and strike_data.call.oi:
                total_calls += strike_data.call.oi
            if strike_data.put and strike_data.put.oi:
                total_puts += strike_data.put.oi
        
        state.total_oi_calls = total_calls
        state.total_oi_puts = total_puts
    
    async def get_live_data_for_frontend(self, symbol: str) -> Dict[str, Any]:
        """
        Get processed data ready for frontend consumption
        """
        state = await self.get_symbol_state(symbol)
        if not state:
            return {}
        
        # Get ATM and surrounding strikes
        atm_strike = state.get_atm_strike()
        if not atm_strike:
            return {}
        
        # Build frontend data structure
        frontend_data = {
            "symbol": symbol,
            "spot": state.spot,
            "atm_strike": atm_strike,
            "timestamp": state.last_update.isoformat() if state.last_update else None,
            "total_oi_calls": state.total_oi_calls,
            "total_oi_puts": state.total_oi_puts,
            "pcr": state.total_oi_calls / (state.total_oi_calls + state.total_oi_puts) if (state.total_oi_calls + state.total_oi_puts) > 0 else 0,
            "strikes": {}
        }
        
        # Add strike data (limited range for performance)
        active_strikes = state.get_strike_range(15)  # ATM ± 15 strikes
        
        for strike in active_strikes:
            strike_data = state.strikes[strike]
            strike_info = {
                "strike": strike
            }
            
            if strike_data.call:
                strike_info["call"] = {
                    "ltp": strike_data.call.ltp,
                    "oi": strike_data.call.oi,
                    "delta": strike_data.call.delta,
                    "gamma": strike_data.call.gamma,
                    "theta": strike_data.call.theta,
                    "vega": strike_data.call.vega,
                    "iv": strike_data.call.iv,
                    "volume": strike_data.call.volume,
                    "change": self._calculate_change(strike_data.call)
                }
            
            if strike_data.put:
                strike_info["put"] = {
                    "ltp": strike_data.put.ltp,
                    "oi": strike_data.put.oi,
                    "delta": strike_data.put.delta,
                    "gamma": strike_data.put.gamma,
                    "theta": strike_data.put.theta,
                    "vega": strike_data.put.vega,
                    "iv": strike_data.put.iv,
                    "volume": strike_data.put.volume,
                    "change": self._calculate_change(strike_data.put)
                }
            
            frontend_data["strikes"][strike] = strike_info
        
        return frontend_data
    
    def _calculate_change(self, instrument: InstrumentData) -> float:
        """Calculate price change from close price"""
        if instrument.ltp and instrument.cp:
            return round(instrument.ltp - instrument.cp, 2)
        return 0.0
    
    async def get_market_snapshot(self, symbol: str) -> Dict[str, Any]:
        """
        Get market snapshot for analytics processing
        """
        state = await self.get_symbol_state(symbol)
        if not state:
            return {}
        
        return {
            "symbol": symbol,
            "spot": state.spot,
            "total_oi_calls": state.total_oi_calls,
            "total_oi_puts": state.total_oi_puts,
            "pcr": state.total_oi_calls / (state.total_oi_calls + state.total_oi_puts) if (state.total_oi_calls + state.total_oi_puts) > 0 else 0,
            "atm_strike": state.get_atm_strike(),
            "active_strikes": len(state.strikes),
            "last_update": state.last_update.isoformat() if state.last_update else None
        }
    
    async def cleanup_old_data(self, max_age_minutes: int = 30) -> None:
        """
        Clean up old data to prevent memory leaks
        """
        async with self._lock:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_minutes * 60)
            
            for symbol, state in self.market_states.items():
                # Clean old strike data
                strikes_to_remove = []
                for strike, strike_data in state.strikes.items():
                    if (strike_data.last_update and 
                        strike_data.last_update.timestamp() < cutoff_time):
                        strikes_to_remove.append(strike)
                
                for strike in strikes_to_remove:
                    del state.strikes[strike]
                
                # Remove symbol if no recent data
                if (state.last_update and 
                    state.last_update.timestamp() < cutoff_time and
                    len(state.strikes) == 0):
                    del self.market_states[symbol]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get market state statistics
        """
        async with self._lock:
            total_symbols = len(self.market_states)
            total_strikes = sum(len(state.strikes) for state in self.market_states.values())
            
            return {
                "total_symbols": total_symbols,
                "total_strikes": total_strikes,
                "symbols": list(self.market_states.keys()),
                "last_update": max((state.last_update for state in self.market_states.values() if state.last_update), default=None)
            }
