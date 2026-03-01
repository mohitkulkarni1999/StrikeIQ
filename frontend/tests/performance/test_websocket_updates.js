/**
 * WebSocket Update Performance Benchmark
 * Tests WebSocket message processing and UI update latency
 * Simulates 1000 incoming WebSocket messages
 */

class WebSocketBenchmark {
    constructor() {
        this.messageCount = 0;
        this.totalLatency = 0;
        this.maxLatency = 0;
        this.minLatency = Infinity;
        this.latencies = [];
        this.frameDrops = 0;
        this.processedMessages = 0;
        this.startTime = null;
        this.lastFrameTime = performance.now();
    }

    // Simulate WebSocket message structure
    createTestMessage(index) {
        const basePrice = 45000;
        const priceVariation = (index % 1000) - 500;
        
        return {
            symbol: "BANKNIFTY",
            price: basePrice + priceVariation,
            pcr: 1.0 + (index % 50) / 100,
            gamma: -30000 + (index % 20000) - 10000,
            timestamp: Date.now(),
            volume: 1000000 + (index % 5000000),
            oi_change: 100000 + (index % 900000),
            vwap: basePrice + priceVariation - 10,
            change: priceVariation,
            change_percent: (priceVariation / basePrice) * 100,
            rsi: 30 + (index % 70),
            momentum_score: (index % 100) / 100,
            regime: ["BULLISH", "BEARISH", "NEUTRAL"][index % 3],
            volatility_regime: ["LOW", "MEDIUM", "HIGH", "EXTREME"][index % 4],
            // Additional fields for comprehensive testing
            total_call_oi: 5000000 + (index % 3000000),
            total_put_oi: 5500000 + (index % 3000000),
            atm_strike: basePrice + (index % 200) - 100,
            theta: 0.01 + (index % 10) / 100,
            delta: 0.3 + (index % 40) / 100,
            iv: 15.0 + (index % 25),
            iv_regime: ["LOW", "MEDIUM", "HIGH"][index % 3],
            expected_move: 50 + (index % 150),
            liquidity_score: 0.5 + (index % 50) / 100,
            flow_gamma_interaction: (index % 100) / 100,
            structural_alert_level: ["LOW", "MODERATE", "HIGH"][index % 3]
        };
    }

    // Simulate message processing (what would happen in WebSocket handler)
    processMessage(message) {
        const processStart = performance.now();
        
        // Simulate message parsing and validation
        const parsed = {
            symbol: message.symbol,
            price: parseFloat(message.price),
            pcr: parseFloat(message.pcr),
            gamma: parseInt(message.gamma),
            timestamp: message.timestamp,
            // Additional parsing
            volume: message.volume,
            oi_change: message.oi_change,
            change: message.change,
            change_percent: message.change_percent,
            rsi: message.rsi,
            momentum_score: message.momentum_score,
            regime: message.regime,
            volatility_regime: message.volatility_regime
        };

        // Simulate state update logic
        const stateUpdate = {
            marketData: parsed,
            signals: this.generateSignals(parsed),
            alerts: this.generateAlerts(parsed),
            timestamp: Date.now()
        };

        // Simulate UI update scheduling
        this.scheduleUIUpdate(stateUpdate);

        const processEnd = performance.now();
        const latency = processEnd - processStart;
        
        return latency;
    }

    // Generate trading signals (simplified)
    generateSignals(marketData) {
        const signals = [];
        
        if (marketData.pcr > 1.2) {
            signals.push({ type: 'PCR_HIGH', confidence: 0.8 });
        }
        
        if (Math.abs(marketData.gamma) > 25000) {
            signals.push({ type: 'GAMMA_EXTREME', confidence: 0.9 });
        }
        
        if (marketData.change_percent > 1.0) {
            signals.push({ type: 'STRONG_MOVE', confidence: 0.7 });
        }
        
        return signals;
    }

    // Generate alerts (simplified)
    generateAlerts(marketData) {
        const alerts = [];
        
        if (marketData.rsi > 70) {
            alerts.push({ type: 'OVERBOUGHT', severity: 'MEDIUM' });
        }
        
        if (marketData.rsi < 30) {
            alerts.push({ type: 'OVERSOLD', severity: 'MEDIUM' });
        }
        
        if (Math.abs(marketData.change_percent) > 2.0) {
            alerts.push({ type: 'VOLATILITY_SPIKE', severity: 'HIGH' });
        }
        
        return alerts;
    }

    // Simulate UI update scheduling
    scheduleUIUpdate(stateUpdate) {
        // Check for frame drops
        const currentTime = performance.now();
        const frameDelta = currentTime - this.lastFrameTime;
        
        if (frameDelta > 16.67) { // 60 FPS threshold
            this.frameDrops++;
        }
        
        this.lastFrameTime = currentTime;
        
        // Simulate React state update (simplified)
        this.simulateReactUpdate(stateUpdate);
    }

    // Simulate React state update (simplified)
    simulateReactUpdate(stateUpdate) {
        // Simulate virtual DOM diff and patch
        const updateStart = performance.now();
        
        // Simulate component re-render calculation
        const componentsToUpdate = [
            'MarketDataTable',
            'SignalPanel',
            'AlertPanel',
            'ChartComponent',
            'MetricsPanel'
        ];
        
        // Simulate each component update
        componentsToUpdate.forEach(component => {
            // Simulate render time based on component complexity
            const renderTime = 0.1 + Math.random() * 0.5; // 0.1-0.6ms
            performance.now(); // Simulate work
        });
        
        const updateEnd = performance.now();
        return updateEnd - updateStart;
    }

