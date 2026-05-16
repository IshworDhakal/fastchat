from typing import Dict
# pyrefly: ignore [missing-import]
from fastapi import WebSocket
import json
from app.core.config import ROOMS

class ConnectionManager:
    def __init__(self):
        self.users: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {r: {} for r in ROOMS}
        self.private_room_members: Dict[str, set] = {}

    async def connect(self, username: str, websocket: WebSocket):
        self.users[username] = websocket

    def disconnect(self, username: str):
        self.users.pop(username, None)
        for room in self.rooms:
            self.rooms[room].pop(username, None)

    async def send_to(self, username: str, message: dict):
        ws = self.users.get(username)
        if ws:
            try: 
                await ws.send_text(json.dumps(message))
            except Exception: 
                pass

    async def broadcast_room(self, room: str, message: dict):
        if room not in self.rooms: return
        dead = []
        for username, ws in self.rooms[room].items():
            try: 
                await ws.send_text(json.dumps(message))
            except Exception: 
                dead.append(username)
        for u in dead: 
            self.rooms[room].pop(u, None)

    async def broadcast_all(self, message: dict):
        for username in list(self.users.keys()):
            await self.send_to(username, message)

    def online_users(self):
        return list(self.users.keys())

    def users_in_room(self, room: str):
        return list(self.rooms.get(room, {}).keys())

    def ensure_room(self, room: str):
        if room not in self.rooms:
            self.rooms[room] = {}

manager = ConnectionManager()
