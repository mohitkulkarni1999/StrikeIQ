from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any
from ...services.upstox_auth_service import get_upstox_auth_service, UpstoxAuthService
from ...core.config import settings
import logging

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)

import secrets
import urllib.parse

@router.get("/test")
async def test_oauth_flow():
    """Test endpoint to show correct OAuth flow"""
    try:
        auth_service = get_upstox_auth_service()
        state = auth_service.generate_signed_state()
        auth_url = auth_service.get_authorization_url(state)
        
        return {
            "status": "success",
            "message": "This is the correct OAuth flow",
            "steps": [
                "1. Call /api/v1/auth/upstox (not directly accessing callback)",
                "2. Backend generates state and returns authorization URL",
                "3. User is redirected to Upstox with state parameter",
                "4. Upstox redirects back to callback with code AND state",
                "5. Backend validates state and exchanges code for tokens"
            ],
            "correct_auth_url": auth_url,
            "state_parameter": state,
            "note": "Never access the callback URL directly - always go through /api/v1/auth/upstox first"
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate test data")

@router.get("/upstox", response_model=Dict[str, Any])
async def get_upstox_auth_url(request: Request):
    """Get Upstox OAuth authorization URL with rate limiting"""
    try:
        logger.info("API request: Upstox auth URL")
        auth_service = get_upstox_auth_service()
        client_ip = auth_service._get_client_ip(request)
        
        # SECURITY: Check rate limiting before generating state
        if not auth_service._check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        
        # SECURITY: Generate signed state token
        state = auth_service.generate_signed_state()
        
        # SECURITY: Include state in authorization URL
        auth_url = auth_service.get_authorization_url(state)
        
        return {
            "status": "success",
            "data": {
                "authorization_url": auth_url
            }
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")

@router.get("/upstox/callback")
async def upstox_auth_callback(
    request: Request,
    code: str = Query(None, description="Authorization code from Upstox"),
    state: str = Query(None, description="OAuth state parameter"),
    error: str = Query(None, description="OAuth error parameter"),
    error_description: str = Query(None, description="OAuth error description")
):
    """Handle Upstox OAuth callback"""
    try:
        logger.info(f"API request: Upstox callback - code: {code is not None}, state: {state is not None}, error: {error}")
        
        # Handle OAuth errors from Upstox
        if error:
            logger.error(f"OAuth error: {error} - {error_description}")
            raise HTTPException(
                status_code=400, 
                detail=f"OAuth authorization failed: {error_description or error}"
            )
        
        # Check if this is a direct access (should not happen in normal flow)
        if not code and not state:
            logger.warning("Direct access to callback endpoint without OAuth parameters")
            raise HTTPException(
                status_code=400,
                detail="This endpoint should only be accessed via OAuth redirect. Please initiate authentication through /api/v1/auth/upstox"
            )
        
        if not code:
            logger.error("No authorization code received in OAuth callback")
            raise HTTPException(status_code=400, detail="Authorization code is required")
        
        if not state:
            logger.warning("No state parameter received - this may indicate a security issue")
            
            # For development/testing: Allow code-only access with a generated state
            if code and settings.ENVIRONMENT == "development":
                logger.info("Development mode: Generating fallback state for testing")
                auth_service = get_upstox_auth_service()
                fallback_state = auth_service.generate_signed_state()
                logger.info(f"Generated fallback state: {fallback_state}")
                state = fallback_state
            else:
                # Production: Return helpful error response
                return {
                    "error": "missing_state",
                    "message": "State parameter is missing. Please initiate OAuth flow from the beginning.",
                    "solution": "Access /api/v1/auth/upstox to start the OAuth process",
                    "auth_url": "/api/v1/auth/upstox",
                    "development_note": "In development mode, you can access the callback with just a code parameter"
                }
        
        # auth_service is already defined above if fallback was used, otherwise get it here
        if 'auth_service' not in locals():
            auth_service = get_upstox_auth_service()
        
        client_ip = auth_service._get_client_ip(request)
        
        # SECURITY: Validate signed state parameter
        if not auth_service.validate_signed_state(state):
            logger.error(f"Invalid or expired state: {state}")
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
        
        # SECURITY: Check rate limiting
        if not auth_service._check_rate_limit(client_ip):
            logger.error(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        
        token_data = auth_service.exchange_code_for_token(code)
        
        # Redirect to frontend success page with state validation
        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/success?status=success&state={state}",
            status_code=302
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error in auth callback: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")
