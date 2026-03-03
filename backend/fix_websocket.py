"""
Server Side Fix - Remove dead websocket clients
Add this to your WebSocket connection handler
"""

dead_clients = []

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
