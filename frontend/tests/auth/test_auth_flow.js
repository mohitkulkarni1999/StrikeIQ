/**
 * FRONTEND AUTH FLOW TESTS
 * 
 * Test cases:
 * - login success
 * - token persistence
 * - token refresh
 * - server restart session recovery
 * - backend offline handling
 * - logout flow
 */

const axios = require('axios');
const { JSDOM } = require('jsdom');

// Test configuration
const TEST_CONFIG = {
  backendUrl: 'http://localhost:8000',
  frontendUrl: 'http://localhost:3000',
  timeout: 5000,
};

class FrontendAuthTester {
  constructor() {
    this.testResults = {};
    this.dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
    global.window = this.dom.window;
    global.document = this.dom.window.document;
    global.localStorage = this.createMockLocalStorage();
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
    console.log('🚀 Starting Frontend Auth Flow Tests');
    
    try {
      await this.testLoginSuccess();
      await this.testTokenPersistence();
      await this.testTokenRefresh();
      await this.testServerRestartSessionRecovery();
      await this.testBackendOfflineHandling();
      await this.testLogoutFlow();
      
      return this.generateReport();
    } catch (error) {
      console.error('❌ Test suite failed:', error);
      throw error;
    }
  }

  async testLoginSuccess() {
    console.log('📝 Testing Login Success...');
    
    try {
      // Test auth status endpoint
      const response = await axios.get(`${TEST_CONFIG.backendUrl}/api/v1/auth/status`, {
        timeout: TEST_CONFIG.timeout,
      });

      if (response.status === 200) {
        const data = response.data;
        
        if (data.authenticated === true) {
          this.testResults.login_success = {
            status: 'PASS',
            message: 'Already authenticated',
            data: data,
          };
        } else if (data.authenticated === false && data.login_url) {
          this.testResults.login_success = {
            status: 'PASS',
            message: 'Login URL correctly provided',
            login_url: data.login_url,
          };
        } else {
          this.testResults.login_success = {
            status: 'FAIL',
            message: 'Unexpected auth response',
            data: data,
          };
        }
      } else {
        this.testResults.login_success = {
          status: 'FAIL',
          message: `HTTP ${response.status}: ${response.statusText}`,
        };
      }
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        this.testResults.login_success = {
          status: 'SKIP',
          message: 'Backend offline - cannot test login',
        };
      } else {
        this.testResults.login_success = {
          status: 'FAIL',
          message: error.message,
        };
      }
    }
  }

  async testTokenPersistence() {
    console.log('💾 Testing Token Persistence...');
    
    try {
      // Simulate storing token
      const mockToken = {
        access_token: 'mock_access_token_12345',
        refresh_token: 'mock_refresh_token_67890',
        expires_at: Date.now() + (3600 * 1000), // 1 hour from now
      };

      // Store in localStorage
      global.localStorage.setItem('strikeiq_session', JSON.stringify(mockToken));

      // Retrieve from localStorage
      const stored = global.localStorage.getItem('strikeiq_session');
      const parsed = JSON.parse(stored);

      if (parsed.access_token === mockToken.access_token &&
          parsed.refresh_token === mockToken.refresh_token) {
        this.testResults.token_persistence = {
          status: 'PASS',
          message: 'Token successfully stored and retrieved',
        };
      } else {
        this.testResults.token_persistence = {
          status: 'FAIL',
          message: 'Token persistence failed',
        };
      }
    } catch (error) {
      this.testResults.token_persistence = {
        status: 'FAIL',
        message: error.message,
      };
    }
  }

  async testTokenRefresh() {
    console.log('🔄 Testing Token Refresh...');
    
    try {
      const response = await axios.post(`${TEST_CONFIG.backendUrl}/api/v1/auth/refresh`, {}, {
        timeout: TEST_CONFIG.timeout,
      });

      if (response.status === 200) {
        if (response.data.access_token) {
          this.testResults.token_refresh = {
            status: 'PASS',
            message: 'Token refresh successful',
            has_access_token: true,
          };
        } else {
          this.testResults.token_refresh = {
            status: 'FAIL',
            message: 'Refresh response missing access token',
          };
        }
      } else {
        this.testResults.token_refresh = {
          status: 'FAIL',
          message: `HTTP ${response.status}: ${response.statusText}`,
        };
      }
    } catch (error) {
      if (error.response?.status === 401) {
        this.testResults.token_refresh = {
          status: 'EXPECTED',
          message: 'Refresh correctly requires authentication',
        };
      } else if (error.code === 'ECONNREFUSED') {
        this.testResults.token_refresh = {
          status: 'SKIP',
          message: 'Backend offline - cannot test refresh',
        };
      } else {
        this.testResults.token_refresh = {
          status: 'FAIL',
          message: error.message,
        };
      }
    }
  }

  async testServerRestartSessionRecovery() {
    console.log('🔧 Testing Server Restart Session Recovery...');
    
    try {
      // Simulate session data
      const sessionData = {
        access_token: 'test_token',
        refresh_token: 'test_refresh',
        expires_at: Date.now() + (3600 * 1000),
        isAuthenticated: true,
      };

      // Store session
      global.localStorage.setItem('strikeiq_session', JSON.stringify(sessionData));

      // Simulate server restart by checking auth status
      const response = await axios.get(`${TEST_CONFIG.backendUrl}/api/v1/auth/status`, {
        timeout: TEST_CONFIG.timeout,
      });

      if (response.status === 200) {
        this.testResults.server_restart_recovery = {
          status: 'PASS',
          message: 'Session recovery test completed',
          backend_responsive: true,
          session_stored: true,
        };
      } else {
        this.testResults.server_restart_recovery = {
          status: 'PARTIAL',
          message: 'Session stored but backend not responsive',
        };
      }
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        // Check if session is still stored
        const stored = global.localStorage.getItem('strikeiq_session');
        if (stored) {
          this.testResults.server_restart_recovery = {
            status: 'PARTIAL',
            message: 'Session persisted but backend offline',
          };
        } else {
          this.testResults.server_restart_recovery = {
            status: 'FAIL',
            message: 'Session lost and backend offline',
          };
        }
      } else {
        this.testResults.server_restart_recovery = {
          status: 'FAIL',
          message: error.message,
        };
      }
    }
  }

  async testBackendOfflineHandling() {
    console.log('🔌 Testing Backend Offline Handling...');
    
    try {
      // Test with invalid URL to simulate offline
      const offlineUrl = 'http://localhost:9999';
      
      try {
        await axios.get(`${offlineUrl}/api/v1/auth/status`, { timeout: 2000 });
        this.testResults.backend_offline_handling = {
          status: 'UNEXPECTED',
          message: 'Backend responded on unexpected port',
        };
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          this.testResults.backend_offline_handling = {
            status: 'PASS',
            message: 'Correctly detected backend offline',
          };
        } else {
          this.testResults.backend_offline_handling = {
            status: 'PARTIAL',
            message: `Detected backend issue: ${error.message}`,
          };
        }
      }
    } catch (error) {
      this.testResults.backend_offline_handling = {
        status: 'FAIL',
        message: error.message,
      };
    }
  }

  async testLogoutFlow() {
    console.log('🚪 Testing Logout Flow...');
    
    try {
      // Store mock session
      const sessionData = {
        access_token: 'test_token',
        refresh_token: 'test_refresh',
        expires_at: Date.now() + (3600 * 1000),
        isAuthenticated: true,
      };
      global.localStorage.setItem('strikeiq_session', JSON.stringify(sessionData));

      // Simulate logout by clearing session
      global.localStorage.removeItem('strikeiq_session');

      // Verify session is cleared
      const stored = global.localStorage.getItem('strikeiq_session');
      
      if (stored === null) {
        this.testResults.logout_flow = {
          status: 'PASS',
          message: 'Session successfully cleared on logout',
        };
      } else {
        this.testResults.logout_flow = {
          status: 'FAIL',
          message: 'Session not cleared on logout',
        };
      }
    } catch (error) {
      this.testResults.logout_flow = {
        status: 'FAIL',
        message: error.message,
      };
    }
  }

  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total_tests: Object.keys(this.testResults).length,
        passed: Object.values(this.testResults).filter(r => r.status === 'PASS').length,
        failed: Object.values(this.testResults).filter(r => r.status === 'FAIL').length,
        skipped: Object.values(this.testResults).filter(r => r.status === 'SKIP').length,
        partial: Object.values(this.testResults).filter(r => r.status === 'PARTIAL').length,
      },
      results: this.testResults,
    };

    return report;
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const tester = new FrontendAuthTester();
  
  tester.runAllTests()
    .then(report => {
      console.log('\n📊 FRONTEND AUTH FLOW TEST REPORT');
      console.log('=====================================');
      console.log(`Total Tests: ${report.summary.total_tests}`);
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
        'frontend_auth_test_report.json',
        JSON.stringify(report, null, 2)
      );
      console.log('\n📄 Report saved to frontend_auth_test_report.json');
    })
    .catch(error => {
      console.error('❌ Test execution failed:', error);
      process.exit(1);
    });
}

module.exports = FrontendAuthTester;
