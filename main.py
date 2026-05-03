from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict
import json, datetime, sqlite3, bcrypt, os, uuid

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

def search_messages(room, query):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute(
        "SELECT sender, text, timestamp FROM room_messages WHERE room=? AND text LIKE ? ORDER BY id DESC LIMIT 20",
        (room, f"%{query}%")
    ).fetchall()
    conn.close()
    return [{"sender": r[0], "text": r[1], "timestamp": r[2]} for r in reversed(rows)]

init_db()

ROOMS = ["general", "random", "tech"]

class Manager:
    def __init__(self):
        self.users: Dict[str, WebSocket] = {}
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

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("index.html", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        return {"error": "Invalid file type."}
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"url": f"/uploads/{filename}"}

@app.get("/uploads/{filename}")
async def get_upload(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return {"error": "Not found"}
    return FileResponse(path)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

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

    for u in list(manager.users.keys()):
        if u != username:
            await manager.send_to(u, {
                "type": "user_online",
                "username": username,
                "online_users": manager.online_users(),
                "all_users": get_all_users(),
            })

    history = load_room_messages(current_room)
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

            if data.get("type") == "typing":
                is_dm = data.get("to") is not None
                if is_dm:
                    await manager.send_to(data.get("to"), {"type": "typing", "username": username, "is_dm": True})
                else:
                    await manager.broadcast_room(current_room, {"type": "typing", "username": username, "room": current_room, "is_dm": False})

            elif data.get("type") == "switch_room":
                new_room = data.get("room")
                if new_room not in ROOMS:
                    continue
                manager.rooms[current_room].pop(username, None)
                await manager.broadcast_room(current_room, {
                    "type": "system", "text": f"{username} left #{current_room}",
                    "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                })
                current_room = new_room
                manager.rooms[current_room][username] = websocket
                history = load_room_messages(current_room)
                await websocket.send_text(json.dumps({"type": "history", "messages": history, "room": current_room}))
                await manager.broadcast_room(current_room, {
                    "type": "system", "text": f"{username} joined #{current_room}",
                    "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                })

            elif data.get("type") == "load_dm":
                other = data.get("with")
                messages = load_dm(username, other)
                await websocket.send_text(json.dumps({"type": "dm_history", "with": other, "messages": messages}))

            elif data.get("type") == "dm":
                receiver = data.get("to")
                text = data.get("text", "")
                ts = _now()
                save_dm(username, receiver, text, ts)
                msg = {"type": "dm", "sender": username, "receiver": receiver, "text": text, "timestamp": ts}
                await manager.send_to(receiver, msg)
                await manager.send_to(username, msg)

            elif data.get("type") == "search":
                query = data.get("query", "")
                results = search_messages(current_room, query)
                await websocket.send_text(json.dumps({"type": "search_results", "results": results, "query": query}))

            elif data.get("text"):
                text = data["text"]
                ts = _now()
                save_room_message(current_room, username, text, ts)
                await manager.broadcast_room(current_room, {
                    "type": "message", "sender": username, "text": text, "timestamp": ts, "room": current_room,
                })

    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_room(current_room, {
            "type": "system", "text": f"{username} left the chat",
            "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
        })
        for u in list(manager.users.keys()):
            await manager.send_to(u, {
                "type": "user_offline", "username": username,
                "online_users": manager.online_users(), "all_users": get_all_users(),
            })

def _now():
    return datetime.datetime.now().strftime("%H:%M")