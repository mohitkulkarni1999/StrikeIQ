#!/usr/bin/env python3
"""
Performance test script for StrikeIQ WebSocket optimizations
Tests high-frequency market data handling
"""

import asyncio
import time
import websockets
import json
from typing import Dict, List
import statistics

async def test_websocket_latency():
    """Test WebSocket broadcast latency with simulated high-frequency data"""
    
    print("🚀 Starting WebSocket Performance Test...")
    
    # Test parameters
    NUM_CLIENTS = 100  # Simulate 100 concurrent clients
    MESSAGES_PER_SECOND = 500  # 500 market ticks per second
    TEST_DURATION = 10  # 10 seconds
    
    latencies = []
    message_count = 0
    start_time = time.time()
    
    async def client_handler(client_id: int):
        """Handle individual WebSocket client"""
        uri = "ws://localhost:8000/ws/market"
        
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✅ Client {client_id} connected")
                
                # Subscribe to market data
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "symbol": "NIFTY",
                    "expiry": "2024-12-26"
                }))
                
                # Listen for messages
                while time.time() - start_time < TEST_DURATION:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        received_time = time.time()
                        
                        # Parse message and calculate latency
                        data = json.loads(message)
                        if 'timestamp' in data:
                            latency = (received_time - data['timestamp']) * 1000  # ms
                            latencies.append(latency)
                            message_count += 1
                            
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"❌ Client {client_id} error: {e}")
                        break
                        
        except Exception as e:
            print(f"❌ Client {client_id} failed to connect: {e}")
    
    # Start all clients
    tasks = []
    for i in range(NUM_CLIENTS):
        tasks.append(asyncio.create_task(client_handler(i)))
    
    # Simulate market data sender
    async def market_data_sender():
        """Send high-frequency market data"""
        uri = "ws://localhost:8000/ws/market"
        
        try:
            async with websockets.connect(uri) as websocket:
                while time.time() - start_time < TEST_DURATION:
                    # Send market tick
                    message = {
                        "type": "market_tick",
                        "data": {
                            "symbol": "NSE_INDEX|Nifty 50",
                            "ltp": 19850.25 + (time.time() % 100),
                            "timestamp": time.time()
                        }
                    }
                    
                    await websocket.send(json.dumps(message))
                    await asyncio.sleep(1.0 / MESSAGES_PER_SECOND)
                    
        except Exception as e:
            print(f"❌ Market data sender failed: {e}")
    
    # Start market data sender
    tasks.append(asyncio.create_task(market_data_sender()))
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Calculate performance metrics
    total_time = time.time() - start_time
    
    if latencies:
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        max_latency = max(latencies)
        min_latency = min(latencies)
    else:
        avg_latency = p95_latency = p99_latency = max_latency = min_latency = 0
    
    print("\n📊 PERFORMANCE RESULTS:")
    print(f"🔹 Test Duration: {total_time:.2f}s")
    print(f"🔹 Total Messages: {message_count}")
    print(f"🔹 Messages/Second: {message_count/total_time:.2f}")
    print(f"🔹 Concurrent Clients: {NUM_CLIENTS}")
    print(f"🔹 Average Latency: {avg_latency:.2f}ms")
    print(f"🔹 95th Percentile: {p95_latency:.2f}ms")
    print(f"🔹 99th Percentile: {p99_latency:.2f}ms")
    print(f"🔹 Max Latency: {max_latency:.2f}ms")
    print(f"🔹 Min Latency: {min_latency:.2f}ms")
    
    # Performance targets
    print("\n🎯 PERFORMANCE TARGETS:")
    print(f"✅ WebSocket Latency < 100ms: {'PASS' if avg_latency < 100 else 'FAIL'}")
    print(f"✅ 95th Percentile < 200ms: {'PASS' if p95_latency < 200 else 'FAIL'}")
    print(f"✅ 99th Percentile < 500ms: {'PASS' if p99_latency < 500 else 'FAIL'}")
    print(f"✅ Messages/Second > 1000: {'PASS' if message_count/total_time > 1000 else 'FAIL'}")
    
    # Calculate system stability score
    latency_score = max(0, 100 - (avg_latency / 100) * 50)  # 50% weight
    throughput_score = min(100, (message_count/total_time / 1000) * 50)  # 50% weight
    stability_score = (latency_score + throughput_score) / 2
    
    print(f"\n🏆 SYSTEM STABILITY SCORE: {stability_score:.1f}/100")
    
    return stability_score >= 80

if __name__ == "__main__":
    asyncio.run(test_websocket_latency())
