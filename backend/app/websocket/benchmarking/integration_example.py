"""
Integration Example
Demonstrates how to integrate latency benchmarking into existing pipeline
"""

import asyncio
import logging
from typing import Dict, Any

from . import (
    initialize_latency_tracking,
    shutdown_latency_tracking,
    websocket_instrumentation,
    raw_queue_instrumentation,
    decoded_queue_instrumentation,
    signal_queue_instrumentation,
    protobuf_decode,
    dto_mapping,
    strategy_execution,
    signal_generation,
    ui_broadcast,
    measure_latency,
    create_instrumented_tick,
    get_tick_id
)

logger = logging.getLogger(__name__)

class BenchmarkingIntegrationExample:
    """
    Example of integrating benchmarking into existing tick processing pipeline
    Shows how to wrap existing functions without modifying business logic
    """
    
    def __init__(self):
        self.raw_queue = asyncio.Queue(maxsize=10000)
        self.decoded_queue = asyncio.Queue(maxsize=5000)
        self.signal_queue = asyncio.Queue(maxsize=2000)
        
        # Initialize benchmarking system
        initialize_latency_tracking(sampling_rate=10, latency_threshold_ms=50.0)
    
    async def shutdown(self):
        """Shutdown the system"""
        shutdown_latency_tracking()
    
    # Example: Wrap existing WebSocket receive function
    async def websocket_receive_wrapper(self, websocket_data: bytes) -> Dict[str, Any]:
        """
        Wrapper for WebSocket receive - no changes to original logic
        """
        # Instrument the message
        instrumented_message = websocket_instrumentation.instrument_websocket_message(websocket_data)
        
        # Original logic (unchanged)
        processed_data = self._original_websocket_processing(instrumented_message['data'])
        
        # Add tick_id to processed data
        processed_data['tick_id'] = instrumented_message['tick_id']
        
        return processed_data
    
    def _original_websocket_processing(self, data: bytes) -> Dict[str, Any]:
        """Original WebSocket processing logic (unchanged)"""
        # This is your existing WebSocket processing code
        return {
            'binary_data': data,
            'message_id': f"msg_{hash(data) % 10000}",
            'received_at': asyncio.get_event_loop().time()
        }
    
    # Example: Wrap existing decode function
    @protobuf_decode
    async def decode_wrapper(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper for protobuf decode - decorator handles instrumentation
        """
        tick_id = message_data.get('tick_id')
        
        # Original decode logic (unchanged)
        decoded_data = await self._original_decode_logic(message_data['binary_data'])
        
        # Add tick_id for tracking
        decoded_data['tick_id'] = tick_id
        
        return decoded_data
    
    async def _original_decode_logic(self, binary_data: bytes) -> Dict[str, Any]:
        """Original decode logic (unchanged)"""
        # Simulate protobuf decoding
        await asyncio.sleep(0.001)  # 1ms decode time
        
        return {
            'instrument_key': 'NIFTY-25000-CE',
            'last_price': 250.50,
            'volume': 1000,
            'decoded_at': asyncio.get_event_loop().time()
        }
    
    # Example: Wrap existing DTO mapping
    @dto_mapping
    async def dto_mapping_wrapper(self, decoded_data: Dict[str, Any]) -> Any:
        """
        Wrapper for DTO mapping - decorator handles instrumentation
        """
        tick_id = decoded_data.get('tick_id')
        
        # Original DTO mapping logic (unchanged)
        dto_object = await self._original_dto_mapping(decoded_data)
        
        # Add tick_id for tracking
        if hasattr(dto_object, '__dict__'):
            dto_object.tick_id = tick_id
        
        return dto_object
    
    async def _original_dto_mapping(self, decoded_data: Dict[str, Any]) -> Any:
        """Original DTO mapping logic (unchanged)"""
        # Simulate DTO mapping
        await asyncio.sleep(0.0005)  # 0.5ms mapping time
        
        # Return a simple object (in real code, this would be your MarketTickDTO)
        class MockDTO:
            def __init__(self, data):
                self.instrument_key = data.get('instrument_key')
                self.last_price = data.get('last_price')
                self.volume = data.get('volume')
        
        return MockDTO(decoded_data)
    
    # Example: Wrap existing strategy execution
    @strategy_execution
    async def strategy_execution_wrapper(self, dto_object: Any) -> Dict[str, Any]:
        """
        Wrapper for strategy execution - decorator handles instrumentation
        """
        tick_id = getattr(dto_object, 'tick_id', None)
        
        # Original strategy logic (unchanged)
        signals = await self._original_strategy_execution(dto_object)
        
        # Add tick_id to signals
        signals['tick_id'] = tick_id
        
        return signals
    
    async def _original_strategy_execution(self, dto_object: Any) -> Dict[str, Any]:
        """Original strategy execution logic (unchanged)"""
        # Simulate strategy execution
        await asyncio.sleep(0.005)  # 5ms strategy time
        
        return {
            'signals': [
                {'type': 'buy', 'strength': 0.8},
                {'type': 'momentum', 'strength': 0.6}
            ],
            'executed_at': asyncio.get_event_loop().time()
        }
    
    # Example: Wrap existing signal generation
    @signal_generation
    async def signal_generation_wrapper(self, strategy_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper for signal generation - decorator handles instrumentation
        """
        tick_id = strategy_result.get('tick_id')
        
        # Original signal generation logic (unchanged)
        broadcast_data = await self._original_signal_generation(strategy_result)
        
        # Add tick_id for tracking
        broadcast_data['tick_id'] = tick_id
        
        return broadcast_data
    
    async def _original_signal_generation(self, strategy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Original signal generation logic (unchanged)"""
        # Simulate signal generation
        await asyncio.sleep(0.002)  # 2ms signal generation time
        
        return {
            'broadcast_data': strategy_result['signals'],
            'format': 'ui_ready',
            'generated_at': asyncio.get_event_loop().time()
        }
    
    # Example: Wrap existing UI broadcast
    @ui_broadcast
    async def ui_broadcast_wrapper(self, broadcast_data: Dict[str, Any]) -> None:
        """
        Wrapper for UI broadcast - decorator handles instrumentation
        """
        tick_id = broadcast_data.get('tick_id')
        
        # Original broadcast logic (unchanged)
        await self._original_ui_broadcast(broadcast_data)
        
        # No return needed for broadcast
    
    async def _original_ui_broadcast(self, broadcast_data: Dict[str, Any]) -> None:
        """Original UI broadcast logic (unchanged)"""
        # Simulate UI broadcast
        await asyncio.sleep(0.001)  # 1ms broadcast time
        
        # In real code, this would send to WebSocket clients
        logger.debug(f"Broadcasting to UI: {broadcast_data['broadcast_data']}")
    
    # Example: Complete pipeline integration
    async def process_tick_with_benchmarking(self, websocket_data: bytes) -> None:
        """
        Complete tick processing with benchmarking
        Shows how all stages work together
        """
        try:
            # Stage 1: WebSocket receive (instrumented)
            message_data = await self.websocket_receive_wrapper(websocket_data)
            tick_id = message_data['tick_id']
            
            # Stage 2: Queue to decode (instrumented)
            await raw_queue_instrumentation.put_with_tracking(
                self.raw_queue, message_data, tick_id
            )
            
            # Stage 3: Decode (instrumented)
            queued_message = await raw_queue_instrumentation.get_with_tracking(self.raw_queue)
            decoded_data = await self.decode_wrapper(queued_message)
            
            # Stage 4: Queue to strategy (instrumented)
            await decoded_queue_instrumentation.put_with_tracking(
                self.decoded_queue, decoded_data, tick_id
            )
            
            # Stage 5: DTO mapping (instrumented)
            queued_decoded = await decoded_queue_instrumentation.get_with_tracking(self.decoded_queue)
            dto_object = await self.dto_mapping_wrapper(queued_decoded)
            
            # Stage 6: Strategy execution (instrumented)
            strategy_result = await self.strategy_execution_wrapper(dto_object)
            
            # Stage 7: Queue to broadcast (instrumented)
            await signal_queue_instrumentation.put_with_tracking(
                self.signal_queue, strategy_result, tick_id
            )
            
            # Stage 8: Signal generation (instrumented)
            queued_signal = await signal_queue_instrumentation.get_with_tracking(self.signal_queue)
            broadcast_data = await self.signal_generation_wrapper(queued_signal)
            
            # Stage 9: UI broadcast (instrumented)
            await self.ui_broadcast_wrapper(broadcast_data)
            
            logger.debug(f"Successfully processed tick {tick_id} with benchmarking")
            
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
            # Benchmarking automatically tracks the error timing
    
    # Example: Custom measurement with context manager
    @measure_latency("custom_processing")
    async def custom_processing_step(self, data: Any, tick_id: str = None) -> Any:
        """
        Example of using the measure_latency decorator
        """
        # Custom processing logic
        await asyncio.sleep(0.003)  # 3ms processing time
        
        return {
            'processed_data': data,
            'custom_result': 'success'
        }
    
    # Example: Ad-hoc latency measurement
    async def ad_hoc_measurement_example(self, data: Any) -> Any:
        """
        Example of using context manager for ad-hoc measurements
        """
        from . import LatencyContextManager, get_latency_tracker
        
        tracker = get_latency_tracker()
        tick_id = tracker.create_tick_id()
        
        with LatencyContextManager("ad_hoc_operation", tick_id):
            # Your custom operation here
            await asyncio.sleep(0.004)  # 4ms operation
            
            return {
                'result': 'success',
                'tick_id': tick_id
            }

# Example usage
async def main_example():
    """Example of how to use the benchmarking integration"""
    
    # Initialize the system
    system = BenchmarkingIntegrationExample()
    
    try:
        # Simulate processing some ticks
        for i in range(100):
            # Simulate WebSocket data
            websocket_data = f"tick_data_{i}".encode()
            
            # Process with full benchmarking
            await system.process_tick_with_benchmarking(websocket_data)
            
            # Small delay between ticks
            await asyncio.sleep(0.01)
        
        # Get performance reports
        from . import get_latency_tracker
        
        tracker = get_latency_tracker()
        
        # Percentile report
        percentile_report = tracker.get_percentile_report()
        print("Percentile Report:")
        print(f"P50: {percentile_report.get('percentiles_ms', {}).get('total_end_to_end', {}).get('p50', 0):.2f}ms")
        print(f"P90: {percentile_report.get('percentiles_ms', {}).get('total_end_to_end', {}).get('p90', 0):.2f}ms")
        print(f"P99: {percentile_report.get('percentiles_ms', {}).get('total_end_to_end', {}).get('p99', 0):.2f}ms")
        
        # Decode vs Strategy comparison
        comparison = tracker.get_decode_vs_strategy_comparison()
        print("\nDecode vs Strategy Comparison:")
        print(f"Decode mean: {comparison.get('decode_performance', {}).get('mean_ms', 0):.2f}ms")
        print(f"Strategy mean: {comparison.get('strategy_performance', {}).get('mean_ms', 0):.2f}ms")
        print(f"Faster stage: {comparison.get('comparison', {}).get('faster_stage', 'unknown')}")
        
        # Export metrics
        tracker.export_metrics("latency_report.json")
        
    finally:
        # Cleanup
        await system.shutdown()

if __name__ == "__main__":
    asyncio.run(main_example())
