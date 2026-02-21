"""
Tick Processor
Handles async tick processing without blocking event loop
"""

import asyncio
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime, timezone

from ..dto.market_tick_dto import MarketTickDTO

logger = logging.getLogger(__name__)

class TickProcessor:
    """
    Non-blocking tick processor for strategy execution
    Processes decoded ticks without blocking websocket ingestion
    """
    
    def __init__(self, strategy_handlers: Dict[str, Callable] = None):
        self.strategy_handlers = strategy_handlers or {}
        self.processing_queue = asyncio.Queue(maxsize=5000)
        
        # Statistics
        self.ticks_processed = 0
        self.ticks_failed = 0
        self.processing_time_total_ms = 0.0
        self.strategies_executed = 0
        
        # Control flags
        self.is_running = False
        self.processor_task: Optional[asyncio.Task] = None
        
    async def start_processing(self):
        """Start the tick processor"""
        if self.is_running:
            logger.warning("Tick processor already running")
            return
            
        self.is_running = True
        self.processor_task = asyncio.create_task(self._processing_loop())
        logger.info("Tick processor started")
    
    async def stop_processing(self):
        """Stop the tick processor"""
        self.is_running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Tick processor stopped")
    
    async def process_tick(self, tick_dto: MarketTickDTO) -> bool:
        """
        Queue tick for processing
        
        Args:
            tick_dto: Decoded market tick DTO
            
        Returns:
            bool: True if successfully queued, False if queue full
        """
        try:
            await self.processing_queue.put({
                'tick': tick_dto,
                'queued_at': datetime.now(timezone.utc)
            })
            return True
            
        except asyncio.QueueFull:
            self.ticks_failed += 1
            logger.warning(f"Processing queue full, dropping tick for {tick_dto.instrument_key}")
            return False
    
    async def _processing_loop(self):
        """Main processing loop - executes strategies"""
        logger.info("Starting tick processing loop")
        
        while self.is_running:
            try:
                # Get tick from processing queue
                tick_data = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=0.1  # 100ms timeout
                )
                
                # Process tick with all registered strategies
                await self._execute_strategies(tick_data['tick'])
                
                self.ticks_processed += 1
                
            except asyncio.TimeoutError:
                # No ticks to process, continue
                continue
                
            except asyncio.CancelledError:
                logger.info("Tick processing loop cancelled")
                break
                
            except Exception as e:
                self.ticks_failed += 1
                logger.error(f"Error processing tick: {str(e)}")
                await asyncio.sleep(0.01)  # Prevent tight error loop
        
        logger.info("Tick processing loop ended")
    
    async def _execute_strategies(self, tick_dto: MarketTickDTO):
        """
        Execute all registered strategies on tick
        
        Args:
            tick_dto: Decoded market tick DTO
        """
        start_time = datetime.now()
        
        # Execute all strategy handlers concurrently
        strategy_tasks = []
        
        for strategy_name, handler in self.strategy_handlers.items():
            try:
                # Create task for each strategy
                task = asyncio.create_task(
                    self._execute_strategy_safe(strategy_name, handler, tick_dto)
                )
                strategy_tasks.append(task)
                
            except Exception as e:
                logger.error(f"Error creating strategy task {strategy_name}: {str(e)}")
        
        if strategy_tasks:
            # Wait for all strategies to complete or timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*strategy_tasks, return_exceptions=True),
                    timeout=1.0  # 1 second timeout for all strategies
                )
                self.strategies_executed += len(strategy_tasks)
                
            except asyncio.TimeoutError:
                logger.warning(f"Strategy execution timeout for tick {tick_dto.instrument_key}")
        
        # Update processing statistics
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        self.processing_time_total_ms += processing_time
    
    async def _execute_strategy_safe(self, strategy_name: str, handler: Callable, tick_dto: MarketTickDTO):
        """
        Safely execute a single strategy
        
        Args:
            strategy_name: Name of the strategy
            handler: Strategy handler function
            tick_dto: Market tick DTO
        """
        try:
            # Run strategy handler in thread pool if it's CPU intensive
            if asyncio.iscoroutinefunction(handler):
                await handler(tick_dto)
            else:
                await asyncio.to_thread(handler, tick_dto)
                
        except Exception as e:
            logger.error(f"Strategy {strategy_name} failed on tick {tick_dto.instrument_key}: {str(e)}")
    
    def register_strategy(self, strategy_name: str, handler: Callable):
        """
        Register a strategy handler
        
        Args:
            strategy_name: Name of the strategy
            handler: Strategy handler function (sync or async)
        """
        self.strategy_handlers[strategy_name] = handler
        logger.info(f"Registered strategy: {strategy_name}")
    
    def unregister_strategy(self, strategy_name: str):
        """
        Unregister a strategy handler
        
        Args:
            strategy_name: Name of the strategy to remove
        """
        if strategy_name in self.strategy_handlers:
            del self.strategy_handlers[strategy_name]
            logger.info(f"Unregistered strategy: {strategy_name}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processor statistics"""
        avg_processing_time = (
            self.processing_time_total_ms / max(self.ticks_processed, 1)
        )
        
        return {
            'ticks_processed': self.ticks_processed,
            'ticks_failed': self.ticks_failed,
            'success_rate': (
                self.ticks_processed / max(self.ticks_processed + self.ticks_failed, 1)
            ),
            'strategies_registered': len(self.strategy_handlers),
            'strategies_executed': self.strategies_executed,
            'average_processing_time_ms': avg_processing_time,
            'total_processing_time_ms': self.processing_time_total_ms,
            'queue_size': self.processing_queue.qsize(),
            'queue_capacity': self.processing_queue.maxsize
        }
    
    async def clear_processing_queue(self):
        """Clear all pending ticks from processing queue"""
        cleared_count = 0
        
        while not self.processing_queue.empty():
            try:
                self.processing_queue.get_nowait()
                cleared_count += 1
            except asyncio.QueueEmpty:
                break
        
        logger.info(f"Cleared {cleared_count} ticks from processing queue")
