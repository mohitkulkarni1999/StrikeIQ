"""
Server Side Fix - Remove dead websocket clients
Add this to your WebSocket connection handler
"""

async def handle_websocket_message(websocket, connections):
    """Handle WebSocket message with dead client cleanup"""
    dead_clients = []
    
    # Send message to all connected clients
    for ws in connections:
        try:
            await ws.send_json(data)
        except Exception as e:
            print(f"Dead client detected: {e}")
            dead_clients.append(ws)
    
    # Clean up dead clients
    for ws in dead_clients:
        if ws in connections:
            connections.remove(ws)
            print(f"Removed dead WebSocket client")
    
    dead_clients.clear()

# Usage in your FastAPI WebSocket endpoint:
# @app.websocket("/ws/market")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     connections.append(websocket)
#     
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await handle_websocket_message(websocket, connections, data)
#     except WebSocketDisconnect:
#         if websocket in connections:
#             connections.remove(websocket)
#         print(f"Client disconnected: {websocket.client}")
#     except Exception as e:
#         if websocket in connections:
#             connections.remove(websocket)
#         print(f"Error with client {websocket.client}: {e}")
