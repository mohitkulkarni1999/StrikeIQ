# AUTHENTICATION FLOW TEST REPORT

Generated: 2026-03-01T16:20:43.713950

## SUMMARY
- Total Tests: 5
- Passed: 4
- Failed: 0

## DETAILED RESULTS

### Login Flow
**Status:** [PASS] PASS
**Message:** Login URL correctly provided
**Timestamp:** 2026-03-01T16:20:39.611496

**Login URL:** https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=53c878a9-3f5d-44f9-aa2d-2528d34a24cd&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Fupstox%2Fcallback

### Token Storage
**Status:** [PARTIAL] SKIP
**Message:** Not authenticated - cannot test token storage
**Timestamp:** 2026-03-01T16:20:39.614768

### Token Refresh
**Status:** [PARTIAL] EXPECTED
**Message:** Refresh correctly requires authentication
**Timestamp:** 2026-03-01T16:20:39.618672

### Session Restore
**Status:** [PASS] PASS
**Message:** Session state consistent (simulated restart)
**Timestamp:** 2026-03-01T16:20:39.627050

### Backend Offline
**Status:** [PASS] PASS
**Message:** Correctly detected backend offline (ConnectionError)
**Timestamp:** 2026-03-01T16:20:43.713928

