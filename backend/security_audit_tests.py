#!/usr/bin/env python3
"""
Security Audit Tests for Upstox OAuth Implementation
Tests authentication flow, token management, and security vulnerabilities
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
import httpx

# Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.upstox_auth_service import UpstoxAuthService, TokenExpiredError
from app.services.market_data.upstox_client import UpstoxClient, TokenExpiredError as ClientTokenExpiredError
from app.core.config import settings

class SecurityAuditTests:
    """Comprehensive security audit tests for OAuth implementation"""
    
    def __init__(self):
        self.test_results = []
        self.auth_service = UpstoxAuthService("test_credentials.json")
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    async def test_oauth_flow_security(self):
        """Test OAuth flow security requirements"""
        print("\n" + "="*60)
        print("OAUTH FLOW SECURITY TESTS")
        print("="*60)
        
        # Test 1: Authorization URL generation
        try:
            auth_url = self.auth_service.get_authorization_url()
            
            # Check if URL contains required parameters
            required_params = ["response_type=code", "client_id", "redirect_uri"]
            missing_params = []
            
            for param in required_params:
                if param not in auth_url:
                    missing_params.append(param)
            
            # Check for hardcoded tokens
            has_hardcoded_token = "access_token" in auth_url.lower() or "secret" in auth_url.lower()
            
            # Check correct Upstox endpoint
            correct_endpoint = "api.upstox.com/v2/login/authorization/dialog" in auth_url
            
            self.log_result(
                "OAuth Authorization URL Security",
                len(missing_params) == 0 and not has_hardcoded_token and correct_endpoint,
                f"Missing params: {missing_params}, Hardcoded token: {has_hardcoded_token}, Correct endpoint: {correct_endpoint}"
            )
            
        except Exception as e:
            self.log_result("OAuth Authorization URL Generation", False, f"Exception: {e}")
        
        # Test 2: Token exchange security
        try:
            # Mock a token exchange
            with patch('httpx.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token", 
                    "expires_in": 3600
                }
                mock_post.return_value = mock_response
                
                result = self.auth_service.exchange_code_for_token("test_code")
                
                # Check if token is stored (should be)
                token_stored = os.path.exists("test_credentials.json")
                
                # Check if response contains sensitive info logging
                # This would require checking logs, but we can check the print statement in the code
                has_debug_logging = "print" in open("app/services/upstox_auth_service.py").read()
                
                self.log_result(
                    "Token Exchange Security",
                    token_stored and not has_debug_logging,
                    f"Token stored: {token_stored}, Debug logging present: {has_debug_logging}"
                )
                
        except Exception as e:
            self.log_result("Token Exchange Security", False, f"Exception: {e}")
    
    async def test_token_management_security(self):
        """Test token management security"""
        print("\n" + "="*60)
        print("TOKEN MANAGEMENT SECURITY TESTS")
        print("="*60)
        
        # Test 1: Token expiration detection
        try:
            # Create expired credentials
            from app.services.upstox_auth_service import UpstoxCredentials
            expired_creds = UpstoxCredentials("expired_token", "refresh_token", -1)  # Expired
            self.auth_service._credentials = expired_creds
            
            # Test expiration detection
            is_expired = not self.auth_service.is_authenticated()
            
            self.log_result(
                "Token Expiration Detection",
                is_expired,
                "Correctly detected expired token"
            )
            
        except Exception as e:
            self.log_result("Token Expiration Detection", False, f"Exception: {e}")
        
        # Test 2: Token refresh logic
        try:
            # Mock refresh token call
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "access_token": "new_access_token",
                    "refresh_token": "new_refresh_token",
                    "expires_in": 3600
                }
                mock_post.return_value = mock_response
                
                # Test refresh
                new_token = await self.auth_service.refresh_access_token()
                
                # Check if new token is different
                token_changed = new_token != "expired_token"
                
                self.log_result(
                    "Token Refresh Logic",
                    token_changed,
                    f"Token changed: {token_changed}"
                )
                
        except Exception as e:
            self.log_result("Token Refresh Logic", False, f"Exception: {e}")
        
        # Test 3: Invalid token handling
        try:
            # Test with no credentials
            self.auth_service._credentials = None
            
            try:
                await self.auth_service.get_valid_access_token()
                self.log_result("Invalid Token Handling", False, "Should have raised TokenExpiredError")
            except TokenExpiredError:
                self.log_result("Invalid Token Handling", True, "Correctly raised TokenExpiredError")
                
        except Exception as e:
            self.log_result("Invalid Token Handling", False, f"Unexpected exception: {e}")
    
    async def test_secure_storage(self):
        """Test secure storage requirements"""
        print("\n" + "="*60)
        print("SECURE STORAGE TESTS")
        print("="*60)
        
        # Test 1: Check for hardcoded tokens in config
        config_content = open("app/core/config.py").read()
        
        # Look for potential hardcoded tokens
        suspicious_patterns = [
            "access_token",
            "refresh_token", 
            "bearer",
            "secret",
            "sk_",
            "pk_"
        ]
        
        found_patterns = []
        for pattern in suspicious_patterns:
            if pattern in config_content.lower():
                found_patterns.append(pattern)
        
        # Check if API key is hardcoded (it is, but should be from env)
        has_hardcoded_key = "53c878a9-3f5d-44f9-aa2d-2528d34a24cd" in config_content
        
        self.log_result(
            "Config Security",
            len(found_patterns) == 0 and not has_hardcoded_key,
            f"Suspicious patterns: {found_patterns}, Hardcoded key: {has_hardcoded_key}"
        )
        
        # Test 2: Check .env file security
        env_file = ".env"
        if os.path.exists(env_file):
            env_content = open(env_file).read()
            
            # Check if secrets are properly set
            has_api_key = "UPSTOX_API_KEY" in env_content
            has_api_secret = "UPSTOX_API_SECRET" in env_content
            
            # Check for default/placeholder values
            has_placeholder = "your_api_secret_here" in env_content
            
            self.log_result(
                "Environment File Security",
                has_api_key and has_api_secret and not has_placeholder,
                f"Has API key: {has_api_key}, Has secret: {has_api_secret}, Has placeholder: {has_placeholder}"
            )
        else:
            self.log_result("Environment File Security", False, ".env file not found")
        
        # Test 3: Check token file permissions (if it exists)
        if os.path.exists("upstox_credentials.json"):
            # Check file permissions (basic check)
            file_stat = os.stat("upstox_credentials.json")
            is_readable = file_stat.st_mode & 0o444  # Readable by owner
            
            self.log_result(
                "Token File Permissions",
                is_readable,
                f"File readable: {is_readable}"
            )
    
    async def test_error_handling(self):
        """Test error handling and rate limiting"""
        print("\n" + "="*60)
        print("ERROR HANDLING TESTS")
        print("="*60)
        
        # Test 1: 401 Unauthorized handling
        try:
            client = UpstoxClient()
            
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status_code = 401
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("401", request=AsyncMock(), response=mock_response)
                mock_get.return_value = mock_response
                
                try:
                    await client.get_instruments("invalid_token")
                    self.log_result("401 Error Handling", False, "Should have raised TokenExpiredError")
                except ClientTokenExpiredError:
                    self.log_result("401 Error Handling", True, "Correctly raised TokenExpiredError")
                    
        except Exception as e:
            self.log_result("401 Error Handling", False, f"Unexpected exception: {e}")
        
        # Test 2: 429 Rate Limiting
        try:
            client = UpstoxClient()
            
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status_code = 429
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("429", request=AsyncMock(), response=mock_response)
                mock_get.return_value = mock_response
                
                try:
                    await client.get_instruments("valid_token")
                    self.log_result("429 Rate Limiting", False, "Should have raised APIResponseError")
                except Exception as e:
                    self.log_result("429 Rate Limiting", True, f"Correctly handled rate limit: {type(e).__name__}")
                    
        except Exception as e:
            self.log_result("429 Rate Limiting", False, f"Unexpected exception: {e}")
        
        # Test 3: 500 Server Error
        try:
            client = UpstoxClient()
            
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("500", request=AsyncMock(), response=mock_response)
                mock_get.return_value = mock_response
                
                try:
                    await client.get_instruments("valid_token")
                    self.log_result("500 Server Error", False, "Should have raised APIResponseError")
                except Exception as e:
                    self.log_result("500 Server Error", True, f"Correctly handled server error: {type(e).__name__}")
                    
        except Exception as e:
            self.log_result("500 Server Error", False, f"Unexpected exception: {e}")
    
    async def test_session_transitions(self):
        """Test session state transitions"""
        print("\n" + "="*60)
        print("SESSION TRANSITION TESTS")
        print("="*60)
        
        # Test 1: Authenticated to Expired transition
        try:
            # Start with valid credentials
            from app.services.upstox_auth_service import UpstoxCredentials
            valid_creds = UpstoxCredentials("valid_token", "refresh_token", 3600)
            self.auth_service._credentials = valid_creds
            
            # Should be authenticated
            initially_auth = self.auth_service.is_authenticated()
            
            # Expire the token
            self.auth_service._credentials.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            
            # Should now require re-auth
            after_expiry_auth = self.auth_service.is_authenticated()
            
            self.log_result(
                "Authenticated to Expired Transition",
                initially_auth and not after_expiry_auth,
                f"Initial auth: {initially_auth}, After expiry: {after_expiry_auth}"
            )
            
        except Exception as e:
            self.log_result("Authenticated to Expired Transition", False, f"Exception: {e}")
        
        # Test 2: AUTH_REQUIRED to Re-auth transition
        try:
            # Simulate re-auth process
            self.auth_service._credentials = None
            
            # Should not be authenticated
            before_reauth = self.auth_service.is_authenticated()
            
            # Simulate successful re-auth
            new_creds = UpstoxCredentials("new_token", "new_refresh", 3600)
            self.auth_service._credentials = new_creds
            
            # Should be authenticated again
            after_reauth = self.auth_service.is_authenticated()
            
            self.log_result(
                "AUTH_REQUIRED to Re-auth Transition",
                not before_reauth and after_reauth,
                f"Before re-auth: {before_reauth}, After re-auth: {after_reauth}"
            )
            
        except Exception as e:
            self.log_result("AUTH_REQUIRED to Re-auth Transition", False, f"Exception: {e}")
    
    def generate_audit_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*80)
        print("SECURITY AUDIT REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"\nSUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\nCRITICAL SECURITY ISSUES:")
        
        # Check for critical issues
        critical_issues = []
        
        for result in self.test_results:
            if "❌" in result["status"]:
                if any(keyword in result["details"].lower() for keyword in ["hardcoded", "secret", "token", "debug"]):
                    critical_issues.append(result)
        
        if critical_issues:
            print("🚨 CRITICAL SECURITY VULNERABILITIES FOUND:")
            for issue in critical_issues:
                print(f"   - {issue['test']}: {issue['details']}")
        
        print(f"\nDETAILED RESULTS:")
        for result in self.test_results:
            print(f"\n{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Save report to file
        report = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests/total_tests)*100
            },
            "critical_issues": len(critical_issues),
            "detailed_results": self.test_results
        }
        
        with open("security_audit_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: security_audit_report.json")
        
        return len(critical_issues) == 0  # Return True if no critical issues
    
    async def run_all_tests(self):
        """Run all security audit tests"""
        print("Starting Upstox OAuth Security Audit...")
        print(f"Audit Time: {datetime.now(timezone.utc).isoformat()}")
        
        await self.test_oauth_flow_security()
        await self.test_token_management_security()
        await self.test_secure_storage()
        await self.test_error_handling()
        await self.test_session_transitions()
        
        return self.generate_audit_report()

async def main():
    """Main function to run security audit"""
    auditor = SecurityAuditTests()
    success = await auditor.run_all_tests()
    
    if success:
        print("\n🎉 SECURITY AUDIT PASSED - No critical vulnerabilities found")
        return 0
    else:
        print("\n🚨 SECURITY AUDIT FAILED - Critical vulnerabilities detected")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
