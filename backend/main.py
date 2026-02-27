import logging
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

# ================= LOGGING =================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)

logger = logging.getLogger(__name__)

# ================= AI CONFIG =================

ENABLE_AI = False


# ================= CORE =================

from app.services.upstox_auth_service import get_upstox_auth_service
from app.services.websocket_market_feed import ws_feed_manager
from app.services.live_structural_engine import LiveStructuralEngine
from app.services.instrument_registry import get_instrument_registry
from app.core.redis_client import test_redis_connection
from app.market_data.market_data_service import get_latest_option_chain
from ai.scheduler import ai_scheduler


# ================= ROUTERS =================

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
    ws_router,
    ai_status_router,
)

from app.api.v1.ws.live_options import router as ui_ws_router


# ================= LOCK =================

_ws_start_lock = asyncio.Lock()


# ================= LIFESPAN =================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("🚀 Starting StrikeIQ API...")

    # -------- REDIS --------
    try:
        redis_ok = await test_redis_connection()
        if redis_ok:
            logger.info("✅ Redis connection established")
        else:
            logger.warning("⚠️ Redis unavailable")
    except Exception as e:
        logger.error(f"Redis check failed: {e}")

    # -------- INSTRUMENT REGISTRY --------
    try:
        registry = get_instrument_registry()
        await registry.load()
        app.state.registry = registry
        logger.info("🟢 Instrument registry READY")
    except Exception as e:
        logger.error(f"Instrument load failed: {e}")

    # -------- MARKET SESSION --------
    try:
        from app.services.market_session_manager import get_market_session_manager
        app.state.market_session_manager = get_market_session_manager()
    except Exception as e:
        logger.error(f"Market session startup failed: {e}")

    # -------- ANALYTICS ENGINE --------
    try:
        app.state.live_engine = LiveStructuralEngine(ws_feed_manager)

        app.state.analytics_task = asyncio.create_task(
            app.state.live_engine.start_analytics_loop()
        )

        logger.info("🧠 Analytics Engine Started")

    except Exception as e:
        logger.error(f"Live engine startup failed: {e}")

    # -------- AI SCHEDULER --------
    try:
        if ENABLE_AI:
            ai_scheduler.start()
            logger.info("🧠 AI Scheduler Started")
        else:
            logger.info("🧠 AI Scheduler DISABLED")
    except Exception as e:
        logger.error(f"AI Scheduler start failed: {e}")

    yield

    # ================= SHUTDOWN =================

    logger.info("🛑 Shutdown initiated...")

    try:
        if hasattr(app.state, "analytics_task"):
            app.state.analytics_task.cancel()
            await asyncio.gather(app.state.analytics_task, return_exceptions=True)
            logger.info("Analytics loop stopped")
    except Exception as e:
        logger.error(f"Analytics shutdown error: {e}")

    try:
        await ws_feed_manager.cleanup_all()
        logger.info("WS feed cleaned")
    except Exception as e:
        logger.error(f"WS cleanup failed: {e}")

    try:
        if ENABLE_AI:
            ai_scheduler.stop()
    except Exception as e:
        logger.error(f"AI Scheduler stop failed: {e}")

    try:
        auth_service = get_upstox_auth_service()
        await auth_service.close()
        logger.info("Auth service closed")
    except Exception as e:
        logger.error(f"Auth shutdown failed: {e}")


# ================= APP =================

app = FastAPI(
    title="StrikeIQ API",
    version="2.1.0",
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
    secret_key="strikeiq_dev_secret",
    session_cookie="session",
    same_site="lax"
)


# ================= REQUEST LOGGING =================

@app.middleware("http")
async def log_requests(request: Request, call_next):

    logger.info(f"REST → {request.method} {request.url.path}")

    response = await call_next(request)

    logger.info(f"REST ← {response.status_code}")

    return response


# ================= HEALTH =================

@app.get("/health")
async def health():
    return {"status": "ok"}


# ================= ROOT =================

@app.get("/")
async def root():
    return {"message": "StrikeIQ API running"}


# ================= MARKET DATA =================

@app.get("/api/v1/market-data/{symbol}")
async def get_market_data(symbol: str):

    try:

        data = await get_latest_option_chain(symbol.upper())

        return {"status": "success", "data": data}

    except Exception as e:

        logger.error(str(e))

        raise HTTPException(status_code=500, detail="Market fetch failed")


# ================= WS INIT =================

@app.get("/api/ws/init")
async def init_websocket(request: Request):

    async with _ws_start_lock:

        feed = await ws_feed_manager.get_feed()

        if feed and feed.is_connected:

            logger.info("WS already connected")

            return {"status": "already_connected"}

        try:

            feed = await ws_feed_manager.start_feed()

            if not feed or not feed.is_connected:

                return JSONResponse(
                    status_code=500,
                    content={"msg": "WS connect failed"}
                )

            request.session["WS_CONNECTED"] = True

            logger.info("🟢 WS CONNECTED")

            return {"status": "connected"}

        except Exception as e:

            logger.error(f"WS init failed: {str(e)}")

            raise HTTPException(status_code=500, detail="WebSocket init failed")


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
app.include_router(ws_router)
app.include_router(ai_status_router)
app.include_router(ui_ws_router)


# ================= RUN =================

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )