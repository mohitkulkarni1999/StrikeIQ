from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.websocket("/ws/test")
async def websocket_endpoint(websocket: WebSocket):
    """Simple WebSocket endpoint"""
    await websocket.accept()
    await websocket.send_text("WebSocket working!")
    await websocket.close()

@app.get("/")
async def root():
    return {"message": "Minimal WebSocket server"}

if __name__ == "__main__":
    print("Starting minimal FastAPI WebSocket server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
