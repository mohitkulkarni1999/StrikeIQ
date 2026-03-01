/**
 * Frame Rate Test
 * Tests FPS stability during live updates
 * Uses requestAnimationFrame to measure actual frame rate
 */

class FrameRateBenchmark {
    constructor() {
        this.frameCount = 0;
        this.fpsSamples = [];
        this.lastFrameTime = performance.now();
        this.startTime = null;
        this.testDuration = 10000; // 10 seconds
        this.targetFPS = 60;
        this.minAcceptableFPS = 50;
        this.frameDrops = 0;
        this.totalFrames = 0;
        this.droppedFrames = 0;
        this.avgFPS = 0;
        this.minFPS = Infinity;
        this.maxFPS = 0;
        this.fpsStability = 0;
    }

    // Calculate current FPS
    calculateFPS() {
        const currentTime = performance.now();
        const deltaTime = currentTime - this.lastFrameTime;
        const currentFPS = 1000 / deltaTime;
        
        return {
            fps: currentFPS,
            deltaTime: deltaTime,
            timestamp: currentTime
        };
    }

    // Simulate UI update work
    simulateUIWork() {
        const workStart = performance.now();
        
        // Simulate DOM operations
        const operations = [
            'createElement',
            'appendChild',
            'removeChild',
            'setAttribute',
            'removeAttribute',
            'addClass',
            'removeClass',
            'updateStyle'
        ];
        
        // Perform random DOM operations
        const operationCount = 5 + Math.floor(Math.random() * 10);
        for (let i = 0; i < operationCount; i++) {
            const operation = operations[i % operations.length];
            
            // Simulate work based on operation type
            switch (operation) {
                case 'createElement':
                    // Simulate element creation
                    const element = {
                        tagName: 'div',
                        attributes: {},
                        children: [],
                        textContent: ''
                    };
                    break;
                case 'appendChild':
                    // Simulate adding child
                    performance.now();
                    break;
                case 'removeChild':
                    // Simulate removing child
                    performance.now();
                    break;
                case 'setAttribute':
                    // Simulate setting attribute
                    performance.now();
                    break;
                case 'removeAttribute':
                    // Simulate removing attribute
                    performance.now();
                    break;
                case 'addClass':
                    // Simulate adding class
                    performance.now();
                    break;
                case 'removeClass':
                    // Simulate removing class
                    performance.now();
                    break;
                case 'updateStyle':
                    // Simulate style update
                    performance.now();
                    break;
            }
        }
        
        // Simulate layout calculations
        this.simulateLayoutWork();
        
        // Simulate paint operations
        this.simulatePaintWork();
        
        const workEnd = performance.now();
        return workEnd - workStart;
    }

    // Simulate layout work
    simulateLayoutWork() {
        // Simulate CSS layout calculations
        const elements = 100 + Math.floor(Math.random() * 200);
        
        for (let i = 0; i < elements; i++) {
            // Simulate layout calculations
            const width = 100 + Math.random() * 800;
            const height = 50 + Math.random() * 400;
            const x = Math.random() * 1200;
            const y = Math.random() * 800;
            
            // Simulate box model calculations
            const margin = 10 + Math.random() * 20;
            const padding = 5 + Math.random() * 15;
            const border = 1 + Math.random() * 3;
            
            // Calculate final dimensions
            const finalWidth = width + margin * 2 + padding * 2 + border * 2;
            const finalHeight = height + margin * 2 + padding * 2 + border * 2;
            
            performance.now(); // Simulate calculation time
        }
    }

