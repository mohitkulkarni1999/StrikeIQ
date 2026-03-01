/**
 * Memory Usage Benchmark
 * Tests memory allocation, heap usage, and potential leaks
 * Simulates 2000 UI updates to detect memory growth
 */

class MemoryUsageBenchmark {
    constructor() {
        this.initialMemory = null;
        this.memorySnapshots = [];
        this.updateCount = 0;
        this.componentInstances = new Map();
        this.eventListeners = new Set();
        this.timers = new Set();
        this.observers = new Set();
        this.gcCount = 0;
    }

    // Get current memory usage
    getMemoryUsage() {
        if (performance.memory) {
            return {
                used: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limit: performance.memory.jsHeapSizeLimit,
                timestamp: performance.now()
            };
        } else {
            // Fallback for browsers without memory API
            return {
                used: 0,
                total: 0,
                limit: 0,
                timestamp: performance.now()
            };
        }
    }

    // Force garbage collection if available
    forceGC() {
        if (window.gc) {
            window.gc();
            this.gcCount++;
        } else if (performance.memory) {
            // Trigger GC indirectly
            const dummy = new Array(1000000).fill(0);
            dummy.length = 0;
        }
    }

    // Create mock React component
    createMockComponent(name, complexity = 'medium') {
        const complexityFactors = {
            low: { props: 5, state: 3, listeners: 2 },
            medium: { props: 10, state: 5, listeners: 4 },
            high: { props: 20, state: 10, listeners: 8 }
        };
        
        const factor = complexityFactors[complexity];
        
        const component = {
            name: name,
            props: {},
            state: {},
            listeners: [],
            timers: [],
            observers: [],
            children: [],
            renderCount: 0,
            memoryFootprint: 0,
            ...factor
        };
        
        // Calculate initial memory footprint
        component.memoryFootprint = this.estimateComponentMemory(component);
        
        return component;
    }

    // Estimate component memory usage
    estimateComponentMemory(component) {
        let memory = 0;
        
        // Props memory
        memory += component.props * 64; // ~64 bytes per prop
        
        // State memory
        memory += component.state * 128; // ~128 bytes per state
        
        // Listeners memory
        memory += component.listeners * 256; // ~256 bytes per listener
        
        // Children memory
        memory += component.children.length * 512; // ~512 bytes per child
        
        // Base component overhead
        memory += 1024; // ~1KB base overhead
        
        return memory;
    }

    // Initialize mock components (simulate StrikeIQ frontend)
    initializeComponents() {
        const components = [
            { name: 'MarketDataTable', complexity: 'high' },
            { name: 'SignalPanel', complexity: 'medium' },
            { name: 'AlertPanel', complexity: 'low' },
            { name: 'ChartComponent', complexity: 'high' },
            { name: 'MetricsPanel', complexity: 'medium' },
            { name: 'OrderBookPanel', complexity: 'high' },
            { name: 'TradeHistory', complexity: 'medium' },
            { name: 'PositionPanel', complexity: 'low' },
            { name: 'WatchlistPanel', complexity: 'medium' },
            { name: 'NewsFeed', complexity: 'low' }
        ];

        components.forEach(({ name, complexity }) => {
            const component = this.createMockComponent(name, complexity);
            this.componentInstances.set(name, component);
        });
        
        console.log(`Initialized ${this.componentInstances.size} mock components`);
    }

    // Create event listeners (potential memory leak source)
    createEventListeners(component) {
        for (let i = 0; i < component.listeners; i++) {
            const listener = {
                id: `${component.name}-listener-${i}`,
                component: component.name,
                callback: () => {
                    // Simulate event handling
                    performance.now();
                },
                active: true
            };
            
            component.listeners.push(listener);
            this.eventListeners.add(listener);
        }
    }

    // Create timers (potential memory leak source)
    createTimers(component) {
        for (let i = 0; i < 2; i++) {
            const timerId = setInterval(() => {
                // Simulate timer work
                performance.now();
            }, 1000 + Math.random() * 2000);
            
            component.timers.push(timerId);
            this.timers.add(timerId);
        }
    }

