/**
 * Chart Rendering Performance Benchmark
 * Tests chart update latency, frame rate, and render time
 * Simulates 200 live updates for various chart types
 */

class ChartRenderingBenchmark {
    constructor() {
        this.chartTypes = ['line', 'candlestick', 'area', 'bar', 'scatter'];
        this.updateCount = 0;
        this.totalRenderTime = 0;
        this.maxRenderTime = 0;
        minRenderTime: Infinity;
        this.renderTimes = [];
        this.frameRates = [];
        this.chartInstances = new Map();
        this.startTime = null;
        this.lastFrameTime = performance.now();
        this.frameCount = 0;
        this.frameDrops = 0;
    }

    // Mock chart data structure
    createChartData(pointCount = 100) {
        const data = [];
        const basePrice = 45000;
        const baseTime = Date.now() - (pointCount * 60000); // 1 minute intervals
        
        for (let i = 0; i < pointCount; i++) {
            const priceVariation = Math.sin(i / 10) * 100 + (Math.random() - 0.5) * 50;
            data.push({
                time: baseTime + (i * 60000),
                open: basePrice + priceVariation,
                high: basePrice + priceVariation + Math.random() * 20,
                low: basePrice + priceVariation - Math.random() * 20,
                close: basePrice + priceVariation + (Math.random() - 0.5) * 10,
                volume: 1000000 + Math.random() * 5000000,
                timestamp: baseTime + (i * 60000)
            });
        }
        
        return data;
    }

    // Mock chart instance
    createMockChart(type, containerId) {
        return {
            type: type,
            containerId: containerId,
            data: this.createChartData(100),
            options: this.getChartOptions(type),
            renderCount: 0,
            totalRenderTime: 0,
            lastRenderTime: 0,
            canvas: {
                width: 800,
                height: 400,
                context: this.createMockCanvasContext()
            },
            animations: {
                enabled: true,
                duration: 300,
                easing: 'easeInOut'
            }
        };
    }

    // Get chart options based on type
    getChartOptions(type) {
        const baseOptions = {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 300
            },
            scales: {
                x: {
                    type: 'time',
                    display: true
                },
                y: {
                    display: true
                }
            }
        };