    // Simulate paint work
    simulatePaintWork() {
        // Simulate canvas drawing operations
        const drawOperations = 50 + Math.floor(Math.random() * 100);
        
        for (let i = 0; i < drawOperations; i++) {
            // Simulate different draw operations
            const operation = ['fillRect', 'strokeRect', 'drawText', 'drawImage', 'drawPath'][i % 5];
            
            switch (operation) {
                case 'fillRect':
                    // Simulate rectangle fill
                    performance.now();
                    break;
                case 'strokeRect':
                    // Simulate rectangle stroke
                    performance.now();
                    break;
                case 'drawText':
                    // Simulate text rendering
                    performance.now();
                    break;
                case 'drawImage':
                    // Simulate image rendering
                    performance.now();
                    break;
                case 'drawPath':
                    // Simulate path drawing
                    performance.now();
                    break;
            }
        }
    }

    // Simulate market data update
    simulateMarketDataUpdate(frameIndex) {
        const basePrice = 45000;
        const priceVariation = Math.sin(frameIndex / 60) * 100 + (Math.random() - 0.5) * 50;
        
        return {
            symbol: "BANKNIFTY",
            price: basePrice + priceVariation,
            pcr: 1.0 + (frameIndex % 50) / 100,
            gamma: -30000 + (frameIndex % 20000) - 10000,
            timestamp: Date.now(),
            volume: 1000000 + (frameIndex % 5000000),
            change: priceVariation,
            changePercent: (priceVariation / basePrice) * 100,
            rsi: 30 + (frameIndex % 70),
            momentum: (frameIndex % 100) / 100,
            regime: ["BULLISH", "BEARISH", "NEUTRAL"][frameIndex % 3],
            volatility_regime: ["LOW", "MEDIUM", "HIGH", "EXTREME"][frameIndex % 4]
        };
    }

    // Animation frame callback
    animationFrameCallback = () => {
        const currentTime = performance.now();
        const fpsData = this.calculateFPS();
        
        // Update frame statistics
        this.frameCount++;
        this.totalFrames++;
        this.fpsSamples.push(fpsData.fps);
        
        // Track min/max FPS
        this.minFPS = Math.min(this.minFPS, fpsData.fps);
        this.maxFPS = Math.max(this.maxFPS, fpsData.fps);
        
        // Check for frame drops
        if (fpsData.fps < this.minAcceptableFPS) {
            this.frameDrops++;
            this.droppedFrames++;
        }
        
        // Simulate UI work
        const uiWorkTime = this.simulateUIWork();
        
        // Simulate market data update
        const marketData = this.simulateMarketDataUpdate(this.frameCount);
        
        // Simulate chart updates
        this.simulateChartUpdate(marketData);
        
        // Update last frame time
        this.lastFrameTime = currentTime;
        
        // Check if test duration is complete
        if (currentTime - this.startTime < this.testDuration) {
            // Continue animation
            requestAnimationFrame(this.animationFrameCallback);
        } else {
            // Test complete
            this.finalizeResults();
        }
    };

    // Simulate chart update
    simulateChartUpdate(marketData) {
        // Simulate chart rendering work
        const chartTypes = ['line', 'candlestick', 'area', 'bar'];
        const chartType = chartTypes[this.frameCount % chartTypes.length];
        
        // Simulate chart data processing
        const dataPoints = 100 + Math.floor(Math.random() * 200);
        const chartData = [];
        
        for (let i = 0; i < dataPoints; i++) {
            chartData.push({
                time: Date.now() - (dataPoints - i) * 60000,
                value: marketData.price + (Math.random() - 0.5) * 100,
                volume: marketData.volume + (Math.random() - 0.5) * 1000000
            });
        }
        
        // Simulate chart rendering based on type
        switch (chartType) {
            case 'line':
                this.simulateLineChart(chartData);
                break;
            case 'candlestick':
                this.simulateCandlestickChart(chartData);
                break;
            case 'area':
                this.simulateAreaChart(chartData);
                break;
            case 'bar':
                this.simulateBarChart(chartData);
                break;
        }
    }

    // Simulate line chart rendering
    simulateLineChart(data) {
        for (let i = 0; i < data.length - 1; i++) {
            // Simulate line drawing
            const x1 = i * 10;
            const y1 = 400 - data[i].value / 100;
            const x2 = (i + 1) * 10;
            const y2 = 400 - data[i + 1].value / 100;
            
            performance.now(); // Simulate drawing time
        }
    }

