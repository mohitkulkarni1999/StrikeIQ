"""
High-Frequency WebSocket Ingestion Architecture
Safe separation of concerns with asyncio.Queue for each stage
"""

import asyncio
import logging
import websockets
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from ..dto.market_tick_dto import MarketTickDTO
from ..decoder.protobuf_decoder import ProtobufDecoder

logger = logging.getLogger(__name__)

@dataclass
class IngestionMetrics:
    """Metrics for monitoring ingestion performance"""
    ticks_received: int = 0
    ticks_decoded: int = 0
    ticks_processed: int = 0
    signals_broadcast: int = 0
    decode_errors: int = 0
    strategy_errors: int = 0
    broadcast_errors: int = 0
    
    # Queue sizes
    raw_queue_size: int = 0
    decoded_queue_size: int = 0
    signal_queue_size: int = 0
    
    # Timing metrics
    avg_decode_time_ms: float = 0.0
    avg_strategy_time_ms: float = 0.0
    avg_broadcast_time_ms: float = 0.0

class HighFrequencyIngestion:
    """
    High-frequency tick ingestion with complete separation of concerns
    Uses asyncio.Queue for each processing stage
    """
    
    def __init__(self, 
                 raw_queue_size: int = 10000,
                 decoded_queue_size: int = 5000,
                 signal_queue_size: int = 2000,
                 decode_workers: int = 4,
                 strategy_workers: int = 2,
                 broadcast_workers: int = 2):
        
        # Queue configuration
        self.raw_queue_size = raw_queue_size
        self.decoded_queue_size = decoded_queue_size
        self.signal_queue_size = signal_queue_size
        
        # Worker configuration
        self.decode_workers = decode_workers
        self.strategy_workers = strategy_workers
        self.broadcast_workers = broadcast_workers
        
        # Queues for each stage
        self.raw_binary_queue = asyncio.Queue(maxsize=raw_queue_size)
        self.decoded_tick_queue = asyncio.Queue(maxsize=decoded_queue_size)
        self.signal_queue = asyncio.Queue(maxsize=signal_queue_size)
        
        # Components
        self.decoder = ProtobufDecoder()
        self.thread_pool = ThreadPoolExecutor(max_workers=decode_workers + strategy_workers)
        
        # Strategy registration
        self.strategy_handlers: Dict[str, Callable] = {}
        
        # UI broadcast handlers
        self.broadcast_handlers: List[Callable] = []
        
        # Connection management
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        
        # Task management
        self.ingestion_task: Optional[asyncio.Task] = None
        self.decode_tasks: List[asyncio.Task] = []
        self.strategy_tasks: List[asyncio.Task] = []
        self.broadcast_tasks: List[asyncio.Task] = []
        
        # Control flags
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # Metrics
        self.metrics = IngestionMetrics()
        self.decode_times: List[float] = []
        self.strategy_times: List[float] = []
        self.broadcast_times: List[float] = []
        
    async def start_ingestion(self, websocket_url: str) -> bool:
        """
        Start the complete ingestion pipeline
        
        Args:
            websocket_url: Upstox V3 websocket URL
            
        Returns:
            bool: True if started successfully
        """
        try:
            logger.info("Starting high-frequency ingestion pipeline")
            
            # Connect to websocket
            self.websocket = await websockets.connect(
                websocket_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.is_connected = True
            
            # Reset shutdown event
            self.shutdown_event.clear()
            self.is_running = True
            
            # Start all pipeline stages
            await self._start_pipeline_stages()
            
            logger.info("High-frequency ingestion pipeline started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ingestion: {str(e)}")
            return False
    
    async def stop_ingestion(self):
        """Stop the ingestion pipeline gracefully"""
        logger.info("Stopping high-frequency ingestion pipeline")
        
        self.is_running = False
        self.shutdown_event.set()
        
        # Close websocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket: {str(e)}")
        
        self.is_connected = False
        
        # Wait for all tasks to complete
        all_tasks = (
            [self.ingestion_task] + 
            self.decode_tasks + 
            self.strategy_tasks + 
            self.broadcast_tasks
        )
        
        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        logger.info("High-frequency ingestion pipeline stopped")
    
    async def _start_pipeline_stages(self):
        """Start all pipeline stages"""
        # Stage 1: Ingestion loop
        self.ingestion_task = asyncio.create_task(self._ingestion_loop())
        
        # Stage 2: Decode workers
        for i in range(self.decode_workers):
            task = asyncio.create_task(self._decode_worker(f"decoder_{i}"))
            self.decode_tasks.append(task)
        
        # Stage 3: Strategy execution workers
        for i in range(self.strategy_workers):
            task = asyncio.create_task(self._strategy_worker(f"strategy_{i}"))
            self.strategy_tasks.append(task)
        
        # Stage 4: Broadcast workers
        for i in range(self.broadcast_workers):
            task = asyncio.create_task(self._broadcast_worker(f"broadcast_{i}"))
            self.broadcast_tasks.append(task)
    
    # 1. INGESTION LOOP
    async def _ingestion_loop(self):
        """
        Stage 1: WebSocket ingestion loop
        Receives binary data and queues for decoding
        """
        logger.info("Starting ingestion loop")
        
        while self.is_running and self.is_connected:
            try:
                # Receive binary message with timeout
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=30.0
                )
                
                # Queue raw binary data
                success = await self._queue_raw_binary(message)
                if not success:
                    logger.warning("Raw binary queue full, dropping message")
                
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Error in ingestion loop: {str(e)}")
                break
        
        self.is_connected = False
        logger.info("Ingestion loop ended")
    
    async def _queue_raw_binary(self, binary_data: bytes) -> bool:
        """
        Queue raw binary data for decoding
        
        Args:
            binary_data: Raw binary protobuf data
            
        Returns:
            bool: True if queued successfully
        """
        try:
            message_data = {
                'binary_data': binary_data,
                'received_at': datetime.now(timezone.utc),
                'message_id': f"raw_{self.metrics.ticks_received}"
            }
            
            await self.raw_binary_queue.put(message_data)
            self.metrics.ticks_received += 1
            return True
            
        except asyncio.QueueFull:
            return False
    
    # 2. DECODE WORKER
    async def _decode_worker(self, worker_name: str):
        """
        Stage 2: Decode worker
        Processes binary data to MarketTickDTO
        """
        logger.info(f"Starting decode worker: {worker_name}")
        
        while self.is_running:
            try:
                # Get raw binary data
                raw_data = await asyncio.wait_for(
                    self.raw_binary_queue.get(),
                    timeout=1.0
                )
                
                # Decode protobuf (non-blocking)
                start_time = datetime.now()
                decode_result = await self.decoder.decode_binary_message(
                    raw_data['binary_data'],
                    raw_data['message_id']
                )
                
                # Update timing metrics
                decode_time = (datetime.now() - start_time).total_seconds() * 1000
                self.decode_times.append(decode_time)
                if len(self.decode_times) > 1000:
                    self.decode_times = self.decode_times[-1000:]
                
                if decode_result.success:
                    # Queue decoded tick
                    await self._queue_decoded_tick(decode_result.tick_dto)
                    self.metrics.ticks_decoded += 1
                else:
                    self.metrics.decode_errors += 1
                    logger.error(f"Decode failed: {decode_result.error}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in decode worker {worker_name}: {str(e)}")
                await asyncio.sleep(0.01)
        
        logger.info(f"Decode worker {worker_name} ended")
    
    async def _queue_decoded_tick(self, tick_dto: MarketTickDTO) -> bool:
        """
        Queue decoded tick for strategy processing
        
        Args:
            tick_dto: Decoded market tick DTO
            
        Returns:
            bool: True if queued successfully
        """
        try:
            tick_data = {
                'tick': tick_dto,
                'decoded_at': datetime.now(timezone.utc)
            }
            
            await self.decoded_tick_queue.put(tick_data)
            return True
            
        except asyncio.QueueFull:
            logger.warning(f"Decoded tick queue full, dropping {tick_dto.instrument_key}")
            return False
    
    # 3. STRATEGY EXECUTION LOOP
    async def _strategy_worker(self, worker_name: str):
        """
        Stage 3: Strategy execution worker
        Processes ticks through registered strategies
        """
        logger.info(f"Starting strategy worker: {worker_name}")
        
        while self.is_running:
            try:
                # Get decoded tick
                tick_data = await asyncio.wait_for(
                    self.decoded_tick_queue.get(),
                    timeout=1.0
                )
                
                tick_dto = tick_data['tick']
                
                # Execute strategies
                start_time = datetime.now()
                signals = await self._execute_strategies(tick_dto)
                strategy_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Update timing metrics
                self.strategy_times.append(strategy_time)
                if len(self.strategy_times) > 1000:
                    self.strategy_times = self.strategy_times[-1000:]
                
                # Queue signals for broadcast
                if signals:
                    await self._queue_signals(signals, tick_dto)
                
                self.metrics.ticks_processed += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in strategy worker {worker_name}: {str(e)}")
                self.metrics.strategy_errors += 1
                await asyncio.sleep(0.01)
        
        logger.info(f"Strategy worker {worker_name} ended")
    
    async def _execute_strategies(self, tick_dto: MarketTickDTO) -> List[Dict[str, Any]]:
        """
        Execute all registered strategies on tick
        
        Args:
            tick_dto: Market tick DTO
            
        Returns:
            List of strategy signals
        """
        signals = []
        
        # Execute all strategies concurrently
        strategy_tasks = []
        for strategy_name, handler in self.strategy_handlers.items():
            if asyncio.iscoroutinefunction(handler):
                task = asyncio.create_task(
                    self._execute_async_strategy(strategy_name, handler, tick_dto)
                )
            else:
                task = asyncio.create_task(
                    self._execute_sync_strategy(strategy_name, handler, tick_dto)
                )
            strategy_tasks.append(task)
        
        if strategy_tasks:
            try:
                # Wait for all strategies with timeout
                results = await asyncio.wait_for(
                    asyncio.gather(*strategy_tasks, return_exceptions=True),
                    timeout=2.0  # 2 second timeout for all strategies
                )
                
                # Collect signals from successful strategies
                for i, result in enumerate(results):
                    if not isinstance(result, Exception) and result:
                        signals.append({
                            'strategy': list(self.strategy_handlers.keys())[i],
                            'signal': result,
                            'tick': tick_dto,
                            'timestamp': datetime.now(timezone.utc)
                        })
                        
            except asyncio.TimeoutError:
                logger.warning(f"Strategy execution timeout for {tick_dto.instrument_key}")
        
        return signals
    
    async def _execute_async_strategy(self, strategy_name: str, handler: Callable, tick_dto: MarketTickDTO):
        """Execute async strategy safely"""
        try:
            return await handler(tick_dto)
        except Exception as e:
            logger.error(f"Async strategy {strategy_name} failed: {str(e)}")
            return None
    
    async def _execute_sync_strategy(self, strategy_name: str, handler: Callable, tick_dto: MarketTickDTO):
        """Execute sync strategy in thread pool"""
        try:
            return await asyncio.to_thread(handler, tick_dto)
        except Exception as e:
            logger.error(f"Sync strategy {strategy_name} failed: {str(e)}")
            return None
    
    async def _queue_signals(self, signals: List[Dict[str, Any]], tick_dto: MarketTickDTO):
        """
        Queue strategy signals for UI broadcast
        
        Args:
            signals: List of strategy signals
            tick_dto: Original tick DTO
        """
        try:
            signal_data = {
                'signals': signals,
                'tick': tick_dto,
                'generated_at': datetime.now(timezone.utc)
            }
            
            await self.signal_queue.put(signal_data)
            
        except asyncio.QueueFull:
            logger.warning(f"Signal queue full, dropping signals for {tick_dto.instrument_key}")
    
    # 4. EVENT BROADCAST LAYER
    async def _broadcast_worker(self, worker_name: str):
        """
        Stage 4: Broadcast worker
        Sends signals to UI clients
        """
        logger.info(f"Starting broadcast worker: {worker_name}")
        
        while self.is_running:
            try:
                # Get signals to broadcast
                signal_data = await asyncio.wait_for(
                    self.signal_queue.get(),
                    timeout=1.0
                )
                
                # Broadcast to all UI handlers
                start_time = datetime.now()
                await self._broadcast_to_ui(signal_data)
                broadcast_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Update timing metrics
                self.broadcast_times.append(broadcast_time)
                if len(self.broadcast_times) > 1000:
                    self.broadcast_times = self.broadcast_times[-1000:]
                
                self.metrics.signals_broadcast += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in broadcast worker {worker_name}: {str(e)}")
                self.metrics.broadcast_errors += 1
                await asyncio.sleep(0.01)
        
        logger.info(f"Broadcast worker {worker_name} ended")
    
    async def _broadcast_to_ui(self, signal_data: Dict[str, Any]):
        """
        Broadcast signals to all registered UI handlers
        
        Args:
            signal_data: Signals and metadata to broadcast
        """
        broadcast_tasks = []
        
        for handler in self.broadcast_handlers:
            if asyncio.iscoroutinefunction(handler):
                task = asyncio.create_task(handler(signal_data))
            else:
                task = asyncio.create_task(asyncio.to_thread(handler, signal_data))
            broadcast_tasks.append(task)
        
        if broadcast_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*broadcast_tasks, return_exceptions=True),
                    timeout=1.0  # 1 second timeout for all broadcasts
                )
            except asyncio.TimeoutError:
                logger.warning("UI broadcast timeout")
    
    # 5. ASYNC TASK ORCHESTRATION
    def register_strategy(self, strategy_name: str, handler: Callable):
        """Register a strategy handler"""
        self.strategy_handlers[strategy_name] = handler
        logger.info(f"Registered strategy: {strategy_name}")
    
    def unregister_strategy(self, strategy_name: str):
        """Unregister a strategy handler"""
        if strategy_name in self.strategy_handlers:
            del self.strategy_handlers[strategy_name]
            logger.info(f"Unregistered strategy: {strategy_name}")
    
    def register_broadcast_handler(self, handler: Callable):
        """Register a UI broadcast handler"""
        self.broadcast_handlers.append(handler)
        logger.info(f"Registered broadcast handler: {len(self.broadcast_handlers)} total")
    
    def unregister_broadcast_handler(self, handler: Callable):
        """Unregister a UI broadcast handler"""
        if handler in self.broadcast_handlers:
            self.broadcast_handlers.remove(handler)
            logger.info(f"Unregistered broadcast handler: {len(self.broadcast_handlers)} total")
    
    def get_metrics(self) -> IngestionMetrics:
        """Get current ingestion metrics"""
        # Update queue sizes
        self.metrics.raw_queue_size = self.raw_binary_queue.qsize()
        self.metrics.decoded_queue_size = self.decoded_tick_queue.qsize()
        self.metrics.signal_queue_size = self.signal_queue.qsize()
        
        # Calculate averages
        if self.decode_times:
            self.metrics.avg_decode_time_ms = sum(self.decode_times) / len(self.decode_times)
        if self.strategy_times:
            self.metrics.avg_strategy_time_ms = sum(self.strategy_times) / len(self.strategy_times)
        if self.broadcast_times:
            self.metrics.avg_broadcast_time_ms = sum(self.broadcast_times) / len(self.broadcast_times)
        
        return self.metrics
    
    def is_healthy(self) -> bool:
        """Check if ingestion pipeline is healthy"""
        if not self.is_running or not self.is_connected:
            return False
        
        # Check queue utilization
        raw_util = self.raw_binary_queue.qsize() / self.raw_queue_size
        decoded_util = self.decoded_tick_queue.qsize() / self.decoded_queue_size
        signal_util = self.signal_queue.qsize() / self.signal_queue_size
        
        # Healthy if all queues < 80% full
        return all(util < 0.8 for util in [raw_util, decoded_util, signal_util])
