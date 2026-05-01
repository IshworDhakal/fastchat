from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict, Set
import json, datetime, sqlite3, bcrypt

app = FastAPI()

# ── Database ───────────────────────────────────
def init_db():
    conn = sqlite3.connect("chat.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            room      TEXT,
            sender    TEXT,
            text      TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def register_user(username, password):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = sqlite3.connect("chat.db")
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not row:
        return False
    return bcrypt.checkpw(password.encode(), row[0].encode())

def save_message(room, sender, text, timestamp):
    conn = sqlite3.connect("chat.db")
    conn.execute("INSERT INTO messages (room, sender, text, timestamp) VALUES (?, ?, ?, ?)",
                 (room, sender, text, timestamp))
    conn.commit()
    conn.close()

def load_messages(room):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute(
        "SELECT sender, text, timestamp FROM messages WHERE room = ? ORDER BY id DESC LIMIT 50",
        (room,)
    ).fetchall()
    conn.close()
    return [{"sender": r[0], "text": r[1], "timestamp": r[2]} for r in reversed(rows)]

init_db()

# ── Room Manager ───────────────────────────────
ROOMS = ["general", "random", "tech"]

class RoomManager:
    def __init__(self):
        # room -> {username -> websocket}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {r: {} for r in ROOMS}

    async def join_room(self, room, username, websocket):
        self.rooms[room][username] = websocket

    def leave_room(self, room, username):
        self.rooms[room].pop(username, None)

    def leave_all_rooms(self, username):
        for room in self.rooms:
            self.rooms[room].pop(username, None)

    def users_in_room(self, room):
        return list(self.rooms[room].keys())

    async def broadcast_room(self, room, message):
        dead = []
        for username, ws in self.rooms[room].items():
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(username)
        for u in dead:
            self.leave_room(room, u)

manager = RoomManager()

# ── Routes ─────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def get():
    with open("index.html") as f:
        return f.read()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Auth
    data = json.loads(await websocket.receive_text())
    action   = data.get("action")
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Username and password required."}))
        await websocket.close()
        return

    if action == "register":
        if not register_user(username, password):
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Username already taken."}))
            await websocket.close()
            return
    elif action == "login":
        if not login_user(username, password):
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Wrong username or password."}))
            await websocket.close()
            return

    # Auth OK
    current_room = "general"
    await websocket.send_text(json.dumps({
        "type": "auth_ok",
        "username": username,
        "rooms": ROOMS
    }))

    # Join default room
    await manager.join_room(current_room, username, websocket)
    history = load_messages(current_room)
    await websocket.send_text(json.dumps({"type": "history", "messages": history, "room": current_room}))
    await manager.broadcast_room(current_room, {
        "type": "system",
        "text": f"{username} joined #{current_room}",
        "users": manager.users_in_room(current_room),
        "room": current_room,
        "timestamp": _now(),
    })

    try:
        while True:
            data = json.loads(await websocket.receive_text())

            # Switch room
            if data.get("type") == "switch_room":
                new_room = data.get("room")
                if new_room not in ROOMS:
                    continue

                # Leave old room
                manager.leave_room(current_room, username)
                await manager.broadcast_room(current_room, {
                    "type": "system",
                    "text": f"{username} left #{current_room}",
                    "users": manager.users_in_room(current_room),
                    "room": current_room,
                    "timestamp": _now(),
                })

                # Join new room
                current_room = new_room
                await manager.join_room(current_room, username, websocket)
                history = load_messages(current_room)
                await websocket.send_text(json.dumps({
                    "type": "history",
                    "messages": history,
                    "room": current_room
                }))
                await manager.broadcast_room(current_room, {
                    "type": "system",
                    "text": f"{username} joined #{current_room}",
                    "users": manager.users_in_room(current_room),
                    "room": current_room,
                    "timestamp": _now(),
                })

            # Chat message
            elif data.get("text"):
                text = data["text"]
                ts   = _now()
                save_message(current_room, username, text, ts)
                await manager.broadcast_room(current_room, {
                    "type": "message",
                    "sender": username,
                    "text": text,
                    "timestamp": ts,
                    "room": current_room,
                })

    except WebSocketDisconnect:
        manager.leave_all_rooms(username)
        await manager.broadcast_room(current_room, {
            "type": "system",
            "text": f"{username} left the chat",
            "users": manager.users_in_room(current_room),
            "room": current_room,
            "timestamp": _now(),
        })

def _now():
    return datetime.datetime.now().strftime("%H:%M")