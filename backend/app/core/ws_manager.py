from fastapi import WebSocket
from typing import Dict, List, Set
import json

class WSConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, symbol: str):
        # WebSocket already accepted in live_ws.py - do NOT accept again
        if symbol not in self.active_connections:
            self.active_connections[symbol] = set()

        self.active_connections[symbol].add(websocket)

    def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            if websocket in self.active_connections[symbol]:
                self.active_connections[symbol].remove(websocket)

    async def broadcast_json(self, symbol: str, message: dict):
        if symbol not in self.active_connections:
            return

        dead = []
        for ws in self.active_connections[symbol]:
            try:
                await ws.send_text(json.dumps(message))
            except:
                dead.append(ws)

        for ws in dead:
            self.active_connections[symbol].remove(ws)

manager = WSConnectionManager()