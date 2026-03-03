"""
Integration Example - How to use the new WebSocket Market Status Broadcaster
Add this to your main FastAPI application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from websocket_market_status import market_status_broadcaster, start_market_status_service
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Start services on application startup"""
    # Start the market status broadcasting service
    await start_market_status_service()

@app.websocket("/ws/market")
async def websocket_market_endpoint(websocket: WebSocket):
    """Main market WebSocket endpoint with market status broadcasting"""
    await websocket.accept()
    
    # Add connection to market status broadcaster
    await market_status_broadcaster.add_connection(websocket)
    
    try:
        while True:
            # Handle incoming messages if needed
            data = await websocket.receive_text()
            
            # Echo back or process as needed
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {websocket.client}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Always remove connection on disconnect
        await market_status_broadcaster.remove_connection(websocket)

@app.get("/api/v1/market/session")
async def get_market_session():
    """Existing market session endpoint - keep for compatibility"""
    # This endpoint should continue to work as before
    # The WebSocket broadcaster will call this endpoint
    
    # Your existing implementation here
    return {
        "market_status": "OPEN",  # or your actual logic
        "engine_mode": "LIVE",
        "data_source": "websocket_stream",
        "last_check": datetime.now().isoformat()
    }

# Example: Manual market status update (if you have admin endpoints)
@app.post("/admin/market-status")
async def update_market_status(market_open: bool):
    """Manual market status update endpoint"""
    await market_status_broadcaster.update_market_status(market_open)
    return {"status": "updated", "market_open": market_open}
