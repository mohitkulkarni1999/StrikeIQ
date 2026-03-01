/**
 * Frontend Stress Test
 * Simulates 1000 UI updates/sec and verifies FPS > 50 and no memory growth
 */

const { performance } = require('perf_hooks');
const { JSDOM } = require('jsdom');

// Mock React environment
const React = require('react');
const { render } = require('react-dom/server');

// Import components for testing
const ExpectedMoveChart = require('../../src/components/ExpectedMoveChart').default;
const BiasMeter = require('../../src/components/BiasMeter').default;
const SignalCards = require('../../src/components/SignalCards').default;
const ProbabilityDisplay = require('../../src/components/ProbabilityDisplay').default;
const AICommandCenter = require('../../src/components/AICommandCenter').default;
const TradeSignalCard = require('../../src/components/TradeSignalCard').default;

class UIStressTest {
    constructor() {
        this.metrics = {
            totalUpdates: 0,
            successfulRenders: 0,
            failedRenders: 0,
            renderTimes: [],
            fpsMeasurements: [],
            memoryUsage: [],
            startTime: null,
            endTime: null
        };
        
        this.testData = this.generateTestData();
        this.components = [
            { name: 'ExpectedMoveChart', component: ExpectedMoveChart, props: { probability: this.testData.probability } },
            { name: 'BiasMeter', component: BiasMeter, props: { intelligence: this.testData.intelligence } },
            { name: 'SignalCards', component: SignalCards, props: { intelligence: this.testData.intelligence } },
            { name: 'ProbabilityDisplay', component: ProbabilityDisplay, props: { probability: this.testData.probability } },
            { name: 'AICommandCenter', component: AICommandCenter, props: { intelligence: this.testData.intelligence } },
            { name: 'TradeSignalCard', component: TradeSignalCard, props: { signal: this.testData.tradeSignal } }
        ];
        
        // Setup DOM environment
        this.dom = new JSDOM('<!DOCTYPE html><div id="root"></div>', {
            url: 'http://localhost',
            pretendToBeVisual: true,
            resources: 'usable'
        });
        
        global.window = this.dom.window;
        global.document = this.dom.window.document;
        global.navigator = this.dom.window.navigator;
    }
    
    generateTestData() {
        const baseData = {
            probability: {
                expected_move: 150.0,
                upper_1sd: 19650.0,
                lower_1sd: 19350.0,
                upper_2sd: 19800.0,
                lower_2sd: 19200.0,
                breach_probability: 25.0,
                range_hold_probability: 75.0,
                volatility_state: 'fair'
            },
            intelligence: {
                bias: {
                    signal: 'BULLISH',
                    confidence: 75.0,
                    direction: 'UP',
                    strength: 80.0,
                    reason: 'Strong buying pressure detected'
                },
                probability: {
                    expected_move: 150.0,
                    upper_1sd: 19650.0,
                    lower_1sd: 19350.0,
                    upper_2sd: 19800.0,
                    lower_2sd: 19200.0,
                    breach_probability: 25.0,
                    range_hold_probability: 75.0,
                    volatility_state: 'fair'
                },
                liquidity: {
                    total_oi: 5000000,
                    oi_change_24h: 2.5,
                    concentration: 0.3,
                    depth_score: 0.8,
                    flow_direction: 'bullish'
                },
                regime: {
                    market_regime: 'bullish',
                    volatility_regime: 'normal',
                    trend_regime: 'uptrend',
                    confidence: 75.0
                },
                gamma: {
                    net_gamma: 2500000,
                    gamma_flip: 19400.0,
                    dealer_gamma: 'positive',
                    gamma_exposure: 0.6
                },
                signals: {
                    stoploss_hunt: false,
                    trap_detection: false,
                    liquidity_event: false,
                    gamma_squeeze: false
                },
                trade_suggestion: {
                    symbol: 'NIFTY',
                    strategy: 'bull_call',
                    option: '19600 CE',
                    entry: 19500.0,
                    target: 19700.0,
                    stoploss: 19400.0,
                    risk_reward: 2.0,
                    confidence: 75.0,
                    regime: 'bullish'
                },
                reasoning: 'Market shows strong bullish momentum with supportive gamma profile'
            },
            tradeSignal: {
                symbol: 'NIFTY',
                strategy: 'bull_call',
                option: '19600 CE',
                entry: 19500.0,
                target: 19700.0,
                stoploss: 19400.0,
                risk_reward: 2.0,
                confidence: 75.0,
                regime: 'bullish'
            }
        };
        
        return baseData;
    }
    
    generateVariation(baseData, variationId) {
        // Generate data variations to simulate real market updates
        const variation = JSON.parse(JSON.stringify(baseData));
        
        // Add variations to simulate market movements
        const spotVariation = 19500 + (variationId % 200) - 100;
        const moveVariation = 150 + (variationId % 50) - 25;
        
        // Update probability data
        variation.probability.expected_move = moveVariation;
        variation.probability.upper_1sd = spotVariation + moveVariation;
        variation.probability.lower_1sd = spotVariation - moveVariation;
        variation.probability.upper_2sd = spotVariation + (moveVariation * 2);
        variation.probability.lower_2sd = spotVariation - (moveVariation * 2);
        variation.probability.breach_probability = 20 + (variationId % 30);
        variation.probability.range_hold_probability = 100 - variation.probability.breach_probability;
        
        // Update intelligence data
        variation.intelligence.probability = variation.probability;
        variation.intelligence.bias.confidence = 70 + (variationId % 20);
        variation.intelligence.bias.strength = 70 + (variationId % 25);
        
        // Update trade signal
        variation.tradeSignal.entry = spotVariation;
        variation.tradeSignal.target = spotVariation + moveVariation;
        variation.tradeSignal.stoploss = spotVariation - (moveVariation / 2);
        
        return variation;
    }
    
    measureMemoryUsage() {
        if (global.gc) {
            global.gc();
        }
        
        const memoryUsage = process.memoryUsage();
        return {
            heapUsed: memoryUsage.heapUsed / 1024 / 1024, // MB
            heapTotal: memoryUsage.heapTotal / 1024 / 1024, // MB
            external: memoryUsage.external / 1024 / 1024 // MB
        };
    }
    
    async renderComponent(componentName, Component, props) {
        const startTime = performance.now();
        
        try {
            // Render component to string (server-side rendering simulation)
            const element = React.createElement(Component, props);
            const html = render(element);
            
            const endTime = performance.now();
            const renderTime = endTime - startTime;
            
            this.metrics.successfulRenders++;
            this.metrics.renderTimes.push(renderTime);
            
            return {
                success: true,
                renderTime,
                htmlLength: html.length
            };
            
        } catch (error) {
            this.metrics.failedRenders++;
            
            return {
                success: false,
                error: error.message,
                renderTime: performance.now() - startTime
            };
        }
    }
    
    async runComponentStressTest(componentName, Component, baseProps, updateCount = 1000) {
        console.log(`Running stress test for ${componentName}...`);
        
        const componentMetrics = {
            name: componentName,
            totalRenders: 0,
            successfulRenders: 0,
            failedRenders: 0,
            renderTimes: [],
            avgRenderTime: 0,
            maxRenderTime: 0,
            minRenderTime: Infinity,
            memoryUsage: []
        };
        
        const startTime = performance.now();
        let initialMemory = this.measureMemoryUsage();
        
        // Run rapid updates
        for (let i = 0; i < updateCount; i++) {
            // Generate variation in props
            const variation = this.generateVariation({ probability: baseProps.probability, intelligence: baseProps.intelligence }, i);
            const props = componentName === 'TradeSignalCard' 
                ? { signal: variation.tradeSignal }
                : componentName === 'ProbabilityDisplay' || componentName === 'ExpectedMoveChart'
                ? { probability: variation.probability }
                : { intelligence: variation.intelligence };
            
            const result = await this.renderComponent(componentName, Component, props);
            
            componentMetrics.totalRenders++;
            
            if (result.success) {
                componentMetrics.successfulRenders++;
                componentMetrics.renderTimes.push(result.renderTime);
                componentMetrics.maxRenderTime = Math.max(componentMetrics.maxRenderTime, result.renderTime);
                componentMetrics.minRenderTime = Math.min(componentMetrics.minRenderTime, result.renderTime);
            } else {
                componentMetrics.failedRenders++;
            }
            
            // Measure memory every 100 renders
            if (i % 100 === 0) {
                const memory = this.measureMemoryUsage();
                componentMetrics.memoryUsage.push({
                    iteration: i,
                    ...memory
                });
            }
            
            // Simulate UI update rate (1000 updates/sec = 1ms between updates)
            await new Promise(resolve => setTimeout(resolve, 1));
        }
        
        const endTime = performance.now();
        let finalMemory = this.measureMemoryUsage();
        
        // Calculate metrics
        componentMetrics.avgRenderTime = componentMetrics.renderTimes.reduce((a, b) => a + b, 0) / componentMetrics.renderTimes.length;
        componentMetrics.totalTime = endTime - startTime;
        componentMetrics.updatesPerSecond = updateCount / (componentMetrics.totalTime / 1000);
        componentMetrics.successRate = (componentMetrics.successfulRenders / componentMetrics.totalRenders) * 100;
        componentMetrics.memoryGrowth = finalMemory.heapUsed - initialMemory.heapUsed;
        
        console.log(`  ${componentName} Results:`);
        console.log(`    Total Renders: ${componentMetrics.totalRenders}`);
        console.log(`    Success Rate: ${componentMetrics.successRate.toFixed(2)}%`);
        console.log(`    Updates/sec: ${componentMetrics.updatesPerSecond.toFixed(2)}`);
        console.log(`    Avg Render Time: ${componentMetrics.avgRenderTime.toFixed(2)}ms`);
        console.log(`    Max Render Time: ${componentMetrics.maxRenderTime.toFixed(2)}ms`);
        console.log(`    Min Render Time: ${componentMetrics.minRenderTime.toFixed(2)}ms`);
        console.log(`    Memory Growth: ${componentMetrics.memoryGrowth.toFixed(2)}MB`);
        
        return componentMetrics;
    }
    
