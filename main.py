from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict
import json, datetime, sqlite3, bcrypt, os, uuid, asyncio

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── ADMIN CONFIG ──────────────────────────────
ADMINS = ["Ishwor123"]  # Add any username here to make them admin

def init_db():
    conn = sqlite3.connect("chat.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS room_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            room      TEXT,
            sender    TEXT,
            text      TEXT,
            timestamp TEXT,
            edited    INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dm_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender    TEXT,
            receiver  TEXT,
            text      TEXT,
            timestamp TEXT,
            edited    INTEGER DEFAULT 0
        )
    """)
    try:
        conn.execute("ALTER TABLE room_messages ADD COLUMN edited INTEGER DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE dm_messages ADD COLUMN edited INTEGER DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except: pass
    conn.commit()
    conn.close()

def register_user(username, password):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        is_admin = 1 if username in ADMINS else 0
        conn = sqlite3.connect("chat.db")
        conn.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, hashed, is_admin))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT password, is_banned FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not row: return False
    if row[1]: return "banned"
    return bcrypt.checkpw(password.encode(), row[0].encode())

def get_all_users():
    conn = sqlite3.connect("chat.db")
    rows = conn.execute("SELECT username, is_admin, is_banned FROM users").fetchall()
    conn.close()
    return [{"username": r[0], "is_admin": bool(r[1]), "is_banned": bool(r[2])} for r in rows]

def is_admin(username):
    if username in ADMINS: return True
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT is_admin FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return bool(row[0]) if row else False

def ban_user(username):
    conn = sqlite3.connect("chat.db")
    conn.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def unban_user(username):
    conn = sqlite3.connect("chat.db")
    conn.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def make_admin(username):
    conn = sqlite3.connect("chat.db")
    conn.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def remove_admin(username):
    conn = sqlite3.connect("chat.db")
    conn.execute("UPDATE users SET is_admin = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def save_room_message(room, sender, text, timestamp):
    conn = sqlite3.connect("chat.db")
    cursor = conn.execute(
        "INSERT INTO room_messages (room, sender, text, timestamp) VALUES (?, ?, ?, ?)",
        (room, sender, text, timestamp)
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def load_room_messages(room):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute(
        "SELECT id, sender, text, timestamp, edited FROM room_messages WHERE room = ? ORDER BY id DESC LIMIT 50",
        (room,)
    ).fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "text": r[2], "timestamp": r[3], "edited": bool(r[4])} for r in reversed(rows)]

def save_dm(sender, receiver, text, timestamp):
    conn = sqlite3.connect("chat.db")
    cursor = conn.execute(
        "INSERT INTO dm_messages (sender, receiver, text, timestamp) VALUES (?, ?, ?, ?)",
        (sender, receiver, text, timestamp)
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def load_dm(user1, user2):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute("""
        SELECT id, sender, receiver, text, timestamp, edited FROM dm_messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY id DESC LIMIT 50
    """, (user1, user2, user2, user1)).fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "receiver": r[2], "text": r[3], "timestamp": r[4], "edited": bool(r[5])} for r in reversed(rows)]

def edit_room_message(msg_id, username, new_text):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT sender FROM room_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username:
        conn.close()
        return False
    conn.execute("UPDATE room_messages SET text=?, edited=1 WHERE id=?", (new_text, msg_id))
    conn.commit()
    conn.close()
    return True

def delete_room_message_admin(msg_id):
    conn = sqlite3.connect("chat.db")
    conn.execute("DELETE FROM room_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return True

def delete_room_message(msg_id, username):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT sender FROM room_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username:
        conn.close()
        return False
    conn.execute("DELETE FROM room_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return True

def edit_dm_message(msg_id, username, new_text):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT sender FROM dm_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username:
        conn.close()
        return False
    conn.execute("UPDATE dm_messages SET text=?, edited=1 WHERE id=?", (new_text, msg_id))
    conn.commit()
    conn.close()
    return True

def delete_dm_message(msg_id, username):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT sender, receiver FROM dm_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username:
        conn.close()
        return False
    conn.execute("DELETE FROM dm_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return True

def search_messages(room, query):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute(
        "SELECT id, sender, text, timestamp FROM room_messages WHERE room=? AND text LIKE ? ORDER BY id DESC LIMIT 20",
        (room, f"%{query}%")
    ).fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "text": r[2], "timestamp": r[3]} for r in reversed(rows)]

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
            except: pass

    async def broadcast_room(self, room, message):
        dead = []
        for username, ws in self.rooms[room].items():
            try:
                await ws.send_text(json.dumps(message))
            except:
                dead.append(username)
        for u in dead:
            self.rooms[room].pop(u, None)

    async def broadcast_all(self, message):
        for username in list(self.users.keys()):
            await self.send_to(username, message)

    def online_users(self):
        return list(self.users.keys())

    def users_in_room(self, room):
        return list(self.rooms[room].keys())

manager = Manager()

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("index.html", encoding="utf-8") as f:
        return f.read()

@app.get("/check-username/{username}")
async def check_username(username: str):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return {"available": row is None}

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

@app.get("/logo.png")
async def get_logo():
    return FileResponse("logo.png")

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
        result = login_user(username, password)
        if result == "banned":
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "You have been banned from GufGaff."}))
            await websocket.close()
            return
        if not result:
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Wrong username or password."}))
            await websocket.close()
            return

    await manager.connect(username, websocket)
    current_room = "general"
    manager.rooms[current_room][username] = websocket
    user_is_admin = is_admin(username)
    all_users = get_all_users()

    await websocket.send_text(json.dumps({
        "type": "auth_ok",
        "username": username,
        "rooms": ROOMS,
        "all_users": [u["username"] for u in all_users if not u["is_banned"]],
        "online_users": manager.online_users(),
        "is_admin": user_is_admin,
        "users_data": all_users,
    }))

    for u in list(manager.users.keys()):
        if u != username:
            await manager.send_to(u, {
                "type": "user_online",
                "username": username,
                "online_users": manager.online_users(),
                "all_users": [u2["username"] for u2 in get_all_users() if not u2["is_banned"]],
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

    async def keepalive():
        while True:
            await asyncio.sleep(25)
            try:
                await websocket.send_text('{"type":"ping"}')
            except:
                break

    asyncio.create_task(keepalive())

    try:
        while True:
            data = json.loads(await websocket.receive_text())

            if data.get("type") == "ping":
                await websocket.send_text('{"type":"pong"}')
                continue

            elif data.get("type") == "admin_delete_user":
                if not is_admin(username):
                    continue
                target = data.get("username")
                if target in ADMINS:
                    continue
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "Your account has been deleted by an admin."})
                    manager.disconnect(target)
                conn = sqlite3.connect("chat.db")
                conn.execute("DELETE FROM users WHERE username = ?", (target,))
                conn.commit()
                conn.close()
                await manager.broadcast_all({
                    "type": "system_admin",
                    "text": f"🗑️ {target}'s account was deleted by admin.",
                    "users_data": get_all_users(),
                })

            elif data.get("type") == "typing":
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
                msg_id = save_dm(username, receiver, text, ts)
                msg = {"type": "dm", "id": msg_id, "sender": username, "receiver": receiver, "text": text, "timestamp": ts, "edited": False}
                await manager.send_to(receiver, msg)
                await manager.send_to(username, msg)

            elif data.get("type") == "edit_message":
                msg_id = data.get("id")
                new_text = data.get("text", "").strip()
                is_dm = data.get("is_dm", False)
                if not new_text:
                    continue
                if is_dm:
                    other = data.get("other")
                    if edit_dm_message(msg_id, username, new_text):
                        msg = {"type": "message_edited", "id": msg_id, "text": new_text, "is_dm": True}
                        await manager.send_to(username, msg)
                        await manager.send_to(other, msg)
                else:
                    if edit_room_message(msg_id, username, new_text):
                        await manager.broadcast_room(current_room, {
                            "type": "message_edited", "id": msg_id, "text": new_text, "is_dm": False, "room": current_room
                        })

            elif data.get("type") == "delete_message":
                msg_id = data.get("id")
                is_dm = data.get("is_dm", False)
                force = data.get("force", False)
                if is_dm:
                    other = data.get("other")
                    if delete_dm_message(msg_id, username):
                        msg = {"type": "message_deleted", "id": msg_id, "is_dm": True}
                        await manager.send_to(username, msg)
                        await manager.send_to(other, msg)
                else:
                    if force and is_admin(username):
                        delete_room_message_admin(msg_id)
                        await manager.broadcast_room(current_room, {
                            "type": "message_deleted", "id": msg_id, "is_dm": False, "room": current_room
                        })
                    elif delete_room_message(msg_id, username):
                        await manager.broadcast_room(current_room, {
                            "type": "message_deleted", "id": msg_id, "is_dm": False, "room": current_room
                        })

            elif data.get("type") == "search":
                query = data.get("query", "")
                results = search_messages(current_room, query)
                await websocket.send_text(json.dumps({"type": "search_results", "results": results, "query": query}))

            # ── ADMIN ACTIONS ──────────────────────────────
            elif data.get("type") == "admin_ban":
                if not is_admin(username):
                    continue
                target = data.get("username")
                if target in ADMINS:
                    continue
                ban_user(target)
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "You have been banned by an admin."})
                    manager.disconnect(target)
                await manager.broadcast_all({
                    "type": "system_admin",
                    "text": f"🚫 {target} has been banned by admin.",
                    "users_data": get_all_users(),
                })

            elif data.get("type") == "admin_unban":
                if not is_admin(username):
                    continue
                target = data.get("username")
                unban_user(target)
                await manager.broadcast_all({
                    "type": "system_admin",
                    "text": f"✅ {target} has been unbanned.",
                    "users_data": get_all_users(),
                })

            elif data.get("type") == "admin_make_admin":
                if not is_admin(username):
                    continue
                target = data.get("username")
                make_admin(target)
                await manager.send_to(target, {"type": "promoted", "text": "You have been made an admin! 👑"})
                await manager.broadcast_all({
                    "type": "system_admin",
                    "text": f"👑 {target} has been made an admin.",
                    "users_data": get_all_users(),
                })

            elif data.get("type") == "admin_remove_admin":
                if not is_admin(username):
                    continue
                target = data.get("username")
                if target in ADMINS:
                    continue
                remove_admin(target)
                await manager.broadcast_all({
                    "type": "system_admin",
                    "text": f"👤 {target} admin role removed.",
                    "users_data": get_all_users(),
                })

            elif data.get("type") == "admin_kick":
                if not is_admin(username):
                    continue
                target = data.get("username")
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "You have been kicked by an admin."})
                    manager.disconnect(target)
                await manager.broadcast_all({
                    "type": "system_admin",
                    "text": f"👢 {target} was kicked by admin.",
                    "users_data": get_all_users(),
                })

            elif data.get("type") == "admin_get_users":
                if not is_admin(username):
                    continue
                await websocket.send_text(json.dumps({
                    "type": "admin_users_list",
                    "users_data": get_all_users(),
                    "online_users": manager.online_users(),
                }))

            elif data.get("type") == "call_offer":
                target = data.get("to")
                await manager.send_to(target, {
                    "type": "call_offer",
                    "from": username,
                    "offer": data.get("offer"),
                    "callType": data.get("callType", "video")
                })

            elif data.get("type") == "call_answer":
                target = data.get("to")
                await manager.send_to(target, {
                    "type": "call_answer",
                    "from": username,
                    "answer": data.get("answer")
                })

            elif data.get("type") == "call_ice":
                target = data.get("to")
                await manager.send_to(target, {
                    "type": "call_ice",
                    "from": username,
                    "candidate": data.get("candidate")
                })

            elif data.get("type") == "call_reject":
                target = data.get("to")
                await manager.send_to(target, {"type": "call_reject", "from": username})

            elif data.get("type") == "call_end":
                target = data.get("to")
                await manager.send_to(target, {"type": "call_end", "from": username})

            elif data.get("text"):
                text = data["text"]
                ts = _now()
                msg_id = save_room_message(current_room, username, text, ts)
                await manager.broadcast_room(current_room, {
                    "type": "message", "id": msg_id, "sender": username,
                    "text": text, "timestamp": ts, "room": current_room, "edited": False,
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
                "online_users": manager.online_users(),
                "all_users": [u2["username"] for u2 in get_all_users() if not u2["is_banned"]],
            })

def _now():
    return datetime.datetime.now().strftime("%H:%M")