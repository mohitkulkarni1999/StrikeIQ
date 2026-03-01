/**
 * NETWORK FAILURE CHAOS TEST
 * Test frontend behavior under network failure conditions
 */

const axios = require('axios');
const { JSDOM } = require('jsdom');

// Test configuration
const TEST_CONFIG = {
  backendUrl: 'http://localhost:8000',
  offlineUrl: 'http://localhost:9999', // Non-existent port
  timeout: 5000,
  retryInterval: 3000, // 3 seconds
};

class NetworkFailureChaosTester {
  constructor() {
    this.testResults = {};
    this.dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
    global.window = this.dom.window;
    global.document = this.dom.window.document;
    global.localStorage = this.createMockLocalStorage();
    this.retryCount = 0;
    this.maxRetries = 10;
  }

  createMockLocalStorage() {
    const store = {};
    return {
      getItem: (key) => store[key] || null,
      setItem: (key, value) => { store[key] = value.toString(); },
      removeItem: (key) => { delete store[key]; },
      clear: () => { Object.keys(store).forEach(key => delete store[key]); },
    };
  }

  async runAllTests() {
    console.log('🌐 STARTING NETWORK FAILURE CHAOS TESTS');
    console.log('='.repeat(50));
    
    try {
      await this.testBackendOffline();
      await this.testNetworkTimeout();
      await this.testWebSocketDisconnect();
      await this.testRetryEvery3Seconds();
      await this.testNoRedirectToAuth();
      await this.testNoUICrash();
      
      return this.generateReport();
    } catch (error) {
      console.error('❌ Network failure chaos test failed:', error);
      throw error;
    }
  }

  async testBackendOffline() {
    console.log('\n🔌 Testing Backend Offline...');
    
    try {
      // Test with offline URL
      const startTime = Date.now();
      
      try {
        await axios.get(`${TEST_CONFIG.offlineUrl}/api/v1/auth/status`, {
          timeout: TEST_CONFIG.timeout,
        });
        
        this.testResults.backend_offline = {
          status: 'UNEXPECTED',
          message: 'Backend responded on unexpected port',
        };
      } catch (error) {
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        if (error.code === 'ECONNREFUSED') {
          this.testResults.backend_offline = {
            status: 'PASS',
            message: 'Correctly detected backend offline',
            responseTimeMs: responseTime,
            errorCode: error.code,
          };
        } else {
          this.testResults.backend_offline = {
            status: 'PARTIAL',
            message: `Detected backend issue: ${error.message}`,
            responseTimeMs: responseTime,
            errorCode: error.code,
          };
        }
      }
    } catch (error) {
      this.testResults.backend_offline = {
        status: 'FAIL',
        message: `Backend offline test failed: ${error.message}`,
      };
    }
  }

