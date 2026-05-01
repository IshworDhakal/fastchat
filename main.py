from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict
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
        CREATE TABLE IF NOT EXISTS room_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            room      TEXT,
            sender    TEXT,
            text      TEXT,
            timestamp TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dm_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender    TEXT,
            receiver  TEXT,
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

def get_all_users():
    conn = sqlite3.connect("chat.db")
    rows = conn.execute("SELECT username FROM users").fetchall()
    conn.close()
    return [r[0] for r in rows]

def save_room_message(room, sender, text, timestamp):
    conn = sqlite3.connect("chat.db")
    conn.execute("INSERT INTO room_messages (room, sender, text, timestamp) VALUES (?, ?, ?, ?)",
                 (room, sender, text, timestamp))
    conn.commit()
    conn.close()

def load_room_messages(room):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute(
        "SELECT sender, text, timestamp FROM room_messages WHERE room = ? ORDER BY id DESC LIMIT 50",
        (room,)
    ).fetchall()
    conn.close()
    return [{"sender": r[0], "text": r[1], "timestamp": r[2]} for r in reversed(rows)]

def save_dm(sender, receiver, text, timestamp):
    conn = sqlite3.connect("chat.db")
    conn.execute("INSERT INTO dm_messages (sender, receiver, text, timestamp) VALUES (?, ?, ?, ?)",
                 (sender, receiver, text, timestamp))
    conn.commit()
    conn.close()

def load_dm(user1, user2):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute("""
        SELECT sender, receiver, text, timestamp FROM dm_messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY id DESC LIMIT 50
    """, (user1, user2, user2, user1)).fetchall()
    conn.close()
    return [{"sender": r[0], "receiver": r[1], "text": r[2], "timestamp": r[3]} for r in reversed(rows)]

init_db()

# ── Connection Manager ─────────────────────────
ROOMS = ["general", "random", "tech"]

class Manager:
    def __init__(self):
        self.users: Dict[str, WebSocket] = {}  # username -> ws
        self.rooms: Dict[str, Dict[str, WebSocket]] = {r: {} for r in ROOMS}

    async def connect(self, username, websocket):
        self.users[username] = websocket

    def disconnect(self, username):
        self.users.pop(username, None)
        for room in self.rooms:
            self.rooms[room].pop(username, None)

    async def send_to(self, username, message):
        ws = self.users.get(username)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except:
                pass

    async def broadcast_room(self, room, message):
        dead = []
        for username, ws in self.rooms[room].items():
            try:
                await ws.send_text(json.dumps(message))
            except:
                dead.append(username)
        for u in dead:
            self.rooms[room].pop(u, None)

    def online_users(self):
        return list(self.users.keys())

    def users_in_room(self, room):
        return list(self.rooms[room].keys())

manager = Manager()

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
    await manager.connect(username, websocket)
    current_room = "general"
    manager.rooms[current_room][username] = websocket

    await websocket.send_text(json.dumps({
        "type": "auth_ok",
        "username": username,
        "rooms": ROOMS,
        "all_users": get_all_users(),
        "online_users": manager.online_users(),
    }))

    # Notify others user is online
    for u, ws in manager.users.items():
        if u != username:
            await manager.send_to(u, {
                "type": "user_online",
                "username": username,
                "online_users": manager.online_users(),
            })

    # Send room history
    history = load_room_messages(current_room)
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

    try:
        while True:
            data = json.loads(await websocket.receive_text())

            # Switch room
            if data.get("type") == "switch_room":
                new_room = data.get("room")
                if new_room not in ROOMS:
                    continue
                manager.rooms[current_room].pop(username, None)
                await manager.broadcast_room(current_room, {
                    "type": "system",
                    "text": f"{username} left #{current_room}",
                    "users": manager.users_in_room(current_room),
                    "room": current_room,
                    "timestamp": _now(),
                })
                current_room = new_room
                manager.rooms[current_room][username] = websocket
                history = load_room_messages(current_room)
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

            # DM history request
            elif data.get("type") == "load_dm":
                other = data.get("with")
                messages = load_dm(username, other)
                await websocket.send_text(json.dumps({
                    "type": "dm_history",
                    "with": other,
                    "messages": messages
                }))

            # Send DM
            elif data.get("type") == "dm":
                receiver = data.get("to")
                text = data.get("text", "")
                ts = _now()
                save_dm(username, receiver, text, ts)
                msg = {
                    "type": "dm",
                    "sender": username,
                    "receiver": receiver,
                    "text": text,
                    "timestamp": ts,
                }
                await manager.send_to(receiver, msg)
                await manager.send_to(username, msg)

            # Room message
            elif data.get("text"):
                text = data["text"]
                ts = _now()
                save_room_message(current_room, username, text, ts)
                await manager.broadcast_room(current_room, {
                    "type": "message",
                    "sender": username,
                    "text": text,
                    "timestamp": ts,
                    "room": current_room,
                })

    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_room(current_room, {
            "type": "system",
            "text": f"{username} left the chat",
            "users": manager.users_in_room(current_room),
            "room": current_room,
            "timestamp": _now(),
        })
        for u in manager.users:
            await manager.send_to(u, {
                "type": "user_offline",
                "username": username,
                "online_users": manager.online_users(),
            })

def _now():
    return datetime.datetime.now().strftime("%H:%M")