    // Create observers (potential memory leak source)
    createObservers(component) {
        for (let i = 0; i < 2; i++) {
            const observer = {
                id: `${component.name}-observer-${i}`,
                component: component.name,
                callback: (data) => {
                    // Simulate observer work
                    performance.now();
                },
                active: true
            };
            
            component.observers.push(observer);
            this.observers.add(observer);
        }
    }

    // Create test data update
    createDataUpdate(index) {
        const basePrice = 45000;
        const priceVariation = (index % 1000) - 500;
        
        return {
            marketData: {
                symbol: "BANKNIFTY",
                price: basePrice + priceVariation,
                pcr: 1.0 + (index % 50) / 100,
                gamma: -30000 + (index % 20000) - 10000,
                timestamp: Date.now(),
                volume: 1000000 + (index % 5000000),
                change: priceVariation,
                changePercent: (priceVariation / basePrice) * 100,
                rsi: 30 + (index % 70),
                momentum: (index % 100) / 100,
                regime: ["BULLISH", "BEARISH", "NEUTRAL"][index % 3],
                // Additional data for memory testing
                trades: this.generateTrades(50 + (index % 100)),
                orders: this.generateOrders(25 + (index % 50)),
                alerts: this.generateAlerts(10 + (index % 20))
            },
            signals: [
                { type: 'LIQUIDITY_SWEEP', confidence: 0.8, direction: 'UP' },
                { type: 'GAMMA_SQUEEZE', confidence: 0.6, direction: 'DOWN' }
            ].slice(0, 1 + (index % 2)),
            ui: {
                selectedTab: ['overview', 'signals', 'alerts', 'history'][index % 4],
                chartType: ['line', 'candlestick', 'area'][index % 3],
                timeframe: ['1m', '5m', '15m'][index % 3],
                filters: this.generateFilters(5 + (index % 10))
            }
        };
    }

    // Generate mock trades
    generateTrades(count) {
        const trades = [];
        for (let i = 0; i < count; i++) {
            trades.push({
                id: `trade-${i}`,
                price: 45000 + (Math.random() - 0.5) * 200,
                quantity: 100 + Math.floor(Math.random() * 900),
                timestamp: Date.now() - Math.random() * 3600000,
                type: ['BUY', 'SELL'][Math.floor(Math.random() * 2)]
            });
        }
        return trades;
    }

    // Generate mock orders
    generateOrders(count) {
        const orders = [];
        for (let i = 0; i < count; i++) {
            orders.push({
                id: `order-${i}`,
                price: 45000 + (Math.random() - 0.5) * 200,
                quantity: 100 + Math.floor(Math.random() * 900),
                status: ['PENDING', 'FILLED', 'CANCELLED'][Math.floor(Math.random() * 3)],
                timestamp: Date.now() - Math.random() * 3600000
            });
        }
        return orders;
    }

    // Generate mock alerts
    generateAlerts(count) {
        const alerts = [];
        for (let i = 0; i < count; i++) {
            alerts.push({
                id: `alert-${i}`,
                type: ['PRICE_ALERT', 'VOLUME_ALERT', 'PCR_ALERT'][Math.floor(Math.random() * 3)],
                message: `Alert message ${i}`,
                severity: ['LOW', 'MEDIUM', 'HIGH'][Math.floor(Math.random() * 3)],
                timestamp: Date.now() - Math.random() * 3600000
            });
        }
        return alerts;
    }

    // Generate mock filters
    generateFilters(count) {
        const filters = {};
        for (let i = 0; i < count; i++) {
            filters`filter-${i}` = {
                type: ['range', 'select', 'multiselect'][Math.floor(Math.random() * 3)],
                value: Math.random() > 0.5 ? Math.random() * 100 : `option-${Math.floor(Math.random() * 5)}`
            };
        }
        return filters;
    }

