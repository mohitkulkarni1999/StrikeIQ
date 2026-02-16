from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """Simple WebSocket test"""
    await websocket.accept()
    await websocket.send_text("WebSocket working!")
    await websocket.close()

@app.websocket("/ws/live-options/{symbol}")
async def websocket_live(websocket: WebSocket, symbol: str):
    """Live options WebSocket"""
    await websocket.accept()
    await websocket.send_json({
        "status": "connected",
        "symbol": symbol,
        "message": "WebSocket connection successful"
    })
    
    # Send heartbeat
    import asyncio
    while True:
        await asyncio.sleep(5)
        await websocket.send_json({
            "status": "heartbeat",
            "symbol": symbol
        })

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting minimal WebSocket server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