    // Simulate candlestick chart rendering
    simulateCandlestickChart(data) {
        for (let i = 0; i < data.length; i++) {
            // Simulate candlestick drawing
            const x = i * 10;
            const open = data[i].value - 10;
            const close = data[i].value + 10;
            const high = data[i].value + 20;
            const low = data[i].value - 20;
            
            // Draw high-low line
            performance.now();
            
            // Draw open-close body
            performance.now();
        }
    }

    // Simulate area chart rendering
    simulateAreaChart(data) {
        // Simulate area fill
        for (let i = 0; i < data.length - 1; i++) {
            const x = i * 10;
            const y = 400 - data[i].value / 100;
            
            performance.now(); // Simulate fill time
        }
    }

    // Simulate bar chart rendering
    simulateBarChart(data) {
        for (let i = 0; i < data.length; i++) {
            // Simulate bar drawing
            const x = i * 10;
            const height = data[i].value / 100;
            const y = 400 - height;
            
            performance.now(); // Simulate drawing time
        }
    }

    // Finalize and calculate results
    finalizeResults() {
        const endTime = performance.now();
        const actualDuration = endTime - this.startTime;
        
        // Calculate average FPS
        this.avgFPS = this.fpsSamples.reduce((sum, fps) => sum + fps, 0) / this.fpsSamples.length;
        
        // Calculate FPS stability (standard deviation)
        const variance = this.fpsSamples.reduce((sum, fps) => sum + Math.pow(fps - this.avgFPS, 2), 0) / this.fpsSamples.length;
        this.fpsStability = Math.sqrt(variance);
        
        // Calculate frame drop rate
        const frameDropRate = (this.droppedFrames / this.totalFrames) * 100;
        
        // Calculate percentiles
        const sortedFPS = this.fpsSamples.slice().sort((a, b) => a - b);
        const p50FPS = sortedFPS[Math.floor(sortedFPS.length * 0.5)];
        const p95FPS = sortedFPS[Math.floor(sortedFPS.length * 0.95)];
        const p99FPS = sortedFPS[Math.floor(sortedFPS.length * 0.99)];
        
        const results = {
            duration: actualDuration,
            totalFrames: this.totalFrames,
            avgFPS: this.avgFPS,
            minFPS: this.minFPS,
            maxFPS: this.maxFPS,
            p50FPS: p50FPS,
            p95FPS: p95FPS,
            p99FPS: p99FPS,
            fpsStability: this.fpsStability,
            droppedFrames: this.droppedFrames,
            frameDropRate: frameDropRate,
            targetFPS: this.targetFPS,
            minAcceptableFPS: this.minAcceptableFPS
        };
        
        this.printResults(results);
        return results;
    }

    // Run FPS benchmark
    runFPSBenchmark(duration = 10000) {
        console.log(`🚀 Starting Frame Rate Benchmark (${duration}ms duration)`);
        console.log("=" * 60);
        console.log(`Target FPS: ${this.targetFPS}`);
        console.log(`Minimum Acceptable FPS: ${this.minAcceptableFPS}`);
        console.log("=" * 60);
        
        // Reset counters
        this.frameCount = 0;
        this.fpsSamples = [];
        this.lastFrameTime = performance.now();
        this.startTime = performance.now();
        this.testDuration = duration;
        this.frameDrops = 0;
        this.totalFrames = 0;
        this.droppedFrames = 0;
        this.avgFPS = 0;
        this.minFPS = Infinity;
        this.maxFPS = 0;
        this.fpsStability = 0;
        
        // Start animation
        requestAnimationFrame(this.animationFrameCallback);
        
        return new Promise((resolve) => {
            this.resolvePromise = resolve;
        });
    }

