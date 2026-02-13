from fastapi import APIRouter, HTTPException, Query, Request
from typing import Dict, Any
from ...services.upstox_auth_service import get_upstox_auth_service, UpstoxAuthService
from ...core.config import settings
import logging

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)

import secrets
import urllib.parse

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
    state: str = Query(None, description="OAuth state parameter")
):
    """Handle Upstox OAuth callback"""
    try:
        logger.info(f"API request: Upstox callback with code: {code}, state: {state}")
        
        if not code:
            logger.error("No authorization code received")
            raise HTTPException(status_code=400, detail="Authorization code is required")
        
        if not state:
            logger.warning("No state parameter received - generating temporary state for testing")
            # For testing purposes, generate a temporary state
            auth_service = get_upstox_auth_service()
            state = auth_service.generate_signed_state()
            logger.info(f"Generated temporary state: {state}")
        
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
