# CHAOS TEST SUITE

Extreme chaos testing for the StrikeIQ trading platform to validate system stability under real-world failure conditions.

## 🎯 OBJECTIVE

Test system stability under extreme conditions focusing on:

- **Authentication** resilience and session management
- **WebSocket** stability and throughput
- **AI Engine** performance under load
- **Memory** safety and leak detection
- **Frontend** crash protection
- **Network** failure handling
- **Full system** pipeline performance

## 📁 STRUCTURE

```
backend/tests/chaos/
├── test_auth_chaos.py              # Authentication chaos tests
├── test_server_restart.py           # Server restart tests
├── test_websocket_chaos.py         # WebSocket stability tests
├── test_ai_engine_chaos.py         # AI engine stress tests
├── test_memory_safety.py           # Memory safety tests
├── test_full_system_chaos.py       # Full system pipeline tests
└── generate_chaos_report.py       # Report generator

frontend/tests/chaos/
├── test_network_failure.js         # Network failure tests
├── test_market_status.js           # Market status validation tests
└── test_ui_crash_protection.js    # UI crash protection tests

run_chaos_tests.py                  # Master test runner
CHAOS_TEST_REPORT.md               # Generated comprehensive report
```

## 🚀 QUICK START

### Run All Chaos Tests

```bash
python run_chaos_tests.py
```

### Run Individual Test Categories

#### Backend Tests
```bash
# Authentication chaos
cd backend && python tests/chaos/test_auth_chaos.py

# AI engine chaos
cd backend && python tests/chaos/test_ai_engine_chaos.py

# Memory safety
cd backend && python tests/chaos/test_memory_safety.py

# Full system tests
cd backend && python tests/chaos/test_full_system_chaos.py
```

#### Frontend Tests
```bash
# Network failure tests
cd frontend && node tests/chaos/test_network_failure.js

# Market status tests
cd frontend && node tests/chaos/test_market_status.js

# UI crash protection tests
cd frontend && node tests/chaos/test_ui_crash_protection.js
```

### Generate Report Only
```bash
cd backend && python tests/chaos/generate_chaos_report.py
```

## 📊 TEST CATEGORIES

### 1. AUTHENTICATION CHAOS TESTS
**File:** `test_auth_chaos.py`

Tests:
- Login success under stress
- Token expiry simulation
- Refresh token flow
- Backend restart with valid/expired tokens
- Concurrent refresh requests
- Session restore from localStorage

**Success Criteria:**
- Valid token → User remains logged in
- Expired token → Auto refresh
- Refresh fail → Redirect to `/auth`

### 2. SERVER RESTART TESTS
**File:** `test_server_restart.py`

Tests:
- Login and save token
- Backend stop simulation
- Backend restart simulation
- Frontend session reload
- Session restoration validation

**Success Criteria:**
- User session restored automatically
- No forced login required

### 3. WEBSOCKET CHAOS TESTS
**File:** `test_websocket_chaos.py`

Tests:
- Connection stability
- 1000 ticks per second throughput
- Message backlog handling
- Memory growth monitoring
- UI update delay simulation

**Success Criteria:**
- No memory leaks
- No dropped connections
- UI updates remain stable

### 4. AI ENGINE CHAOS TESTS
**File:** `test_ai_engine_chaos.py`

Tests:
- All AI engines under stress
- 10,000 executions
- Memory growth monitoring
- Execution latency validation

**Engines Tested:**
- LiquidityEngine
- StoplossHuntEngine
- SmartMoneyEngine
- GammaSqueezeEngine
- OptionsTrapEngine
- DealerGammaEngine
- LiquidityVacuumEngine

**Success Criteria:**
- Execution time < 1ms
- No memory growth
- No crashes

### 5. NETWORK FAILURE TESTS
**File:** `test_network_failure.js`

Tests:
- Backend offline simulation
- Network timeout handling
- WebSocket disconnect simulation
- Retry mechanism validation

**Success Criteria:**
- SERVER OFFLINE state visible
- Retry every 3 seconds
- No redirect to `/auth`
- No UI crash

### 6. MARKET STATUS VALIDATION
**File:** `test_market_status.js`

Tests:
- 09:14 IST → MARKET CLOSED
- 09:15 IST → MARKET OPEN
- 15:30 IST → MARKET CLOSED
- Weekend and holiday handling
- Timezone accuracy

**Success Criteria:**
- Correct status at critical times
- Accurate timezone handling

### 7. FRONTEND CRASH PROTECTION
**File:** `test_ui_crash_protection.js`

Tests:
- Invalid API responses
- Missing data handling
- WebSocket interruption
- AI engine error responses
- ErrorBoundary validation
- Memory leak protection
- Infinite loop protection