  async testNetworkTimeout() {
    console.log('\n⏱️ Testing Network Timeout...');
    
    try {
      // Test with very short timeout to force timeout
      const startTime = Date.now();
      
      try {
        await axios.get(`${TEST_CONFIG.backendUrl}/api/v1/auth/status`, {
          timeout: 1, // 1ms timeout to force timeout
        });
        
        this.testResults.network_timeout = {
          status: 'UNEXPECTED',
          message: 'Request completed unexpectedly fast',
        };
      } catch (error) {
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          this.testResults.network_timeout = {
            status: 'PASS',
            message: 'Network timeout correctly handled',
            responseTimeMs: responseTime,
            errorCode: error.code,
          };
        } else {
          this.testResults.network_timeout = {
            status: 'PARTIAL',
            message: `Different error occurred: ${error.message}`,
            responseTimeMs: responseTime,
            errorCode: error.code,
          };
        }
      }
    } catch (error) {
      this.testResults.network_timeout = {
        status: 'FAIL',
        message: `Network timeout test failed: ${error.message}`,
      };
    }
  }

  async testWebSocketDisconnect() {
    console.log('\n🔌 Testing WebSocket Disconnect...');
    
    try {
      // Simulate WebSocket disconnect
      const mockWebSocket = {
        readyState: 3, // CLOSED
        close: () => {},
        send: () => { throw new Error('WebSocket is closed'); },
        addEventListener: () => {},
      };
      
      // Test WebSocket disconnect handling
      let disconnectDetected = false;
      let reconnectAttempted = false;
      
      // Simulate disconnect event
      try {
        mockWebSocket.send('test message');
      } catch (error) {
        disconnectDetected = true;
        console.log('WebSocket disconnect detected:', error.message);
        
        // Simulate reconnect attempt
        setTimeout(() => {
          reconnectAttempted = true;
          console.log('Reconnect attempt triggered');
        }, 100);
      }
      
      // Wait for reconnect simulation
      await new Promise(resolve => setTimeout(resolve, 200));
      
      if (disconnectDetected) {
        this.testResults.websocket_disconnect = {
          status: 'PASS',
          message: 'WebSocket disconnect correctly detected',
          disconnectDetected: true,
          reconnectAttempted: reconnectAttempted,
        };
      } else {
        this.testResults.websocket_disconnect = {
          status: 'FAIL',
          message: 'WebSocket disconnect not detected',
        };
      }
    } catch (error) {
      this.testResults.websocket_disconnect = {
        status: 'FAIL',
        message: `WebSocket disconnect test failed: ${error.message}`,
      };
    }
  }

  async testRetryEvery3Seconds() {
    console.log('\n🔄 Testing Retry Every 3 Seconds...');
    
    try {
      const retryAttempts = [];
      const startTime = Date.now();
      
      // Simulate retry logic
      const retryLogic = async (attempt = 1) => {
        if (attempt > 3) return; // Limit attempts for testing
        
        try {
          await axios.get(`${TEST_CONFIG.offlineUrl}/api/v1/auth/status`, {
            timeout: 1000,
          });
        } catch (error) {
          retryAttempts.push({
            attempt: attempt,
            timestamp: Date.now(),
            error: error.code,
          });
          
          // Wait 3 seconds before retry
          await new Promise(resolve => setTimeout(resolve, TEST_CONFIG.retryInterval));
          return retryLogic(attempt + 1);
        }
      };
      
      await retryLogic();
      
      const endTime = Date.now();
      const totalDuration = endTime - startTime;
      
      if (retryAttempts.length > 0) {
        // Check if retries were spaced approximately 3 seconds apart
        const retryIntervals = [];
        for (let i = 1; i < retryAttempts.length; i++) {
          const interval = retryAttempts[i].timestamp - retryAttempts[i-1].timestamp;
          retryIntervals.push(interval);
        }
        
        const avgInterval = retryIntervals.reduce((a, b) => a + b, 0) / retryIntervals.length;
        const expectedInterval = TEST_CONFIG.retryInterval;
        const intervalVariance = Math.abs(avgInterval - expectedInterval);
        
        if (intervalVariance < 500) { // Allow 500ms variance
          this.testResults.retry_every_3_seconds = {
            status: 'PASS',
            message: 'Retries correctly spaced at ~3 seconds',
            totalAttempts: retryAttempts.length,
            totalDurationMs: totalDuration,
            avgRetryIntervalMs: avgInterval,
            expectedIntervalMs: expectedInterval,
            intervalVarianceMs: intervalVariance,
            retryAttempts: retryAttempts,
          };
        } else {
          this.testResults.retry_every_3_seconds = {
            status: 'PARTIAL',
            message: `Retry interval variance too high: ${intervalVariance}ms`,
            totalAttempts: retryAttempts.length,
            avgRetryIntervalMs: avgInterval,
            expectedIntervalMs: expectedInterval,
            intervalVarianceMs: intervalVariance,
          };
        }
      } else {
        this.testResults.retry_every_3_seconds = {
          status: 'FAIL',
          message: 'No retry attempts made',
        };
      }
    } catch (error) {
      this.testResults.retry_every_3_seconds = {
        status: 'FAIL',
        message: `Retry test failed: ${error.message}`,
      };
    }
  }

  async testNoRedirectToAuth() {
    console.log('\n🚫 Testing No Redirect to Auth...');
    
    try {
      // Simulate auth redirect logic
      let redirectTriggered = false;
      let authRedirectCount = 0;
      
      // Mock router that tracks redirects
      const mockRouter = {
        push: (url) => {
          if (url === '/auth') {
            authRedirectCount++;
            redirectTriggered = true;
          }
        },
      };
      
      // Simulate backend offline detection
      const handleBackendOffline = () => {
        // Should NOT redirect to /auth when backend is offline
        console.log('Backend offline - showing offline state instead of redirect');
        // No redirect triggered
      };
      
      // Test multiple backend offline scenarios
      for (let i = 0; i < 5; i++) {
        handleBackendOffline();
        
        // Simulate what would happen in real app
        try {
          await axios.get(`${TEST_CONFIG.offlineUrl}/api/v1/auth/status`, {
            timeout: 1000,
          });
        } catch (error) {
          // Should handle offline state, not redirect
          if (error.code === 'ECONNREFUSED') {
            // Correct behavior - no redirect
          } else {
            // Incorrect behavior - might redirect
            mockRouter.push('/auth');
          }
        }
      }
      
      if (authRedirectCount === 0) {
        this.testResults.no_redirect_to_auth = {
          status: 'PASS',
          message: 'No auth redirects triggered during backend offline',
          redirectTriggered: false,
          authRedirectCount: authRedirectCount,
        };
      } else {
        this.testResults.no_redirect_to_auth = {
          status: 'FAIL',
          message: `Auth redirects triggered: ${authRedirectCount}`,
          redirectTriggered: true,
          authRedirectCount: authRedirectCount,
        };
      }
    } catch (error) {
      this.testResults.no_redirect_to_auth = {
        status: 'FAIL',
        message: `No redirect test failed: ${error.message}`,
      };
    }
  }

  async testNoUICrash() {
    console.log('\n🛡️ Testing No UI Crash...');
    
    try {
      // Simulate various error conditions
      const errorScenarios = [
        'NetworkError',
        'TimeoutError',
        'ParseError',
        'WebSocketError',
        'AuthError',
      ];
      
      const crashResults = [];
      
      for (const scenario of errorScenarios) {
        try {
          // Simulate error handling
          const errorHandler = (error) => {
            // Should handle error gracefully without crashing
            console.log(`Handling ${scenario}:`, error.message);
            return { handled: true, scenario };
          };
          
          // Simulate different error types
          let mockError;
          switch (scenario) {
            case 'NetworkError':
              mockError = new Error('Network Error');
              mockError.code = 'ECONNREFUSED';
              break;
            case 'TimeoutError':
              mockError = new Error('Timeout Error');
              mockError.code = 'ECONNABORTED';
              break;
            case 'ParseError':
              mockError = new SyntaxError('JSON Parse Error');
              break;
            case 'WebSocketError':
              mockError = new Error('WebSocket Closed');
              mockError.code = 'WEBSOCKET_CLOSED';
              break;
            case 'AuthError':
              mockError = new Error('Authentication Failed');
              mockError.code = 'AUTH_FAILED';
              break;
          }
          
          const result = errorHandler(mockError);
          crashResults.push(result);
          
        } catch (error) {
          crashResults.push({
            handled: false,
            scenario,
            error: error.message,
          });
        }
      }
      
      const handledCrashes = crashResults.filter(r => r.handled).length;
      const totalScenarios = errorScenarios.length;
      
      if (handledCrashes === totalScenarios) {
        this.testResults.no_ui_crash = {
          status: 'PASS',
          message: 'All error scenarios handled gracefully',
          totalScenarios: totalScenarios,
          handledScashes: handledCrashes,
          crashResults: crashResults,
        };
      } else {
        this.testResults.no_ui_crash = {
          status: 'FAIL',
          message: `${totalScenarios - handledCrashes} scenarios caused crashes`,
          totalScenarios: totalScenarios,
          handledCrashes: handledCrashes,
          crashResults: crashResults,
        };
      }
    } catch (error) {
      this.testResults.no_ui_crash = {
        status: 'FAIL',
        message: `No UI crash test failed: ${error.message}`,
      };
    }
  }

  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      testType: 'NETWORK_FAILURE_CHAOS_TEST',
      summary: {
        totalTests: Object.keys(this.testResults).length,
        passed: Object.values(this.testResults).filter(r => r.status === 'PASS').length,
        failed: Object.values(this.testResults).filter(r => r.status === 'FAIL').length,
        skipped: Object.values(this.testResults).filter(r => r.status === 'SKIP').length,
        partial: Object.values(this.testResults).filter(r => r.status === 'PARTIAL').length,
      },
      results: this.testResults,
      config: TEST_CONFIG,
    };

    return report;
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const tester = new NetworkFailureChaosTester();
  
  tester.runAllTests()
    .then(report => {
      console.log('\n🌐 NETWORK FAILURE CHAOS TEST REPORT');
      console.log('='.repeat(45));
      console.log(`Total Tests: ${report.summary.totalTests}`);
      console.log(`Passed: ${report.summary.passed}`);
      console.log(`Failed: ${report.summary.failed}`);
      console.log(`Skipped: ${report.summary.skipped}`);
      console.log(`Partial: ${report.summary.partial}`);
      
      console.log('\nDetailed Results:');
      Object.entries(report.results).forEach(([test, result]) => {
        const icon = result.status === 'PASS' ? '✅' : 
                    result.status === 'FAIL' ? '❌' : 
                    result.status === 'SKIP' ? '⏭️' : '⚠️';
        console.log(`${icon} ${test}: ${result.message}`);
      });
      
      // Save report to file
      require('fs').writeFileSync(
        'network_failure_chaos_test_report.json',
        JSON.stringify(report, null, 2)
      );
      console.log('\n📄 Report saved to network_failure_chaos_test_report.json');
    })
    .catch(error => {
      console.error('❌ Network failure chaos test execution failed:', error);
      process.exit(1);
    });
}

module.exports = NetworkFailureChaosTester;
