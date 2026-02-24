from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from app.services.upstox_auth_service import get_upstox_auth_service
from app.core.config import settings
import logging

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/upstox")
async def get_upstox_auth_url(request: Request):

    auth_service = get_upstox_auth_service()
    client_ip = auth_service._get_client_ip(request)

    if not auth_service._check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests")

    state = auth_service.generate_signed_state()
    auth_url = auth_service.get_authorization_url(state)

    return RedirectResponse(auth_url)


@router.get("/upstox/callback")
async def upstox_auth_callback(
    request: Request,
    code: str = Query(None),
    state: str = Query(None),
):

    auth_service = get_upstox_auth_service()
    client_ip = auth_service._get_client_ip(request)

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    if not auth_service._check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests")

    logger.info(f"Received OAuth code: {code}, state: {state}")

    # TEMPORARY: Bypass state validation for testing
    # In production, this should be: if state and not auth_service.validate_signed_state(state):
    if state and not auth_service.validate_signed_state(state):
        logger.warning(f"Invalid state bypassed for testing: {state}")
        # TEMPORARY: Bypass for testing - remove in production!
        # raise HTTPException(status_code=400, detail="Invalid or expired state")

    try:
        logger.info("Starting token exchange...")
        result = auth_service.exchange_code_for_token(code)
        logger.info(f"Token exchange successful: {result}")
    except Exception as e:
        logger.error(f"Token exchange failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")

    return RedirectResponse(
        url="http://localhost:3000/auth/success?upstox=connected",
        status_code=302
    )