/**
 * Frontend Logic Parity Test
 * Launches frontend using Puppeteer and captures displayed values from UI components
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class FrontendParityTest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.frontendUrl = 'http://localhost:3000';
        this.backendUrl = 'http://localhost:8000';
        this.testData = null;
        this.comparisons = [];
        this.capturedValues = {};
    }
    
    async initialize() {
        console.log('🔧 Initializing frontend parity test...');
        
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
            if (response.url().includes('/metrics') || response.url().includes('/signals')) {
                console.log('API Response:', response.url(), response.status());
            }
        });
        
        console.log('✅ Browser initialized');
    }
    
    async cleanup() {
        console.log('🧹 Cleaning up frontend parity test...');
        
        if (this.browser) {
            await this.browser.close();
        }
        
        console.log('✅ Cleanup complete');
    }
    
    async loadTestData() {
        console.log('📂 Loading test data from backend-API parity test...');
        
        try {
            const dataPath = path.join(__dirname, 'backend_api_parity_data.json');
            const rawData = fs.readFileSync(dataPath, 'utf8');
            const data = JSON.parse(rawData);
            
            this.testData = data.test_data;
            console.log(`✅ Loaded ${this.testData.length} test scenarios`);
            
            return true;
        } catch (error) {
            console.error('❌ Failed to load test data:', error.message);
            return false;
        }
    }
    
    async navigateToFrontend() {
        console.log('🌐 Navigating to frontend...');
        
        try {
            await this.page.goto(this.frontendUrl, { 
                waitUntil: 'networkidle2', 
                timeout: 15000 
            });
            
            // Wait for key components to load
            await this.page.waitForSelector('[data-testid="market-data-table"]', { timeout: 10000 });
            await this.page.waitForSelector('[data-testid="signal-panel"]', { timeout: 10000 });
            await this.page.waitForSelector('[data-testid="metrics-panel"]', { timeout: 10000 });
            
            console.log('✅ Frontend loaded successfully');
            return true;
            
        } catch (error) {
            console.error('❌ Frontend navigation failed:', error.message);
            return false;
        }
    }
    
    async simulateMarketUpdate(testScenario) {
        console.log(`🔄 Simulating market update for ${testScenario.test_id}...`);
        
        try {
            // Send market data to backend to trigger updates
            const response = await this.page.evaluate(async (backendUrl, metrics) => {
                const response = await fetch(`${backendUrl}/api/v1/market/update`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(metrics)
                });
                
                return {
                    status: response.status,
                    ok: response.ok
                };
            }, this.backendUrl, testScenario.live_metrics);
            
            if (response.ok) {
                console.log('✅ Market update sent successfully');
                
                // Wait for frontend to update
                await this.page.waitForTimeout(3000);
                
                return true;
            } else {
                console.error(`❌ Market update failed: ${response.status}`);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Market update error:', error.message);
            return false;
        }
    }
    
    async captureUIValues(testScenario) {
        console.log(`📸 Capturing UI values for ${testScenario.test_id}...`);
        
        const capturedValues = {};
        
        try {
            // Capture PCR value
            const pcrValue = await this.page.evaluate(() => {
                const pcrElement = document.querySelector('[data-testid="pcr-value"]');
                return pcrElement ? pcrElement.textContent : null;
            });
            capturedValues.pcr = pcrValue;
            
            // Capture Net Gamma value
            const netGammaValue = await this.page.evaluate(() => {
                const gammaElement = document.querySelector('[data-testid="net-gamma-value"]');
                return gammaElement ? gammaElement.textContent : null;
            });
            capturedValues.net_gamma = netGammaValue;
            
            // Capture Support value
            const supportValue = await this.page.evaluate(() => {
                const supportElement = document.querySelector('[data-testid="support-value"]');
                return supportElement ? supportElement.textContent : null;
            });
            capturedValues.support = supportValue;
            
            // Capture Resistance value
            const resistanceValue = await this.page.evaluate(() => {
                const resistanceElement = document.querySelector('[data-testid="resistance-value"]');
                return resistanceElement ? resistanceElement.textContent : null;
            });
            capturedValues.resistance = resistanceValue;
            
            // Capture Signal value
            const signalValue = await this.page.evaluate(() => {
                const signalElement = document.querySelector('[data-testid="latest-signal"]');
                return signalElement ? signalElement.textContent : null;
            });
            capturedValues.signal = signalValue;
            
            // Capture Confidence value
            const confidenceValue = await this.page.evaluate(() => {
                const confidenceElement = document.querySelector('[data-testid="signal-confidence"]');
                return confidenceElement ? confidenceElement.textContent : null;
            });
            capturedValues.confidence = confidenceValue;
            
            console.log('✅ UI values captured:', capturedValues);
            
            return capturedValues;
            
        } catch (error) {
            console.error('❌ UI value capture error:', error.message);
            return null;
        }
    }
    
    parseNumericValue(value) {
        // Parse numeric value from string
        if (value === null || value === undefined) {
            return null;
        }
        
        // Remove common formatting characters
        const cleanValue = value.toString().replace(/[,|%]/g, '').trim();
        
        // Extract number
        const match = cleanValue.match(/-?\d+\.?\d*/);
        if (match) {
            return parseFloat(match[0]);
        }
        
        return null;
    }
    
    compareValues(apiValue, frontendValue, field) {
        // Compare API and frontend values
        const apiNum = this.parseNumericValue(apiValue);
        const frontendNum = this.parseNumericValue(frontendValue);
        
        if (apiNum === null && frontendNum === null) {
            return true; // Both null, consider as match
        }
        
        if (apiNum === null || frontendNum === null) {
            return false; // One null, one not null
        }
        
        // For numeric values, use tolerance
        const tolerance = 0.01;
        const match = Math.abs(apiNum - frontendNum) <= tolerance;
        
        console.log(`  ${field}: API=${apiNum}, Frontend=${frontendNum} -> ${match ? 'PASS' : 'FAIL'}`);
        
        return match;
    }
    
    async runParityTest(testScenario) {
        // Run parity test for a single scenario
        console.log(`\n🔍 Running frontend parity test ${testScenario.test_id}...`);
        
        // Simulate market update
        const updateSuccess = await this.simulateMarketUpdate(testScenario);
        if (!updateSuccess) {
            return {
                test_id: testScenario.test_id,
                success: false,
                error: 'Market update failed'
            };
        }
        
        // Capture UI values
        const uiValues = await this.captureUIValues(testScenario);
        if (!uiValues) {
            return {
                test_id: testScenario.test_id,
                success: false,
                error: 'UI value capture failed'
            };
        }
        
        // Store captured values
        this.capturedValues[testScenario.test_id] = uiValues;
        
        return {
            test_id: testScenario.test_id,
            success: true,
            ui_values: uiValues
        };
    }
    
    async runAllTests() {
        // Run all frontend parity tests
        console.log('🚀 Starting Frontend Logic Parity Tests');
        console.log('=' * 60);
        
        // Load test data
        const dataLoaded = await this.loadTestData();
        if (!dataLoaded) {
            return [];
        }
        
        await this.initialize();
        
        try {
            // Navigate to frontend
            const navSuccess = await this.navigateToFrontend();
            if (!navSuccess) {
                return [];
            }
            
            const results = [];
            
            // Run tests for each scenario
            for (const testScenario of this.testData) {
                const result = await this.runParityTest(testScenario);
                results.push(result);
                
                if (!result.success) {
                    console.error(`❌ Test ${testScenario.test_id} failed: ${result.error}`);
                }
                
                // Wait between tests
                await this.page.waitForTimeout(2000);
            }
            
            return results;
            
        } finally {
            await this.cleanup();
        }
    }
    
    generateComparisonTable() {
        // Generate comparison table for report
        if (!this.testData || !this.capturedValues) {
            return "| No data available for comparison |";
        }
        
        const tableLines = [];
        tableLines.push("| Field | Backend | API | Frontend | Status |");
        tableLines.push("| ----- | ------- | --- | -------- | ------ |");
        
        // Load backend-API comparison data
        let backendApiData = {};
        try {
            const dataPath = path.join(__dirname, 'backend_api_parity_data.json');
            const rawData = fs.readFileSync(dataPath, 'utf8');
            const data = JSON.parse(rawData);
            
            // Create field mapping for each test
            data.test_data.forEach(test => {
                backendApiData[test.test_id] = {
                    backend: test.backend_fields,
                    api: test.api_fields
                };
            });
        } catch (error) {
            console.error('Failed to load backend-API data:', error.message);
        }
        
        // Compare values across all test scenarios
        for (const testScenario of this.testData) {
            const testId = testScenario.test_id;
            const backendFields = backendApiData[testId]?.backend || {};
            const apiFields = backendApiData[testId]?.api || {};
            const uiValues = this.capturedValues[testId] || {};
            
            for (const field of ['pcr', 'net_gamma', 'support', 'resistance', 'signal', 'confidence']) {
                const backendVal = backendFields[field];
                const apiVal = apiFields[field];
                const frontendVal = uiValues[field];
                
                // Compare all three
                const backendApiMatch = this.compareValues(backendVal, apiVal, field);
                const apiFrontendMatch = this.compareValues(apiVal, frontendVal, field);
                const backendFrontendMatch = this.compareValues(backendVal, frontendVal, field);
                const overallMatch = backendApiMatch && apiFrontendMatch && backendFrontendMatch;
                
                const status = overallMatch ? 'PASS' : 'FAIL';
                
                // Format values for display
                const backendDisplay = backendVal !== null ? backendVal.toString() : 'N/A';
                const apiDisplay = apiVal !== null ? apiVal.toString() : 'N/A';
                const frontendDisplay = frontendVal !== null ? frontendVal.toString() : 'N/A';
                
                tableLines.push(`| ${field} | ${backendDisplay} | ${apiDisplay} | ${frontendDisplay} | ${status} |`);
            }
        }
        
        return '\n'.join(tableLines);
    }
    
    async saveResults() {
        // Save test results
        const results = {
            test_data: this.testData,
            captured_values: this.capturedValues,
            comparisons: this.comparisons,
            timestamp: new Date().toISOString()
        };
        
        const filename = 'frontend_parity_results.json';
        fs.writeFileSync(filename, JSON.stringify(results, null, 2));
        console.log(`✅ Results saved to ${filename}`);
    }
}

async function runFrontendParityTests() {
    const testSuite = new FrontendParityTest();
    
    try {
        const results = await testSuite.runAllTests();
        
        // Generate comparison table
        const comparisonTable = testSuite.generateComparisonTable();
        
        // Save results
        await testSuite.saveResults();
        
        return {
            results: results,
            comparisonTable: comparisonTable
        };
        
    } catch (error) {
        console.error('❌ Frontend parity test error:', error);
        return {
            results: [],
            comparisonTable: '| Test failed with error |'
        };
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FrontendParityTest, runFrontendParityTests };
}

// Auto-run if executed directly
if (typeof window !== 'undefined') {
    // Browser environment
    window.FrontendParityTest = FrontendParityTest;
} else if (typeof global !== 'undefined') {
    // Node.js environment
    global.FrontendParityTest = FrontendParityTest;
    
    // Auto-run tests
    runFrontendParityTests()
        .then(result => {
            console.log('\n' + '=' * 60);
            console.log('Frontend Logic Parity Test Complete');
            console.log('=' * 60);
            console.log(result.comparisonTable);
        })
        .catch(error => console.error('Test error:', error));
}