        switch (type) {
            case 'candlestick':
                return {
                    ...baseOptions,
                    candlestick: {
                        upColor: '#26a69a',
                        downColor: '#ef5350',
                        borderUpColor: '#26a69a',
                        borderDownColor: '#ef5350'
                    }
                };
            case 'line':
                return {
                    ...baseOptions,
                    elements: {
                        line: {
                            tension: 0.1
                        },
                        point: {
                            radius: 0
                        }
                    }
                };
            case 'area':
                return {
                    ...baseOptions,
                    fill: true,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)'
                };
            case 'bar':
                return {
                    ...baseOptions,
                    barPercentage: 0.8
                };
            case 'scatter':
                return {
                    ...baseOptions,
                    showLine: false
                };
            default:
                return baseOptions;
        }
    }

    // Mock canvas context for rendering simulation
    createMockCanvasContext() {
        const operations = [];
        
        return {
            // Canvas operations tracking
            fillRect: (x, y, width, height) => operations.push({ type: 'fillRect', x, y, width, height }),
            strokeRect: (x, y, width, height) => operations.push({ type: 'strokeRect', x, y, width, height }),
            beginPath: () => operations.push({ type: 'beginPath' }),
            moveTo: (x, y) => operations.push({ type: 'moveTo', x, y }),
            lineTo: (x, y) => operations.push({ type: 'lineTo', x, y }),
            arc: (x, y, radius, startAngle, endAngle) => operations.push({ type: 'arc', x, y, radius, startAngle, endAngle }),
            fill: () => operations.push({ type: 'fill' }),
            stroke: () => operations.push({ type: 'stroke' }),
            clearRect: (x, y, width, height) => operations.push({ type: 'clearRect', x, y, width, height }),
            
            // Style operations
            fillStyle: '#000000',
            strokeStyle: '#000000',
            lineWidth: 1,
            
            // Get operations count for performance measurement
            getOperationCount: () => operations.length,
            resetOperations: () => operations.length = 0
        };
    }

    // Initialize charts
    initializeCharts() {
        this.chartTypes.forEach((type, index) => {
            const chart = this.createMockChart(type, `chart-${index}`);
            this.chartInstances.set(type, chart);
        });
        
        console.log(`Initialized ${this.chartInstances.size} chart instances`);
    }

    // Simulate chart rendering
    renderChart(chart, newData) {
        const renderStart = performance.now();
        
        // Update chart data
        const dataUpdateStart = performance.now();
        chart.data = this.updateChartData(chart.data, newData);
        const dataUpdateTime = performance.now() - dataUpdateStart;
        
        // Clear canvas
        const clearStart = performance.now();
        chart.canvas.context.clearRect(0, 0, chart.canvas.width, chart.canvas.height);
        const clearTime = performance.now() - clearStart;
        
        // Render chart based on type
        const chartRenderStart = performance.now();
        const renderOperations = this.renderChartByType(chart);
        const chartRenderTime = performance.now() - chartRenderStart;
        
        // Update animations if enabled
        const animationStart = performance.now();
        if (chart.animations.enabled) {
            this.updateAnimations(chart);
        }
        const animationTime = performance.now() - animationStart;
        
        const renderEnd = performance.now();
        const totalRenderTime = renderEnd - renderStart;
        
        // Update metrics
        chart.renderCount++;
        chart.totalRenderTime += totalRenderTime;
        chart.lastRenderTime = totalRenderTime;
        
        return {
            totalRenderTime,
            dataUpdateTime,
            clearTime,
            chartRenderTime,
            animationTime,
            operations: renderOperations
        };
    }

    // Update chart data with new point
    updateChartData(currentData, newDataPoint) {
        // Remove oldest point and add new one
        const updatedData = [...currentData.slice(1), newDataPoint];
        return updatedData;
    }

    // Render chart based on type
    renderChartByType(chart) {
        const context = chart.canvas.context;
        context.resetOperations();
        
        let operations = 0;
        
        switch (chart.type) {
            case 'line':
                operations = this.renderLineChart(chart, context);
                break;
            case 'candlestick':
                operations = this.renderCandlestickChart(chart, context);
                break;
            case 'area':
                operations = this.renderAreaChart(chart, context);
                break;
            case 'bar':
                operations = this.renderBarChart(chart, context);
                break;
            case 'scatter':
                operations = this.renderScatterChart(chart, context);
                break;
            default:
                operations = this.renderLineChart(chart, context);
        }
        
        return operations;
    }

    // Render line chart
    renderLineChart(chart, context) {
        const data = chart.data;
        const width = chart.canvas.width;
        const height = chart.canvas.height;
        const padding = 40;
        
        // Draw axes
        context.strokeStyle = '#666';
        context.lineWidth = 1;
        context.beginPath();
        context.moveTo(padding, padding);
        context.lineTo(padding, height - padding);
        context.lineTo(width - padding, height - padding);
        context.stroke();
        
        // Draw line
        context.strokeStyle = '#26a69a';
        context.lineWidth = 2;
        context.beginPath();
        
        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
            const y = height - padding - ((point.close - 44800) / 400) * (height - 2 * padding);
            
            if (index === 0) {
                context.moveTo(x, y);
            } else {
                context.lineTo(x, y);
            }
        });
        
        context.stroke();
        
        return context.getOperationCount();
    }

    // Render candlestick chart
    renderCandlestickChart(chart, context) {
        const data = chart.data;
        const width = chart.canvas.width;
        const height = chart.canvas.height;
        const padding = 40;
        const candleWidth = (width - 2 * padding) / data.length * 0.8;
        
        // Draw axes
        context.strokeStyle = '#666';
        context.lineWidth = 1;
        context.beginPath();
        context.moveTo(padding, padding);
        context.lineTo(padding, height - padding);
        context.lineTo(width - padding, height - padding);
        context.stroke();
        
        // Draw candlesticks
        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
            const yOpen = height - padding - ((point.open - 44800) / 400) * (height - 2 * padding);
            const yClose = height - padding - ((point.close - 44800) / 400) * (height - 2 * padding);
            const yHigh = height - padding - ((point.high - 44800) / 400) * (height - 2 * padding);
            const yLow = height - padding - ((point.low - 44800) / 400) * (height - 2 * padding);
            
            // Set color based on price movement
            context.strokeStyle = point.close >= point.open ? '#26a69a' : '#ef5350';
            context.fillStyle = point.close >= point.open ? '#26a69a' : '#ef5350';
            
            // Draw high-low line
            context.lineWidth = 1;
            context.beginPath();
            context.moveTo(x, yHigh);
            context.lineTo(x, yLow);
            context.stroke();
            
            // Draw open-close box
            context.lineWidth = 2;
            const bodyHeight = Math.abs(yClose - yOpen);
            const bodyY = Math.min(yOpen, yClose);
            
            if (point.close !== point.open) {
                context.fillRect(x - candleWidth / 2, bodyY, candleWidth, bodyHeight);
            } else {
                // Doji (open equals close)
                context.fillRect(x - candleWidth / 2, bodyY - 1, candleWidth, 2);
            }
        });
        
        return context.getOperationCount();
    }

    // Render area chart
    renderAreaChart(chart, context) {
        // Similar to line chart but with fill
        const operations = this.renderLineChart(chart, context);
        
        // Add fill operations
        const data = chart.data;
        const width = chart.canvas.width;
        const height = chart.canvas.height;
        const padding = 40;
        
        context.fillStyle = 'rgba(54, 162, 235, 0.2)';
        context.beginPath();
        
        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
            const y = height - padding - ((point.close - 44800) / 400) * (height - 2 * padding);
            
            if (index === 0) {
                context.moveTo(x, height - padding);
                context.lineTo(x, y);
            } else {
                context.lineTo(x, y);
            }
        });
        
        context.lineTo(width - padding, height - padding);
        context.closePath();
        context.fill();
        
        return operations + context.getOperationCount();
    }

    // Render bar chart
    renderBarChart(chart, context) {
        const data = chart.data;
        const width = chart.canvas.width;
        const height = chart.canvas.height;
        const padding = 40;
        const barWidth = (width - 2 * padding) / data.length * 0.8;
        
        // Draw axes
        context.strokeStyle = '#666';
        context.lineWidth = 1;
        context.beginPath();
        context.moveTo(padding, padding);
        context.lineTo(padding, height - padding);
        context.lineTo(width - padding, height - padding);
        context.stroke();
        
        // Draw bars
        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
            const barHeight = ((point.close - 44800) / 400) * (height - 2 * padding);
            const y = height - padding - barHeight;
            
            context.fillStyle = '#26a69a';
            context.fillRect(x - barWidth / 2, y, barWidth, barHeight);
        });
        
        return context.getOperationCount();
    }

    // Render scatter chart
    renderScatterChart(chart, context) {
        const data = chart.data;
        const width = chart.canvas.width;
        const height = chart.canvas.height;
        const padding = 40;
        
        // Draw axes
        context.strokeStyle = '#666';
        context.lineWidth = 1;
        context.beginPath();
        context.moveTo(padding, padding);
        context.lineTo(padding, height - padding);
        context.lineTo(width - padding, height - padding);
        context.stroke();
        
        // Draw scatter points
        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
            const y = height - padding - ((point.close - 44800) / 400) * (height - 2 * padding);
            
            context.fillStyle = '#26a69a';
            context.beginPath();
            context.arc(x, y, 3, 0, 2 * Math.PI);
            context.fill();
        });
        
        return context.getOperationCount();
    }

    // Update animations
    updateAnimations(chart) {
        // Simulate animation work
        const animationSteps = 10;
        for (let i = 0; i < animationSteps; i++) {
            // Simulate interpolation
            performance.now();
        }
    }

    // Create new data point for update
    createNewDataPoint(index) {
        const basePrice = 45000;
        const priceVariation = Math.sin(index / 10) * 100 + (Math.random() - 0.5) * 50;
        
        return {
            time: Date.now(),
            open: basePrice + priceVariation,
            high: basePrice + priceVariation + Math.random() * 20,
            low: basePrice + priceVariation - Math.random() * 20,
            close: basePrice + priceVariation + (Math.random() - 0.5) * 10,
            volume: 1000000 + Math.random() * 5000000,
            timestamp: Date.now()
        };
    }

    // Measure frame rate
    measureFrameRate() {
        const currentTime = performance.now();
        const frameDelta = currentTime - this.lastFrameTime;
        const fps = 1000 / frameDelta;
        
        this.frameRates.push(fps);
        this.frameCount++;
        
        // Check for frame drops
        if (frameDelta > 16.67) { // 60 FPS threshold
            this.frameDrops++;
        }
        
        this.lastFrameTime = currentTime;
        return fps;
    }

    // Run chart rendering benchmark
    async runChartBenchmark(updateCount = 200) {
        console.log(`🚀 Starting Chart Rendering Benchmark (${updateCount} updates)`);
        console.log("=" * 60);
        
        this.updateCount = updateCount;
        this.totalRenderTime = 0;
        this.maxRenderTime = 0;
        this.minRenderTime = Infinity;
        this.renderTimes = [];
        this.frameRates = [];
        this.frameDrops = 0;
        this.startTime = performance.now();
        
        // Initialize charts
        this.initializeCharts();
        
        // Warm up
        console.log("Warming up...");
        for (let i = 0; i < 5; i++) {
            const warmupDataPoint = this.createNewDataPoint(i);
            this.chartInstances.forEach(chart => {
                this.renderChart(chart, warmupDataPoint);
            });
        }
        
        // Reset metrics
        this.renderTimes = [];
        this.totalRenderTime = 0;
        this.maxRenderTime = 0;
        this.minRenderTime = Infinity;
        this.frameRates = [];
        this.frameDrops = 0;
        
        console.log("Running main benchmark...");
        
        // Process updates
        for (let i = 0; i < updateCount; i++) {
            const newDataPoint = this.createNewDataPoint(i);
            
            // Render all charts
            this.chartInstances.forEach((chart, chartType) => {
                const renderStart = performance.now();
                const renderResult = this.renderChart(chart, newDataPoint);
                const renderEnd = performance.now();
                
                const totalRenderTime = renderEnd - renderStart;
                this.renderTimes.push(totalRenderTime);
                this.totalRenderTime += totalRenderTime;
                this.maxRenderTime = Math.max(this.maxRenderTime, totalRenderTime);
                this.minRenderTime = Math.min(this.minRenderTime, totalRenderTime);
                
                // Measure frame rate
                this.measureFrameRate();
            });
            
            // Progress indicator
            if ((i + 1) % 20 === 0) {
                console.log(`  Progress: ${i + 1}/${updateCount} updates`);
            }
            
            // Simulate real-time update frequency (60 FPS)
            await new Promise(resolve => setTimeout(resolve, 16));
        }
        
        const endTime = performance.now();
        const totalTime = endTime - this.startTime;
        
        // Calculate final metrics
        const avgRenderTime = this.totalRenderTime / this.renderTimes.length;
        const p95RenderTime = this.calculatePercentile(this.renderTimes, 95);
        const p99RenderTime = this.calculatePercentile(this.renderTimes, 99);
        const avgFPS = this.frameRates.reduce((sum, fps) => sum + fps, 0) / this.frameRates.length;
        const updatesPerSecond = updateCount / (totalTime / 1000);
        
        return {
            updateCount: updateCount,
            totalTime: totalTime,
            avgRenderTime: avgRenderTime,
            maxRenderTime: this.maxRenderTime,
            minRenderTime: this.minRenderTime,
            p95RenderTime: p95RenderTime,
            p99RenderTime: p99RenderTime,
            avgFPS: avgFPS,
            frameDrops: this.frameDrops,
            frameDropRate: (this.frameDrops / this.frameCount) * 100,
            updatesPerSecond: updatesPerSecond,
            chartMetrics: this.getChartMetrics()
        };
    }

    // Calculate percentile
    calculatePercentile(values, percentile) {
        const sorted = values.slice().sort((a, b) => a - b);
        const index = Math.ceil((percentile / 100) * sorted.length) - 1;
        return sorted[Math.max(0, index)];
    }

    // Get chart-specific metrics
    getChartMetrics() {
        const metrics = {};
        
        this.chartInstances.forEach((chart, type) => {
            metrics[type] = {
                renderCount: chart.renderCount,
                avgRenderTime: chart.totalRenderTime / chart.renderCount,
                totalRenderTime: chart.totalRenderTime
            };
        });
        
        return metrics;
    }

    // Print results
    printResults(results) {
        console.log("\n" + "=" * 80);
        console.log("📊 CHART RENDERING PERFORMANCE RESULTS");
        console.log("=" * 80);
        console.log(`Chart Updates: ${results.updateCount}`);
        console.log(`Total Time: ${results.totalTime.toFixed(2)} ms`);
        console.log(`Updates/Second: ${results.updatesPerSecond.toFixed(1)}`);
        console.log(`Average Render Time: ${results.avgRenderTime.toFixed(3)} ms`);
        console.log(`Max Render Time: ${results.maxRenderTime.toFixed(3)} ms`);
        console.log(`Min Render Time: ${results.minRenderTime.toFixed(3)} ms`);
        console.log(`P95 Render Time: ${results.p95RenderTime.toFixed(3)} ms`);
        console.log(`P99 Render Time: ${results.p99RenderTime.toFixed(3)} ms`);
        console.log(`Average FPS: ${results.avgFPS.toFixed(1)}`);
        console.log(`Frame Drops: ${results.frameDrops}`);
        console.log(`Frame Drop Rate: ${results.frameDropRate.toFixed(2)}%`);
        
        // Chart-specific results
        console.log("\nChart Type Performance:");
        console.log("-" * 50);
        Object.entries(results.chartMetrics).forEach(([type, metrics]) => {
            console.log(`${type}:`);
            console.log(`  Renders: ${metrics.renderCount}`);
            console.log(`  Avg: ${metrics.avgRenderTime.toFixed(3)} ms`);
            console.log(`  Total: ${metrics.totalRenderTime.toFixed(2)} ms`);
        });
        
        // Success criteria check
        console.log("\n🎯 SUCCESS CRITERIA CHECK:");
        console.log("-" * 40);
        const under16ms = results.avgRenderTime < 16.0;
        const fpsAbove50 = results.avgFPS > 50;
        const lowFrameDrops = results.frameDropRate < 10;
        
        console.log(`Chart updates < 16ms: ${under16ms ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`FPS > 50: ${fpsAbove50 ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Frame drop rate < 10%: ${lowFrameDrops ? '✅ PASS' : '❌ FAIL'}`);
        
        if (under16ms && fpsAbove50 && lowFrameDrops) {
            console.log("\n🎉 CHART RENDERING PERFORMANCE: EXCELLENT");
        } else {
            console.log("\n⚠️  CHART RENDERING PERFORMANCE: NEEDS OPTIMIZATION");
        }
        
        return results;
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartRenderingBenchmark;
}

// Auto-run if executed directly
if (typeof window !== 'undefined') {
    // Browser environment
    window.ChartRenderingBenchmark = ChartRenderingBenchmark;
    
    // Auto-run benchmark
    const benchmark = new ChartRenderingBenchmark();
    benchmark.runChartBenchmark(200)
        .then(results => benchmark.printResults(results))
        .catch(error => console.error('Benchmark error:', error));
} else if (typeof global !== 'undefined') {
    // Node.js environment
    global.ChartRenderingBenchmark = ChartRenderingBenchmark;
}
