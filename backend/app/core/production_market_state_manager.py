"""
Production-Grade Market State Manager
Optimized for high-frequency updates with memory management
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class MarketSnapshot:
    """Immutable market snapshot for thread safety"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class ProductionMarketStateManager:
    """Production-grade market state manager with memory optimization"""
    
    def __init__(self, max_history_size: int = 1000, cleanup_interval: int = 300):
        self.max_history_size = max_history_size
        self.cleanup_interval = cleanup_interval
        
        # Current market state
        self.current_state: Dict[str, MarketSnapshot] = {}
        
        # Historical data with limited size
        self.historical_data: Dict[str, deque] = {}
        
        # Performance metrics
        self.update_count: int = 0
        self.last_cleanup: datetime = datetime.utcnow()
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the market state manager"""
        if self._cleanup_task:
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Market state manager started")
    
    async def stop(self):
        """Stop the market state manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        logger.info("Market state manager stopped")
    
    async def update_market_state(self, symbol: str, price: float, volume: int, metadata: Dict[str, Any] = None):
        """Update market state for a symbol"""
        async with self._lock:
            now = datetime.utcnow()
            snapshot = MarketSnapshot(
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=now,
                metadata=metadata or {}
            )
            
            # Update current state
            self.current_state[symbol] = snapshot
            
            # Add to historical data
            if symbol not in self.historical_data:
                self.historical_data[symbol] = deque(maxlen=self.max_history_size)
            
            self.historical_data[symbol].append(snapshot)
            self.update_count += 1
    
    async def get_current_state(self, symbol: str) -> Optional[MarketSnapshot]:
        """Get current market state for symbol"""
        async with self._lock:
            return self.current_state.get(symbol)
    
    async def get_all_current_states(self) -> Dict[str, MarketSnapshot]:
        """Get all current market states"""
        async with self._lock:
            return self.current_state.copy()
    
    async def get_historical_data(self, symbol: str, limit: int = 100) -> List[MarketSnapshot]:
        """Get historical data for symbol"""
        async with self._lock:
            if symbol not in self.historical_data:
                return []
            
            history = list(self.historical_data[symbol])
            return history[-limit:] if len(history) > limit else history
    
    async def get_price_history(self, symbol: str, minutes: int = 60) -> List[float]:
        """Get price history for the last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        async with self._lock:
            if symbol not in self.historical_data:
                return []
            
            return [
                snapshot.price for snapshot in self.historical_data[symbol]
                if snapshot.timestamp >= cutoff_time
            ]
    
    async def calculate_volume_weighted_price(self, symbol: str, minutes: int = 5) -> Optional[float]:
        """Calculate volume-weighted average price"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        async with self._lock:
            if symbol not in self.historical_data:
                return None
            
            relevant_snapshots = [
                snapshot for snapshot in self.historical_data[symbol]
                if snapshot.timestamp >= cutoff_time
            ]
            
            if not relevant_snapshots:
                return None
            
            total_volume = sum(s.volume for s in relevant_snapshots)
            if total_volume == 0:
                return None
            
            vwap = sum(s.price * s.volume for s in relevant_snapshots) / total_volume
            return vwap
    
    async def get_price_change(self, symbol: str, minutes: int = 1) -> Optional[float]:
        """Get price change percentage"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        async with self._lock:
            if symbol not in self.historical_data:
                return None
            
            snapshots = list(self.historical_data[symbol])
            if len(snapshots) < 2:
                return None
            
            # Find oldest and newest snapshots within time window
            oldest = None
            newest = None
            
            for snapshot in snapshots:
                if snapshot.timestamp >= cutoff_time:
                    if oldest is None or snapshot.timestamp < oldest.timestamp:
                        oldest = snapshot
                    if newest is None or snapshot.timestamp > newest.timestamp:
                        newest = snapshot
            
            if oldest and newest and oldest.price > 0:
                change = ((newest.price - oldest.price) / oldest.price) * 100
                return change
            
            return None
    
    async def _cleanup_loop(self):
        """Periodic cleanup of old data"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Market state cleanup error: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old historical data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Keep 24 hours
        
        async with self._lock:
            removed_count = 0
            
            for symbol, history in self.historical_data.items():
                original_size = len(history)
                
                # Remove old snapshots
                while history and history[0].timestamp < cutoff_time:
                    history.popleft()
                    removed_count += 1
                
                # Log significant cleanups
                if original_size - len(history) > 100:
                    logger.info(f"Cleaned {original_size - len(history)} old entries for {symbol}")
            
            self.last_cleanup = datetime.utcnow()
            
            if removed_count > 0:
                logger.info(f"Market state cleanup: removed {removed_count} old entries")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        async with self._lock:
            total_snapshots = sum(len(history) for history in self.historical_data.values())
            
            return {
                "total_symbols": len(self.current_state),
                "total_snapshots": total_snapshots,
                "update_count": self.update_count,
                "last_cleanup": self.last_cleanup.isoformat(),
                "memory_efficiency": f"{total_snapshots}/{len(self.historical_data) * self.max_history_size}"
            }

# Global market state manager instance
market_state_manager = ProductionMarketStateManager()

async def get_market_state_manager() -> ProductionMarketStateManager:
    """Get market state manager instance"""
    return market_state_manager
