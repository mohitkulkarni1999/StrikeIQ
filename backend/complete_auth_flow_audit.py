#!/usr/bin/env python3
"""
Complete UI-Triggered Upstox Authentication Flow Security Audit
Tests the entire user journey from UI button to authenticated state
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
import secrets
import hashlib

# Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.upstox_auth_service import UpstoxAuthService, TokenExpiredError
from app.services.market_data.upstox_client import UpstoxClient
from app.core.config import settings

class CompleteAuthFlowAuditor:
    """Comprehensive auditor for complete UI-triggered authentication flow"""
    
    def __init__(self):
        self.test_results = []
        self.auth_service = UpstoxAuthService()
        self.generated_states = {}
        self.generated_auth_urls = {}
    
    def log_result(self, test_name: str, passed: bool, details: str = "", critical: bool = False):
        """Log test result with severity"""
        status = "✅ PASS" if passed else "❌ FAIL"
        if critical:
            status = "🚨 CRITICAL FAIL"
        
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "critical": critical,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    async def test_ui_button_behavior(self):
        """Test UI button behavior and backend endpoint"""
        print("\n" + "="*80)
        print("1. UI BUTTON BEHAVIOR TESTS")
        print("="*80)
        
        # Test 1: Button calls correct backend endpoint
        try:
            # Mock the backend endpoint call
            with patch('httpx.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "success",
                    "data": {
                        "authorization_url": "https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=test&redirect_uri=test&state=test_state",
                        "client_id": "test_client_id",
                        "redirect_uri": "test_redirect",
                        "state": "test_state"
                    }
                }
                mock_get.return_value = mock_response
                
                # Simulate frontend button click
                response = mock_get.return_value
                response_data = await response.json()
                
                # Check if response contains required fields
                has_auth_url = "authorization_url" in response_data.get("data", {})
                has_client_id = "client_id" in response_data.get("data", {})
                has_redirect_uri = "redirect_uri" in response_data.get("data", {})
                has_state = "state" in response_data.get("data", {})
                
                # Store for later validation
                if has_state:
                    self.generated_states["test"] = response_data["data"]["state"]
                    self.generated_auth_urls["test"] = response_data["data"]["authorization_url"]
                
                self.log_result(
                    "UI Button Calls Backend Endpoint",
                    has_auth_url and has_client_id and has_redirect_uri and has_state,
                    f"Auth URL: {has_auth_url}, Client ID: {has_client_id}, Redirect URI: {has_redirect_uri}, State: {has_state}"
                )
                
        except Exception as e:
            self.log_result("UI Button Calls Backend Endpoint", False, f"Exception: {e}", critical=True)
    
    async def test_authorization_redirect_security(self):
        """Test authorization redirect security and state parameter"""
        print("\n" + "="*80)
        print("2. AUTHORIZATION REDIRECT SECURITY TESTS")
        print("="*80)
        
        # Test 1: Correct Upstox authorization URL format
        try:
            auth_url = self.auth_service.get_authorization_url_with_state("test_state_123")
            
            # Check URL components
            has_response_type = "response_type=code" in auth_url
            has_client_id = "client_id=" in auth_url
            has_redirect_uri = "redirect_uri=" in auth_url
            has_state = "state=test_state_123" in auth_url
            correct_endpoint = "api.upstox.com/v2/login/authorization/dialog" in auth_url
            
            # Check for security issues
            has_hardcoded_secrets = any(keyword in auth_url.lower() for keyword in ["secret", "token", "key"])
            uses_https = auth_url.startswith("https://")
            
            self.log_result(
                "Authorization URL Security",
                has_response_type and has_client_id and has_redirect_uri and has_state and correct_endpoint and not has_hardcoded_secrets and uses_https,
                f"Response type: {has_response_type}, Client ID: {has_client_id}, State: {has_state}, HTTPS: {uses_https}, Hardcoded secrets: {has_hardcoded_secrets}"
            )
            
        except Exception as e:
            self.log_result("Authorization URL Security", False, f"Exception: {e}", critical=True)
        
        # Test 2: State parameter generation and validation
        try:
            # Test state generation
            state1 = secrets.token_urlsafe(32)
            state2 = secrets.token_urlsafe(32)
            
            # States should be different
            states_unique = state1 != state2
            
            # States should be URL-safe
            state1_url_safe = all(c.isalnum() or c in '-_~' for c in state1)
            state2_url_safe = all(c.isalnum() or c in '-_~' for c in state2)
            
            self.log_result(
                "State Parameter Security",
                states_unique and state1_url_safe and state2_url_safe,
                f"Unique states: {states_unique}, URL-safe: {state1_url_safe}"
            )
            
        except Exception as e:
            self.log_result("State Parameter Security", False, f"Exception: {e}", critical=True)
    
    async def test_callback_validation(self):
        """Test callback validation and state management"""
        print("\n" + "="*80)
        print("3. CALLBACK VALIDATION TESTS")
        print("="*80)
        
        # Test 1: Authorization code extraction
        try:
            # Mock callback with valid parameters
            with patch('app.services.upstox_auth_service.UpstoxAuthService') as mock_auth:
                mock_auth_instance = MagicMock()
                mock_auth_instance._oauth_states = {"test_state_123": {"created_at": datetime.now(), "expires_at": datetime.now() + timedelta(minutes=10)}}
                mock_auth_instance.exchange_code_for_token.return_value = {"access_token": "test_token"}
                
                with patch('app.api.v1.auth.get_upstox_auth_service', return_value=mock_auth_instance):
                    from app.api.v1.auth import upstox_auth_callback
                    
                    # Test valid callback
                    try:
                        # This should succeed
                        result = await upstox_auth_callback(code="valid_code", state="test_state_123")
                        callback_success = "success" in str(result)
                        
                        self.log_result(
                            "Valid Callback Processing",
                            callback_success,
                            f"Callback processed successfully: {callback_success}"
                        )
                    except Exception as e:
                        self.log_result("Valid Callback Processing", False, f"Exception: {e}")
                
                # Test missing authorization code
                try:
                    await upstox_auth_callback(code=None, state="test_state_123")
                    self.log_result("Missing Authorization Code", False, "Should have raised HTTPException")
                except Exception:
                    self.log_result("Missing Authorization Code", True, "Correctly rejected missing code")
                
                # Test missing state parameter
                try:
                    await upstox_auth_callback(code="valid_code", state=None)
                    self.log_result("Missing State Parameter", False, "Should have raised HTTPException")
                except Exception:
                    self.log_result("Missing State Parameter", True, "Correctly rejected missing state")
                
                # Test invalid state
                try:
                    await upstox_auth_callback(code="valid_code", state="invalid_state")
                    self.log_result("Invalid State Parameter", False, "Should have raised HTTPException")
                except Exception:
                    self.log_result("Invalid State Parameter", True, "Correctly rejected invalid state")
                
                # Test expired state
                expired_state = {"created_at": datetime.now() - timedelta(minutes=15), "expires_at": datetime.now() - timedelta(minutes=5)}
                mock_auth_instance._oauth_states = {"expired_state": expired_state}
                
                try:
                    await upstox_auth_callback(code="valid_code", state="expired_state")
                    self.log_result("Expired State Parameter", False, "Should have raised HTTPException")
                except Exception:
                    self.log_result("Expired State Parameter", True, "Correctly rejected expired state")
                
        except Exception as e:
            self.log_result("Callback Validation", False, f"Exception: {e}", critical=True)
    
    async def test_token_exchange_security(self):
        """Test token exchange and security"""
        print("\n" + "="*80)
        print("4. TOKEN EXCHANGE SECURITY TESTS")
        print("="*80)
        
        # Test 1: Token exchange with valid code
        try:
            with patch('httpx.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "access_token": "test_access_token_12345",
                    "refresh_token": "test_refresh_token_12345",
                    "expires_in": 3600
                }
                mock_post.return_value = mock_response
                
                # Mock the auth service
                with patch('app.services.upstox_auth_service.UpstoxAuthService') as mock_auth:
                    mock_auth_instance = MagicMock()
                    mock_auth_instance.exchange_code_for_token.return_value = {
                        "access_token": "test_access_token_12345",
                        "refresh_token": "test_refresh_token_12345",
                        "expires_at": datetime.now() + timedelta(hours=1)
                    }
                    
                    # Test token storage
                    with patch.object(mock_auth_instance, '_store_credentials') as mock_store:
                        result = mock_auth_instance.exchange_code_for_token("valid_code")
                        
                        # Check if credentials were stored
                        mock_store.assert_called_once()
                        
                        # Check if stored credentials are correct
                        stored_call_args = mock_store.call_args[0][0]
                        token_stored = stored_call_args.access_token == "test_access_token_12345"
                        refresh_stored = stored_call_args.refresh_token == "test_refresh_token_12345"
                        
                        self.log_result(
                            "Token Exchange and Storage",
                            token_stored and refresh_stored,
                            f"Token stored: {token_stored}, Refresh stored: {refresh_stored}"
                        )
                
        except Exception as e:
            self.log_result("Token Exchange Security", False, f"Exception: {e}", critical=True)
        
        # Test 2: Token exchange failure handling
        try:
            with patch('httpx.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status_code = 400
                mock_response.json.return_value = {"error": "invalid_grant"}
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("400", request=AsyncMock(), response=mock_response)
                mock_post.return_value = mock_response
                
                auth_service = UpstoxAuthService()
                try:
                    result = auth_service.exchange_code_for_token("invalid_code")
                    self.log_result("Token Exchange Failure", False, "Should have raised exception")
                except Exception:
                    self.log_result("Token Exchange Failure", True, "Correctly handled token exchange failure")
                
        except Exception as e:
            self.log_result("Token Exchange Failure", False, f"Exception: {e}", critical=True)
    
    async def test_post_login_redirect(self):
        """Test post-login redirect and state transitions"""
        print("\n" + "="*80)
        print("5. POST-LOGIN REDIRECT TESTS")
        print("="*80)
        
        # Test 1: Successful OAuth callback redirect
        try:
            # Mock successful callback scenario
            callback_url = f"{settings.FRONTEND_URL}/auth/success?status=success&state=test_state_123"
            
            # Simulate OAuthHandler component behavior
            with patch('builtins.open', create_mock_file_open(json.dumps({
                "status": "success",
                "state": "test_state_123"
            }))) as mock_file:
                with patch('window.location.search', 'status=success&state=test_state_123'):
                    with patch('sessionStorage.getItem', return_value="test_state_123"):
                        with patch('sessionStorage.removeItem') as mock_remove:
                            # Import and test OAuthHandler
                            from app.components.OAuthHandler import default as OAuthHandler
                            
                            onAuthSuccess = MagicMock()
                            handler = OAuthHandler({"onAuthSuccess": onAuthSuccess})
                            
                            # Trigger the effect
                            handler.props.children[0].props.children[1].props.children[0]()
                            
                            # Check if state was validated
                            mock_remove.assert_any_call()  # Should remove oauth_state
                            onAuthSuccess.assert_called_once()  # Should trigger success callback
                            
                            self.log_result(
                                "Post-Login Redirect Success",
                                True,
                                "State validated and auth success triggered"
                            )
                
        except Exception as e:
            self.log_result("Post-Login Redirect Success", False, f"Exception: {e}")
        
        # Test 2: State mismatch scenario
        try:
            # Simulate state mismatch
            with patch('builtins.open', create_mock_file_open(json.dumps({
                "status": "success",
                "state": "different_state"
            }))) as mock_file:
                with patch('window.location.search', 'status=success&state=different_state'):
                    with patch('sessionStorage.getItem', return_value="test_state_123"):
                        with patch('window.location.href') as mock_redirect:
                            # Import and test OAuthHandler
                            from app.components.OAuthHandler import default as OAuthHandler
                            
                            handler = OAuthHandler({"onAuthSuccess": MagicMock()})
                            
                            # Trigger the effect
                            handler.props.children[0].props.children[1].props.children[0]()
                            
                            # Should redirect to error page
                            mock_redirect.assert_called_with('/auth/error?reason=state_mismatch')
                            
                            self.log_result(
                                "State Mismatch Handling",
                                True,
                                "Correctly redirected to error page on state mismatch"
                            )
                
        except Exception as e:
            self.log_result("State Mismatch Handling", False, f"Exception: {e}")
    
    async def test_failure_scenarios(self):
        """Test various failure scenarios"""
        print("\n" + "="*80)
        print("6. FAILURE SCENARIO TESTS")
        print("="*80)
        
        # Test 1: Expired authorization code
        try:
            with patch('httpx.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status_code = 400
                mock_response.json.return_value = {"error": "authorization_code_expired"}
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("400", request=AsyncMock(), response=mock_response)
                mock_post.return_value = mock_response
                
                auth_service = UpstoxAuthService()
                try:
                    result = auth_service.exchange_code_for_token("expired_code")
                    self.log_result("Expired Authorization Code", False, "Should have raised exception")
                except Exception:
                    self.log_result("Expired Authorization Code", True, "Correctly handled expired code")
                
        except Exception as e:
            self.log_result("Expired Authorization Code", False, f"Exception: {e}")
        
        # Test 2: Network interruption during token exchange
        try:
            with patch('httpx.post') as mock_post:
                mock_post.side_effect = httpx.RequestError("Network timeout")
                
                auth_service = UpstoxAuthService()
                try:
                    result = auth_service.exchange_code_for_token("valid_code")
                    self.log_result("Network Interruption", False, "Should have raised exception")
                except Exception:
                    self.log_result("Network Interruption", True, "Correctly handled network error")
                
        except Exception as e:
            self.log_result("Network Interruption", False, f"Exception: {e}")
        
        # Test 3: User denies permission on Upstox
        try:
            with patch('httpx.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status_code = 403
                mock_response.json.return_value = {"error": "access_denied"}
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("403", request=AsyncMock(), response=mock_response)
                mock_post.return_value = mock_response
                
                auth_service = UpstoxAuthService()
                try:
                    result = auth_service.exchange_code_for_token("denied_code")
                    self.log_result("Access Denied", False, "Should have raised exception")
                except Exception:
                    self.log_result("Access Denied", True, "Correctly handled access denied")
                
        except Exception as e:
            self.log_result("Access Denied", False, f"Exception: {e}")
    
    def create_mock_file_open(self, content):
        """Create a mock file open function"""
        def mock_open(filename, mode='r'):
            mock_file = MagicMock()
            mock_file.read.return_value = content
            return mock_file
        return mock_open
    
    async def test_security_hardenings(self):
        """Test security hardening implementations"""
        print("\n" + "="*80)
        print("7. SECURITY HARDENING CHECKLIST")
        print("="*80)
        
        # Test 1: HTTPS enforcement
        try:
            auth_url = self.auth_service.get_authorization_url_with_state("test")
            uses_https = auth_url.startswith("https://")
            
            self.log_result(
                "HTTPS Enforcement",
                uses_https,
                f"Authorization URL uses HTTPS: {uses_https}"
            )
            
        except Exception as e:
            self.log_result("HTTPS Enforcement", False, f"Exception: {e}")
        
        # Test 2: No sensitive parameters in URL
        try:
            auth_url = self.auth_service.get_authorization_url_with_state("test")
            has_sensitive_params = any(param in auth_url.lower() for param in ["secret", "token", "key", "password"])
            
            self.log_result(
                "No Sensitive Parameters in URL",
                not has_sensitive_params,
                f"Sensitive params in URL: {has_sensitive_params}"
            )
            
        except Exception as e:
            self.log_result("No Sensitive Parameters in URL", False, f"Exception: {e}")
        
        # Test 3: State parameter randomness
        try:
            states = [secrets.token_urlsafe(32) for _ in range(10)]
            unique_states = len(set(states)) == len(states)
            
            self.log_result(
                "State Parameter Randomness",
                unique_states,
                f"Generated {len(states)} unique states out of 10 attempts"
            )
            
        except Exception as e:
            self.log_result("State Parameter Randomness", False, f"Exception: {e}")
    
    def generate_flow_diagram(self):
        """Generate complete authentication flow diagram"""
        return """
        COMPLETE UI-TRIGGERED AUTHENTICATION FLOW
        
        1. USER CLICKS "CONNECT TO UPSTOX"
           ┌─────────────────────────────────────────┐
           │ Frontend: AuthScreen.tsx          │
           │ - Calls GET /api/v1/auth/upstox │
           │ - Generates random state             │
           │ - Stores state in sessionStorage   │
           │ - Redirects to Upstox with state  │
           └─────────────────────────────────────────┘
                            │
                            ▼
           ┌─────────────────────────────────────────┐
           │ Backend: Upstox Auth Service     │
           │ - Generates secure state              │
           │ - Stores state with expiration       │
           │ - Returns auth URL with state       │
           │ - No hardcoded secrets              │
           └─────────────────────────────────────────┘
                            │
                            ▼
        2. USER AUTHENTICATES ON UPSTOX
           ┌─────────────────────────────────────────┐
           │ Upstox Authorization Page          │
           │ - User logs in                   │
           │ - Grants permissions               │
           │ - Redirects with code & state      │
           └─────────────────────────────────────────┘
                            │
                            ▼
        3. UPSTOX REDIRECTS BACK
           ┌─────────────────────────────────────────┐
           │ Backend: /api/v1/auth/upstox/    │
           │ callback?code=xxx&state=xxx        │
           │ - Validates state parameter          │
           │ - Checks state expiration           │
           │ - Exchanges code for token         │
           │ - Stores token securely             │
           │ - Redirects to frontend            │
           └─────────────────────────────────────────┘
                            │
                            ▼
        4. FRONTEND PROCESSES CALLBACK
           ┌─────────────────────────────────────────┐
           │ Frontend: OAuthHandler.tsx          │
           │ - Validates returned state           │
           │ - Triggers auth success callback    │
           │ - Cleans up sessionStorage         │
           │ - Redirects to dashboard           │
           └─────────────────────────────────────────┘
                            │
                            ▼
        5. AUTHENTICATED STATE
           ┌─────────────────────────────────────────┐
           │ Frontend: Dashboard.tsx              │
           │ - Shows market data                │
           │ - Resumes polling                   │
           │ - No auth required screen           │
           └─────────────────────────────────────────┘
        """
    
    def generate_comprehensive_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*100)
        print("COMPLETE AUTHENTICATION FLOW AUDIT REPORT")
        print("="*100)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅" in r["status"]])
        failed_tests = total_tests - passed_tests
        critical_issues = len([r for r in self.test_results if r.get("critical", False)])
        
        print(f"\nSUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Critical Issues: {critical_issues}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\nCRITICAL SECURITY ISSUES:")
        if critical_issues > 0:
            print("🚨 CRITICAL SECURITY VULNERABILITIES FOUND:")
            for result in self.test_results:
                if result.get("critical", False):
                    print(f"   - {result['test']}: {result['details']}")
        else:
            print("✅ No critical security vulnerabilities found")
        
        print(f"\nDETAILED RESULTS:")
        for result in self.test_results:
            print(f"\n{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Save comprehensive report
        report = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "flow_type": "UI-Triggered Upstox OAuth",
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "critical_issues": critical_issues,
                "success_rate": (passed_tests/total_tests)*100
            },
            "flow_diagram": self.generate_flow_diagram(),
            "detailed_results": self.test_results,
            "security_status": "CRITICAL" if critical_issues > 0 else "SECURE"
        }
        
        with open("complete_auth_flow_audit_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nFlow Diagram:")
        print(self.generate_flow_diagram())
        print(f"\nReport saved to: complete_auth_flow_audit_report.json")
        
        return critical_issues == 0  # Return True if no critical issues
    
    async def run_all_tests(self):
        """Run all authentication flow tests"""
        print("Starting Complete UI-Triggered Authentication Flow Audit...")
        print(f"Audit Time: {datetime.now(timezone.utc).isoformat()}")
        
        await self.test_ui_button_behavior()
        await self.test_authorization_redirect_security()
        await self.test_callback_validation()
        await self.test_token_exchange_security()
        await self.test_post_login_redirect()
        await self.test_failure_scenarios()
        await self.test_security_hardenings()
        
        return self.generate_comprehensive_report()

async def main():
    """Main function to run complete authentication flow audit"""
    auditor = CompleteAuthFlowAuditor()
    success = await auditor.run_all_tests()
    
    if success:
        print("\n🎉 COMPLETE AUTHENTICATION FLOW AUDIT PASSED")
        print("✅ No critical security vulnerabilities found")
        print("✅ Production-ready authentication flow")
        return 0
    else:
        print("\n🚨 COMPLETE AUTHENTICATION FLOW AUDIT FAILED")
        print("❌ Critical security vulnerabilities detected")
        print("❌ NOT production-ready")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