    // Simulate component update with memory allocation
    updateComponent(component, dataUpdate) {
        const updateStart = performance.now();
        
        // Update component state (allocate new memory)
        const previousState = { ...component.state };
        component.state = {
            ...previousState,
            marketData: dataUpdate.marketData,
            signals: dataUpdate.signals,
            ui: dataUpdate.ui,
            lastUpdate: Date.now()
        };
        
        // Update props (allocate new memory)
        component.props = {
            ...component.props,
            data: dataUpdate,
            key: `update-${this.updateCount}`
        };
        
        // Simulate render memory allocation
        const renderData = this.simulateRenderMemory(component);
        
        // Update children (allocate new memory)
        component.children = this.updateChildren(component, dataUpdate);
        
        // Recalculate memory footprint
        component.memoryFootprint = this.estimateComponentMemory(component);
        component.renderCount++;
        
        const updateEnd = performance.now();
        return updateEnd - updateStart;
    }

    // Simulate render memory allocation
    simulateRenderMemory(component) {
        const renderData = {
            vdom: [],
            elements: [],
            styles: {},
            events: []
        };
        
        // Simulate virtual DOM nodes
        const nodeCount = 50 + Math.floor(Math.random() * 100);
        for (let i = 0; i < nodeCount; i++) {
            renderData.vdom.push({
                type: ['div', 'span', 'table', 'tr', 'td'][i % 5],
                props: {
                    key: `node-${i}`,
                    className: `node-${i % 10}`,
                    style: `color: ${['red', 'green', 'blue'][i % 3]}`
                },
                children: []
            });
        }
        
        // Simulate DOM elements
        for (let i = 0; i < nodeCount / 2; i++) {
            renderData.elements.push({
                element: document.createElement('div'),
                ref: `element-${i}`
            });
        }
        
        return renderData;
    }

    // Update children components
    updateChildren(parent, dataUpdate) {
        const childCount = Math.max(1, Math.floor(parent.children.length * (0.8 + Math.random() * 0.4)));
        const updatedChildren = [];
        
        for (let i = 0; i < childCount; i++) {
            const child = {
                type: 'child-component',
                key: `child-${i}-${this.updateCount}`,
                props: {
                    data: dataUpdate,
                    index: i
                },
                memoryFootprint: 512 + Math.random() * 1024
            };
            updatedChildren.push(child);
        }
        
        return updatedChildren;
    }

    // Take memory snapshot
    takeMemorySnapshot(label) {
        const memory = this.getMemoryUsage();
        const snapshot = {
            label: label,
            updateCount: this.updateCount,
            memory: memory,
            componentCount: this.componentInstances.size,
            listenerCount: this.eventListeners.size,
            timerCount: this.timers.size,
            observerCount: this.observers.size,
            gcCount: this.gcCount,
            timestamp: performance.now()
        };
        
        this.memorySnapshots.push(snapshot);
        return snapshot;
    }

