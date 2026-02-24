from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import uvicorn

from app.market_data.market_data_service import get_latest_option_chain

from app.api.v1 import (
    auth_router,
    market_router,
    options_router,
    system_router,
    predictions_router,
    debug_router,
    intelligence_router,
    market_session_router,
    live_ws_router,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ================= LIFESPAN =================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("🚀 Starting StrikeIQ API...")

    try:
        from app.services.market_session_manager import get_market_session_manager
        app.state.market_session_manager = get_market_session_manager()
        logger.info("✅ Market session manager initialized")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")

    yield

    logger.info("🛑 Shutdown started...")

    try:
        from app.services.websocket_market_feed import ws_feed_manager
        await ws_feed_manager.cleanup_all()
        logger.info("✅ WS feed cleaned up")
    except Exception as e:
        logger.error(f"❌ Shutdown cleanup failed: {e}")

# ================= APP =================

app = FastAPI(
    title="StrikeIQ API",
    version="2.0.0",
    lifespan=lifespan
)

# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= SESSION =================

app.add_middleware(
    SessionMiddleware,
    secret_key="supersecretkey",
    session_cookie="session",
    same_site="lax"
)

# ================= ROUTERS =================

app.include_router(auth_router)
app.include_router(market_router)
app.include_router(options_router)
app.include_router(system_router)
app.include_router(predictions_router)
app.include_router(debug_router)
app.include_router(intelligence_router)
app.include_router(market_session_router)
app.include_router(live_ws_router)

# ================= LOGGER =================

@app.middleware("http")
async def log_all_http_requests(request: Request, call_next):
    print(f"🌐 REST HIT: {request.url.path}")
    response = await call_next(request)
    print(f"🌐 REST STATUS: {response.status_code}")
    return response

# ================= ROOT =================

@app.get("/")
async def root():
    return {"message": "StrikeIQ API running"}

# ================= MARKET =================

@app.get("/api/v1/market-data/{symbol}")
async def get_market_data(symbol: str):
    try:
        data = await get_latest_option_chain(symbol.upper())
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail="Failed")

# ================= OAUTH CALLBACK =================

@app.get("/api/v1/auth/upstox/callback")
async def upstox_auth_callback(code: str = Query(None), state: str = Query(None)):

    try:
        from app.services.upstox_auth_service import get_upstox_auth_service
        from app.services.websocket_market_feed import ws_feed_manager

        auth_service = get_upstox_auth_service()

        if not code:
            raise HTTPException(status_code=400, detail="Authorization code missing")

        logger.info(f"Received OAuth code: {code}")

        # 🔥 Exchange token
        await auth_service.exchange_code_for_token(code)

        logger.info("🟢 TOKEN STORED SUCCESSFULLY")

        # 🔥 START WS AFTER LOGIN
        feed = await ws_feed_manager.start_feed()

        if not feed or not feed.is_connected:
            raise HTTPException(status_code=500, detail="WS connection failed after login")

        logger.info("🟢 WS CONNECTED AFTER LOGIN")

        return RedirectResponse(
            url="http://localhost:5173/auth/success?upstox=connected",
            status_code=302
        )

    except Exception as e:
        logger.error(f"OAuth failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

# ================= FALLBACK =================

@app.get("/upstox/callback")
async def upstox_callback_fallback(code: str = Query(None), state: str = Query(None)):

    if code:
        redirect_url = f"/api/v1/auth/upstox/callback?code={code}"
        if state:
            redirect_url += f"&state={state}"

        return RedirectResponse(
            url=redirect_url,
            status_code=302
        )

    return RedirectResponse(
        url="/api/v1/auth/upstox/callback",
        status_code=302
    )

# ================= WS INIT =================

@app.get("/api/ws/init")
async def init_websocket(request: Request):

    try:
        from app.services.websocket_market_feed import ws_feed_manager

        feed = await ws_feed_manager.start_feed()

        if not feed or not feed.is_connected:
            return JSONResponse(status_code=500, content={"msg":"WS connect failed"})

        request.session["WS_CONNECTED"] = True

        logger.info("✅ WS CONNECTED + SESSION SET")

        return {"status":"connected"}

    except Exception as e:
        logger.error(f"WS init failed: {str(e)}")
        raise HTTPException(status_code=500, detail="WebSocket init failed")

# ================= WS STATUS =================

@app.get("/api/ws/status")
async def check_websocket_status(request: Request):

    if request.session.get("WS_CONNECTED") == True:
        return {"status":"connected"}

    return JSONResponse(status_code=401, content={"msg":"not ready"})

# ================= RUN =================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )