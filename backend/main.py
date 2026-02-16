from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging
from datetime import datetime
from contextlib import asynccontextmanager
import uvicorn
import os
import sys

from app.core.config import settings
from app.models.database import get_db
from app.services.market_dashboard_service import MarketDashboardService
from app.market_data import start_data_scheduler, stop_data_scheduler
from app.market_data.market_data_service import get_latest_option_chain
from app.api.v1 import (
    auth_router,
    market_router,
    options_router,
    system_router,
    predictions_router,
    debug_router,
    intelligence_router,
    live_ws_router
)

# Configure logging with file output
import logging
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
import os
os.makedirs("logs", exist_ok=True)

# DEBUG: Log process ID for debugging
logger = logging.getLogger(__name__)
logger.info(f"Process ID: {os.getpid()}")

# Setup file logging
file_handler = RotatingFileHandler(
    "logs/server.log", 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

# Setup console logging
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    handlers=[file_handler, console_handler]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting StrikeIQ API...")
    
    # Start data scheduler
    try:
        await start_data_scheduler()
        logger.info("Data scheduler started successfully")
    except Exception as e:
        logger.warning(f"Failed to start data scheduler: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down StrikeIQ API...")
    await stop_data_scheduler()


app = FastAPI(
    title="StrikeIQ API",
    description="Options Market Intelligence SaaS for Indian Markets",
    version="2.0.0",
    lifespan=lifespan
)

# Include all v1 routers
app.include_router(auth_router)
app.include_router(market_router)
app.include_router(options_router)
app.include_router(system_router)
app.include_router(predictions_router)
app.include_router(debug_router)
app.include_router(intelligence_router)
app.include_router(live_ws_router)

# CORS middleware - Fixed for WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "ws://localhost:3000", "http://localhost:8000", "ws://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔍 GLOBAL HTTP REQUEST LOGGER FOR AUDIT
@app.middleware("http")
async def log_all_http_requests(request, call_next):
    print(f"🌐 REST HIT: {request.url.path}")
    print(f"🌐 REST METHOD: {request.method}")
    print(f"🌐 REST TIMESTAMP: {datetime.now().isoformat()}")
    
    response = await call_next(request)
    
    print(f"🌐 REST STATUS: {response.status_code}")
    print(f"🌐 REST COMPLETED: {request.url.path}")
    
    return response
logger.info("=== REGISTERED ROUTES ===")
for route in app.routes:
    if hasattr(route, 'path'):
        route_type = getattr(route, 'methods', 'N/A')
        logger.info(f"Route: {route.path} | Methods: {route_type} | Type: {type(route).__name__}")
        
        # Specifically check for WebSocket routes
        if hasattr(route, 'path') and 'ws' in route.path:
            logger.info(f"🔌 WEBSOCKET ROUTE FOUND: {route.path}")
            
logger.info("=== END ROUTES ===")


@app.get("/")
async def root():
    return {"message": "StrikeIQ API is running", "version": "2.0.0"}


# Add simple WebSocket test directly to main app
@app.websocket("/ws/simple-test")
async def simple_websocket_test(websocket: WebSocket):
    """Simple WebSocket test endpoint"""
    print(f"🔌 WebSocket connection attempt to /ws/simple-test")
    try:
        await websocket.accept()
        print(f"✅ WebSocket accepted for /ws/simple-test")
        await websocket.send_text("Hello from simple WebSocket!")
        print(f"📨 Message sent to /ws/simple-test")
        await websocket.close()
        print(f"🔌 WebSocket closed for /ws/simple-test")
    except Exception as e:
        print(f"❌ WebSocket error in /ws/simple-test: {e}")
        await websocket.close()

@app.get("/ws-test")
async def ws_test():
    """Test endpoint to verify server is running"""
    return {"message": "WebSocket test endpoint working", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-10T14:30:00Z"}


@app.get("/api/dashboard/{symbol}")
async def get_dashboard_data(symbol: str, db: Depends = Depends(get_db)):
    """Get real-time dashboard data for a symbol"""
    try:
        service = MarketDashboardService(db)
        data = await service.get_dashboard_data(symbol.upper())
        return data
    except Exception as e:
        logger.error(f"Error in dashboard endpoint for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get latest option chain data for symbol"""
    try:
        data = await get_latest_option_chain(symbol.upper())
        return {
            "status": "success",
            "data": data
        }
    except ValueError as e:
        logger.error(f"Invalid symbol {symbol}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@app.get("/api/v1/auth/upstox")
async def get_upstox_auth_url():
    """Get Upstox OAuth authorization URL"""
    try:
        from app.services.upstox_auth_service import get_upstox_auth_service
        auth_service = get_upstox_auth_service()
        auth_url = auth_service.get_authorization_url()
        return {"authorization_url": auth_url}
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")


@app.get("/api/v1/auth/upstox/callback")
async def upstox_auth_callback(code: str = Query(None)):
    """Handle Upstox OAuth callback"""
    try:
        from app.services.upstox_auth_service import get_upstox_auth_service
        auth_service = get_upstox_auth_service()
        
        # Debug logging
        logger.info(f"Received callback with code: {code}")
        
        if not code:
            logger.error("No authorization code received")
            raise ValueError("Authorization code is required")
        
        token_data = auth_service.exchange_code_for_token(code)
        
        # Redirect to frontend success page
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:3000/auth/success?status=success")
    except ValueError as e:
        logger.error(f"Invalid callback parameters: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in auth callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@app.get("/api/v1/status/data-collection")
async def get_data_collection_status():
    """Get data collection status"""
    try:
        from app.market_data import get_data_scheduler
        scheduler = get_data_scheduler()
        status = await scheduler.get_collection_status()
        return status
    except Exception as e:
        logger.error(f"Error getting data collection status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@app.post("/api/v1/trigger/data-collection")
async def trigger_data_collection(symbol: str = None):
    """Trigger manual data collection"""
    try:
        from app.market_data import get_data_scheduler
        scheduler = get_data_scheduler()
        results = await scheduler.trigger_manual_collection(symbol)
        return {"message": "Data collection triggered", "results": results}
    except Exception as e:
        logger.error(f"Error triggering data collection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger data collection")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
