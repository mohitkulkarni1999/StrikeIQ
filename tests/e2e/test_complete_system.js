/**
 * Complete System End-to-End Test Suite
 * Tests full system flow from market update to frontend UI update
 */

const puppeteer = require('puppeteer');
const axios = require('axios');

class CompleteSystemE2ETest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.backendUrl = 'http://localhost:8000';
        this.frontendUrl = 'http://localhost:3000';
        this.testResults = [];
        this.wsMessages = [];
    }
    
    async initialize() {
        console.log('🔧 Initializing E2E test environment...');
        
        // Launch browser
        this.browser = await puppeteer.launch({
            headless: false, // Set to true for CI/CD
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        this.page = await this.browser.newPage();
        
        // Enable console logging
        this.page.on('console', msg => {
            console.log('Browser Console:', msg.text());
        });
        
        // Enable network monitoring
        this.page.on('response', response => {
            console.log('Network Response:', response.url(), response.status());
        });
        
        console.log('✅ Browser initialized');
    }
    
    async cleanup() {
        console.log('🧹 Cleaning up E2E test environment...');
        
        if (this.browser) {
            await this.browser.close();
        }
        
        console.log('✅ Cleanup complete');
    }
    
    async checkBackendHealth() {
        console.log('🔍 Checking backend health...');
        
        try {
            const response = await axios.get(`${this.backendUrl}/health`, { timeout: 5000 });
            
            if (response.status === 200) {
                console.log('✅ Backend is healthy');
                return true;
            } else {
                console.log(`❌ Backend health check failed: ${response.status}`);
                return false;
            }
        } catch (error) {
            console.log(`❌ Backend health check error: ${error.message}`);
            return false;
        }
    }
    
    async checkFrontendHealth() {
        console.log('🔍 Checking frontend health...');
        
        try {
            await this.page.goto(this.frontendUrl, { waitUntil: 'networkidle2', timeout: 10000 });
            
            // Check if page loaded successfully
            const title = await this.page.title();
            
            if (title && title.includes('StrikeIQ')) {
                console.log('✅ Frontend is healthy');
                return true;
            } else {
                console.log(`❌ Frontend title check failed: ${title}`);
                return false;
            }
        } catch (error) {
            console.log(`❌ Frontend health check error: ${error.message}`);
            return false;
        }
    }
    
    async simulateMarketUpdate() {
        console.log('🔄 Simulating market update...');
        
        try {
            // Simulate market data update via API
            const marketData = {
                symbol: 'BANKNIFTY',
                price: 45123.45,
                change: 123.45,
                changePercent: 0.27,
                volume: 2500000,
                timestamp: Date.now(),
                pcr: 1.15,
                gamma: -25000,
                rsi: 65.5,
                regime: 'BULLISH',
                volatility_regime: 'HIGH'
            };
            
            const response = await axios.post(
                `${this.backendUrl}/api/v1/market/update`,
                marketData,
                { timeout: 5000 }
            );
            
            if (response.status === 200) {
                console.log('✅ Market update simulated successfully');
                return marketData;
            } else {
                console.log(`❌ Market update failed: ${response.status}`);
                return null;
            }
        } catch (error) {
            console.log(`❌ Market update error: ${error.message}`);
            return null;
        }
    }
    
    async verifySignalGeneration() {
        console.log('🔍 Verifying AI signal generation...');
        
        try {
            // Wait a moment for AI processing
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check for recent signals
            const response = await axios.get(
                `${this.backendUrl}/api/v1/signals/recent`,
                { timeout: 5000 }
            );
            
            if (response.status === 200) {
                const signals = response.data.signals || [];
                
                if (signals.length > 0) {
                    console.log(`✅ Found ${signals.length} recent signals`);
                    
                    // Return the most recent signal
                    const latestSignal = signals[0];
                    return latestSignal;
                } else {
                    console.log('❌ No recent signals found');
                    return null;
                }
            } else {
                console.log(`❌ Signal verification failed: ${response.status}`);
                return null;
            }
        } catch (error) {
            console.log(`❌ Signal verification error: ${error.message}`);
            return null;
        }
    }
    
    async verifyAPIResponse() {
        console.log('🔍 Verifying API response...');
        
        try {
            // Test metrics endpoint
            const metricsResponse = await axios.get(
                `${this.backendUrl}/metrics`,
                { timeout: 5000 }
            );
            
            if (metricsResponse.status !== 200) {
                return { passed: false, error: 'Metrics endpoint failed' };
            }
            
            const metricsData = metricsResponse.data;
            
            // Validate metrics structure
            if (!metricsData.spot_price || !metricsData.timestamp) {
                return { passed: false, error: 'Invalid metrics data structure' };
            }
            
            // Test signals endpoint
            const signalsResponse = await axios.get(
                `${this.backendUrl}/signals`,
                { timeout: 5000 }
            );
            
            if (signalsResponse.status !== 200) {
                return { passed: false, error: 'Signals endpoint failed' };
            }
            
            const signalsData = signalsResponse.data;
            
            // Validate signals structure
            if (!Array.isArray(signalsData.signals)) {
                return { passed: false, error: 'Invalid signals data structure' };
            }
            
            console.log('✅ API responses are valid');
            return { passed: true };
            
        } catch (error) {
            console.log(`❌ API verification error: ${error.message}`);
            return { passed: false, error: error.message };
        }
    }
    
    async verifyFrontendUpdate(signal) {
        console.log('🔍 Verifying frontend UI update...');
        
        try {
            // Navigate to the frontend page
            await this.page.goto(this.frontendUrl, { waitUntil: 'networkidle2', timeout: 10000 });
            
            // Wait for components to load
            await this.page.waitForSelector('[data-testid="market-data-table"]', { timeout: 5000 });
            await this.page.waitForSelector('[data-testid="signal-panel"]', { timeout: 5000 });
            
            // Check market data table
            const marketDataElement = await this.page.$('[data-testid="market-data-table"]');
            const marketDataText = await this.page.evaluate(el => el.textContent, marketDataElement);
            
            if (!marketDataText || !marketDataText.includes('BANKNIFTY')) {
                return { passed: false, error: 'Market data not displayed correctly' };
            }
            
            // Check signal panel
            const signalPanelElement = await this.page.$('[data-testid="signal-panel"]');
            const signalPanelText = await this.page.evaluate(el => el.textContent, signalPanelElement);
            
            if (!signalPanelText) {
                return { passed: false, error: 'Signal panel not displaying content' };
            }
            
            // Wait for WebSocket connection and updates
            await this.page.waitForFunction(
                () => {
                    return window.websocketConnected === true;
                },
                { timeout: 10000 }
            );
            
            // Wait for UI updates
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            // Check if signal is displayed
            const signalElements = await this.page.$$('[data-testid="signal-item"]');
            
            if (signalElements.length === 0) {
                return { passed: false, error: 'No signals displayed in UI' };
            }
            
            // Verify signal content
            const firstSignalElement = signalElements[0];
            const signalText = await this.page.evaluate(el => el.textContent, firstSignalElement);
            
            if (!signalText) {
                return { passed: false, error: 'Signal content not displayed' };
            }
            
            console.log('✅ Frontend UI updated correctly');
            return { passed: true };
            
        } catch (error) {
            console.log(`❌ Frontend update verification error: ${error.message}`);
            return { passed: false, error: error.message };
        }
    }
    
    async testWebSocketConnection() {
        console.log('🔍 Testing WebSocket connection...');
        
        try {
            // Navigate to frontend
            await this.page.goto(this.frontendUrl, { waitUntil: 'networkidle2', timeout: 10000 });
            
            // Inject WebSocket test code
            await this.page.evaluate(() => {
                window.websocketConnected = false;
                window.websocketMessages = [];
                
                // Mock WebSocket for testing
                const originalWebSocket = window.WebSocket;
                window.WebSocket = function(url) {
                    const ws = new originalWebSocket(url);
                    
                    ws.addEventListener('open', () => {
                        window.websocketConnected = true;
                        console.log('WebSocket connected');
                    });
                    
                    ws.addEventListener('message', (event) => {
                        try {
                            const message = JSON.parse(event.data);
                            window.websocketMessages.push(message);
                            console.log('WebSocket message received:', message);
                        } catch (e) {
                            console.log('WebSocket message parse error:', e);
                        }
                    });
                    
                    return ws;
                };
            });
            
            // Wait for WebSocket connection
            await this.page.waitForFunction(
                () => window.websocketConnected === true,
                { timeout: 10000 }
            );
            
            const isConnected = await this.page.evaluate(() => window.websocketConnected);
            
            if (isConnected) {
                console.log('✅ WebSocket connection successful');
                return { passed: true };
            } else {
                return { passed: false, error: 'WebSocket connection failed' };
            }
            
        } catch (error) {
            console.log(`❌ WebSocket test error: ${error.message}`);
            return { passed: false, error: error.message };
        }
    }
    
    async runCompleteFlowTest() {
        console.log('🔄 Running complete system flow test...');
        
        try {
            // Step 1: Simulate market update
            const marketData = await this.simulateMarketUpdate();
            if (!marketData) {
                return { testName: 'Complete Flow', passed: false, error: 'Market update failed' };
            }
            
            // Step 2: Verify signal generation
            const signal = await this.verifySignalGeneration();
            if (!signal) {
                return { testName: 'Complete Flow', passed: false, error: 'Signal generation failed' };
            }
            
            // Step 3: Verify API response
            const apiResult = await this.verifyAPIResponse();
            if (!apiResult.passed) {
                return { testName: 'Complete Flow', passed: false, error: apiResult.error };
            }
            
            // Step 4: Verify frontend update
            const frontendResult = await this.verifyFrontendUpdate(signal);
            if (!frontendResult.passed) {
                return { testName: 'Complete Flow', passed: false, error: frontendResult.error };
            }
            
            console.log('✅ Complete system flow test passed');
            return { testName: 'Complete Flow', passed: true };
            
        } catch (error) {
            console.log(`❌ Complete flow test error: ${error.message}`);
            return { testName: 'Complete Flow', passed: false, error: error.message };
        }
    }
    
    async runAllTests() {
        console.log('🚀 Starting Complete System End-to-End Tests');
        console.log('=' * 60);
        
        await this.initialize();
        
        this.testResults = [];
        
        try {
            // Test 1: Backend Health
            const backendHealthy = await this.checkBackendHealth();
            this.testResults.push({
                testName: 'Backend Health',
                passed: backendHealthy,
                error: backendHealthy ? null : 'Backend not healthy'
            });
            
            if (!backendHealthy) {
                console.log('❌ Backend not healthy, skipping remaining tests');
                return this.testResults;
            }
            
            // Test 2: Frontend Health
            const frontendHealthy = await this.checkFrontendHealth();
            this.testResults.push({
                testName: 'Frontend Health',
                passed: frontendHealthy,
                error: frontendHealthy ? null : 'Frontend not healthy'
            });
            
            if (!frontendHealthy) {
                console.log('❌ Frontend not healthy, skipping remaining tests');
                return this.testResults;
            }
            
            // Test 3: WebSocket Connection
            const wsResult = await this.testWebSocketConnection();
            this.testResults.push(wsResult);
            
            // Test 4: Complete System Flow
            const flowResult = await this.runCompleteFlowTest();
            this.testResults.push(flowResult);
            
        } catch (error) {
            console.log(`❌ E2E test suite error: ${error.message}`);
            this.testResults.push({
                testName: 'E2E Suite',
                passed: false,
                error: error.message
            });
        } finally {
            await this.cleanup();
        }
        
        return this.testResults;
    }
    
    printSummary(results) {
        console.log('\n' + '=' * 80);
        console.log('📊 COMPLETE SYSTEM END-TO-END TEST RESULTS');
        console.log('=' * 80);
        
        const passedCount = results.filter(r => r.passed).length;
        const totalCount = results.length;
        
        console.log(`Total Tests: ${totalCount}`);
        console.log(`Passed: ${passedCount}`);
        console.log(`Failed: ${totalCount - passedCount}`);
        console.log(`Success Rate: ${(passedCount / totalCount * 100).toFixed(1)}%`);
        
        console.log('\nDetailed Results:');
        console.log('-' * 50);
        console.log(`${'Test Name'.padEnd(20)} | ${'Result'.padEnd(8)} | ${'Error'}`);
        console.log('-' * 50);
        
        results.forEach(result => {
            const status = result.passed ? '✅ PASS' : '❌ FAIL';
            const error = result.error || 'None';
            console.log(`${result.testName.padEnd(20)} | ${status.padEnd(8)} | ${error}`);
        });
        
        // Success criteria check
        console.log('\n🎯 SUCCESS CRITERIA CHECK:');
        console.log('-' * 40);
        
        const allPassed = results.every(r => r.passed);
        const backendHealthy = results.find(r => r.testName === 'Backend Health')?.passed || false;
        const frontendHealthy = results.find(r => r.testName === 'Frontend Health')?.passed || false;
        const completeFlow = results.find(r => r.testName === 'Complete Flow')?.passed || false;
        
        console.log(`All tests pass: ${allPassed ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Backend healthy: ${backendHealthy ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Frontend healthy: ${frontendHealthy ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Complete flow works: ${completeFlow ? '✅ PASS' : '❌ FAIL'}`);
        
        if (allPassed && backendHealthy && frontendHealthy && completeFlow) {
            console.log('\n🎉 COMPLETE SYSTEM E2E TESTS: ALL PASSED');
        } else {
            console.log('\n⚠️  COMPLETE SYSTEM E2E TESTS: SOME FAILED');
        }
        
        return results;
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CompleteSystemE2ETest;
}

// Auto-run if executed directly
if (typeof window !== 'undefined') {
    // Browser environment
    window.CompleteSystemE2ETest = CompleteSystemE2ETest;
} else if (typeof global !== 'undefined') {
    // Node.js environment
    global.CompleteSystemE2ETest = CompleteSystemE2ETest;
    
    // Auto-run tests
    const testSuite = new CompleteSystemE2ETest();
    testSuite.runAllTests()
        .then(results => testSuite.printSummary(results))
        .catch(error => console.error('E2E test error:', error));
}