    // Run memory usage benchmark
    async runMemoryBenchmark(updateCount = 2000) {
        console.log(`🚀 Starting Memory Usage Benchmark (${updateCount} updates)`);
        console.log("=" * 60);
        
        this.updateCount = 0;
        this.memorySnapshots = [];
        this.gcCount = 0;
        
        // Initialize components
        this.initializeComponents();
        
        // Create event listeners, timers, and observers
        this.componentInstances.forEach(component => {
            this.createEventListeners(component);
            this.createTimers(component);
            this.createObservers(component);
        });
        
        console.log(`Created ${this.eventListeners.size} listeners, ${this.timers.size} timers, ${this.observers.size} observers`);
        
        // Take initial memory snapshot
        this.forceGC();
        await new Promise(resolve => setTimeout(resolve, 100));
        this.initialMemory = this.takeMemorySnapshot('Initial');
        
        console.log(`Initial memory usage: ${(this.initialMemory.memory.used / 1024 / 1024).toFixed(2)} MB`);
        
        // Warm up
        console.log("Warming up...");
        for (let i = 0; i < 10; i++) {
            const warmupData = this.createDataUpdate(i);
            this.componentInstances.forEach(component => {
                this.updateComponent(component, warmupData);
            });
        }
        
        // Force GC and take snapshot
        this.forceGC();
        await new Promise(resolve => setTimeout(resolve, 100));
        const warmupMemory = this.takeMemorySnapshot('Warmup');
        
        console.log(`Warmup memory usage: ${(warmupMemory.memory.used / 1024 / 1024).toFixed(2)} MB`);
        
        // Main benchmark
        console.log("Running main benchmark...");
        
        for (let i = 0; i < updateCount; i++) {
            const dataUpdate = this.createDataUpdate(i);
            
            // Update all components
            this.componentInstances.forEach(component => {
                this.updateComponent(component, dataUpdate);
            });
            
            this.updateCount++;
            
            // Progress indicator
            if ((i + 1) % 200 === 0) {
                // Take periodic snapshot
                const snapshot = this.takeMemorySnapshot(`Update-${i + 1}`);
                console.log(`  Progress: ${i + 1}/${updateCount} updates - Memory: ${(snapshot.memory.used / 1024 / 1024).toFixed(2)} MB`);
                
                // Force GC periodically
                if (i % 500 === 0) {
                    this.forceGC();
                    await new Promise(resolve => setTimeout(resolve, 50));
                }
            }
            
            // Small delay to simulate real UI updates
            if (i % 50 === 0) {
                await new Promise(resolve => setTimeout(resolve, 1));
            }
        }
        
        // Final GC and snapshot
        this.forceGC();
        await new Promise(resolve => setTimeout(resolve, 100));
        const finalMemory = this.takeMemorySnapshot('Final');
        
        console.log(`Final memory usage: ${(finalMemory.memory.used / 1024 / 1024).toFixed(2)} MB`);
        
        // Calculate memory growth
        const memoryGrowth = finalMemory.memory.used - this.initialMemory.memory.used;
        const memoryGrowthMB = memoryGrowth / 1024 / 1024;
        
        return {
            updateCount: updateCount,
            initialMemory: this.initialMemory,
            finalMemory: finalMemory,
            memoryGrowth: memoryGrowth,
            memoryGrowthMB: memoryGrowthMB,
            snapshots: this.memorySnapshots,
            gcCount: this.gcCount,
            componentMetrics: this.getComponentMemoryMetrics()
        };
    }

    // Get component-specific memory metrics
    getComponentMemoryMetrics() {
        const metrics = {};
        
        this.componentInstances.forEach((component, name) => {
            metrics[name] = {
                renderCount: component.renderCount,
                memoryFootprint: component.memoryFootprint,
                listenerCount: component.listeners.length,
                timerCount: component.timers.length,
                observerCount: component.observers.length,
                childCount: component.children.length
            };
        });
        
        return metrics;
    }

    // Analyze memory leaks
    analyzeMemoryLeaks(results) {
        const analysis = {
            hasLeaks: false,
            leakRate: 0,
            leakSeverity: 'none',
            recommendations: []
        };
        
        // Calculate leak rate (MB per 1000 updates)
        analysis.leakRate = (results.memoryGrowthMB / results.updateCount) * 1000;
        
        // Determine leak severity
        if (analysis.leakRate > 10) {
            analysis.hasLeaks = true;
            analysis.leakSeverity = 'critical';
            analysis.recommendations.push('Critical memory leak detected - immediate investigation required');
        } else if (analysis.leakRate > 5) {
            analysis.hasLeaks = true;
            analysis.leakSeverity = 'high';
            analysis.recommendations.push('High memory leak rate detected - optimization needed');
        } else if (analysis.leakRate > 2) {
            analysis.hasLeaks = true;
            analysis.leakSeverity = 'medium';
            analysis.recommendations.push('Moderate memory leak detected - monitor closely');
        } else if (analysis.leakRate > 0.5) {
            analysis.leakSeverity = 'low';
            analysis.recommendations.push('Minor memory growth detected - acceptable for now');
        } else {
            analysis.recommendations.push('No significant memory leaks detected');
        }
        
        return analysis;
    }