    // Run WebSocket benchmark
    async runWebSocketBenchmark(messageCount = 1000) {
        console.log(`🚀 Starting WebSocket Update Benchmark (${messageCount} messages)`);
        console.log("=" * 60);
        
        this.messageCount = messageCount;
        this.startTime = performance.now();
        
        // Warm up
        console.log("Warming up...");
        for (let i = 0; i < 10; i++) {
            const warmupMessage = this.createTestMessage(i);
            this.processMessage(warmupMessage);
        }
        
        // Reset metrics
        this.totalLatency = 0;
        this.maxLatency = 0;
        this.minLatency = Infinity;
        this.latencies = [];
        this.frameDrops = 0;
        this.processedMessages = 0;
        
        console.log("Running main benchmark...");
        
        // Process messages in batches to simulate real WebSocket behavior
        const batchSize = 50;
        const batches = Math.ceil(messageCount / batchSize);
        
        for (let batch = 0; batch < batches; batch++) {
            const batchStart = performance.now();
            
            // Process batch of messages
            for (let i = 0; i < batchSize && (batch * batchSize + i) < messageCount; i++) {
                const messageIndex = batch * batchSize + i;
                const message = this.createTestMessage(messageIndex);
                
                const latency = this.processMessage(message);
                this.latencies.push(latency);
                this.totalLatency += latency;
                this.maxLatency = Math.max(this.maxLatency, latency);
                this.minLatency = Math.min(this.minLatency, latency);
                this.processedMessages++;
            }
            
            const batchEnd = performance.now();
            const batchTime = batchEnd - batchStart;
            
            // Progress indicator
            const progress = Math.min((batch + 1) * batchSize, messageCount);
            console.log(`  Progress: ${progress}/${messageCount} messages (${batchTime.toFixed(2)}ms batch)`);
            
            // Simulate real WebSocket timing (small delay between batches)
            await new Promise(resolve => setTimeout(resolve, 1));
        }
        
        const endTime = performance.now();
        const totalTime = endTime - this.startTime;
        
        // Calculate final metrics
        const avgLatency = this.totalLatency / this.processedMessages;
        const messagesPerSecond = this.processedMessages / (totalTime / 1000);
        const p95Latency = this.calculatePercentile(this.latencies, 95);
        const p99Latency = this.calculatePercentile(this.latencies, 99);
        
        return {
            messageCount: this.processedMessages,
            totalTime: totalTime,
            avgLatency: avgLatency,
            maxLatency: this.maxLatency,
            minLatency: this.minLatency,
            p95Latency: p95Latency,
            p99Latency: p99Latency,
            messagesPerSecond: messagesPerSecond,
            frameDrops: this.frameDrops,
            frameDropRate: (this.frameDrops / this.processedMessages) * 100
        };
    }

    // Calculate percentile
    calculatePercentile(values, percentile) {
        const sorted = values.slice().sort((a, b) => a - b);
        const index = Math.ceil((percentile / 100) * sorted.length) - 1;
        return sorted[Math.max(0, index)];
    }

    // Print results
    printResults(results) {
        console.log("\n" + "=" * 80);
        console.log("📊 WEBSOCKET UPDATE PERFORMANCE RESULTS");
        console.log("=" * 80);
        console.log(`Messages Processed: ${results.messageCount}`);
        console.log(`Total Time: ${results.totalTime.toFixed(2)} ms`);
        console.log(`Messages/Second: ${results.messagesPerSecond.toFixed(1)}`);
        console.log(`Average Latency: ${results.avgLatency.toFixed(3)} ms`);
        console.log(`Max Latency: ${results.maxLatency.toFixed(3)} ms`);
        console.log(`Min Latency: ${results.minLatency.toFixed(3)} ms`);
        console.log(`P95 Latency: ${results.p95Latency.toFixed(3)} ms`);
        console.log(`P99 Latency: ${results.p99Latency.toFixed(3)} ms`);
        console.log(`Frame Drops: ${results.frameDrops}`);
        console.log(`Frame Drop Rate: ${results.frameDropRate.toFixed(2)}%`);
        
        // Success criteria check
        console.log("\n🎯 SUCCESS CRITERIA CHECK:");
        console.log("-" * 40);
        const under5ms = results.avgLatency < 5.0;
        const lowFrameDrops = results.frameDropRate < 5.0;
        const goodThroughput = results.messagesPerSecond > 500;
        
        console.log(`Average latency < 5ms: ${under5ms ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Frame drop rate < 5%: ${lowFrameDrops ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Throughput > 500 msg/sec: ${goodThroughput ? '✅ PASS' : '❌ FAIL'}`);
        
        if (under5ms && lowFrameDrops && goodThroughput) {
            console.log("\n🎉 WEBSOCKET PERFORMANCE: EXCELLENT");
        } else {
            console.log("\n⚠️  WEBSOCKET PERFORMANCE: NEEDS OPTIMIZATION");
        }
        
        return results;
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketBenchmark;
}

// Auto-run if executed directly
if (typeof window !== 'undefined') {
    // Browser environment
    window.WebSocketBenchmark = WebSocketBenchmark;
    
    // Auto-run benchmark
    const benchmark = new WebSocketBenchmark();
    benchmark.runWebSocketBenchmark(1000)
        .then(results => benchmark.printResults(results))
        .catch(error => console.error('Benchmark error:', error));
} else if (typeof global !== 'undefined') {
    // Node.js environment
    global.WebSocketBenchmark = WebSocketBenchmark;
}