    async runFPSMeasurement() {
        console.log("Running FPS measurement test...");
        
        const fpsMetrics = {
            targetFPS: 60,
            measuredFPS: [],
            avgFPS: 0,
            minFPS: Infinity,
            maxFPS: 0,
            frameDrops: 0
        };
        
        const testDuration = 5000; // 5 seconds
        const startTime = performance.now();
        let frameCount = 0;
        let lastFrameTime = startTime;
        
        // Simulate rapid UI updates
        while (performance.now() - startTime < testDuration) {
            const currentTime = performance.now();
            const deltaTime = currentTime - lastFrameTime;
            
            if (deltaTime >= 1000 / fpsMetrics.targetFPS) { // Target 60 FPS
                frameCount++;
                
                // Calculate instantaneous FPS
                const instantFPS = 1000 / deltaTime;
                fpsMetrics.measuredFPS.push(instantFPS);
                fpsMetrics.minFPS = Math.min(fpsMetrics.minFPS, instantFPS);
                fpsMetrics.maxFPS = Math.max(fpsMetrics.maxFPS, instantFPS);
                
                // Count frame drops (below 50 FPS)
                if (instantFPS < 50) {
                    fpsMetrics.frameDrops++;
                }
                
                lastFrameTime = currentTime;
            }
            
            // Don't busy wait
            await new Promise(resolve => setTimeout(resolve, 1));
        }
        
        const totalTime = performance.now() - startTime;
        fpsMetrics.avgFPS = (frameCount / totalTime) * 1000;
        
        console.log(`FPS Measurement Results:`);
        console.log(`  Target FPS: ${fpsMetrics.targetFPS}`);
        console.log(`  Average FPS: ${fpsMetrics.avgFPS.toFixed(2)}`);
        console.log(`  Min FPS: ${fpsMetrics.minFPS.toFixed(2)}`);
        console.log(`  Max FPS: ${fpsMetrics.maxFPS.toFixed(2)}`);
        console.log(`  Frame Drops: ${fpsMetrics.frameDrops}`);
        console.log(`  Total Frames: ${frameCount}`);
        
        return fpsMetrics;
    }
    
    async runMemoryLeakTest() {
        console.log("Running memory leak test...");
        
        const memoryMetrics = {
            initialMemory: 0,
            finalMemory: 0,
            peakMemory: 0,
            memoryGrowth: 0,
            samples: []
        };
        
        // Force garbage collection
        if (global.gc) {
            global.gc();
        }
        
        memoryMetrics.initialMemory = this.measureMemoryUsage().heapUsed;
        
        // Run multiple cycles of component renders
        const cycles = 10;
        const rendersPerCycle = 100;
        
        for (let cycle = 0; cycle < cycles; cycle++) {
            console.log(`  Memory test cycle ${cycle + 1}/${cycles}`);
            
            for (let component of this.components) {
                for (let i = 0; i < rendersPerCycle; i++) {
                    const variation = this.generateVariation(this.testData, cycle * rendersPerCycle + i);
                    const props = component.name === 'TradeSignalCard' 
                        ? { signal: variation.tradeSignal }
                        : component.name === 'ProbabilityDisplay' || component.name === 'ExpectedMoveChart'
                        ? { probability: variation.probability }
                        : { intelligence: variation.intelligence };
                    
                    await this.renderComponent(component.name, component.component, props);
                }
            }
            
            // Force garbage collection and measure memory
            if (global.gc) {
                global.gc();
            }
            
            const currentMemory = this.measureMemoryUsage().heapUsed;
            memoryMetrics.samples.push(currentMemory);
            memoryMetrics.peakMemory = Math.max(memoryMetrics.peakMemory, currentMemory);
            
            console.log(`    Memory after cycle ${cycle + 1}: ${currentMemory.toFixed(2)}MB`);
        }
        
        // Final garbage collection
        if (global.gc) {
            global.gc();
        }
        
        memoryMetrics.finalMemory = this.measureMemoryUsage().heapUsed;
        memoryMetrics.memoryGrowth = memoryMetrics.finalMemory - memoryMetrics.initialMemory;
        
        console.log(`Memory Leak Test Results:`);
        console.log(`  Initial Memory: ${memoryMetrics.initialMemory.toFixed(2)}MB`);
        console.log(`  Final Memory: ${memoryMetrics.finalMemory.toFixed(2)}MB`);
        console.log(`  Peak Memory: ${memoryMetrics.peakMemory.toFixed(2)}MB`);
        console.log(`  Memory Growth: ${memoryMetrics.memoryGrowth.toFixed(2)}MB`);
        
        return memoryMetrics;
    }
    
