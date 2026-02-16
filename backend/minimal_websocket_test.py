from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.websocket("/ws/minimal")
async def minimal_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Minimal WebSocket working!")
    await websocket.close()

@app.get("/")
async def root():
    return {"message": "Minimal WebSocket test server"}

if __name__ == "__main__":
    print("Starting minimal WebSocket test server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
