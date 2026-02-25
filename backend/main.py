from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import uvicorn

# ================= AI IMPORT =================
from ai.scheduler import ai_scheduler
from app.services.live_structural_engine import LiveStructuralEngine
from app.services.websocket_market_feed import ws_feed_manager
# ============================================

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

from app.api.v1.ws.live_options import router as ui_ws_router

# 🔥 INSTRUMENT REGISTRY (MOST IMPORTANT)
from app.core.instrument_runtime import registry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ================= LIFESPAN =================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("🚀 Starting StrikeIQ API...")

    # ================= LOAD CDN FIRST =================
    try:
        logger.info("📦 Loading Upstox Instruments CDN...")
        await registry.load()  # 🔥 BLOCK SYSTEM BOOT HERE
        logger.info("✅ Instruments Ready")
        logger.info("🟢 Instrument store ready")
    except Exception as e:
        logger.error(f"❌ Instrument load failed: {e}")

    # ================= LIVE OPTION CHAIN BUILDER =================
    try:
        from app.services.live_option_chain_builder import get_live_chain_builder
        builder = get_live_chain_builder()
        await builder.start()
        logger.info("✅ Live Option Chain Builder Started")
    except Exception as e:
        logger.error(f"❌ Live Option Chain Builder startup failed: {e}")

    # ================= MARKET SESSION =================
    try:
        from app.services.market_session_manager import get_market_session_manager
        app.state.market_session_manager = get_market_session_manager()
        logger.info("✅ Market session manager initialized")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")

    # ================= LIVE STRUCTURAL ENGINE =================
    try:
        market_state_manager = ws_feed_manager.market_states
        app.state.live_engine = LiveStructuralEngine(market_state_manager)
        asyncio.create_task(app.state.live_engine.start_analytics_loop())
        logger.info("🧠 Live Structural Analytics Engine Started")
    except Exception as e:
        logger.error(f"❌ Live AI Engine startup failed: {e}")

    # ================= AI LEARNING ENGINE =================
    try:
        logger.info("🧠 Starting StrikeIQ AI Learning Engine...")
        ai_scheduler.start()
        logger.info("✅ AI Scheduler Started")
    except Exception as e:
        logger.error(f"❌ AI Scheduler start failed: {e}")

    yield

    logger.info("🛑 Shutdown started...")

    try:
        await ws_feed_manager.cleanup_all()
        logger.info("✅ WS feed cleaned up")
    except Exception as e:
        logger.error(f"❌ Shutdown cleanup failed: {e}")

    try:
        logger.info("🧠 Stopping StrikeIQ AI Learning Engine...")
        ai_scheduler.stop()
        logger.info("✅ AI Scheduler Stopped")
    except Exception as e:
        logger.error(f"❌ AI Scheduler stop failed: {e}")

# ================= APP =================

app = FastAPI(
    title="StrikeIQ API",
    version="2.0.0",
    lifespan=lifespan
)

# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
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
app.include_router(ui_ws_router)

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

# ================= WS INIT =================

@app.get("/api/ws/init")
async def init_websocket(request: Request):

    try:
        feed = await ws_feed_manager.start_feed()

        if not feed or not feed.is_connected:
            return JSONResponse(status_code=500, content={"msg":"WS connect failed"})

        request.session["WS_CONNECTED"] = True

        logger.info("✅ WS CONNECTED + SESSION SET")

        return {"status":"connected"}

    except Exception as e:
        logger.error(f"WS init failed: {str(e)}")
        raise HTTPException(status_code=500, detail="WebSocket init failed")

# ================= RUN =================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )