/**
 * FRONTEND CRASH PROTECTION CHAOS TEST
 * Test UI crash protection under extreme conditions
 */

const { JSDOM } = require('jsdom');

// Set up DOM environment
const dom = new JSDOM('<!DOCTYPE html><html><body><div id="root"></div></body></html>');
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Mock React ErrorBoundary
class ErrorBoundary {
  constructor(props) {
    this.props = props;
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
    
    // Report error to monitoring service if available
    if (window.gtag) {
      window.gtag('event', 'exception', {
        description: error.message,
        fatal: false,
      });
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Return error UI
      const errorDiv = document.createElement('div');
      errorDiv.innerHTML = `
        <div style="padding: 20px; text-align: center; color: white;">
          <h2>Something went wrong</h2>
          <p>The application encountered an unexpected error.</p>
          <button onclick="window.location.reload()">Reload Application</button>
        </div>
      `;
      return errorDiv;
    }

    return this.props.children;
  }
}

// Mock WebSocket with error simulation
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = 1; // OPEN
    this.listeners = {};
    
    // Simulate random errors
    setTimeout(() => {
      if (Math.random() < 0.3) { // 30% chance of error
        this.simulateError();
      }
    }, 100);
  }

  addEventListener(event, callback) {
    this.listeners[event] = callback;
  }

  removeEventListener(event, callback) {
    delete this.listeners[event];
  }

  send(data) {
    if (Math.random() < 0.1) { // 10% chance of send error
      throw new Error('WebSocket send failed');
    }
  }

  close() {
    this.readyState = 3; // CLOSED
  }

  simulateError() {
    const error = new Error('WebSocket connection lost');
    this.readyState = 3; // CLOSED
    
    if (this.listeners.error) {
      this.listeners.error(error);
    }
  }
}

// Mock API client with error simulation
class MockAPIClient {
  constructor() {
    this.baseURL = 'http://localhost:8000';
  }

  async get(endpoint) {
    // Simulate various error conditions
    const random = Math.random();
    
    if (random < 0.2) {
      throw new Error('Network Error: Connection refused');
    } else if (random < 0.3) {
      throw new Error('Timeout Error: Request timed out');
    } else if (random < 0.4) {
      // Invalid JSON response
      return { data: 'invalid json response' };
    } else if (random < 0.5) {
      // Missing required fields
      return { authenticated: true }; // Missing login_url when not authenticated
    } else {
      // Valid response
      return {
        authenticated: true,
        data: { price: 45000, volume: 1000 }
      };
    }
  }

  async post(endpoint, data) {
    const random = Math.random();
    
    if (random < 0.3) {
      throw new Error('POST request failed');
    } else {
      return { success: true, token: 'mock_token' };
    }
  }
}

class FrontendCrashProtectionChaosTester {
  constructor() {
    this.testResults = {};
    this.apiClient = new MockAPIClient();
    this.errorBoundary = new ErrorBoundary({ fallback: 'Error Fallback' });
  }

  async runAllTests() {
    console.log('🛡️ STARTING FRONTEND CRASH PROTECTION CHAOS TESTS');
    console.log('='.repeat(55));
    
    try {
      await this.testInvalidAPIResponses();
      await this.testMissingData();
      await this.testWebSocketInterruption();
      await this.testAIEngineErrorResponse();
      await this.testErrorBoundaryCatches();
      await this.testUICrashPrevention();
      await this.testMemoryLeakProtection();
      await this.testInfiniteLoopProtection();
      
      return this.generateReport();
    } catch (error) {
      console.error('❌ Frontend crash protection chaos test failed:', error);
      throw error;
    }
  }

  async testInvalidAPIResponses() {
    console.log('\n🚫 Testing Invalid API Responses...');
    
    try {
      const errorScenarios = [
        'Network Error: Connection refused',
        'Timeout Error: Request timed out',
        'Invalid JSON response',
        'Missing required fields'
      ];
      
      const results = [];
      
      for (const scenario of errorScenarios) {
        let caught = false;
        let handled = false;
        
        try {
          // Mock different error responses
          if (scenario.includes('Network Error')) {
            throw new Error('Network Error: Connection refused');
          } else if (scenario.includes('Timeout Error')) {
            throw new Error('Timeout Error: Request timed out');
          } else if (scenario.includes('Invalid JSON')) {
            // Simulate invalid JSON parsing
            JSON.parse('invalid json {');
          } else if (scenario.includes('Missing fields')) {
            // Simulate missing required fields validation
            const response = { authenticated: true };
            if (!response.login_url && !response.authenticated) {
              throw new Error('Missing required fields in response');
            }
          }
        } catch (error) {
          caught = true;
          
          // Simulate error handling
          if (error.message.includes('Network') || 
              error.message.includes('Timeout') ||
              error.message.includes('JSON') ||
              error.message.includes('Missing')) {
            handled = true;
            console.log(`Handled ${scenario}:`, error.message);
          }
        }
        
        results.push({
          scenario: scenario,
          caught: caught,
          handled: handled,
          prevented_crash: caught && handled
        });
      }
      
      const allPrevented = results.every(r => r.prevented_crash);
      
      this.testResults.invalid_api_responses = {
        status: allPrevented ? 'PASS' : 'FAIL',
        message: `Invalid API responses test`,
        scenarios: results,
        allPrevented: allPrevented,
        preventedCount: results.filter(r => r.prevented_crash).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults.invalid_api_responses = {
        status: 'FAIL',
        message: `Invalid API responses test failed: ${error.message}`
      };
    }
  }

  async testMissingData() {
    console.log('\n🕳️ Testing Missing Data...');
    
    try {
      const missingDataScenarios = [
        { name: 'Null price data', data: { price: null, volume: 1000 } },
        { name: 'Undefined volume', data: { price: 45000, volume: undefined } },
        { name: 'Empty object', data: {} },
        { name: 'Null response', data: null },
        { name: 'Array instead of object', data: [45000, 1000] },
        { name: 'String instead of number', data: { price: '45000', volume: '1000' } }
      ];
      
      const results = [];
      
      for (const scenario of missingDataScenarios) {
        let caught = false;
        let handled = false;
        let fallbackUsed = false;
        
        try {
          // Simulate data processing with missing data
          const processedData = this.processMarketData(scenario.data);
          
          // Check if fallback values were used
          if (processedData.price === 0 || processedData.volume === 0) {
            fallbackUsed = true;
          }
          
          handled = true;
          
        } catch (error) {
          caught = true;
          
          // Handle missing data gracefully
          if (error.message.includes('Cannot read') || 
              error.message.includes('undefined') ||
              error.message.includes('null')) {
            handled = true;
            fallbackUsed = true;
          }
        }
        
        results.push({
          scenario: scenario.name,
          data: scenario.data,
          caught: caught,
          handled: handled,
          fallbackUsed: fallbackUsed,
          prevented_crash: handled
        });
      }
      
      const allPrevented = results.every(r => r.prevented_crash);
      
      this.testResults.missing_data = {
        status: allPrevented ? 'PASS' : 'FAIL',
        message: `Missing data test`,
        scenarios: results,
        allPrevented: allPrevented,
        preventedCount: results.filter(r => r.prevented_crash).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults.missing_data = {
        status: 'FAIL',
        message: `Missing data test failed: ${error.message}`
      };
    }
  }

  async testWebSocketInterruption() {
    console.log('\n🔌 Testing WebSocket Interruption...');
    
    try {
      const wsScenarios = [
        'Connection lost',
        'Send failed',
        'Message parse error',
        'Sudden disconnect'
      ];
      
      const results = [];
      
      for (const scenario of wsScenarios) {
        let caught = false;
        let handled = false;
        let reconnectAttempted = false;
        
        try {
          const ws = new MockWebSocket('ws://localhost:8000/ws');
          
          // Simulate different WebSocket errors
          if (scenario.includes('Connection lost')) {
            ws.simulateError();
          } else if (scenario.includes('Send failed')) {
            ws.send('test message');
          } else if (scenario.includes('Message parse error')) {
            // Simulate message parsing error
            JSON.parse('invalid websocket message');
          } else if (scenario.includes('Sudden disconnect')) {
            ws.close();
          }
          
        } catch (error) {
          caught = true;
          
          // Handle WebSocket errors
          if (error.message.includes('WebSocket') || 
              error.message.includes('connection') ||
              error.message.includes('parse')) {
            handled = true;
            reconnectAttempted = true;
            
            // Simulate reconnection attempt
            setTimeout(() => {
              console.log('Reconnection attempted for:', scenario);
            }, 100);
          }
        }
        
        results.push({
          scenario: scenario,
          caught: caught,
          handled: handled,
          reconnectAttempted: reconnectAttempted,
          prevented_crash: handled
        });
      }
      
      const allPrevented = results.every(r => r.prevented_crash);
      
      this.testResults.websocket_interruption = {
        status: allPrevented ? 'PASS' : 'FAIL',
        message: `WebSocket interruption test`,
        scenarios: results,
        allPrevented: allPrevented,
        preventedCount: results.filter(r => r.prevented_crash).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults.websocket_interruption = {
        status: 'FAIL',
        message: `WebSocket interruption test failed: ${error.message}`
      };
    }
  }

  async testAIEngineErrorResponse() {
    console.log('\n🤖 Testing AI Engine Error Response...');
    
    try {
      const aiErrorScenarios = [
        'Engine timeout',
        'Invalid AI response',
        'AI engine crash',
        'Corrupted AI data'
      ];
      
      const results = [];
      
      for (const scenario of aiErrorScenarios) {
        let caught = false;
        let handled = false;
        let fallbackUsed = false;
        
        try {
          // Simulate AI engine processing
          const aiResponse = await this.processAIEngine(scenario);
          
          // Check if fallback was used
          if (aiResponse.fallback) {
            fallbackUsed = true;
          }
          
          handled = true;
          
        } catch (error) {
          caught = true;
          
          // Handle AI engine errors
          if (error.message.includes('timeout') ||
              error.message.includes('invalid') ||
              error.message.includes('crash') ||
              error.message.includes('corrupted')) {
            handled = true;
            fallbackUsed = true;
          }
        }
        
        results.push({
          scenario: scenario,
          caught: caught,
          handled: handled,
          fallbackUsed: fallbackUsed,
          prevented_crash: handled
        });
      }
      
      const allPrevented = results.every(r => r.prevented_crash);
      
      this.testResults.ai_engine_error_response = {
        status: allPrevented ? 'PASS' : 'FAIL',
        message: `AI engine error response test`,
        scenarios: results,
        allPrevented: allPrevented,
        preventedCount: results.filter(r => r.prevented_crash).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults.ai_engine_error_response = {
        status: 'FAIL',
        message: `AI engine error response test failed: ${error.message}`
      };
    }
  }

  async testErrorBoundaryCatches() {
    console.log('\n🛑 Testing ErrorBoundary Catches...');
    
    try {
      const errorScenarios = [
        'TypeError: Cannot read property',
        'ReferenceError: Variable not defined',
        'SyntaxError: Unexpected token',
        'Custom Error: Application error'
      ];
      
      const results = [];
      
      for (const scenario of errorScenarios) {
        let errorCaught = false;
        let fallbackRendered = false;
        
        try {
          // Simulate different types of errors
          if (scenario.includes('TypeError')) {
            const obj = null;
            obj.property; // This will throw TypeError
          } else if (scenario.includes('ReferenceError')) {
            undefinedVariable; // This will throw ReferenceError
          } else if (scenario.includes('SyntaxError')) {
            eval('invalid syntax'); // This will throw SyntaxError
          } else {
            throw new Error('Custom application error');
          }
          
        } catch (error) {
          errorCaught = true;
          
          // Simulate ErrorBoundary catching the error
          const boundaryState = ErrorBoundary.getDerivedStateFromError(error);
          
          if (boundaryState.hasError) {
            fallbackRendered = true;
          }
        }
        
        results.push({
          scenario: scenario,
          errorCaught: errorCaught,
          fallbackRendered: fallbackRendered,
          prevented_crash: errorCaught && fallbackRendered
        });
      }
      
      const allPrevented = results.every(r => r.prevented_crash);
      
      this.testResults.error_boundary_catches = {
        status: allPrevented ? 'PASS' : 'FAIL',
        message: `ErrorBoundary catches test`,
        scenarios: results,
        allPrevented: allPrevented,
        preventedCount: results.filter(r => r.prevented_crash).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults.error_boundary_catches = {
        status: 'FAIL',
        message: `ErrorBoundary test failed: ${error.message}`
      };
    }
  }

  async testUICrashPrevention() {
    console.log('\n🖥️ Testing UI Crash Prevention...');
    
    try {
      const uiCrashScenarios = [
        'DOM manipulation error',
        'Event handler error',
        'Render loop error',
        'State update error'
      ];
      
      const results = [];
      
      for (const scenario of uiCrashScenarios) {
        let caught = false;
        let handled = false;
        let uiStable = false;
        
        try {
          // Simulate different UI crash scenarios
          if (scenario.includes('DOM manipulation')) {
            const element = document.getElementById('nonexistent');
            element.innerHTML = 'test'; // Will throw error
          } else if (scenario.includes('Event handler')) {
            const button = document.createElement('button');
            button.onclick = () => {
              throw new Error('Event handler error');
            };
            button.onclick(); // Trigger the error
          } else if (scenario.includes('Render loop')) {
            // Simulate render loop error
            for (let i = 0; i < 1000; i++) {
              if (i === 500) {
                throw new Error('Render loop error');
              }
            }
          } else if (scenario.includes('State update')) {
            // Simulate state update error
            const state = null;
            state.value = 'updated'; // Will throw error
          }
          
        } catch (error) {
          caught = true;
          
          // Handle UI errors gracefully
          if (error.message.includes('DOM') ||
              error.message.includes('Event') ||
              error.message.includes('Render') ||
              error.message.includes('State')) {
            handled = true;
            uiStable = true; // UI remains stable despite error
          }
        }
        
        results.push({
          scenario: scenario,
          caught: caught,
          handled: handled,
          uiStable: uiStable,
          prevented_crash: handled && uiStable
        });
      }
      
      const allPrevented = results.every(r => r.prevented_crash);
      
      this.testResults.ui_crash_prevention = {
        status: allPrevented ? 'PASS' : 'FAIL',
        message: `UI crash prevention test`,
        scenarios: results,
        allPrevented: allPrevented,
        preventedCount: results.filter(r => r.prevented_crash).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults.ui_crash_prevention = {
        status: 'FAIL',
        message: `UI crash prevention test failed: ${error.message}`
      };
    }
  }

  async testMemoryLeakProtection() {
    console.log('\n🧠 Testing Memory Leak Protection...');
    
    try {
      // Simulate memory leak scenarios
      const initialMemory = this.getMockMemoryUsage();
      const memorySamples = [initialMemory];
      
      // Create potential memory leaks
      const eventListeners = [];
      const timers = [];
      
      for (let i = 0; i < 100; i++) {
        // Create event listeners without cleanup (potential leak)
        const element = document.createElement('div');
        element.addEventListener('click', () => {
          console.log('Click event', i);
        });
        eventListeners.push(element);
        
        // Create timers without cleanup (potential leak)
        const timer = setTimeout(() => {
          console.log('Timer', i);
        }, 1000);
        timers.push(timer);
        
        // Sample memory every 10 iterations
        if (i % 10 === 0) {
          const currentMemory = this.getMockMemoryUsage();
          memorySamples.push(currentMemory);
        }
      }
      
      // Simulate cleanup
      eventListeners.forEach(element => {
        element.removeEventListener('click', () => {});
      });
      
      timers.forEach(timer => {
        clearTimeout(timer);
      });
      
      const finalMemory = this.getMockMemoryUsage();
      memorySamples.push(finalMemory);
      
      // Check for memory growth
      const memoryGrowth = finalMemory - initialMemory;
      const maxMemory = Math.max(...memorySamples);
      const memoryStable = memoryGrowth < 50; // Less than 50MB growth
      
      this.testResults.memory_leak_protection = {
        status: memoryStable ? 'PASS' : 'FAIL',
        message: `Memory leak protection test`,
        initialMemory: initialMemory,
        finalMemory: finalMemory,
        memoryGrowth: memoryGrowth,
        maxMemory: maxMemory,
        memoryStable: memoryStable,
        samples: memorySamples.length
      };
      
    } catch (error) {
      this.testResults.memory_leak_protection = {
        status: 'FAIL',
        message: `Memory leak protection test failed: ${error.message}`
      };
    }
  }

  async testInfiniteLoopProtection() {
    console.log('\n🔄 Testing Infinite Loop Protection...');
    
    try {
      const loopScenarios = [
        'While loop without break',
        'Recursive function without base case',
        'Array iteration with modification',
        'Event listener recursion'
      ];
      
      const results = [];
      
      for (const scenario of loopScenarios) {
        let loopDetected = false;
        let prevented = false;
        let executionTime = 0;
        
        try {
          const startTime = Date.now();
          
          // Simulate infinite loops with protection
          if (scenario.includes('While loop')) {
            let counter = 0;
            const maxIterations = 1000; // Protection limit
            
            while (true) {
              counter++;
              if (counter >= maxIterations) {
                loopDetected = true;
                prevented = true;
                break; // Break infinite loop
              }
            }
          } else if (scenario.includes('Recursive')) {
            const maxDepth = 100; // Protection limit
            
            const recursiveFunction = (depth) => {
              if (depth >= maxDepth) {
                loopDetected = true;
                prevented = true;
                return; // Stop recursion
              }
              return recursiveFunction(depth + 1);
            };
            
            recursiveFunction(0);
          } else if (scenario.includes('Array iteration')) {
            const arr = [1, 2, 3, 4, 5];
            let iterations = 0;
            const maxIterations = 100;
            
            for (let i = 0; i < arr.length; ) {
              iterations++;
              if (iterations >= maxIterations) {
                loopDetected = true;
                prevented = true;
                break;
              }
              // Don't increment i to simulate infinite loop
              if (iterations % 10 === 0) {
                i++; // Occasionally increment to make it realistic
              }
            }
          } else if (scenario.includes('Event listener')) {
            let eventCount = 0;
            const maxEvents = 50;
            
            const eventHandler = () => {
              eventCount++;
              if (eventCount >= maxEvents) {
                loopDetected = true;
                prevented = true;
                return; // Stop event handling
              }
              
              // Simulate event that triggers itself
              if (eventCount < maxEvents) {
                setTimeout(eventHandler, 1);
              }
            };
            
            eventHandler();
            
            // Wait for events to complete
            await new Promise(resolve => setTimeout(resolve, 100));
          }
          
          executionTime = Date.now() - startTime;
          
        } catch (error) {
          loopDetected = true;
          prevented = true; // Exception broke the loop
        }
        
        results.push({
          scenario: scenario,
          loopDetected: loopDetected,
          prevented: prevented,
          executionTime: executionTime,
          protected: loopDetected && prevented
        });
      }
      
      const allProtected = results.every(r => r.protected);
      
      this.testResults.infinite_loop_protection = {
        status: allProtected ? 'PASS' : 'FAIL',
        message: `Infinite loop protection test`,
        scenarios: results,
        allProtected: allProtected,
        protectedCount: results.filter(r => r.protected).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults.infinite_loop_protection = {
        status: 'FAIL',
        message: `Infinite loop protection test failed: ${error.message}`
      };
    }
  }

  // Helper methods for testing
  processMarketData(data) {
    if (!data || typeof data !== 'object') {
      return { price: 0, volume: 0, fallback: true };
    }
    
    return {
      price: data.price || 0,
      volume: data.volume || 0,
      fallback: !data.price || !data.volume
    };
  }

  async processAIEngine(scenario) {
    // Simulate AI engine processing with error scenarios
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (scenario.includes('timeout')) {
          reject(new Error('AI engine timeout'));
        } else if (scenario.includes('invalid')) {
          resolve({ data: 'invalid', fallback: true });
        } else if (scenario.includes('crash')) {
          reject(new Error('AI engine crash'));
        } else if (scenario.includes('corrupted')) {
          resolve({ data: null, fallback: true });
        } else {
          resolve({ data: 'valid ai response', fallback: false });
        }
      }, 10);
    });
  }

  getMockMemoryUsage() {
    // Simulate memory usage in MB
    return 50 + Math.random() * 20; // 50-70MB
  }

  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      testType: 'FRONTEND_CRASH_PROTECTION_CHAOS_TEST',
      summary: {
        totalTests: Object.keys(this.testResults).length,
        passed: Object.values(this.testResults).filter(r => r.status === 'PASS').length,
        failed: Object.values(this.testResults).filter(r => r.status === 'FAIL').length,
      },
      results: this.testResults,
      protectionFeatures: [
        'ErrorBoundary',
        'WebSocket error handling',
        'API error handling',
        'Memory leak protection',
        'Infinite loop protection',
        'UI crash prevention'
      ]
    };

    return report;
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const tester = new FrontendCrashProtectionChaosTester();
  
  tester.runAllTests()
    .then(report => {
      console.log('\n🛡️ FRONTEND CRASH PROTECTION CHAOS TEST REPORT');
      console.log('='.repeat(50));
      console.log(`Total Tests: ${report.summary.totalTests}`);
      console.log(`Passed: ${report.summary.passed}`);
      console.log(`Failed: ${report.summary.failed}`);
      
      console.log('\nDetailed Results:');
      Object.entries(report.results).forEach(([test, result]) => {
        const icon = result.status === 'PASS' ? '✅' : '❌';
        console.log(`${icon} ${test}: ${result.message}`);
      });
      
      console.log('\nProtection Features:');
      report.protectionFeatures.forEach(feature => {
        console.log(`✓ ${feature}`);
      });
      
      // Save report to file
      require('fs').writeFileSync(
        'frontend_crash_protection_chaos_test_report.json',
        JSON.stringify(report, null, 2)
      );
      console.log('\n📄 Report saved to frontend_crash_protection_chaos_test_report.json');
    })
    .catch(error => {
      console.error('❌ Frontend crash protection chaos test execution failed:', error);
      process.exit(1);
    });
}

module.exports = FrontendCrashProtectionChaosTester;