    // Print results
    printResults(results) {
        console.log("\n" + "=" * 80);
        console.log("📊 MEMORY USAGE ANALYSIS RESULTS");
        console.log("=" * 80);
        
        console.log(`Updates Processed: ${results.updateCount}`);
        console.log(`Initial Memory: ${(results.initialMemory.memory.used / 1024 / 1024).toFixed(2)} MB`);
        console.log(`Final Memory: ${(results.finalMemory.memory.used / 1024 / 1024).toFixed(2)} MB`);
        console.log(`Memory Growth: ${results.memoryGrowthMB.toFixed(2)} MB`);
        console.log(`Growth Rate: ${(results.memoryGrowthMB / results.updateCount * 1000).toFixed(3)} MB/1000 updates`);
        console.log(`GC Count: ${results.gcCount}`);
        
        // Memory snapshots analysis
        console.log("\nMemory Snapshots:");
        console.log("-" * 50);
        results.snapshots.forEach(snapshot => {
            const memoryMB = snapshot.memory.used / 1024 / 1024;
            console.log(`${snapshot.label}: ${memoryMB.toFixed(2)} MB`);
        });
        
        // Component memory metrics
        console.log("\nComponent Memory Usage:");
        console.log("-" * 50);
        Object.entries(results.componentMetrics).forEach(([name, metrics]) => {
            console.log(`${name}:`);
            console.log(`  Renders: ${metrics.renderCount}`);
            console.log(`  Memory: ${(metrics.memoryFootprint / 1024).toFixed(1)} KB`);
            console.log(`  Listeners: ${metrics.listenerCount}`);
            console.log(`  Timers: ${metrics.timerCount}`);
            console.log(`  Observers: ${metrics.observerCount}`);
        });
        
        // Memory leak analysis
        const leakAnalysis = this.analyzeMemoryLeaks(results);
        
        console.log("\n🔍 MEMORY LEAK ANALYSIS:");
        console.log("-" * 50);
        console.log(`Leak Rate: ${leakAnalysis.leakRate.toFixed(3)} MB/1000 updates`);
        console.log(`Leak Severity: ${leakAnalysis.leakSeverity}`);
        console.log(`Has Leaks: ${leakAnalysis.hasLeaks ? '⚠️  YES' : '✅ NO'}`);
        
        console.log("\n💡 RECOMMENDATIONS:");
        leakAnalysis.recommendations.forEach(rec => {
            console.log(`  • ${rec}`);
        });
        
        // Success criteria check
        console.log("\n🎯 SUCCESS CRITERIA CHECK:");
        console.log("-" * 40);
        const acceptableGrowth = results.memoryGrowthMB < 50; // Less than 50MB growth
        const noCriticalLeaks = leakAnalysis.leakSeverity !== 'critical';
        const reasonableGrowthRate = leakAnalysis.leakRate < 5;
        
        console.log(`Memory growth < 50MB: ${acceptableGrowth ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`No critical leaks: ${noCriticalLeaks ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Growth rate < 5MB/1000: ${reasonableGrowthRate ? '✅ PASS' : '❌ FAIL'}`);
        
        if (acceptableGrowth && noCriticalLeaks && reasonableGrowthRate) {
            console.log("\n🎉 MEMORY USAGE: EXCELLENT");
        } else {
            console.log("\n⚠️  MEMORY USAGE: NEEDS OPTIMIZATION");
        }
        
        return results;
    }

    // Cleanup resources
    cleanup() {
        // Clear timers
        this.timers.forEach(timerId => clearInterval(timerId));
        this.timers.clear();
        
        // Clear event listeners
        this.eventListeners.clear();
        
        // Clear observers
        this.observers.clear();
        
        // Clear components
        this.componentInstances.clear();
        
        // Force final GC
        this.forceGC();
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MemoryUsageBenchmark;
}

// Auto-run if executed directly
if (typeof window !== 'undefined') {
    // Browser environment
    window.MemoryUsageBenchmark = MemoryUsageBenchmark;
    
    // Auto-run benchmark
    const benchmark = new MemoryUsageBenchmark();
    benchmark.runMemoryBenchmark(2000)
        .then(results => {
            benchmark.printResults(results);
            benchmark.cleanup();
        })
        .catch(error => {
            console.error('Benchmark error:', error);
            benchmark.cleanup();
        });
} else if (typeof global !== 'undefined') {
    // Node.js environment
    global.MemoryUsageBenchmark = MemoryUsageBenchmark;
}
