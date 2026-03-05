"""
Tick Batcher for StrikeIQ
Batches individual ticks for improved performance
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable
from datetime import datetime
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class TickBatcher:
    """Batches individual ticks for improved processing performance"""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 0.1):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Batches by symbol and type
        self.batches: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Callback for processing batches
        self.process_callback: Callable[[List[Dict[str, Any]]], None] = None
        
        # Background task
        self._task: asyncio.Task = None
        self._running = False
        
        # Timing
        self._last_flush = datetime.now()
    
    async def start(self, process_callback: Callable[[List[Dict[str, Any]]], None]):
        """Start the batcher with processing callback"""
        self.process_callback = process_callback
        self._running = True
        self._task = asyncio.create_task(self._batch_loop())
        logger.info("Tick batcher started")
    
    async def stop(self):
        """Stop the batcher and flush remaining ticks"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining ticks
        await self._flush_all_batches()
        logger.info("Tick batcher stopped")
    
    async def add_tick(self, tick: Dict[str, Any]):
        """Add a tick to the appropriate batch"""
        if not self._running:
            return
        
        symbol = tick.get("symbol", "UNKNOWN")
        self.batches[symbol].append(tick)
        
        # Check if batch is full
        if len(self.batches[symbol]) >= self.batch_size:
            await self._flush_batch(symbol)
    
    async def _batch_loop(self):
        """Background loop for periodic flushing"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_all_batches()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch loop: {e}")
    
    async def _flush_all_batches(self):
        """Flush all batches that have data"""
        for symbol in list(self.batches.keys()):
            if self.batches[symbol]:
                await self._flush_batch(symbol)
    
    async def _flush_batch(self, symbol: str):
        """Flush batch for a specific symbol"""
        if not self.batches[symbol] or not self.process_callback:
            return
        
        batch = self.batches[symbol].copy()
        self.batches[symbol].clear()
        
        try:
            await self.process_callback(batch)
            logger.debug(f"Flushed batch for {symbol}: {len(batch)} ticks")
        except Exception as e:
            logger.error(f"Error processing batch for {symbol}: {e}")
        
        self._last_flush = datetime.now()
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """Get current batch statistics"""
        return {
            "batch_count": len(self.batches),
            "total_ticks": sum(len(batch) for batch in self.batches.values()),
            "last_flush": self._last_flush.isoformat(),
            "running": self._running
        }

# Global instance
tick_batcher = TickBatcher()