    // Print results
    printResults(results) {
        console.log("\n" + "=" * 80);
        console.log("📊 FRAME RATE PERFORMANCE RESULTS");
        console.log("=" * 80);
        console.log(`Test Duration: ${(results.duration / 1000).toFixed(2)} seconds`);
        console.log(`Total Frames: ${results.totalFrames}`);
        console.log(`Target FPS: ${results.targetFPS}`);
        console.log(`Average FPS: ${results.avgFPS.toFixed(2)}`);
        console.log(`Min FPS: ${results.minFPS.toFixed(2)}`);
        console.log(`Max FPS: ${results.maxFPS.toFixed(2)}`);
        console.log(`P50 FPS: ${results.p50FPS.toFixed(2)}`);
        console.log(`P95 FPS: ${results.p95FPS.toFixed(2)}`);
        console.log(`P99 FPS: ${results.p99FPS.toFixed(2)}`);
        console.log(`FPS Stability (Std Dev): ${results.fpsStability.toFixed(2)}`);
        console.log(`Dropped Frames: ${results.droppedFrames}`);
        console.log(`Frame Drop Rate: ${results.frameDropRate.toFixed(2)}%`);
        
        // Performance analysis
        console.log("\n🔍 PERFORMANCE ANALYSIS:");
        console.log("-" * 50);
        
        const fpsScore = (results.avgFPS / results.targetFPS) * 100;
        const stabilityScore = results.fpsStability < 5 ? 100 : Math.max(0, 100 - results.fpsStability * 10);
        const dropScore = Math.max(0, 100 - results.frameDropRate * 2);
        
        console.log(`FPS Score: ${fpsScore.toFixed(1)}%`);
        console.log(`Stability Score: ${stabilityScore.toFixed(1)}%`);
        console.log(`Drop Score: ${dropScore.toFixed(1)}%`);
        
        // Success criteria check
        console.log("\n🎯 SUCCESS CRITERIA CHECK:");
        console.log("-" * 40);
        const fpsAbove50 = results.avgFPS > results.minAcceptableFPS;
        const stableFPS = results.fpsStability < 5;
        const lowDropRate = results.frameDropRate < 5;
        const goodP95 = results.p95FPS > results.minAcceptableFPS;
        
        console.log(`Average FPS > 50: ${fpsAbove50 ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`FPS Stability < 5: ${stableFPS ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Frame Drop Rate < 5%: ${lowDropRate ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`P95 FPS > 50: ${goodP95 ? '✅ PASS' : '❌ FAIL'}`);
        
        if (fpsAbove50 && stableFPS && lowDropRate && goodP95) {
            console.log("\n🎉 FRAME RATE PERFORMANCE: EXCELLENT");
        } else {
            console.log("\n⚠️  FRAME RATE PERFORMANCE: NEEDS OPTIMIZATION");
        }
        
        // Recommendations
        console.log("\n💡 RECOMMENDATIONS:");
        if (!fpsAbove50) {
            console.log("  • Optimize rendering to achieve > 50 FPS");
        }
        if (!stableFPS) {
            console.log("  • Reduce frame time variance for smoother experience");
        }
        if (!lowDropRate) {
            console.log("  • Minimize frame drops during heavy updates");
        }
        if (!goodP95) {
            console.log("  • Improve worst-case performance scenarios");
        }
        
        // Resolve promise if exists
        if (this.resolvePromise) {
            this.resolvePromise(results);
        }
        
        return results;
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FrameRateBenchmark;
}

// Auto-run if executed directly
if (typeof window !== 'undefined') {
    // Browser environment
    window.FrameRateBenchmark = FrameRateBenchmark;
    
    // Auto-run benchmark
    const benchmark = new FrameRateBenchmark();
    benchmark.runFPSBenchmark(10000)
        .then(results => {
            console.log("FPS Benchmark completed successfully");
        })
        .catch(error => console.error('Benchmark error:', error));
} else if (typeof global !== 'undefined') {
    // Node.js environment
    global.FrameRateBenchmark = FrameRateBenchmark;
}