**Success Criteria:**
- ErrorBoundary catches errors
- UI does not crash

### 8. MEMORY SAFETY TESTS
**File:** `test_memory_safety.py`

Tests:
- AI pipeline memory usage
- 50,000 executions
- Memory growth monitoring
- Garbage collection efficiency
- Reference cycle handling
- Large object handling
- Concurrent memory usage

**Success Criteria:**
- Memory stable
- No leaks detected

### 9. FULL SYSTEM CHAOS TESTS
**File:** `test_full_system_chaos.py`

Tests:
- LiveMetrics → AI engines pipeline
- AI engines orchestrator
- Signal logger integration
- API → Frontend pipeline
- 1000 market updates
- Pipeline latency under load
- System throughput
- Error propagation

**Success Criteria:**
- Pipeline latency < 1 second
- System remains stable under load

## 🎯 SUCCESS CRITERIA

The system must pass if:

| Metric | Target | Status |
|--------|--------|--------|
| AI Engine Latency | < 1ms | ⏱️ |
| API Latency | < 50ms | ⚡ |
| WebSocket Throughput | ≥ 1000 ticks/sec | 🔌 |
| Pipeline Latency | < 1 second | 🔄 |
| Memory Leaks | < 100MB | 🧠 |
| UI Crash Prevention | 100% | 🛡️ |
| Auth Redirect Loops | 0 | 🔐 |

## 📈 REPORTS

After running tests, comprehensive reports are generated:

### CHAOS_TEST_REPORT.md
- Executive summary
- Test category results
- Performance metrics
- Stability metrics
- Recommendations
- Detailed test results

### chaos_test_report.json
- Machine-readable format
- Complete test data
- Performance metrics
- Analysis results

## 🔧 REQUIREMENTS

### Backend Tests
- Python 3.13+
- asyncio
- httpx
- psutil
- statistics
- tracemalloc

### Frontend Tests
- Node.js 18+
- jsdom
- axios (mocked)

### Optional Dependencies
- pytest (for enhanced testing)
- memory-profiler (for detailed memory analysis)

## 🚨 IMPORTANT NOTES

### DO NOT MODIFY
- Core architecture components
- LiveStructuralEngine
- MarketStateManager
- WebSocket feed system
- Router APIs
- Database schemas

### ALLOWED ACTIONS
- Create helper utilities
- Add validation layers
- Fix authentication session logic
- Add frontend guards
- Add safe reconnection logic
- Create test scripts

### NO BREAKING CHANGES
All tests are designed to be non-destructive and should not modify production data.

## 📊 INTERPRETING RESULTS

### Status Indicators
- ✅ **PASS** - Test completed successfully
- ❌ **FAIL** - Test failed with critical issues
- ⚠️ **PARTIAL** - Test completed with some failures
- ⏭️ **SKIP** - Test skipped (usually due to missing dependencies)

### Performance Grades
- **A** (90-100%) - Production ready
- **B** (80-89%) - Staging ready
- **C** (70-79%) - Development ready
- **F** (<70%) - Not ready

### Readiness Levels
- **PRODUCTION_READY** - All critical tests pass
- **STAGING_READY** - Minor issues, acceptable for staging
- **DEVELOPMENT_READY** - Some issues, needs fixes
- **NOT_READY** - Critical failures, not deployable

## 🔄 CONTINUOUS TESTING

For CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run Chaos Tests
  run: |
    python run_chaos_tests.py
    if [ $? -ne 0 ]; then
      echo "Chaos tests failed"
      exit 1
    fi
```

## 🐛 TROUBLESHOOTING

### Common Issues

1. **Backend Offline Tests**
   - Ensure backend is running for live tests
   - Offline tests simulate failures and should pass even when backend is down

2. **Memory Test Failures**
   - Close other applications to free memory
   - Check for system memory constraints

3. **WebSocket Test Failures**
   - Verify WebSocket server is running
   - Check firewall settings

4. **Frontend Test Failures**
   - Ensure Node.js is installed
   - Check for missing dependencies: `npm install`

### Debug Mode

Run individual tests with verbose output:

```bash
# Python tests
cd backend && python -v tests/chaos/test_auth_chaos.py

# JavaScript tests
cd frontend && DEBUG=* node tests/chaos/test_network_failure.js
```

## 📞 SUPPORT

For issues with the chaos test suite:

1. Check individual test logs
2. Review generated reports
3. Verify system requirements
4. Check for known issues in test files

## 📝 CHANGELOG

### v1.0.0 (2026-03-01)
- Initial chaos test suite
- 9 test categories
- Comprehensive reporting
- Success criteria validation
- CI/CD integration ready

---

**⚠️ WARNING:** Chaos tests are designed to stress test the system. Run them in a controlled environment and never against production systems without proper authorization.