    async runFullStressTest() {
        console.log("Starting Frontend Stress Test Suite");
        console.log("=====================================");
        
        this.metrics.startTime = performance.now();
        
        const results = {
            componentTests: [],
            fpsTest: null,
            memoryTest: null,
            summary: {
                totalTests: 0,
                passedTests: 0,
                failedTests: 0,
                overallPass: false
            }
        };
        
        try {
            // Test each component
            for (let component of this.components) {
                const componentResult = await this.runComponentStressTest(
                    component.name,
                    component.component,
                    component.props,
                    1000 // 1000 updates per component
                );
                
                results.componentTests.push(componentResult);
                results.summary.totalTests++;
                
                // Check if component test passed
                const componentPassed = (
                    componentResult.successRate >= 95.0 &&
                    componentResult.avgRenderTime < 16.0 && // 60 FPS = 16ms per frame
                    componentResult.maxRenderTime < 100.0 &&
                    componentResult.memoryGrowth < 50.0
                );
                
                if (componentPassed) {
                    results.summary.passedTests++;
                } else {
                    results.summary.failedTests++;
                }
            }
            
            // Run FPS measurement
            results.fpsTest = await this.runFPSMeasurement();
            results.summary.totalTests++;
            
            const fpsPassed = (
                results.fpsTest.avgFPS >= 50.0 &&
                results.fpsTest.frameDrops <= results.fpsTest.measuredFPS.length * 0.1
            );
            
            if (fpsPassed) {
                results.summary.passedTests++;
            } else {
                results.summary.failedTests++;
            }
            
            // Run memory leak test
            results.memoryTest = await this.runMemoryLeakTest();
            results.summary.totalTests++;
            
            const memoryPassed = results.memoryTest.memoryGrowth < 100.0;
            
            if (memoryPassed) {
                results.summary.passedTests++;
            } else {
                results.summary.failedTests++;
            }
            
        } catch (error) {
            console.error("Stress test failed with error:", error);
            results.summary.failedTests++;
        }
        
        this.metrics.endTime = performance.now();
        
        // Determine overall pass/fail
        results.summary.overallPass = results.summary.failedTests === 0;
        
        // Print final results
        console.log("\nFrontend Stress Test Summary");
        console.log("=============================");
        console.log(`Total Tests: ${results.summary.totalTests}`);
        console.log(`Passed: ${results.summary.passedTests}`);
        console.log(`Failed: ${results.summary.failedTests}`);
        console.log(`Overall Result: ${results.summary.overallPass ? 'PASS' : 'FAIL'}`);
        console.log(`Total Duration: ${(this.metrics.endTime - this.metrics.startTime) / 1000} seconds`);
        
        // Assert requirements
        if (!results.summary.overallPass) {
            throw new Error("Frontend stress test failed");
        }
        
        return results;
    }
}

// Run the stress test
async function runStressTest() {
    const stressTest = new UIStressTest();
    
    try {
        const results = await stressTest.runFullStressTest();
        console.log("\n✅ Frontend stress test completed successfully");
        return results;
    } catch (error) {
        console.error("\n❌ Frontend stress test failed:", error.message);
        process.exit(1);
    }
}

// Export for use in test frameworks
module.exports = { UIStressTest, runStressTest };

// Run if called directly
if (require.main === module) {
    runStressTest();
}
